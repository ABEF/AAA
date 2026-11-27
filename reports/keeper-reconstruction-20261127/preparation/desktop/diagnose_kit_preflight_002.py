"""Retain only safe source frames/size for the new kit helper refusal."""
from pathlib import Path
import hashlib,json,traceback
BASE=Path(__file__).resolve().parent.parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private/campaign-001')
path=BASE/'core/reconstruction_kit.py';raw=path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='5dcd535b9d4764695fcd22b336140fa4c70e3f6bccbf7e5788a364ead45c0a68'
namespace={'__name__':'pinned_kit_diagnosis','__file__':str(path)}
exec(compile(raw,str(path),'exec'),namespace)
try:
    proof=namespace['verify'](PRIVATE/'kit')
    result={'schema':1,'verification_completed':True,'encoded_proof_bytes':len(namespace['encode'](proof))}
except Exception as exc:
    result={'schema':1,'verification_completed':False,'error_type':type(exc).__name__,
      'frames':[{'file':Path(row.filename).name,'line':row.lineno,'function':row.name}
        for row in traceback.extract_tb(exc.__traceback__)]}
with (PRIVATE/'proof/PREFLIGHT_DIAGNOSIS-002.json').open('x',encoding='utf8') as stream:json.dump(result,stream,sort_keys=True,indent=2);stream.write('\n')
print(json.dumps(result,sort_keys=True))
