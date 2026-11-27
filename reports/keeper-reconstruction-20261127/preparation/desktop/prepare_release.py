"""Build the private release from trusted Git, and copy the retained package."""
from pathlib import Path
import hashlib,json,os,re,stat,subprocess
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
HEAD='a418a567abbc3c0b7c6dd8425ef31306e8e48f17'
PRIVATE=V/'keeper-reconstruction-20261127/private'
KIT=PRIVATE/'campaign-001/kit'
OLD=V/'keeper-offhost-20261126/private/campaign-001/export-003/package'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def git(*args,input=None):
    value=subprocess.run(['git',*args],cwd=ROOT,input=input,capture_output=True,check=True,timeout=30).stdout
    assert len(value)<=2*1024*1024;return value
def write(name,raw):
    path=KIT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:assert stream.write(raw)==len(raw);stream.flush();os.fsync(stream.fileno())
assert git('rev-parse','HEAD').decode().strip()==HEAD and not KIT.exists()
manifest_raw=(V/'keeper-reconstruction-20261127/trust/SOURCE_MANIFEST.json').read_bytes()
assert sha(manifest_raw)=='c287aa0c4b8e4113f7ffa1459f39a704bd17b5165f23084e3a8f26995cdb0e08'
sources=json.loads(manifest_raw)['source_files'];assert len(sources)==41
names=sorted(sources)
assert all(re.fullmatch(r'(keeper|zzz_ops|scripts|tests_python)/[A-Za-z0-9_-]+\.py',name) for name in names)
response=git('cat-file','--batch',input=''.join(HEAD+':'+name+'\n' for name in names).encode());at=0;copied={}
for name in names:
    end=response.index(b'\n',at);header=response[at:end].split();assert header[1]==b'blob'
    size=int(header[2]);at=end+1;raw=response[at:at+size];at+=size+1
    row=sources[name];assert response[at-1:at]==b'\n' and len(raw)==row['bytes'] and sha(raw)==row['sha256']
    write('source/'+name,raw);copied['source/'+name]={'bytes':len(raw),'sha256':sha(raw)}
assert at==len(response)
write('SOURCE_MANIFEST.json',manifest_raw)
public=git('show',HEAD+':reports/keeper-offhost-20261126/evidence/c823/export-003/EXPORT_METADATA.json')
expected=json.loads(public)['files'];assert len(expected)==5
for name,row in expected.items():
    assert name in ('manifest.json','selection.json','alert-state.json','selected/manifest.json','selected/journal.json')
    path=OLD/name
    for parent in (*reversed(path.parents),path):
        item=parent.lstat();assert not stat.S_ISLNK(item.st_mode) and not getattr(item,'st_file_attributes',0)&0x400
    before=path.lstat();assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==row['bytes']<=65536
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0));key=lambda st:(st.st_dev,st.st_ino,st.st_nlink,st.st_size,st.st_mtime_ns)
    with os.fdopen(fd,'rb') as stream:
        raw=stream.read(65537);assert key(os.fstat(stream.fileno()))==key(before)==key(path.lstat())
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256'];write('package/'+name,raw)
    copied['package/'+name]=row
record={'schema':1,'source_commit':HEAD,'release_files':41,'retained_package_files':5,
 'prepared_kit_members':47,'required_final_members':49,'source_raw_bytes':sum(row['bytes'] for row in sources.values()),
 'source_manifest_sha256':sha(manifest_raw),'references_not_yet_exported':True,
 'raw_files_outside_checkout':True,'test_bodies_run':0,'server_actions':0,'files':copied}
with (BASE/'RELEASE_PREPARATION.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({key:value for key,value in record.items() if key!='files'}))
