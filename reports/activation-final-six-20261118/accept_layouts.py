"""Record the specifically reviewed fresh layouts; no generic normalization."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parents[2]
O=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-final-six-20261118')
B=O/'build/final02'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
result=json.loads((B/'COMPILED_RESULT.json').read_bytes())
details=json.loads((B/'PRIVATE_LAYOUT_DIFFS.json').read_bytes())
p='src/ZZZContributionPricing.sol:ZZZContributionPricing'
r='src/ZZZRoyaltyRewards.sol:ZZZRoyaltyRewards'
assert set(details)=={p,r}
assert [(x['label'],x['slot'],x['offset'],x['type']['label'])for x in details[p]['baseline']]==[
 ('maintenanceBucket','0',0,'uint256'),('basis','1',0,'struct ZZZContributionPricing.Basis'),
 ('marks','10',0,'mapping(address => struct ZZZContributionPricing.Mark)'),('assets','11',0,'address[]')]
assert details[p]['final']==details[p]['baseline'][:1]
a={x['label']:x for x in details[r]['baseline']}
b={x['label']:x for x in details[r]['final']}
assert set(a)-set(b)=={'initialAllocated','allocationCursor','eligibleCount','eligibleWeight'}
assert set(b)-set(a)=={'assetStatus'}
assert b['assetStatus']['slot']=='16'and b['assetStatus']['type']['label']=='mapping(address => uint256)'
for label in set(a)&set(b):
    before,after=a[label],b[label]
    assert before['offset']==after['offset'] and before['contract']==after['contract']
    if label=='allocationBooks':
        oldbook=before['type']['value']['value'];newbook=after['type']['value']['value']
        assert oldbook['numberOfBytes']==newbook['numberOfBytes']=='64'
        assert [(m['label'],m['slot'],m['offset'],m['type']['label'])for m in oldbook['members']]==[('rounds','0',0,'uint256'),('position','1',0,'uint256')]
        assert [(m['label'],m['slot'],m['offset'],m['type']['label'])for m in newbook['members']]==[('packed','0',0,'uint256'),('wideRounds','1',0,'uint256')]
    else:assert before['type']==after['type'],label
    slot=int(before['slot'])
    shift=0 if slot<23 else 1 if slot<=28 else 3
    assert int(after['slot'])==slot-shift,label
assert len(result['abi_name_differences'])==1
names=result['abi_name_differences'][0]
assert names['identity']==r and len(names['parameter_output_name_or_internalType_changes'])==3
for row in names['parameter_output_name_or_internalType_changes']:
    assert row['baseline']=='' and row['final']=='asset'and row['field'].endswith('/inputs/0/name')
assert result['canonical_abi_types_identical'] and result['all_pass']
acceptance={
 'schema':1,'build_id':'activation-final-six-20261118','reviewed':True,
 'source_freeze_sha256':sha((O/'SOURCE_FREEZE.json').read_bytes()),
 'compiler_input_sha256':result['compiler_input_sha256'],'compiler_output_sha256':result['compiler_output_sha256'],
 'accepted_semantic_storage_deltas':{x['identity']:{'baseline_semantic_sha256':x['baseline_semantic_sha256'],
    'final_semantic_sha256':x['final_semantic_sha256']}for x in result['semantic_storage_differences']},
 'accepted_abi_name_changes':{r:names['parameter_output_name_or_internalType_changes']},
 'review_scope':'Fresh deployment only. No old private storage reinterpretation. Source code, exact-domain proofs and focused host/canonical checks reviewed separately.',
}
with (O/'LAYOUT_ACCEPTANCE.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(acceptance,f,indent=2);f.write('\n')
print('Accepted only two reviewed fresh private layouts and three cosmetic ABI input names.')
