"""One authorized local mempool cleanup, with fixed identity and archived state checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,urllib.request,hashlib

HOME=Path(__file__).parent
RUN=HOME.parent/'runs/run-20261022-001857-b830df'
RPC='http://127.0.0.1:57306'
HASH='0x7df63aa0d6bf24461b7fdf1858b778c7d1e051d904a11a86ad0dd538a9400cc6'
OWNER='0x70997970c51812dc3a010c7d01b50e0d17dc79c8'
TARGET='0x2279b7a0a67db372996a5fab50d91eaa73d2ebe6'
GENESIS='0x19df3ff29a52f43ea4c9120bcbf65ec6a3d707f90c4e6537d54274cfe3f4d439'
OUT=HOME/'reconciliation.json'
assert not OUT.exists(),'Existing record must be reviewed; never rerun cleanup blindly'
running=json.loads((RUN/'running.json').read_text())
manifest=json.loads((RUN/'website-manifest.json').read_text())
assert running['rpc']==RPC and running['url']=='http://127.0.0.1:8902'
assert manifest['genesis_hash']==GENESIS and manifest['contracts']['vault']['address'].lower()==TARGET
record={'time_utc':datetime.now(timezone.utc).isoformat(),'scope':'User-authorized removal of this exact unmined local mint; no signing, chain reset or nonce/balance/storage edit','hash':HASH,'actions':[],'browser_journal':'Unchanged; browser archive and MetaMask local nonce-history reset still required'}
def save():OUT.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
def rpc(method,params=[]):
    request=urllib.request.Request(RPC,json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=10) as response: result=json.load(response)
    if 'error' in result:raise RuntimeError(result['error'])
    return result['result']
def hashes(value):
    if isinstance(value,dict):
        if 'hash' in value and 'nonce' in value:return {value['hash']}
        result=set()
        for v in value.values():result|=hashes(v)
        return result
    if isinstance(value,list):return set().union(*(hashes(v) for v in value))
    return set()
def snapshot():
    assert rpc('eth_chainId')=='0x7a69'
    assert rpc('eth_getBlockByNumber',['0x0',False])['hash']==GENESIS
    block=rpc('eth_getBlockByNumber',['latest',False]);number=block['number']
    return {'block':{k:block[k] for k in ['number','hash','stateRoot','timestamp']},
            'accounts':{a:{'balance':rpc('eth_getBalance',[a,number]),'nonce':rpc('eth_getTransactionCount',[a,number])} for a in running['accounts']},
            'receipt':rpc('eth_getTransactionReceipt',[HASH]),'transaction':rpc('eth_getTransactionByHash',[HASH]),
            'pool':rpc('txpool_content'),'pool_status':rpc('txpool_status')}
try:
    record['before']=snapshot();tx=record['before']['transaction']
    assert record['before']['receipt'] is None and tx and tx['blockNumber'] is None
    assert tx['hash']==HASH and tx['from'].lower()==OWNER and tx['to'].lower()==TARGET
    assert tx['nonce']=='0x23' and tx['chainId']=='0x7a69' and tx['input']=='0x21bf772d'
    assert int(tx['value'],16)==50_000_000_000_000_000
    assert record['before']['accounts'][OWNER]['nonce']=='0x19'
    assert hashes(record['before']['pool'])=={HASH}
    assert rpc('eth_getCode',[TARGET,'latest'])==manifest['contracts']['vault']['runtime_code']
    save()
    result=rpc('anvil_dropTransaction',[HASH]);record['actions'].append({'method':'anvil_dropTransaction','params':[HASH],'result':result});save()
    # Old Anvil builds may not remove queued transactions by hash. Narrow fallback
    # is this sender only, and only after rechecking that the exact mint is alone.
    if rpc('eth_getTransactionByHash',[HASH]) is not None:
        assert rpc('eth_getTransactionReceipt',[HASH]) is None
        assert hashes(rpc('txpool_content'))=={HASH}
        assert rpc('eth_getTransactionCount',[OWNER,'latest'])=='0x19'
        result=rpc('anvil_removePoolTransactions',[OWNER]);record['actions'].append({'method':'anvil_removePoolTransactions','params':[OWNER],'result':result});save()
    record['after']=snapshot()
    assert record['after']['receipt'] is None and record['after']['transaction'] is None,'Target still queued; no broad reset permitted'
    assert not hashes(record['after']['pool'])
    assert record['before']['accounts']==record['after']['accounts']
    assert record['before']['block']['stateRoot']==record['after']['block']['stateRoot'],'State changed; inspect before any further action'
    record['pass']=True;record['assertions']=['Exact pending mint removed','No receipt or execution','Queue empty','Both wallet balances and nonces identical','Complete chain stateRoot unchanged: all NFT/LP/reward contract storage preserved']
    save();print(json.dumps({'pass':True,'removed_hash':HASH,'chain_state_unchanged':True,'browser_step_pending':True}))
except Exception as exc:
    record['pass']=False;record['error']=str(exc);save();raise
