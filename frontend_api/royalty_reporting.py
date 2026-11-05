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
        if type(config['schema']) is not int or config['schema'] not in (1, 2, 3, 4, 5):
            raise ValueError('Unsupported royalty reporting profile')
        self.schema = config['schema']
        if self.schema == 5 and projection.accounting_version != 6:
            raise ValueError('Exact royalty reporting requires accounting6/canonicalV8')
        if self.schema == 2 and config['converter'] is None:
            raise ValueError('Governed converter reporting requires an explicit runtime pin')
        if self.schema >= 3 and config['converter'] is not None:
            raise ValueError('Original-currency royalties have no converter')
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
        if self.schema >= 3:
            if p._uint('royalties','ROYALTY_SETTLEMENT_VERSION()',block=block) != (4 if self.schema == 5 else 3 if self.schema == 4 else 2):
                raise ProjectionError('Original-currency royalty capability mismatch')
            return {'address':None,'available':True,'enabled':False,
                    'reason':'original_currency_settlement','next_execution_at':None,
                    'scope':'Royalties are claimed in their received currency; no swap or unwrap.'}
        # Ledger getter failures are a wrong-profile/core failure, not a token outage.
        bound = p._addr('royalties', 'converter()', block=block, native=True)
        result = {'address': None if bound == ZERO else bound, 'available': False,
                  'enabled': None, 'reason': None, 'next_execution_at': None,
                  'scope': 'Binding, enable control and configured execution-loss policy only; routes, prices, gas and keeper timing are not qualified by this read.'}
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
            raw = p._call(bound, 'MAX_LOSS_BPS()', block=block)
            if len(raw) != 1:
                raise ProjectionError('Converter execution limit ABI mismatch')
            ceiling = int(raw[0], 16)
            loss = ceiling
            if self.schema == 2:
                raw = p._call(bound, 'conversionLossBps()', block=block)
                if len(raw) != 1:
                    raise ProjectionError('Converter operating limit ABI mismatch')
                loss = int(raw[0], 16)
            if ceiling != (1000 if self.schema == 2 else 100) or not 0 <= loss <= ceiling:
                raise ProjectionError('Converter execution limit mismatch')
            enabled = _bool(p._call(bound, 'enabled()', block=block)[0])
        except WorkLimit:
            raise
        except RpcError:
            result['reason'] = 'converter_verification_unavailable'
            return result
        result.update(available=True, enabled=enabled, maximum_execution_loss_bps=loss, gas_separate=True)
        if self.schema == 2:
            result.update(hard_maximum_execution_loss_bps=ceiling, loss_policy='governed')
        return result

    def opening(self, block, timestamp):
        from frontend_api.service import ProjectionError, _bool
        end = self.p._uint('royalties', 'mintEnd()', block=block)
        deadline = self.p._uint('royalties', 'royaltiesOpenAt()', block=block)
        opened = _bool(self.p._call(self.p.contracts['royalties'].address, 'royaltiesOpen()', block=block)[0])
        if end >= 2**64 or deadline != (end+3600 if end else 0) or (opened and not end):
            raise ProjectionError('Royalty opening configuration mismatch')
        if type(timestamp) is not int or timestamp < 0 or opened != bool(end and timestamp >= deadline):
            raise ProjectionError('Royalty opening state differs from confirmed timestamp')
        return {'configured':bool(end), 'mint_end':end or None, 'claims_open_at':deadline or None,
                'claims_open':opened, 'activation_window_seconds':3600,
                'status':'open' if opened else 'locked' if end else 'unconfigured'}

    def read(self, token_id, weight, assets, health, block, *, timestamp=None):
        from frontend_api.service import ZERO, ProjectionError, _bool
        p = self.p
        converter = self._converter(block)
        opening = self.opening(block, timestamp) if self.schema >= 4 else None
        if p._addr('royalties', 'canonicalController()', block=block) != p.contracts['access'].address:
            raise ProjectionError('Royalty ledger controller mismatch')
        total = p._uint('royalties', 'activationCount()', block=block)
        ordinal = p._uint('royalties', 'activationOrdinal(uint256)', token_id, block=block)
        if total > 1000 or ordinal > total or (ordinal != 0) != (weight != 0):
            raise ProjectionError('Royalty activation ordinal mismatch')
        ticket_start = None
        if self.schema == 5:
            ticket_start = p._uint('royalties', 'ticketStart(uint256)', token_id, block=block)
            total_weight = p._uint('royalties', 'totalWeight()', block=block)
            if (not total <= total_weight <= 3*total or
                    (weight == 0 and ticket_start != 0) or
                    (weight != 0 and (not ordinal <= ticket_start <= 3*(ordinal-1)+1 or ticket_start+weight-1 > total_weight))):
                raise ProjectionError('Exact royalty ticket identity mismatch')
        balances = []
        for asset in assets:
            count = p._uint('royalties', ('effectiveEligibleCount(address)' if self.schema >= 4 else 'eligibleCount(address)'), asset, block=block)
            eligible = _bool(p._call(p.contracts['royalties'].address,
                'eligibleFor(uint256,address)', token_id, asset, block=block)[0])
            if count > total or eligible != (ordinal != 0 and ordinal <= count):
                raise ProjectionError('Inconsistent royalty currency eligibility')
            if asset == ZERO and count != total:
                if self.schema >= 3:
                    raise ProjectionError('Original-currency native eligibility mismatch')
                if p.accounting_version in (4,5,6):
                    # There is no native-token read fault or external custody
                    # path in this fresh ledger. Never invoke removed selectors.
                    raise ProjectionError('Inconsistent native royalty eligibility')
                # ETH has no optional-token read failure. A native prefix may
                # lag only after an authenticated custody exit; it can still lag
                # after full return until the next sync enrolls waiting NFTs.
                # Older pinned ledgers without this getter remain fail-closed.
                nonce = p._uint('royalties', 'custodyNonce(address)', ZERO, block=block)
                native_weight = p._uint('royalties', 'eligibleWeight(address)', ZERO, block=block)
                total_weight = p._uint('royalties', 'totalWeight()', block=block)
                waiting = total-count
                waiting_weight = total_weight-native_weight
                if (nonce == 0 or not count <= native_weight <= 3*count or
                        not total <= total_weight <= 3*total or native_weight > total_weight or
                        not waiting <= waiting_weight <= 3*waiting):
                    raise ProjectionError('Inconsistent native royalty custody eligibility')
                if weight != 0:
                    cohort_count, cohort_weight = (count, native_weight) if eligible else (waiting, waiting_weight)
                    if cohort_count == 0 or not cohort_count-1 <= cohort_weight-weight <= 3*(cohort_count-1):
                        raise ProjectionError('NFT weight differs from native royalty custody cohort')
            item = self.balance('royalties', token_id, asset, health, block)
            if opening is not None and not opening['claims_open'] and item['available'] and int(item['raw']) != 0:
                raise ProjectionError('Locked royalty window reports spendable rewards')
            if weight == 0 and item['available'] and int(item['raw']) != 0:
                raise ProjectionError('Inactive NFT has royalty entitlement')
            if asset == ZERO and weight != 0 and not eligible and item['available'] and int(item['raw']) != 0:
                raise ProjectionError('Deferred native royalty entitlement predates eligibility')
            item.update(eligible=eligible, eligibility='inactive' if not weight else 'eligible' if eligible else 'deferred',
                        settlement_currency=('ETH' if asset == ZERO else 'source_asset'),
                        unconverted_raw=item['raw'] if asset != ZERO and self.schema < 3 else None)
            if self.schema >= 3:
                item.update(settlement_mode='original_currency',claim_asset=asset,conversion_required=False)
            if self.schema == 5:
                supply = p._uint('royalties', 'eligibleWeight(address)', asset, block=block)
                cursor = p._uint('royalties', 'allocationCursor(address)', asset, block=block)
                if (supply == 0 and cursor != 0) or (supply != 0 and cursor >= supply):
                    raise ProjectionError('Exact royalty allocation cursor mismatch')
                item.update(allocation_cursor=cursor)
            balances.append(item)
        result = {'available': True, 'schema': self.schema, 'activation_ordinal': ordinal,
                'balances_complete': all(item['available'] for item in balances),
                'balances': balances, 'converter': converter,
                'opening': opening,
                'scope': ('Eligibility is per currency; deferred NFTs join only future receipts after recovery. '
                          'All royalties are claimed in their original currency; no conversion or unwrap.' if self.schema >= 3 else
                          'Eligibility is per currency; deferred NFTs join only future receipts after recovery. Non-ETH balances may be converted or claimed directly; they are not queued ETH payments.')}
        if self.schema == 5:
            result.update(allocation_method='whole_unit_rotating_tickets', ticket_start=ticket_start)
        return result
