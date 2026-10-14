from pathlib import Path
import json
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from zzz_ops.abi import keccak256
root = Path(__file__).resolve().parents[1]
texts = [x.read_text() for x in sorted((root/'src').glob('*.sol'))]
texts.append('event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);')
texts.append('event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);')
texts.append('event ApprovalForAll(address indexed owner, address indexed operator, bool approved);')
schema = {}
for text in texts:
    for name,arguments in re.findall(r'event\s+(\w+)\s*\((.*?)\)\s*;',text,re.S):
        fields=[]
        for argument in arguments.split(','):
            terms=argument.strip().split()
            if not terms: continue
            fields.append({'type':terms[0],'name':terms[-1],'indexed':'indexed' in terms})
        signature=f"{name}({','.join(f['type'] for f in fields)})"
        topic='0x'+keccak256(signature.encode()).hex()
        schema[topic]={'name':name,'signature':signature,'fields':fields}
(root/'indexer/event_schema.json').write_text(json.dumps(schema,indent=2,sort_keys=True)+'\n')
print(f'Generated {len(schema)} event schemas from current source')
