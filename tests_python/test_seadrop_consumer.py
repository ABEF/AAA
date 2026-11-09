"""Opt-in V10 reader/claim boundary, with synthetic pinned RPC transcripts.

These tests exercise the actual Projection and unsigned preparer, not an actual
SeaDrop deployment, OpenSea onboarding, public signing or operating acceptance.
"""
import copy
from pathlib import Path
import tempfile
import unittest

from frontend_api.service import Projection, ProjectionError, ZERO
from frontend_api.transactions import Transactions, TransactionInputError
from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python.test_frontend_api import addr, words
from tests_python.test_frontend_transactions import transaction_config
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import Budget, request_scope


V10 = '0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10').hex()


class SeaDropAPI:
    def __init__(self, case):
        self.old = Fresh7API(case)
        self.rpc, self.config = self.old.rpc, copy.deepcopy(self.old.config)
        self.c = dict(self.old.c)
        self.config['mint_integration_version'] = 2
        for number, role in enumerate(('seadrop_mint', 'seadrop'), 15000):
            target, code = addr(number), '0x6002' + f'{number:04x}'
            self.c[role] = target
            self.rpc.codes[target] = code
            self.config['contracts'][role] = dict(address=target,
                code_hash='0x' + keccak256(bytes.fromhex(code[2:])).hex())
        for role, signature, value in (
                ('nft', 'seaDropMint()', self.c['seadrop_mint']),
                ('seadrop_mint', 'access()', self.c['access']),
                ('seadrop_mint', 'nft()', self.c['nft']),
                ('seadrop_mint', 'seaDrop()', self.c['seadrop']),
                ('seadrop_mint', 'MINT_INTEGRATION_VERSION()', 1),
                ('seadrop_mint', 'seaDropCodeHash()', self.config['contracts']['seadrop']['code_hash']),
                ('handoff', 'SCHEMA()', V10)):
            self.rpc.put(self.c[role], signature, values=(value,))
        self.p = Projection(self.config, self.rpc, clock=lambda: 4000)
        self.simulations = []

    def block(self):
        return self.old.block()

    def transactions(self, amounts=(18,)):
        original = self.rpc.call
        def call(method, params):
            if method == 'eth_call' and 'from' in params[0]:
                self.rpc.calls.append((method, copy.deepcopy(params)))
                self.simulations.append(copy.deepcopy(params))
                if params[0]['to'] != self.c['claim_router']:
                    raise AssertionError('Only the fixed claim router may be simulated')
                return words(32, len(amounts), *amounts)
            if method == 'eth_estimateGas':
                self.rpc.calls.append((method, copy.deepcopy(params)))
                return hex(100000)
            if method == 'eth_gasPrice':
                self.rpc.calls.append((method, copy.deepcopy(params)))
                return hex(10**9)
            if method == 'eth_getBalance':
                self.rpc.calls.append((method, copy.deepcopy(params)))
                return hex(10**18)
            if 'send' in method or 'sign' in method:
                raise AssertionError('No signing or transaction submission is allowed')
            return original(method, params)
        self.rpc.call = call
        return Transactions(self.p, transaction_config(self.p))

    def claim(self, *, royalty=False, asset=ZERO):
        return dict(token_id=str(self.rpc.nft_id), asset=asset, royalty=royalty)


class SeaDropConsumerTests(unittest.TestCase):
    def test_v9_default_and_explicit_one_remain_historical_without_new_roles(self):
        old = Fresh7API(self)
        self.assertEqual(1, old.p.mint_integration_version)
        self.assertNotIn('seadrop', old.p.contracts)
        self.assertEqual('operating', old.p._verify_deployment(old.block())['state'])
        cfg = copy.deepcopy(old.config); cfg['mint_integration_version'] = 1
        self.assertEqual('operating', Projection(cfg, old.rpc, clock=lambda:4000)._verify_deployment(old.block())['state'])
        old.rpc.put(old.c['handoff'], 'SCHEMA()', values=(V10,))
        with self.assertRaisesRegex(ProjectionError, 'schema'):
            old.p._verify_deployment(old.block())

    def test_profile_flag_rejects_booleans_unknown_values_and_non7(self):
        f = SeaDropAPI(self)
        for value in (True, False, None, 0, 3, '2', 2.0):
            cfg = copy.deepcopy(f.config); cfg['mint_integration_version'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'mint integration'):
                Projection(cfg, f.rpc)
        cfg = copy.deepcopy(f.config); cfg['accounting_version'] = 6
        with self.assertRaisesRegex(ValueError, 'mint integration'):
            Projection(cfg, f.rpc)

    def test_two_extra_distinct_pinned_contract_roles_are_required(self):
        f = SeaDropAPI(self)
        for role in ('seadrop_mint', 'seadrop'):
            cfg = copy.deepcopy(f.config); cfg['contracts'].pop(role)
            with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'contracts'):
                Projection(cfg, f.rpc)
        cfg = copy.deepcopy(f.config)
        cfg['contracts']['seadrop'] = copy.deepcopy(cfg['contracts']['seadrop_mint'])
        with self.assertRaisesRegex(ValueError, 'distinct'):
            Projection(cfg, f.rpc)
        cfg = copy.deepcopy(f.config); cfg.pop('mint_integration_version')
        with self.assertRaisesRegex(ValueError, 'contracts'):
            Projection(cfg, f.rpc)

    def test_funded_nft_and_royalties_read_at_the_same_canonical_hash(self):
        f = SeaDropAPI(self)
        result = f.p.nft(f.rpc.nft_id)
        self.assertEqual(addr(30), result['owner'])
        self.assertEqual('18', result['claimable']['lp'][0]['raw'])
        self.assertGreater(int(result['claimable']['royalties'][0]['raw']), 0)
        self.assertEqual(f.c['seadrop_mint'], result['contracts']['seadrop_mint'])
        calls = [(m,p) for m,p in f.rpc.calls if m in ('eth_call','eth_getCode')]
        self.assertTrue(calls)
        self.assertTrue(all(p[-1] == f.block() for _,p in calls))
        for role, signature in (('nft','seaDropMint()'),('seadrop_mint','access()'),
                ('seadrop_mint','nft()'),('seadrop_mint','MINT_INTEGRATION_VERSION()'),
                ('seadrop_mint','seaDrop()'),('seadrop_mint','seaDropCodeHash()')):
            self.assertTrue(any(m=='eth_call' and p[0] == dict(to=f.c[role],data=calldata(signature)) for m,p in calls))

    def test_every_new_binding_and_capability_is_checked(self):
        for role, signature in (('nft','seaDropMint()'),('seadrop_mint','access()'),
                ('seadrop_mint','nft()'),('seadrop_mint','seaDrop()'),
                ('seadrop_mint','MINT_INTEGRATION_VERSION()'),('seadrop_mint','seaDropCodeHash()')):
            with self.subTest(signature=signature):
                f = SeaDropAPI(self)
                f.rpc.put(f.c[role], signature, values=(addr(34567),))
                with self.assertRaises(ProjectionError):
                    f.p._verify_deployment(f.block())

    def test_runtime_changes_and_v9_schema_are_never_relabelled_v10(self):
        for variant in ('seadrop_mint','seadrop','schema'):
            with self.subTest(variant=variant):
                f = SeaDropAPI(self)
                if variant == 'schema':
                    f.rpc.put(f.c['handoff'],'SCHEMA()', values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9').hex(),))
                else:
                    f.rpc.codes[f.c[variant]] = '0x6000'
                with self.assertRaises(ProjectionError):
                    f.p._verify_deployment(f.block())

    def test_mint2_refuses_direct_draft_before_any_rpc_or_simulation(self):
        f = SeaDropAPI(self); service = f.transactions()
        before = copy.deepcopy(f.rpc.calls)
        with self.assertRaisesRegex(TransactionInputError, 'Use OpenSea'):
            service.prepare(dict(action='mint',wallet=addr(30)))
        self.assertEqual(before, f.rpc.calls)
        self.assertEqual([], f.simulations)

    def test_protocol_marks_open_collection_window_as_unverified_opensea_eligibility(self):
        f = SeaDropAPI(self)
        f.rpc.put(f.c['royalties'],'mintEnd()',values=(9000,))
        f.rpc.put(f.c['royalties'],'mintEndRevision()',values=(1,))
        f.rpc.put(f.c['nft'],'mintedCount()',values=(1,))
        result = f.p.protocol()['minting']
        self.assertTrue(result['available_by_sale_window'])
        self.assertTrue(result['available_by_controls'])
        self.assertIsNone(result['available'])
        self.assertEqual('opensea',result['channel'])
        self.assertEqual('unverified',result['stage_eligibility'])
        self.assertFalse(result['direct_transaction_preparation_supported'])

    def test_closed_or_unconfigured_sale_does_not_block_owned_lp_and_currency_claims(self):
        f = SeaDropAPI(self); original = f.rpc.call
        prohibited = {calldata(s) for s in ('configurationHash()','configured()', 'publicDrop()',
            'salePolicy()', 'mintFingerprint()', 'reviewedMintPrice()', 'settings()')}
        def call(method, params):
            if method == 'eth_call' and (params[0]['to']==f.c['seadrop'] or params[0]['data'] in prohibited):
                raise AssertionError('Mutable sale configuration must not gate LP or claim reads')
            return original(method, params)
        f.rpc.call = call
        result = f.p.nft(f.rpc.nft_id)
        self.assertEqual('18', result['claimable']['lp'][0]['raw'])
        service = f.transactions((18,25000001))
        draft = service.prepare(dict(action='claim',wallet=addr(30),claims=[
            f.claim(), f.claim(royalty=True,asset=addr(21))]))
        self.assertEqual(['18','25000001'],[v['view_raw'] for v in draft['claim_operations']])
        self.assertEqual(['18','25000001'],[v['simulated_raw'] for v in draft['claim_operations']])
        self.assertEqual(1,len(f.simulations))
        self.assertEqual('0x0',draft['transaction']['value'])
        self.assertEqual('12000000',draft['simulation']['gas_cap'])
        self.assertTrue(all(p[-1]==f.block() for m,p in f.rpc.calls if m in ('eth_call','eth_getCode','eth_estimateGas','eth_getBalance')))

    def test_nonowner_or_zero_claim_cannot_create_an_unsigned_success(self):
        for variant in ('owner','zero'):
            with self.subTest(variant=variant):
                f = SeaDropAPI(self); service = f.transactions()
                if variant=='owner':
                    f.rpc.put(f.c['nft'],'ownerOf(uint256)',(f.rpc.nft_id,),(addr(31),))
                else:
                    f.rpc.put(f.c['rewards'],'claimable(uint256,address)',(f.rpc.nft_id,ZERO),(0,))
                with self.assertRaises(TransactionInputError):
                    service.prepare(dict(action='claim',wallet=addr(30),claims=[f.claim()]))
                self.assertEqual([],f.simulations)

    def test_claim_planner_caches_only_required_new_identity_reads_and_keeps_budgets(self):
        f = SeaDropAPI(self); service = f.transactions()
        result = service.plan_claims(dict(action='claim',wallet=addr(30),claims=[f.claim()]))
        self.assertEqual('in_next_batch',result['entries'][0]['status'])
        self.assertEqual('18',result['next_batch']['claim_operations'][0]['simulated_raw'])
        self.assertEqual(2,len(f.simulations))
        self.assertEqual(10,result['planning']['maximum_trials'])
        self.assertEqual(32,result['planning']['maximum_selection'])
        self.assertEqual(2,result['provenance']['mint_integration_version'])
        for role, signature in (('nft','seaDropMint()'),('seadrop_mint','access()'),
                ('seadrop_mint','nft()'),('seadrop_mint','MINT_INTEGRATION_VERSION()'),
                ('seadrop_mint','seaDrop()'),('seadrop_mint','seaDropCodeHash()')):
            selected = [p for m,p in f.rpc.calls if m=='eth_call' and p[0]==dict(to=f.c[role],data=calldata(signature))]
            self.assertEqual(1,len(selected),signature)
        ownership = [p for m,p in f.rpc.calls if m=='eth_call' and p[0]==dict(to=f.c['nft'],data=calldata('ownerOf(uint256)',f.rpc.nft_id))]
        self.assertEqual(3,len(ownership))

    def _lineage_config(self, f, peer_profile):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        cfg = copy.deepcopy(f.config)
        history = lambda contracts,name:dict(database=str(Path(temporary.name)/name),start_block=1,
            start_parent_hash='0x'+'1'*64,contracts=[contracts[r]['address'] for r in ('nft','rewards','royalties')],max_events=100)
        cfg['history'] = history(cfg['contracts'],'current.sqlite')
        peer = copy.deepcopy(f.old.config if peer_profile==1 else f.config)
        for role,item in peer['contracts'].items():
            if role!='seadrop':item['address']=addr(int(item['address'],16)+20000)
        fields = ('deployment_block','deployment_block_hash','contracts','assets','accounting_version','custody_version','royalty_reporting')
        descriptor = {key:peer[key] for key in fields}
        descriptor.update(history=history(peer['contracts'],'peer.sqlite'),retirement_transaction_hash='0x'+'2'*64)
        if peer_profile==2:descriptor['mint_integration_version']=2
        cfg['predecessors'] = [descriptor]
        return cfg

    def test_lineage_omitted_peer_flag_stays_v9_and_explicit_two_keeps_v10(self):
        for profile in (1,2):
            with self.subTest(profile=profile):
                f = SeaDropAPI(self); cfg = self._lineage_config(f,profile)
                p = Projection(cfg,f.rpc,clock=lambda:4000)
                peer = p.lineage.entries[0].projection
                self.assertEqual(profile,peer.mint_integration_version)
                self.assertEqual(profile==2,'seadrop_mint' in peer.contracts)
                if profile==2:self.assertEqual(p.contracts['seadrop'],peer.contracts['seadrop'])

    def test_lineage_cannot_infer_new_profile_or_reuse_owned_helper_or_conflicting_core(self):
        for variant in ('missing_profile','boolean','helper_reuse','core_pin'):
            with self.subTest(variant=variant):
                f = SeaDropAPI(self); cfg = self._lineage_config(f,2); peer=cfg['predecessors'][0]
                if variant=='missing_profile':peer.pop('mint_integration_version')
                elif variant=='boolean':peer['mint_integration_version']=True
                elif variant=='helper_reuse':peer['contracts']['seadrop_mint']=copy.deepcopy(cfg['contracts']['seadrop_mint'])
                else:peer['contracts']['seadrop']['code_hash']='0x'+'3'*64
                with self.assertRaises(ValueError):Projection(cfg,f.rpc,clock=lambda:4000)

    def test_new_reads_do_not_expand_request_rpc_budget(self):
        f = SeaDropAPI(self)
        with request_scope(Budget(calls=1)),self.assertRaises(WorkLimit):
            f.p.nft(f.rpc.nft_id)


if __name__ == '__main__':
    unittest.main()
