"""Copy only authenticated public lab outputs; no network or production edits."""
from pathlib import Path
import ast,hashlib,json,tarfile
BASE=Path(__file__).resolve().parent
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
REPORT=ROOT/'reports/ubuntu-hybrid-20261124'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def put(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,path
    else:path.write_bytes(raw)
def enc(data):return (json.dumps(data,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def load(path):return json.loads(path.read_bytes())
def main():
    for folder,tag in [('hybrid','c7ff'),('hybrid-retry','c800')]:
        source=BASE/folder;dest=REPORT/'evidence'/tag
        for fetch in sorted(source.glob('fetch-*-001')):
            execution=load(fetch/'EXECUTION.json');assert execution['exit_code']==0 and execution['artifact_sha256']
            selected=[p for p in fetch.iterdir()if p.name not in ('EXECUTION.json','stdout.raw','stderr.raw')]
            assert len(selected)==1
            raw=selected[0].read_bytes();assert sha(raw)==execution['artifact_sha256']
            put(dest/selected[0].name,raw)
            put(dest/'capture'/('EXECUTION-'+selected[0].name+'.json'),(fetch/'EXECUTION.json').read_bytes())
        for name in ('BUILD_RECEIPT.json','CHANGES.json'):
            if(source/name).exists():put(dest/name,(source/name).read_bytes())
        for action in ('validate','upload','install','start','stop'):
            where=source/(action+'-001');put(dest/'control'/(action+'-EXECUTION.json'),(where/'EXECUTION.json').read_bytes())
            if action=='stop':
                stopped=load(where/'PUBLIC_RESULT.json');assert stopped['after']['owned_cgroup_pids']==[] and stopped['after']['properties']['ActiveState']=='inactive'
                put(dest/'control'/'STOP.json',(where/'PUBLIC_RESULT.json').read_bytes())
        for name in ('keeper_runtime.py','keeper_jobs.py','job_cases.py','run_jobs.py','remote_capsule.py','host_control.py'):
            raw=(source/name).read_bytes();ast.parse(raw);put(REPORT/'verification'/tag/name,raw)
        with tarfile.open(source/(tag+'.inputs.tar.gz'),'r:gz')as arc:
            for name in ('MANIFEST.json','inputs/SOURCE_MANIFEST.json'):
                put(dest/Path(name).name,arc.extractfile(name).read())
    for name in ('package_lab.py','prepare_retry.py','package_retry.py'):
        put(REPORT/'verification'/name,(BASE/name).read_bytes())
    put(REPORT/'verification'/'verify_saved_hybrid.py',(BASE/'independent-review/verify_saved_hybrid.py').read_bytes())
    put(REPORT/'evidence'/'INDEPENDENT_ACCOUNTING.json',(BASE/'INDEPENDENT_ACCOUNTING.json').read_bytes())
    preservation=BASE.parent/'history-export-20261124/host-preservation/compare-004'
    candidates=[p for p in preservation.glob('*.json')if load(p).get('phase')=='authorized_host_preservation_comparison']
    assert len(candidates)==1;assert load(candidates[0])['success']
    put(REPORT/'evidence'/'HOST_PRESERVATION.json',candidates[0].read_bytes())
    result=load(REPORT/'evidence/c800/RESULT.json');assert result['success']
    rows=load(REPORT/'evidence/c800/hybrid-RECEIPTS.json')
    metrics=[]
    for row in rows:
        intent=row['intent'];receipt=row['receipt'];metrics.append({'hash':row['hash'],'padded':intent['fee_review']['gas_limit'],'actual':int(receipt['gasUsed'],16),'nonce':intent['nonce']})
    print(json.dumps({'report':str(REPORT),'gas':metrics,'files':sum(p.is_file()for p in REPORT.rglob('*'))}))
if __name__=='__main__':main()
