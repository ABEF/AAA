"""Explicit payload4 admission; actual trusted bytecode, synthetic read-only RPC.

Only these new methods are selected. No provider, signing, deployment or release
approval is inferred from source-owned bytes or a coherent unsigned inventory.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import Mock,patch

from zzz_ops import factory_code_v3 as F3,factory_code_v4 as F4
from zzz_ops import production_v14 as OLD,production_v15 as P
from zzz_ops import production_observer_v15 as O
from zzz_ops import deployment_plan as D,preseal_plan as PRESEAL
from zzz_ops.deployment_plan import Artifacts

ROOT=Path(__file__).resolve().parents[1]
BLOCK={'blockHash':'0x'+'ab'*32,'requireCanonical':True}


def addr(n):return '0x'+f'{n:040x}'
def config():return json.loads((ROOT/'config/production.example.json').read_text())
def historical():return json.loads((ROOT/'config/production.schema17.payload3.example.json').read_text())


def compiled():
    """Actual accepted compiler artifact, never guessed/mutated creation bytes."""
    return Artifacts(ROOT).output


def runtime_parts():
    output=compiled();F4.verify_compiler_output(output)
    code=bytes.fromhex(output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
    return ['0x'+value.hex() for value in F4.split_creation(code)]


def observed_chain():
    chain=config()['chains'][0]
    chain['helpers']['activation_assets']['bindings']['zzz']=addr(700)
    chain['reward_assets'].update(asset_count=2,observed_asset_count=2,
        assets=[dict(address=P.BASE.ZERO),dict(address=addr(700))])
    section=chain['factory_code']
    for row,part in zip(section['parts'],F4.SPEC.parts):
        row.update(address=addr(800+part.index),observed_data_length=part.data_length,
            observed_runtime_length=part.runtime_length,observed_runtime_hash=part.runtime_hash,
            observed_prefix='0x5f5ffd')
    section.update(observed_creation_code_length=F4.SPEC.creation_length,
        observed_creation_code_hash=F4.SPEC.creation_hash)
    return chain


class FactoryPayload4Tests(unittest.TestCase):
    def test_payload4_matches_actual_trusted_normal_creation_and_exact_parts(self):
        output=compiled();self.assertTrue(F4.verify_compiler_output(output))
        parts=runtime_parts();seen,whole=F4.verify_runtime_parts(parts)
        self.assertEqual(whole['observed_creation_code_hash'],F4.SPEC.creation_hash)
        self.assertEqual(whole['observed_creation_code_length'],F4.SPEC.creation_length)
        self.assertEqual([row['observed_data_length'] for row in seen],
                         [p.data_length for p in F4.SPEC.parts])
        self.assertNotEqual(F4.SPEC.creation_hash,F3.SPEC.creation_hash)
        with self.assertRaises(ValueError):F3.verify_runtime_parts(parts)
        with self.assertRaises(ValueError):F3.verify_compiler_output(output)

    def test_historical_archive_and_payload3_are_not_relabelled(self):
        raw=(ROOT/'config/production.schema17.payload3.example.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
            '2c7fda19ebcffd4f302b1945c3853716f7979c0153757f0a79fc0377390015ca')
        old=historical()['chains'][0]
        self.assertNotIn('factory_payload_version',old)
        self.assertIs(P.factory_module(old),F3)
        self.assertEqual(F3.ARTIFACT_CANONICAL_SHA256,
            'a887d3d80cf9355ff69d34df8bdb75b38f272bd8fe6b885798652509ddfaba29')
        self.assertEqual(OLD.ROYALTY_CREATION_CODE_HASH,F3.SPEC.creation_hash)
        self.assertEqual(P.ROYALTY_CREATION_CODE_HASH,F3.SPEC.creation_hash) # Historical default constant only.
        self.assertEqual(P.precheck_chain(old),F3.parse_section(old))

    def test_omission_and_explicit3_preserve_the_exact_historical_bindings(self):
        chain=historical()['chains'][0]
        omitted=P.expected_bindings(chain,1)
        chain['factory_payload_version']=3
        self.assertIs(P.factory_module(chain),F3)
        self.assertEqual(P.expected_bindings(chain,1),omitted)
        self.assertEqual(omitted['helpers']['royalty_factory']['royaltyCodeHash'],F3.SPEC.creation_hash)
        self.assertEqual(omitted['modules']['canonical']['SCHEMA'],P.SCHEMA_HASH)
        self.assertEqual(omitted['helpers']['seadrop_mint']['MINT_INTEGRATION_VERSION'],1)

    def test_explicit4_drives_precheck_bindings_and_template_identity_consistently(self):
        chain=config()['chains'][0];self.assertIs(P.factory_module(chain),F4)
        self.assertEqual(P.precheck_chain(chain),F4.parse_section(chain))
        bindings=P.expected_bindings(chain,1)['helpers']['royalty_factory']
        wanted=dict(CODE_STORAGE_VERSION=2,royaltyCodeHash=F4.SPEC.creation_hash,
            creationCodeLength=F4.SPEC.creation_length,part0=chain['factory_code']['parts'][0]['address'],
            part1=chain['factory_code']['parts'][1]['address'],part0CodeHash=F4.SPEC.parts[0].runtime_hash,
            part1CodeHash=F4.SPEC.parts[1].runtime_hash)
        self.assertEqual({key:bindings[key] for key in wanted},wanted)
        declared=chain['helpers']['royalty_factory']['bindings']
        self.assertTrue(all(declared[key]==value for key,value in wanted.items()))
        self.assertEqual((P.VERSIONS['schema_version'],len(P.HELPERS)),(17,20))
        observed=observed_chain();observed['modules']['access']['address']=addr(77)
        exact=P.expected_bindings(observed,1)['helpers']['royalty_factory']
        record=dict(bindings=copy.deepcopy(exact),observed_bindings=copy.deepcopy(exact))
        gate=P.V.Gate(None);P.V._bindings(gate,record,exact,'factory',helper=True)
        self.assertEqual(gate.issues,[])
        record['bindings']['royaltyCodeHash']=F3.SPEC.creation_hash
        record['observed_bindings']['royaltyCodeHash']=F3.SPEC.creation_hash
        gate=P.V.Gate(None);P.V._bindings(gate,record,exact,'factory',helper=True)
        self.assertEqual({i['code'] for i in gate.issues},{'binding.intended','binding.observed'})

    def test_bool_unknown_and_mixed_payloads_reject_before_any_observer_read(self):
        for value in (None,True,False,'4',4.0,0,2,5,{},[]):
            chain=config()['chains'][0];chain['factory_payload_version']=value;rpc=Mock()
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):P.precheck_chain(chain)
                with self.assertRaises(ValueError):P.expected_bindings(chain,1)
                with self.assertRaises(ValueError):O.Observer(rpc,chain)
                rpc.assert_not_called();rpc.call.assert_not_called()
        for current,other in ((config(),historical()),(historical(),config())):
            chain=current['chains'][0]
            chain['factory_code']=copy.deepcopy(other['chains'][0]['factory_code'])
            with self.assertRaises(ValueError):P.precheck_chain(chain)

    def test_single_changed_creation_or_part_identity_cannot_mix_payloads(self):
        chain=config()['chains'][0]
        for mutate in (
            lambda c:c['factory_code'].update(creation_code_hash=F3.SPEC.creation_hash),
            lambda c:c['factory_code'].update(creation_code_length=F3.SPEC.creation_length),
            lambda c:c['factory_code']['parts'][0].update(runtime_hash=F3.SPEC.parts[0].runtime_hash),
            lambda c:c['factory_code']['parts'][1].update(runtime_length=F3.SPEC.parts[1].runtime_length)):
            changed=copy.deepcopy(chain);mutate(changed)
            with self.assertRaises(ValueError):P.precheck_chain(changed)

    def test_actual_factory_gate_checks_selected_observations_and_keeps_lp_assets_fixed(self):
        chain=observed_chain();g=P.V.Gate(None)
        self.assertEqual(P.factory_code(g,chain,'chain',[]),[addr(800),addr(801)])
        self.assertFalse(any(i['code'].startswith('factory.code.') or i['code']=='lp.assets.fixed' for i in g.issues))
        changed=copy.deepcopy(chain);changed['factory_code']['parts'][1]['observed_runtime_hash']=F3.SPEC.parts[1].runtime_hash
        g=P.V.Gate(None);P.factory_code(g,changed,'chain',[])
        self.assertIn('factory.code.runtime',{i['code'] for i in g.issues})
        changed=copy.deepcopy(chain);changed['reward_assets']['assets'].append(dict(address=addr(701)))
        g=P.V.Gate(None);P.factory_code(g,changed,'chain',[])
        self.assertIn('lp.assets.fixed',{i['code'] for i in g.issues})

    def observer(self,*,corrupt=False):
        chain=observed_chain();parts=runtime_parts();calls=[]
        if corrupt:parts[1]=parts[1][:-2]+('00' if parts[1][-2:]!='00' else '01')
        def call(method,params):
            calls.append((method,copy.deepcopy(params)))
            self.assertEqual(method,'eth_getCode');self.assertEqual(params[1],BLOCK)
            self.assertIn(params[0],(addr(800),addr(801)))
            return parts[(addr(800),addr(801)).index(params[0])]
        rpc=Mock();rpc.call.side_effect=call
        observer=O.Observer(rpc,chain,execution_price_version=1);observer.block=BLOCK
        return chain,observer,calls

    def test_actual_observer_uses_both_selected_parts_at_one_canonical_hash(self):
        chain,observer,calls=self.observer();observer.observe_chain_extension()
        self.assertEqual(observer.errors,[]);self.assertEqual(len(calls),2)
        self.assertEqual([args[0] for _,args in calls],[addr(800),addr(801)])
        self.assertEqual(chain['factory_code']['observed_creation_code_hash'],F4.SPEC.creation_hash)
        self.assertEqual(chain['factory_code']['observed_creation_code_length'],F4.SPEC.creation_length)
        self.assertTrue(all(row['observed_runtime_hash']==part.runtime_hash
            for row,part in zip(chain['factory_code']['parts'],F4.SPEC.parts)))

    def test_observer_failure_clears_old_positive_observations_without_accepting_new_bytes(self):
        chain,observer,calls=self.observer(corrupt=True);observer.observe_chain_extension()
        self.assertEqual(len(calls),2)
        self.assertIn('factory.code.mismatch',{i['code'] for i in observer.errors})
        self.assertIsNone(chain['factory_code']['observed_creation_code_hash'])
        self.assertIsNone(chain['factory_code']['observed_creation_code_length'])
        for row in chain['factory_code']['parts']:
            for key in ('observed_data_length','observed_runtime_length','observed_runtime_hash','observed_prefix'):
                self.assertIsNone(row[key])

    def test_observe_frontdoor_uses_selected_precheck_bindings_and_constructor(self):
        current=config();rpc=Mock();seen=[]
        def run(_config,_rpc,*,profile,observer_class):
            chain=_config['chains'][0];self.assertIs(profile.factory_module(chain),F4)
            self.assertEqual(profile.expected_bindings(chain)['helpers']['royalty_factory']['royaltyCodeHash'],F4.SPEC.creation_hash)
            instance=observer_class(_rpc,chain)
            self.assertIs(instance._factory_code_module,F4);seen.append(instance)
            return {'scope':'outer observation deliberately mocked'}
        with patch.object(O.BASE,'_observe',side_effect=run) as outer:
            self.assertEqual(O.observe(current,rpc),{'scope':'outer observation deliberately mocked'})
        outer.assert_called_once();self.assertEqual(len(seen),1);rpc.call.assert_not_called()

    def test_fresh_gate_keeps_all_approval_flags_false_and_old_schema_rejects_new_field(self):
        current=config();result=P.validate(current,now=1794930000)
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertFalse(result['production_qualification_supported'])
        self.assertFalse(any(i['code']=='schema.keys' and i['path']=='chains[0]' for i in result['issues']))
        self.assertTrue(all(row['address'] is None and row['observed_runtime_hash'] is None
            for row in current['chains'][0]['helpers'].values()))
        old=json.loads((ROOT/'config/production.schema16.example.json').read_text())
        old['chains'][0]['factory_payload_version']=4
        blocked=OLD.validate(old,now=1794930000)
        self.assertTrue(any(i['code']=='schema.keys' and i['path']=='chains[0]' for i in blocked['issues']))
        # Exercise the real new-default constructor→pre-seal composition too;
        # unknown inputs must not become executable configuration or seal calls.
        preview=PRESEAL.prepare(PRESEAL.example())
        self.assertEqual(preview['build_profile'],D.DEFAULT_BUILD_PROFILE)
        self.assertEqual(preview['constructor_review']['accepted_build']['profile'],D.DEFAULT_BUILD_PROFILE)
        self.assertFalse(preview['configuration_inputs_complete'])
        self.assertTrue(all(preview[key] is False for key in PRESEAL.FALSE_FLAGS))
        self.assertIsNone(preview['seal_boundary_review']['seal_calldata'])
        self.assertTrue(all(call['calldata'] is None for step in preview['steps'] for call in step['calls']))
        with patch.object(D,'Artifacts',side_effect=AssertionError('Historical selection must fail before artifact reads')):
            with self.assertRaisesRegex(D.PlanError,'preseal_current_build_required'):
                PRESEAL.prepare(PRESEAL.example(),build_profile='seal-boundaries-20261117')


if __name__=='__main__':unittest.main()
