"""Assemble NEW native capture plus current release; no signing or network."""
from pathlib import Path
import argparse,hashlib,json,math,os,stat,time
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def decode(raw):
    def pairs(rows):
        out={}
        for name,item in rows:assert name not in out;out[name]=item
        return out
    def invalid(_):raise ValueError('Invalid metadata')
    def number(raw):
        item=float(raw);assert math.isfinite(item);return item
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,parse_float=number)
def safe(path,*,new=False):
    path=Path(path).absolute();assert path.is_relative_to(PRIVATE)and'..'not in path.parts
    for item in(*reversed(path.parents),path):
        if not item.is_relative_to(PRIVATE):continue
        if new and item==path:assert not os.path.lexists(item);continue
        try:info=item.lstat()
        except FileNotFoundError:assert new;continue
        assert not stat.S_ISLNK(info.st_mode)and not getattr(info,'st_file_attributes',0)&0x400
    return path
def read(path,maximum=1048576):
    path=safe(path);before=path.lstat();key=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns)
    assert stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_ino!=0 and 0<before.st_size<=maximum
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb')as stream:
        assert key(os.fstat(stream.fileno()))==key(before);raw=stream.read(maximum+1)
        assert len(raw)==before.st_size and key(os.fstat(stream.fileno()))==key(before)==key(path.lstat())
    return raw
def write(path,raw):
    assert len(raw)<=1048576;safe(path,new=True);path.parent.mkdir(parents=True,exist_ok=True);safe(path.parent)
    with path.open('xb')as stream:assert stream.write(raw)==len(raw);stream.flush();os.fsync(stream.fileno())
def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--trust',type=Path,required=True)
    p.add_argument('--canonical',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    started=time.monotonic();output=safe(a.output,new=True);output.mkdir(parents=True)
    release_raw=(BASE.parent/'core/RELEASE_PREPARATION.json').read_bytes()
    assert len(release_raw)<=16384 and sha(release_raw)=='5cf74c4c3218e938cf56bb18d1934140d9233fd564a24a7302d4d8144a8fd573'
    release=decode(release_raw)
    assert release['ok']is True and release['total_members']==42
    trusted=decode(read(a.trust,65536));canonical=decode(read(a.canonical,32768))
    assert trusted['accepted_hash']==canonical['hash']==canonical['receipt']['transactionHash']
    assert trusted['actual_node_pending_before_inclusion']is True and trusted['raw_attempts']==trusted['raw_forwarded']==1
    assert canonical['receipt']['status']=='0x1' and canonical['confirmations']==12
    capture=safe(a.capture);files={}
    for name,row in release['files'].items():
        raw=read(PRIVATE/'release-001'/name);assert {'bytes':len(raw),'sha256':sha(raw)}==row;files[name]=raw
    assert sha(files['SOURCE_MANIFEST.json'])=='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
    source=decode(files['SOURCE_MANIFEST.json'])['source_files']
    assert set(files)=={'SOURCE_MANIFEST.json',*('source/'+name for name in source)}and len(source)==41
    for name in('CONFIG.json','bundle/manifest.json','bundle/journal.json'):files[name]=read(capture/name,65536)
    assert len(files)==45 and sum(map(len,files.values()))<=1048576
    for name,key in(('CONFIG.json','configuration_sha256'),('bundle/manifest.json','backup_manifest_sha256'),('bundle/journal.json','pending_journal_sha256')):
        assert sha(files[name])==trusted[key]
    manifest=decode(files['bundle/manifest.json']);state=decode(files['bundle/journal.json']);config=decode(files['CONFIG.json'])
    assert state['pending']['hash']==trusted['accepted_hash']and state['pending']['nonce']==state['next_nonce']==0
    assert state['pending']['data']==canonical['transaction_without_signature']['input']
    assert config['sender']==canonical['receipt']['from'].lower() and config['chain_id']==4663
    assert config['interval_seconds']==240 and config['confirmations']==12 and config['max_gas_limit']==24000000
    assert config['max_gas_price_wei']=='5000000000'and config['max_transaction_cost_wei']=='10000000000000000'
    assert config['max_daily_cost_wei']=='50000000000000000'and config['maintenance']['harvest_interval_seconds']==3600
    assert config['rpc_urls']==['http://127.0.0.1:19627']and config.get('submission_fee_profile',1)==1
    assert manifest['configuration_raw_sha256']==sha(files['CONFIG.json'])
    assert type(manifest['created_at'])is int and 0<=time.time()-manifest['created_at']<=900
    kit=output/'kit';kit.mkdir()
    for name,raw in files.items():write(kit/name,raw)
    directories={parent.as_posix()for name in files for parent in Path(name).parents if parent!=Path('.')}
    for _ in range(2):
        actual=set()
        for path in kit.rglob('*'):
            name=path.relative_to(kit).as_posix();info=path.lstat()
            assert not stat.S_ISLNK(info.st_mode)and not getattr(info,'st_file_attributes',0)&0x400
            assert name in set(files)|directories and name not in actual;actual.add(name)
            assert stat.S_ISDIR(info.st_mode)if name in directories else stat.S_ISREG(info.st_mode)and info.st_nlink==1
        assert actual==set(files)|directories
        assert all(read(kit/name)==raw for name,raw in files.items())
        assert time.monotonic()-started<=60
    proof={'schema':1,'kind':'c828-desktop-recovery-kit','ok':True,'unsigned':True,'readiness_approved':False,'production_approved':False,
        'source_manifest_sha256':sha(files['SOURCE_MANIFEST.json']),'configuration_sha256':sha(files['CONFIG.json']),
        'journal_manifest_sha256':sha(files['bundle/manifest.json']),'pending_journal_sha256':sha(files['bundle/journal.json']),
        'accepted_hash':trusted['accepted_hash'],'original_created_at':manifest['created_at'],'review_max_age_seconds':900,
        'signer_material_included':False,'actual_private_files_reread':45,'total_raw_bytes':sum(map(len,files.values())),
        'files':{name:{'bytes':len(raw),'sha256':sha(raw)}for name,raw in sorted(files.items())}}
    raw=enc(proof);assert len(raw)<=16384;write(output/'KIT_PROOF.json',raw)
    print(json.dumps({'success':True,'private_files':45,'total_raw_bytes':proof['total_raw_bytes'],'proof_sha256':sha(raw),
        'source_capture_time_unchanged':True,'signer_material_included':False,'test_bodies_run':0,'network_calls':0}))
if __name__=='__main__':main()
