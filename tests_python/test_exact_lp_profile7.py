"""Explicit fresh7 graph fixtures; no existing runtime/journal is relabelled."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from frontend_api.service import Projection,ProjectionError,ZERO
from frontend_api.transactions import Transactions
from frontend_api.earnings_checkpoint import identity
from frontend_api.history import HistoryError
from keeper.monitor import Keeper
from keeper.operation_review import PinnedReads
from tests_python import test_frontend_policy_v6 as neutral_api
from tests_python.test_frontend_api import addr,words
from tests_python.test_frontend_transactions import transaction_config
from tests_python.test_native_backend_boundary import native_data
from tests_python.test_keeper_policy_v6 import PolicyRPC
from zzz_ops.abi import calldata,keccak256
from zzz_ops.position import decode_position,position_word_count
from zzz_ops.rpc import RpcError


class Fresh7API:
    """Reuse unchanged neutral geometry scaffolding; construct explicit7 identities."""
    def __init__(self,case):
        self.f=neutral_api.FrontendPolicyV6Tests('runTest');self.f.setUp();case.addCleanup(self.f.doCleanups)
        self.rpc,self.q=self.f.rpc,self.f.q
        self.config=copy.deepcopy(self.f.config)
        self.config.update(accounting_version=7,custody_version=5,royalty_reporting={'schema':5,'converter':None})
        self.c=dict(self.f.c);self.c['rewards_canonical']=addr(9999)
        for role in ('vault','rewards','rewards_canonical'):
            code='0x6007'+f'{len(role):02x}';target=self.c[role]
            self.rpc.codes[target]=code;self.q.code_overrides[target]=code
            self.config['contracts'][role]=dict(address=target,code_hash='0x'+keccak256(bytes.fromhex(code[2:])).hex())
        self.q.overrides[self.c['vault'],'ACCOUNTING_VERSION()']=[f'{7:064x}']
        self.rpc.put(self.c['vault'],'ACCOUNTING_VERSION()',values=(7,))
        self.rpc.put(self.c['principal_exit'],'CUSTODY_VERSION()',values=(5,))
        self.rpc.put(self.c['handoff'],'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9').hex(),))
        self.rpc.put(self.c['handoff'],'moduleAt(uint8)',(3,),(self.c['rewards_canonical'],))
        for role,method,value in (('rewards','LP_ALLOCATION_VERSION()',1),
                ('rewards','canonicalModule()',self.c['rewards_canonical']),
                ('rewards_canonical','access()',self.c['access']),('rewards_canonical','rewards()',self.c['rewards']),
                ('pools','ZZZ()',addr(20))):self.rpc.put(self.c[role],method,values=(value,))
        self.rpc.header_timestamp=4000;self.q.now=4000
        id=self.rpc.nft_id
        self.rpc.put(self.c['nft'],'rarityOf(uint256)',(id,),(0,))
        for method,value in (('mintEnd()',100),('royaltiesOpenAt()',3700),('royaltiesOpen()',1),
                ('canonicalController()',self.c['access']),('activationCount()',1),('totalWeight()',1),
                ('ROYALTY_SETTLEMENT_VERSION()',4)):
            self.rpc.put(self.c['royalties'],method,values=(value,))
        for method,value in (('activationOrdinal(uint256)',1),('ticketStart(uint256)',1),('weightOf(uint256)',1)):
            self.rpc.put(self.c['royalties'],method,(id,),(value,))
        for asset in (ZERO,addr(21)):
            for method,value,args in (('effectiveEligibleCount(address)',1,(asset,)),
                    ('eligibleFor(uint256,address)',1,(id,asset)),('eligibleWeight(address)',1,(asset,)),
                    ('allocationCursor(address)',0,(asset,))):
                self.rpc.responses[self.c['royalties'],native_data(method,*args)]=words(value)
        self.rpc.responses[self.c['rewards'],native_data('claimable(uint256,address)',id,ZERO)]=words(18)
        self.p=Projection(self.config,self.rpc,clock=lambda:4000)

    def block(self):return {'blockHash':self.rpc.hash,'requireCanonical':True}


class Fresh7KeeperRPC(PolicyRPC):
    def __init__(self,path):
        super().__init__(path)
        self.contracts['rewards']=addr(9911);self.reward=self.contracts['rewards']
        self.cfg.update(accounting_version=7,custody_version=5,royalty_settlement_version=4)
        self.cfg['code_hashes']['rewards']=self.pin
        self.current=7;self.allocation=1
    def read(self,target,signature,*args,count=1):
        if signature=='ACCOUNTING_VERSION()':return [f'{self.current:064x}']
        if signature=='CUSTODY_VERSION()':return [f'{5:064x}']
        return super().read(target,signature,*args,count=count)
    def call(self,method,params):
        if method=='eth_call' and 'from' not in params[0]:
            target,data=params[0]['to'],params[0]['data'];value=None
            if target==self.reward and data==calldata('LP_ALLOCATION_VERSION()'):value=self.allocation
            elif data==calldata('CUSTODY_VERSION()'):value=5
            elif target==self.reward and data==calldata('access()'):value=int(self.contracts['access'],16)
            elif data==calldata('module(bytes32)','0x'+keccak256(b'ZZZRewards').hex()):value=int(self.reward,16)
            if value is not None:return '0x'+f'{value:064x}'
        return super().call(method,params)


class ExactLPProfile7Tests(unittest.TestCase):
    def test_eight_word_codec_is_explicit7_not_unknown_tuple_guess(self):
        self.assertEqual(8,position_word_count(7))
        fields=['0'*64]*8;fields[7]=f'{5:064x}'
        self.assertEqual('exited',decode_position(fields,7)['status'])
        with self.assertRaises(ValueError):decode_position(fields,3)
        with self.assertRaises(ValueError):position_word_count(8)

    def test_current7_graph_binds_actual_versions_and_typed_canonical_child(self):
        f=Fresh7API(self);life=f.p._verify_deployment(f.block())
        self.assertEqual('operating',life['state'])
        self.assertEqual(7,f.p.accounting_version);self.assertEqual(5,f.p.custody_version)
        self.assertEqual([ZERO,addr(20)],f.p._admitted(f.block())[0])
        self.assertEqual('18',f.p._balance('rewards',f.rpc.nft_id,ZERO,f.block())['raw'])

    def test_old_v8_marker_wrong_child_or_runtime_fail_closed(self):
        for variant in ('schema','marker','child','runtime'):
            with self.subTest(variant=variant):
                f=Fresh7API(self)
                if variant=='schema':f.rpc.put(f.c['handoff'],'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8').hex(),))
                elif variant=='marker':f.rpc.put(f.c['rewards'],'LP_ALLOCATION_VERSION()',values=(0,))
                elif variant=='child':f.rpc.put(f.c['handoff'],'moduleAt(uint8)',(3,),(f.c['rewards'],))
                else:f.rpc.codes[f.c['rewards']]='0x6006'
                with self.assertRaises(ProjectionError):f.p._verify_deployment(f.block())

    def test_missing_new_authority_profile_and_reporting_are_not_inherited(self):
        f=Fresh7API(self)
        for key in ('custody_version','royalty_reporting'):
            cfg=copy.deepcopy(f.config);cfg.pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError):Projection(cfg,f.rpc,clock=lambda:4000)

    def test_third_lp_currency_rejects_while_original_royalty_currency_is_admitted(self):
        f=Fresh7API(self);lp,royalties=f.p._admitted(f.block())
        self.assertIn(addr(21),royalties);self.assertNotIn(addr(21),lp)
        f.rpc.put(f.c['rewards'],'assetCount()',values=(3,))
        with self.assertRaises(ProjectionError):f.p._admitted(f.block())

    def test_price_fault_keeps_both_leg_custody_and_raw_funded_claims(self):
        f=Fresh7API(self);f.f.base.outage();f.q.secondary=124;f.q.secondary_count=1
        result=f.p.nft(f.rpc.nft_id)
        self.assertFalse(result['position']['current_lp_value']['available'])
        self.assertEqual('18',result['claimable']['lp'][0]['raw'])
        self.assertEqual('124',result['position']['local_custody']['portfolio']['secondary_lp_token_id'])

    def test_current7_unsigned_claim_uses_actual_claimable_and_never_sends(self):
        f=Fresh7API(self);original=f.rpc.call;calls=[]
        def call(method,params):
            if method=='eth_call' and 'from' in params[0]:calls.append(params);return words(32,1,18)
            if method=='eth_estimateGas':return hex(100000)
            if method=='eth_gasPrice':return hex(10**9)
            if method=='eth_getBalance':return hex(10**18)
            if 'send' in method:raise AssertionError('Unsigned preparation cannot send')
            return original(method,params)
        f.rpc.call=call
        result=Transactions(f.p,transaction_config(f.p)).prepare({'action':'claim','wallet':addr(30),
            'claims':[{'token_id':str(f.rpc.nft_id),'asset':ZERO,'royalty':False}]})
        self.assertEqual('0x0',result['transaction']['value']);self.assertEqual(1,len(calls))
        self.assertEqual('18',result['claim_operations'][0]['view_raw'])

    def test_checkpoint1_is_explicitly_rejected_before_any_new_model_seed(self):
        with self.assertRaisesRegex(HistoryError,'checkpoint2'):
            identity(SimpleNamespace(p=SimpleNamespace(accounting_version=7,history=None)))

    def test_keeper7_read_only_operation_review_is_not_a_historical_profile(self):
        from keeper.operation_review import review
        with tempfile.TemporaryDirectory() as tmp:
            rpc=Fresh7KeeperRPC(Path(tmp)/'fresh7.json')
            Keeper(rpc.cfg,rpc=rpc).save();before=Path(rpc.cfg['state_path']).read_bytes()
            with patch('keeper.monitor.subprocess.run') as signer:
                result=review(rpc.cfg,[7],rpc=rpc,now=lambda:rpc.now)
            signer.assert_not_called()
            self.assertEqual(result['profile']['accounting_version'],7)
            self.assertTrue(all(r['state']!='unsupported' for r in result['operations']))
            self.assertEqual(before,Path(rpc.cfg['state_path']).read_bytes())

    def test_keeper7_invalid_exact_ledger_pin_is_configuration_error_before_rpc(self):
        with tempfile.TemporaryDirectory() as tmp:
            rpc=Fresh7KeeperRPC(Path(tmp)/'fresh7.json')
            for pin in (None,True,0,'0x'+'0'*64,'0x1234'):
                cfg=copy.deepcopy(rpc.cfg);cfg['code_hashes']['rewards']=pin
                with self.subTest(pin=pin),self.assertRaisesRegex(ValueError,'Rewards runtime'):
                    Keeper(cfg,rpc=rpc)
                self.assertFalse(Path(cfg['state_path']).exists())

    def test_keeper7_authenticates_exact_ledger_and_never_adopts_saved6_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            rpc=Fresh7KeeperRPC(Path(tmp)/'fresh7.json')
            pinned=PinnedReads(rpc,rpc.call('eth_getBlockByNumber',['latest',False]));k=Keeper(rpc.cfg,rpc=pinned)
            with patch('keeper.monitor.time.time',return_value=rpc.now):k._validate_accounting_version()
            k.save();before=k.path.read_bytes()
            config=copy.deepcopy(rpc.cfg);config['accounting_version']=6
            with self.assertRaises(ValueError):Keeper(config,rpc=pinned)
            self.assertEqual(before,k.path.read_bytes())
            rpc.allocation=0
            with patch('keeper.monitor.time.time',return_value=rpc.now),self.assertRaises(RpcError):k._validate_accounting_version()


if __name__=='__main__':unittest.main()
