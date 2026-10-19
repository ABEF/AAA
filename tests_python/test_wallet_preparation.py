"""Current lifecycle, failure isolation, fee policy and worker regressions."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions, TransactionConfig, TransactionInputError, MINT_PRICE
from frontend_api.worker import WorkerClient, _run
from tests_python.test_frontend_api import addr, configuration
from tests_python.test_frontend_transactions import TransactionRPC, transaction_config
from zzz_ops.abi import calldata
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, request_scope


class WalletSafetyTests(unittest.TestCase):
    def setUp(self):
        self.rpc = TransactionRPC(); self.wall = 1000
        self.p = Projection(configuration(), self.rpc, clock=lambda:self.wall)
        self.config = transaction_config(self.p)
        self.service = Transactions(self.p, self.config)
        self.mint = {'action':'mint', 'wallet':addr(30)}
        self.claim = {'action':'claim', 'wallet':addr(30), 'claims':[
            {'token_id':str(self.rpc.nft_id), 'asset':ZERO, 'royalty':True}]}

    def test_mint_only_pause_blocks_mint_but_not_claims(self):
        self.rpc.put(addr(2), 'mintPaused()', values=(1,))
        with self.assertRaises(TransactionInputError): self.service.prepare(self.mint)
        self.assertEqual(self.rpc.simulations, [])
        self.assertEqual(self.service.prepare(self.claim)['action'], 'claim')

    def test_preparation_blocks_mint_but_leaves_funded_claims_available(self):
        self.rpc.put(addr(1), 'preparationActive()', values=(1,))
        with self.assertRaises(TransactionInputError): self.service.prepare(self.mint)
        self.assertEqual(self.rpc.simulations, [])
        self.assertEqual(self.service.prepare(self.claim)['action'], 'claim')

    def test_frozen_retired_importing_cancelled_cannot_prepare_any_action(self):
        for state,phase in ((1,1),(2,2),(3,3),(4,7)):
            with self.subTest(state=state):
                self.rpc.put(addr(1),'canonicalState()',values=(state,))
                self.rpc.put(addr(1),'preparationActive()',values=(int(state in (1,3)),))
                self.rpc.put(addr(7),'phase()',values=(phase,))
                self.rpc.put(addr(7),'incomingSource()',values=(addr(90) if state in (2,4) else ZERO,))
                self.rpc.put(addr(7),'destinationController()',values=(addr(91) if state in (1,3) else ZERO,))
                self.rpc.put(addr(8),'originVault()',values=(addr(92) if state in (2,4) else addr(3),))
                for action in (self.mint,self.claim):
                    with self.assertRaisesRegex(ProjectionError,'locked'):self.service.prepare(action)
        self.assertEqual(self.rpc.simulations, [])

    def test_mint_never_reads_reward_inventory_or_token_health(self):
        self.rpc.codes[addr(21)] = '0x'
        self.rpc.put(addr(5),'assetCount()',values=(500,))
        self.assertEqual(self.service.prepare(self.mint)['action'],'mint')
        self.assertFalse(any(m=='eth_call' and p[0]['data']==calldata('assetCount()') for m,p in self.rpc.calls))

    def test_failed_unselected_currency_allows_healthy_claim_but_selected_fails(self):
        self.rpc.codes[addr(21)] = '0x'
        self.assertEqual(self.service.prepare(self.claim)['claim_operations'][0]['asset'], ZERO)
        self.claim['claims'][0]['asset']=addr(21)
        with self.assertRaisesRegex(ProjectionError,'currency'):self.service.prepare(self.claim)
        self.assertEqual(len(self.rpc.simulations),1)

    def test_inventory_change_and_core_mismatch_still_fail_closed(self):
        self.rpc.put(addr(5),'assets(uint256)',(1,),(addr(99),))
        with self.assertRaises(ProjectionError):self.service.prepare(self.claim)
        self.rpc.codes[addr(4)]='0x'
        with self.assertRaises(ProjectionError):self.service.prepare(self.mint)
        self.assertEqual(self.rpc.simulations,[])

    def test_fee_estimate_and_ceiling_are_separate_from_mint_payment(self):
        r=self.service.prepare(self.mint);gas=r['network_gas']
        self.assertEqual(r['transaction']['value'],hex(MINT_PRICE))
        self.assertEqual(gas['estimated_fee_wei'],str(100000*10**9))
        self.assertEqual(gas['suggested_limit_cost_wei'],str(120000*10**9))
        self.assertTrue(gas['wallet_must_refresh'])
        self.assertEqual(gas['fee_policy_review_hash'],self.config['fee_policy']['review_hash'])
        self.assertEqual(r['provenance']['transaction_configuration_sha256'],self.service.config.identity)

    def test_balance_cannot_fund_gas_with_expected_claim_proceeds(self):
        self.rpc.native_balance=0
        with self.assertRaises(TransactionInputError):self.service.prepare(self.claim)
        self.rpc.native_balance=MINT_PRICE
        with self.assertRaises(TransactionInputError):self.service.prepare(self.mint)
        self.rpc.native_balance=MINT_PRICE+120000*10**9
        self.assertEqual(self.service.prepare(self.mint)['action'],'mint')

    def test_gas_price_estimate_and_total_fee_bounds(self):
        for field,value in (('estimate',20999),('estimate',12000001),('gas_price',0),('gas_price',10000000001),('estimate',9000000)):
            with self.subTest(field=field,value=value):
                self.setUp();setattr(self.rpc,field,value)
                with self.assertRaises(ProjectionError):self.service.prepare(self.mint)

    def test_fee_policy_bound_to_exact_read_manifest_and_explicit_review(self):
        cases=[{'schema':True},{'chain_id':1},{'projection_sha256':'0'*64},
               {'fee_policy':{**self.config['fee_policy'],'estimate_includes_all_fees':False}},
               {'fee_policy':{**self.config['fee_policy'],'review_hash':'0x'+'0'*64}},
               {'fee_policy':{**self.config['fee_policy'],'max_gas_price_wei':1}},
               {'fee_policy':{**self.config['fee_policy'],'max_network_fee_wei':'01'}}]
        for change in cases:
            with self.subTest(change=change),self.assertRaises(ValueError):
                TransactionConfig({**self.config,**change},self.p)
        self.assertEqual(self.rpc.calls,[])

    def test_expired_rpc_result_ends_work_before_next_request_even_with_relaxed_age(self):
        self.p.max_age=86400;original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_getCode':self.wall=1110
            return result
        self.rpc.call=call
        with self.assertRaises(WorkLimit):self.service.prepare(self.mint)
        self.assertEqual(self.rpc.calls[-1][0],'eth_getCode')
        self.assertEqual(self.rpc.simulations,[])

    def test_nested_work_budget_cannot_be_reset_and_next_request_recovers(self):
        with self.assertRaises(WorkLimit),request_scope(Budget(calls=10)):
            self.service.prepare(self.mint)
        self.assertEqual(self.service.prepare(self.mint)['action'],'mint')

    def test_token_health_does_not_swallow_terminal_budget_error(self):
        original=self.rpc.call
        def call(method,params):
            if method=='eth_getCode' and params[0]==addr(21):raise WorkLimit('rpc_budget')
            return original(method,params)
        self.rpc.call=call
        with self.assertRaises(WorkLimit):self.service.prepare(self.claim)
        self.assertEqual(self.rpc.simulations,[])

    def test_expiry_during_estimate_stops_before_gas_price_or_draft(self):
        original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_estimateGas':self.wall=1110
            return result
        self.rpc.call=call
        with self.assertRaises(WorkLimit):self.service.prepare(self.mint)
        self.assertEqual(self.rpc.calls[-1][0],'eth_estimateGas')

    def test_missing_hash_estimation_support_has_no_latest_fallback(self):
        original=self.rpc.call
        def call(method,params):
            if method=='eth_estimateGas':raise RpcError('Unsupported canonical selector')
            return original(method,params)
        self.rpc.call=call
        with self.assertRaises(RpcError):self.service.prepare(self.mint)

    def test_worker_config_requires_opt_in_and_rejects_ambiguous_services(self):
        client=WorkerClient(configuration())
        with patch.object(client,'_request') as request:
            with self.assertRaises(RpcError):client.prepare(self.mint)
            request.assert_not_called()
        with self.assertRaises(ValueError):WorkerClient(configuration(),{},transaction_config=self.config)
        client=WorkerClient(configuration(),transaction_config=self.config)
        with patch.object(client,'_request',return_value={'ok':True}) as request:
            self.assertEqual(client.prepare(self.mint),{'ok':True})
            request.assert_called_once_with('transactions',self.mint)

    def test_child_sanitizes_input_failures_and_receives_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'result.json'
            with patch('frontend_api.worker.Projection',return_value=self.p):
                _run(str(output),configuration(),None,'transactions',{'action':'mint','wallet':'SECRET'},self.config)
            self.assertEqual(json.loads(output.read_text()),{'error':'invalid_transaction'})
            with patch('frontend_api.worker.Projection',return_value=self.p):
                _run(str(output),configuration(),None,'transactions',self.mint,self.config)
            self.assertEqual(json.loads(output.read_text())['ok']['action'],'mint')


def input_error_child(output, config, activation, action, payload, transactions):
    Path(output).write_text(json.dumps({'error':'invalid_transaction'}))


class WalletWorkerTests(unittest.TestCase):
    def test_spawned_input_error_preserves_type_and_reaps_worker(self):
        p=Projection(configuration());client=WorkerClient(configuration(),transaction_config=transaction_config(p))
        with patch('frontend_api.worker._run',input_error_child),contextlib.redirect_stdout(io.StringIO()) as log:
            with self.assertRaises(TransactionInputError):client.prepare({'action':'mint'})
        self.assertIsNone(client._unreaped)
        self.assertNotIn('wallet',log.getvalue())


if __name__=='__main__':unittest.main()
