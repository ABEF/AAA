"""Package exact new fixture evidence without executing a chain or tests."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
WORK=V/'pool-integration-20261120/entry'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    execution=json.loads((WORK/'attempt1-supervisor.json').read_bytes())
    assert execution['returncode']==0 and sha((HERE/'run_entry.py').read_bytes())==execution['runner_sha256']
    stage=json.loads((WORK/'attempt1/SOURCE_STAGE.json').read_bytes());assert stage['driver_sha256']==execution['runner_sha256']
    assert json.loads((WORK/'attempt1/cleanup.json').read_bytes())['owned_node_stopped']
    files={}
    for path in sorted((WORK/'attempt1').rglob('*')):
        if path.is_file():files['attempt1/'+path.relative_to(WORK/'attempt1').as_posix()]=path.read_bytes()
    for suffix in ('.json','.stdout','.stderr'):
        path=WORK/('attempt1-supervisor'+suffix);files[path.name]=path.read_bytes()
    for name in ('run_entry.py','supervise.py','verify_entry.py','package_entry.py','VERIFICATION.json'):
        files['tools/'+name]=(HERE/name).read_bytes()
    # Exact imported report-only transport, independently shared by swap stage.
    files['tools/imported-warm_cache.py']=(ROOT/'reports/pool-integration-20261120/swap/warm_cache.py').read_bytes()
    for name in ('run_pool.py','warm_cache.py'):
        files['tools/imported-physical-'+name]=(ROOT/'reports/pool-lifecycle-20261120/run'/name).read_bytes()
    files['tools/imported-native_fixture.py']=(ROOT/'reports/full-claim-admission-20261120/tools/native_fixture.py').read_bytes()
    assert len(files)<=512 and sum(map(len,files.values()))<=64*1024*1024
    manifest={name:{'sha256':sha(raw),'bytes':len(raw)}for name,raw in files.items()}
    target=HERE/'evidence.zip'
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9)as z:
        for name,raw in files.items():z.writestr(name,raw)
    with zipfile.ZipFile(target)as z:
        assert set(z.namelist())==set(files)
        for name,row in manifest.items():
            raw=z.read(name);assert len(raw)==row['bytes']and sha(raw)==row['sha256']
    result={'schema':1,'archive':'evidence.zip','sha256':sha(target.read_bytes()),'bytes':target.stat().st_size,'members':manifest,'member_count':len(manifest),'source_scope':'new finite2NFT Entry partition only; actual supplied-pool core with controlled platform/price/depth seams','production_approved':False}
    with (HERE/'EVIDENCE_MANIFEST.json').open('x',encoding='utf8')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items()if k!='members'}));return 0
if __name__=='__main__':raise SystemExit(main())
