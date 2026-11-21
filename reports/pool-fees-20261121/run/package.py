"""Preserve both finite stages and exact verification bytes; no EVM/RPC work."""
from pathlib import Path
import hashlib,json,zipfile
HERE=Path(__file__).resolve().parent
WORK=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/pool-fees-20261121/run')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def main():
    assert not (HERE/'evidence.zip').exists()and not(HERE/'EVIDENCE_MANIFEST.json').exists()
    final=load(WORK/'attempt2-supervisor.json');assert final['returncode']==0 and final['runner_sha256']==sha((HERE/'run_fees.py').read_bytes())
    assert load(WORK/'attempt1-supervisor.json')['returncode']==1
    files={}
    for name in('attempt1','attempt2','offline-prefix-stage','reused-fixture'):
        directory=WORK/name
        for path in sorted(directory.rglob('*')):
            if path.is_file()and'__pycache__'not in path.parts:files[name+'/'+path.relative_to(directory).as_posix()]=path.read_bytes()
    for attempt in('attempt1','attempt2'):
        assert load(WORK/attempt/'cleanup.json')['owned_node_stopped']and load(WORK/attempt/'cleanup.json')['pending']is None
        for suffix in('.json','.stdout','.stderr'):
            path=WORK/(attempt+'-supervisor'+suffix);files[path.name]=path.read_bytes()
    for name in('run_fees.py','driver_base.py','warm_cache.py','eager_oracle.py','supervise.py','verify_saved.py','package.py','VERIFICATION.json','ORACLE_CONTROL.json','PREFIX_REPLAY.json','PREFIX_SOURCE_REUSE.json'):
        files['tools/'+name]=(HERE/name).read_bytes()
    assert len(files)==len(set(files))<=512 and sum(map(len,files.values()))<=64*1024*1024
    with zipfile.ZipFile(HERE/'evidence.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
        for name,raw in files.items():archive.writestr(name,raw)
    with zipfile.ZipFile(HERE/'evidence.zip')as archive:
        assert set(archive.namelist())==set(files)
        for name,raw in files.items():assert archive.read(name)==raw
    raw=(HERE/'evidence.zip').read_bytes();manifest={'schema':1,'archive':'evidence.zip','bytes':len(raw),'sha256':sha(raw),'members':{k:{'bytes':len(v),'sha256':sha(v)}for k,v in files.items()},'roundtrip_verified':True,'production_approved':False}
    with(HERE/'EVIDENCE_MANIFEST.json').open('x',encoding='utf8',newline='\n')as f:json.dump(manifest,f,indent=2);f.write('\n')
    print(json.dumps({'archive_members':len(files),'bytes':len(raw),'sha256':sha(raw),'raw_member_bytes':sum(map(len,files.values()))}))
if __name__=='__main__':main()
