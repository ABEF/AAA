"""Diagnose the new helper using source-line/type events only, never values."""
from pathlib import Path
import hashlib,json,sys
BASE=Path(__file__).resolve().parent.parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private/campaign-001')
path=BASE/'core/reconstruction_kit.py';raw=path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='5dcd535b9d4764695fcd22b336140fa4c70e3f6bccbf7e5788a364ead45c0a68'
namespace={'__name__':'trace_private_kit_entrypoint','__file__':str(path)}
exec(compile(raw,str(path),'exec'),namespace)
events=[]
def trace(frame,event,arg):
    if event=='exception' and frame.f_code.co_filename==str(path) and len(events)<16:
        events.append({'function':frame.f_code.co_name,'line':frame.f_lineno,'error_type':arg[0].__name__})
    return trace
sys.argv=[str(path),'verify','--kit',str(PRIVATE/'kit'),'--proof',str(PRIVATE/'proof/KIT_PROOF-003.json')]
try:
    sys.settrace(trace);code=namespace['main']()
finally:sys.settrace(None)
record={'schema':1,'returncode':code,'source_only_exception_frames':events,
 'private_values_logged':False,'application_imports':0,'test_bodies_run':0}
with (PRIVATE/'proof/ENTRYPOINT_DIAGNOSIS.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps(record,sort_keys=True))
