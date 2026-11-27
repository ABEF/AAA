"""Run one separately pinned c825 complete continuation with frozen bounded transport."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,importlib.util,json,shlex,time

BASE=Path(__file__).resolve().parent
WRAPPER=BASE.parent/'host_control.py'
WRAPPER_SHA='a066ae767685c1c1dd5a3bc02e640177b44faadef6057fcf2e6e902f112f95e1'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    pins=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    for name in('complete_continuation.py','host_continuation.py'):assert sha((BASE/name).read_bytes())==pins[name]
    assert sha(WRAPPER.read_bytes())==WRAPPER_SHA
    spec=importlib.util.spec_from_file_location('fixed_c825_complete_wrapper',WRAPPER)
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    assert sha(host.TRANSPORT.read_bytes())==host.TRANSPORT_SHA
    output=host.private_path(a.output);assert not output.exists();output.mkdir(parents=True)
    code=(BASE/'complete_continuation.py').read_bytes();assert 0<len(code)<=65536
    argv=['python3','-I','-S','-B','-c',host.BOOTSTRAP,'--controller-sha256',sha(code)]
    transport=host.module(host.TRANSPORT,'fixed_c825_complete_opaque_transport');started=time.monotonic()
    exit_code,reason,counts,errors=host.capture(transport.ssh()+[' '.join(map(shlex.quote,argv))],
        len(code).to_bytes(4,'big')+code,output)
    receipt={'schema':1,'kind':'popl-c825-complete-continuation-execution','exit_code':exit_code,
        'capture_reason':reason,'capture_errors':errors,'continuation_sha256':sha(code),
        'preserved_controller_sha256':'f102550ea30927350c5b815fda020ccf4ea6a23fae00379668af8ccba351f10e',
        'passed_negative_result_sha256':'ad5813b9433039f5cf35925988bc673833b4b5c7f7a237d3e8a5ca21d9d0390d',
        'frozen_wrapper_sha256':WRAPPER_SHA,'transport_sha256':host.TRANSPORT_SHA,
        'stdout_bytes':counts[0],'stderr_bytes':counts[1],'combined_output_limit':65536,
        'elapsed_seconds':time.monotonic()-started,'opaque_SSH_transport':True,
        'only_action':'start-complete','installer_or_negative_called':False,'raw_transport_kept_private':True}
    for name in('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if exit_code==0 and reason is None and not errors:
        result=json.loads((output/'stdout.raw').read_bytes());assert result['phase']=='started'and result['mode']=='complete'
        assert result['preserved_controller_sha256']==receipt['preserved_controller_sha256']
        assert result['continuation_sha256']==sha(code)and result['passed_negative_result_sha256']==receipt['passed_negative_result_sha256']
        host.write(output/'SANITIZED_RESULT.json',host.enc(result))
    host.write(output/'EXECUTION.json',host.enc(receipt));print(json.dumps(receipt,sort_keys=True))
    return 0 if exit_code==0 and reason is None and not errors else 1


if __name__=='__main__':raise SystemExit(main())
