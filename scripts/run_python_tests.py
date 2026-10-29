"""Run defined, canonical off-chain tests once; never evidence of EVM execution."""
import argparse
import datetime
import hashlib
import importlib
import inspect
import json
import platform
import re
import secrets
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zzz_ops.evidence import Evidence


def select_tests(modules=None,importer=importlib.import_module):
    if modules is None:
        modules=tuple(path.stem for path in sorted((ROOT/'tests_python').glob('test*.py')))
    if not modules or len(modules)!=len(set(modules)):
        raise ValueError('Empty or repeated Python test module selection')
    tests={};classes=[];seen=set()
    for short in modules:
        if not isinstance(short,str) or not re.fullmatch(r'test\w*',short,re.ASCII):
            raise ValueError('Invalid Python test module name')
        module=importer('tests_python.'+short)
        if module.__name__!='tests_python.'+short:
            raise ValueError('Selected Python module identity differs')
        if getattr(module,'load_tests',None) is not None:
            raise ValueError('Custom test loading requires explicit reviewed selection')
        local=0
        for _,cls in inspect.getmembers(module,inspect.isclass):
            if not issubclass(cls,unittest.TestCase) or cls.__module__!=module.__name__ or cls in seen:
                continue
            seen.add(cls);classes.append(cls.__module__+'.'+cls.__name__)
            for name in unittest.defaultTestLoader.getTestCaseNames(cls):
                item=cls(name)
                if item.id() in tests:raise ValueError('Repeated Python test identity')
                tests[item.id()]=item;local+=1
        if not local:raise ValueError('Selected Python module defines no test methods')
    return tests,classes


def inputs():
    paths={Path(__file__).resolve()}
    for directory in ('scripts','tests_python','keeper','zzz_ops','frontend_api','indexer'):
        paths.update((ROOT/directory).rglob('*.py'))
    return {path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths) if '__pycache__' not in path.parts}


class Results(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.methods=[]
    def startTest(self,test):super().startTest(test);self.methods.append(test.id())


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true',help='Inventory only; do not execute tests')
    parser.add_argument('--output',type=Path,help='New JSON evidence file; old JSON/logs are never overwritten')
    args=parser.parse_args(argv)
    if args.list and args.output is None:parser.error('--list requires an explicit new --output')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
    output=args.output or ROOT/'reports'/f'python-tests-{stamp}-{secrets.token_hex(4)}.json'
    if output.suffix!='.json':raise ValueError('Python evidence requires a JSON output path')
    if any(path.exists() or path.is_symlink() for path in (output,output.with_suffix('.log'))):
        raise ValueError('Python evidence output already exists')
    # Inventory-only mode retains its no-execution-log contract.
    with Evidence(output,with_log=not args.list,kind='python_test_evidence') as evidence:
        before=inputs();tests,classes=select_tests()
        result=None if args.list else unittest.TextTestRunner(stream=evidence.log,verbosity=2,resultclass=Results).run(unittest.TestSuite(tests.values()))
        after=inputs();changed=sorted(name for name in before.keys()|after.keys() if before.get(name)!=after.get(name))
        breakdown={}
        for item in tests.values():
            module=item.__class__.__module__;breakdown[module]=breakdown.get(module,0)+1
        successful=not changed and (args.list or result.wasSuccessful() and result.testsRun==len(tests) and result.methods==list(tests))
        report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),
            'execution_performed':not args.list,'selected_methods':list(tests),'classes':classes,
            'executed_methods':result.methods if result else [],'tests_run':result.testsRun if result else 0,
            'failures':len(result.failures) if result else 0,'errors':len(result.errors) if result else 0,
            'skipped':len(result.skipped) if result else 0,'successful':bool(successful),'by_module':breakdown,
            'failure_methods':[x.id() for x,_ in result.failures] if result else [],
            'error_methods':[x.id() for x,_ in result.errors] if result else [],
            'skipped_methods':[(x.id(),reason) for x,reason in result.skipped] if result else [],
            'source_sha256_before':before,'source_sha256_after':after,'source_changes_during_run':changed,
            'solidity_tests_executed':0,'notice':'Python model/unit checks do not execute or verify Solidity; an inventory is not a test pass.'}
        diagnostics=evidence.read_log()
        evidence.finish(report)
    print(diagnostics);print(json.dumps({**{key:report[key] for key in ('tests_run','execution_performed','successful')},'output':str(output)}))
    return 0 if successful else 1


if __name__=='__main__':raise SystemExit(main())
