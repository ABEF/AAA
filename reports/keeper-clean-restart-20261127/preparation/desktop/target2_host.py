"""Pinned target2-only continuation; never node/source/setup restart or signing."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,shlex
BASE=Path(__file__).resolve().parent;LAB=BASE.parent/'c828'
CONT=LAB/'continuation/target2_continuation.py'
EXPECTED='c6ef1c1ed2b1f10c9c393e6d9c5438fb81e913f6eccce53b491b70b1bf8f9e8d'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('fresh2','start2','status2','result2','private2','final2','stop2'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=CONT.read_bytes();assert len(raw)<=65536 and sha(raw)==EXPECTED
    pins=json.loads((LAB/'PARENT_REVIEW_PINS.json').read_bytes());assert sha((LAB/'host_control.py').read_bytes())==pins['files']['host_control.py']
    spec=importlib.util.spec_from_file_location('fixed_c828_host',LAB/'host_control.py');host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    assert sha(host.CAPTURE.read_bytes())==host.CAPTURE_SHA and sha(host.TRANSPORT.read_bytes())==host.TRANSPORT_SHA
    output=host.private_path(a.output,new=True);output.mkdir(parents=True)
    capture=host.module(host.CAPTURE,'fixed_c825_capture');transport=host.module(host.TRANSPORT,'fixed_ssh_transport')
    args=['python3','-I','-S','-B','-c',host.BOOTSTRAP,a.action,'--controller-sha256',EXPECTED]
    code,reason,counts,errors=capture.capture(transport.ssh()+[' '.join(map(shlex.quote,args))],len(raw).to_bytes(4,'big')+raw,output)
    receipt={'schema':1,'action':a.action,'exit_code':code,'capture_reason':reason,'capture_errors':errors,'counts':counts,
        'controller_sha256':EXPECTED,'preserved_c828_controller_sha256':'22d459431d168fa5822ea8917544a2de166f2e1a820b1d9f6de39516a1d31a91',
        'combined_output_limit':65536,'action_timeout_seconds':45,'node_or_source_restart_or_setup_replay':False,'signing':False,'private_raw_capture':True}
    if code==0 and reason is None and not errors:
        result=host.decode((output/'stdout.raw').read_bytes())
        if a.action in('result2','private2'):
            artifact='TARGET2_RESULT.json'if a.action=='result2'else'TARGET2_PRIVATE.zlib'
            data=base64.b64decode(result['raw_base64'],validate=True)
            assert result['name']==artifact and len(data)==result['bytes']<=32768 and sha(data)==result['sha256'];host.write(output/artifact,data)
        else:host.write(output/'SANITIZED_RESULT.json',host.enc(result))
    host.write(output/'EXECUTION.json',host.enc(receipt));print(json.dumps(receipt));assert code==0 and reason is None and not errors
if __name__=='__main__':main()
