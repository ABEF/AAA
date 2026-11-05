"""Code-owned immutable royalty-factory data format; never adopts RPC pins."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from zzz_ops.abi import keccak256

VERSION=2
PREFIX=bytes.fromhex('5f5ffd')
PART_DATA_LIMIT=24573
ARTIFACT=Path(__file__).resolve().parents[1]/'config/factory-code-storage-v2.json'
ARTIFACT_CANONICAL_SHA256='cef671e1bf1293d82d5313c5d54649e28db2f6bf8a3034675b66b3681ced9ba1'
MAX_ARTIFACT_BYTES=64*1024
SECTION_FIELDS=frozenset(('code_storage_version','creation_code_length','creation_code_hash',
    'parts','review_evidence','observed_creation_code_length','observed_creation_code_hash'))
PART_FIELDS=frozenset(('index','address','data_length','runtime_length','runtime_hash',
    'observed_data_length','observed_runtime_length','observed_runtime_hash','observed_prefix'))

@dataclass(frozen=True)
class Part:
    index:int
    data_length:int
    runtime_length:int
    runtime_hash:str

@dataclass(frozen=True)
class Artifact:
    creation_length:int
    creation_hash:str
    parts:tuple
    source_sha256:tuple


def _unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate factory artifact key')
        result[key]=value
    return result


def _hash(raw):return '0x'+keccak256(raw).hex()


def split_creation(code):
    if not isinstance(code,bytes) or not 1<=len(code)<=2*PART_DATA_LIMIT:
        raise ValueError('Unsupported fixed creation payload length')
    return PREFIX+code[:PART_DATA_LIMIT],PREFIX+code[PART_DATA_LIMIT:]


def load_artifact(path=ARTIFACT):
    with Path(path).open('rb') as source:raw=source.read(MAX_ARTIFACT_BYTES+1)
    if len(raw)>MAX_ARTIFACT_BYTES:raise ValueError('Oversized factory artifact')
    value=json.loads(raw.decode('utf-8'),object_pairs_hook=_unique,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite artifact value')))
    canonical=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    if hashlib.sha256(canonical).hexdigest()!=ARTIFACT_CANONICAL_SHA256:
        raise ValueError('Factory artifact differs from source-owned pin')
    expected={'schema','profile','code_storage_version','prefix','data_offset','max_part_data_bytes',
        'compiler','source_sha256','creation_code_length','creation_code_hash','parts'}
    if set(value)!=expected or value['schema']!=1 or value['profile']!='royalty_factory_code_storage_v2' or (
        value['code_storage_version'],value['prefix'],value['data_offset'],value['max_part_data_bytes'])!=(2,'0x5f5ffd',3,24573):
        raise ValueError('Unsupported factory artifact format')
    parts=tuple(Part(**row) for row in value['parts'])
    if len(parts)!=2 or [x.index for x in parts]!=[0,1] or sum(x.data_length for x in parts)!=value['creation_code_length']:
        raise ValueError('Inconsistent factory artifact parts')
    return Artifact(value['creation_code_length'],value['creation_code_hash'],parts,tuple(sorted(value['source_sha256'].items())))


SPEC=load_artifact()


def parse_section(chain):
    section=chain.get('factory_code')
    if not isinstance(section,dict) or set(section)!=SECTION_FIELDS:
        raise ValueError('Use exact factory code-data section')
    if type(section['code_storage_version']) is not int or section['code_storage_version']!=VERSION or (
        type(section['creation_code_length']) is not int or section['creation_code_length']!=SPEC.creation_length or
        section['creation_code_hash']!=SPEC.creation_hash):raise ValueError('Wrong source-owned factory identity')
    parts=section['parts']
    if not isinstance(parts,list) or len(parts)!=2:raise ValueError('Use exactly two factory data children')
    for row,expected in zip(parts,SPEC.parts):
        if not isinstance(row,dict) or set(row)!=PART_FIELDS or any(type(row[k]) is not int for k in ('index','data_length','runtime_length')):
            raise ValueError('Malformed factory data record')
        if (row['index'],row['data_length'],row['runtime_length'],row['runtime_hash'])!=(
            expected.index,expected.data_length,expected.runtime_length,expected.runtime_hash):
            raise ValueError('Factory data pin differs from compiled source')
    return section


def verify_runtime_parts(values):
    if not isinstance(values,(list,tuple)) or len(values)!=2:raise ValueError('Use exactly two runtime replies')
    code=[];observed=[]
    for raw,expected in zip(values,SPEC.parts):
        if not isinstance(raw,str) or len(raw)!=2+expected.runtime_length*2 or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',raw):
            raise ValueError('Missing, malformed or oversized factory data code')
        runtime=bytes.fromhex(raw[2:])
        if not runtime.startswith(PREFIX) or _hash(runtime)!=expected.runtime_hash:
            raise ValueError('Factory data runtime differs from independent pin')
        code.append(runtime[len(PREFIX):]);observed.append(dict(observed_data_length=len(runtime)-3,
            observed_runtime_length=len(runtime),observed_runtime_hash=_hash(runtime),observed_prefix='0x'+PREFIX.hex()))
    payload=b''.join(code)
    if len(payload)!=SPEC.creation_length or _hash(payload)!=SPEC.creation_hash:
        raise ValueError('Reconstructed factory payload differs from independent pin')
    return observed,dict(observed_creation_code_length=len(payload),observed_creation_code_hash=_hash(payload))


def verify_compiler_output(output):
    try:raw=output['contracts']['src/ZZZRoyaltyRewards.sol']['ZZZRoyaltyRewards']['evm']['bytecode']['object']
    except (TypeError,KeyError) as exc:raise ValueError('Missing exact royalty creation artifact') from exc
    if not isinstance(raw,str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2})+',raw):raise ValueError('Unlinked creation artifact')
    parts=split_creation(bytes.fromhex(raw))
    verify_runtime_parts(['0x'+x.hex() for x in parts])
    return True
