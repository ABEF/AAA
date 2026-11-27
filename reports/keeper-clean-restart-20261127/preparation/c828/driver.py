"""Three finite c828 fixture actions. No prior scenario or test body is invoked."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,copy,json,os,re,time
import shared as S
sys.path.insert(0,str(S.SOURCE))

TX_FIELDS=('hash','from','to','input','nonce','value','gas','gasPrice','type','chainId',
    'maxFeePerGas','maxPriorityFeePerGas','blockHash','blockNumber','transactionIndex')


def private_copy(path,raw):
    S.need(len(raw)<=2097152,'copy_bound')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def setup_transaction(label,address,data):
    nonce=S.request('eth_getTransactionCount',[S.OWNER,'latest'])
    S.need(nonce==S.request('eth_getTransactionCount',[S.OWNER,'pending']),'setup_nonce')
    envelope={'from':S.OWNER,'to':address,'data':data,'value':'0x0','nonce':nonce,'gas':hex(24000000)}
    S.request('eth_call',[envelope,'latest']);estimate=int(S.request('eth_estimateGas',[envelope]),16)
    padded=(estimate*125+99)//100;S.need(padded<=24000000,'setup_gas');envelope['gas']=hex(padded)
    digest=S.request('eth_sendTransaction',[envelope]);S.mine()
    receipt=S.request('eth_getTransactionReceipt',[digest]);transaction=S.request('eth_getTransactionByHash',[digest])
    S.need(type(receipt)is dict and receipt['status']=='0x1'and transaction['input']==data
        and transaction['from'].lower()==S.OWNER and transaction['nonce']==nonce,'setup_receipt')
    return{'label':label,'hash':digest,'estimate':estimate,'padded':padded,'receipt':receipt,
        'transaction_without_signature':{key:transaction.get(key)for key in TX_FIELDS}}


def bootstrap():
    S.need(not(S.OUT/'BOOTSTRAP.json').exists()and not(S.ACTOR/'config.json').exists(),'fresh_bootstrap')
    fixture=S.value(S.ROOT/'fixture.json');roles=fixture['roles'];a=lambda role:roles[role]['address']
    from zzz_ops.abi import keccak256
    readiness_end=time.monotonic()+20
    for readiness_attempt in range(20):
        remaining=readiness_end-time.monotonic();S.need(remaining>0,'node_readiness_deadline')
        try:
            S.need(S.request('eth_chainId',[],timeout=min(1.0,remaining))=='0x1237','node_readiness_wrong_chain')
            break
        except(ConnectionError,OSError):
            S.need(readiness_attempt<19 and time.monotonic()<readiness_end,'node_readiness_exhausted')
            time.sleep(min(.25,max(0,readiness_end-time.monotonic())))
    else:raise ValueError('node_readiness_exhausted')
    before=S.request('eth_getBlockByNumber',['latest',False])
    S.need(before['hash']=='0x6880a335003c0f15184918ca84724ed5c79c27f9115a86a1475eedc683bc2ddf','immutable_base_head')
    for role,row in roles.items():
        code=S.request('eth_getCode',[row['address'],'latest'])
        S.need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==row['runtime_keccak256'].lower(),'base_runtime')
    S.need(len(roles)==39 and S.one(a('access'),'isSealed()')==1 and S.one(a('nft'),'mintedCount()')==2,'base_graph')
    S.request('evm_setIntervalMining',[0]);S.request('evm_setAutomine',[False]);fresh=S.mine()
    # Ordinary empty mining uses Anvil's current wall clock; no clock setter exists here.
    secrets=S.ACTOR/'secrets';secrets.mkdir(mode=0o700)
    password=secrets/'password';key=secrets/'keeper'
    private_copy(password,os.urandom(32).hex().encode()+b'\n')
    environment=S.environment();environment['CAST_PASSWORD']=password.read_text().strip()
    S.command([S.ROOT/'tools/cast','wallet','new',secrets,'keeper'],env=environment,seconds=30,secret_output=True)
    del environment['CAST_PASSWORD']
    S.need(key.is_file(),'new_disposable_key');os.chmod(key,0o600)
    _,out,err=S.command([S.ROOT/'tools/cast','wallet','address','--keystore',key,'--password-file',password],seconds=30)
    S.need(not err,'new_sender_output');sender=out.decode('utf8','strict').strip().lower()
    S.need(re.fullmatch('0x[0-9a-f]{40}',sender)is not None and sender not in{row['address']for row in roles.values()}|{S.OWNER},'new_sender')
    S.request('anvil_setBalance',[sender,hex(10**18)]);S.request('anvil_setBalance',[S.OWNER,hex(10**18)])
    S.request('anvil_impersonateAccount',[S.OWNER]);setup=[];feed_before={}
    for label,address in sorted(fixture['feeds'].items()):
        values=S.call(address,'latestRoundData()');S.need(len(values)==5 and 0<values[1]<1<<255,'mock_feed')
        feed_before[label]={'address':address,'raw_words':values}
        stamp=int(S.fresh_head()['timestamp'],16)
        feed_data='0x'+keccak256(b'set(int256,uint256,uint256)').hex()[:8]+''.join(f'{item:064x}'for item in(values[1],stamp,stamp))
        setup.append(setup_transaction('refresh_mock_feed:'+label,address,feed_data))
    S.need(len(setup)==4,'four_feed_setup')
    setup.append(setup_transaction('enable_new_disposable_keeper',a('access'),S.encode('setKeeper(address,bool)',sender,True)))
    S.request('anvil_stopImpersonatingAccount',[S.OWNER])
    names=('access','vault','strategy','fees','compounder','buyback','pools','rewards','liquidity','balancing_router',
        'lp_balance_math','lp_position_executor','portfolio_policy','protocol_policy','rebalance_confirmation','oracle','contribution_pricing','nft')
    contracts={role:a(role)for role in names};pins={role:roles[role]['runtime_keccak256'].lower()for role in names}
    contracts.update(principal_exit=a('migration'),pool_manager=S.CORE,state_view=S.STATE)
    pins.update(principal_exit=roles['migration']['runtime_keccak256'].lower(),pool_manager=S.CORE_HASH,state_view=S.STATE_HASH,
        idle_compounding_budget=roles['migration_budget']['runtime_keccak256'].lower())
    config={'chain_id':4663,'accounting_model':'shared-pools-v2','accounting_version':7,'custody_version':5,'protocol_policy_version':1,
        'portfolio_version':2,'maintenance_policy_version':3,'rebalance_confirmation_version':3,'fee_intake_version':1,'lp_routing_version':3,
        'execution_quality_version':1,'execution_price_version':1,'royalty_settlement_version':4,'rpc_urls':['http://127.0.0.1:19627'],
        'sender':sender,'contracts':contracts,'code_hashes':pins,'idle_compounding_budget':a('migration_budget'),'reviewed_for_live_use':True,
        'cast_binary':str(S.ROOT/'tools/cast'),'keystore':str(key),'password_file':str(password),'interval_seconds':240,'confirmations':12,
        'max_gas_limit':24000000,'max_gas_price_wei':'5000000000','max_transaction_cost_wei':'10000000000000000',
        'max_daily_cost_wei':'50000000000000000','l1_fee_allowance_wei':'0','receipt_fee_policy':'included','revert_cooldown_seconds':3600,
        'state_path':str(S.ACTOR/'state.json'),'health_path':str(S.ACTOR/'health.json'),'lock_path':str(S.ACTOR/'keeper.lock'),
        'bucket_discovery':{'maximum_count':4,'max_per_cycle':4},'maintenance':{'compound':False,'compound_idle':False,'harvest':True,
        'minimum_liquidity':1,'harvest_interval_seconds':3600},'bucket_overrides':{},'adaptive_range':{'enabled':False},
        'royalty_conversion':{'enabled':False},'lp_conversion':{'enabled':False},'metadata_refresh':{'enabled':False},
        'principal_distribution':{'enabled':False},'buybacks':[]}
    private_copy(S.ACTOR/'config.json',S.enc(config))
    for _ in range(12):S.mine()
    S.need(S.one(a('strategy'),'needsRebalance(uint256)',S.BUCKET)==0 and S.one(a('strategy'),'rangeUpdatePending(uint256)',S.BUCKET)==0,'harvest_partition')
    S.save('FINANCIAL_INITIAL.json',S.physical(fixture))
    S.save('BOOTSTRAP.json',{'schema':1,'fresh_sender':sender,'setup_transactions':setup,'setup_transaction_count':5,
        'local_balance_funding_calls':2,'mock_feed_before':feed_before,'base_head':before,'first_fresh_head':fresh,
        'configuration_sha256':S.sha(S.read(S.ACTOR/'config.json')),'clock_overrides':0,'deployments':0,'new_seals':0,
        'old_test_bodies_run':0,'public_transactions':0,'production_approved':False})


def capture_include():
    S.need((S.ROOT/'control/SOURCE_FENCED.json').exists()and not(S.OUT/'INCLUDED.json').exists(),'source_fenced_before_capture')
    fence=S.value(S.ROOT/'control/SOURCE_FENCED.json');S.need(fence['source_group_empty']is True and fence['restart_inhibited']is True,'source_fence')
    raw=S.read(S.ACTOR/'state.json');state=S.decode(raw);pending=state['pending'];config_raw=S.read(S.ACTOR/'config.json');config=S.decode(config_raw)
    S.need(type(pending)is dict and re.fullmatch('0x[0-9a-f]{64}',pending['hash'])is not None and pending['nonce']==state['next_nonce']==0,'actual_known_pending')
    digest=pending['hash'];transaction=S.request('eth_getTransactionByHash',[digest])
    S.need(type(transaction)is dict and transaction['blockNumber']is None and S.request('eth_getTransactionReceipt',[digest])is None
        and transaction['from'].lower()==config['sender']and transaction['to'].lower()==pending['to']and transaction['input']==pending['data']
        and int(transaction['nonce'],16)==0 and int(transaction['value'],16)==0,'actual_node_pending_binding')
    budget=S.value(S.SHARED/'BUDGET.json');S.need(budget['raw_attempts']==budget['raw_forwarded']==1
        and budget['accepted_hash']==digest and budget['accepted_transaction_verified']is True,'actual_once_forward')
    private_copy(S.OUT/'PENDING.json',raw);private_copy(S.OUT/'ORIGINAL_CONFIG.json',config_raw)
    # Native backup runs once on this NEW source journal; original package is not reused.
    argv=['/usr/bin/python3','-S','-B',str(S.SOURCE/'scripts/keeper-recovery.py'),'backup','--config',str(S.ACTOR/'config.json'),
        '--working-directory',str(S.SOURCE),'--output',str(S.OUT/'bundle')]
    code,out,err=S.command(argv,seconds=75);S.need(code==0 and not err,'native_capture')
    match=re.search('^Manifest SHA-256: ([0-9a-f]{64})$',out.decode('utf8','strict'),re.M);S.need(match is not None,'native_manifest_pin')
    S.need(S.read(S.OUT/'bundle/journal.json')==raw and S.read(S.ACTOR/'state.json')==raw,'capture_exact_pending')
    deadline=int(pending['data'][-64:],16)
    S.need(pending['data']==S.encode('collectFees(uint256,uint256)',S.BUCKET,deadline),'exact_harvest_calldata')
    S.need(int(S.fresh_head()['timestamp'],16)<=deadline and time.time()+10<=deadline,'harvest_deadline_before_inclusion')
    S.mine()
    for _ in range(11):S.mine()
    receipt=S.request('eth_getTransactionReceipt',[digest]);head=S.fresh_head()
    S.need(type(receipt)is dict and receipt['status']=='0x1'and receipt['transactionHash']==digest
        and int(head['number'],16)-int(receipt['blockNumber'],16)+1==12,'actual_twelve_confirmations')
    block=S.request('eth_getBlockByHash',[receipt['blockHash'],False]);S.need(int(block['timestamp'],16)<=deadline,'actual_inclusion_deadline')
    transaction=S.request('eth_getTransactionByHash',[digest])
    canonical={'schema':1,'hash':digest,'receipt':receipt,'receipt_block':block,'head':head,'confirmations':12,
        'transaction_without_signature':{key:transaction.get(key)for key in TX_FIELDS}}
    S.save('CANONICAL.json',canonical);S.save('FINANCIAL_INCLUDED.json',S.physical(S.value(S.ROOT/'fixture.json')))
    S.save('INCLUDED.json',{'schema':1,'accepted_hash':digest,'pending_journal_sha256':S.sha(raw),
        'configuration_sha256':S.sha(config_raw),'backup_manifest_sha256':match[1],
        'native_backup_stdout_sha256':S.sha(out),'native_backup_returncode':code,'actual_node_pending_before_inclusion':True,
        'confirmations':12,'harvest_deadline':deadline,'actual_inclusion_timestamp':int(block['timestamp'],16),
        'raw_attempts':1,'raw_forwarded':1,'clock_overrides':0,'source_journal_unchanged':S.read(S.ACTOR/'state.json')==raw})


def final():
    S.need(not(S.OUT/'FINANCIAL_FINAL.json').exists(),'final_once')
    source=S.read(S.ACTOR/'state.json');S.need(source==S.read(S.OUT/'PENDING.json'),'source_journal_preserved')
    final=S.physical(S.value(S.ROOT/'fixture.json'));S.save('FINANCIAL_FINAL.json',final)
    S.need(final==S.value(S.OUT/'FINANCIAL_INCLUDED.json'),'post_inclusion_financial_unchanged')
    budget=S.value(S.SHARED/'BUDGET.json');S.need(budget['raw_attempts']==budget['raw_forwarded']==budget['transaction_method_attempts']==1,'no_recovery_resend')
    digest=S.value(S.OUT/'INCLUDED.json')['accepted_hash'];receipt=S.request('eth_getTransactionReceipt',[digest])
    S.need(receipt==S.value(S.OUT/'CANONICAL.json')['receipt'],'canonical_receipt_unchanged')
    S.save('FINAL_CHAIN.json',{'schema':1,'accepted_hash':digest,'budget':S.value(S.SHARED/'BUDGET.json'),
        'source_journal_sha256':S.sha(source),'receipt_unchanged':True,'post_inclusion_financial_unchanged':True,
        'node_nonce_latest':int(S.request('eth_getTransactionCount',[S.value(S.ACTOR/'config.json')['sender'],'latest']),16),
        'node_nonce_pending':int(S.request('eth_getTransactionCount',[S.value(S.ACTOR/'config.json')['sender'],'pending']),16),
        'public_transactions':0,'production_approved':False,'clock_overrides':0})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('bootstrap','capture-include','final','fresh-head'));a=p.parse_args()
    S.namespace_guard()
    if a.action=='fresh-head':S.mine();print('{"fresh_head":true}')
    else:globals()[a.action.replace('-','_')]();print(json.dumps({'completed':a.action}))
