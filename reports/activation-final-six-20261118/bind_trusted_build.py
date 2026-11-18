"""Add the explicitly admitted offline build; preserve every historical pin."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
artifact=json.loads((P/'build/final/ARTIFACTS.json').read_bytes())
files={n:artifact['files'][n]for n in ('compiler-input.json.gz','compiler-output.json.gz','normal-size-evidence.json','START.json')}
assert all(hashlib.sha256((P/'build/final'/n).read_bytes()).hexdigest()==h for n,h in files.items())
result=json.loads((P/'build/final/RESULT.json').read_bytes())
assert result['pass'] and result['phase']=='admitted_without_recompilation'
path=R/'zzz_ops/deployment_plan.py'
raw=path.read_bytes();text=raw.decode('utf-8')
old="DEFAULT_BUILD_PROFILE='activation-gas-20261118'"
assert text.count(old)==1
text=text.replace(old,"ACTIVATION_BUILD_PROFILE='activation-gas-20261118'\nDEFAULT_BUILD_PROFILE='activation-final-six-20261118'")
needle=" DEFAULT_BUILD_PROFILE:{'directory':'reports/activation-gas-20261118/build/final'"
assert text.count(needle)==1
text=text.replace(needle," ACTIVATION_BUILD_PROFILE:{'directory':'reports/activation-gas-20261118/build/final'")
end="'source_inventory':'START.json','source_key':'compiler_content_sha256','gates':'normal-size-evidence.json'}}"
assert text.count(end)==1
entry="'source_inventory':'START.json','source_key':'compiler_content_sha256','gates':'normal-size-evidence.json'},\n DEFAULT_BUILD_PROFILE:{'directory':'reports/activation-final-six-20261118/build/final',\n 'files':"+repr(files)+",\n 'source_inventory':'START.json','source_key':'compiler_content_sha256','gates':'normal-size-evidence.json'}}"
text=text.replace(end,entry)
path.write_bytes(text.encode('utf-8'))
record={'build_id':'activation-final-six-20261118','files':files,'prior_profile':'activation-gas-20261118','prior_pins_unchanged':True,'production_approved':False}
(P/'TRUSTED_BUILD_BINDING.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
