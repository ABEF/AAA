"""Read-only checkpoint construction; no automatic approval, pruning or signing."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace

from frontend_api.earnings_checkpoint import Checkpoint, SHARED, COLLECTION, decode, encode, identity, source_identity, MAX_BYTES
from frontend_api.earnings_replay import Replay, require
from frontend_api.history import conversion_report
from zzz_ops.work_budget import Budget, checkpoint, request_scope


class BuildBudget(Budget):
    """Explicit offline limits; HTTP request budgets are never increased."""
    def __init__(self, seconds=60, calls=4096, posts=8192):
        if type(seconds) is not int or not 1<=seconds<=3600:
            raise ValueError('Checkpoint build seconds must be1..3600')
        if any(type(v) is not int or not 1<=v<=65536 for v in (calls,posts)):
            raise ValueError('Checkpoint RPC limits must be1..65536')
        self.clock=time.monotonic;self.deadline=self.clock()+seconds
        self.calls,self.posts=calls,posts;self.expiries=[]


def build(engine, number, *, budget=None):
    with request_scope(budget or BuildBudget()):
        return _build(engine,number)


def _build(engine, number):
    """Build/advance one operating fresh deployment, reconciling every NFT.

    The caller must budget this explicit maintenance job, not expose it as HTTP.
    No artifact is written until all historical RPC/state checks have passed.
    """
    p=engine.p;bound=identity(engine)
    require(type(number) is int and p.start<=number<1<<63, 'Invalid checkpoint block')
    sources=source_identity()
    safe=confirmed_head(p)
    require(number<=safe['number'], 'Checkpoint block is not confirmed')
    header=p._header(hex(number));at={'blockHash':header['hash'],'requireCanonical':True}
    life=p._verify_deployment(at)
    require(life['predecessor_controller'] is None, 'Checkpoint requires original deployment history')
    lp,royalties=p._admitted(at);emitters=engine.check_profile(p,at)
    model=Replay(header['timestamp'],track_all=True)
    model.begin(emitters,lp,royalties,fee_intake_version=p.fee_intake_version)
    history=engine.history_snapshot(p,header,at,lp,royalties,consumer=model,extra_emitters=tuple(emitters.values()))
    model.finish()
    require(not model.frozen and not model.retired and not model.royalty_custody and not model.custody_ids,
            'Canonical or historical external-custody checkpoint is unsupported')
    engine.reconcile(p,model,at,lp,royalties,history.provenance['minted_count'])
    for ordinal,i in enumerate(model.mints,1):
        checkpoint()
        require(p._addr('nft','ownerOf(uint256)',i,block=at)==history.owners[i] and
                p._uint('nft','mintOrdinalOf(uint256)',i,block=at)==ordinal and
                p._uint('nft','tokenAtOrdinal(uint256)',ordinal,block=at)==i,
                'Checkpoint NFT identity or ownership differs from chain')
        bucket,shares=model.shares.get(i,(0,0))
        require(p._uint('vault','sharesOf(uint256)',i,block=at)==shares and
                p._uint('vault','nftBucket(uint256)',i,block=at)==bucket and
                p._uint('royalties','weightOf(uint256)',i,block=at)==model.weights.get(i,0),
                'Checkpoint NFT rights differ from chain')
        financial=dict(previously_claimed={'assets':history.claimed(i,set(engine.descriptors))},
            lp_conversions=conversion_report(history.lp_conversions,i,engine.descriptors,{}),
            royalty_conversions=conversion_report(history.conversions,i,engine.descriptors,{}))
        account=SimpleNamespace(nft_id=i,totals=model.account_totals[i],scaled=model.accounts[i],
                                cohorts=model.cohorts,weights=model.weights)
        engine.check_paid(p,account,financial,at,lp,royalties)
    # Historical blocks need canonical/depth checks, not the live UI max-age rule.
    require(p._header(hex(number))==header,'Checkpoint anchor changed during construction')
    final=confirmed_head(p)
    require(number<=final['number'],'Checkpoint confirmation depth retreated')
    engine.finish_checkpoint()
    state=dict(shared={name:getattr(model,name) for name in SHARED},
        accounts=model.accounts,
        collection={k:v for k,v in model.totals.items() if k[0] in COLLECTION},
        emitters=emitters,lp_assets=sorted(lp),royalty_assets=sorted(royalties),
        history=dict(owners=dict(history.owners),claims=dict(history.claims),
            conversions={k:(*v[:3],dict(v[3])) for k,v in history.conversions.items()},
            lp_conversions={k:(*v[:3],dict(v[3])) for k,v in history.lp_conversions.items()},
            provenance=dict(history.provenance)))
    encoded=encode(state)
    # Apply the reader's exact grammar/node/depth limits before publication.
    # Successful economic replay alone must not produce an unreadable artifact.
    Checkpoint._validate(decode(encoded),header,engine)
    require(source_identity()==sources, 'Checkpoint semantic source changed during construction')
    payload=dict(schema=1,sources=sources,identity=encode(bound),anchor=encode(header),
                 state=encoded,previous_sha256=None if engine.checkpoint is None else engine.checkpoint.digest)
    raw=(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
    require(len(raw)<=MAX_BYTES,'Checkpoint exceeds the reviewed artifact size bound')
    return raw


def confirmed_head(p):
    # A historical construction is not a live user quote. Use fresh head/depth
    # checks without installing the HTTP UI snapshot expiry on this offline job.
    # The explicit build budget (or any stricter outer budget) still applies.
    from frontend_api.service import _quantity
    require(p.rpc.call('eth_chainId',[])==p.chain, 'Checkpoint RPC chain changed')
    safe=_quantity(p.rpc.call('eth_blockNumber',[]))-p.confirmations+1
    require(safe>=p.start and p._header(hex(p.start))['hash']==p.start_hash,
            'Checkpoint deployment anchor/depth changed')
    header=p._header(hex(safe))
    require(header['number']==safe, 'Checkpoint confirmed header is misnumbered')
    p._fresh(header)
    return header


def publish_candidate(path, raw):
    """Atomic exclusive hard-link publication; an existing artifact is never replaced."""
    target=Path(path)
    fd,name=tempfile.mkstemp(prefix='.'+target.name+'.',suffix='.partial',dir=target.parent)
    temporary=Path(name)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        os.link(temporary,target)  # Atomic create-if-absent on supported filesystems.
        if hasattr(os,'O_DIRECTORY'):
            directory=os.open(target.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(raw).hexdigest()
