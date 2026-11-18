"""Rebind only the source hash; retain all operator example row bytes."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from zzz_ops.function_reference import canonical_json

p=Path('docs/operator-call-examples.json')
raw=p.read_bytes();value=json.loads(raw)
reference=json.loads(Path('docs/function-reference.json').read_bytes())
old=value['reference_sha256'].encode('ascii')
new=hashlib.sha256(canonical_json(reference).encode('utf-8')).hexdigest().encode('ascii')
assert raw.count(old)==1 and len(value['rows'])==1021
updated=raw.replace(old,new)
assert json.loads(updated)['rows']==value['rows']
p.write_bytes(updated)
print('Rebound source hash; preserved all 1021 operator rows byte-for-byte.')
