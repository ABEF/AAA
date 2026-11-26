"""One fixed c812 file-only selection. No action on import or generic SSH API."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shlex
import sys
import time

ROOT=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BASE=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--execute-reviewed',action='store_true',required=True);a=p.parse_args()
    assert a.execute_reviewed
    approval=json.loads((BASE/'EXECUTION_APPROVAL.json').read_bytes())
    assert set(approval)=={'bundle_sha256','controller_sha256','runner_sha256'}
    bundle=(BASE/'c812.inputs.tar.gz').read_bytes();controller=(BASE/'remote_capsule.py').read_bytes()
    assert len(bundle)<=2*1024*1024 and len(controller)<=65536
    assert sha(bundle)==approval['bundle_sha256']and sha(controller)==approval['controller_sha256']
    assert sha((BASE/'run_selected.py').read_bytes())==approval['runner_sha256']
    output=BASE/'execution-001';output.mkdir(mode=0o700,exist_ok=False)
    sys.dont_write_bytecode=True
    transport=module(ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py','existing_opaque_transport')
    capture=module(V/'ubuntu-storage-20261125/c808/host_control.py','existing_bounded_capture')
    capture.MAX_CAPTURE=65536
    command='python3 -c '+shlex.quote(controller.decode())
    start=time.monotonic();code,reason,counts,errors=capture.captured(transport.ssh()+[command],bundle,output,125)
    receipt={'schema':1,'exit_code':code,'capture_reason':reason,'capture_errors':errors,
        'elapsed_seconds':time.monotonic()-start,'controller_sha256':sha(controller),'bundle_sha256':sha(bundle),
        'combined_output_limit':65536,'stdout_bytes':counts[0],'stderr_bytes':counts[1],
        'stdout_sha256':sha((output/'stdout.raw').read_bytes()),'stderr_sha256':sha((output/'stderr.raw').read_bytes()),
        'credential_contents_exported':False,'opaque_existing_transport_used':True,
        'Ethereum_signer_files_read_or_copied':False,'existing_environments_changed':False,'service_actions':0}
    if code in (0,1) and reason is None:
        try:
            result=json.loads((output/'stdout.raw').read_bytes())
            assert type(result)is dict
            with (output/'RESULT.json').open('x',encoding='utf8')as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
            receipt['selection_success']=result.get('success')is True
        except (ValueError,TypeError,AssertionError):receipt['selection_success']=False
    with (output/'EXECUTION.json').open('x',encoding='utf8')as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(receipt));return code or bool(reason)or not receipt.get('selection_success',False)


if __name__=='__main__':raise SystemExit(main())
