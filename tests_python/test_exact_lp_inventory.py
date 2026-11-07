"""Source-only schema16 admission and historical boundary, never release approval."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout,redirect_stderr
from unittest.mock import patch
from zzz_ops import production_v14 as P,production_v13 as OLD
from zzz_ops import production_observer_v14 as O,production_observer_v13 as OLD_O
from zzz_ops import factory_code_v3 as F,factory_code_v2 as OLD_F
from tests_python.test_residual_reinvest_profile import load_script

ROOT=Path(__file__).resolve().parents[1]
GATE=load_script('validate-production-config')
CLI=load_script('observe-production-config')
def config():return json.loads((ROOT/'config/production.example.json').read_text())
def old():return json.loads((ROOT/'config/production.schema15.example.json').read_text())
def addr(i):return '0x'+format(i,'040x')

class ExactLPInventoryTests(unittest.TestCase):
    def test_schema15_archived_bytes_and_factory_payload2_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT/'config/production.schema15.example.json').read_bytes()).hexdigest(),
            '3fb9071f631fb3664b15c580514fac1a61f887c787837caa7077054cac72881c')
        self.assertEqual(old()['schema_version'],15)
        self.assertEqual(OLD.VERSIONS['accounting_version'],6)
        self.assertNotIn('lp_allocation_version',OLD.VERSIONS)
        self.assertEqual(OLD_F.SPEC.creation_hash,'0x4a520b4af1c8ded6fe2539ec7f3ec4f6d9a1c7fbdd710a53ccffd3412bfce831')
        self.assertNotIn('rewards_canonical',OLD.HELPERS)

    def test_current_template_explicit7_v9_has_no_observations_or_approval(self):
        c=config();self.assertEqual(c['schema_version'],16);self.assertEqual(c['accounting_version'],7)
        self.assertEqual(c['lp_allocation_version'],1);self.assertEqual(c['canonical_schema'],P.SCHEMA_NAME)
        self.assertEqual(len(P.HELPERS),19);self.assertEqual(len(c['chains'][0]['helpers']),19)
        self.assertTrue(all(r['address'] is None and r['observed_runtime_hash'] is None for r in c['chains'][0]['helpers'].values()))
        r=GATE.validate(c,now=1793970000)
        self.assertEqual(r['schema_version'],16);self.assertFalse(r['ready']);self.assertFalse(r['deployment_authorized'])
        self.assertIn('mint.opensea_unsupported',{x['code'] for x in r['issues']})
        self.assertNotIn('schema.fields',{x['code'] for x in r['issues']})

    def test_exact_getters_and_fixed_canonical_child_binding_are_required(self):
        c=config()['chains'][0];c['helpers']['rewards_canonical']['address']=addr(900)
        c['modules']['rewards']['address']=addr(901);c['modules']['access']['address']=addr(902)
        b=P.expected_bindings(c)
        self.assertEqual(b['modules']['rewards']['LP_ALLOCATION_VERSION'],1)
        self.assertEqual(b['modules']['rewards']['MAX_ASSETS'],2)
        self.assertEqual(b['modules']['vault']['ACCOUNTING_VERSION'],7)
        self.assertEqual(b['modules']['canonical']['SCHEMA'],P.SCHEMA_HASH)
        self.assertEqual(b['modules']['canonical']['moduleAt3'],addr(900))
        self.assertEqual(b['modules']['rewards']['canonicalModule'],addr(900))
        self.assertEqual(b['helpers']['rewards_canonical'],dict(access=addr(902),rewards=addr(901)))
        for group,role in OLD.REINVEST_ROLES:self.assertEqual(b[group][role]['RESIDUAL_REINVEST_VERSION'],1)

    def test_old15_cannot_enter_current_gate_or_observer(self):
        r=GATE.validate(old());self.assertEqual(r['schema_version'],16)
        self.assertFalse(r['ready']);self.assertFalse(r['deployment_authorized'])
        class NoRpc:
            def call(self,*_):raise AssertionError('Historical profile must stop before RPC')
        for key,value in (('schema_version',15),('accounting_version',6),('lp_allocation_version',True)):
            c=config();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):O.observe(c,NoRpc())

    def test_new_payload_identity_is_separate_from_storage_format2(self):
        self.assertEqual(F.VERSION,2);self.assertEqual(F.SPEC.creation_length,25522)
        self.assertEqual(F.SPEC.creation_hash,'0x0b5b619ca10d338f29e7a76fd3f9069b2e034864112bbd3101bbc20a279c50aa')
        self.assertNotEqual(F.SPEC.creation_hash,OLD_F.SPEC.creation_hash)
        self.assertEqual(vars(F.SPEC.parts[0]),vars(OLD_F.SPEC.parts[0]))
        self.assertNotEqual(vars(F.SPEC.parts[1]),vars(OLD_F.SPEC.parts[1]));self.assertEqual(len(F.SPEC.source_sha256),87)
        with self.assertRaises(ValueError):F.parse_section(old()['chains'][0])
        with self.assertRaises(ValueError):OLD_F.parse_section(config()['chains'][0])
        self.assertEqual(F.parse_section(config()['chains'][0])['code_storage_version'],2)

    def test_observer_reads_exact_getter_types_and_real_moduleAt_selector(self):
        o=object.__new__(O.Observer);calls=[]
        o.read=lambda target,sig,*args:calls.append((sig,args)) or [format(1,'064x')]
        for name in ('LP_ALLOCATION_VERSION','MAX_ASSETS'):self.assertIs(type(o.typed(addr(1),name,None)),int)
        for name in ('canonicalModule','rewards','moduleAt3'):self.assertEqual(o.typed(addr(1),name,None),addr(1))
        self.assertEqual(calls[-1],('moduleAt(uint8)',(3,)))

    def test_cli_requires_explicit_current16_or_historical15(self):
        result={'chains':[{'observation':{'complete':False}}]}
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.json';out=Path(folder)/'out.json'
            for historical_config,historical_flag in ((False,False),(True,True),(True,False)):
                source.write_text(json.dumps(old() if historical_config else config()))
                args=['--config',str(source),'--rpc-env','POPL_REVIEW_RPC','--output',str(out)]
                if historical_flag:args.append('--historical-consistency')
                with patch.dict(os.environ,{'POPL_REVIEW_RPC':'http://127.0.0.1:1'}),patch.object(CLI,'Rpc',return_value=object()),patch.object(O,'observe',return_value=result) as fresh,patch.object(OLD_O,'observe',return_value=result) as previous,patch.object(CLI,'write_observation') as write,redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                    status=CLI.main(args)
                self.assertEqual(status,1 if historical_config and not historical_flag else 2)
                self.assertEqual(fresh.call_count,int(not historical_config))
                self.assertEqual(previous.call_count,int(historical_config and historical_flag))
                self.assertEqual(write.call_count,int(not historical_config or historical_flag))

    def test_current_offline_operator_templates_preserve_exact_archives(self):
        from zzz_ops import operator_review as O
        expected={'mode': 'dacbb597bb89fdb66a11329c744b68619fb8ff164846c2d752b2e30a604a0a26', 'residual-close': 'c2965e8beb19b30fd1f3308e671e7ecfb9c1358581247d5d6005c7ce51a768a2', 'emergency': 'f047d5ceb7af939a241424bac2dbb672192597108cf55b3515bd033617f4e39d'}
        for kind,digest in expected.items():
            current=ROOT/('config/operator-review.'+kind+'.example.json')
            archived=ROOT/('config/operator-review.accounting6.'+kind+'.example.json')
            raw=archived.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
            a,b=json.loads(current.read_bytes()),json.loads(raw)
            self.assertEqual(a.pop('profile'),O.PROFILE)
            self.assertTrue(b.pop('profile').startswith('accounting6/'))
            self.assertEqual(a,b)
            self.assertIn('<CURRENT_GOVERNANCE_ADDRESS>',a['chain']['governance'])

    def test_fixed_two_lp_assets_do_not_limit_original_royalty_currencies(self):
        from zzz_ops.production_v2 import Gate
        c=config()['chains'][0];c['helpers']['activation_assets']['bindings']['zzz']=addr(700)
        c['reward_assets'].update(asset_count=2,observed_asset_count=2,assets=[dict(address=P.BASE.ZERO),dict(address=addr(700))])
        for n,row in enumerate(c['factory_code']['parts']):
            row.update(address=addr(800+n),observed_data_length=row['data_length'],observed_runtime_length=row['runtime_length'],observed_runtime_hash=row['runtime_hash'],observed_prefix='0x5f5ffd')
        c['factory_code'].update(observed_creation_code_length=F.SPEC.creation_length,observed_creation_code_hash=F.SPEC.creation_hash)
        def codes():
            g=Gate(None);P.factory_code(g,c,'chain',[]);return {x['code'] for x in g.issues}
        self.assertNotIn('lp.assets.fixed',codes())
        c['reward_assets']['assets'].append(dict(address=addr(701)))
        c['reward_assets']['asset_count']=c['reward_assets']['observed_asset_count']=3
        self.assertIn('lp.assets.fixed',codes());self.assertEqual(P.MAX_TOKEN_RECORDS,66)

if __name__=='__main__':unittest.main()
