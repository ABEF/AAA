"""New payload5 and scoped bounded-read policy controls; no live qualification."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from zzz_ops import factory_code_v3 as F3,factory_code_v4 as F4,factory_code_v5 as F5
from zzz_ops import production_v15 as P,production_observer_v15 as O
from zzz_ops import royalty_read_policy as R,deployment_plan as D,preseal_plan as PRE
from tests_python import preseal_fixture

ROOT=Path(__file__).resolve().parents[1]
BLOCK={'blockHash':'0x'+'ab'*32,'requireCanonical':True}
def addr(n):return '0x'+f'{n:040x}'
def config(name='production.example.json'):return json.loads((ROOT/'config'/name).read_bytes())
def word(n):return f'{n:064x}'
def h(raw):return '0x'+D.keccak256(raw).hex()


def declared_policy(policy=addr(99),cap=50000,revision=1):
    return dict(version=1,policy=policy,balance_gas=cap,gas_revision=revision,
        fingerprint=R.fingerprint(policy,cap,revision),fingerprint_scope=R.SCOPE)


def chain():
    value=config()['chains'][0]
    value['modules']['access']['address']=addr(77)
    value['helpers']['protocol_policy']['address']=addr(99)
    value['helpers']['royalty_rewards']['address']=addr(98)
    value['helpers']['activation_assets']['bindings']['zzz']=addr(700)
    value['reward_assets'].update(asset_count=2,observed_asset_count=2,
        assets=[dict(address=P.BASE.ZERO),dict(address=addr(700))])
    row=value['royalty_read_policy'];row.update(declared_policy(),observed=declared_policy())
    value['protocol_policy']['gas']['revision']=1
    for row,part in zip(value['factory_code']['parts'],F5.SPEC.parts):
        row.update(address=addr(800+part.index),observed_data_length=part.data_length,
            observed_runtime_length=part.runtime_length,observed_runtime_hash=part.runtime_hash,observed_prefix='0x5f5ffd')
    value['factory_code'].update(observed_creation_code_length=F5.SPEC.creation_length,
        observed_creation_code_hash=F5.SPEC.creation_hash)
    return value


def actual_parts():
    output=D.Artifacts().output
    F5.verify_compiler_output(output)
    code=bytes.fromhex(output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
    return ['0x'+part.hex() for part in F5.split_creation(code)]


class FactoryPayload5Tests(unittest.TestCase):
    def test_new_payload5_matches_actual_trusted_full_normal_and_rejects_old_bytes(self):
        output=D.Artifacts().output;parts=actual_parts()
        self.assertTrue(F5.verify_compiler_output(output))
        _,whole=F5.verify_runtime_parts(parts)
        self.assertEqual(whole,dict(observed_creation_code_length=F5.SPEC.creation_length,
            observed_creation_code_hash=F5.SPEC.creation_hash))
        self.assertEqual(len(parts),2)
        self.assertNotIn(F5.SPEC.creation_hash,(F3.SPEC.creation_hash,F4.SPEC.creation_hash))
        for old in (F3,F4):
            with self.subTest(old=old.__name__):
                with self.assertRaises(ValueError):old.verify_runtime_parts(parts)
                with self.assertRaises(ValueError):old.verify_compiler_output(output)

    def test_exact_historical3_and4_templates_retain_separate_identity_and_no_read_policy(self):
        names=(('production.schema17.payload3.example.json',F3,
            '2c7fda19ebcffd4f302b1945c3853716f7979c0153757f0a79fc0377390015ca'),
            ('production.schema17.payload4.example.json',F4,
            'cc1061255416857aab34b6ccfe4c44b0281f6745fc142cda2440ea08a011692b'))
        for name,module,pin in names:
            raw=(ROOT/'config'/name).read_bytes();old=json.loads(raw)['chains'][0]
            self.assertEqual(hashlib.sha256(raw).hexdigest(),pin)
            self.assertIs(P.factory_module(old),module)
            self.assertNotIn('royalty_read_policy',old)
            self.assertEqual(P.precheck_chain(old),module.parse_section(old))
            bindings=P.expected_bindings(old,1)
            self.assertNotIn('royaltyBalanceGas',bindings['helpers']['protocol_policy'])
            self.assertNotIn('ROYALTY_ALLOCATION_VERSION',bindings['helpers']['royalty_rewards'])
            self.assertEqual(bindings['helpers']['royalty_factory']['royaltyCodeHash'],module.SPEC.creation_hash)
        old=config('production.schema17.payload3.example.json')['chains'][0]
        old['factory_payload_version']=3;self.assertIs(P.factory_module(old),F3)
        # Exercise the repaired historical loader, not just its code-owned JSON.
        from tests_python.test_factory_payload4 import compiled as historical_compiled
        archived=historical_compiled()
        self.assertTrue(F4.verify_compiler_output(archived))
        with self.assertRaises(ValueError):F5.verify_compiler_output(archived)

    def test_five_selects_one_payload_and_adds_only_its_explicit_read_cap_binding(self):
        value=chain();self.assertIs(P.factory_module(value),F5)
        self.assertEqual(P.precheck_chain(value),F5.parse_section(value))
        bindings=P.expected_bindings(value,1)
        self.assertEqual(bindings['helpers']['royalty_factory']['royaltyCodeHash'],F5.SPEC.creation_hash)
        self.assertEqual(bindings['helpers']['protocol_policy']['royaltyBalanceGas'],50000)
        self.assertEqual(bindings['helpers']['royalty_rewards']['ROYALTY_ALLOCATION_VERSION'],2)
        self.assertEqual(bindings['helpers']['royalty_rewards']['ROYALTY_SETTLEMENT_VERSION'],4)
        gate=P.V.Gate(None);P.factory_code(gate,value,'chain',[])
        self.assertFalse(any(i['code'].startswith('royalty.read.') for i in gate.issues),gate.issues)
        changed=copy.deepcopy(value);changed['royalty_read_policy']['observed']['balance_gas']=50001
        gate=P.V.Gate(None);P.factory_code(gate,changed,'chain',[])
        self.assertIn('royalty.read.observation',{i['code'] for i in gate.issues})
        changed=copy.deepcopy(value);changed['protocol_policy']['gas']['revision']=2
        gate=P.V.Gate(None);P.factory_code(gate,changed,'chain',[])
        self.assertIn('royalty.read.revision',{i['code'] for i in gate.issues})
        changed=copy.deepcopy(value);target=addr(0xabc)
        changed['helpers']['protocol_policy']['address']=target
        changed['royalty_read_policy'].update(declared_policy(target),observed=declared_policy(target))
        changed['royalty_read_policy']['policy']='0x'+target[2:].upper()
        gate=P.V.Gate(None);P.factory_code(gate,changed,'chain',[])
        self.assertFalse(any(i['code'].startswith('royalty.read.') for i in gate.issues),gate.issues)

    def test_invalid_selector_mixed_payload_and_legacy_read_fields_fail_before_rpc(self):
        for bad in (True,False,None,5.0,'5',0,2,6,{},[]):
            value=chain();value['factory_payload_version']=bad;rpc=Mock()
            with self.subTest(value=repr(bad)):
                with self.assertRaises(ValueError):O.Observer(rpc,value)
                rpc.call.assert_not_called()
        for name in ('production.schema17.payload3.example.json','production.schema17.payload4.example.json'):
            old=config(name)['chains'][0]
            mixed=chain();mixed['factory_code']=copy.deepcopy(old['factory_code'])
            with self.assertRaises(ValueError):P.precheck_chain(mixed)
            old['royalty_read_policy']=copy.deepcopy(chain()['royalty_read_policy'])
            rpc=Mock()
            with self.assertRaises(ValueError):O.Observer(rpc,old)
            rpc.call.assert_not_called()
        missing=chain();del missing['royalty_read_policy']
        with self.assertRaises(ValueError):P.precheck_chain(missing)
        for field,bad in (('version',True),('version',2),('balance_gas',True),
                          ('balance_gas',9999),('gas_revision',True),('gas_revision',0),
                          ('fingerprint_scope','onchain_getter')):
            value=chain();value['royalty_read_policy'][field]=bad;rpc=Mock()
            with self.subTest(field=field,bad=bad):
                with self.assertRaises(ValueError):O.Observer(rpc,value)
                rpc.call.assert_not_called()

    def test_computed_fingerprint_has_explicit_scope_bounds_revision_and_independent_encoding(self):
        raw=D.keccak256(b'ZZZ_ROYALTY_BALANCE_READ_POLICY_V1')+bytes.fromhex(word(99)+word(50000)+word(1))
        self.assertEqual(R.fingerprint(addr(99),50000,1),h(raw))
        self.assertNotEqual(R.fingerprint(addr(99),50001,1),h(raw))
        self.assertNotEqual(R.fingerprint(addr(99),50000,2),h(raw))
        for cap in (True,'50000',9999,1000001):
            with self.subTest(cap=cap):
                with self.assertRaises(ValueError):R.fingerprint(addr(99),cap,1)
        for revision in (True,0,2**64):
            with self.subTest(revision=revision):
                with self.assertRaises(ValueError):R.fingerprint(addr(99),50000,revision)
        self.assertEqual(len(R.fingerprint(addr(99),10000,1)),66)
        self.assertEqual(len(R.fingerprint(addr(99),1000000,1)),66)

    def observer(self,cap_reply=50000,cap_error=False):
        value=chain();parts=actual_parts();calls=[]
        gas=[180000,500000,1000000,1]
        table={('0x'+D.keccak256(sig.encode()).hex()[:8]):(target,answer) for target,sig,answer in (
            (addr(99),'PROTOCOL_POLICY_VERSION()',word(1)),(addr(99),'access()',word(77)),
            (addr(77),'protocolPolicy()',word(99)),(addr(99),'gasPolicy()',''.join(word(n) for n in gas)),
            (addr(99),'gasFingerprint()',h(bytes.fromhex(word(99)+''.join(word(n) for n in gas)))[2:]),
            (addr(99),'royaltyBalanceGas()',word(cap_reply)),
            (addr(98),'ROYALTY_ALLOCATION_VERSION()',word(2)))}
        cap_selector='0x'+D.keccak256(b'royaltyBalanceGas()').hex()[:8]
        def call(method,params):
            calls.append((method,copy.deepcopy(params)))
            self.assertEqual(params[1],BLOCK)
            if method=='eth_getCode':return parts[(addr(800),addr(801)).index(params[0])]
            self.assertEqual(method,'eth_call');tx=params[0]
            expected,answer=table[tx['data']];self.assertEqual(tx['to'],expected)
            self.assertLessEqual(int(tx['gas'],16),O.O.MAX_GETTER_GAS)
            if cap_error and tx['data']==cap_selector:raise ValueError('synthetic completed cap read failure')
            return '0x'+answer
        rpc=Mock();rpc.call.side_effect=call
        observer=O.Observer(rpc,value,execution_price_version=1);observer.block=BLOCK
        return value,observer,calls

    def test_real_part_and_read_policy_observer_uses_one_anchor_and_actual_legacy_gas_hash(self):
        value,observer,calls=self.observer();observer.observe_chain_extension()
        self.assertEqual(observer.errors,[])
        self.assertEqual(len(calls),8)
        self.assertEqual(value['royalty_read_policy']['observed'],declared_policy())
        self.assertEqual(value['factory_code']['observed_creation_code_hash'],F5.SPEC.creation_hash)
        self.assertEqual(observer.typed(addr(98),'ROYALTY_ALLOCATION_VERSION',2),2)
        self.assertEqual(len(calls),9)

    def test_failed_or_out_of_bounds_cap_clears_stale_observation_and_never_adopts_declared_cap(self):
        for cap,error in ((50000,True),(1000001,False)):
            value,observer,calls=self.observer(cap,error)
            self.assertIsNotNone(value['royalty_read_policy']['observed'])
            observer.observe_chain_extension()
            self.assertIsNone(value['royalty_read_policy']['observed'])
            self.assertIn('royalty.read.unavailable',{i['code'] for i in observer.errors})
        value,observer,calls=self.observer(50001)
        observer.observe_chain_extension()
        self.assertEqual(value['royalty_read_policy']['observed']['balance_gas'],50001)
        self.assertEqual(value['royalty_read_policy']['balance_gas'],50000)
        self.assertIn('royalty.read.mismatch',{i['code'] for i in observer.errors})

    def test_fresh_five_template_remains_unapproved_and_unknown_cap_is_not_defaulted(self):
        value=config();result=P.validate(value,now=1795000000)
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertFalse(result['production_qualification_supported'])
        self.assertFalse(any(i['code']=='schema.keys' and i['path']=='chains[0]' for i in result['issues']))
        self.assertIsNone(value['chains'][0]['royalty_read_policy']['balance_gas'])
        self.assertIsNone(value['chains'][0]['royalty_read_policy']['observed'])
        self.assertIn('royalty.read.fingerprint',{i['code'] for i in result['issues']})
        self.assertTrue(all(row['address'] is None and row['observed_runtime_hash'] is None
            for row in value['chains'][0]['helpers'].values()))

    def test_optional_preseal_cap_call_is_exact_and_original_twelve_steps_stay_identical(self):
        with tempfile.TemporaryDirectory(prefix='popl-cap-plan-') as temporary:
            request=preseal_fixture.complete(Path(temporary));original=copy.deepcopy(request)
            baseline=PRE.prepare(request)
            self.assertFalse(baseline['optional_royalty_balance_policy']['requested'])
            self.assertEqual(baseline['optional_royalty_balance_policy']['calls'],[])
            request['royalty_balance_policy']={'balanceGas':'50000','reviewHash':'0x'+'cd'*32}
            result=PRE.prepare(request);section=result['optional_royalty_balance_policy']
            self.assertEqual(result['steps'],baseline['steps']);self.assertEqual(len(result['steps']),12)
            self.assertTrue(section['inputs_prepared']);self.assertFalse(section['setting_adopted'])
            self.assertTrue(result['configuration_inputs_complete'])
            self.assertEqual(len(section['calls']),1);call=section['calls'][0]
            self.assertEqual(call['from'],request['bootstrap'])
            self.assertEqual(call['to'],request['constructor_input']['planned_addresses']['protocol_policy'])
            self.assertEqual(call['value'],'0')
            self.assertEqual(call['signature'],'setRoyaltyBalanceGas(uint32,bytes32)')
            self.assertEqual(call['calldata'],'0x'+D.keccak256(b'setRoyaltyBalanceGas(uint32,bytes32)').hex()[:8]+word(50000)+'cd'*32)
            self.assertTrue(all(result[flag] is False for flag in PRE.FALSE_FLAGS))
            self.assertIsNone(result['seal_boundary_review']['seal_calldata'])
            del request['royalty_balance_policy'];self.assertEqual(request,original)

    def test_unknown_optional_cap_blocks_calldata_and_bounds_fail_before_artifact_reads(self):
        for setting in (None,{'balanceGas':None,'reviewHash':'0x'+'ab'*32},
                        {'balanceGas':'50000','reviewHash':None}):
            request=PRE.example();request['royalty_balance_policy']=setting
            result=PRE.prepare(request);row=result['optional_royalty_balance_policy']
            self.assertTrue(row['requested']);self.assertFalse(row['inputs_prepared'])
            self.assertFalse(result['configuration_inputs_complete'])
            self.assertIsNone(row['calls'][0]['calldata']);self.assertIsNone(row['calls'][0]['arguments'])
        for cap in ('9999','1000001',True,50000,'050000'):
            request=PRE.example();request['royalty_balance_policy']={'balanceGas':cap,'reviewHash':'0x'+'ab'*32}
            with self.subTest(cap=cap),patch.object(D,'Artifacts',side_effect=AssertionError('invalid inputs must precede artifacts')):
                with self.assertRaises(D.PlanError):PRE.prepare(request)

    def test_current_preseal_read_policy_check_uses_only_actual_abi_and_no_qualification(self):
        result=PRE.prepare(PRE.example())
        rows={r['id']:r for r in result['seal_boundary_review']['checks']}
        row=rows['royalty_balance_read_policy'];self.assertFalse(row['verified'])
        self.assertIsNone(row['assigned_target']);self.assertEqual(row['target_role'],'protocol_policy')
        _,obj,_=D.Artifacts().contract('ZZZProtocolPolicy')
        signatures={item['name']+'('+','.join(a['type'] for a in item['inputs'])+')'
            for item in obj['abi'] if item['type']=='function' and item['stateMutability'] in ('view','pure')}
        self.assertTrue(set(row['required_reads'])<=signatures)
        self.assertEqual(row['required_reads'],['royaltyBalanceGas()','gasPolicy()','gasFingerprint()'])
        self.assertIn('20M contribution budget with full20%',row['requirement'])
        profile=rows['royalty_allocation_profile']
        _,royalty,_=D.Artifacts().contract('ZZZRoyaltyRewards')
        getters={r['name']+'()' for r in royalty['abi'] if r['type']=='function' and not r['inputs']}
        self.assertTrue(set(profile['required_reads'])<=getters)
        self.assertFalse(profile['verified'])


if __name__=='__main__':unittest.main()
