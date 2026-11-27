"""Offline concatenation only; preserved controller is parsed, never executed."""
from pathlib import Path
import ast,hashlib,json

BASE=Path(__file__).resolve().parent
PRESERVED='f102550ea30927350c5b815fda020ccf4ea6a23fae00379668af8ccba351f10e'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    original=(BASE.parent/'remote_capsule.py').read_bytes();assert sha(original)==PRESERVED and len(original)==56751
    prefix=b"__name__='_preserved_c825_controller'\n"
    tail=(BASE/'continuation_tail.py').read_bytes()
    ast.parse(original);ast.parse(tail)
    combined=prefix+original+b'\n'+tail;ast.parse(combined);assert len(combined)<=65536
    assert combined[len(prefix):len(prefix)+len(original)]==original
    with(BASE/'complete_continuation.py').open('xb')as stream:stream.write(combined)
    receipt={'schema':1,'kind':'c825-offline-complete-continuation-build','bytes':len(combined),'sha256':sha(combined),
        'preserved_controller_bytes':len(original),'preserved_controller_sha256':PRESERVED,
        'preserved_controller_byte_slice_equal':True,'only_native_mode_requested':'complete',
        'native_calls':0,'application_imports':0,'server_actions':0,'test_bodies_run':0,
        'original_controller_or_worker_or_installed_inputs_modified':False,
        'passed_negative_result_sha256':'ad5813b9433039f5cf35925988bc673833b4b5c7f7a237d3e8a5ca21d9d0390d',
        'passed_negative_bytes':3714,'tail_sha256':sha(tail)}
    with(BASE/'BUILD_RECEIPT.json').open('x',encoding='utf8')as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(receipt,sort_keys=True))


if __name__=='__main__':main()
