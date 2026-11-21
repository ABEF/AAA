"""Read-only reconciliation of the first owned fixture governor transaction."""
from pathlib import Path
import importlib.util
import subprocess
ROOT=Path(__file__).resolve().parents[3]
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/ubuntu-keeper-20261121')
s=importlib.util.spec_from_file_location('strict',ROOT/'reports/ubuntu-keeper-20261121/transport/strict_transport.py');T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
CODE=r'''
from pathlib import Path
import importlib.util,hashlib,json
lab=Path('/opt/popl-ubuntu-20261121-8a629f43');p=lab/'source/reports/ubuntu-keeper-20261121/run/capsule.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='071aa8eb1dc83493a5774dd5d5666dacefcd091fa9ffd7eb9e8a3e2177e634d6'
s=importlib.util.spec_from_file_location('frozen',p);M=importlib.util.module_from_spec(s);s.loader.exec_module(M);l=M.Lab(lab)
sender=json.loads((lab/'public/sender.json').read_bytes())['address'];instances=json.loads((lab/'public/instances.json').read_bytes());access=next(r['address']for r in instances if r['role']=='access')
head=l.rpc('eth_getBlockByNumber',['latest',False]);start=119107223+1;end=int(head['number'],16);assert 0<end-start<900
records=[]
for n in range(start,end+1):
 b=l.rpc('eth_getBlockByNumber',[hex(n),False])
 for h in b['transactions']:
  tx=l.rpc('eth_getTransactionByHash',[h]);rec=l.rpc('eth_getTransactionReceipt',[h]);tx={k:v for k,v in tx.items()if k in ('hash','from','to','input','nonce','value','blockHash','blockNumber','gas','gasPrice','type')};records.append({'transaction':tx,'receipt':rec})
print(json.dumps({'scanned_local_interval':[start,end],'records':records,'head':head,'keeper_grant':l.ethcall(access,'keepers(address)',sender),'nonce':l.rpc('eth_getTransactionCount',[sender,'latest'])}),flush=True)
assert len(records)==1 and records[0]['transaction']['to']==access and records[0]['transaction']['input']==l.calldata('setKeeper(address,bool)',sender,'true')
assert int(records[0]['receipt']['status'],16)==1 and int(l.ethcall(access,'keepers(address)',sender),16)==1
assert int(l.rpc('eth_getTransactionCount',[sender,'latest']),16)==0
print(json.dumps({'records':records,'keeper_grant_confirmed':True,'fresh_signer_nonce':0,'resubmitted':False}))
'''
r=subprocess.run([*T.ssh(),'python3','-'],input=CODE.encode(),capture_output=True,timeout=90)
out=V/'run2/reconcile-setup-02';out.mkdir(exist_ok=False)
(out/'stdout.json').write_bytes(r.stdout);(out/'stderr.raw').write_bytes(r.stderr)
assert r.returncode==0,r.stderr.decode()
print('Original fixture grant confirmed; disposable real signer nonce remains zero.')
