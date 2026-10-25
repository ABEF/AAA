"""Explicit local Position3 services, with historical fixtures kept separate."""
import copy
import json
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper, NATIVE_ASSET
from zzz_ops import production_v2 as P, production_observer as O
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError
from tests_python import test_keeper as K
import tests_python.test_keeper_native as N
from tests_python import test_production_v2 as F
from tests_python.fee_intake_fixtures import lp_only_fixture
from tests_python.test_production_observer import CompositionRPC, RUNTIME, encoded, selector


class LocalPositionKeeperTests(unittest.TestCase):
    def setUp(self):
        fixture = N.NativeKeeperTests('runTest'); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.f = fixture; self.base = fixture.f; self.rpc = fixture.rpc
        self.cfg = copy.deepcopy(fixture.cfg)
        self.cfg.update(accounting_version=3,fee_intake_version=1)
        self.cfg['code_hashes']['fees'] = '0x'+keccak256(bytes.fromhex('6000')).hex()
        self.cfg.setdefault('maintenance',{})['sync_external_rewards'] = False
        fixture.version = 3
        self.base.group_words = self.base.group_words[:8]
        original = self.rpc.call
        def current_call(method,params):
            if method == 'eth_call' and params[0]['data'] == calldata('FEE_INTAKE_VERSION()'):
                self.rpc.calls.append((method,params)); return '0x'+f'{1:064x}'
            return original(method,params)
        self.rpc.call = current_call
        self.k = self.base.k = Keeper(self.cfg,rpc=self.rpc)

    def test_current_active_position_compounds_native_currency_without_legacy_reads(self):
        self.base.invoke().assert_called_once_with('compounder','compound(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'compound:7')
        fields,tokens = self.k._bucket(7)
        self.assertEqual(8,len(fields)); self.assertEqual([NATIVE_ASSET,K.C],tokens)
        calls = [params[0]['data'][:10] for method,params in self.rpc.calls if method == 'eth_call']
        self.assertNotIn(calldata('nativeAsset(bytes32)',self.base.pool)[:10],calls)
        self.assertNotIn(calldata('rewardReceiver(uint256)',7)[:10],calls)

    def test_dormant_three_is_skipped_and_parked_four_never_runs_maintenance(self):
        for status in (0,2,3,4):
            with self.subTest(status=status):
                self.base.group_words[7] = status
                self.base.group_words[1] = 0 if status == 4 else 10
                self.base.invoke().assert_not_called()

    def test_current_eight_word_profile_rejects_legacy_rows_and_remote_statuses(self):
        original = self.base.group_words[:]
        for words in (original+[1]*7,original[:-1],original[:7]+[5],original[:7]+[6]):
            with self.subTest(words=len(words),status=words[7] if len(words)>7 else None):
                self.base.group_words = words
                with self.assertRaisesRegex(RpcError,'vault group ABI'): self.k._bucket(7)

    def test_active_and_parked_physical_position_invariants_stay_enforced(self):
        for status,lp in ((1,0),(4,10)):
            self.base.group_words[7] = status; self.base.group_words[1] = lp
            with self.subTest(status=status),self.assertRaises(RpcError): self.k._bucket(7)

    def test_runtime_profile_mismatch_stops_before_scheduling(self):
        self.f.version = 2
        with patch.object(self.k,'submit') as submit:
            with self.assertRaisesRegex(RpcError,'accounting version differs'): self.k.cycle()
            submit.assert_not_called()

    def test_saved_old_or_new_journal_cannot_be_relabelled(self):
        self.k.state['next_nonce']=7
        self.k.state['pending']={'key':'harvest:7','nonce':7,'to':K.B,
            'data':calldata('collectFees(uint256,uint256)',7,100),'value':0,'day':'2026-10-24','hash':K.H}
        self.k.save(); current = self.k.path.read_bytes()
        old = copy.deepcopy(self.cfg); old['accounting_version']=2
        with self.assertRaisesRegex(ValueError,'another accounting version'): Keeper(old,rpc=self.rpc)
        self.assertEqual(current,self.k.path.read_bytes())
        state=json.loads(current); state['accounting_version']=2
        self.k.path.write_text(json.dumps(state)); historical=self.k.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'another accounting version'): Keeper(self.cfg,rpc=self.rpc)
        self.assertEqual(historical,self.k.path.read_bytes())

    def test_pending_recovery_precedes_current_runtime_gate(self):
        pending={'key':'saved'}; self.k.state['pending']=pending; self.f.version=2
        with patch.object(self.k,'poll_pending',return_value=True),patch.object(self.k,'submit') as submit:
            self.k.cycle(); submit.assert_not_called()
        self.assertIs(pending,self.k.state['pending'])

    def test_current_position_requires_explicit_lp_only_fee_profile(self):
        for version in (None,0,False,'1'):
            cfg=copy.deepcopy(self.cfg);cfg['fee_intake_version']=version
            with self.subTest(version=version),self.assertRaises(ValueError): Keeper(cfg,rpc=self.rpc)

    def test_historical_parked_position_preserves_original_home_provenance(self):
        old=N.NativeKeeperTests('runTest');old.setUp();self.addCleanup(old.doCleanups)
        old.f.group_words[7]=6;old.f.group_words[1]=0
        old.f.group_words[8]=42;old.f.group_words[9]=int(K.A,16)
        fields,tokens=old.k._bucket(7)
        self.assertEqual(15,len(fields));self.assertEqual([NATIVE_ASSET,K.C],tokens)
        self.assertEqual(42,int(fields[8],16));self.assertEqual(int(K.A,16),int(fields[9],16))


class LocalPositionInventoryTests(unittest.TestCase):
    def test_current_bindings_require_local_codec_and_direct_governance(self):
        config=lp_only_fixture(F.fixture());chain=config['chains'][0]
        report=P.validate(config,now=F.NOW)
        self.assertTrue(report['ready'],report['issues'])
        expected=P.expected_bindings(chain,fee_intake_version=1)
        self.assertEqual(3,expected['modules']['vault']['ACCOUNTING_VERSION'])
        self.assertEqual(2,expected['modules']['access']['GOVERNANCE_VERSION'])
        self.assertEqual(chain['governance']['multisig'],expected['modules']['access']['governance'])
        self.assertEqual(P.ZERO,expected['modules']['access']['pendingGovernance'])
        self.assertNotIn('getMinDelay',expected['modules']['access'])
        self.assertEqual(P.LP_ONLY_CANONICAL_SCHEMA,expected['modules']['canonical']['SCHEMA'])

    def test_current_profile_never_relabels_old_accounting_or_canonical_schema(self):
        for mutation in ('version','schema','getter'):
            config=lp_only_fixture(F.fixture());chain=config['chains'][0]
            if mutation=='version':config['accounting_version']=2;chain['native_accounting']['version']=2
            elif mutation=='schema':chain['native_accounting']['canonical_schema']=P.HISTORICAL_LP_ONLY_CANONICAL_SCHEMA
            else:chain['modules']['vault']['observed_bindings']['ACCOUNTING_VERSION']=2
            result=P.validate(config,now=F.NOW)
            with self.subTest(mutation=mutation):self.assertFalse(result['ready'])

    def test_retired_roles_pending_governance_or_wrong_governor_block_release(self):
        for mutation in ('roles','pending','governor','version'):
            config=lp_only_fixture(F.fixture());chain=config['chains'][0]
            if mutation=='roles':chain['governance']['proposers']=[chain['governance']['multisig']]
            elif mutation=='pending':chain['governance']['observed_roles']['pending_governance']=F.addr(9999)
            elif mutation=='governor':chain['modules']['access']['observed_bindings']['governance']=F.addr(9999)
            else:chain['modules']['access']['observed_bindings']['GOVERNANCE_VERSION']=1
            result=P.validate(config,now=F.NOW)
            with self.subTest(mutation=mutation):self.assertFalse(result['ready'])

    def test_direct_observer_never_calls_removed_timelock_selectors(self):
        deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(F,'HASH',RUNTIME):
            config=lp_only_fixture(F.fixture());rpc=CompositionRPC(config)
            result=O.observe(config,rpc)
            self.assertTrue(result['chains'][0]['observation']['complete'],result['chains'][0]['observation']['errors'])
            self.assertTrue(P.validate(result,now=F.NOW)['ready'])
            calls={params[0]['data'][:10] for method,params in rpc.calls if method=='eth_call'}
            for signature in ('GOVERNANCE_VERSION()','governance()','pendingGovernance()'):
                self.assertIn(selector(signature),calls)
            for signature in ('getMinDelay()','hasRole(bytes32,address)','schedule(address,uint256,bytes,bytes32,bytes32,uint256)'):
                self.assertNotIn(selector(signature),calls)

    def test_observer_wrong_or_unreadable_governor_cannot_reuse_declared_address(self):
        deps={role:(address,RUNTIME) for role,(address,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(F,'HASH',RUNTIME):
            for response in ('0x',encoded(F.addr(99999))):
                config=lp_only_fixture(F.fixture());rpc=CompositionRPC(config)
                rpc.overrides[config['chains'][0]['modules']['access']['address'],selector('governance()')]=response
                result=O.observe(config,rpc)
                with self.subTest(response=response):
                    self.assertFalse(result['chains'][0]['observation']['complete'])
                    self.assertFalse(P.validate(result,now=F.NOW)['ready'])

    def test_observer_rejects_profile_mismatch_before_network(self):
        for version in (None,2,True,'3'):
            config=lp_only_fixture(F.fixture());config['accounting_version']=version
            rpc=CompositionRPC(config)
            with self.subTest(version=version),self.assertRaisesRegex(ValueError,'accounting3'): O.observe(config,rpc)
            self.assertEqual([],rpc.calls)


if __name__=='__main__':unittest.main()
