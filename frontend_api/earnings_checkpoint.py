"""Reviewed immutable earnings state, never an automatically trusted total cache.

The external configuration digest authenticates the exact artifact. Canonical
block/runtime/ledger checks still run. This is operator-approved evidence, not
a proof of complete logs or a replacement for preserving the raw database.
"""
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType

from frontend_api.earnings_replay import COLLECTION, NFT, Replay, SCALE, require, royalty_profile, allocation_unit
from frontend_api.history import HistoryError, HistorySnapshot, _stored_json, _hash
from zzz_ops.abi import address
from zzz_ops.work_budget import checkpoint

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 32 * 1024 * 1024
SOURCE_FILES = ('frontend_api/earnings_checkpoint.py', 'frontend_api/earnings_checkpoint_build.py',
    'frontend_api/earnings_replay.py', 'frontend_api/history.py', 'frontend_api/earnings.py',
    'frontend_api/service.py', 'frontend_api/wallet_earnings.py', 'zzz_ops/abi.py',
    'zzz_ops/log_provenance.py')
SHARED = ('mints', 'shares', 'supply', 'members', 'weights', 'activation_order',
          'cohorts', 'owner_index', 'collective_index', 'royalty_index', 'fee_dust',
          'fee_keys', 'events', 'last_timestamp', 'frozen', 'retired',
          'royalty_mint_end', 'royalty_opening', 'initial_royalty_allocations',
          'royalty_settlement_version', 'ticket_offsets', 'royalty_cursors')
DEFAULT_MAPS = ('supply', 'owner_index', 'collective_index', 'royalty_index', 'fee_dust', 'royalty_cursors')


def source_identity():
    return {n: hashlib.sha256((ROOT/n).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            for n in SOURCE_FILES}


def identity(engine):
    p, h = engine.p, engine.p.history
    require(p.lineage is None, 'Checkpoint profile does not support predecessor lineage')
    require(p.accounting_version == 6 and p.custody_version == 5 and p.fee_intake_version == 1,
            'Checkpoint requires explicit accounting6/custody5/fee-intake1')
    return dict(chain=p.chain, deployment_block=p.start, deployment_hash=p.start_hash,
        accounting=6, custody=5, fee_intake=1, royalty_settlement=royalty_profile(p),
        contracts={role:dict(address=c.address, code_hash=c.code_hash) for role,c in p.contracts.items()},
        extra={role:dict(address=c.address,code_hash=c.code_hash)
               for role,c in engine.profiles[p.contracts['access'].address].items()},
        history=dict(start=h.start,parent=h.parent,contracts=h.contracts,
                     nft=h.nft,rewards=h.rewards,royalties=h.royalties),
        assets={a:dict(symbol=d.symbol,decimals=d.decimals,code_hash=d.code_hash) for a,d in p.assets.items()})


def encode(value):
    """Small fixed tagged grammar; no Python objects, floats or executable codec."""
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        require(-1 <= value < 1 << 512, 'Checkpoint integer exceeds the supported bound')
        return ['int', str(value)]
    if isinstance(value, dict):
        rows = [[encode(k), encode(v)] for k,v in value.items()]
        return ['map', sorted(rows, key=lambda r: json.dumps(r[0], sort_keys=True))]
    if isinstance(value, (list, tuple, set)):
        tag = 'set' if isinstance(value,set) else 'tuple' if isinstance(value,tuple) else 'list'
        rows = [encode(v) for v in value]
        return [tag, sorted(rows,key=lambda v:json.dumps(v,sort_keys=True)) if tag=='set' else rows]
    raise HistoryError('Unsupported checkpoint value type')


def decode(value, *, limit=1000000):
    remaining = limit
    def visit(v, depth=0):
        nonlocal remaining
        remaining -= 1
        require(remaining >= 0 and depth <= 12, 'Checkpoint structure exceeds supported bounds')
        if remaining % 256 == 0:
            checkpoint()
        if type(v) in (str,bool) or v is None:
            require(not isinstance(v,str) or len(v)<=1024, 'Oversized checkpoint scalar')
            return v
        require(isinstance(v,list) and len(v)==2 and isinstance(v[0],str), 'Invalid checkpoint encoding')
        tag, items = v
        if tag == 'int':
            require(isinstance(items,str) and len(items)<=155 and
                    re.fullmatch(r'-1|0|[1-9][0-9]*',items), 'Invalid checkpoint integer')
            result=int(items)
            require(result < 1 << 512, 'Checkpoint integer exceeds supported bounds')
            return result
        require(tag in ('list','tuple','set','map') and isinstance(items,list), 'Unknown checkpoint encoding')
        if tag == 'map':
            result={}
            for row in items:
                require(isinstance(row,list) and len(row)==2, 'Invalid checkpoint mapping row')
                key,item=visit(row[0],depth+1),visit(row[1],depth+1)
                require(key not in result, 'Duplicate checkpoint mapping key')
                result[key]=item
            return result
        result=[visit(x,depth+1) for x in items]
        if tag == 'set':
            require(len(set(result))==len(result), 'Duplicate checkpoint set item')
            return set(result)
        return tuple(result) if tag=='tuple' else result
    try:
        return visit(value)
    except (TypeError, ValueError, RecursionError):
        raise HistoryError('Invalid checkpoint structure') from None


def _nonnegative(value):
    if type(value) is int:
        require(value >= 0, 'Negative checkpoint accounting value')
    elif isinstance(value,dict):
        for k,v in value.items():
            _nonnegative(k);_nonnegative(v)
    elif isinstance(value,(set,list,tuple)):
        for v in value:_nonnegative(v)


@dataclass(frozen=True)
class Seed:
    digest: str
    anchor: dict
    bound: dict
    payload: dict
    history: HistorySnapshot

    def validate_history(self, h, db, target, timestamp, lp, royalties):
        expected=dict(start=h.start,parent=h.parent,contracts=h.contracts,
                      nft=h.nft,rewards=h.rewards,royalties=h.royalties)
        require(self.bound['chain']==h.chain and self.bound['history']==expected,
                'Checkpoint history identity differs')
        n=self.anchor['number']
        require(h.start<=n<=target and self.anchor['timestamp']<=timestamp,
                'Requested history precedes checkpoint')
        row=db.execute('SELECT hash,timestamp FROM blocks WHERE chain=? AND number=?',(h.chain,n)).fetchone()
        require(row==(self.anchor['hash'],self.anchor['timestamp']), 'Checkpoint is not the indexed canonical anchor')
        first=db.execute('SELECT hash FROM blocks WHERE chain=? AND number=?',(h.chain,h.start)).fetchone()
        require(first==(self.history.provenance['start_block_hash'],), 'Checkpoint creation history differs')
        require(set(self.payload['lp_assets']) <= lp and set(self.payload['royalty_assets']) <= royalties,
                'Checkpoint currencies are absent from admitted history')
        # This bounds the cross-prefix duplicate lookup by the existing PK index.
        keys=[r[2] for r in db.execute('PRAGMA index_info(sqlite_autoindex_logs_1)')]
        require(keys==['chain','transaction_hash','log_index'], 'Checkpoint needs the reviewed transaction lookup index')
        return n

    def restore(self, model):
        require(isinstance(model,Replay) and not model.minted and model.events==0,
                'Checkpoint consumer is not a fresh earnings replay')
        require(model.roles=={v:k for k,v in self.payload['emitters'].items()} and
                model.fee_intake_version==1, 'Checkpoint earnings emitter/profile differs')
        require(model.timestamp >= self.anchor['timestamp'], 'Checkpoint is newer than replay')
        if not model.track_all:
            require(model.timestamp-self.anchor['timestamp']>=86400,
                    'Earnings checkpoint must precede the complete rolling day')
        shared=self.payload['shared']
        for name in SHARED:
            value=shared[name]
            setattr(model,name,defaultdict(int,value) if name in DEFAULT_MAPS else value)
        model.minted=set(model.mints)
        selected=tuple(model.mints) if model.track_all else model.selected
        model.selected=selected
        all_accounts=self.payload['accounts']
        model.accounts={i:defaultdict(int,all_accounts.get(i,{})) for i in selected}
        model.account_totals={i:defaultdict(int,{k:v//SCALE for k,v in model.accounts[i].items()}) for i in selected}
        model.totals=defaultdict(int,self.payload['collection'])
        for account in model.account_totals.values():
            for key,value in account.items():model.totals[key]+=value
        if model.nft_id is not None:
            model.scaled=defaultdict(int,model.accounts[model.nft_id])
        # No stored day totals: the entire actual day is in the raw suffix.
        model.day=defaultdict(int)


class Checkpoint:
    def __init__(self, config, engine):
        require(isinstance(config,dict) and set(config)=={'path','sha256'} and
                isinstance(config['path'],str) and config['path'] and
                isinstance(config['sha256'],str) and re.fullmatch('[0-9a-f]{64}',config['sha256']),
                'Invalid reviewed earnings checkpoint configuration')
        self.digest=config['sha256']
        try:
            with Path(config['path']).open('rb') as f: raw=f.read(MAX_BYTES+1)
            require(len(raw)<=MAX_BYTES and hashlib.sha256(raw).hexdigest()==self.digest,
                    'Earnings checkpoint bytes differ from the reviewed configuration pin')
            data=_stored_json(raw.decode('utf-8'))
            require(isinstance(data,dict) and set(data)=={'schema','sources','identity','anchor','state','previous_sha256'}
                    and type(data['schema']) is int and data['schema']==1,
                    'Unknown earnings checkpoint schema')
            require(data['sources']==source_identity(), 'Earnings checkpoint semantic source changed')
            bound=decode(data['identity']);current=identity(engine)
            assets=bound.pop('assets');current_assets=current.pop('assets')
            require(encode(bound)==encode(current) and isinstance(assets,dict) and
                    all(encode(current_assets.get(a))==encode(d) for a,d in assets.items()),
                    'Earnings checkpoint deployment identity changed')
            bound['assets']=assets
            anchor=decode(data['anchor'])
            require(isinstance(anchor,dict) and set(anchor)=={'number','hash','timestamp'} and
                    type(anchor['number']) is int and engine.p.history.start<=anchor['number']<1<<63 and
                    type(anchor['timestamp']) is int and 0<=anchor['timestamp']<1<<63,
                    'Invalid earnings checkpoint anchor')
            _hash(anchor['hash'])
            payload=decode(data['state'])
            self._validate(payload,anchor,engine)
            require(data['previous_sha256'] is None or isinstance(data['previous_sha256'],str) and
                    re.fullmatch('[0-9a-f]{64}',data['previous_sha256']), 'Invalid previous checkpoint identity')
            # Retain immutable encoded bytes. Each request gets independent maps;
            # model replay must never mutate another user's checkpoint state.
            self._raw=raw
            self.anchor=MappingProxyType(anchor)
        except (OSError,UnicodeError,ValueError,KeyError,TypeError,AttributeError,RecursionError):
            raise HistoryError('Earnings checkpoint is unavailable or malformed') from None

    @staticmethod
    def _validate(v, anchor, engine):
        require(isinstance(v,dict) and set(v)=={'shared','accounts','collection','history','emitters','lp_assets','royalty_assets'},
                'Incomplete earnings checkpoint state')
        s=v['shared']
        require(isinstance(s,dict) and set(s)==set(SHARED), 'Unknown shared earnings checkpoint state')
        require(type(s['last_timestamp']) is int and -1<=s['last_timestamp']<=anchor['timestamp'], 'Invalid checkpoint chronology')
        _nonnegative({k:x for k,x in v.items() if k not in ('shared','history')})
        _nonnegative({k:x for k,x in s.items() if k!='last_timestamp'})
        mints=s['mints']
        require(isinstance(mints,list) and len(mints)<=1000 and len(set(mints))==len(mints) and
                all(type(i) is int and 0<i<1<<256 for i in mints), 'Invalid checkpoint NFT inventory')
        require(isinstance(v['accounts'],dict) and set(v['accounts'])==set(mints) and
                all(type(i) is int for i in v['accounts']), 'Incomplete checkpoint fraction inventory')
        def uint(n):return type(n) is int and 0<=n<1<<256
        def currency(a):return a in engine.descriptors
        for name,maximum in (('lp_assets',33),('royalty_assets',65)):
            a=v[name]
            require(isinstance(a,list) and len(a)<=maximum and len(set(a))==len(a) and all(currency(x) for x in a),
                    'Invalid checkpoint currency inventory')
        require('0x'+'0'*40 in v['royalty_assets'], 'Checkpoint omits native royalty currency')
        expected_emitters={r:engine.p.contracts[r].address for r in ('nft','vault','rewards','royalties','handoff')}
        expected_emitters.update({r:c.address for r,c in engine.profiles[engine.p.contracts['access'].address].items()})
        require(v['emitters']==expected_emitters, 'Checkpoint emitters differ from configuration')
        require(isinstance(s['shares'],dict) and set(s['shares'])<=set(mints) and all(type(i) is int for i in s['shares']),
                'Invalid checkpoint share inventory')
        supply=defaultdict(int)
        for i,pair in s['shares'].items():
            require(isinstance(pair,tuple) and len(pair)==2 and all(uint(n) and n>0 for n in pair),
                    'Invalid checkpoint share record')
            supply[pair[0]]+=pair[1]
        require(isinstance(s['supply'],dict) and s['supply']==dict(supply) and len(supply)<=4 and
                all(uint(k) and uint(n) and n>0 for k,n in s['supply'].items()),
                'Checkpoint share denominators differ')
        require(isinstance(s['members'],set) and isinstance(s['weights'],dict) and
                s['members']==set(s['weights'])==set(s['shares']) and
                all(type(i) is int for i in s['members']) and all(type(i) is int for i in s['weights']) and
                all(type(w) is int and 1<=w<=3 for w in s['weights'].values()), 'Invalid checkpoint active weights')
        order=s['activation_order']
        require(isinstance(order,list) and len(set(order))==len(order) and set(order)==s['members'] and all(type(i) is int for i in order),
                'Invalid checkpoint activation order')
        require(s['royalty_settlement_version']==royalty_profile(engine.p), 'Checkpoint royalty profile differs')
        require(isinstance(s['ticket_offsets'],dict) and set(s['ticket_offsets'])==set(order), 'Invalid checkpoint ticket inventory')
        start=0
        for i in order:
            require(type(s['ticket_offsets'][i]) is int and s['ticket_offsets'][i]==start, 'Checkpoint ticket order differs')
            start+=s['weights'][i]
        require(isinstance(s['royalty_cursors'],dict) and all(a in v['royalty_assets'] and uint(n)
                and (n < sum(s['weights'][i] for i in s['cohorts'][a]) and
                     n % allocation_unit(s['weights'][i] for i in s['cohorts'][a]) == 0 if s['cohorts'][a] else n==0)
                for a,n in s['royalty_cursors'].items()), 'Invalid checkpoint exact royalty cursor')
        end, opening = s['royalty_mint_end'], s['royalty_opening']
        require(end is None or (type(end) is int and 0<end<2**64), 'Invalid checkpoint royalty sale end')
        require(opening is None or (isinstance(opening,tuple) and len(opening)==3 and end is not None and
                all(uint(n) for n in opening) and opening[0]==end+3600 and opening[0]<=anchor['timestamp'] and
                opening[1]<=len(order) and opening[2]==sum(s['weights'][i] for i in order[:opening[1]])),
                'Invalid checkpoint initial royalty cohort')
        require(isinstance(s['initial_royalty_allocations'],set) and s['initial_royalty_allocations']<=set(v['royalty_assets']) and
                (not s['initial_royalty_allocations'] or opening is not None), 'Invalid checkpoint initial currency allocations')
        require(isinstance(s['cohorts'],dict) and set(s['cohorts'])==set(v['royalty_assets']) and
                all(isinstance(c,set) and c<=s['members'] and c==set(order[:len(c)]) and
                    all(type(i) is int for i in c) for c in s['cohorts'].values()),
                'Invalid checkpoint royalty cohorts')
        for name in ('owner_index','fee_dust'):
            require(isinstance(s[name],dict) and all(isinstance(k,tuple) and len(k)==2 and
                    uint(k[0]) and k[0] in supply and k[1] in v['lp_assets'] and uint(n) and (name!='fee_dust' or n<20)
                    for k,n in s[name].items()), 'Invalid checkpoint bucket index/dust')
        for name,assets in (('collective_index',v['lp_assets']),('royalty_index',v['royalty_assets'])):
            require(isinstance(s[name],dict) and all(a in assets and uint(n) for a,n in s[name].items()),
                    'Invalid checkpoint global index')
        require(isinstance(s['fee_keys'],set) and all(isinstance(k,tuple) and len(k)==2 and
                uint(k[0]) and k[0] in supply and k[1] in v['lp_assets'] for k in s['fee_keys']), 'Invalid checkpoint fee keys')
        require(type(s['events']) is int and s['events']>0 and s['last_timestamp']>=0,
                'Invalid checkpoint event count/chronology')
        for i,account in v['accounts'].items():
            require(isinstance(account,dict), 'Invalid checkpoint earnings account')
            for key,amount in account.items():
                require(isinstance(key,tuple) and len(key)==2 and key[0] in NFT and key[1] in engine.descriptors
                        and type(amount) is int and amount>=0, 'Invalid checkpoint NFT earnings')
                require(amount==0 or i in s['members'], 'Dormant checkpoint NFT has earnings')
                if s['royalty_settlement_version']==4 and key[0]=='royalties':
                    require(amount%SCALE==0, 'Exact royalty checkpoint contains fractional entitlement')
        require(isinstance(v['collection'],dict) and all(isinstance(k,tuple) and len(k)==2 and k[0] in COLLECTION
                and k[1] in engine.descriptors and type(n) is int and n>=0 for k,n in v['collection'].items()),
                'Invalid checkpoint collection earnings')
        require(s['frozen'] is False and s['retired'] is False, 'Canonical lifecycle checkpoint is unsupported')
        history=v['history']
        require(isinstance(history,dict) and set(history)=={'owners','claims','conversions','lp_conversions','provenance'}
                and set(history['owners'])==set(mints) and all(type(i) is int for i in history['owners']),
                'Checkpoint ownership inventory differs')
        require(all(address(a)==a for a in history['owners'].values()), 'Invalid checkpoint owner')
        require(isinstance(history['claims'],dict), 'Invalid checkpoint claims')
        for key,amounts in history['claims'].items():
            require(isinstance(key,tuple) and len(key)==2 and type(key[0]) is int and key[0] in mints and currency(key[1]) and
                    isinstance(amounts,tuple) and len(amounts)==2 and all(type(n) is int and n>=0 for n in amounts),
                    'Invalid checkpoint claimed amounts')
        for field,role in (('conversions','royalties'),('lp_conversions','rewards')):
            require(isinstance(history[field],dict), 'Invalid checkpoint conversions')
            for key,row in history[field].items():
                require(isinstance(key,tuple) and len(key)==2 and type(key[0]) is int and key[0] in mints and currency(key[1]) and
                        key[1]!='0x'+'0'*40 and isinstance(row,tuple) and len(row)==4 and
                        all(type(n) is int and n>=0 for n in row[:3]) and row[2]>0,
                        'Invalid checkpoint conversion amounts')
                last=row[3]
                require(isinstance(last,dict) and set(last)=={'ledger','block_number','block_hash','timestamp','transaction_hash','log_index'}
                        and last['ledger']==engine.p.contracts[role].address and
                        type(last['block_number']) is int and engine.p.history.start<=last['block_number']<=anchor['number'] and
                        type(last['timestamp']) is int and 0<=last['timestamp']<=anchor['timestamp'] and
                        type(last['log_index']) is int and 0<=last['log_index']<1<<63,
                        'Invalid checkpoint conversion provenance')
                _hash(last['block_hash']);_hash(last['transaction_hash'])
        for name in ('logs_examined','claim_events','royalty_conversion_events','lp_conversion_events'):
            require(type(history['provenance'].get(name)) is int and history['provenance'][name]>=0,
                    'Invalid checkpoint history counts')
        require(history['provenance'].get('through_block')==anchor['number'] and
                history['provenance'].get('block_hash')==anchor['hash'] and
                history['provenance'].get('from_block')==engine.p.history.start and
                history['provenance'].get('start_parent_hash')==engine.p.history.parent and
                history['provenance'].get('minted_count')==len(mints), 'Checkpoint history cutoff differs')
        _hash(history['provenance']['start_block_hash'])
        probe=Replay(anchor['timestamp'],track_all=True)
        probe.begin(v['emitters'],v['lp_assets'],v['royalty_assets'],fee_intake_version=1,royalty_settlement_version=royalty_profile(engine.p))
        seed=Seed('',anchor,{},v,None);seed.restore(probe);probe.finish()

    def seed(self):
        data=_stored_json(self._raw.decode('utf-8'))
        payload=decode(data['state']);anchor=decode(data['anchor']);bound=decode(data['identity'])
        h=payload['history']
        history=HistorySnapshot(MappingProxyType(h['owners']),MappingProxyType(h['claims']),
            MappingProxyType(h['provenance']),MappingProxyType(h['conversions']),MappingProxyType(h['lp_conversions']))
        return Seed(self.digest,anchor,bound,payload,history)

    def check_anchor(self,p):
        require(p._header(hex(self.anchor['number']))==dict(self.anchor),
                'Earnings checkpoint anchor is no longer canonical; preserve evidence and rebuild')
