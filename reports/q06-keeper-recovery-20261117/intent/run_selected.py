"""Run only the new intent/shutdown methods, with source-bracketed evidence."""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--evidence',required=True,type=Path)
    parser.add_argument('--stage',required=True)
    parser.add_argument('--method',action='append')
    args=parser.parse_args()
    stage=args.evidence/args.stage
    stage.mkdir(parents=True,exist_ok=False)
    module=importlib.import_module('tests_python.test_keeper_intent_shutdown')
    case=module.KeeperIntentShutdownTests
    discovered=unittest.defaultTestLoader.getTestCaseNames(case)
    selected=args.method or discovered
    if not selected or len(selected)!=len(set(selected)) or not set(selected)<=set(discovered):
        raise SystemExit('Nonempty exact new method selection required')
    methods=[case(name) for name in selected]
    source_paths=set()
    for imported in list(sys.modules.values()):
        name=getattr(imported,'__file__',None)
        if name:
            path=Path(name).resolve()
            if path.is_file() and path.is_relative_to(ROOT) and path.suffix=='.py':source_paths.add(path)
    source_paths.add(Path(__file__).resolve())
    before={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in sorted(source_paths)}
    for name in ('keeper/monitor.py','tests_python/test_keeper_intent_shutdown.py'):
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    start={'command':sys.argv,'python':sys.executable,'python_version':sys.version,
        'selected_methods':selected,'discovered_new_methods':discovered,'source_sha256':before,
        'scope':'inert current-profile RPC and signer; real submit validators and temporary atomic journal; no services/network/signing'}
    (stage/'START.json').write_text(json.dumps(start,indent=2)+'\n',encoding='utf-8')
    started=time.monotonic()
    with (stage/'unittest.log').open('w',encoding='utf-8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.TestSuite(methods))
    after={name:sha(ROOT/name) for name in before}
    failed={test.id():'failure' for test,_ in result.failures}
    failed.update({test.id():'error' for test,_ in result.errors})
    entries=[{'id':test.id(),'status':failed.get(test.id(),'pass'),
        'boundary_evidence':getattr(test,'boundary_evidence',{})} for test in methods]
    final={'methods':entries,'tests_run':result.testsRun,'expected_count':len(selected),
        'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
        'nonzero_exact_selection':result.testsRun==len(selected)>0,
        'source_unchanged':before==after,'source_after_sha256':after,
        'elapsed_seconds':time.monotonic()-started,'log_sha256':sha(stage/'unittest.log')}
    final['pass']=result.wasSuccessful() and final['nonzero_exact_selection'] and final['source_unchanged'] and not result.skipped
    (stage/'RESULT.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in final.items() if k!='source_after_sha256'}))
    return 0 if final['pass'] else 1

if __name__=='__main__':raise SystemExit(main())
