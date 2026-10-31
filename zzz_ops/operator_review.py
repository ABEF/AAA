"""Offline operator provenance hashes and explorer arguments, never transactions.

reviewHash is SHA256(DOMAIN || canonical manifest), where canonical JSON is
ASCII, sorted keys, no whitespace, no floats. Exact reviewHash/reviewed ABI fields
contain $REVIEW_HASH in the preimage and the derived hash in the explorer output.
This hash is neither a custody/portfolio fingerprint nor on-chain authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from zzz_ops import function_reference as reference

ROOT=Path(__file__).resolve().parents[1]
PROFILE=('accounting6/protocol-policy1/portfolio2/maintenance3/confirmation3/compound4/custody4/emergency2/LP-routing2/'
    'pricing2/Entry-routing2/reviewedEntry2/directgovernance2/fee-intake1')
DOMAIN=b'ZZZ_POPL_OPERATOR_REVIEW_V1\n'
MARKER='$REVIEW_HASH'
MAX_DOCUMENT=128*1024
MAX_ARTIFACT=512*1024
MAX_CATALOG=4*1024*1024
MAX_DEPTH=16
MAX_ARRAY=128
MAX_EVIDENCE=16
BOUNDARIES=dict(offline_only=True,ready_for_submission=False,simulation_performed=False,
    onchain_snapshot_verified=False,target_runtime_verified=False,authority_verified=False,
    snapshot_freshness_verified=False,human_callability_verified=False,
    operational_guards_verified=False,contract_validates_review_preimage=False,
    review_hash_is_custody_or_portfolio_fingerprint=False)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def _keys(value,expected):
    if not isinstance(value,dict) or set(value)!=set(expected):raise ValueError('Unexpected or missing object fields')


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON field')
        result[key]=value
    return result


def _reject(_value):raise ValueError('Only integer JSON numbers are permitted')


def decode(raw,maximum=MAX_DOCUMENT):
    if not isinstance(raw,bytes) or len(raw)>maximum:raise ValueError('JSON document exceeds limit')
    text=raw.decode('utf-8-sig');depth=0;quoted=False;escape=False
    for char in text:
        if quoted:
            if escape:escape=False
            elif char=='\\':escape=True
            elif char=='"':quoted=False
        elif char=='"':quoted=True
        elif char in '[{':
            depth+=1
            if depth>MAX_DEPTH:raise ValueError('JSON nesting exceeds limit')
        elif char in ']}':depth-=1
    try:return json.loads(text,object_pairs_hook=_pairs,parse_float=_reject,parse_constant=_reject)
    except (RecursionError,UnicodeError) as exc:raise ValueError('Invalid bounded JSON document') from exc


def load(path,maximum=MAX_DOCUMENT):
    with Path(path).open('rb') as stream:return decode(stream.read(maximum+1),maximum)


def _hex(value,length,*,nonzero=False,prefix=True):
    pattern=('0x' if prefix else '')+'[0-9a-f]{'+str(length*2)+'}'
    if not isinstance(value,str) or re.fullmatch(pattern,value) is None:raise ValueError('Expected canonical lower-case hexadecimal')
    if nonzero and int(value,16)==0:raise ValueError('Zero identity is not permitted')
    return value


def _integer(value,bits=256,*,signed=False,positive=False):
    pattern=r'(?:0|[1-9][0-9]*)' if not signed else r'(?:0|-?[1-9][0-9]*)'
    if not isinstance(value,str) or len(value)>79 or re.fullmatch(pattern,value) is None:
        raise ValueError('ABI integers require canonical decimal strings')
    number=int(value);lower=-(1<<(bits-1)) if signed else 0;upper=1<<(bits-1) if signed else 1<<bits
    if not lower<=number<upper or positive and number<=0:raise ValueError('Integer exceeds allowed bounds')
    return value


def _arguments(items,values,*,depth=0):
    if depth>MAX_DEPTH or not isinstance(items,list) or len(items)>MAX_ARRAY:raise ValueError('ABI shape exceeds limit')
    labels=[item['label'] for item in items]
    if len(set(labels))!=len(labels):raise ValueError('Ambiguous ABI argument labels')
    _keys(values,labels)
    return {item['label']:_value(item,values[item['label']],depth=depth+1) for item in items}


def _value(item,value,*,depth):
    if depth>MAX_DEPTH:raise ValueError('ABI nesting exceeds limit')
    typ=item['type'];label=item['label']
    array=re.fullmatch(r'(.+)\[([0-9]*)\]',typ)
    if array:
        if not isinstance(value,list) or len(value)>MAX_ARRAY or array[2] and len(value)!=int(array[2]):
            raise ValueError('ABI array length differs')
        element={**item,'type':array[1]}
        return [_value(element,v,depth=depth+1) for v in value]
    if typ=='tuple':return _arguments(item['components'],value,depth=depth+1)
    if typ=='bytes32' and label in ('reviewHash','reviewed'):
        if value!=MARKER:raise ValueError('Review fields must use the explicit review-hash marker')
        return value
    if typ=='bool':
        if type(value) is not bool:raise ValueError('ABI bool requires true or false')
        return value
    if typ=='address':return _hex(value,20)
    integer=re.fullmatch(r'(u?int)([0-9]+)',typ)
    if integer:
        bits=int(integer[2])
        if not 8<=bits<=256 or bits%8:raise ValueError('Unsupported ABI integer width')
        return _integer(value,bits,signed=integer[1]=='int')
    fixed=re.fullmatch(r'bytes([0-9]+)',typ)
    if fixed:
        length=int(fixed[1])
        if not 1<=length<=32:raise ValueError('Unsupported ABI byte width')
        return _hex(value,length)
    if typ=='bytes':
        if not isinstance(value,str) or len(value)>8194 or re.fullmatch(r'0x(?:[0-9a-f]{2})*',value) is None:
            raise ValueError('Invalid bounded ABI bytes')
        return value
    if typ=='string':
        if not isinstance(value,str) or len(value.encode('utf-8'))>4096 or any(ord(c)<32 for c in value):
            raise ValueError('Invalid bounded ABI string')
        if MARKER in value:raise ValueError('Review marker is only valid in reviewHash/reviewed fields')
        return value
    raise ValueError('Unsupported ABI type')


def _ordered(items,values,review_hash):
    def convert(item,value):
        typ=item['type'];array=re.fullmatch(r'(.+)\[([0-9]*)\]',typ)
        if array:return [convert({**item,'type':array[1]},v) for v in value]
        if typ=='tuple':return _ordered(item['components'],value,review_hash)
        return review_hash if typ=='bytes32' and item['label'] in ('reviewHash','reviewed') else value
    return [convert(item,values[item['label']]) for item in items]


def _catalog_shape(data):
    _keys(data,('schema','source_snapshot','abi_snapshot','excluded_objects','notes_sha256','contracts','gaps','counts'))
    if type(data['schema']) is not int or data['schema']!=1:raise ValueError('Unsupported callable reference')
    if any(not isinstance(data[k],dict) for k in ('source_snapshot','abi_snapshot','counts')):
        raise ValueError('Malformed callable reference bindings')
    if (not isinstance(data['contracts'],list) or not 1<=len(data['contracts'])<=64 or
            any(not isinstance(data[k],list) for k in ('excluded_objects','gaps'))):
        raise ValueError('Malformed callable reference inventory')
    for contract in data['contracts']:
        if (not isinstance(contract,dict) or not isinstance(contract.get('name'),str) or
                not isinstance(contract.get('source'),str) or not isinstance(contract.get('functions'),list) or
                not 1<=len(contract['functions'])<=1024):raise ValueError('Malformed source contract')
        for fn in contract['functions']:
            if (not isinstance(fn,dict) or any(not isinstance(fn.get(k),str) for k in
                    ('kind','name','signature','state_mutability','access')) or not isinstance(fn.get('inputs'),list)):
                raise ValueError('Malformed callable inventory')


def render(value):
    raw=(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode('utf-8')
    if len(raw)>MAX_ARTIFACT:raise ValueError('Review artifact exceeds limit')
    return raw


class Catalog:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.path=self.root/'docs/function-reference.json'
        with self.path.open('rb') as stream:raw=stream.read(MAX_CATALOG+1)
        self.data=decode(raw,MAX_CATALOG)
        _catalog_shape(self.data)
        reference._check_sources(self.root,self.data['source_snapshot'])
        self.reference_sha256=digest(raw)
        self.source_snapshot_sha256=digest(canonical(self.data['source_snapshot']))

    def identity(self):
        return dict(schema=1,profile=PROFILE,reference_sha256=self.reference_sha256,
            source_snapshot_sha256=self.source_snapshot_sha256,boundaries=dict(BOUNDARIES))

    def prepare(self,request):
        _keys(request,('schema','profile','reference_sha256','source_snapshot_sha256','chain','snapshot',
            'contract','signature','arguments','review_notes_sha256','evidence_sha256'))
        if (type(request['schema']) is not int or request['schema']!=1 or request['profile']!=PROFILE or
                request['reference_sha256']!=self.reference_sha256 or request['source_snapshot_sha256']!=self.source_snapshot_sha256):
            raise ValueError('Review profile or source/catalog binding differs')
        chain=request['chain'];_keys(chain,('id','controller','governance','target','target_runtime_keccak256'))
        _integer(chain['id'],positive=True)
        for name in ('controller','governance','target'):_hex(chain[name],20,nonzero=True)
        _hex(chain['target_runtime_keccak256'],32,nonzero=True)
        snap=request['snapshot'];_keys(snap,('block_number','block_hash','timestamp'))
        _integer(snap['block_number']);_hex(snap['block_hash'],32,nonzero=True);_integer(snap['timestamp'],64,positive=True)
        _hex(request['review_notes_sha256'],32,nonzero=True,prefix=False)
        evidence=request['evidence_sha256']
        if not isinstance(evidence,list) or not 1<=len(evidence)<=MAX_EVIDENCE:raise ValueError('Bounded evidence hashes are required')
        for value in evidence:_hex(value,32,nonzero=True,prefix=False)
        if len(set(evidence))!=len(evidence):raise ValueError('Repeated evidence hash')
        contracts=[c for c in self.data['contracts'] if c['name']==request['contract']]
        if len(contracts)!=1:raise ValueError('Unknown or ambiguous source contract')
        matches=[f for f in contracts[0]['functions'] if f['kind']=='function' and f['signature']==request['signature']]
        if len(matches)!=1:raise ValueError('Unknown or ambiguous callable signature')
        fn=matches[0]
        expected=fn['name']+'('+','.join(reference.canonical_type(i) for i in fn['inputs'])+')'
        if expected!=fn['signature']:raise ValueError('ABI signature and argument shape differ')
        args=_arguments(fn['inputs'],request['arguments'])
        manifest={**request,'arguments':args}
        encoded=canonical(manifest)
        if len(encoded)>MAX_DOCUMENT:raise ValueError('Review manifest exceeds limit')
        review_hash='0x'+digest(DOMAIN+encoded)
        # Detect concurrent local source/catalog edits without adopting new pins.
        reference._check_sources(self.root,self.data['source_snapshot'])
        with self.path.open('rb') as stream:final_raw=stream.read(MAX_CATALOG+1)
        if len(final_raw)>MAX_CATALOG or digest(final_raw)!=self.reference_sha256:
            raise ValueError('Callable reference changed during preparation')
        artifact=dict(schema=1,kind='offline_operator_review',hash_algorithm='SHA-256',
            hash_domain=DOMAIN.decode('ascii'),canonicalization='ASCII JSON; sorted keys; separators comma/colon; no floats',
            review_hash=review_hash,manifest=manifest,
            explorer=dict(source_contract=request['contract'],signature=request['signature'],
                abi_mutability=fn['state_mutability'],catalog_access_description=fn['access'],
                argument_order=[i['label'] for i in fn['inputs']],arguments=_ordered(fn['inputs'],args,review_hash),
                value='Not prepared. ABI arguments are not transaction value or network gas.'),
            boundaries=dict(BOUNDARIES))
        render(artifact)
        return artifact

    def check(self,artifact):
        if not isinstance(artifact,dict) or 'manifest' not in artifact:raise ValueError('Missing review artifact')
        expected=self.prepare(artifact['manifest'])
        if canonical(artifact)!=canonical(expected):raise ValueError('Review artifact or hash was modified')
        return dict(schema=1,review_hash=expected['review_hash'],artifact_matches=True,boundaries=dict(BOUNDARIES))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    profile=sub.add_parser('profile',help='Print current local source/catalog pins; no deployment inspection')
    profile.add_argument('--output',type=Path,help='Create a NEW UTF-8 file; never overwrite')
    for name in ('prepare','check'):
        command=sub.add_parser(name);command.add_argument('input',type=Path)
        command.add_argument('--output',type=Path,help='Create a NEW UTF-8 file; never overwrite')
    args=parser.parse_args(argv)
    try:
        catalog=Catalog()
        result=(catalog.identity() if args.command=='profile' else
            catalog.prepare(load(args.input)) if args.command=='prepare' else catalog.check(load(args.input,MAX_ARTIFACT)))
        raw=render(result)
        if args.output is None:sys.stdout.write(raw.decode('utf-8'))
        else:
            with args.output.open('xb') as handle:
                if handle.write(raw)!=len(raw):raise OSError('Incomplete offline output')
        return 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,RecursionError):
        print('Offline review rejected: invalid input, changed source bindings or modified artifact.',file=sys.stderr)
        return 1


if __name__=='__main__':sys.exit(main())
