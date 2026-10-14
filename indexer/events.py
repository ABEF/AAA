"""Static event decoding. Unknown/dynamic events retain their complete raw log."""
from __future__ import annotations
import json
from pathlib import Path
import re
from typing import Any
from zzz_ops.abi import decode_words

SCHEMA = json.loads((Path(__file__).parent/'event_schema.json').read_text())

def decode(log: dict[str,Any]) -> tuple[str|None,dict[str,Any]|None]:
    topics=log.get('topics',[])
    if not topics or topics[0].lower() not in SCHEMA: return None,None
    entry=SCHEMA[topics[0].lower()]
    words=decode_words(log.get('data','0x'))
    indexed=[t[2:] for t in topics[1:]]
    if any(not re.fullmatch(r'[0-9a-fA-F]{64}',w) for w in indexed): raise ValueError('Malformed indexed topic')
    if len(indexed)!=sum(f['indexed'] for f in entry['fields']): raise ValueError('Indexed argument count mismatch')
    if any(f['type'] not in ('address','bytes32','bool') and not re.fullmatch(r'uint\d*',f['type']) for f in entry['fields']):
        return entry['name'],None
    if len(words)!=sum(not f['indexed'] for f in entry['fields']): raise ValueError('Event data length mismatch')
    result={};i=j=0
    for f in entry['fields']:
        if f['indexed']: word=indexed[i];i+=1
        else: word=words[j];j+=1
        typ=f['type']
        if typ=='address':
            if int(word[:24],16): raise ValueError('Noncanonical event address')
            result[f['name']]='0x'+word[-40:].lower()
        elif typ=='bytes32': result[f['name']]='0x'+word.lower()
        elif typ=='bool':
            if int(word,16)>1: raise ValueError('Invalid event boolean')
            result[f['name']]=bool(int(word,16))
        else:
            bits=int(typ[4:] or 256)
            if int(word,16)>=1<<bits: raise ValueError('Event integer overflow')
            result[f['name']]=str(int(word,16))
    return entry['name'],result
