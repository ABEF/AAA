"""One new offline evidence-admission regression; no compiler, node or RPC."""
import importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('local_deployment_evidence',ROOT/'scripts/check-local-deployment-evidence.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
from zzz_ops.deployment_plan import BUILD_PINS

class LocalDeploymentEvidenceTests(unittest.TestCase):
    def test_forged_build_inventory_and_values_rejected_before_filesystem(self):
        class Captured:
            def __init__(self,path):self.zip=None
            def obj(self,name):return records[name]
        valid_tools={'scripts/rehearse-local-deployment.py':M.LEGACY_RUNNER}
        records={'RESULT.json':{'status':'controlled_local_constructor_and_binding_rehearsal_passed','sealed':False,'release_ready':False,'production_approved':False},
          'source-stage.json':{'tool_sources_sha256':valid_tools,'accepted_build_files_sha256':{}},
          'node/cleanup.json':{'owned_node_stopped':True,'pending_submission':None,'failure_type':None},
          'node/process.json':{'chain_id':4663,'port':61000,'pid':123,'minimal_environment':True,'size_limit_override':False,'command':['anvil.exe','--host','127.0.0.1','--accounts','0','--silent','--hardfork','cancun','--gas-limit','32000000']},
          'node/socket-ownership.json':[],'SOURCE_UNCHANGED.json':valid_tools}
        bad_inputs=({**BUILD_PINS,'../untrusted':'0'*64},{**BUILD_PINS,'compiler-output.json.gz':'0'*64})
        for bad in bad_inputs:
            with self.subTest(keys=list(bad)):
                records['source-stage.json']['accepted_build_files_sha256']=bad
                with patch.object(M,'Evidence',Captured),patch.object(Path,'open',side_effect=AssertionError('No build filesystem read before fixed pin admission')):
                    with self.assertRaisesRegex(ValueError,'Accepted build pin inventory'):M.reconcile(Path('.'),Path('unused'))

if __name__=='__main__':unittest.main()
