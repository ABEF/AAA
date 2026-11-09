"""Read exact same-block witnesses from a caller-owned disposable source9 fork.

No signing, submission, state override or persistent connection. This supplements
actual API/website DTOs; it does not replace their production admission checks.
"""
from __future__ import annotations

import base64
import json

from scripts.source9_rehearsal_deploy import _transport
from zzz_ops.abi import calldata, decode_words


def capture(rpc, inventory, token_ids, *, block_number=None):
    call = _transport(rpc)
    contracts, dependencies = inventory['contracts'], inventory['dependencies']
    if block_number is not None and (type(block_number) is not int or block_number < rpc.fork_block_number):
        raise ValueError('Historical witness needs an explicit local-fork block')
    head = call('eth_getBlockByNumber', ['latest' if block_number is None else hex(block_number), False])
    if head is None:
        raise ValueError('Witness block is unavailable')
    block = {'blockHash': head['hash'], 'requireCanonical': True}

    def read(target, signature, *args):
        return decode_words(call('eth_call', [{'to': target, 'data': calldata(signature, *args)}, block]))

    def number(target, signature, *args):
        result = read(target, signature, *args)
        if len(result) != 1:
            raise ValueError('Unexpected witness scalar ABI')
        return int(result[0], 16)

    def owner(target, identifier):
        result = read(target, 'ownerOf(uint256)', identifier)
        if len(result) != 1 or int(result[0][:24], 16):
            raise ValueError('Unexpected witness owner ABI')
        return '0x' + result[0][-40:]

    rows = []
    for identifier in token_ids:
        identifier = int(identifier)
        nft_owner = owner(contracts['nft'], identifier)
        bucket = number(contracts['vault'], 'nftBucket(uint256)', identifier)
        group = read(contracts['vault'], 'group(uint256)', bucket)
        if len(group) != 8:
            raise ValueError('Unexpected source9 Position ABI')
        main = int(group[1], 16)
        uri = read(contracts['nft'], 'tokenURI(uint256)', identifier)
        encoded = bytes.fromhex(''.join(uri))
        offset = int.from_bytes(encoded[:32])
        size = int.from_bytes(encoded[offset:offset + 32])
        value = encoded[offset + 32:offset + 32 + size].decode('utf-8')
        if not value.startswith('data:application/json;base64,'):
            raise ValueError('Unexpected actual metadata URI')
        metadata = json.loads(base64.b64decode(value.split(',', 1)[1], validate=True))
        row = dict(token_id=str(identifier), owner=nft_owner, bucket_id=str(bucket),
            shares_raw=str(number(contracts['vault'], 'sharesOf(uint256)', identifier)),
            contribution_usd_18=str(number(contracts['vault'], 'contributionUSD(uint256)', identifier)),
            group_words=group, main_id=str(main),
            last_rebalance=str(int(group[6], 16)), idle0=str(int(group[2], 16)), idle1=str(int(group[3], 16)),
            total_shares=str(number(contracts['vault'], 'bucketTotalShares(uint256)', bucket)),
            wallet_eth_wei=str(int(call('eth_getBalance', [nft_owner, block]), 16)),
            wallet_zzz_raw=str(number(dependencies['zzz'], 'balanceOf(address)', nft_owner)),
            entry_allowance_raw=str(number(dependencies['zzz'], 'allowance(address,address)', nft_owner, contracts['entry'])),
            current_lp_value_words=read(contracts['nft'], 'currentLPValue(uint256)', identifier), metadata=metadata)
        if main:
            row.update(main_ticks_words=read(contracts['liquidity'], 'ticks(uint256)', main),
                main_liquidity_raw=str(number(dependencies['position_manager'], 'getPositionLiquidity(uint256)', main)),
                main_owner=owner(dependencies['position_manager'], main),
                secondary_id=str(number(contracts['liquidity'], 'secondaryId(uint256)', main)),
                physical_amounts_words=read(contracts['liquidity'], 'portfolioAmounts(uint256)', main))
        rows.append(row)
    entry = dict(eth_wei=str(int(call('eth_getBalance', [contracts['entry'], block]), 16)),
        zzz_raw=str(number(dependencies['zzz'], 'balanceOf(address)', contracts['entry'])))
    final = call('eth_getBlockByNumber', [head['number'], False])
    if final is None or final['hash'] != head['hash']:
        raise ValueError('Witness anchor was reorganized')
    return dict(schema=1, accounting_version=7, chain_id=4663, block_number=int(head['number'], 16),
        block_hash=head['hash'], block_timestamp=int(head['timestamp'], 16),
        entry=entry, rows=rows, simulation=False, public_transactions=False)
