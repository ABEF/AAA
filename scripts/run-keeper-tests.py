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
 'test_keeper_harvest_isolation',
 'test_keeper_outside_schedule','test_keeper_compound_cadence','test_keeper_reservations',
 'test_keeper_principal_distribution','test_keeper_revert_health','test_keeper_watchdog',
 'test_keeper_execution_telemetry','test_keeper_rebalance_confirmation',
 'test_keeper_confirmation_incidents','test_keeper_confirmation_followup',
 'test_keeper_confirmation_health','test_keeper_confirmation_writer',
 'test_keeper_checkpoint_confirmation','test_keeper_conversion_headers','test_rpc_integrity',
 'test_keeper_runner_inventory',
 'test_keeper_metadata_restart',
 'test_keeper_confirmation_cadence',
)
def select_tests(modules=MODULES,importer=importlib.import_module):
 """Build a strict inventory without executing any selected test body."""
 if not modules or len(modules)!=len(set(modules)):raise ValueError('Empty or repeated keeper module selection')
 tests={};classes=[];seen=set()
 for short in modules:
  mod=importer('tests_python.'+short)
  if mod.__name__!='tests_python.'+short:raise ValueError('Selected keeper module identity differs')
  count=0
  for _,cls in inspect.getmembers(mod,inspect.isclass):
   if not issubclass(cls,unittest.TestCase) or cls.__module__!=mod.__name__ or cls in seen:continue
   seen.add(cls);classes.append(cls.__module__+'.'+cls.__name__)
   for name in unittest.defaultTestLoader.getTestCaseNames(cls):
    item=cls(name)
    if item.id() in tests:raise ValueError('Repeated keeper test identity')
    tests[item.id()]=item;count+=1
  if not count:raise ValueError('Selected keeper module defines no test methods')
 return tests,classes
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
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
 parser.add_argument('--list',action='store_true',help='Write selected method inventory without executing tests')
 args=parser.parse_args()
 tests,classes=select_tests()
 before=inputs();start=time.monotonic();stream=io.StringIO()
 result=None if args.list else unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Results).run(unittest.TestSuite(tests.values()))
 after=inputs();changed={n for n in before|after if before.get(n)!=after.get(n)}
 report={'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'scope':'Selection inventory only; no tests executed.' if args.list else 'Affected keeper unit/loopback regression; not whole repo or actual Unix/target-chain operating qualification.',
  'execution_performed':not args.list,
  'modules':list(MODULES),'classes':classes,'selected_methods':list(tests),'executed_methods':result.methods if result else [],'tests_run':result.testsRun if result else 0,
  'failures':[(x.id(),s) for x,s in result.failures] if result else [],'errors':[(x.id(),s) for x,s in result.errors] if result else [],
  'skips':[(x.id(),s) for x,s in result.skipped] if result else [],
  'source_sha256_before':before,'source_sha256_after':after,'source_changes_during_run':sorted(changed),
  'successful':not changed and (args.list or result.wasSuccessful() and result.testsRun==len(tests)),
  'elapsed_seconds':round(time.monotonic()-start,3),'production_approved':False}
 path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 path.with_suffix('.log').write_text(stream.getvalue(),encoding='utf-8',newline='\n')
 print(stream.getvalue());print(json.dumps({k:report[k] for k in ('tests_run','successful','elapsed_seconds')}))
 raise SystemExit(0 if report['successful'] else 1)
