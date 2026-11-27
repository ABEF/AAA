"""Compact fixed-block ownership, totals and currency-paged NFT earnings.

Each request retains the normal work budget and live final proofs. All NFT and
currency pages are required before an earnings total is complete.
"""
from copy import deepcopy

from frontend_api.canonical_cache import scope
from frontend_api.earnings_replay import require
from frontend_api.history import HistoryError
from frontend_api.portfolio import CHUNK_SIZE, read as read_summary
from frontend_api.service import ProjectionError
from frontend_api.wallet_earnings import asset_page, read as read_earnings
from zzz_ops.abi import address
from zzz_ops.errors import RpcError, WorkLimit


def _same_page(ownership, earnings):
    for key in ('schema', 'chain_id', 'wallet', 'nft_contract', 'count', 'offset',
                'chunk_size', 'token_ids', 'next_offset', 'inventory_sha256', 'lifecycle'):
        require(ownership[key] == earnings[key], 'Compact wallet section identity differs')
    for key in ('block_number', 'block_hash', 'block_timestamp', 'configuration_sha256',
                'confirmations', 'finality'):
        require(ownership['provenance'][key] == earnings['provenance'][key],
                'Compact wallet section cutoff differs')
    history = ownership['history']
    current = earnings['provenance']['epochs'][-1]['history']
    for key in ('through_block', 'block_hash', 'minted_count', 'from_block',
                'start_block_hash', 'start_parent_hash'):
        require(history[key] == current[key], 'Compact wallet history identity differs')


def read(p, wallet_address, block_number, offset=0, asset_offset=0):
    wallet = address(wallet_address)
    if p.accounting_version != 7 or p.earnings_history is None:
        raise HistoryError('Compact wallet view requires exact LP and configured earnings history')
    if (type(block_number) is not int or type(offset) is not int or
            not 0 <= offset < 1000 or offset % CHUNK_SIZE):
        raise ValueError('Invalid compact wallet NFT cursor')
    engine = p.earnings_history
    assets = asset_page(engine, asset_offset)
    with scope([p]):
        # Summary already verifies every returned owner. Other currency slices
        # need only the existing ownership proof, with the same raw provenance.
        summary = (read_summary(p, wallet, block_number, offset, include_history=True)
                   if asset_offset == 0 else None)
        ownership = summary if summary is not None else p.wallet_page(wallet, block_number, offset)
        earnings = None
        earnings_error = None
        if getattr(p, 'wallet_read_batch', 0) == 1 and asset_offset == 0:
            # Explicit profile2 assembles this independent ownership/summary
            # axis first, then reads four-currency full-wallet aggregates.
            earnings_error = 'aggregate_earnings_required'
        else:
            try:
                earnings = read_earnings(engine, wallet, block_number, offset, asset_offset=asset_offset)
            except (WorkLimit, ProjectionError, HistoryError):
                raise
            except RpcError:
                # No partial earnings survives a transport failure. The independent
                # verified ownership/summary still needs fresh final proofs below.
                earnings_error = 'earnings_unavailable'
        if earnings is not None:
            _same_page(ownership, earnings)
            for key, value in assets.items():
                require(earnings[key] == value, 'Compact wallet currency cursor differs')
            require(earnings['provenance']['epochs'][-1]['controller'] == p.contracts['access'].address,
                    'Compact wallet current earnings controller differs')
        provenance = ownership['provenance']
        history = ownership['history']
        require(history['available'] is True and history['through_block'] == block_number and
                history['block_hash'] == provenance['block_hash'] and
                history['minted_count'] >= ownership['count'], 'Compact wallet ownership history differs')
        header = p._header(hex(block_number))
        require(header['hash'] == provenance['block_hash'] and
                header['timestamp'] == provenance['block_timestamp'], 'Compact wallet anchor changed')
        engine.finish_checkpoint()
        p._finish(header)
        result = {key:deepcopy(ownership[key]) for key in
                  ('chain_id', 'wallet', 'nft_contract', 'count', 'offset', 'chunk_size',
                   'token_ids', 'next_offset', 'inventory_sha256', 'lifecycle', 'history', 'provenance')}
        result['provenance'].update(protocol_finalized=False, eip1898_require_canonical=True,
                                    accounting_version=p.accounting_version)
        result.update(schema=1, kind='fixed_block_wallet_view_page', available=True,
            verified_count=len(ownership['token_ids']),
            complete=offset == 0 and len(ownership['token_ids']) == ownership['count'],
            **assets, summary=summary, earnings=earnings, earnings_error=earnings_error,
            scope='Ownership is verified only for the returned NFT IDs. Collect every ordered NFT page '
                  'at this inventory and block for complete ownership and totals; collect every NFT and '
                  'currency page before displaying complete earnings. ETH claimable remains ETH-only.')
        return result
