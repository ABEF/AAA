"""Authenticate historical build bytes without treating them as current state."""
import gzip,hashlib,io,json
from pathlib import Path
from types import SimpleNamespace
from zzz_ops import deployment_plan as D

ROOT=Path(__file__).resolve().parents[1]

def archived(profile):
 spec=D.trusted_build(profile);raws={}
 for name,pin in spec['files'].items():
  with(ROOT/spec['directory']/name).open('rb')as source:raw=source.read(D.MAX_BUILD+1)
  if len(raw)>D.MAX_BUILD or hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('Historical factory build file differs from accepted pin')
  raws[name]=raw
 def unpack(name):
  with gzip.GzipFile(fileobj=io.BytesIO(raws[name]))as source:return D.decode(source.read(D.MAX_BUILD+1),D.MAX_BUILD)
 inp=unpack('compiler-input.json.gz');out=unpack('compiler-output.json.gz')
 manifest=D.decode(raws[spec['source_inventory']],D.MAX_BUILD);pins=manifest[spec['source_key']]
 if len(inp['sources'])!=100 or {n:hashlib.sha256(row['content'].encode('utf-8')).hexdigest()for n,row in inp['sources'].items()}!=pins:
  raise ValueError('Historical complete source closure differs from accepted manifest')
 # This hash-authenticated evidence includes fractional elapsed seconds. Those
 # report fields are not integer-only transaction or monetary inputs.
 gates=json.loads(raws[spec['gates']].decode('utf-8'),object_pairs_hook=D._pairs,
  parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite historical report')) )['gates']
 if len(gates)!=48:raise ValueError('Historical normal gate inventory incomplete')
 return SimpleNamespace(profile=profile,input=inp,output=out,source_pins=pins,gates=gates)
