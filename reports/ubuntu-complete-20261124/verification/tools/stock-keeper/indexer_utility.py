"""Finite actual-Anvil indexer CLI ingestion/restart/empty-branch reorg only.

No new transaction, signing, sealing or old-history/provider completeness claim.
Controls touch only future empty blocks after the recovered keeper receipt.
"""
from pathlib import Path
import hashlib,http.client,json,re,sqlite3,time


def need(ok,reason):
    if not ok:raise ValueError(reason)


def save(path,value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    need(len(raw)<=1024*1024,'Indexer receipt bound')
    with path.open('xb')as stream:stream.write(raw)


def norm(log):
    return(int(log['blockNumber'],16),log['blockHash'].lower(),log['transactionHash'].lower(),int(log['logIndex'],16),log['address'].lower(),log['data'].lower(),tuple(x.lower()for x in log['topics']))


def database(path):
    connection=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    try:
        need(connection.execute('PRAGMA integrity_check').fetchone()==('ok',),'Indexer database integrity')
        cursors=connection.execute('SELECT chain,next_block,config FROM cursors').fetchall();need(len(cursors)==1,'Indexer cursor inventory')
        blocks=connection.execute('SELECT number,hash,parent,timestamp FROM blocks ORDER BY number').fetchall()
        logs=[json.loads(row[0])for row in connection.execute('SELECT raw FROM logs ORDER BY block_number,log_index')]
        need(bool(blocks)and cursors[0][1]==blocks[-1][0]+1,'Indexer cursor boundary')
        return{'chain':cursors[0][0],'next_block':cursors[0][1],'blocks':blocks,'logs':[norm(log)for log in logs]}
    finally:connection.close()


def run(source,out,cfg,operation):
    from zzz_ops.rpc import Rpc
    from zzz_ops.abi import keccak256
    root=out/'indexer';root.mkdir(mode=0o700)
    result={'schema':1,'scope':'actual isolated actor receipt + incremental/restart and 13-empty-block future branches replacing TWO CONFIRMED indexed headers','success':False,'production_approved':False,'complete_original_NFT_history':False,'orphaned_financial_log_deletion_qualified':False,'public_transactions':0,'signing':False,'sealing':False,'controls':[]}
    rpc=Rpc(['http://127.0.0.1:19592'],4663,timeout=5,retries=1)
    state_path=Path(cfg['state_path']);state_bytes=state_path.read_bytes();state=json.loads(state_bytes)
    anchor=state.get('receipt_anchor');need(type(anchor)is dict and type(anchor.get('number'))is int,'Recovered actor receipt anchor required')
    tx=state['last_fee_observation']['transaction'];receipt=rpc.call('eth_getTransactionReceipt',[tx])
    need(type(receipt)is dict and receipt['status']=='0x1'and receipt['transactionHash'].lower()==tx.lower()and int(receipt['blockNumber'],16)==anchor['number']and receipt['blockHash']==anchor['hash'],'Actual actor receipt differs')
    vault=cfg['contracts']['vault'];topic='0x'+keccak256(b'FeesCollected(uint256,uint256,uint256)').hex()
    need(any(log['address'].lower()==vault and log['topics']and log['topics'][0]==topic for log in receipt['logs']),'Actual actor collection event absent')
    start=anchor['number'];header=rpc.call('eth_getBlockByNumber',[hex(start),False]);need(header['hash']==anchor['hash']and start>0,'Actual collection header differs')
    config={'chain_id':4663,'rpc_urls':['http://127.0.0.1:19592'],'contracts':[vault],'start_block':start,'start_parent_hash':header['parentHash'],'confirmations':12,'block_chunk':100,'max_reorg_depth':256,'database':str(root/'events.sqlite'),'lock_path':str(root/'indexer.lock'),'poll_seconds':1}
    config_path=root/'config.json';save(config_path,config);db=root/'events.sqlite';stage='pause_owned_interval_mining';paused=False
    def control(method,params):
        allowed=(method=='anvil_setIntervalMining'and params in([0],[1])or method=='evm_snapshot'and params==[]or method=='anvil_mine'and params==['0xd']or method=='evm_revert'and len(params)==1 and type(params[0])is str and re.fullmatch('0x[0-9a-fA-F]{1,64}',params[0])is not None or method=='evm_setNextBlockTimestamp'and len(params)==1 and type(params[0])is int and 0<params[0]<1<<63 and abs(params[0]-time.time())<=60)
        need(allowed and len(result['controls'])<16,'Closed owned indexer control allowlist')
        request={'jsonrpc':'2.0','id':1+len(result['controls']),'method':method,'params':params};raw=json.dumps(request,separators=(',',':')).encode();need(len(raw)<=1024,'Owned control request bound')
        intent={'method':method,'parameters':params,'state':'attempted_outcome_unknown'};result['controls'].append(intent)
        conn=http.client.HTTPConnection('127.0.0.1',19592,timeout=10);deadline=time.monotonic()+10
        try:
            conn.request('POST','/',raw,{'Content-Type':'application/json'});response=conn.getresponse();need(response.status==200,'Owned control HTTP status')
            parts=[];size=0
            while True:
                need(time.monotonic()<deadline,'Owned control deadline');part=response.read1(min(4096,4097-size));need(time.monotonic()<deadline,'Owned control deadline')
                if not part:break
                size+=len(part);need(size<=4096,'Owned control response bound');parts.append(part)
            value=json.loads(b''.join(parts));need(type(value)is dict and value.get('jsonrpc')=='2.0'and type(value.get('id'))is int and value['id']==request['id']and'result'in value and'error'not in value,'Owned control response identity')
            intent.update(state='confirmed_response',result=value['result']);return value['result']
        finally:conn.close()
    def index(label):
        operation(label,['-m','indexer.monitor','--config',config_path,'--once'],timeout=45)
        value=database(db);need(value['chain']==4663 and value['blocks'][0][0]==start,'Indexer actual start/chain differs')
        expected=rpc.call('eth_getLogs',[{'address':[vault],'fromBlock':hex(start),'toBlock':hex(value['blocks'][-1][0])}])
        need(sorted(value['logs'])==sorted(norm(log)for log in expected),'Actual indexed logs differ from actual node')
        need(any(row[2]==tx.lower()for row in value['logs']),'Actual actor collection log missing in indexer')
        return value
    try:
        paused=True;control('anvil_setIntervalMining',[0])
        stage='index_initial';initial=index('indexer-initial')
        # --once intentionally processes one bounded chunk; catch up at most
        # three more chunks, never changing the configured chunk/reorg budget.
        for ordinal in range(3):
            tip=int(rpc.call('eth_getBlockByNumber',['latest',False])['number'],16)
            if initial['next_block']>tip-(config['confirmations']-1):break
            initial=index('indexer-catchup-%d'%ordinal)
        confirmed=int(rpc.call('eth_getBlockByNumber',['latest',False])['number'],16)-(config['confirmations']-1)
        need(initial['next_block']==confirmed+1,'Actual initial indexer remains behind its bounded confirmed partition')
        stage='index_restart';restarted=index('indexer-restart');need(restarted==initial,'Indexer restart duplicated or rewrote same-head data')
        stage='snapshot_after_actor';base=rpc.call('eth_getBlockByNumber',['latest',False]);need(int(base['number'],16)>=start,'Snapshot predates actor anchor');snapshot=control('evm_snapshot',[]);need(type(snapshot)is str and snapshot.startswith('0x'),'Owned snapshot ID')
        stage='old_empty_branch';control('anvil_mine',['0xd']);oldtip=rpc.call('eth_getBlockByNumber',['latest',False]);need(int(oldtip['number'],16)==int(base['number'],16)+13,'Owned old branch height');old=index('indexer-old-empty-branch')
        stage='new_empty_branch';need(control('evm_revert',[snapshot])is True,'Owned future-branch revert failed');now=rpc.call('eth_getBlockByNumber',['latest',False]);need(now['hash']==base['hash'],'Owned snapshot head differs')
        control('evm_setNextBlockTimestamp',[max(int(oldtip['timestamp'],16)+1,int(time.time()))]);control('anvil_mine',['0xd'])
        newtip=rpc.call('eth_getBlockByNumber',['latest',False]);need(newtip['number']==oldtip['number']and newtip['hash']!=oldtip['hash'],'Owned new branch does not differ')
        stage='index_reorg';reconciled=index('indexer-reorg');need(reconciled['logs']==old['logs']==initial['logs'],'Empty-branch reorg lost or duplicated actual earlier logs')
        oldrows={row[0]:row for row in old['blocks']};newrows={row[0]:row for row in reconciled['blocks']};cut=int(base['number'],16)
        changed=[n for n in oldrows if n>cut]
        need(set(oldrows)==set(newrows)and changed==[cut+1,cut+2]and all(oldrows[n]==newrows[n]for n in oldrows if n<=cut)and all(oldrows[n][1]!=newrows[n][1]for n in changed),'Reorg did not replace exactly two future confirmed empty branch headers')
        final_anchor=rpc.call('eth_getBlockByNumber',[hex(start),False]);need(final_anchor['hash']==anchor['hash']and state_path.read_bytes()==state_bytes,'Indexer experiment changed recovered actor anchor/journal')
        result.update(success=True,start=start,actual_actor_transaction=tx,actual_log_count=len(initial['logs']),initial_next_block=initial['next_block'],final_next_block=reconciled['next_block'],confirmations=12,mined_empty_blocks_per_branch=13,replaced_empty_headers=2,same_actor_anchor=True,same_actor_journal=True,configuration_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest())
    except Exception as exc:result.update(failure_stage=stage,error_class=type(exc).__name__)
    finally:
        if paused:
            try:control('anvil_setIntervalMining',[1]);result['one_second_interval_restored']=True
            except Exception as exc:result.update(success=False,interval_restore_error_class=type(exc).__name__)
        try:
            preserved=rpc.call('eth_getBlockByNumber',[hex(start),False])
            result['same_actor_anchor']=preserved['hash']==anchor['hash']
            result['same_actor_journal']=state_path.read_bytes()==state_bytes
            if not(result['same_actor_anchor']and result['same_actor_journal']):result['success']=False
        except Exception as exc:result.update(success=False,actor_preservation_error_class=type(exc).__name__)
        save(root/'RESULT.json',result)
    return result
