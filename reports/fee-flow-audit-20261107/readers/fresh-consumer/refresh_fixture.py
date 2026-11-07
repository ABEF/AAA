from pathlib import Path
import hashlib,json
r=Path.cwd();e=Path(__file__).parent;stage=e/'evm-real-vault-wire-current'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
status=json.loads((stage/'status.json').read_bytes());assert status['successful']
assert status['closed_unchanged'] and status['source_unchanged']
assert status['closed_after']['src/base/ZZZRewardConverter.sol']=='8bc96c86a0a8f18d95a1d9e69cd1dc4667e72d486b1367861a30fcd9414eb232'
assert all(sha(r/n)==h for n,h in status['closed_after'].items())
oldpath=e/'historical-original/exact-lp-source7-wire.json';old=json.loads(oldpath.read_bytes())
assert sha(oldpath)=='0fbff68493129dfae788cfd40c36cdc835037230a7c14b2d448297f40c90cf24'
data=json.loads((stage/'stdout.json').read_bytes());records=[]
for suite,body in data.items():
 if isinstance(body,dict):
  for name,item in body.get('test_results',{}).items():records.append((suite,name,item))
assert len(records)==1
suite,name,item=records[0]
assert suite=='test/ExactLPVaultWire.t.sol:ExactLPVaultWireTest'
assert name=='testExactLPRealVaultWireEnrollmentHarvestGrowthAndClaim()' and item['status']=='Success'
assert len(item['logs'])==77 and len(status['closed_after'])==95
start=json.loads((stage/'START.json').read_bytes())
new=dict(test_method=name,status=item['status'],test_source_sha256=sha(r/'test/ExactLPVaultWire.t.sol'),
 source_snapshot='evm-real-vault-wire-current/test-source.sol',normal_source_basis=start['normal_source_basis'],
 producer_stdout_sha256=sha(stage/'stdout.json'),producer_status_sha256=sha(stage/'status.json'),
 prior_fixture_sha256=sha(oldpath),raw_logs=item['logs'],decoded_logs=item.get('decoded_logs',[]))
for key in ('snapshot_field_order','snapshot_encoding','stage_meanings','actual_production_boundary'):new[key]=old[key]
new['complete_raw_closure']=status['closed_after']
target=r/'tests_python/fixtures/exact-lp-source7-wire.json';previous_pin=sha(target);target.write_bytes((json.dumps(new,indent=2)+'\n').encode('utf-8'))
pin=sha(target);test=r/'tests_python/test_exact_lp_source_wire.py';raw=test.read_bytes();assert raw.count(previous_pin.encode())==1
raw=raw.replace(previous_pin.encode(),pin.encode());test.write_bytes(raw)
(e/'final-exact-lp-source7-wire.json').write_bytes(target.read_bytes());(e/'final-test_exact_lp_source_wire.py').write_bytes(test.read_bytes())
proof=dict(prior_fixture_sha256=sha(oldpath),current_fixture_sha256=pin,
 producer_stdout_sha256=sha(stage/'stdout.json'),normal_source_basis=start['normal_source_basis'],
 actual_method=name,actual_status=item['status'],raw_log_count=len(item['logs']),complete_raw_source_count=len(status['closed_after']),
 raw_logs_equal_prior=item['logs']==old['raw_logs'],
 changed_raw_log_indices=[i for i,(a,b) in enumerate(zip(item['logs'],old['raw_logs'])) if a!=b],
 changed_closure={n:dict(previous=old['complete_raw_closure'].get(n),current=h) for n,h in status['closed_after'].items() if old['complete_raw_closure'].get(n)!=h},
 unchanged_producer_source=old['test_source_sha256']==new['test_source_sha256'],
 scope='Fresh actual production Vault/NFT/Rewards/Fees/Membership local synthetic-venue producer; no target-provider/route/gas/marketplace or release qualification. Previous bytes retained as historical-original, not relabeled.')
(e/'REFRESH_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,indent=2))
