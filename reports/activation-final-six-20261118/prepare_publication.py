"""Create an exact owned path list; never stage, commit or push itself."""
from pathlib import Path
import hashlib,json,subprocess
from urllib.parse import urlparse

R=Path(__file__).resolve().parents[2]
O=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-final-six-20261118')
P=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
freeze=json.loads((O/'SOURCE_FREEZE.json').read_bytes())
assert subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip()=='main'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()=='963e039caa163a4921d08ed4bfc6b3a44cb79d42'
url=subprocess.check_output(['git','remote','get-url','origin'],cwd=R).decode().strip()
parsed=urlparse(url);assert parsed.hostname=='github.com' and parsed.username is None and parsed.password is None
assert parsed.path.lower().rstrip('.git')=='/abef/aaa'
allowed={'.gitattributes','AGENTS.md','PROJECT_CONTEXT.md','README.md','TODO.md','config/production.example.json','reports/README.md',
 'scripts/check-slither-review.py','tests_python/test_activation_build20261118.py','tests_python/test_factory_payload5.py',
 'zzz_ops/deployment_plan.py','zzz_ops/preseal_plan.py','zzz_ops/production_observer_v15.py','zzz_ops/production_v15.py','zzz_ops/royalty_read_policy.py'}
allowed|=set(freeze['normal_build']['approved_changed_source_sha256'])
allowed|={'docs/'+n for n in ('AUDIT_FINDINGS.md','CONTRACT_FUNCTIONS.md','DEPLOYMENT_ADDRESSES.md','DEPLOYMENT_PREPARATION.md','DEPLOYMENT_SEQUENCE.md',
 'DEVELOPMENT.md','EXACT_LP_ALLOCATION.md','EXACT_ROYALTY_ALLOCATION.md','FACTORY_CODE_STORAGE.md','IMPLEMENTATION_STATUS.md','OPERATOR_MANUAL.md',
 'POSITION_V7.md','PRESEAL_CONFIGURATION.md','PRODUCTION_PREFLIGHT.md','RELEASE_CHECKLIST.md','ROADMAP.md','ROYALTY_SETTLEMENT.md',
 'SOURCE10_WEBSITE_PROFILE.md','WORK_HANDOFF.md','function-reference.json','operator-call-examples.json','project-todo.json')}
modified=set(subprocess.check_output(['git','diff','HEAD','--name-only','-z'],cwd=R).decode().strip('\0').split('\0'))
protected=set(freeze['protected_sha256'])
assert all(sha((R/n).read_bytes())==pin for n,pin in freeze['protected_sha256'].items())
new={'config/factory-code-storage-v6.json','config/production.schema17.payload5.example.json','zzz_ops/factory_code_v6.py',
 'tests_python/factory_payload_archive.py','tests_python/test_factory_payload6.py','tests_python/test_slither_current_default.py'}
new|={p.relative_to(R).as_posix()for p in P.rglob('*')if p.is_file()and'__pycache__'not in p.parts and p.suffix!='.pyc'}
assert modified-protected<=allowed|new,modified-protected-allowed-new
paths=sorted((modified-protected)|new)
assert all((R/n).is_file()for n in paths)and not protected.intersection(paths)
(O/'PUBLICATION_PATHS.txt').write_bytes(b'\0'.join(n.encode('utf-8')for n in paths)+b'\0')
record={'schema':1,'baseline_main':'963e039caa163a4921d08ed4bfc6b3a44cb79d42','owned_files':len(paths),
 'owned_paths':paths,'protected_excluded':sorted(protected),'native_sha256':{n:sha((R/n).read_bytes())for n in paths},
 'scope':'Explicit owned source/docs/evidence publication plan; not staging, deployment or approval.'}
(O/'PUBLICATION_PLAN.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(paths),'owned paths; four unrelated tracked files and all unrelated drafts excluded.')
