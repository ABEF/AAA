"""Explicit opt-in for the current royalty ledger's currency-isolated views.

Core deployment/identity/lifecycle checks remain strict. Only per-asset balance
or token-metadata failures may become unavailable fields; work limits still abort.
This module does not prepare claims, quote swaps or schedule keeper transactions.
"""
from zzz_ops.abi import address
from zzz_ops.errors import RpcError, WorkLimit


class Reporting:
    def __init__(self, config, projection):
        from frontend_api.service import Contract, _hash, _keys
        _keys(config, {'schema', 'converter'}, 'royalty_reporting')
        if type(config['schema']) is not int or config['schema'] != 1:
            raise ValueError('Unsupported royalty reporting profile')
        self.p = projection
        self.converter = None
        if config['converter'] is not None:
            _keys(config['converter'], {'address', 'code_hash'}, 'royalty converter')
            self.converter = Contract(address(config['converter']['address']), _hash(config['converter']['code_hash']))
            if self.converter.address in projection.assets or self.converter.address in {c.address for c in projection.contracts.values()}:
                raise ValueError('Royalty converter collides with another configured address')

    def balance(self, role, token_id, asset, health, block):
        p = self.p; descriptor = p.assets[asset]
        result = {'asset': asset, 'symbol': descriptor.symbol, 'decimals': descriptor.decimals,
                  'available': False, 'raw': None, 'asset_verified': health[asset], 'reason': None}
        if not health[asset]:
            result['reason'] = 'asset_verification_unavailable'
            return result
        try:
            result['raw'] = str(p._uint(role, 'claimable(uint256,address)', token_id, asset, block=block))
        except WorkLimit:
            raise
        except RpcError:
            result['reason'] = 'claimable_view_unavailable'
            return result
        result['available'] = True
        return result

    def _converter(self, block):
        from frontend_api.service import ZERO, ProjectionError, _address_word, _bool
        p = self.p
        # Ledger getter failures are a wrong-profile/core failure, not a token outage.
        bound = p._addr('royalties', 'converter()', block=block, native=True)
        result = {'address': None if bound == ZERO else bound, 'available': False,
                  'enabled': None, 'reason': None, 'next_execution_at': None,
                  'scope': 'Binding and enable control only; routes, prices, gas and keeper timing are not qualified by this read.'}
        if bound == ZERO:
            result['reason'] = 'converter_not_bound'
            return result
        if self.converter is None or bound != self.converter.address:
            result['reason'] = 'converter_pin_missing_or_mismatched'
            return result
        try:
            p._code(bound, self.converter.code_hash, block)
            for sig, expected in (('ledger()', p.contracts['royalties'].address),
                                  ('access()', p.contracts['access'].address)):
                if _address_word(p._call(bound, sig, block=block)[0]) != expected:
                    raise ProjectionError('Converter binding mismatch')
            loss = int(p._call(bound, 'MAX_LOSS_BPS()', block=block)[0], 16)
            if loss != 100:
                raise ProjectionError('Converter execution limit mismatch')
            enabled = _bool(p._call(bound, 'enabled()', block=block)[0])
        except WorkLimit:
            raise
        except RpcError:
            result['reason'] = 'converter_verification_unavailable'
            return result
        result.update(available=True, enabled=enabled, maximum_execution_loss_bps=loss, gas_separate=True)
        return result

    def read(self, token_id, weight, assets, health, block):
        from frontend_api.service import ZERO, ProjectionError, _bool
        p = self.p
        if p._addr('royalties', 'canonicalController()', block=block) != p.contracts['access'].address:
            raise ProjectionError('Royalty ledger controller mismatch')
        total = p._uint('royalties', 'activationCount()', block=block)
        ordinal = p._uint('royalties', 'activationOrdinal(uint256)', token_id, block=block)
        if total > 1000 or ordinal > total or (ordinal != 0) != (weight != 0):
            raise ProjectionError('Royalty activation ordinal mismatch')
        balances = []
        for asset in assets:
            count = p._uint('royalties', 'eligibleCount(address)', asset, block=block)
            eligible = _bool(p._call(p.contracts['royalties'].address,
                'eligibleFor(uint256,address)', token_id, asset, block=block)[0])
            if count > total or eligible != (ordinal != 0 and ordinal <= count) or (asset == ZERO and count != total):
                raise ProjectionError('Inconsistent royalty currency eligibility')
            item = self.balance('royalties', token_id, asset, health, block)
            if weight == 0 and item['available'] and int(item['raw']) != 0:
                raise ProjectionError('Inactive NFT has royalty entitlement')
            item.update(eligible=eligible, eligibility='inactive' if not weight else 'eligible' if eligible else 'deferred',
                        settlement_currency='ETH' if asset == ZERO else 'source_asset',
                        unconverted_raw=item['raw'] if asset != ZERO else None)
            balances.append(item)
        return {'available': True, 'schema': 1, 'activation_ordinal': ordinal,
                'balances_complete': all(item['available'] for item in balances),
                'balances': balances, 'converter': self._converter(block),
                'scope': 'Eligibility is per currency; deferred NFTs join only future receipts after recovery. Non-ETH balances may be converted or claimed directly; they are not queued ETH payments.'}
