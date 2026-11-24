"""Read only the stopped c801 disposable actor's exact journal, never key files."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess
BASE=Path(__file__).resolve().parent
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
transport_path=ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py'
remote='''import pathlib,stat,hashlib,json
p=pathlib.Path('/opt/popl-ubuntu-key-rotation-20261124-c801/runtime/run-001/jobs/rotation/old/state.json')
s=p.lstat();assert stat.S_ISREG(s.st_mode)and not p.is_symlink()and s.st_uid==65534 and s.st_size<=65536
b=p.read_bytes();assert len(b)==s.st_size
v=json.loads(b);assert v['sender']=='0xe4ccdc5192d57e086469e9ad84d1f1b248f166b3'and v['chain_id']==4663 and v['next_nonce']==0 and v['pending']['hash']is None
def check(x):
 if isinstance(x,dict):
  assert not set(x)&{'private_key','password','keystore','password_file','rpc_urls','mnemonic'}
  for a in x.values():check(a)
 elif isinstance(x,list):
  for a in x:check(a)
check(v)
print(json.dumps({'schema':1,'scope':'stopped_new_c801_actor_only','read_only':True,'journal_bytes':len(b),'journal_sha256':hashlib.sha256(b).hexdigest(),'raw_utf8':b.decode('utf8'),'state':v,'key_files_read':False,'service_actions':0}))
'''
spec=importlib.util.spec_from_file_location('opaque_transport',transport_path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
out=BASE/'rotation/preserved-intent-001';out.mkdir(exist_ok=False)
r=subprocess.run(mod.ssh()+['python3 -'],input=remote.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
assert len(r.stdout)<=256*1024 and len(r.stderr)<=65536
(out/'stdout.raw').write_bytes(r.stdout);(out/'stderr.raw').write_bytes(r.stderr)
assert r.returncode==0,'Stopped actor read failed'
v=json.loads(r.stdout);assert v['read_only']and not v['key_files_read'];(out/'ORIGINAL_HASHLESS_JOURNAL.json').write_bytes(r.stdout)
print(json.dumps({k:v[k]for k in ('scope','read_only','journal_bytes','journal_sha256','key_files_read','service_actions')}))
