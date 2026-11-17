"""Focused exact-envelope regressions; injected RPC, no chain or signer."""
import contextlib
import copy
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_python import test_manual_lp_review as fixture
from tests_python import test_parked_manual_lp_review as parked_fixture
from zzz_ops import manual_lp_review as M, management_review as G
from zzz_ops.errors import RpcError


class ManualFrozenGasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=M.offline.Catalog()

    def setUp(self):
        self.f=fixture.ManualLPReviewTests('runTest');self.f.catalog=self.catalog
        self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.rpc=self.f.rpc

    def after_initial_exact(self,change):
        original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if (method=='eth_call' and params[0]['data'][:10] in self.rpc.void_selectors
                    and len(self.rpc.simulations)==2 and params[-1]['blockHash']==self.f.f.rpc.hash):
                change()
            return result
        replacement=patch.object(self.rpc,'call',side_effect=call)
        replacement.start();self.addCleanup(replacement.stop)

    def test_exact_gas_is_frozen_across_healthy_lower_cost_market_change(self):
        self.after_initial_exact(lambda:setattr(self.rpc,'gas',80000))
        out=self.f.prepare()
        self.assertEqual(hex(125000),out['transaction']['gas'])
        self.assertEqual('125000',out['simulation']['initial']['transaction_gas'])
        self.assertEqual('125000',out['simulation']['final']['transaction_gas'])
        self.assertEqual('100000',out['simulation']['final']['padded_gas'])
        self.assertEqual('250000',out['network_gas']['maximum_network_fee_wei'])
        self.assertEqual('125000',out['network_gas']['transaction_gas'])
        self.assertEqual([1000000,125000,1000000,125000],
            [int(p[0]['gas'],16) for p in self.rpc.simulations])
        self.assertEqual(self.rpc.simulations[1][0],self.rpc.simulations[3][0])
        self.assertEqual([self.f.f.rpc.hash,self.f.f.rpc.hash,self.rpc.latest_hash,self.rpc.latest_hash],
            [p[-1]['blockHash'] for p in self.rpc.simulations])
        self.assertFalse(out['ready_for_submission']);self.assertFalse(out['production_approved'])
        self.assertEqual('4180',out['arguments']['deadline'])
        self.assertFalse(any('send' in method.lower() for method,_ in self.rpc.calls))

    def test_initial_exact_gas_failure_is_not_hidden_by_successful_cap_probe(self):
        original=self.rpc.call
        def call(method,params):
            if (method=='eth_call' and params[0]['data'][:10] in self.rpc.void_selectors
                    and params[0].get('gas')==hex(125000)):
                raise RpcError('exact envelope fails at low gas')
            return original(method,params)
        with patch.object(self.rpc,'call',side_effect=call),self.assertRaises(RpcError):self.f.prepare()
        self.assertEqual(1,len(self.rpc.estimates))
        self.assertEqual(1,len(self.rpc.simulations))

    def test_final_cost_increase_cannot_silently_raise_transaction_gas(self):
        original=copy.deepcopy(self.f.request)
        self.after_initial_exact(lambda:setattr(self.rpc,'gas',120000))
        with self.assertRaises(M.ManualReadBlocked) as caught:self.f.prepare()
        self.assertEqual('frozen_gas_insufficient',caught.exception.manual_code)
        self.assertEqual('final_simulation',caught.exception.manual_stage)
        self.assertEqual(3,len(self.rpc.simulations));self.assertEqual(2,len(self.rpc.estimates))
        self.assertEqual(original,self.f.request)

    def test_final_fee_budget_uses_frozen_gas_not_cheaper_new_estimate(self):
        self.f.policy['fee_policy']['max_network_fee_wei']='325000'
        def change():self.rpc.gas=80000;self.rpc.price=3
        self.after_initial_exact(change)
        with self.assertRaises(M.ManualReadBlocked) as caught:self.f.prepare()
        self.assertEqual('network_fee_budget_exceeded',caught.exception.manual_code)
        self.assertEqual('final_simulation',caught.exception.manual_stage)

    def test_final_exact_gas_return_must_still_match_void_abi(self):
        original=self.rpc.call
        def call(method,params):
            if (method=='eth_call' and params[0]['data'][:10] in self.rpc.void_selectors
                    and params[-1].get('blockHash')==self.rpc.latest_hash
                    and params[0].get('gas')==hex(125000)):
                return '0x'+'0'*64
            return original(method,params)
        with patch.object(self.rpc,'call',side_effect=call),self.assertRaises(M.ManualReadBlocked) as caught:
            self.f.prepare()
        self.assertEqual('unexpected_simulation_output',caught.exception.manual_code)
        self.assertEqual('final_simulation',caught.exception.manual_stage)

    def test_frozen_budget_still_requires_final_block_capacity(self):
        self.after_initial_exact(lambda:setattr(self.rpc,'block_limit',120000))
        with self.assertRaises(M.ManualReadBlocked):self.f.prepare()
        self.assertEqual('1000000',self.f.policy['fee_policy']['max_gas_limit'])

    def test_parked_schema2_also_freezes_gas_without_enabling_active_guards(self):
        f=parked_fixture.ParkedManualLPReviewTests('runTest');f.catalog=self.catalog
        f.setUp();self.addCleanup(f.doCleanups)
        out=f.prepare()
        self.assertEqual(2,out['schema']);self.assertEqual(hex(125000),out['transaction']['gas'])
        self.assertEqual('125000',out['simulation']['final']['transaction_gas'])
        self.assertEqual([],out['safeguards']['retained'])
        self.assertEqual([1,2,4,8,16],[row['bit'] for row in out['safeguards']['bypassed']])

    def test_management_dangling_output_is_preserved_before_any_input_or_rpc(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'review.json';stderr=io.StringIO()
            args=[value for key in ('read-config','policy','selection','output')
                for value in ('--'+key,str(output if key=='output' else Path(directory)/(key+'.json')))]
            with patch.object(G.os.path,'lexists',return_value=True),patch.object(G,'prepare') as prepare,\
                    patch.object(G.offline,'load') as load,contextlib.redirect_stderr(stderr):
                self.assertEqual(1,G.main(args))
            prepare.assert_not_called();load.assert_not_called()
            diagnostic=json.loads(stderr.getvalue())
            self.assertEqual('existing_output_preserved',diagnostic['reason'])
            self.assertTrue(diagnostic['output_may_exist'])
            self.assertFalse(diagnostic['transaction_submitted'])

    def test_owned_rehearsal_preserves_current_gas_and_explicit_old_artifacts(self):
        path=Path(__file__).resolve().parents[1]/'scripts/rehearse-manual-recovery.py'
        spec=importlib.util.spec_from_file_location('manual_frozen_gas_rehearsal',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        current={'transaction':{'gas':hex(125000)},
            'simulation':{'final':{'transaction_gas':'125000','padded_gas':'100000'}}}
        self.assertEqual(125000,module.reviewed_execution_gas(current))
        current['transaction']['gas']=hex(100000)
        with self.assertRaisesRegex(ValueError,'frozen envelope'):module.reviewed_execution_gas(current)
        old={'transaction':{},'simulation':{'final':{'padded_gas':'125000'}}}
        self.assertEqual(125000,module.reviewed_execution_gas(old))

    def test_strict_reference_wrapper_accepts_only_the_exact_updated_base_source(self):
        path=Path(__file__).resolve().parents[1]/'scripts/rehearse-manual-reference.py'
        spec=importlib.util.spec_from_file_location('manual_frozen_gas_reference',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertTrue(callable(module.b.reviewed_execution_gas))
        # A successful import alone never proved rejection of changed bytes.
        # Exercise the actual guard on a disposable copy before it can import
        # the changed base; no chain, executable launch or source edit occurs.
        with tempfile.TemporaryDirectory() as directory:
            copied=Path(directory)/path.name
            copied.write_bytes(path.read_bytes())
            base=Path(directory)/'rehearse-manual-recovery.py'
            base.write_bytes(path.with_name(base.name).read_bytes()+b'\n# changed copied source\n')
            changed=importlib.util.spec_from_file_location('manual_changed_copy',copied)
            candidate=importlib.util.module_from_spec(changed)
            with self.assertRaisesRegex(ValueError,'Reviewed base launcher source differs'):
                changed.loader.exec_module(candidate)


if __name__=='__main__':unittest.main()
