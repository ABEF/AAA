import copy,datetime as dt,json,os,shutil,tempfile,time,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from keeper.monitor import Keeper,positive,ACCOUNTING_MODEL
from zzz_ops.rpc import RpcError
from zzz_ops.abi import keccak256,calldata
A='0x'+'11'*20;B='0x'+'22'*20;H='0x'+'ab'*32;C='0x'+'33'*20
class FakeRpc:
    active_url='https://rpc.invalid'
    def __init__(self):self.now=int(time.time());self.gas=100;self.gas_price=2;self.receipt=None;self.tx=None;self.error=False;self.calls=[]
    def call(self,method,params):
        self.calls.append((method,params))
        if method=='eth_getBlockByNumber':return {'number':'0x64' if params[0]=='latest' else params[0],'timestamp':hex(self.now),'hash':H}
        if method=='eth_call':
            if self.error:raise RpcError('simulation failed')
            return '0x'+'0'*64
        if method=='eth_estimateGas':return hex(self.gas)
        if method=='eth_gasPrice':return hex(self.gas_price)
        if method=='eth_getTransactionCount':return '0x7'
        if method=='eth_getBalance':return hex(10**18)
        if method=='eth_getCode':return '0x6000'
        if method=='eth_getTransactionReceipt':return self.receipt
        if method=='eth_getTransactionByHash':return self.tx
        raise AssertionError(method)
    def eth_call(self,to,data):return self.call('eth_call',[{'to':to,'data':data},'latest'])
class KeeperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.rpc=FakeRpc()
        self.cfg={'chain_id':1,'sender':A,'contracts':{k:B for k in ['access','vault','strategy','fees','compounder','buyback','pools']},
            'state_path':str(Path(self.tmp.name)/'state.json'),'confirmations':2,'max_gas_limit':100000,
            'max_gas_price_wei':100,'max_transaction_cost_wei':1000000,'max_daily_cost_wei':10000000}
        self.k=Keeper(self.cfg,rpc=self.rpc)
        self.quiet=patch('keeper.monitor.log');self.quiet.start();self.addCleanup(self.quiet.stop)
    def enable_test_signer(self):
        self.k.state['next_nonce']=7
        self.k.state['receipt_anchor']={'number':98,'hash':H,'timestamp':self.rpc.now,'nonce':6}
        self.k.live=True;self.k.cast='/mock/cast';self.k.keystore=Path('/mock/key');self.k.password=Path('/mock/pass')
        self.k._validate_code_hashes=lambda:None
    def pending(self):
        self.k.state['pending']={'key':'collect:1','nonce':7,'to':B,'data':calldata('collectFees(uint256,uint256)',1,123),
            'value':10,'day':'2026-10-14','hash':H}
        return self.k.state['pending']
    def receipt(self,success=True):
        p=self.pending()
        self.rpc.receipt={'transactionHash':H,'blockNumber':'0x63','blockHash':H,'status':hex(int(success)),
            'gasUsed':'0x64','effectiveGasPrice':'0x2','l1Fee':'0x5','from':A,'to':B,'transactionIndex':'0x0'}
        self.rpc.tx={'hash':H,'from':A,'to':B,'nonce':'0x7','input':p['data'],'value':hex(p['value']),
            'blockNumber':'0x63','blockHash':H,'transactionIndex':'0x0','gas':'0x100'}
    def test_default_dry_run_never_signs(self):
        with patch('subprocess.run') as run:
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
            run.assert_not_called();self.assertIsNone(self.k.state['pending']);self.assertFalse(self.k.path.exists())
    def test_live_requires_explicit_review(self):
        with self.assertRaises(ValueError):Keeper(self.cfg,live=True,rpc=self.rpc)
    def test_bad_chain_state_rejected(self):
        self.k.state['chain_id']=2;self.k.save()
        with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_simulation_failure_never_signs(self):
        self.enable_test_signer();self.rpc.error=True
        with patch('subprocess.run') as run:
            with self.assertRaises(RpcError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
            run.assert_not_called();self.assertIsNone(self.k.state['pending'])
    def test_gas_cap(self):
        self.rpc.gas=1000000
        self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
    def test_gas_price_cap(self):
        self.rpc.gas_price=101
        self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
    def test_cost_cap(self):
        self.cfg['max_transaction_cost_wei']=1
        self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
    def test_stale_head_rejected(self):
        self.rpc.now-=1000
        with self.assertRaises(RpcError):self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
    def test_broadcast_state_durable_before_signer(self):
        self.enable_test_signer()
        def run(*args,**kwargs):
            state=json.loads(self.k.path.read_text());self.assertIsNone(state['pending']['hash']);self.assertEqual(state['pending']['nonce'],7)
            return subprocess.CompletedProcess(args[0],0,json.dumps(H),'')
        with patch('subprocess.run',side_effect=run):
            self.assertTrue(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c'))
        self.assertEqual(self.k.state['pending']['hash'],H)
    def test_timeout_preserves_ambiguous_state(self):
        self.enable_test_signer()
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('cast',90)) as run:
            with self.assertRaises(subprocess.TimeoutExpired):
                self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
            self.assertIsNotNone(self.k.state['pending']);self.assertIsNone(self.k.state['pending']['hash'])
            self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
            self.assertEqual(run.call_count,1)
    def test_pending_waits(self):
        self.pending();self.assertTrue(self.k.poll_pending());self.assertIsNotNone(self.k.state['pending'])
    def test_success_accounts_actual_cost(self):
        self.receipt();self.assertFalse(self.k.poll_pending())
        day=dt.datetime.fromtimestamp(self.rpc.now,dt.timezone.utc).date().isoformat()
        self.assertEqual(self.k.state['spent'][day],215)
        self.assertEqual(self.k.state['last']['collect:1'],self.rpc.now)
    def test_failed_tx_not_marked_success(self):
        self.receipt(False);self.k.poll_pending()
        day=dt.datetime.fromtimestamp(self.rpc.now,dt.timezone.utc).date().isoformat()
        self.assertEqual(self.k.state['spent'][day],205);self.assertNotIn('collect:1',self.k.state['last'])
        self.assertEqual(self.k.state['retry_after']['collect:1'],self.rpc.now+3600)
    def test_reverted_action_cannot_immediately_spend_again(self):
        self.receipt(False);self.k.poll_pending()
        with patch('subprocess.run') as signer:
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'collect:1'))
            signer.assert_not_called()
        self.assertEqual(self.k.blocked_actions,1)
    def test_wrong_sender_fails_closed(self):
        self.receipt();self.rpc.tx['from']=B
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertIsNotNone(self.k.state['pending'])
    def test_wrong_value_fails_closed(self):
        self.receipt();self.rpc.tx['value']='0xff'
        with self.assertRaises(RpcError):self.k.poll_pending()
    def test_wrong_calldata_fails_closed(self):
        self.receipt();self.rpc.tx['input']='0x'
        with self.assertRaises(RpcError):self.k.poll_pending()
    def test_receipt_reorg_not_confirmed(self):
        self.receipt();self.rpc.receipt['blockHash']='0x'+'cd'*32
        self.assertTrue(self.k.poll_pending());self.assertIsNotNone(self.k.state['pending'])
    def test_insufficient_confirmations_waits(self):
        self.receipt();self.rpc.receipt['blockNumber']='0x64'
        self.assertTrue(self.k.poll_pending())
    def test_unknown_resolve_hash_rejected(self):
        with self.assertRaises(ValueError):self.k.resolve_pending('0x123')
    def test_changed_code_rejected(self):
        self.cfg['code_hashes']={k:'0x'+keccak256(b'wrong').hex() for k in self.cfg['contracts']}
        with self.assertRaises(ValueError):self.k._validate_code_hashes()
    def test_valid_code_hash_accepted(self):
        self.cfg['code_hashes']={k:'0x'+keccak256(bytes.fromhex('6000')).hex() for k in self.cfg['contracts']}
        self.k._validate_code_hashes()
    def test_numeric_limits_reject_non_integer_json_values(self):
        for value in (True,False,1.9,1.0,None,'1.9','-1',' 1','1e3'):
            with self.subTest(value=value),self.assertRaises(ValueError):positive(value,'budget')
        self.assertEqual(positive('5000000000','budget'),5000000000)
        self.assertEqual(positive(0,'allowance',zero=True),0)
    def test_live_command_binds_sender_and_removes_ambient_wallet_overrides(self):
        self.enable_test_signer()
        ambient={'ETH_FROM':B,'ETH_PASSWORD':'ambient-password','ETH_PRIORITY_GAS_PRICE':'999',
            'CAST_ASYNC':'false','FOUNDRY_CONFIG':'/unreviewed/config','CHAIN':'2',
            'AWS_KMS_KEY_ID':'other-key','GCP_PROJECT_ID':'other-project','PRIVATE_KEY':'ambient-key'}
        with patch.dict(os.environ,ambient),patch('subprocess.run',return_value=subprocess.CompletedProcess([],0,H,'')) as run:
            self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
        command=run.call_args.args[0];environment=run.call_args.kwargs['env']
        self.assertEqual(command[:4],[self.k.cast,'send',B,calldata('collectFees(uint256,uint256)',1,123)])
        self.assertNotIn('--data',command)
        self.assertEqual(command[command.index('--from')+1],A)
        self.assertEqual(environment['ETH_RPC_URL'],self.rpc.active_url)
        for key in ambient:self.assertNotIn(key,environment)
    @unittest.skipUnless(shutil.which('cast'),'Foundry cast is not installed')
    def test_cast_cli_accepts_generated_command_without_signing(self):
        self.enable_test_signer();self.k.cast=shutil.which('cast')
        with patch('subprocess.run',return_value=subprocess.CompletedProcess([],0,H,'')) as run:
            self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'c')
        # --help validates the actual installed parser and exits before RPC/signing.
        result=subprocess.run(run.call_args.args[0]+['--help'],capture_output=True,text=True,timeout=30,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_recovery_rejects_wrong_candidate_without_overwriting_state(self):
        self.receipt();self.k.state['pending']['hash']=None;self.k.save()
        self.rpc.tx['from']=B
        before=self.k.path.read_text()
        with self.assertRaises(RpcError):self.k.resolve_pending(H)
        self.assertIsNone(self.k.state['pending']['hash']);self.assertEqual(self.k.path.read_text(),before)
    def test_recovery_rejects_unknown_transaction_without_overwriting_state(self):
        self.pending();self.k.state['pending']['hash']=None;self.k.save()
        before=self.k.path.read_text()
        with self.assertRaises(RpcError):self.k.resolve_pending(H)
        self.assertEqual(self.k.path.read_text(),before)
    def test_recovery_accepts_verified_pending_transaction(self):
        self.receipt();self.rpc.receipt=None;self.k.state['pending']['hash']=None
        self.k.resolve_pending(H)
        self.assertEqual(self.k.state['pending']['hash'],H)
        self.assertEqual(json.loads(self.k.path.read_text())['pending']['hash'],H)
    def test_wrong_transaction_hash_fails_closed(self):
        self.receipt();self.rpc.tx['hash']='0x'+'cd'*32
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertIsNotNone(self.k.state['pending'])
    def test_wrong_receipt_transaction_hash_fails_closed(self):
        self.receipt();self.rpc.receipt['transactionHash']='0x'+'cd'*32
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertIsNotNone(self.k.state['pending'])
    def assert_pending_unchanged(self,mutate):
        self.receipt();self.k.save()
        expected=copy.deepcopy(self.k.state);disk=self.k.path.read_text()
        mutate()
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertEqual(self.k.state,expected);self.assertEqual(self.k.path.read_text(),disk)
    def test_incomplete_receipt_never_clears_pending_or_assumes_free_gas(self):
        fields=('transactionHash','blockNumber','blockHash','transactionIndex','from','to','status','gasUsed','effectiveGasPrice')
        for field in fields:
            with self.subTest(field=field):
                self.assert_pending_unchanged(lambda:self.rpc.receipt.pop(field))
    def test_noncanonical_receipt_quantities_fail_closed(self):
        for field in ('blockNumber','transactionIndex','status','gasUsed','effectiveGasPrice','l1Fee'):
            for value in (None,True,1,-1,'-0x1','0x','0x00','0x01','0x-1','1','0x'+'1'*65):
                with self.subTest(field=field,value=value):
                    self.assert_pending_unchanged(lambda:self.rpc.receipt.update({field:value}))
    def test_invalid_receipt_status_and_zero_gas_fail_closed(self):
        for field,value in (('status','0x2'),('gasUsed','0x0')):
            with self.subTest(field=field):
                self.assert_pending_unchanged(lambda:self.rpc.receipt.update({field:value}))
    def test_receipt_sender_target_and_hash_are_required_to_match(self):
        for field,value in (('from',B),('to',A),('blockHash','0x'+'0'*64)):
            with self.subTest(field=field):
                self.assert_pending_unchanged(lambda:self.rpc.receipt.update({field:value}))
    def test_pending_transaction_inclusion_and_gas_limit_match_receipt(self):
        for field,value in (('blockNumber','0x62'),('blockHash','0x'+'cd'*32),('transactionIndex','0x1'),('gas','0x63')):
            with self.subTest(field=field):
                self.assert_pending_unchanged(lambda:self.rpc.tx.update({field:value}))
    def test_missing_transaction_identity_and_inclusion_fields_fail_closed(self):
        for field in ('hash','from','to','nonce','input','value','blockNumber','blockHash','transactionIndex','gas'):
            with self.subTest(field=field):
                self.assert_pending_unchanged(lambda:self.rpc.tx.pop(field))
    def test_receipt_header_number_is_validated(self):
        original=self.rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_getBlockByNumber' and params[0]=='0x63':result['number']='0x62'
            return result
        self.rpc.call=call
        self.assert_pending_unchanged(lambda:None)
    def test_ordinary_receipt_reorg_after_transaction_read_retains_state(self):
        original=self.rpc.call;changed=False
        def call(method,params):
            nonlocal changed
            result=original(method,params)
            if method=='eth_getTransactionByHash':changed=True
            if changed and method=='eth_getBlockByNumber' and params[0]=='0x63':result['hash']='0x'+'cd'*32
            return result
        self.rpc.call=call
        self.assert_pending_unchanged(lambda:None)
    def test_head_retreat_below_confirmation_depth_preserves_pending(self):
        self.receipt();self.k.save();before=copy.deepcopy(self.k.state);disk=self.k.path.read_text()
        original=self.rpc.call;heads=0
        def call(method,params):
            nonlocal heads
            result=original(method,params)
            if method=='eth_getBlockByNumber' and params[0]=='latest':
                heads+=1
                if heads==2:result['number']='0x63'
            return result
        self.rpc.call=call
        self.assertTrue(self.k.poll_pending());self.assertEqual(self.k.state,before)
        self.assertEqual(self.k.path.read_text(),disk)
    def test_inclusion_day_cost_blocks_new_day_budget_overspend(self):
        self.receipt();self.rpc.now=int(dt.datetime(2026,10,16,0,0,10,tzinfo=dt.timezone.utc).timestamp())
        self.k.state['pending']['day']='2026-10-15'
        self.k.state['spent']={'2026-10-15':600,'2026-10-16':100}
        self.cfg['max_daily_cost_wei']=500
        with patch('keeper.monitor.time.time',return_value=self.rpc.now),patch('keeper.monitor.log') as logger:
            self.assertFalse(self.k.poll_pending())
            self.assertEqual(self.k.state['spent'],{'2026-10-15':600,'2026-10-16':315})
            self.assertFalse(self.k.submit('vault','collectFees(uint256,uint256)',(1,123),'next'))
        self.assertEqual(logger.call_args.args[0],'cost_cap_exceeded')
    def test_confirmed_cost_is_applied_exactly_once(self):
        self.receipt();self.assertFalse(self.k.poll_pending())
        after=copy.deepcopy(self.k.state)
        self.assertFalse(self.k.poll_pending());self.assertEqual(self.k.state,after)
        restarted=Keeper(self.cfg,rpc=self.rpc)
        self.assertFalse(restarted.poll_pending());self.assertEqual(restarted.state,after)
    def test_optional_l1_fee_absent_but_explicit_zero_effective_price_supported(self):
        self.receipt();self.rpc.receipt.pop('l1Fee');self.rpc.receipt['effectiveGasPrice']='0x0'
        self.assertFalse(self.k.poll_pending())
        self.assertEqual(sum(self.k.state['spent'].values()),10)
    def test_reviewed_separate_l1_fee_cannot_be_omitted(self):
        self.receipt();self.k.fee_policy='separate_l1_fee';self.rpc.receipt.pop('l1Fee')
        before=copy.deepcopy(self.k.state)
        with self.assertRaises(RpcError):self.k.poll_pending()
        self.assertEqual(self.k.state,before)
    def test_included_policy_rejects_conflicting_extra_fee(self):
        self.receipt();self.k.fee_policy='included'
        with self.assertRaises(RpcError):self.k.poll_pending()
    def test_failed_checkpoint_preserves_in_memory_pending_and_costs(self):
        self.receipt();self.k.save();before=copy.deepcopy(self.k.state);disk=self.k.path.read_text()
        with patch.object(self.k,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.k.poll_pending()
        self.assertEqual(self.k.state,before);self.assertEqual(self.k.path.read_text(),disk)
    def reward_cycle(self,status):
        self.k.maintenance={'minimum_liquidity':1,'harvest':True,'compound':True,
            'reward_routes':[{'token':B,'route_id':H,'minimum_units':1,'native_fee_wei':3}]}
        fields=[0]*15;fields[7]=status
        reads={'paused()':0,'preparationActive()':0,'canonicalState()':0,'isSealed()':1,'keepers(address)':1,
            'bucketCount()':1,'bucketAt(uint256)':7,
            'rewardReceiver(uint256)':0,
            'remoteIndividual(uint256,address)':10,'remoteCollective(uint256,address)':6}
        with patch.object(self.k,'_bucket',return_value=([f'{value:064x}' for value in fields],[B,C])), \
             patch.object(self.k,'view',side_effect=lambda name,signature,*args:reads[signature]) as view, \
             patch.object(self.k,'submit',return_value=True) as submit:
            self.k.cycle()
        return view,submit
    def test_legacy_rewards_delivered_after_principal_departure(self):
        for status in (2,3,4,6):
            with self.subTest(status=status):
                view,submit=self.reward_cycle(status)
                submit.assert_called_once_with('fees','bridgeRewards(uint256,address,bytes32)',
                    (7,B,H),f'bridge_rewards:7:{B}',value=3)
                self.assertNotIn('needsRebalance(uint256)',[call.args[1] for call in view.call_args_list])
    def test_missing_and_dormant_groups_do_not_bridge_rewards(self):
        for status in (0,5):
            with self.subTest(status=status):
                view,submit=self.reward_cycle(status)
                submit.assert_not_called()
                self.assertFalse(any(call.args[1].startswith('remote') for call in view.call_args_list))

class PoolKeeperTests(unittest.TestCase):
    """Pool discovery and maintenance exercise real static-ABI decoding."""
    def setUp(self):
        KeeperTests.setUp(self)
        self.ids=[7,9,11]
        self.config_words=[int(B,16),int(C,16),3000,60,0,1,1,1000,500,100,100,600,1,10**30]
        self.pool='0x'+keccak256(bytes.fromhex(''.join(f'{n:064x}' for n in self.config_words[:5]))).hex()
        self.group_words=[int(self.pool,16),10,0,0,1000,1<<96,self.rpc.now,1,1,
            int(B,16),int(B,16),int(B,16),int(C,16),1,int(B,16)]
        self.rebalance=True
        self.paused=False;self.preparing=False;self.canonical_state=0;self.inbox=0;self.inbox_pending=[0,0]
        self.inbox_fees=int(B,16);self.inbox_bucket=7
        self.reserves={B:0,C:0}
        self.accounting_words=None;self.native_wrapper=int(B,16)
        self.original_call=self.rpc.call
        self.rpc.call=self.contract_call
    enable_test_signer=KeeperTests.enable_test_signer
    def contract_call(self,method,params):
        if method!='eth_call':return self.original_call(method,params)
        if 'from' in params[0]:return self.original_call(method,params)
        self.rpc.calls.append((method,params))
        data=params[0]['data']
        selector=data[:10]
        args=[int(data[i:i+64],16) for i in range(10,len(data),64)]
        values={
            'paused()':int(self.paused),'preparationActive()':int(self.preparing),'canonicalState()':self.canonical_state,'isSealed()':1,'keepers(address)':1,'bucketCount()':len(self.ids),
            'rewardReceiver(uint256)':self.inbox,'fees()':self.inbox_fees,'bucketId()':self.inbox_bucket,
            'needsRebalance(uint256)':int(self.rebalance),'bucketTotalShares(uint256)':100,
            'remoteIndividual(uint256,address)':0,'remoteCollective(uint256,address)':0,
            'buybackBalance(address)':0,
        }
        if selector==calldata('pending()')[:10]:return '0x'+''.join(f'{n:064x}' for n in self.inbox_pending)
        elif selector==calldata('bucketAt(uint256)',0)[:10]:value=self.ids[args[0]]
        elif selector==calldata('poolBucket(bytes32)',self.pool)[:10]:
            # A fixture shares the same token pair across independent reviewed
            # pool identities; this getter is selected by the currently read group.
            value=self.current_bucket
        elif selector==calldata('group(uint256)',7)[:10]:
            self.current_bucket=args[0]
            return '0x'+''.join(f'{n:064x}' for n in self.group_words)
        elif selector==calldata('get(bytes32)',self.pool)[:10]:return '0x'+''.join(f'{n:064x}' for n in self.config_words)
        elif selector==calldata('accounting(bytes32)',self.pool)[:10]:return '0x'+''.join(f'{n:064x}' for n in (self.accounting_words or self.config_words))
        elif selector==calldata('nativeAsset(bytes32)',self.pool)[:10]:value=self.native_wrapper
        elif selector==calldata('compoundBalance(uint256,address)',7,B)[:10]:value=self.reserves['0x'+f'{args[1]:040x}']
        else:
            for signature,value in values.items():
                types=signature[signature.index('(')+1:-1]
                placeholders=[A if typ=='address' else 0 for typ in types.split(',')] if types else []
                if selector==calldata(signature,*placeholders)[:10]:break
            else:raise AssertionError(f'Unexpected contract call: {data}')
        return '0x'+f'{value:064x}'
    def invoke(self,submitted=True):
        with patch.object(self.k,'submit',return_value=submitted) as submit:
            self.k.cycle()
        return submit
    def test_one_pool_operation_does_not_scan_nft_ids(self):
        self.ids=[7]
        submit=self.invoke()
        submit.assert_called_once_with('vault','rebalance(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'rebalance:7')
        calls=[call[1][0]['data'][:10] for call in self.rpc.calls if call[0]=='eth_call']
        self.assertNotIn(calldata('position(uint256)',0)[:10],calls)
        self.assertNotIn(calldata('ownerOf(uint256)',0)[:10],calls)
    def test_repeated_cycles_rotate_even_when_each_pool_needs_work(self):
        selected=[]
        for _ in range(4):selected.append(self.invoke().call_args.args[2][0])
        self.assertEqual(selected,[7,9,11,7])
    def test_scan_budget_limits_contract_reads(self):
        self.ids=list(range(1,101));self.k.batch_size=2
        self.rebalance=False;self.k.maintenance={'compound':False,'harvest':False}
        self.invoke()
        selector=calldata('group(uint256)',0)[:10]
        reads=[p for method,p in self.rpc.calls if method=='eth_call' and p[0]['data'].startswith(selector)]
        self.assertEqual(len(reads),2);self.assertEqual(self.k.state['bucket_cursor'],2)
    def test_empty_inventory_submits_nothing(self):
        self.ids=[];self.invoke().assert_not_called()
    def test_inventory_above_reviewed_limit_fails_closed(self):
        self.k.max_buckets=2
        with self.assertRaises(RpcError):self.invoke()
    def test_duplicate_inventory_ids_fail_before_submission(self):
        self.ids=[7,7]
        with self.assertRaises(RpcError):self.invoke()
    def test_zero_inventory_id_fails_before_submission(self):
        self.ids=[0]
        with self.assertRaises(RpcError):self.invoke()
    def test_malformed_group_is_skipped_and_cursor_advances(self):
        self.ids=[7];self.group_words.pop()
        self.invoke().assert_not_called();self.assertEqual(self.k.state['bucket_cursor'],1)
    def test_pool_identity_mismatch_never_submits(self):
        self.ids=[7];self.config_words[2]=500
        self.invoke().assert_not_called()
    def test_noncanonical_token_address_never_submits(self):
        self.ids=[7];self.config_words[0]=1<<200
        self.invoke().assert_not_called()
    def test_active_group_missing_lp_never_submits(self):
        self.ids=[7];self.group_words[1]=0
        self.invoke().assert_not_called()
    def test_parked_group_never_runs_lp_upkeep_even_with_reserves(self):
        self.ids=[7];self.group_words[7]=6;self.group_words[1]=0
        self.reserves[C]=100
        self.invoke().assert_not_called()
        calls=[p[0]['data'][:10] for method,p in self.rpc.calls if method=='eth_call']
        for signature,args in (('needsRebalance(uint256)',(7,)),
                               ('compoundBalance(uint256,address)',(7,C))):
            self.assertNotIn(calldata(signature,*args)[:10],calls)
    def test_parked_group_with_live_lp_fails_before_any_receiver_submission(self):
        self.ids=[7];self.group_words[7]=6
        self.inbox=int(A,16);self.inbox_pending=[100,0]
        self.invoke().assert_not_called()
    def test_parked_group_keeps_accounting_and_provenance_validation(self):
        self.ids=[7];self.group_words[7]=6;self.group_words[1]=0
        self.inbox=int(A,16);self.inbox_pending=[100,0]
        for field,wrong in ((0,0),(8,0),(13,0),(13,2),(14,int(C,16)),(14,1<<200)):
            with self.subTest(field=field):
                before=self.group_words[field];self.group_words[field]=wrong
                self.invoke().assert_not_called();self.group_words[field]=before
        self.accounting_words=list(self.config_words);self.accounting_words[0]=int(A,16)
        self.invoke().assert_not_called()
    def test_parked_pending_rewards_sync_while_paused_or_unpaused(self):
        self.ids=[7];self.group_words[7]=6;self.group_words[1]=0
        self.inbox=int(A,16);self.inbox_pending=[100,0]
        for paused in (False,True):
            with self.subTest(paused=paused):
                self.paused=paused
                self.invoke().assert_called_once_with('fees','syncExternal(uint256)',(7,),'external_rewards:7')
    def test_native_pool_uses_wrapped_accounting_asset_without_resorting(self):
        self.ids=[7];self.rebalance=False
        self.config_words[0]=0;self.config_words[2]=0;self.config_words[4]=123
        self.pool='0x'+keccak256(bytes.fromhex(''.join(f'{n:064x}' for n in self.config_words[:5]))).hex()
        self.group_words[0]=int(self.pool,16)
        self.accounting_words=list(self.config_words);self.accounting_words[0]=int(B,16)
        self.reserves[B]=17
        submit=self.invoke()
        submit.assert_called_once_with('compounder','compound(uint256,uint128,uint256)',(7,1,self.rpc.now+180),'compound:7')
    def test_wrong_native_wrapper_or_accounting_policy_never_submits(self):
        self.ids=[7];self.config_words[0]=0
        self.pool='0x'+keccak256(bytes.fromhex(''.join(f'{n:064x}' for n in self.config_words[:5]))).hex()
        self.group_words[0]=int(self.pool,16)
        self.accounting_words=list(self.config_words);self.accounting_words[0]=int(B,16)
        self.native_wrapper=int(C,16)
        self.invoke().assert_not_called()
        self.native_wrapper=int(B,16);self.accounting_words[2]+=1
        self.invoke().assert_not_called()
    def test_compound_reads_actual_local_pool_tokens(self):
        self.ids=[7];self.rebalance=False
        self.group_words[11]=int(A,16) # Canonical asset differs from local asset.
        self.reserves[C]=17
        submit=self.invoke()
        submit.assert_called_once_with('compounder','compound(uint256,uint128,uint256)',
            (7,1,self.rpc.now+180),'compound:7')
        selector=calldata('compoundBalance(uint256,address)',7,B)[:10]
        tokens=[p[0]['data'][-40:] for method,p in self.rpc.calls if method=='eth_call' and p[0]['data'].startswith(selector)]
        self.assertEqual(tokens,[B[2:],C[2:]])
    def test_paused_protocol_scans_receivers_without_lp_or_bridge_operations(self):
        self.paused=True;self.ids=[7]
        self.invoke().assert_not_called()
        calls=[p[0]['data'][:10] for method,p in self.rpc.calls if method=='eth_call']
        self.assertIn(calldata('rewardReceiver(uint256)',7)[:10],calls)
        self.assertNotIn(calldata('needsRebalance(uint256)',7)[:10],calls)
    def test_unknown_or_legacy_state_is_not_silently_reused(self):
        self.k.save();state=json.loads(self.k.path.read_text());state.pop('accounting_model')
        self.k.path.write_text(json.dumps(state))
        with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_legacy_manual_nft_config_rejected(self):
        self.cfg['positions']=[]
        with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_invalid_scan_limits_rejected(self):
        for settings in ({'max_per_cycle':0},{'max_per_cycle':1001},{'maximum_count':100001},
            {'max_per_cycle':3,'maximum_count':2}):
            self.cfg['bucket_discovery']=settings
            with self.subTest(settings=settings),self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_bucket_override_changes_bounds_without_manual_inventory(self):
        self.ids=[7];self.k.overrides={'7':{'minimum_liquidity':17}}
        self.assertEqual(self.invoke().call_args.args[2][1],17)
    def test_restart_retains_scan_cursor(self):
        self.k.batch_size=1;self.rebalance=False;self.k.maintenance={'compound':False,'harvest':False}
        self.invoke()
        restarted=Keeper(self.cfg,rpc=self.rpc)
        self.assertEqual(restarted.state['bucket_cursor'],1)
        self.assertEqual(restarted._bucket_batch()[0][1],9)
    def test_one_bad_group_does_not_starve_other_groups(self):
        valid_fields=[f'{n:064x}' for n in self.group_words]
        def group(bucket):
            if bucket==7:raise RpcError('Malformed first group')
            return valid_fields,[B,C]
        with patch.object(self.k,'_bucket',side_effect=group):submit=self.invoke()
        self.assertEqual(submit.call_args.args[2][0],9)
        self.assertEqual(self.k.state['bucket_cursor'],2)
    def test_pending_broadcast_stops_discovery(self):
        self.k.state['pending']={'hash':None,'nonce':7,'key':'rebalance:7'}
        with patch.object(self.k,'_bucket_batch') as batch:self.k.cycle()
        batch.assert_not_called()
    def test_persisted_state_cannot_be_reused_for_another_vault(self):
        self.k.save();self.cfg['contracts']['vault']=C
        with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_zero_share_group_never_submits(self):
        self.ids=[7]
        original=self.k.view
        def view(name,signature,*args):
            return 0 if signature=='bucketTotalShares(uint256)' else original(name,signature,*args)
        with patch.object(self.k,'view',side_effect=view):self.invoke().assert_not_called()
    def test_pool_occupancy_mismatch_never_submits(self):
        self.ids=[7]
        original=self.k.view
        def view(name,signature,*args):
            return 9 if signature=='poolBucket(bytes32)' else original(name,signature,*args)
        with patch.object(self.k,'view',side_effect=view):self.invoke().assert_not_called()
    def test_outbound_group_never_rebalances_compounds_or_harvests(self):
        self.ids=[7];self.group_words[7]=2
        self.reserves[C]=100
        self.invoke().assert_not_called()
    def test_live_submission_persists_advanced_cursor_before_signing(self):
        self.ids=[7];self.enable_test_signer()
        def run(*args,**kwargs):
            persisted=json.loads(self.k.path.read_text())
            self.assertEqual(persisted['bucket_cursor'],1)
            self.assertEqual(persisted['accounting_model'],ACCOUNTING_MODEL)
            self.assertEqual(persisted['pending']['key'],'rebalance:7')
            return subprocess.CompletedProcess(args[0],0,H,'')
        with patch('subprocess.run',side_effect=run):self.k.cycle()
    def test_external_pending_rewards_sync_before_lp_maintenance(self):
        self.ids=[7];self.inbox=int(A,16);self.inbox_pending=[0,500]
        self.invoke().assert_called_once_with('fees','syncExternal(uint256)',(7,),'external_rewards:7')
    def test_external_rewards_can_sync_paused_and_remote(self):
        self.ids=[7];self.paused=True;self.inbox=int(A,16);self.inbox_pending=[300,0]
        for status in (1,2,3,4):
            with self.subTest(status=status):
                self.group_words[7]=status
                self.invoke().assert_called_once_with('fees','syncExternal(uint256)',(7,),'external_rewards:7')
    def test_empty_external_receiver_does_not_create_transaction(self):
        self.ids=[7];self.paused=True;self.inbox=int(A,16)
        self.invoke().assert_not_called()
    def test_external_receiver_binding_mismatch_fails_closed(self):
        self.ids=[7];self.inbox=int(A,16);self.inbox_pending=[1,0]
        for field,value in (('inbox_fees',int(C,16)),('inbox_bucket',9),('inbox',1<<200)):
            with self.subTest(field=field):
                before=getattr(self,field);setattr(self,field,value)
                self.invoke().assert_not_called();setattr(self,field,before)
    def test_external_receiver_pending_malformed_fails_closed(self):
        self.ids=[7];self.inbox=int(A,16);self.inbox_pending=[1]
        self.invoke().assert_not_called()
    def test_external_sync_can_be_explicitly_disabled(self):
        self.ids=[7];self.paused=True;self.inbox=int(A,16);self.inbox_pending=[1,0]
        self.k.maintenance={'sync_external_rewards':False}
        self.invoke().assert_not_called()
        calls=[p[0]['data'][:10] for method,p in self.rpc.calls if method=='eth_call']
        self.assertNotIn(calldata('rewardReceiver(uint256)',7)[:10],calls)
    def test_external_sync_flag_rejects_non_boolean_configuration(self):
        for value in ('false',0,1,None):
            with self.subTest(value=value):
                self.cfg['maintenance']={'sync_external_rewards':value}
                with self.assertRaises(ValueError):Keeper(self.cfg,rpc=self.rpc)
    def test_external_sync_keeps_durable_pending_identity_before_signing(self):
        self.ids=[7];self.paused=True;self.inbox=int(A,16);self.inbox_pending=[500,0]
        self.enable_test_signer()
        def run(*args,**kwargs):
            state=json.loads(self.k.path.read_text())
            self.assertEqual(state['bucket_cursor'],1)
            self.assertEqual(state['pending']['to'],B)
            self.assertEqual(state['pending']['data'],calldata('syncExternal(uint256)',7))
            self.assertEqual(state['pending']['value'],0)
            return subprocess.CompletedProcess(args[0],0,H,'')
        with patch('subprocess.run',side_effect=run):self.k.cycle()
