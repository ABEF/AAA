from zzz_ops.position import status_name
"""Read-only collection chunks, pinned to one complete ownership inventory.

LP is read from NFT.currentLPValue, including attributed idle/compound. Chunk
totals are never advertised as a collection total. No historical fee inference.
"""
import hashlib

from frontend_api.history import HistoryError
from frontend_api.service import ProjectionError, STATUS, EVOLUTION, _bool
from frontend_api.portfolio import CHUNK_SIZE
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import expire_at, checkpoint


def read(p, block_number, offset):
    if type(block_number) is not int or type(offset) is not int or not 0 <= offset < 1000 or offset % CHUNK_SIZE:
        raise ValueError('Invalid collection cursor')
    if p.history is None:
        raise HistoryError('Complete indexed ownership is required')
    safe, head, _ = p._snapshot()
    if not p.start <= block_number <= safe['number']:
        raise ProjectionError('Collection block is not confirmed')
    header = p._header(hex(block_number))
    p._fresh(header)
    expire_at(header['timestamp'] + p.max_age, p.clock)
    block = {'blockHash': header['hash'], 'requireCanonical': True}
    life = p._verify_deployment(block)
    lp, royalties = p._admitted(block, asset_health={})
    history = p._history_snapshot(header, block, lp, royalties)
    ids = sorted(history.owners)
    count = p._uint('nft', 'mintedCount()', block=block)
    if count != len(ids) or count > 1000:
        raise HistoryError('Collection inventory differs from canonical minted count')
    if offset >= count and not (offset == count == 0):
        raise ValueError('Cursor is outside collection inventory')
    rows, total, active, all_available = [], 0, 0, True
    for identifier in ids[offset:offset + CHUNK_SIZE]:
        checkpoint()
        ordinal = p._uint('nft', 'mintOrdinalOf(uint256)', identifier, block=block)
        owner = p._addr('nft', 'ownerOf(uint256)', identifier, block=block)
        if not 1 <= ordinal <= count or p._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=block) != identifier or owner != history.owners[identifier]:
            raise HistoryError('Collection ownership or mint identity differs from chain')
        ready = _bool(p._call(p.contracts['nft'].address, 'traitsReady(uint256)', identifier, block=block)[0])
        traits = None
        if ready:
            rarity, palette, pattern = (p._uint('nft', name + '(uint256)', identifier, block=block)
                                       for name in ('rarityOf', 'paletteOf', 'patternOf'))
            if rarity > 2 or palette > 57 or pattern > 3:
                raise ProjectionError('Unreviewed artwork traits')
            traits = dict(rarity=('Commun', 'Rare', 'Legendary')[rarity], palette=palette, pattern=pattern)
        status = p._uint('vault', 'nftStatus(uint256)', identifier, block=block)
        bucket = p._uint('vault', 'nftBucket(uint256)', identifier, block=block)
        shares = p._uint('vault', 'sharesOf(uint256)', identifier, block=block)
        weight = p._uint('royalties', 'weightOf(uint256)', identifier, block=block)
        if not 1 <= status < (5 if p.accounting_version == 3 else len(STATUS)) or weight > 3 or (weight > 0) != (shares > 0) or (shares > 0) != (bucket > 0) or (status == p.dormant_status) != (weight == 0):
            raise ProjectionError('Collection activation state differs')
        if weight and (not ready or weight != rarity + 1):
            raise ProjectionError('Collection royalty weight differs from rarity')
        try:
            value = p._call(p.contracts['nft'].address, 'currentLPValue(uint256)', identifier, block=block, words=2)
            available, amount = _bool(value[0]), int(value[1], 16)
        except (WorkLimit, ProjectionError):
            raise
        except RpcError:
            if not weight:
                raise
            available, amount = False, 0
        if (not available and amount) or (status not in (1, p.dormant_status) and available) or (status == p.dormant_status and (not available or amount)):
            raise ProjectionError('Collection LP valuation contradicts custody')
        stage = 0 if not weight else 3 if available and amount >= 10000 * 10**18 else 2 if available and amount >= 1000 * 10**18 else 1
        active += bool(weight)
        total += amount
        all_available = all_available and available
        rows.append(dict(token_id=str(identifier), mint_ordinal=ordinal, owner=owner, traits_ready=ready, traits=traits,
            position=dict(status=status_name(p.accounting_version,status), activated=bool(weight), royalty_weight=weight,
                principal_redeemable=False, current_lp_value=dict(available=available, raw=str(amount) if available else None,
                decimals=18, unit='USD', source='NFT.currentLPValue'), evolution=EVOLUTION[stage], evolution_value_available=available)))
    p._finish(header)
    return dict(schema=1, chain_id=p.chain, nft_contract=p.contracts['nft'].address, available=True,
        count=count, inventory_sha256=hashlib.sha256(','.join(map(str, ids)).encode('ascii')).hexdigest(),
        inventory_token_ids=list(map(str, ids)) if offset == 0 else None,
        offset=offset, chunk_size=CHUNK_SIZE, positions=rows,
        next_offset=offset + len(rows) if offset + len(rows) < count else None,
        chunk_lp_usd_18=str(total) if all_available else None, chunk_activated=active,
        lifecycle=life, provenance=dict(block_number=header['number'], block_hash=header['hash'],
            block_timestamp=header['timestamp'], observed_head=head, confirmations=p.confirmations,
            configuration_sha256=p.identity, finality='confirmation_depth_only'),
        scope='Chunk only. All inventory chunks at the same block are required for total attached LP. '
              'Activated counts eligibility, including parked/externally held NFTs. Missing valuation is not zero.')
