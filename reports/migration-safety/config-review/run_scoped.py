"""Four exact address-alias regressions for the independently found budget alias."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
PREFIX='tests_python.test_production_config.MigrationBudgetConfigTests.'
NAMES=[PREFIX+name for name in (
    'test_budget_mixed_case_cannot_alias_creator_inbox',
    'test_budget_cannot_alias_nft_helper_or_creator_inbox',
    'test_budget_cannot_alias_modules_entry_or_assets_helper',
    'test_budget_cannot_receive_mint_proceeds')]
SOURCES=['scripts/validate-production-config.py','tests_python/test_production_config.py',
         'zzz_ops/abi.py','zzz_ops/state.py',str(Path(__file__).resolve().relative_to(ROOT)).replace('\\','/')]
def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}
before=hashes();stream=io.StringIO()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(NAMES))
after=hashes()
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tests_run':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'runtime_skips':len(result.skipped),
        'successful':result.wasSuccessful() and not result.skipped and before==after,
        'test_ids':NAMES,'source_sha256_before':before,'source_sha256_after':after,'source_unchanged':before==after,
        'scope':'New mixed-case alias rejection and directly affected helper/custody alias checks only; '
                'earlier complete production-validator execution remains separately scoped.'}
(OUT/'tests.log').write_text(stream.getvalue(),encoding='utf-8')
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:report[key] for key in ('tests_run','failures','errors','runtime_skips','successful','source_unchanged')},indent=2))
sys.exit(0 if report['successful'] else 1)
