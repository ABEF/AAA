import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

root = Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
output = Path(__file__).parent
os.chdir(root)
sys.path.insert(0,str(root))
os.environ['PATH'] = str(output.parent / 'foundry-v1.4.4') + os.pathsep + os.environ['PATH']
modules = sys.argv[1:] or ['tests_python.test_keeper_fees', 'tests_python.test_keeper',
           'tests_python.test_metadata_keeper', 'tests_python.test_keeper_recovery',
           'tests_python.test_keeper_ops', 'tests_python.test_keeper_native']
suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
prefix = 'keeper-' + modules[0].rsplit('.',1)[-1].replace('_','-') if sys.argv[1:] else 'keeper-scope'
with (output/(prefix+'.log')).open('w',encoding='utf-8') as handle:
    result = unittest.TextTestRunner(stream=handle,verbosity=2).run(suite)
paths = ['keeper/monitor.py','keeper/ops.py','zzz_ops/ethereum_fees.py',
    'tests_python/test_keeper_fees.py','tests_python/test_keeper.py','tests_python/test_metadata_keeper.py',
    'tests_python/test_keeper_recovery.py','tests_python/test_keeper_ops.py','tests_python/test_keeper_native.py']
report = {'scope':'Scoped offline keeper receipt/preflight regression. No network, real signer, journal, service or chain changes.',
    'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
    'skipped':[{'test':str(t),'reason':reason} for t,reason in result.skipped],
    'failed_ids':[str(t) for t,_ in result.failures+result.errors],
    'files':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}}
(output/(prefix+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
sys.exit(not result.wasSuccessful())
