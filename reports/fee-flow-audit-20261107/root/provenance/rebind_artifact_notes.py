from pathlib import Path
import json,hashlib,re,sys
R=Path.cwd();E=Path(__file__).parent;D=E/'artifact-rebind';D.mkdir(exist_ok=False)
N=E/'physical-agent/normal-final-4de5dcc67c';inp=json.loads((N/'compiler-input.json').read_text());out=json.loads((N/'compiler-output.json').read_text())
paths=['config/factory-code-storage-v3.json','zzz_ops/factory_code_v3.py','docs/function-reference-notes.json']
for name in paths:
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/name).read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
artifact=json.loads((R/paths[0]).read_text());old=json.loads((D/paths[0]).read_text())
newmap={p:sha(v['content'].encode())for p,v in inp['sources'].items()}
assert len(newmap)==87 and set(newmap)==set(old['source_sha256'])
changed=[p for p,h in newmap.items()if old['source_sha256'][p]!=h];assert changed==['src/base/ZZZRewardConverter.sol'],changed
artifact['source_sha256']=newmap
p=R/paths[0];p.write_bytes((json.dumps(artifact,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode())
canonical=sha(json.dumps(artifact,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
p=R/paths[1];raw=p.read_bytes();s=raw.decode().replace('\r\n','\n');s,n=re.subn(r"ARTIFACT_CANONICAL_SHA256='[0-9a-f]{64}'",f"ARTIFACT_CANONICAL_SHA256='{canonical}'",s);assert n==1;p.write_bytes(s.replace('\n','\r\n').encode()if b'\r\n'in raw else s.encode())
sys.path.insert(0,str(R));from zzz_ops import factory_code_v3 as F
assert F.verify_compiler_output(out)
for key in set(artifact)-{'source_sha256'}:assert artifact[key]==old[key],key
p=R/paths[2];raw=p.read_bytes();notes=json.loads(raw);functions=notes['contracts']['ZZZLPRewardConverter']['functions']
functions['convert(address,uint256,bytes32,uint256,uint256)']['purpose']='Convert selected earned input to measured ETH. Non-wrapper v3 swaps retain the wrapper-reference floor AND require a fresh final-native-ETH floor; authenticated wrappers must have18decimals. Direct unwrap remains exact1:1 without USD reads.'
functions['configureWrapper((bytes32,address,address,address,bytes32,bytes32,bytes32))']['purpose']='Review the immutable18-decimal wrapper runtime/proxy policy; execution revalidates identity, implementation and decimals. Native v4-only paths need no wrapper.'
p.write_bytes((json.dumps(notes,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode()if b'\r\n'in raw else (json.dumps(notes,ensure_ascii=False,indent=2)+'\n').encode())
proof={'schema':1,'normal':str(N),'source_pin_changes':changed,'all87_input_hashes_bound':True,'creation_payload_and_all_part_fields_identical':True,'profile_identity':3,'code_storage_format':2,'artifact_canonical_sha256':canonical,'before_artifact_sha256':sha((D/paths[0]).read_bytes()),'after_artifact_sha256':sha((R/paths[0]).read_bytes()),'verify_actual_compiler_payload':True}
(D/'PROOF.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
