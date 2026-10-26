"""Defined-class/deduplicated keeper regression selection; never full discovery.

Runs offline/unit/loopback fixtures only. Unix-only methods remain explicit skips
where unsupported. This runner does not launch the operating process rehearsal.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib,inspect,io,json,sys,time,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
MODULES=(
 'test_keeper','test_keeper_fees','test_keeper_preparation','test_keeper_canonical',
 'test_keeper_maintenance_policy','test_keeper_range_policy','test_metadata_keeper',
 'test_keeper_recovery','test_keeper_ops','test_keeper_probe','test_staging_monitor',
 'test_rpc','test_state','test_keeper_native','test_keeper_example','test_royalty_keeper',
 'test_typed_v4_conversion_keeper','test_lp_conversion','test_keeper_health_identity',
 'test_keeper_conversion_integrity','test_keeper_rehearsal_profile','test_keeper_buyback_fairness',
)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 paths={Path(__file__).resolve(),ROOT/'keeper/rehearsal/KeeperVenue.sol',ROOT/'scripts/rehearse-keeper.py',ROOT/'keeper/staging.py'}
 # Capture the whole local Python pool before execution, including lazily
 # imported fixture dependencies. Inventory pins do not claim test coverage.
 for directory in ('keeper','zzz_ops','tests_python','frontend_api','indexer'):
  paths.update(p.resolve() for p in (ROOT/directory).rglob('*.py') if '__pycache__' not in p.parts)
 for name,mod in list(sys.modules.items()):
  if name.startswith(('keeper.','zzz_ops.','tests_python.','frontend_api.','indexer.')) and getattr(mod,'__file__',None):
   path=Path(mod.__file__).resolve()
   if ROOT in path.parents and path.suffix=='.py':paths.add(path)
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
class Results(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.methods=[]
 def startTest(self,test):super().startTest(test);self.methods.append(test.id())
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 tests={};classes=[]
 for short in MODULES:
  mod=importlib.import_module('tests_python.'+short)
  for _,cls in inspect.getmembers(mod,inspect.isclass):
   if not issubclass(cls,unittest.TestCase) or cls.__module__!=mod.__name__:continue
   classes.append(cls.__module__+'.'+cls.__name__)
   for name in unittest.defaultTestLoader.getTestCaseNames(cls):
    item=cls(name);assert item.id() not in tests,item.id();tests[item.id()]=item
 before=inputs();start=time.monotonic();stream=io.StringIO()
 result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Results).run(unittest.TestSuite(tests.values()))
 after=inputs();changed={n for n in before|after if before.get(n)!=after.get(n)}
 report={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Affected keeper unit/loopback regression; not whole repo or actual Unix/target-chain operating qualification.',
  'modules':list(MODULES),'classes':classes,'selected_methods':list(tests),'executed_methods':result.methods,'tests_run':result.testsRun,
  'failures':[(x.id(),s) for x,s in result.failures],'errors':[(x.id(),s) for x,s in result.errors],
  'skips':[(x.id(),s) for x,s in result.skipped],
  'source_sha256_before':before,'source_sha256_after':after,'source_changes_during_run':sorted(changed),
  'successful':result.wasSuccessful() and not changed and result.testsRun==len(tests),
  'elapsed_seconds':round(time.monotonic()-start,3),'production_approved':False}
 path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 path.with_suffix('.log').write_text(stream.getvalue(),encoding='utf-8',newline='\n')
 print(stream.getvalue());print(json.dumps({k:report[k] for k in ('tests_run','successful','elapsed_seconds')}))
 raise SystemExit(0 if report['successful'] else 1)
