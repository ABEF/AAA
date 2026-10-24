"""Exact dual-USD policy codec and bounded observation checks; no I/O or signing."""
from __future__ import annotations

import re
from zzz_ops.abi import keccak256

ZERO = '0x' + '00' * 20
ZERO_HASH = '0x' + '00' * 32
DOMAIN = '0x' + keccak256(b'ZZZ_DUAL_USD_V2').hex()
SOURCE_FIELDS = ('source', 'expectedCodeHash', 'independenceId', 'maxAge', 'feedDecimals')
POLICY_KEYS = frozenset(('token', 'primary', 'secondary', 'maxDeviationBps', 'assetDecimals', 'reviewHash'))


def number(value, minimum=0, maximum=(1 << 256) - 1):
    if type(value) is int:
        result = value
    elif isinstance(value, str) and re.fullmatch(r'0|[1-9][0-9]{0,77}', value):
        result = int(value)
    else:
        raise ValueError('Invalid dual-price integer')
    if not minimum <= result <= maximum:
        raise ValueError('Dual-price integer outside bounds')
    return result


def digest(value, length=32, zero=False):
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{'+str(length*2)+'}', value):
        raise ValueError('Invalid dual-price identity')
    result = value.lower()
    if not zero and int(result, 16) == 0:
        raise ValueError('Empty dual-price identity')
    return result


def source(value):
    if not isinstance(value, dict) or set(value) != set(SOURCE_FIELDS):
        raise ValueError('Unexpected dual-price source fields')
    return {'source': digest(value['source'], 20),
        'expectedCodeHash': digest(value['expectedCodeHash']),
        'independenceId': digest(value['independenceId']),
        'maxAge': number(value['maxAge'], 1, 86400),
        'feedDecimals': number(value['feedDecimals'], 0, 18)}


def policy(value, asset, decimals):
    if not isinstance(value, dict) or set(value) != POLICY_KEYS:
        raise ValueError('Unexpected dual-price policy fields')
    result = {'token': digest(value['token'], 20, zero=True),
        'primary': source(value['primary']), 'secondary': source(value['secondary']),
        'maxDeviationBps': number(value['maxDeviationBps'], 0, 500),
        'assetDecimals': number(value['assetDecimals'], 0, 18),
        'reviewHash': digest(value['reviewHash'])}
    if result['token'] != digest(asset, 20, zero=True) or result['assetDecimals'] != decimals:
        raise ValueError('Dual-price asset identity differs')
    if result['primary']['source'] == result['secondary']['source'] or result['primary']['independenceId'] == result['secondary']['independenceId']:
        raise ValueError('Dual-price sources are repeated or correlated by policy')
    return result


def flat(value):
    return [value['token']] + [value[role][key] for role in ('primary', 'secondary') for key in SOURCE_FIELDS] + [value['maxDeviationBps'], value['assetDecimals'], value['reviewHash']]


def words(values):
    result=[]
    for value in values:
        if isinstance(value,str) and re.fullmatch(r'0x[0-9a-fA-F]{1,64}',value):
            value=int(value,16)
        if type(value) is not int or not -(1 << 255) <= value < 1 << 256:
            raise ValueError('Invalid exact dual-price ABI word')
        result.append(f'{value % (1 << 256):064x}')
    return result


def hash_words(values):
    return '0x' + keccak256(bytes.fromhex(''.join(words(values)))).hex()


def policy_id(oracle, ordinal, value):
    return hash_words([digest(oracle,20), number(ordinal)] + flat(value))


def record(value, asset, decimals, oracle=None):
    if not isinstance(value, dict) or set(value) != {'policy_id', 'ordinal', 'policy'}:
        raise ValueError('Unexpected dual-price record fields')
    result = {'policy_id': digest(value['policy_id']), 'ordinal': number(value['ordinal']),
        'policy': policy(value['policy'], asset, decimals)}
    if oracle is not None and result['policy_id'] != policy_id(oracle, result['ordinal'], result['policy']):
        raise ValueError('Dual-price append-only identity differs')
    return result


def round_data(values, config, timestamp=None):
    if len(values) != 5:
        raise ValueError('Unexpected dual-price round ABI')
    items = [int(value, 16) for value in values]
    rid, answer, started, updated, answered = items
    if answer >= 1 << 255:
        answer -= 1 << 256
    if not 0 < rid < 1 << 80 or not rid <= answered < 1 << 80 or not 0 < answer <= 10**36 or not 0 < started <= updated:
        raise ValueError('Invalid dual-price source round')
    if timestamp is not None and (updated > timestamp or timestamp - updated > config['maxAge']):
        raise ValueError('Stale or future dual-price source round')
    normalized = answer * 10 ** (18 - config['feedDecimals'])
    if normalized > 10**36:
        raise ValueError('Dual-price normalized value exceeds bound')
    return normalized, {'round_id':rid, 'answer':answer, 'started_at':started,
        'updated_at':updated, 'answered_in_round':answered}


def observe(read, code, oracle, asset, decimals, approved, chain_id, sequencer_policy, timestamp=None):
    """Read callbacks are supplied by the caller and must share one canonical block."""
    if type(timestamp) is not int or timestamp <= 0:
        raise ValueError('A confirmed dual-price timestamp is required')
    approved = record(approved, asset, decimals, oracle)
    value = approved['policy']; identifier = approved['policy_id']; ordinal = approved['ordinal']
    if int(read(oracle,'PRICING_VERSION()')[0],16) != 2:
        raise ValueError('Dual-price implementation version differs')
    actual_id = '0x'+read(oracle,'activePolicy(address)',asset)[0]
    count = int(read(oracle,'policyCount()')[0],16)
    ordinal_id = '0x'+read(oracle,'policyAt(uint256)',ordinal)[0]
    if actual_id != identifier or count <= ordinal or ordinal_id != identifier:
        raise ValueError('Active dual-price policy differs')
    raw_policy = read(oracle,'policy(bytes32)',identifier,count=14)
    if raw_policy != words(flat(value)):
        raise ValueError('Dual-price policy contents differ')
    rounds, prices, observations = [], [], []
    for role in ('primary','secondary'):
        item = value[role]
        code(item['source'], item['expectedCodeHash'])
        if int(read(item['source'],'decimals()')[0],16) != item['feedDecimals']:
            raise ValueError('Dual-price source precision differs')
        raw = read(item['source'],'latestRoundData()',count=5)
        price, observed = round_data(raw,item,timestamp)
        prices.append(price); rounds.extend(int(word,16) for word in raw)
        observations.append(observed)
    lower, upper = min(prices), max(prices)
    if upper-lower > lower*value['maxDeviationBps']//10000:
        raise ValueError('Dual-price sources disagree')
    fingerprint = hash_words([DOMAIN,number(chain_id,1),digest(oracle,20),identifier,
        digest(sequencer_policy,zero=True)] + rounds)
    actual = read(oracle,'priceBounds(address)',asset,count=3)
    if actual != words([lower,upper,fingerprint]):
        raise ValueError('Dual-price bounds or fingerprint differ')
    return {'lower':lower,'upper':upper,'fingerprint':fingerprint,'policy_id':identifier,
        'policy_count':count,'ordinal_id':ordinal_id,'sources':observations}
