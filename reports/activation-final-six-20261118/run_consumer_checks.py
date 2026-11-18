"""Select only new F6 and affected historical-loader controls after final pins.

No Solidity/compiler/EVM/RPC or unchanged browser/backend suites. Old F3/F4/F5
evidence retains its original source scope; this run does not relabel it.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,time,os,re
R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
NEW='tests_python.test_factory_payload6.FactoryPayload6Tests'
AFFECTED=(
 'tests_python.test_activation_build20261118.ActivationBuild20261118Tests',
 'tests_python.test_factory_payload5.FactoryPayload5Tests.test_new_payload5_matches_actual_trusted_full_normal_and_rejects_old_bytes',
 'tests_python.test_factory_payload5.FactoryPayload5Tests.test_invalid_selector_mixed_payload_and_legacy_read_fields_fail_before_rpc')
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def main():
 generated=P/'consumer/GENERATED_PINS.json';assert generated.is_file(),'Await real finalnormal F6 generation'
 assert len(sys.argv)in(2,3)and re.fullmatch(r'final[0-9]{2}',sys.argv[1]),'Use a fresh consumer finalNN stage name'
 retry_archive=len(sys.argv)==3 and sys.argv[2]=='--retry-archive-only'
 if len(sys.argv)==3:assert retry_archive,'Only the exact affected archive-reader retry is supported'
 dest=P/'consumer'/sys.argv[1];dest.mkdir(exist_ok=False)
 source_paths=('zzz_ops/factory_code_v6.py','config/factory-code-storage-v6.json','config/production.example.json',
  'config/production.schema17.payload5.example.json','zzz_ops/production_v15.py','zzz_ops/production_observer_v15.py',
  'zzz_ops/royalty_read_policy.py','zzz_ops/preseal_plan.py','zzz_ops/deployment_plan.py','tests_python/factory_payload_archive.py',
  'tests_python/test_factory_payload6.py','tests_python/test_factory_payload5.py','tests_python/test_activation_build20261118.py')
 before={n:sha((R/n).read_bytes())for n in source_paths}
 selected=AFFECTED[:-1]if retry_archive else AFFECTED
 new_classes=(NEW,)
 cmd=[sys.executable,'-m','unittest','-v',*new_classes,*selected];then=time.monotonic()
 keep={'SYSTEMROOT','WINDIR','SYSTEMDRIVE','COMSPEC','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PATH'}
 env={k:v for k,v in os.environ.items()if k.upper()in keep};env['PYTHONIOENCODING']='utf-8'
 with(dest/'stdout.log').open('xb')as out,(dest/'stderr.log').open('xb')as err:r=subprocess.run(cmd,cwd=R,env=env,stdout=out,stderr=err,timeout=600)
 after={n:sha((R/n).read_bytes())for n in source_paths}
 stderr=(dest/'stderr.log').read_text(encoding='utf-8');counts=re.findall(r'^Ran (\d+) tests? in',stderr,re.M)
 result={'schema':1,'command':cmd,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-then,
  'new_method_classes':list(new_classes),'actual_unittest_executed_methods':int(counts[-1])if counts else None,
  'affected_historical_controls':list(selected),'source_before':before,'source_after':after,
  'source_bracket_stable':before==after,'generated_pin_record_sha256':sha(generated.read_bytes()),
  'scope':('7 new F6 methods;3 affected historical activation-build methods;1 affected F5 loader method.11selected; the already-passing selector control is not repeated.'if retry_archive else'7 new F6 methods;3 affected historical activation-build methods;2 affected F5 loader/selector methods.12distinct methods, not unchanged suites.'),
  'public_rpc_or_transactions':False,'production_approved':False,'pass':r.returncode==0 and before==after}
 (dest/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2));return 0 if result['pass']else 1

if __name__=='__main__':raise SystemExit(main())
