"""Bounded wallet totals at one canonical snapshot, independent of card pagination.

Clients must collect every ordered chunk of this inventory before displaying a
total. No rolling latest-state sum, balance cache, signing or partial total.
"""
import hashlib
from frontend_api.service import ProjectionError, ZERO, _bool
from frontend_api.history import HistoryError
from zzz_ops.abi import address
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import expire_at

CHUNK_SIZE=16


def read(p, wallet_address, block_number, offset):
    wallet=address(wallet_address)
    if type(block_number) is not int or type(offset) is not int or not 0<=offset<1000 or offset%CHUNK_SIZE:
        raise ValueError('Invalid wallet summary cursor')
    if p.history is None:raise HistoryError('Complete indexed ownership is required')
    safe,head,_=p._snapshot()
    if not p.start<=block_number<=safe['number']:raise ProjectionError('Summary block is not confirmed')
    header=p._header(hex(block_number));p._fresh(header)
    expire_at(header['timestamp']+p.max_age,p.clock)
    block={'blockHash':header['hash'],'requireCanonical':True}
    life=p._verify_deployment(block)
    # Currency failure must not fabricate a total, nor block unrelated ETH reads.
    lp,royalties=p._admitted(block,asset_health={})
    history=p._history_snapshot(header,block,lp,royalties)
    ids=sorted(i for i,owner in history.owners.items() if owner==wallet)
    count=p._uint('nft','balanceOf(address)',wallet,block=block)
    if count!=len(ids) or count>1000:raise HistoryError('Wallet inventory differs from canonical balance')
    if offset>=count and not (offset==0 and count==0):raise ValueError('Cursor is outside wallet inventory')
    selected=ids[offset:offset+CHUNK_SIZE]
    total_lp=0;total_eth=0;lp_ok=True;eth_ok=ZERO in lp and ZERO in royalties
    for identifier in selected:
        if p._addr('nft','ownerOf(uint256)',identifier,block=block)!=wallet:
            raise HistoryError('Wallet ownership differs from indexed snapshot')
        # In the fixed current ledger, weight zero means this NFT has never
        # activated; eligibility is permanent. Read actual views anyway so an
        # unavailable or contradictory response is never replaced with zero.
        inactive=False
        if p.accounting_version==3:
            weight=p._uint('royalties','weightOf(uint256)',identifier,block=block)
            if weight>3:raise ProjectionError('Wallet NFT royalty weight exceeds the reviewed bound')
            inactive=weight==0
        # Keep each metric independent: unreadable LP never becomes a zero sum.
        try:
            value=p._call(p.contracts['nft'].address,'currentLPValue(uint256)',identifier,block=block,words=2)
            available=_bool(value[0]);amount=int(value[1],16)
            if not available and amount:raise ProjectionError('Unavailable LP contains a value')
            if inactive and available and amount:raise ProjectionError('Inactive NFT has attached LP value')
            lp_ok=lp_ok and available;total_lp+=amount
        except (WorkLimit,ProjectionError):raise
        except RpcError:lp_ok=False
        if eth_ok:
            try:
                amount=sum(p._uint(role,'claimable(uint256,address)',identifier,ZERO,block=block)
                           for role in ('rewards','royalties'))
                if inactive and amount:raise ProjectionError('Inactive NFT has native reward entitlement')
                total_eth+=amount
            except (WorkLimit,ProjectionError):raise
            except RpcError:eth_ok=False
    p._finish(header)
    digest=hashlib.sha256(','.join(map(str,ids)).encode('ascii')).hexdigest()
    return dict(schema=1,chain_id=p.chain,wallet=wallet,nft_contract=p.contracts['nft'].address,
        inventory_sha256=digest,count=count,offset=offset,token_ids=list(map(str,selected)),
        next_offset=offset+len(selected) if offset+len(selected)<count else None,chunk_size=CHUNK_SIZE,
        lp_usd_18=str(total_lp) if lp_ok else None,claimable_eth_wei=str(total_eth) if eth_ok else None,
        lifecycle=life,provenance=dict(block_number=header['number'],block_hash=header['hash'],
            block_timestamp=header['timestamp'],observed_head=head,confirmations=p.confirmations,
            configuration_sha256=p.identity,finality='confirmation_depth_only'),
        scope='Chunk only. Sum all chunks of the same inventory and block before displaying wallet totals. '
              'ETH is funded LP plus royalties; unconverted source currencies and historical earnings are excluded.')
