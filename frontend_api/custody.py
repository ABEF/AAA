"""Canonical per-NFT custody checks shared by detail and bounded inventories.

The cache is supplied by one request at one pinned block. It contains only raw
bucket rows and denominators, never a value, permission or cross-request result.
"""
from frontend_api.service import ProjectionError
from zzz_ops.position import decode_position, is_local_position


def read(p, status, bucket, shares, block, *, cache=None, totals=None):
    exited = p.accounting_version in (4, 5, 6) and status == 5
    if status not in (1, p.parked_status) and not exited:
        return None
    if cache is not None and bucket in cache:
        group, decoded, supply = cache[bucket]
    else:
        group = p._position(bucket, block)
        decoded = decode_position(group, p.accounting_version)
        supply = p._uint('vault', 'bucketTotalShares(uint256)', bucket, block=block)
        if cache is not None:
            cache[bucket] = group, decoded, supply
    if (int(group[0], 16) == 0 or (int(group[1], 16) == 0) != (status != 1) or
            int(group[7], 16) != status or
            not is_local_position(decoded, p.accounting_version, p.chain, p.contracts['vault'].address) or
            supply < shares or (exited and (int(group[2], 16) or int(group[3], 16)))):
        raise ProjectionError('Local principal differs from its canonical custody state')
    if totals is not None:
        partial = totals.get(bucket, 0) + shares
        if partial > supply:
            raise ProjectionError('Inventory shares exceed the canonical bucket denominator')
        totals[bucket] = partial
    return {'pool_id': '0x' + group[0],
            'lp_token_id': str(int(group[1], 16)) if status == 1 else None,
            'bucket_total_shares_raw': str(supply),
            'share_numerator_raw': str(shares), 'share_denominator_raw': str(supply),
            'last_rebalance_at': int(group[6], 16),
            'identity_source': 'Vault.group at the confirmed snapshot'}
