"""Fixed no-exec c826 client diagnostic; retained original launch stays failed."""
from pathlib import Path
import base64,hashlib,importlib.util,json,shlex
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
LAB=BASE.parent/'lab';PRIVATE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/keeper-clean-restart-20261127/private')
EXPECTED='9d7985ee2fb9485ac57080bc999cfa23ede28629df12143e53728681a640c7d8'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
body='''import base64,hashlib,json,os,time
from pathlib import Path
raw=base64.b64decode(CONTROLLER,validate=True)
assert hashlib.sha256(raw).hexdigest()==EXPECTED
n={'__name__':'fixed_c826_noexec_diagnostic'};exec(compile(raw,'<reviewed_c826>','exec'),n)
n['ACTIVE_CONTROLLER_SHA']=EXPECTED;n['owned']()
role='node';p=n['common'](role);logical=n['LOGICAL'];lab=n['LAB'];fixture=n['FIXTURE'];tools=n['TOOLS']
p.update(Type='exec',RemainAfterExit='no',TimeoutStartSec='30',LimitFSIZE='65536',
 BindReadOnlyPaths=tools['anvil'][0]+':'+str(logical/'tools/anvil')+' '+str(fixture/'restore-state.json')+':'+str(logical/'inputs/restore-state.json'),
 BindPaths=str(lab/'node')+':'+str(logical/'node'),ReadWritePaths=str(logical/'node'),WorkingDirectory=str(logical/'node'))
for suffix in('stdout','stderr'):p['Standard'+('Output'if suffix=='stdout'else'Error')]='append:'+str(lab/'evidence'/('node.'+suffix))
# A root directory exists on every host. Negating that condition prohibits ExecStart.
p['ConditionPathExists']='!/'
unit='popl-keeper-clean-restart-20261127-c826-noexec-diagnostic.service'
code,before,_=n['run'](['/usr/bin/systemctl','show',unit,'--no-pager','--property=LoadState,ActiveState,MainPID,ControlGroup'])
assert b'LoadState=not-found' in before
argv=[str(logical/'tools/anvil'),'--host','127.0.0.1','--port','19626','--accounts','0','--silent','--chain-id','4663',
 '--hardfork','cancun','--gas-limit','32000000','--gas-price','1000000000','--block-base-fee-per-gas','1',
 '--load-state',str(logical/'inputs/restore-state.json')]
command=['/usr/bin/systemd-run','--quiet','--no-block','--unit='+unit]
command+=['--property='+key+'='+value for key,value in p.items()]
command+=['--setenv='+key+'='+value for key,value in {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}.items()]
exitcode,out,err=n['run']([*command,'--',*argv])
_,version,_=n['run'](['/usr/bin/systemd-run','--version'])
after=b''
try:
 for _ in range(20):
  _,after,_=n['run'](['/usr/bin/systemctl','show',unit,'--no-pager','--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,ConditionResult'])
  if b'ConditionResult=no' in after or b'LoadState=not-found' in after:break
  time.sleep(.05)
 assert b'MainPID=0' in after or b'LoadState=not-found' in after
 if b'LoadState=not-found' not in after:assert b'ConditionResult=no' in after
finally:
 if b'LoadState=not-found' not in after:n['run'](['/usr/bin/systemctl','stop',unit])
fixed_unit='popl-keeper-clean-restart-20261127-c826-noexec-path-diagnostic.service'
_,fixed_before,_=n['run'](['/usr/bin/systemctl','show',fixed_unit,'--no-pager','--property=LoadState'])
assert b'LoadState=not-found' in fixed_before
fixed_command=[item.replace('--unit='+unit,'--unit='+fixed_unit)for item in command]
fixed_command.append('--property=ExecSearchPath='+str(logical/'tools'))
fixed_code,fixed_out,fixed_err=n['run']([*fixed_command,'--',*argv])
fixed_after=b''
try:
 for _ in range(20):
  _,fixed_after,_=n['run'](['/usr/bin/systemctl','show',fixed_unit,'--no-pager','--property=LoadState,ActiveState,SubState,MainPID,ControlGroup,ConditionResult'])
  if b'ConditionResult=no' in fixed_after or b'LoadState=not-found' in fixed_after:break
  time.sleep(.05)
 assert fixed_code==0 and b'MainPID=0' in fixed_after and b'ConditionResult=no' in fixed_after
finally:
 if b'LoadState=not-found' not in fixed_after:n['run'](['/usr/bin/systemctl','stop',fixed_unit])
print(json.dumps({'schema':1,'kind':'c826_guaranteed_noexec_launch_diagnostic','exit_code':exitcode,
 'controller_sha256':EXPECTED,'original_controller_unchanged':True,'condition_guarantees_no_ExecStart':True,
 'namespace_binary_exists_on_host':os.path.exists(argv[0]),'systemd_version':version.decode('utf8','strict'),
 'stdout_base64':base64.b64encode(out).decode(),'stderr_base64':base64.b64encode(err).decode(),
 'diagnostic_unit_properties':after.decode('utf8','strict'),'source_transactions':0,'original_services_modified':False,
 'ExecSearchPath_noexec_probe':{'exit_code':fixed_code,'stdout_base64':base64.b64encode(fixed_out).decode(),
 'stderr_base64':base64.b64encode(fixed_err).decode(),'unit_properties':fixed_after.decode('utf8','strict'),
 'condition_prevented_execution':True}}))
'''
def main():
    controller=(LAB/'remote_capsule.py').read_bytes();assert sha(controller)==EXPECTED
    code=('CONTROLLER='+repr(base64.b64encode(controller).decode())+'\nEXPECTED='+repr(EXPECTED)+'\n'+body).encode()
    assert len(code)<=65536
    assert sha((LAB/'host_control.py').read_bytes())=='e319e719f679feba73cdaca6db24c3d47251c322d33a270db672daa21313dbaa'
    spec=importlib.util.spec_from_file_location('fixed_c826_host',(LAB/'host_control.py'));host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    assert sha(host.TRANSPORT.read_bytes())==host.TRANSPORT_SHA and sha(host.CAPTURE.read_bytes())==host.CAPTURE_SHA
    capture=host.module(host.CAPTURE,'fixed_c825_capture');transport=host.module(host.TRANSPORT,'fixed_diag_transport')
    output=PRIVATE/'diagnostic-001';host.private_path(output,new=True);output.mkdir()
    command=transport.ssh()+['python3 -I -S -B -']
    result,reason,counts,errors=capture.capture(command,code,output)
    receipt={'schema':1,'exit_code':result,'capture_reason':reason,'capture_errors':errors,'counts':counts,
        'fixed_diagnostic_sha256':sha(code),'condition_guarantees_no_ExecStart':True,'only_new_diagnostic_unit':True}
    if result==0 and reason is None and not errors:
        decoded=host.decode((output/'stdout.raw').read_bytes());host.write(output/'RESULT.json',host.enc(decoded))
    host.write(output/'EXECUTION.json',host.enc(receipt));print(json.dumps(receipt));assert result==0 and reason is None and not errors
if __name__=='__main__':main()
