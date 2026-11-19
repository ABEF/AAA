"""Current F6 and exact historical F5 controls; no RPC or EVM qualification."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock
from zzz_ops import factory_code_v3 as F3,factory_code_v4 as F4,factory_code_v5 as F5,factory_code_v6 as F6
from zzz_ops import production_v15 as P,production_observer_v15 as O
from zzz_ops import royalty_read_policy as R,deployment_plan as D,preseal_plan as PRE
from tests_python.factory_payload_archive import archived

ROOT=Path(__file__).resolve().parents[1]
PROFILE='activation-final-six-20261118'
BLOCK={'blockHash':'0x'+'ab'*32,'requireCanonical':True}
HISTORICAL={
 'zzz_ops/factory_code_v5.py':'3e41c39666784e514d35a53e6ed7996b0bd3522126d22c55dcf63dfc943dfb46',
 'config/factory-code-storage-v5.json':'d3273a94c8ffa6347bedec98947d04644a9cc3e6a156ebeceafc3d2ad3c3fd20',
 'config/production.schema17.payload5.example.json':'3469640a7ec586dad0f1037620c2ce4c02441103024d2019cafd19b0adb4366d'}
def addr(n):return '0x'+f'{n:040x}'
def word(n):return f'{n:064x}'
def config(name='production.example.json'):return json.loads((ROOT/'config'/name).read_bytes())
def policy(cap=50000,revision=1):return dict(version=1,policy=addr(99),balance_gas=cap,gas_revision=revision,
 fingerprint=R.fingerprint(addr(99),cap,revision),fingerprint_scope=R.SCOPE)

def chain6():
 value=config()['chains'][0]
 value['modules']['access']['address']=addr(77);value['helpers']['protocol_policy']['address']=addr(99)
 value['helpers']['royalty_rewards']['address']=addr(98);value['helpers']['activation_assets']['bindings']['zzz']=addr(700)
 value['reward_assets'].update(asset_count=2,observed_asset_count=2,assets=[dict(address=P.BASE.ZERO),dict(address=addr(700))])
 value['royalty_read_policy'].update(policy(),observed=policy());value['protocol_policy']['gas']['revision']=1
 for row,part in zip(value['factory_code']['parts'],F6.SPEC.parts):
  row.update(address=addr(800+part.index),observed_data_length=part.data_length,observed_runtime_length=part.runtime_length,
   observed_runtime_hash=part.runtime_hash,observed_prefix='0x5f5ffd')
 value['factory_code'].update(observed_creation_code_length=F6.SPEC.creation_length,observed_creation_code_hash=F6.SPEC.creation_hash)
 return value

class FactoryPayload6Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if F6.SPEC is None:raise AssertionError('Generate source-owned F6 pins only after final normal admission before selecting these tests')
  cls.current=D.Artifacts();cls.previous=archived('activation-gas-20261118')

 def test_current_full_normal_100_sources_48_gates_and_corrupt_source_control(self):
  self.assertEqual(D.DEFAULT_BUILD_PROFILE,PROFILE);self.assertEqual(self.current.profile,PROFILE)
  self.assertEqual(len(self.current.input['sources']),100);self.assertEqual(len(self.current.source_pins),100)
  self.assertEqual(sum(n.startswith('src/')for n in self.current.source_pins),61)
  self.current.check_sources();spec=D.trusted_build(PROFILE)
  gates=json.loads((ROOT/spec['directory']/spec['gates']).read_bytes())['gates'];self.assertEqual(len(gates),48)
  for gate in gates:
   with self.subTest(contract=gate['name']):
    obj=self.current.output['contracts'][gate['path']][gate['name']]['evm'];rt=len(obj['deployedBytecode']['object'])//2;cr=len(obj['bytecode']['object'])//2
    self.assertEqual((rt,cr),(gate['runtime'],gate['creation']));self.assertLessEqual(rt,D.LIMITS['runtime_bytes']);self.assertLessEqual(cr+gate['minimum_args'],D.LIMITS['full_initcode_bytes'])
  changed=copy.copy(self.current);changed.source_pins=dict(self.current.source_pins);changed.source_pins['src/libraries/ExactLPAllocation.sol']='0'*64
  with self.assertRaisesRegex(D.PlanError,'source_changed'):changed.check_sources()

 def test_actual_payload6_parts_are_current_and_reject_every_historical_identity(self):
  output=self.current.output;self.assertTrue(F6.verify_compiler_output(output))
  code=bytes.fromhex(output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object'])
  parts=['0x'+part.hex()for part in F6.split_creation(code)];self.assertEqual(len(parts),2)
  observed,whole=F6.verify_runtime_parts(parts)
  self.assertEqual(whole['observed_creation_code_hash'],F6.SPEC.creation_hash);self.assertEqual(whole['observed_creation_code_length'],len(code))
  self.assertEqual([r['observed_runtime_length']for r in observed],[r.runtime_length for r in F6.SPEC.parts])
  for old in(F3,F4,F5):
   with self.subTest(old=old.__name__):
    self.assertNotEqual(F6.SPEC.creation_hash,old.SPEC.creation_hash)
    with self.assertRaises(ValueError):old.verify_runtime_parts(parts)
    with self.assertRaises(ValueError):old.verify_compiler_output(output)
  corrupted=list(parts);corrupted[0]=corrupted[0][:-2]+('00'if corrupted[0][-2:]!='00'else'01')
  with self.assertRaises(ValueError):F6.verify_runtime_parts(corrupted)

 def test_historical_five_stays_exact_and_never_becomes_current_preparation(self):
  for name,pin in HISTORICAL.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),pin)
  old=config('production.schema17.payload5.example.json')['chains'][0]
  self.assertEqual(old['factory_payload_version'],5);self.assertIs(P.factory_module(old),F5);self.assertEqual(P.precheck_chain(old),F5.parse_section(old))
  self.assertTrue(F5.verify_compiler_output(self.previous.output))
  with self.assertRaises(ValueError):F6.verify_compiler_output(self.previous.output)
  with self.assertRaisesRegex(D.PlanError,'source_changed'):D.Artifacts(build_profile='activation-gas-20261118')
  self.assertEqual(len(self.previous.source_pins),100);self.assertEqual(len(self.previous.gates),48)

 def test_six_policy_bindings_unknown_selectors_and_mixed_parts_fail_before_rpc(self):
  value=chain6();self.assertIs(P.factory_module(value),F6);self.assertEqual(P.precheck_chain(value),F6.parse_section(value))
  expected=P.expected_bindings(value,1);self.assertEqual(expected['helpers']['royalty_factory']['royaltyCodeHash'],F6.SPEC.creation_hash)
  self.assertEqual(expected['helpers']['protocol_policy']['royaltyBalanceGas'],50000)
  self.assertEqual(expected['helpers']['royalty_rewards']['ROYALTY_ALLOCATION_VERSION'],2)
  for bad in(True,None,'6',6.0,0,2,7,[],{}):
   with self.subTest(selector=repr(bad)):
    changed=copy.deepcopy(value);changed['factory_payload_version']=bad;rpc=Mock()
    with self.assertRaises(ValueError):O.Observer(rpc,changed)
    rpc.call.assert_not_called()
  for selector,name in((3,'production.schema17.payload3.example.json'),(4,'production.schema17.payload4.example.json'),(5,'production.schema17.payload5.example.json')):
   with self.subTest(historical=selector):
    old=config(name)['chains'][0];changed=copy.deepcopy(value);changed['factory_code']=old['factory_code'];rpc=Mock()
    with self.assertRaises(ValueError):O.Observer(rpc,changed)
    rpc.call.assert_not_called()
    old['factory_payload_version']=6
    with self.assertRaises(ValueError):P.precheck_chain(old)
  for field,bad in(('balance_gas',True),('balance_gas',9999),('balance_gas',1000001),('version',2),('gas_revision',0),('fingerprint_scope','guessed')):
   with self.subTest(policy_field=field,invalid=bad):
    changed=copy.deepcopy(value);changed['royalty_read_policy'][field]=bad;rpc=Mock()
    with self.assertRaises(ValueError):O.Observer(rpc,changed)
    rpc.call.assert_not_called()

 def observer(self,cap=50000,fail=False):
  value=chain6();output=self.current.output;code=bytes.fromhex(output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object']);parts=['0x'+r.hex()for r in F6.split_creation(code)]
  gas=[180000,500000,1000000,1];hash_='0x'+D.keccak256(bytes.fromhex(word(99)+''.join(word(n)for n in gas))).hex()
  table={'0x'+D.keccak256(sig.encode()).hex()[:8]:(target,answer)for target,sig,answer in(
   (addr(99),'PROTOCOL_POLICY_VERSION()',word(1)),(addr(99),'access()',word(77)),(addr(77),'protocolPolicy()',word(99)),
   (addr(99),'gasPolicy()',''.join(word(n)for n in gas)),(addr(99),'gasFingerprint()',hash_[2:]),(addr(99),'royaltyBalanceGas()',word(cap)))}
  cap_selector='0x'+D.keccak256(b'royaltyBalanceGas()').hex()[:8];calls=[]
  def call(method,params):
   calls.append((method,copy.deepcopy(params)));self.assertEqual(params[1],BLOCK)
   if method=='eth_getCode':return parts[(addr(800),addr(801)).index(params[0])]
   self.assertEqual(method,'eth_call');tx=params[0];target,answer=table[tx['data']];self.assertEqual(tx['to'],target)
   self.assertLessEqual(int(tx['gas'],16),O.O.MAX_GETTER_GAS)
   if fail and tx['data']==cap_selector:raise ValueError('controlled bounded policy read fault')
   return '0x'+answer
  rpc=Mock();rpc.call.side_effect=call;observer=O.Observer(rpc,value,execution_price_version=1);observer.block=BLOCK
  return value,observer,calls

 def test_six_observer_checks_actual_parts_and_cap_at_one_anchor_and_isolates_failure(self):
  value,observer,calls=self.observer();observer.observe_chain_extension();self.assertEqual(observer.errors,[]);self.assertEqual(len(calls),8)
  self.assertEqual(value['royalty_read_policy']['observed'],policy());self.assertEqual(value['factory_code']['observed_creation_code_hash'],F6.SPEC.creation_hash)
  value,observer,calls=self.observer(fail=True);observer.observe_chain_extension();self.assertIsNone(value['royalty_read_policy']['observed'])
  self.assertIn('royalty.read.unavailable',{r['code']for r in observer.errors})
  value,observer,calls=self.observer(cap=50001);observer.observe_chain_extension();self.assertEqual(value['royalty_read_policy']['balance_gas'],50000)
  self.assertEqual(value['royalty_read_policy']['observed']['balance_gas'],50001);self.assertIn('royalty.read.mismatch',{r['code']for r in observer.errors})

 def test_fresh_six_remains_unknown_unapproved_and_preseal_unknown_inputs_stay_blocked(self):
  value=config();self.assertEqual(value['chains'][0]['factory_payload_version'],6)
  result=P.validate(value,now=1795000000);self.assertFalse(result['ready']);self.assertFalse(result['deployment_authorized']);self.assertFalse(result['production_qualification_supported'])
  chain=value['chains'][0];self.assertIsNone(chain['royalty_read_policy']['balance_gas']);self.assertIsNone(chain['royalty_read_policy']['observed'])
  self.assertTrue(all(row['address']is None and row['observed_runtime_hash']is None for group in('modules','helpers')for row in chain[group].values()))
  self.assertTrue(all(row['address']is None and row['observed_runtime_hash']is None for row in chain['factory_code']['parts']))
  request=PRE.example();prepared=PRE.prepare(request);self.assertEqual(prepared['build_profile'],PROFILE)
  self.assertFalse(prepared['configuration_inputs_complete']);self.assertFalse(prepared['seal_prepared']);self.assertFalse(prepared['ready_for_submission'])
  checks={row['id']:row for row in prepared['seal_boundary_review']['checks']};read_policy=checks['royalty_balance_read_policy']
  self.assertFalse(read_policy['verified']);self.assertIsNone(read_policy['assigned_target'])
  self.assertEqual(read_policy['required_reads'],['royaltyBalanceGas()','gasPolicy()','gasFingerprint()'])
  _,policy_obj,_=self.current.contract('ZZZProtocolPolicy')
  getters={row['name']+'('+','.join(arg['type']for arg in row['inputs'])+')'for row in policy_obj['abi']if row['type']=='function'and row['stateMutability']in('view','pure')}
  self.assertTrue(set(read_policy['required_reads'])<=getters);self.assertIn('reviewed configured contribution budget with full20%',read_policy['requirement'])
  _,royalty_obj,_=self.current.contract('ZZZRoyaltyRewards')
  royalty_getters={row['name']+'()'for row in royalty_obj['abi']if row['type']=='function'and not row['inputs']}
  self.assertTrue(set(checks['royalty_allocation_profile']['required_reads'])<=royalty_getters);self.assertFalse(checks['royalty_allocation_profile']['verified'])
  for family in prepared['steps']:
   if not family['inputs_prepared']:
    for call in family['calls']:self.assertIsNone(call['calldata'])
  request['royalty_balance_policy']={'balanceGas':None,'reviewHash':'0x'+'ab'*32}
  prepared=PRE.prepare(request);self.assertFalse(prepared['optional_royalty_balance_policy']['inputs_prepared'])
  self.assertIsNone(prepared['optional_royalty_balance_policy']['calls'][0]['calldata'])

 def test_payload6_artifact_pin_rejects_mutation_or_duplicate_keys(self):
  raw=F6.ARTIFACT.read_bytes();value=json.loads(raw);value['creation_code_hash']='0x'+'00'*32
  with tempfile.TemporaryDirectory(prefix='popl-f6-artifact-')as temporary:
   path=Path(temporary)/'artifact.json';path.write_text(json.dumps(value),encoding='utf-8')
   with self.assertRaises(ValueError):F6.load_artifact(path)
   path.write_text('{"schema":1,"schema":1}',encoding='utf-8')
   with self.assertRaisesRegex(ValueError,'Duplicate'):F6.load_artifact(path)

if __name__=='__main__':unittest.main()
