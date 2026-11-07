import json,sys,unittest
from unittest.mock import patch
from zzz_ops import manual_lp_review as M
from zzz_ops.errors import RpcError
from tests_python.test_manual_lp_review import ManualLPReviewTests
print('CAUSAL NEGATIVE CONTROLS: ephemeral monkeypatches only; production source unchanged; failures below are required and do not add passing-test counts.')
with patch.object(M,'controls',lambda snapshot:{}):
    control=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ManualLPReviewTests('test_changed_final_nonce_controls_and_physical_backing_refuse_without_rewriting')]))
original=M.Reader.snapshot
def wrong_preharvest_ceiling(reader,selected,governance,*,full):
    result=original(reader,selected,governance,full=full)
    if selected['action']=='D' and result['swap'] is not None:
        direction=0 if selected['zeroForOne'] else 1
        if selected['amountIn']>int(result['swap']['available_principal_raw'][direction]):
            raise RpcError('Negative control: incorrect preharvest D spending ceiling')
    return result
with patch.object(M.Reader,'snapshot',wrong_preharvest_ceiling):
    spending=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ManualLPReviewTests('test_d_preharvest_lower_bound_never_replaces_full_source_call_spendability')]))
observed={'kind':'deliberate_ephemeral_negative_controls','source_modified':False,'disabled_control_comparison_failures':len(control.failures),'disabled_control_comparison_errors':len(control.errors),'restored_false_D_ceiling_failures':len(spending.failures),'restored_false_D_ceiling_errors':len(spending.errors),'expected_red':len(control.failures)==5 and not control.errors and len(spending.errors)==1 and not spending.failures}
print(json.dumps(observed,sort_keys=True))
sys.exit(0 if observed['expected_red'] else 1)
