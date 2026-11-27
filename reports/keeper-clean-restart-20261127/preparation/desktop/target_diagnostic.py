"""Fixed read-only diagnosis for the failed c828 target; never starts a unit."""
from pathlib import Path
import base64,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent;LAB=BASE.parent/'c828'
PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
EXPECTED='22d459431d168fa5822ea8917544a2de166f2e1a820b1d9f6de39516a1d31a91'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
body='''import base64,hashlib,json,os,stat
from pathlib import Path
raw=base64.b64decode(CONTROLLER,validate=True);assert hashlib.sha256(raw).hexdigest()==EXPECTED
n={'__name__':'c828_read_only_diagnostic'};exec(compile(raw,'<frozen_c828>','exec'),n)
n['ACTIVE_CONTROLLER_SHA']=EXPECTED;n['owned']()
code,out,err=n['run'](['/usr/bin/journalctl','--unit=popl-keeper-clean-restart-20261127-c828-target.service','--no-pager','-n','25','-o','json'],seconds=12)
assert code==0 and len(out)<=65536 and len(err)<=4096
messages=[]
for line in out.splitlines():
 row=json.loads(line);message=row.get('MESSAGE','');assert type(message)is str and len(message)<=4096
 messages.append({'MESSAGE':message,'time':row.get('__REALTIME_TIMESTAMP'),'unit':row.get('_SYSTEMD_UNIT')})
root=n['LAB']/'target-root';logical=root/str(n['LOGICAL']).lstrip('/')
captured=n['decode'](n['read'](n['LAB']/'evidence/INCLUDED.json'))
state=n['read'](logical/'actor/state.json')
assert hashlib.sha256(state).hexdigest()==captured['pending_journal_sha256']
identity=n['decode'](n['read'](logical/'TARGET_IDENTITY.json'))
paths={}
for suffix in ('','/run','/proc','/sys','/dev','/tmp','/var','/var/tmp'):
 path=Path(str(root)+suffix)
 try:
  info=path.lstat();paths[suffix or'/']={'mode':stat.S_IMODE(info.st_mode),'uid':info.st_uid,'directory':stat.S_ISDIR(info.st_mode),'symlink':stat.S_ISLNK(info.st_mode)}
 except FileNotFoundError:paths[suffix]={'missing':True}
print(json.dumps({'schema':1,'kind':'c828_target_readonly_namespace_diagnostic','messages':messages,
 'target':n['props']('target'),'node':n['props']('node'),'source_pending_unchanged':hashlib.sha256(n['read'](n['LAB']/'actor/state.json')).hexdigest()==captured['pending_journal_sha256'],
 'target_pending_unchanged':True,'target_root_paths':paths,'runtime_review_sha256':identity['runtime_review_sha256'],
 'native_or_keeper_body_run':False,'services_started':0,'transactions_sent':0}))
'''
def main():
    controller=(LAB/'remote_capsule.py').read_bytes();assert sha(controller)==EXPECTED
    code=('CONTROLLER='+repr(base64.b64encode(controller).decode())+'\nEXPECTED='+repr(EXPECTED)+'\n'+body).encode();assert len(code)<=65536
    pins=json.loads((LAB/'PARENT_REVIEW_PINS.json').read_bytes());assert sha((LAB/'host_control.py').read_bytes())==pins['files']['host_control.py']
    spec=importlib.util.spec_from_file_location('c828_fixed_host',LAB/'host_control.py');host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    assert sha(host.TRANSPORT.read_bytes())==host.TRANSPORT_SHA and sha(host.CAPTURE.read_bytes())==host.CAPTURE_SHA
    output=PRIVATE/'target-diagnostic-001';host.private_path(output,new=True);output.mkdir()
    capture=host.module(host.CAPTURE,'fixed_c825_capture');transport=host.module(host.TRANSPORT,'fixed_readonly_transport')
    result,reason,counts,errors=capture.capture(transport.ssh()+['python3 -I -S -B -'],code,output)
    if result==0 and reason is None and not errors:host.write(output/'RESULT.json',host.enc(host.decode((output/'stdout.raw').read_bytes())))
    receipt={'schema':1,'exit_code':result,'capture_reason':reason,'capture_errors':errors,'counts':counts,'diagnostic_sha256':sha(code),'read_only':True}
    host.write(output/'EXECUTION.json',host.enc(receipt));print(json.dumps(receipt));assert result==0 and reason is None and not errors
if __name__=='__main__':main()
