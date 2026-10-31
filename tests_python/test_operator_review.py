"""Offline review preparation, not RPC simulation or execution qualification."""
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr,redirect_stdout
from unittest.mock import patch

from zzz_ops import operator_review as O

ZERO='0x'+'0'*40
H='0x'+'1'*64


def address(n):return '0x'+f'{n:040x}'


class OperatorReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=O.Catalog()

    def request(self,contract='ZZZPortfolioPolicy',function='setMode'):
        fn=next(f for c in self.catalog.data['contracts'] if c['name']==contract
            for f in c['functions'] if f['name']==function)
        return dict(schema=1,profile=O.PROFILE,reference_sha256=self.catalog.reference_sha256,
            source_snapshot_sha256=self.catalog.source_snapshot_sha256,
            chain=dict(id='4663',controller=address(1),governance=address(2),target=address(3),target_runtime_keccak256=H),
            snapshot=dict(block_number='123456',block_hash=H,timestamp='1793448000'),
            contract=contract,signature=fn['signature'],arguments=dict(pool=H,next=True,reviewed=O.MARKER),
            review_notes_sha256='2'*64,evidence_sha256=['3'*64])

    def parking(self):
        req=self.request('ZZZMigration','closeResidual')
        req['arguments']=dict(r=dict(bucketId=str(2**256-1),poolId=H,lpTokenId='9',totalShares=str(10**55),
            depositUSD=str(10**38),custodyEpoch='5',nonce='6',token0=ZERO,token1=address(7),
            minimum0='1000000000000000000',minimum1='0',deadline='1793448300',reviewHash=O.MARKER,portfolioHash=H))
        return req

    def emergency(self):
        req=self.request('ZZZMigration','emergencyRebalance')
        req['arguments']=dict(request=dict(bucket='7',custodyHash=H,checks='14',lower='-887000',upper='887000',
            swapPool='0x'+'0'*64,zeroForOne=False,amountIn='0',minimumOut='0',minimumLiquidity='1',
            deadline='1793448300',reviewHash=O.MARKER))
        return req

    def test_real_closed_reference_and_profile_have_no_deployment_claim(self):
        identity=self.catalog.identity()
        self.assertEqual(O.PROFILE,identity['profile'])
        self.assertGreater(len(self.catalog.data['source_snapshot']['source_sha256']),40)
        for key in ('ready_for_submission','simulation_performed','onchain_snapshot_verified',
                'target_runtime_verified','authority_verified','operational_guards_verified'):
            self.assertIs(False,identity['boundaries'][key])

    def test_canonical_hash_and_self_reference_preserve_exact_tuple_order(self):
        req=self.parking();artifact=self.catalog.prepare(req)
        wanted='0x'+hashlib.sha256(O.DOMAIN+O.canonical(req)).hexdigest()
        self.assertEqual(wanted,artifact['review_hash'])
        self.assertEqual(O.MARKER,artifact['manifest']['arguments']['r']['reviewHash'])
        ordered=artifact['explorer']['arguments'][0]
        self.assertEqual([str(2**256-1),H,'9',str(10**55),str(10**38),'5','6',ZERO,address(7),
            '1000000000000000000','0','1793448300',wanted,H],ordered)
        self.assertTrue(self.catalog.check(artifact)['artifact_matches'])
        self.assertFalse(artifact['boundaries']['review_hash_is_custody_or_portfolio_fingerprint'])

    def test_object_key_order_is_irrelevant_but_every_reviewed_binding_changes_hash(self):
        req=self.request();first=self.catalog.prepare(req)
        reversed_request=dict(reversed(list(req.items())))
        self.assertEqual(first,self.catalog.prepare(reversed_request))
        for target,key,value in (('chain','id','46630'),('chain','target',address(4)),
                ('chain','governance',address(5)),('chain','target_runtime_keccak256','0x'+'4'*64),
                ('snapshot','block_hash','0x'+'5'*64),('arguments','next',False)):
            bad=copy.deepcopy(req);bad[target][key]=value
            with self.subTest(target=target,key=key):self.assertNotEqual(first['review_hash'],self.catalog.prepare(bad)['review_hash'])

    def test_signed_emergency_ticks_and_large_units_remain_exact_strings(self):
        artifact=self.catalog.prepare(self.emergency());args=artifact['explorer']['arguments'][0]
        self.assertEqual('-887000',args[3]);self.assertEqual('887000',args[4]);self.assertEqual('14',args[2])
        self.assertIs(False,args[6]);self.assertEqual('1',args[9])
        for value in (True,1,1.5,'1e18','01','-0','+1','-1',str(2**128)):
            req=self.parking();req['arguments']['r']['minimum0']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.catalog.prepare(req)
        for value in ('8388608','-8388609',False,50):
            req=self.emergency();req['arguments']['request']['lower']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.catalog.prepare(req)

    def test_booleans_addresses_bytes_markers_and_nested_shape_are_strict(self):
        changes=[('next',1),('next','true'),('pool',O.MARKER),('pool','0x'+'G'*64),
            ('pool','0x1234'),('reviewed',H)]
        for key,value in changes:
            req=self.request();req['arguments'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.catalog.prepare(req)
        req=self.parking();req['arguments']['r']['token0']=O.MARKER
        with self.assertRaises(ValueError):self.catalog.prepare(req)
        req=self.parking();req['arguments']['r']['token1']='0x'+'A'*40
        with self.assertRaises(ValueError):self.catalog.prepare(req)
        req=self.parking();req['arguments']['r']['missing']=False
        with self.assertRaises(ValueError):self.catalog.prepare(req)
        req=self.parking();del req['arguments']['r']['portfolioHash']
        with self.assertRaises(ValueError):self.catalog.prepare(req)

    def test_hashless_pause_is_only_an_offline_audit_record(self):
        req=self.request('ZZZAccessController','setPaused');req['arguments']={'state':True}
        artifact=self.catalog.prepare(req)
        self.assertEqual([True],artifact['explorer']['arguments'])
        self.assertFalse(artifact['boundaries']['contract_validates_review_preimage'])
        self.assertFalse(artifact['boundaries']['ready_for_submission'])

    def test_supplied_chain_runtime_and_future_timestamp_remain_unverified(self):
        req=self.request();req['chain']['id']='999999';req['snapshot']['timestamp']=str(2**64-1)
        out=self.catalog.prepare(req)
        for key in ('onchain_snapshot_verified','snapshot_freshness_verified','target_runtime_verified',
                'authority_verified','human_callability_verified','simulation_performed','ready_for_submission'):
            self.assertIs(False,out['boundaries'][key])

    def test_pool_config_nested_tuple_and_array_arguments_use_catalog_order(self):
        req=self.request('ZZZPoolRegistry','configureNative')
        req['arguments']=dict(config=dict(key=dict(currency0=ZERO,currency1=address(7),fee='3000',tickSpacing='60',hooks=ZERO),
            depositsEnabled=False,operationsEnabled=True,rangeBps='5000',triggerBps='100',maxSpotDeviationBps='100',
            maxSlippageBps='200',minRebalanceInterval='43200',minDepositUSD='5000000000000000000',
            maxPositionUSD='1000000000000000000000000'))
        out=self.catalog.prepare(req)['explorer']['arguments'][0]
        self.assertEqual([ZERO,address(7),'3000','60',ZERO],out[0]);self.assertEqual(False,out[1])
        item=dict(type='uint256[]',label='ids')
        self.assertEqual(['1',str(2**256-1)],O._value(item,['1',str(2**256-1)],depth=1))
        for bad in ([True],['-1'],['1']*129):
            with self.subTest(bad=repr(bad)[:30]),self.assertRaises(ValueError):O._value(item,bad,depth=1)

    def test_duplicate_nonfinite_float_depth_and_size_are_rejected_before_use(self):
        for raw in (b'{"schema":1,"schema":1}',b'{"x":{"y":0,"y":1}}',b'{"x":NaN}',
                b'{"x":Infinity}',b'{"x":1.0}',b'{"x":1e3}',b'['*17+b']'*17,b' '*O.MAX_DOCUMENT+b'1'):
            with self.subTest(raw=repr(raw[:45])),self.assertRaises(ValueError):O.decode(raw)
        escaped={'text':'[{}] "quoted"'}
        self.assertEqual(escaped,O.decode(json.dumps(escaped).encode('utf-8')))

    def test_unknown_endpoint_profile_evidence_and_callable_fields_reject(self):
        for name,value in (('rpc_url','https://not-used.invalid'),('private_key','never echo this'),
                ('profile','accounting4'),('schema',True),('reference_sha256','0'*64),('source_snapshot_sha256','0'*64),
                ('contract','ZZZMissing'),('signature','constructor()'),('review_notes_sha256','0'*64),
                ('evidence_sha256',[]),('evidence_sha256',['3'*64]*2),('evidence_sha256',['3'*64]*17)):
            req=self.request();req[name]=value
            with self.subTest(name=name),self.assertRaises(ValueError):self.catalog.prepare(req)

    def test_artifact_hash_arguments_and_false_qualification_flags_cannot_be_tampered(self):
        base=self.catalog.prepare(self.request())
        for change in ('hash','argument','number_as_bool','ready','runtime','extra'):
            artifact=copy.deepcopy(base)
            if change=='hash':artifact['review_hash']='0x'+'7'*64
            elif change=='argument':artifact['explorer']['arguments'][1]=False
            elif change=='number_as_bool':artifact['schema']=True
            elif change=='ready':artifact['boundaries']['ready_for_submission']=0
            elif change=='runtime':artifact['boundaries']['target_runtime_verified']=True
            else:artifact['approval']='yes'
            with self.subTest(change=change),self.assertRaises(ValueError):self.catalog.check(artifact)

    def test_source_dependency_build_and_catalog_drift_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);snap=self.catalog.data['source_snapshot']
            names=set(snap['source_sha256'])|set(snap['dependency_source_sha256'])|set(snap['build_input_sha256'])
            names.add('docs/function-reference.json')
            for name in names:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((O.ROOT/name).read_bytes())
            self.assertEqual(self.catalog.reference_sha256,O.Catalog(root).reference_sha256)
            for name in ('src/ZZZMigration.sol',next(iter(snap['dependency_source_sha256'])),next(iter(snap['build_input_sha256']))):
                target=root/name;old=target.read_bytes();target.write_bytes(old+b'\n')
                try:
                    with self.subTest(name=name),self.assertRaises(ValueError):O.Catalog(root)
                finally:target.write_bytes(old)
            target=root/'docs/function-reference.json';obj=copy.deepcopy(self.catalog.data);obj['contracts'][0]['purpose']='Changed'
            target.write_text(json.dumps(obj),encoding='utf-8')
            changed=O.Catalog(root)
            with self.assertRaises(ValueError):changed.prepare(self.request())

    def test_malformed_catalog_roots_and_list_shapes_refuse_explicitly(self):
        invalid=[None,[],1,'text',{},dict(self.catalog.data,source_snapshot=[]),
            dict(self.catalog.data,contracts=None),dict(self.catalog.data,contracts=[None]),
            dict(self.catalog.data,contracts=[{'name':'ZZZMigration','source':'src/ZZZMigration.sol','functions':[None]}])]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'docs/function-reference.json';path.parent.mkdir()
            for value in invalid:
                path.write_text(json.dumps(value),encoding='utf-8')
                with self.subTest(value=repr(value)[:45]),self.assertRaises(ValueError):O.Catalog(root)

    def test_large_valid_byte_array_artifact_roundtrips_under_its_separate_bound(self):
        req=self.request('ZZZCanonicalHandoff','importRows')
        req['arguments']=dict(slot='0',records=['0x'+'ab'*4096]*14)
        self.assertLess(len(O.canonical(req)),O.MAX_DOCUMENT)
        artifact=self.catalog.prepare(req);raw=O.render(artifact)
        self.assertGreater(len(raw),O.MAX_DOCUMENT);self.assertLess(len(raw),O.MAX_ARTIFACT)
        self.assertTrue(self.catalog.check(O.decode(raw,O.MAX_ARTIFACT))['artifact_matches'])
        with self.assertRaises(ValueError):O.decode(raw)
        with patch.object(O,'MAX_ARTIFACT',100),self.assertRaises(ValueError):self.catalog.prepare(self.request())

    def test_utf8_output_is_exclusive_and_validation_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'request.json';path.write_text(json.dumps(self.parking()),encoding='utf-8')
            output=Path(directory)/'review.json';check=Path(directory)/'check.json'
            self.assertEqual(0,O.main(['prepare',str(path),'--output',str(output)]))
            original=output.read_bytes();self.assertTrue(original.startswith(b'{'))
            self.assertEqual(0,O.main(['check',str(output),'--output',str(check)]))
            self.assertTrue(json.loads(check.read_text(encoding='utf-8'))['artifact_matches'])
            with redirect_stderr(io.StringIO()):self.assertEqual(1,O.main(['profile','--output',str(output)]))
            self.assertEqual(original,output.read_bytes())
            path.write_text('{"private_key":"DO_NOT_ECHO_THIS"}',encoding='utf-8')
            new=Path(directory)/'must-not-exist.json'
            with redirect_stderr(io.StringIO()):self.assertEqual(1,O.main(['prepare',str(path),'--output',str(new)]))
            self.assertFalse(new.exists());self.assertEqual(original,output.read_bytes())

    def test_cli_never_accesses_network_or_subprocess_and_sanitizes_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'request.json';path.write_text(json.dumps(self.request()),encoding='utf-8')
            with patch.object(socket,'socket',side_effect=AssertionError('Network access')), \
                    patch.object(subprocess,'run',side_effect=AssertionError('Process access')):
                for command in (['profile'],['prepare',str(path)]):
                    output=io.StringIO()
                    with redirect_stdout(output):self.assertEqual(0,O.main(command))
                    self.assertFalse(json.loads(output.getvalue())['boundaries']['ready_for_submission'])
                path.write_text('{"private_key":"DO_NOT_ECHO_THIS"}',encoding='utf-8')
                output=io.StringIO();error=io.StringIO()
                with redirect_stdout(output),redirect_stderr(error):self.assertEqual(1,O.main(['prepare',str(path)]))
                self.assertEqual('',output.getvalue());self.assertNotIn('DO_NOT_ECHO_THIS',error.getvalue())


if __name__=='__main__':unittest.main()
