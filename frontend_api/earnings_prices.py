"""Optional current-snapshot USD marks from explicitly reviewed Oracle/feed pins."""
from frontend_api.history import ZERO
from zzz_ops.abi import address, keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.state import integer


class Prices:
    def __init__(self, config, projection, descriptors):
        from frontend_api.service import _keys, _hash
        _keys(config, {'oracle', 'sequencer', 'feeds'}, 'earnings prices')
        def contract(item):
            _keys(item, {'address', 'code_hash'}, 'earnings price contract')
            return address(item['address']), _hash(item['code_hash'])
        self.p, self.descriptors = projection, descriptors
        self.oracle = contract(config['oracle'])
        self.sequencer = None if config['sequencer'] is None else contract(config['sequencer'])
        if not isinstance(config['feeds'], list) or len(config['feeds']) > len(descriptors):
            raise ValueError('Unbounded earnings price feed inventory')
        self.feeds = {}
        for item in config['feeds']:
            _keys(item, {'asset', 'priced_token', 'token_code_hash', 'source', 'source_code_hash',
                         'max_age', 'feed_decimals'}, 'earnings price feed')
            asset = ZERO if item['asset'] == ZERO else address(item['asset'])
            token = address(item['priced_token'])
            if asset not in descriptors or asset in self.feeds or asset != ZERO and token != asset:
                raise ValueError('Unreviewed/repeated earnings price mapping')
            age = integer(item['max_age'], 'max_age', minimum=1)
            decimals = integer(item['feed_decimals'], 'feed_decimals')
            if age > 86400 or decimals > 18 or descriptors[asset].decimals > 18:
                raise ValueError('Unsupported earnings price precision/age')
            self.feeds[asset] = dict(item, asset=asset, priced_token=token, source=address(item['source']),
                token_code_hash=_hash(item['token_code_hash']), source_code_hash=_hash(item['source_code_hash']))

    def read(self, block):
        from frontend_api.service import _address_word, ProjectionError
        p = self.p
        result = {asset: {'available': False, 'usd_per_token_18': None, 'reason': 'price_not_configured'}
                  for asset in self.descriptors}
        try:
            oracle, code = self.oracle
            p._code(oracle, code, block)
            if (_address_word(p._call(oracle, 'access()', block=block)[0]) != p.contracts['access'].address or
                    p._addr('access', 'module(bytes32)', '0x'+keccak256(b'ZZZOracle').hex(), block=block) != oracle):
                raise ProjectionError('Earnings Oracle binding mismatch')
            seq = _address_word(p._call(oracle, 'sequencerFeed()', block=block)[0], native=True)
            if seq != (self.sequencer[0] if self.sequencer else ZERO):
                raise ProjectionError('Unreviewed sequencer change')
            if self.sequencer:
                p._code(*self.sequencer, block)
        except WorkLimit:
            raise
        except RpcError:
            for asset in self.feeds:
                result[asset]['reason'] = 'price_module_verification_unavailable'
            return result
        for asset, policy in self.feeds.items():
            try:
                words = p._call(oracle, 'feeds(address)', policy['priced_token'], block=block, words=4)
                actual = (_address_word(words[0]), *[int(w, 16) for w in words[1:]])
                expected = (policy['source'], policy['max_age'], policy['feed_decimals'], self.descriptors[asset].decimals)
                if actual != expected:
                    raise ProjectionError('Earnings feed policy changed')
                p._code(policy['source'], policy['source_code_hash'], block)
                p._code(policy['priced_token'], policy['token_code_hash'], block)
                value = int(p._call(oracle, 'price(address)', policy['priced_token'], block=block)[0], 16)
                if not 0 < value <= 10**36:
                    raise ProjectionError('Invalid earnings price')
                result[asset] = {'available': True, 'usd_per_token_18': str(value),
                    'priced_token': policy['priced_token'], 'oracle': oracle, 'source': policy['source'], 'reason': None}
            except WorkLimit:
                raise
            except RpcError:
                result[asset]['reason'] = 'price_unavailable_or_policy_changed'
        return result


def value_report(report, descriptors, prices):
    """All earned source amounts marked at today's confirmed price, not historic USD."""
    for period in ('all_time', 'last_24h'):
        totals, complete = {}, {}
        for row in report[period]:
            asset = row['asset']; price = prices[asset]
            row['current_price'] = price
            row['usd_at_current_price_18'] = {}
            for key, raw in list(row.items()):
                if not key.endswith('_raw'):
                    continue
                metric = key[:-4]
                value = (int(raw)*int(price['usd_per_token_18'])//10**descriptors[asset].decimals
                         if price['available'] else 0 if int(raw) == 0 else None)
                row['usd_at_current_price_18'][metric] = None if value is None else str(value)
                complete[metric] = complete.get(metric, True) and value is not None
                totals[metric] = totals.get(metric, 0) + (value or 0)
        report[period+'_usd_at_current_price_18'] = {key: str(value) if complete[key] else None for key, value in totals.items()}
    report['usd_valuation'] = 'Original earned currencies marked at the current confirmed snapshot; not historical USD, realized proceeds or current claimable value.'
    return report
