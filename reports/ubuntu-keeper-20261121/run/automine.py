"""Enable immediate mining only on the already verified new private Anvil."""
from pathlib import Path
import importlib.util
import subprocess

ROOT=Path(__file__).resolve().parents[3]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121')
s=importlib.util.spec_from_file_location('strict',ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py');T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
CODE=r'''
from pathlib import Path
import importlib.util,hashlib,json
lab=Path('/opt/popl-ubuntu-20261121-8a629f43')
p=lab/'source/reports/ubuntu-keeper-20261121/run/capsule.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='071aa8eb1dc83493a5774dd5d5666dacefcd091fa9ffd7eb9e8a3e2177e634d6'
s=importlib.util.spec_from_file_location('frozen',p);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
l=M.Lab(lab)
print(json.dumps({'owned_automine':l.rpc('evm_setAutomine',[True]),'head':l.rpc('eth_getBlockByNumber',['latest',False])}))
'''
r=subprocess.run([*T.ssh(),'python3','-'],input=CODE.encode(),capture_output=True,timeout=30)
out=V/'run2/automine-01';out.mkdir(exist_ok=False)
(out/'stdout.json').write_bytes(r.stdout);(out/'stderr.raw').write_bytes(r.stderr)
assert r.returncode==0,r.stderr.decode()
print('Owned private Anvil automine enabled; captured public header.')
