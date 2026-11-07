import json
import subprocess
import sys
import unittest
import keeper.monitor as monitor
from tests_python.test_exact_lp_conversion_capacity import ExactLPConversionCapacityTests
baseline = subprocess.check_output(['git','show','c055684a558519eab308a24b81746bf1b9842d96:keeper/royalties.py'],text=True,encoding='utf-8')
namespace = {'__name__':'baseline_keeper_royalties'}
exec(compile(baseline,'c055684:keeper/royalties.py','exec'),namespace)
monitor.RoyaltyAutomation = namespace['RoyaltyAutomation']
case = ExactLPConversionCapacityTests('test_affordable_subset_preserves_every_cap_and_persists_remainder_before_one_send')
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([case]))
print(json.dumps({'negative_control':'original worker rejects affordable subset','worker_source':'c055684a558519eab308a24b81746bf1b9842d96:keeper/royalties.py','baseline_attempt_counts':[candidate['count'] for candidate in case.rpc.estimates],'baseline_cursor':case.k.state['lp_conversion']['ordinal'],'signer_calls':case.signer.call_count,'expected_regression_failure':len(result.failures)==1 and not result.errors},sort_keys=True))
sys.exit(0 if len(result.failures)==1 and not result.errors else 1)
