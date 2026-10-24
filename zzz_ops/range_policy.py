"""Strict, versioned Strategy range-policy metadata; no signing or RPC fallback."""
import re

from zzz_ops.abi import keccak256

ZERO_HASH = '0x' + '00' * 32
KEEPER_FIELDS = ('enabled', 'narrow_trigger_bps', 'widen_trigger_bps',
                 'minimum_interval_seconds', 'configuration_hash', 'review_hash')


def _number(value, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('Invalid bounded range-policy integer')
    return value


def _hash(value):
    if not isinstance(value, str) or len(value) != 66 or not value.startswith('0x'):
        raise ValueError('Invalid range-policy hash')
    try:
        if len(bytes.fromhex(value[2:])) != 32: raise ValueError()
    except ValueError as exc:
        raise ValueError('Invalid range-policy hash') from exc
    return value.lower()


def intended(value):
    if not isinstance(value, dict) or set(value) != {'orientation', 'keeper'}:
        raise ValueError('Explicit range orientation and keeper policy are required')
    orientation = _number(value['orientation'], 1)
    keeper = value['keeper']
    if not isinstance(keeper, dict) or set(keeper) != set(KEEPER_FIELDS) or type(keeper['enabled']) is not bool:
        raise ValueError('Invalid explicit keeper range policy')
    result = {'orientation': orientation, 'keeper': dict(keeper)}
    for key, maximum in (('narrow_trigger_bps',65535), ('widen_trigger_bps',65535),
                         ('minimum_interval_seconds',2**32-1)):
        result['keeper'][key] = _number(keeper[key], maximum)
    for key in ('configuration_hash', 'review_hash'):
        result['keeper'][key] = _hash(keeper[key])
    return result


def decode(orientation, policy, target):
    """Require canonical static ABI words, including uint widths and bool."""
    words = [orientation, *policy, target]
    if len(policy) != 7 or any(not isinstance(v,str) or re.fullmatch(r'[0-9a-fA-F]{64}',v) is None for v in words):
        raise ValueError('Malformed range-policy ABI')
    try:
        numbers = [int(v,16) for v in words]
    except ValueError as exc:
        raise ValueError('Malformed range-policy ABI') from exc
    mode, enabled, narrow, wide, interval, last, configuration, review, desired = numbers
    _number(mode,1); _number(enabled,1); _number(narrow,65535); _number(wide,65535)
    _number(interval,2**32-1); _number(last,2**64-1)
    if desired not in (0,2500,5000): raise ValueError('Invalid keeper range target')
    return {'orientation': mode, 'keeper': {'enabled': bool(enabled),
        'narrow_trigger_bps': narrow, 'widen_trigger_bps': wide,
        'minimum_interval_seconds': interval,
        'configuration_hash': '0x'+f'{configuration:064x}',
        'review_hash': '0x'+f'{review:064x}'},
        'last_change_at': last, 'target_half_width_bps': desired}


def observe(read, pool):
    version = read('RANGE_POLICY_VERSION()', count=1)
    if (len(version) != 1 or not isinstance(version[0],str) or
            re.fullmatch(r'[0-9a-fA-F]{64}',version[0]) is None or int(version[0],16) != 1):
        raise ValueError('Unsupported Strategy range-policy version')
    orientation = read('rangeOrientation(bytes32)', pool, count=1)
    target = read('keeperRangeTarget(bytes32)', pool, count=1)
    if len(orientation) != 1 or len(target) != 1:
        raise ValueError('Malformed Strategy range-policy scalar')
    return decode(orientation[0], read('keeperRangePolicy(bytes32)', pool, count=7), target[0])


def fingerprint(config_words, orientation):
    if len(config_words) != 14: raise ValueError('Invalid range-policy pool configuration')
    values = list(config_words)
    values[7] = '0' * 64
    return '0x'+keccak256(bytes.fromhex(''.join(values)+f'{orientation:064x}')).hex()


def verify(expected, observed, config_words, timestamp):
    expected = intended(expected)
    if not isinstance(observed,dict) or set(observed) != {'orientation','keeper','last_change_at','target_half_width_bps'}:
        raise ValueError('Invalid complete observed range-policy metadata')
    intended({key:observed[key] for key in ('orientation','keeper')})
    _number(observed['last_change_at'],2**64-1)
    target = _number(observed['target_half_width_bps'],5000)
    if target not in (0,2500,5000): raise ValueError('Invalid keeper range target')
    if any(expected[key] != observed[key] for key in ('orientation','keeper')):
        raise ValueError('Confirmed range policy differs from reviewed intent')
    keeper = observed['keeper']
    if observed['last_change_at'] > timestamp:
        raise ValueError('Keeper range checkpoint is in the future')
    matches = keeper['configuration_hash'] == fingerprint(config_words, observed['orientation'])
    if keeper['enabled']:
        if (observed['orientation'] != 1 or not 0 <= keeper['narrow_trigger_bps'] < keeper['widen_trigger_bps'] < 2500 or
                not 600 <= keeper['minimum_interval_seconds'] <= 604800 or
                keeper['minimum_interval_seconds'] < int(config_words[11],16) or
                int(config_words[7],16) not in (2500,5000) or keeper['configuration_hash'] == ZERO_HASH or
                keeper['review_hash'] == ZERO_HASH or observed['last_change_at'] == 0):
            raise ValueError('Invalid enabled keeper range policy')
    if observed['target_half_width_bps'] and (not keeper['enabled'] or not matches):
        raise ValueError('Disabled or stale keeper policy reports an executable range target')
    if target and (target == int(config_words[7],16) or
            observed['last_change_at'] + keeper['minimum_interval_seconds'] > timestamp):
        raise ValueError('Keeper target violates its direction or policy cooldown')
    return {**observed, 'configuration_matches': matches,
        'price_unit': 'token0_per_token1' if observed['orientation'] == 1 else 'token1_per_token0'}
