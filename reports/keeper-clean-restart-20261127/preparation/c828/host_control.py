"""Fixed c828 transport, bounded captures and exclusive private outputs only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,math,os,shlex,stat,zlib

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
BASE=Path(__file__).resolve().parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
CAPTURE=ROOT/'reports/keeper-reconstruction-20261127/preparation/c825/host_control.py'
CAPTURE_SHA='a066ae767685c1c1dd5a3bc02e640177b44faadef6057fcf2e6e902f112f95e1'
TRANSPORT=ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py'
TRANSPORT_SHA='a7f7f91863833bca9081b0ad6af833a1cf5147e65f1c2cfe7e058449f1bddc45'
ACTION=('prepare','start-node','bootstrap','gateway','initialize','source','fence','export','status','stop','fetch','fresh','final','install-target','target')
BOOTSTRAP="""import sys,hashlib
sys.dont_write_bytecode=True
n=int.from_bytes(sys.stdin.buffer.read(4),'big');assert 0<n<=65536
code=sys.stdin.buffer.read(n);assert len(code)==n
expected=sys.argv[sys.argv.index('--controller-sha256')+1]
assert hashlib.sha256(code).hexdigest()==expected
exec(compile(code,'<fixed_c828_capsule>','exec'),{'__name__':'__main__','__file__':'<fixed_c828_capsule>'})
"""
sha=lambda raw:hashlib.sha256(raw).hexdigest()
enc=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def decode(raw):
    def pairs(rows):
        out={}
        for name,item in rows:
            assert name not in out;out[name]=item
        return out
    def invalid(_):raise ValueError('Nonfinite metadata')
    def number(raw):
        value=float(raw);assert math.isfinite(value);return value
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid,parse_float=number)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def private_path(path,*,new=False):
    path=Path(path).absolute();assert path.is_relative_to(PRIVATE.absolute())and'..'not in path.parts
    for item in(*reversed(path.parents),path):
        if not item.is_relative_to(PRIVATE.absolute()):continue
        if new and item==path:assert not os.path.lexists(item);break
        try:info=item.lstat()
        except FileNotFoundError:
            assert new;continue
        assert not stat.S_ISLNK(info.st_mode)and not getattr(info,'st_file_attributes',0)&0x400
    return path
def bounded(path,maximum=1048576):
    path=private_path(path);before=path.lstat()
    assert stat.S_ISREG(before.st_mode)and before.st_nlink==1 and 0<=before.st_size<=maximum
    key=lambda item:(item.st_dev,item.st_ino,item.st_mode,item.st_nlink,item.st_size,item.st_mtime_ns)
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb')as stream:
        assert key(os.fstat(stream.fileno()))==key(before)
        raw=stream.read(maximum+1)
        assert key(os.fstat(stream.fileno()))==key(before)==key(path.lstat())and len(raw)==before.st_size
    return raw
def write(path,raw):
    path=private_path(path,new=True);path.parent.mkdir(parents=True,exist_ok=True);private_path(path.parent)
    with path.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def files_packet(folder,metadata):
    files={};total=0
    for name,row in metadata.items():
        assert type(name)is str and'..'not in Path(name).parts and not name.startswith(('/','\\'))and'\\'not in name
        raw=bounded(private_path(folder)/name);assert len(raw)==row['bytes']and sha(raw)==row['sha256']
        total+=len(raw);assert total<=1048576
        files[name]={'bytes':len(raw),'sha256':sha(raw),'raw_base64':base64.b64encode(raw).decode('ascii')}
    return files
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=ACTION);p.add_argument('--artifact')
    p.add_argument('--kit',type=Path);p.add_argument('--proof',type=Path);p.add_argument('--proof-sha256')
    p.add_argument('--runtime-sha256');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pins=decode((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    for name,digest in pins['files'].items():assert sha((BASE/name).read_bytes())==digest,name
    assert sha(CAPTURE.read_bytes())==CAPTURE_SHA and sha(TRANSPORT.read_bytes())==TRANSPORT_SHA
    output=private_path(a.output,new=True);output.mkdir(parents=True)
    controller=(BASE/'remote_capsule.py').read_bytes();assert 0<len(controller)<=65536
    args=['python3','-I','-S','-B','-c',BOOTSTRAP,a.action,'--controller-sha256',sha(controller)]
    data=len(controller).to_bytes(4,'big')+controller;wire_size=expanded_size=0
    if a.action=='fetch':assert a.artifact is not None;args+=['--artifact',a.artifact]
    if a.action=='prepare':
        packet=bounded(PRIVATE/'preparation-003/packet.json',2097152)
        obj=decode(packet);assert obj['kind']=='c828-preparation'
    elif a.action=='install-target':
        assert all(v is not None for v in(a.kit,a.proof,a.proof_sha256,a.runtime_sha256))
        proof=bounded(a.proof,32768);assert sha(proof)==a.proof_sha256;verified=decode(proof)
        assert verified['kind']=='c828-desktop-recovery-kit'and verified['ok']is True and len(verified['files'])==45
        packet=enc({'schema':1,'kind':'c828-desktop-recovery-kit','files':files_packet(a.kit,verified['files']),
            'proof_base64':base64.b64encode(proof).decode('ascii')})
        args+=['--proof-sha256',a.proof_sha256,'--runtime-sha256',a.runtime_sha256]
    else:packet=None
    if packet is not None:
        assert 0<len(packet)<=2097152;wire=zlib.compress(packet,9);assert 0<len(wire)<=2097152
        expanded_size=len(packet);wire_size=len(wire);data+=wire
    capture=module(CAPTURE,'reviewed_c825_capture');transport=module(TRANSPORT,'reviewed_c828_transport')
    code,reason,counts,errors=capture.capture(transport.ssh()+[' '.join(map(shlex.quote,args))],data,output)
    receipt={'schema':1,'action':a.action,'exit_code':code,'capture_reason':reason,'capture_errors':errors,
        'controller_sha256':sha(controller),'transport_sha256':TRANSPORT_SHA,'capture_helper_sha256':CAPTURE_SHA,
        'combined_output_limit':65536,'action_timeout_seconds':45,'compressed_input_limit':2097152,'expanded_input_limit':2097152,
        'compressed_input_bytes':wire_size,'expanded_input_bytes':expanded_size,'stdout_bytes':counts[0],'stderr_bytes':counts[1],
        'raw_transport_private':True,'source_or_target_signer_content_exported':False,'only_new_c828_control':True}
    for name in('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if code==0 and reason is None and not errors:
        result=decode((output/'stdout.raw').read_bytes())
        if a.action=='export':
            assert result['kind']=='c828-private-native-capture'and set(result['files'])=={'CONFIG.json','bundle/manifest.json','bundle/journal.json'}
            metadata={}
            for name,row in result['files'].items():
                raw=base64.b64decode(row['raw_base64'],validate=True);assert len(raw)==row['bytes']<=65536 and sha(raw)==row['sha256']
                write(output/name,raw);metadata[name]={'bytes':len(raw),'sha256':sha(raw)}
            write(output/'EXPORT_METADATA.json',enc({'schema':1,'files':metadata,'INCLUDED':result['INCLUDED'],
                'raw_configuration_and_bundle_private':True,'signer_material_exported':False}))
        elif a.action=='fetch':
            raw=base64.b64decode(result['raw_base64'],validate=True)
            assert result['name']==a.artifact and len(raw)==result['bytes']<=32768 and sha(raw)==result['sha256']
            write(output/a.artifact,raw)
        else:write(output/'SANITIZED_RESULT.json',enc(result))
    write(output/'EXECUTION.json',enc(receipt));print(json.dumps(receipt,sort_keys=True))
    return 0 if code==0 and reason is None and not errors else 1
if __name__=='__main__':raise SystemExit(main())
