"""Run the changed helper once with exact structured arguments and private output."""
from pathlib import Path
import hashlib,json,subprocess,sys
BASE=Path(__file__).resolve().parent.parent
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-reconstruction-20261127/private/campaign-001')
helper=BASE/'core/reconstruction_kit.py';digest=hashlib.sha256(helper.read_bytes()).hexdigest()
assert digest=='d1819f24c0735d1b61b961b20140e7ec2caaa83e1b4329fceba90e23bb27e5c2'
proof=PRIVATE/'proof/KIT_PROOF-004.json'
args=[sys.executable,'-B','-X','utf8',str(helper),'verify','--kit',str(PRIVATE/'kit'),'--proof',str(proof)]
result=subprocess.run(args,capture_output=True,timeout=65)
assert len(result.stdout)+len(result.stderr)<=65536
for name,raw in (('FINAL_CLI.stdout',result.stdout),('FINAL_CLI.stderr',result.stderr)):
    with (PRIVATE/'proof'/name).open('xb') as stream:stream.write(raw)
record={'schema':1,'helper_sha256':digest,'exit_code':result.returncode,
 'stdout_bytes':len(result.stdout),'stderr_bytes':len(result.stderr),
 'structured_arguments_used':True,'app_or_test_bodies_executed':0,
 'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),
 'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
with (PRIVATE/'proof/FINAL_CLI_EXECUTION.json').open('x',encoding='utf8') as stream:json.dump(record,stream,indent=2,sort_keys=True);stream.write('\n')
print(result.stdout.decode('utf8'),end='');print(json.dumps(record,sort_keys=True))
raise SystemExit(result.returncode)
