"""Bounded factory-data authentication; fixtures never establish release approval."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops import factory_code_v2 as F, production_v11 as OLD, production_v12 as P
from zzz_ops import production_observer_v12 as O

ROOT=Path(__file__).resolve().parents[1]
def current():return json.loads((ROOT/'config/production.example.json').read_text())
def address(n):return '0x'+format(n,'040x')


class FactoryCodeProfileTests(unittest.TestCase):
    def test_current_template_is_explicit_unconfigured_and_not_authorized(self):
        config=current();self.assertEqual(config['schema_version'],14)
        self.assertEqual(len(P.HELPERS),18)
        section=F.parse_section(config['chains'][0])
        self.assertEqual(len(section['parts']),2)
        self.assertTrue(all(row['address'] is None for row in section['parts']))
        self.assertIsNone(section['review_evidence'])
        result=P.validate(config,now=1793880000)
        self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized'])
        self.assertIn('mint.opensea_unsupported',{x['code'] for x in result['issues']})

    def test_source_artifact_pins_fixed_format_and_current_complete_graph(self):
        self.assertEqual(F.SPEC.creation_length,25522)
        self.assertEqual(F.SPEC.creation_hash,OLD.ROYALTY_CREATION_CODE_HASH)
        self.assertEqual([x.runtime_length for x in F.SPEC.parts],[24576,952])
        self.assertEqual(len(F.SPEC.source_sha256),84)
        self.assertEqual(sum(x.data_length for x in F.SPEC.parts),F.SPEC.creation_length)

    def test_source_artifact_does_not_adopt_replaced_duplicate_or_nonfinite_content(self):
        original=F.ARTIFACT.read_bytes()
        for raw in (original.replace(b'25522',b'25523',1),b'{"schema":1,"schema":1}',b'{"x":NaN}',b' '*65537):
            with self.subTest(kind=len(raw)),tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'artifact.json';path.write_bytes(raw)
                with self.assertRaises(ValueError):F.load_artifact(path)

    def test_split_has_two_ordered_parts_even_when_second_is_empty(self):
        for data in (b'x',b'a'*24573,b'a'*24573+b'b'*949,b'a'*49146):
            parts=F.split_creation(data)
            self.assertEqual(len(parts),2)
            self.assertEqual(b''.join(x[3:] for x in parts),data)
            self.assertTrue(all(x.startswith(F.PREFIX) and len(x)<=24576 for x in parts))
        self.assertEqual(F.split_creation(b'x')[1],F.PREFIX)
        for data in (b'',b'x'*49147,'x',None):
            with self.subTest(data_type=type(data)),self.assertRaises(ValueError):F.split_creation(data)

    def test_section_rejects_wrong_missing_extra_and_boolean_identity(self):
        for mutation in (lambda s:s.pop('parts'),lambda s:s.update(extra=True),
                         lambda s:s.update(code_storage_version=True),lambda s:s.update(creation_code_length=True),
                         lambda s:s['parts'].reverse(),lambda s:s['parts'].append(s['parts'][0]),
                         lambda s:s['parts'][0].update(index=False),lambda s:s['parts'][0].update(runtime_hash='0x'+'0'*64)):
            chain=copy.deepcopy(current()['chains'][0]);mutation(chain['factory_code'])
            with self.assertRaises(ValueError):F.parse_section(chain)

    def test_bindings_include_source_pins_and_exact_declared_child_pointers(self):
        chain=current()['chains'][0]
        for i,row in enumerate(chain['factory_code']['parts']):row['address']=address(100+i)
        binding=P.expected_bindings(chain)['helpers']['royalty_factory']
        self.assertEqual(binding['CODE_STORAGE_VERSION'],2)
        self.assertEqual(binding['creationCodeLength'],F.SPEC.creation_length)
        for i,spec in enumerate(F.SPEC.parts):
            self.assertEqual(binding['part'+str(i)],address(100+i))
            self.assertEqual(binding['part'+str(i)+'CodeHash'],spec.runtime_hash)

    def test_historical_schema13_has_no_new_mandatory_section_or_bindings(self):
        old=json.loads((ROOT/'config/production.schema13.example.json').read_text())
        self.assertEqual(old['schema_version'],13)
        self.assertNotIn('factory_code',old['chains'][0])
        bindings=OLD.expected_bindings(old['chains'][0])['helpers']['royalty_factory']
        self.assertNotIn('part0',bindings);self.assertNotIn('CODE_STORAGE_VERSION',bindings)
        self.assertEqual(OLD.VERSIONS['schema_version'],13)
        with self.assertRaises(ValueError):P.precheck_chain(old['chains'][0])

    def test_old_or_malformed_profiles_stop_before_any_rpc(self):
        class NoRpc:
            def call(self,*args):raise AssertionError('No RPC expected')
        for version in (13,True,'14',None):
            config=current();config['schema_version']=version
            with self.subTest(version=version),self.assertRaises(ValueError):O.observe(config,NoRpc())
        config=current();config['chains'][0]['factory_code']['parts'][0]['index']=True
        with self.assertRaises(ValueError):O.observe(config,NoRpc())

    def small_spec(self):
        data=b'fixed constructor bytes'
        raw=(F.PREFIX+data[:9],F.PREFIX+data[9:])
        spec=F.Artifact(len(data),F._hash(data),tuple(F.Part(i,len(x)-3,len(x),F._hash(x)) for i,x in enumerate(raw)),())
        return raw,spec

    def test_runtime_authentication_reconstructs_order_and_never_adopts_bad_pins(self):
        raw,spec=self.small_spec()
        with patch.object(F,'SPEC',spec):
            rows,whole=F.verify_runtime_parts(['0x'+x.hex() for x in raw])
            self.assertEqual(whole['observed_creation_code_hash'],spec.creation_hash)
            self.assertEqual([x['observed_data_length'] for x in rows],[9,len(b'fixed constructor bytes')-9])
            for bad in ([raw[1],raw[0]],[raw[0],raw[0]],[raw[0][:-1],raw[1]],[b'\x00'*len(raw[0]),raw[1]]):
                with self.subTest(shape=[len(x) for x in bad]),self.assertRaises(ValueError):
                    F.verify_runtime_parts(['0x'+x.hex() for x in bad])
            with patch.object(F,'SPEC',F.Artifact(spec.creation_length,'0x'+'0'*64,spec.parts,())):
                with self.assertRaisesRegex(ValueError,'Reconstructed'):F.verify_runtime_parts(['0x'+x.hex() for x in raw])

    def test_actual_pins_reject_missing_oversized_and_nonhex_runtime_without_adoption(self):
        n=F.SPEC.parts[0].runtime_length
        for value in (None,'0x','0x'+'00'*(n+1),'0x'+'gg'*n,'0x'+'00'*n):
            with self.subTest(value_type=type(value)),self.assertRaises(ValueError):F.verify_runtime_parts([value,'0x'])
        for value in ([],[None],None):
            with self.assertRaises(ValueError):F.verify_runtime_parts(value)

    def test_prefix_only_second_part_is_present_authenticated_code(self):
        raw=F.split_creation(b'x')
        spec=F.Artifact(1,F._hash(b'x'),tuple(F.Part(i,len(x)-3,len(x),F._hash(x)) for i,x in enumerate(raw)),())
        with patch.object(F,'SPEC',spec):
            rows,_=F.verify_runtime_parts(['0x'+x.hex() for x in raw])
            self.assertEqual(rows[1]['observed_data_length'],0)
            self.assertEqual(rows[1]['observed_runtime_length'],3)
            with self.assertRaises(ValueError):F.verify_runtime_parts(['0x'+raw[0].hex(),'0x'])

    def observer(self):
        obj=object.__new__(O.Observer);obj.chain=current()['chains'][0];obj.errors=[]
        obj.block={'blockHash':'0x'+'a'*64,'requireCanonical':True}
        for i,row in enumerate(obj.chain['factory_code']['parts']):row['address']=address(100+i)
        return obj

    def test_observer_two_raw_reads_use_same_canonical_selector(self):
        obj=self.observer();calls=[]
        obj.request=lambda method,params:calls.append((method,params)) or '0xobserved'
        rows=[dict(observed_data_length=x.data_length,observed_runtime_length=x.runtime_length,
                   observed_runtime_hash=x.runtime_hash,observed_prefix='0x5f5ffd') for x in F.SPEC.parts]
        whole=dict(observed_creation_code_length=F.SPEC.creation_length,observed_creation_code_hash=F.SPEC.creation_hash)
        with patch.object(F,'verify_runtime_parts',return_value=(rows,whole)) as verify:obj.observe_chain_extension()
        self.assertEqual(calls,[('eth_getCode',[address(100),obj.block]),('eth_getCode',[address(101),obj.block])])
        self.assertEqual(verify.call_args.args[0],['0xobserved','0xobserved'])
        self.assertFalse(obj.errors)
        self.assertEqual(obj.chain['factory_code']['observed_creation_code_hash'],F.SPEC.creation_hash)

    def test_observer_clears_stale_success_when_rpc_or_byte_validation_fails(self):
        for fail_rpc in (False,True):
            obj=self.observer();section=obj.chain['factory_code']
            section['observed_creation_code_hash']=F.SPEC.creation_hash
            for row in section['parts']:row['observed_runtime_hash']=row['runtime_hash']
            def request(*_):
                if fail_rpc:raise RuntimeError('secret endpoint must not leak')
                return '0x'
            obj.request=request;obj.observe_chain_extension()
            self.assertIsNone(section['observed_creation_code_hash'])
            self.assertTrue(all(row['observed_runtime_hash'] is None for row in section['parts']))
            self.assertTrue(obj.errors);self.assertNotIn('secret',str(obj.errors))

    def test_observer_typed_factory_getters_keep_exact_abi_types(self):
        obj=self.observer();calls=[]
        values={'CODE_STORAGE_VERSION':2,'creationCodeLength':25522,'part0':100,'part1':101,
                'part0CodeHash':int(F.SPEC.parts[0].runtime_hash,16),'part1CodeHash':int(F.SPEC.parts[1].runtime_hash,16)}
        def read(target,signature):
            calls.append(signature);return [format(values[signature[:-2]],'064x')]
        obj.read=read
        for name,wanted in values.items():
            result=obj.typed(address(1),name,None)
            if name.startswith('part') and name.endswith('CodeHash'):self.assertEqual(result,'0x'+format(wanted,'064x'))
            elif name in ('part0','part1'):self.assertEqual(result,address(wanted))
            else:self.assertEqual(result,wanted)
        self.assertEqual(calls,[name+'()' for name in values])

    def test_data_aliases_and_missing_observations_fail_gate(self):
        from zzz_ops.production_v2 import Gate
        chain=current()['chains'][0];section=chain['factory_code']
        for row,spec in zip(section['parts'],F.SPEC.parts):
            row.update(address=address(spec.index+100),observed_data_length=spec.data_length,
                       observed_runtime_length=spec.runtime_length,observed_runtime_hash=spec.runtime_hash,observed_prefix='0x5f5ffd')
        section.update(observed_creation_code_length=F.SPEC.creation_length,observed_creation_code_hash=F.SPEC.creation_hash)
        with patch.object(P.V,'_bound_proof'):
            gate=Gate(None);P.factory_code(gate,chain,'chains[0]',[address(100)])
            self.assertIn('factory.code.alias',{x['code'] for x in gate.issues})
            section['parts'][0]['observed_runtime_length']=True
            gate=Gate(None);P.factory_code(gate,chain,'chains[0]',[])
            self.assertIn('factory.code.length',{x['code'] for x in gate.issues})

    def test_data_children_cannot_be_external_dependencies_tokens_or_mint_payee(self):
        for role,code in (('dependency','dependency.alias'),('token','token.duplicate'),('payee','mint.recipient')):
            config=current();chain=config['chains'][0]
            for i,row in enumerate(chain['factory_code']['parts']):row['address']=address(100+i)
            if role=='dependency':chain['dependencies']['pool_manager']['address']=address(100)
            if role=='token':chain['tokens'][1]['address']=address(100)
            if role=='payee':chain['protocol_policy']['sale']['recipient']=address(100)
            result=P.validate(config,now=1793880000)
            with self.subTest(role=role):self.assertIn(code,{x['code'] for x in result['issues']})

    def test_compiler_verifier_requires_exact_linked_creation_artifact(self):
        for value in ({},None,{'contracts':{'src/ZZZRoyaltyRewards.sol':{'ZZZRoyaltyRewards':{'evm':{'bytecode':{'object':'__$unlinked$__'}}}}}}):
            with self.assertRaises(ValueError):F.verify_compiler_output(value)


if __name__=='__main__':unittest.main()
