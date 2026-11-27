"""Run only separately pinned loader diagnostic through frozen bounded transport."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,hashlib,importlib.util,json,shlex,time

BASE=Path(__file__).resolve().parent
WRAPPER=BASE.parent/'host_control.py'
WRAPPER_SHA='4ab220c177297f80dd934af23624e50a0edba67e842b8abbad0dc01c82f1dc28'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    pins=json.loads((BASE/'PARENT_REVIEW_PINS.json').read_bytes())
    for name in('runtime_loader.py','host_diagnostic.py'):assert sha((BASE/name).read_bytes())==pins[name]
    assert sha(WRAPPER.read_bytes())==WRAPPER_SHA
    spec=importlib.util.spec_from_file_location('fixed_c824_loader_wrapper',WRAPPER)
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    assert sha(host.TRANSPORT.read_bytes())==host.TRANSPORT_SHA
    output=host.private_path(a.output);assert not output.exists();output.mkdir(parents=True)
    code=(BASE/'runtime_loader.py').read_bytes();assert 0<len(code)<=65536
    argv=['python3','-I','-S','-B','-c',host.BOOTSTRAP,'--controller-sha256',sha(code)]
    transport=host.module(host.TRANSPORT,'fixed_c824_loader_opaque_transport');started=time.monotonic()
    exit_code,reason,counts,errors=host.capture(transport.ssh()+[' '.join(map(shlex.quote,argv))],
        len(code).to_bytes(4,'big')+code,output)
    receipt={'schema':1,'kind':'popl-c824-loader-diagnostic-execution','exit_code':exit_code,
        'capture_reason':reason,'capture_errors':errors,'diagnostic_sha256':sha(code),
        'frozen_wrapper_sha256':WRAPPER_SHA,'transport_sha256':host.TRANSPORT_SHA,
        'stdout_bytes':counts[0],'stderr_bytes':counts[1],'combined_output_limit':65536,
        'elapsed_seconds':time.monotonic()-started,'opaque_SSH_transport':True,
        'fixed_loader_and_OS_metadata_diagnostic_only':True,
        'configuration_or_journal_or_signer_files_accessed':False}
    for name in('stdout.raw','stderr.raw'):receipt[name+'_sha256']=sha((output/name).read_bytes())
    if exit_code==0 and reason is None and not errors:
        raw=(output/'stdout.raw').read_bytes();assert len(raw)<=16384
        result=json.loads(raw);assert result['kind']=='popl-c824-loader-and-OS-alias-diagnostic'
        assert result['native_keeper_calls']==0 and result['service_actions']==0 and result['host_mutations']==0
        host.write(output/'RESULT.json',raw)
    host.write(output/'EXECUTION.json',host.enc(receipt));print(json.dumps(receipt,sort_keys=True))
    return 0 if exit_code==0 and reason is None and not errors else 1


if __name__=='__main__':raise SystemExit(main())
