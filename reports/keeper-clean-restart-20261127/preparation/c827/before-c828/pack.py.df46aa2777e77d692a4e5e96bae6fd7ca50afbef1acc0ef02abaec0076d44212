"""Offline, closed c827 preparation; exact current source and reviewed helpers."""
from pathlib import Path
import ast,base64,hashlib,json,os,stat,subprocess,zlib
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
HEAD='d6e8a909fd2b2a12eb1bee15173e92d526178cdb'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
pin=lambda raw:{'bytes':len(raw),'sha256':sha(raw)}
enc=lambda obj:(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def read(path,maximum=65536):
    before=path.lstat();key=lambda x:(x.st_dev,x.st_ino,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns)
    assert stat.S_ISREG(before.st_mode)and before.st_nlink==1 and 0<before.st_size<=maximum and not getattr(before,'st_file_attributes',0)&0x400
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb')as stream:
        assert key(os.fstat(stream.fileno()))==key(before);raw=stream.read(maximum+1)
        assert len(raw)==before.st_size and key(os.fstat(stream.fileno()))==key(before)==key(path.lstat())
    return raw
def write(path,raw):
    if path.exists():assert path.read_bytes()==raw;return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def main():
    env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
    actual=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,env=env,capture_output=True,check=True,timeout=10).stdout.decode().strip()
    assert actual==HEAD
    receipt_raw=read(BASE.parent/'core/RELEASE_PREPARATION.json')
    assert sha(receipt_raw)=='5cf74c4c3218e938cf56bb18d1934140d9233fd564a24a7302d4d8144a8fd573'
    receipt=json.loads(receipt_raw)
    assert receipt['ok']is True and receipt['source_commit']==HEAD and receipt['total_members']==42
    release=PRIVATE/'release-001';files={}
    for name,row in receipt['files'].items():
        path=release/name;assert path.lstat().st_size==row['bytes']<=1048576
        raw=read(path,1048576)
        assert pin(raw)==row;files[name]=raw
    assert sha(files['SOURCE_MANIFEST.json'])=='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
    manifest=json.loads(files['SOURCE_MANIFEST.json'])
    source_pins={name:{key:row[key]for key in('bytes','sha256')}for name,row in manifest['source_files'].items()}
    worker=read(BASE/'target_worker.py');ast.parse(worker)
    helpers={}
    for name in('shared.py','gateway.py','driver.py','runtime_support.py','target_worker.py'):
        raw=read(BASE/name);ast.parse(raw);helpers[name]=pin(raw);files['helpers/'+name]=raw
    template=read(BASE/'controller_template.py').decode('utf8')
    assert template.count('__SOURCE_PINS__')==template.count('__HELPER_PINS__')==1
    controller=template.replace('__SOURCE_PINS__',repr(source_pins)).replace('__HELPER_PINS__',repr(helpers)).encode()
    assert len(controller)<=65536;ast.parse(controller);write(BASE/'remote_capsule.py',controller)
    assert len(files)==47 and sum(map(len,files.values()))<=1048576
    packet=enc({'schema':1,'kind':'c827-preparation','files':{name:{**pin(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}for name,raw in files.items()}})
    assert len(packet)<=2097152 and len(zlib.compress(packet,9))<=2097152
    write(PRIVATE/'preparation-002/packet.json',packet)
    names=['shared.py','gateway.py','driver.py','runtime_support.py','target_worker.py','controller_template.py','remote_capsule.py','host_control.py','pack.py']
    pins={name:sha(read(BASE/name))for name in names}
    write(BASE/'PARENT_REVIEW_PINS.json',enc({'schema':1,'source_head':HEAD,'files':pins}))
    result={'schema':1,'kind':'fixed_c827_preparation','source_head':HEAD,'source_manifest_sha256':sha(files['SOURCE_MANIFEST.json']),
        'source_files':source_pins,'helpers':helpers,'controller':pin(controller),'packet':pin(packet),
        'compressed_packet_bytes':len(zlib.compress(packet,9)),'total_members':len(files),'source_release_from_desktop':True,
        'raw_configuration_or_signer_included':False,'source_test_members_inert':True,'test_bodies_run':0,'network_calls':0,'server_actions':0}
    write(BASE/'BUILD_RECEIPT.json',enc(result))
    print(json.dumps({'success':True,'members':len(files),'controller_sha256':sha(controller),'packet_bytes':len(packet),
        'compressed_packet_bytes':result['compressed_packet_bytes'],'production_source_edits':0,'server_actions':0}))
if __name__=='__main__':main()
