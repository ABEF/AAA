"""Hydrate exact preserved synthetic rows; no population or old test execution."""
from pathlib import Path
import copy,hashlib,json,sqlite3
from frontend_api.service import Projection
from tests_python.history_scale_rehearsal import ScaleFixture
from tests_python.test_seadrop_consumer import SeaDropAPI
from zzz_ops.abi import keccak256


def need(ok,message):
 if not ok:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def json_bytes(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def tables(path):
    connection=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        need(connection.execute('PRAGMA integrity_check').fetchone()==('ok',),'Database integrity')
        return {t:dict(rows=len(rows),sha256=sha(json_bytes(rows)))for t in ('cursors','blocks','logs')for rows in [connection.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall()]}
    finally:connection.close()


def hydrate(old,folder,case):
    """Hydrate saved rows; never call EpochFixture.__init__/_populate/run."""
    OLD=old
    cfg=json.loads((OLD/'bundle/profile.json').read_bytes())
    cfg['earnings_history'].pop('checkpoint',None)
    previous=cfg.pop('predecessors');configs=[]
    for item in previous:
        old=copy.deepcopy(cfg);old.update(copy.deepcopy(item));old.pop('retirement_transaction_hash',None);configs.append(old)
    configs.append(copy.deepcopy(cfg));cfg['predecessors']=previous
    f=ScaleFixture.__new__(ScaleFixture);f.case=case;f.root=folder
    f.template=SeaDropAPI(case);f.original_life=f.template.p._verify_deployment(f.template.block())
    f.configs=configs;f.config=cfg;f.profiles=copy.deepcopy(cfg['earnings_history']['deployments'])
    f.rows=[];f.roles=[];f.address_epoch={};f.codes={};f.birth={};f.receipts={};f.calls=[]
    f.starts=[c['deployment_block']for c in configs];f.edges=[140,240];f.head=310;f.safe=299
    f.pair=['0x'+'00'*20,'0x'+format(20,'040x')];f.royalties=['0x'+'00'*20,'0x'+format(21,'040x')]
    f.reorg=None;f.unavailable=False;f.retired_claims_unavailable=False;f.late_assets=[]
    f.getter_overrides={};f.indexes=[];f.model_cache={};f._owner_cache={};f.controlled_getters=0
    from frontend_api.lineage import SHARED_DEPENDENCY_ROLES
    for epoch,c in enumerate(configs):
        db=folder/f'epoch-{epoch}.sqlite';raw=(OLD/f'fixture-001/epoch-{epoch}.sqlite').read_bytes()
        need(len(raw)<16*1024*1024,'Preserved database byte bound')
        for suffix in ('-wal','-journal'):
            side=Path(str(OLD/f'fixture-001/epoch-{epoch}.sqlite')+suffix)
            need(not side.exists(),'Unexpected original database sidecar')
        with db.open('xb')as stream:stream.write(raw)
        connection=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
        try:f.rows.append([json.loads(r[0])for r in connection.execute('SELECT raw FROM logs ORDER BY block_number,log_index')])
        finally:connection.close()
        c['history']['database']=str(db)
        if epoch<2:cfg['predecessors'][epoch]['history']['database']=str(db)
        else:cfg['history']['database']=str(db)
        roles={r:c['contracts'][r]['address']for r in ('nft','vault','rewards','royalties','handoff')}
        for role,item in c['contracts'].items():
            code=f.template.rpc.codes[f.template.config['contracts'][role]['address']]
            need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==item['code_hash'],'Saved dependency/runtime identity differs from fixture source')
            f.codes[item['address']]=code;f.birth[item['address']]=0 if role in SHARED_DEPENDENCY_ROLES else f.starts[epoch]
            if role not in SHARED_DEPENDENCY_ROLES:f.address_epoch[item['address']]=epoch,role
        for number,role in enumerate(('fees','membership'),40):
            item=f.profiles[epoch][role];code=bytes([0x60,number,epoch]);need('0x'+keccak256(code).hex()==item['code_hash'],'Saved emitter runtime differs')
            f.codes[item['address']]='0x'+code.hex();f.birth[item['address']]=f.starts[epoch];f.address_epoch[item['address']]=epoch,role;roles[role]=item['address']
        f.roles.append(roles)
    for asset in cfg['assets']:
        if asset['address']==f.pair[0]:continue
        code=f.template.rpc.codes[asset['address']];need('0x'+keccak256(bytes.fromhex(code[2:])).hex()==asset['code_hash'],'Saved asset runtime differs')
        f.codes[asset['address']]=code;f.birth[asset['address']]=0
    transfer='0x'+keccak256(b'Transfer(address,address,uint256)').hex()
    f.ids=tuple(int(row['topics'][3],16)for row in f.rows[0]if row['topics'][0]==transfer and int(row['topics'][1],16)==0)
    need(len(f.ids)==1000 and len(set(f.ids))==1000,'Preserved complete NFT inventory')
    for epoch,boundary in enumerate(f.edges):
        tx=f.transition_tx(epoch)
        logs=sorted([row for e in (epoch,epoch+1)for row in f.rows[e]if row['transactionHash']==tx],key=lambda r:int(r['logIndex'],16))
        need(len(logs)==2 and all(int(row['blockNumber'],16)==boundary for row in logs),'Preserved exact handoff receipt pair')
        f.receipts[tx]=dict(status='0x1',transactionHash=tx,blockNumber=hex(boundary),blockHash=f.header(boundary)['hash'],transactionIndex='0x0',logs=logs)
    return f
