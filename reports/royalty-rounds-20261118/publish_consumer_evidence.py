"""Package existing scoped Python evidence; never executes tests or network calls."""
from pathlib import Path
import gzip,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/royalty-rounds-20261118/consumer-final01')
TARGET=Path(__file__).resolve().parent/'consumer/final01'
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    TARGET.mkdir(parents=True,exist_ok=False)
    raw=(SOURCE/'RESULT.json').read_bytes();result=json.loads(raw)
    assert result['success'] and result['source_stable'] and result['tests_run']==12
    assert len(set(result['methods']))==12 and not result['failures'] and not result['errors'] and not result['skips']
    for name in ('START.json','RESULT.json'):
        (TARGET/(name+'.gz')).write_bytes(gzip.compress((SOURCE/name).read_bytes(),mtime=0))
    shutil.copyfile(SOURCE/'raw.log',TARGET/'raw.log')
    owned=('zzz_ops/factory_code_v5.py','config/factory-code-storage-v5.json',
        'config/production.example.json','config/production.schema17.payload4.example.json',
        'zzz_ops/royalty_read_policy.py','zzz_ops/production_v15.py','zzz_ops/production_observer_v15.py',
        'zzz_ops/preseal_plan.py','tests_python/test_factory_payload5.py','tests_python/test_factory_payload4.py')
    pins={p:sha((ROOT/p).read_bytes()) for p in owned}
    assert all(result['source_sha256_after'][p]==pin for p,pin in pins.items())
    publication=dict(schema=1,kind='Scoped source-stable offline consumer checks',new_methods=11,changed_methods=1,
        actual_methods=12,method_ids=result['methods'],failures=0,errors=0,skips=0,
        started=result['started'],ended=result['ended'],owned_files_sha256=pins,
        protected_sha256=result['protected_sha256'],all_recorded_source_bytes_stable=True,
        files_sha256={p.name:sha(p.read_bytes()) for p in sorted(TARGET.iterdir())},
        limitations=['Synthetic RPC responses exercise real factory-part and read-policy observer branches; no public provider is qualified.',
            'Trusted current compiler artifacts are read and authenticated; no compiler or EVM tests execute here.',
            'No unchanged Python suite is rerun. One old selector control changed because version5 is now valid.',
            'No activation20M, complete fees, currency behavior, OpenSea, operating or production approval is supplied.'],
        production_approved=False,network_rpc_performed=False,signing_performed=False)
    (TARGET/'PUBLICATION.json').write_text(json.dumps(publication,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'packaged_methods':12,'new_methods':11,'changed_methods':1,'files':len(publication['files_sha256'])}))


if __name__=='__main__':main()
