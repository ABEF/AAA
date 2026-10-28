"""Fresh holder-exit profile boundaries; local RPC fixtures, no signer/network."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions, TransactionInputError
from frontend_api.activation import ActivationTransactions, ActivationInputError
from keeper.monitor import Keeper, LP_EXIT_BLOCKED_ACTIONS
from zzz_ops.abi import calldata, keccak256
from zzz_ops.position import decode_position, position_word_count, status_name
from zzz_ops.rpc import RpcError
from tests_python import test_frontend_api as F
from tests_python import test_frontend_transactions as T
from tests_python import test_local_position_services as K
from tests_python import test_royalty_reporting as R
from tests_python import test_current_activation_profile as A


def setup_api(rpc=None):
    rpc = rpc or F.MockRPC()
    cfg = F.configuration()
    cfg.update(accounting_version=4, fee_intake_version=1)
    code = '0x600900'
    rpc.codes[F.addr(9)] = code
    cfg['contracts']['principal_exit'] = {'address': F.addr(9),
        'code_hash': '0x'+keccak256(bytes.fromhex(code[2:])).hex()}
    rpc.put(F.addr(3), 'ACCOUNTING_VERSION()', values=(4,))
    rpc.put(F.addr(7), 'SCHEMA()', values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5').hex(),))
    rpc.put(F.addr(1), 'GOVERNANCE_VERSION()', values=(2,))
    rpc.put(F.addr(1), 'governance()', values=(F.addr(40),))
    rpc.put(F.addr(1), 'module(bytes32)', ('0x'+keccak256(b'ZZZMigration').hex(),), (F.addr(9),))
    rpc.put(F.addr(9), 'access()', values=(F.addr(1),))
    rpc.put(F.addr(9), 'CUSTODY_VERSION()', values=(3,))
    rpc.put(F.addr(9), 'currentZZZ()', values=(F.addr(20),))
    rpc.put(F.addr(9), 'exitPhase()', values=(0,))
    rpc.put(F.addr(1), 'lpExitStarted()', values=(0,))
    rpc.put(F.addr(9), 'principalOf(uint256)', (rpc.nft_id,), (0, 0, 0, 0))
    rpc.put(F.addr(3), 'group(uint256)', (5,), (444, 9, 0, 0, 2000*10**18, 2**96, 990, 1))
    rpc.put(F.addr(4), 'assetCount()', values=(3,))
    for ordinal, asset in enumerate((ZERO, F.addr(20), F.addr(21))):
        rpc.put(F.addr(4), 'assets(uint256)', (ordinal,), (asset,))
    rpc.put(F.addr(4), 'claimable(uint256,address)', (rpc.nft_id, ZERO), (17,))
    return cfg, rpc


def exit_state(rpc, phase=3, *, allocated=True, paid=False, eth=123, zzz=456):
    rpc.put(F.addr(1), 'lpExitStarted()', values=(1,))
    rpc.put(F.addr(9), 'exitPhase()', values=(phase,))
    rpc.put(F.addr(3), 'nftStatus(uint256)', (rpc.nft_id,), (5,))
    rpc.put(F.addr(3), 'group(uint256)', (5,), (444, 0, 0, 0, 2000*10**18, 2**96, 990, 5))
    rpc.put(F.addr(2), 'currentLPValue(uint256)', (rpc.nft_id,), (1, 0))
    rpc.put(F.addr(9), 'principalOf(uint256)', (rpc.nft_id,), (eth, zzz, int(allocated), int(paid)))
    rpc.put(F.addr(9), 'claimablePrincipal(uint256)', (rpc.nft_id,), (0, 0) if paid else (eth, zzz))


class HolderExitAPITests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.rpc = setup_api()

    def read(self):
        return Projection(self.cfg, self.rpc, clock=lambda: 1000).nft(self.rpc.nft_id)

    def test_explicit_codec_never_relabels_historical_dormant_or_remote(self):
        self.assertEqual(8, position_word_count(4))
        self.assertEqual('exited', status_name(4, 5))
        self.assertEqual('dormant', status_name(1, 5))
        self.assertEqual('remote', status_name(2, 3))
        with self.assertRaises(ValueError): status_name(3, 5)
        with self.assertRaises(ValueError): decode_position(['0'*64]*15, 4)

    def test_fresh_profile_requires_principal_module_runtime_and_binding(self):
        missing = copy.deepcopy(self.cfg); del missing['contracts']['principal_exit']
        with self.assertRaises(ValueError): Projection(missing, self.rpc)
        for target, signature, value in ((1,'module(bytes32)',F.addr(91)), (9,'CUSTODY_VERSION()',2),
                (9,'access()',F.addr(91)), (7,'SCHEMA()','0x'+'f'*64)):
            with self.subTest(signature=signature):
                self.cfg, self.rpc = setup_api()
                args = ('0x'+keccak256(b'ZZZMigration').hex(),) if signature == 'module(bytes32)' else ()
                self.rpc.put(F.addr(target), signature, args, (value,))
                with self.assertRaises(ProjectionError): self.read()

    def test_operating_position_keeps_rewards_separate_from_unallocated_principal(self):
        result = self.read()
        self.assertEqual('enhanced', result['position']['evolution'])
        self.assertEqual('operating', result['principal_return']['phase'])
        self.assertIsNone(result['principal_return']['assets'][0]['allocated_raw'])
        self.assertIsNone(result['principal_return']['assets'][0]['remaining_raw'])
        self.assertFalse(result['position']['principal_redeemable'])
        self.assertEqual('17', result['claimable']['lp'][0]['raw'])

    def test_protocol_exposes_verified_exit_phase_and_rejects_unknown_phase(self):
        exit_state(self.rpc)
        p=Projection(self.cfg,self.rpc,clock=lambda:1000)
        result=p.protocol()
        self.assertEqual('ready',result['lifecycle']['lp_exit_phase'])
        self.assertTrue(result['lifecycle']['lp_exit_started'])
        self.assertFalse(result['minting']['available_by_controls'])
        self.rpc.put(F.addr(9),'exitPhase()',values=(4,))
        with self.assertRaises(ProjectionError):p.protocol()

    def test_exited_position_has_zero_lp_but_keeps_royalty_and_earned_claims(self):
        exit_state(self.rpc)
        result = self.read()
        self.assertEqual('exited', result['position']['status'])
        self.assertEqual('lp_exited', result['position']['evolution'])
        self.assertEqual('0', result['position']['current_lp_value']['raw'])
        self.assertEqual(2, result['position']['royalty_weight'])
        self.assertTrue(result['position']['activated'])
        self.assertTrue(result['lifecycle']['claims_available_by_lifecycle'])
        self.assertTrue(result['lifecycle']['transfers_available_by_lifecycle'])
        self.assertFalse(result['lifecycle']['new_economic_work_available_by_lifecycle'])
        self.assertEqual('123', result['principal_return']['assets'][0]['claimable_raw'])
        self.assertEqual('17', result['claimable']['lp'][0]['raw'])
        self.assertNotIn('principal', result['claimable'])

    def test_paid_principal_is_not_erased_or_repeated_and_owner_is_fresh(self):
        exit_state(self.rpc, paid=True)
        self.rpc.put(F.addr(2), 'ownerOf(uint256)', (self.rpc.nft_id,), (F.addr(31),))
        result = self.read()['principal_return']
        self.assertEqual(F.addr(31), result['beneficiary'])
        self.assertTrue(result['paid'])
        self.assertEqual('123', result['assets'][0]['allocated_raw'])
        self.assertEqual('0', result['assets'][0]['claimable_raw'])
        self.assertFalse(result['automatic_payout_available_by_lifecycle'])

    def test_partial_allocation_never_invents_available_zero_or_payability(self):
        exit_state(self.rpc, phase=2, allocated=False, eth=0, zzz=0)
        result = self.read()['principal_return']
        self.assertFalse(result['allocated'])
        self.assertIsNone(result['assets'][0]['remaining_raw'])
        self.assertIsNone(result['assets'][0]['claimable_raw'])
        self.assertFalse(result['holder_claim_available_by_lifecycle'])

    def test_contradictory_exit_values_are_rejected(self):
        mutations = (
            (F.addr(1),'lpExitStarted()',(),(0,)),
            (F.addr(2),'currentLPValue(uint256)',(self.rpc.nft_id,),(1,1)),
            (F.addr(9),'principalOf(uint256)',(self.rpc.nft_id,),(123,456,0,0)),
            (F.addr(9),'principalOf(uint256)',(self.rpc.nft_id,),(123,456,1,2)),
            (F.addr(9),'claimablePrincipal(uint256)',(self.rpc.nft_id,),(124,456)),
        )
        for target, signature, args, values in mutations:
            with self.subTest(signature=signature):
                self.cfg, self.rpc = setup_api(); exit_state(self.rpc)
                self.rpc.put(target,signature,args,values)
                with self.assertRaises(ProjectionError): self.read()

    def test_native_royalty_gap_cannot_call_removed_custody_getter(self):
        self.cfg = R.profile(self.cfg, self.rpc, converter=False)
        self.rpc.responses[F.addr(5), R.native_data('eligibleCount(address)',ZERO)] = F.words(2)
        self.rpc.responses[F.addr(5), R.native_data('eligibleFor(uint256,address)',self.rpc.nft_id,ZERO)] = F.words(0)
        with self.assertRaisesRegex(ProjectionError,'native royalty eligibility'): self.read()
        removed = calldata('custodyNonce(address)',F.addr(1))[:10]
        self.assertFalse(any(method == 'eth_call' and args[0]['data'].startswith(removed) for method,args in self.rpc.calls))

    def test_exit_blocks_mint_draft_but_preserves_current_owner_reward_claim(self):
        cfg, rpc = setup_api(T.TransactionRPC()); exit_state(rpc)
        p = Projection(cfg, rpc, clock=lambda:1000)
        drafts = Transactions(p, T.transaction_config(p))
        with self.assertRaises(TransactionInputError): drafts.prepare({'action':'mint','wallet':F.addr(30)})
        self.assertEqual([],rpc.simulations)
        result = drafts.prepare({'action':'claim','wallet':F.addr(30),'claims':[
            {'token_id':str(rpc.nft_id),'asset':F.addr(21),'royalty':False}]})
        self.assertEqual(F.addr(6),result['transaction']['to'])
        self.assertEqual('0x0',result['transaction']['value'])

    def test_exit_rejects_activation_before_route_or_approval_work(self):
        exit_state(self.rpc)
        p = Projection(self.cfg, self.rpc, clock=lambda:1000)
        draft = object.__new__(ActivationTransactions)
        draft.p = p
        pool = '0x'+'1'*64
        # Only the configuration needed before the lifecycle barrier is present.
        # A regression past that barrier must fail this test rather than quote.
        draft.config = SimpleNamespace(routing_version=2, pricing_version=2,
            lp_routing_version=0,
            review_policy_version=1, sources={(pool,ZERO):('0x'+'0'*64,'0x'+'2'*64)})
        with self.assertRaisesRegex(ActivationInputError,'collective exit'):
            draft.prepare(dict(action='activate', wallet=F.addr(30), token_id=str(self.rpc.nft_id),
                pool_id=pool,source_asset=ZERO,amount_in='100000000000000000',slippage_bps=200))

    def test_operating_profile4_prepares_exact_activation_and_growth(self):
        for increase in (False,True):
            with self.subTest(increase=increase):
                rpc = A.CurrentActivationRPC(increase=increase)
                rpc.config['maintenance_policy_version'] = 1
                cfg = F.configuration()
                cfg.update(accounting_version=4,fee_intake_version=1)
                cfg['assets']=[cfg['assets'][0],dict(address=F.addr(21),decimals=18,
                    symbol='ZZZ',code_hash=rpc.digest(F.addr(21)))]
                cfg['contracts']['principal_exit']=dict(rpc.config['contracts']['migration'])
                module=cfg['contracts']['principal_exit']['address']
                rpc.put(module,'CUSTODY_VERSION()',values=(3,))
                rpc.put(module,'exitPhase()',values=(0,))
                rpc.put(F.addr(1),'lpExitStarted()',values=(0,))
                rpc.put(F.addr(3),'ACCOUNTING_VERSION()',values=(4,))
                rpc.put(F.addr(7),'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5').hex(),))
                p=Projection(cfg,rpc,clock=lambda:1000)
                service=ActivationTransactions(p,rpc.config)
                result=service.prepare(rpc.request)
                self.assertTrue(result['activation_ready'])
                self.assertEqual(4,result['provenance']['accounting_version'])
                self.assertEqual(hex(rpc.original_amount),result['transaction']['value'])


class HolderExitKeeperTests(unittest.TestCase):
    def setUp(self):
        self.f = K.LocalPositionKeeperTests('runTest'); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.cfg = copy.deepcopy(self.f.cfg); self.rpc = self.f.rpc
        self.cfg['accounting_version'] = 4; self.f.f.version = 4
        self.exit = F.addr(91); self.cfg['contracts']['principal_exit'] = self.exit
        pin='0x'+keccak256(bytes.fromhex('6000')).hex()
        self.cfg['code_hashes'].update(access=pin,principal_exit=pin)
        self.started = 0; self.phase = 0
        original = self.rpc.call
        def current_call(method,args):
            if method == 'eth_call' and 'from' not in args[0]:
                data=args[0]['data']; target=args[0]['to']
                value = None
                if data == calldata('lpExitStarted()'): value=self.started
                elif target == self.exit and data == calldata('exitPhase()'): value=self.phase
                elif target == self.exit and data == calldata('CUSTODY_VERSION()'): value=3
                elif target == self.exit and data == calldata('access()'): value=int(self.cfg['contracts']['access'],16)
                elif data == calldata('module(bytes32)','0x'+keccak256(b'ZZZMigration').hex()): value=int(self.exit,16)
                if value is not None:
                    self.rpc.calls.append((method,args)); return F.words(value)
            return original(method,args)
        self.rpc.call=current_call
        self.k = self.f.base.k = Keeper(self.cfg,rpc=self.rpc)

    def test_lp_exit_disables_every_principal_action_but_not_old_reward_jobs(self):
        self.started=1; self.phase=1
        for role,signature in LP_EXIT_BLOCKED_ACTIONS:
            with self.subTest(signature=signature): self.assertTrue(self.k._defer_for_lifecycle(role,signature))
        self.assertFalse(self.k._defer_for_lifecycle('royalties','convertBatch(address,uint256[],bytes32,uint256,uint256)'))
        self.assertFalse(self.k._defer_for_lifecycle('buyback','execute(address,uint256,bytes32,uint256)'))
        with patch.object(self.k,'submit') as submit:
            self.k.cycle(); submit.assert_not_called()

    def test_pending_recovery_runs_before_new_exit_reads(self):
        self.k.state['pending']={'key':'saved'}; self.started=2
        with patch.object(self.k,'poll_pending',return_value=True),patch.object(self.k,'lp_exit_started') as read:
            self.k.cycle(); read.assert_not_called()

    def test_exit_flag_is_strict_and_old_journals_cannot_be_relabelled(self):
        self.started=2
        with self.assertRaises(RpcError): self.k.lp_exit_started()
        self.k.save(); before=self.k.path.read_bytes()
        previous=copy.deepcopy(self.cfg);previous['accounting_version']=3
        with self.assertRaisesRegex(ValueError,'another accounting version'):Keeper(previous,rpc=self.rpc)
        self.assertEqual(before,self.k.path.read_bytes())

    def test_metadata_terminal_stage_requires_explicit_new_profile(self):
        record=dict(ordinal=1,token_id='12',traits_ready=True,available=True,stage=4)
        self.k._validate_metadata_record(record)
        self.f.k._validate_metadata_record(dict(record,stage=1))
        with self.assertRaises(ValueError): self.f.k._validate_metadata_record(record)


if __name__ == '__main__': unittest.main()
