"""Explicit operator-reviewed activation configuration; no symbol-based admission."""
from __future__ import annotations

import hashlib
import json
import re

from frontend_api.service import Contract, ProjectionError, ZERO, _address_word, _bool, _hash, _keys
from zzz_ops.abi import address, calldata, keccak256
from zzz_ops.state import integer

ZERO_HASH = '0x' + '0' * 64
MODULES = {'pools': 'ZZZPoolRegistry', 'oracle': 'ZZZOracle', 'liquidity': 'ZZZLiquidityManager',
           'strategy': 'ZZZStrategy', 'fees': 'ZZZFeeController', 'membership': 'ZZZMembership',
           'migration': 'ZZZMigration'}
HELPERS = {'entry', 'activation_assets', 'budget'}


def bounded(items, maximum, label, minimum=0):
    if not isinstance(items, list) or not minimum <= len(items) <= maximum:
        raise ValueError('Invalid bounded ' + label)
    return items


def hex_bytes(value, maximum):
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value) or len(value) > 2 + 2 * maximum:
        raise ValueError('Invalid bounded hexadecimal value')
    return value.lower()


class ActivationConfig:
    def __init__(self, config, projection):
        _keys(config, {'schema', 'contracts', 'tokens', 'dependencies', 'sources', 'sequencer',
                       'call_pins', 'storage_pins', 'fee_policy'}, 'activation configuration')
        if type(config['schema']) is not int or config['schema'] != 1:
            raise ValueError('Unsupported activation configuration schema')
        _keys(config['contracts'], set(MODULES) | HELPERS, 'activation contracts')
        self.contracts = {}
        for role, item in config['contracts'].items():
            _keys(item, {'address', 'code_hash'}, 'activation contract')
            self.contracts[role] = Contract(address(item['address']), _hash(item['code_hash']))
        addresses = [c.address for c in self.contracts.values()] + [c.address for c in projection.contracts.values()]
        if len(addresses) != len(set(addresses)):
            raise ValueError('Activation protocol bindings must have distinct addresses')
        self.tokens = {}
        for token in bounded(config['tokens'], 32, 'token inventory', 2):
            _keys(token, {'address', 'code_hash', 'decimals', 'feed', 'feed_code_hash',
                          'feed_decimals', 'max_age'}, 'activation token')
            token = dict(token)
            token['address'] = address(token['address']); token['feed'] = address(token['feed'])
            for key in ('code_hash', 'feed_code_hash'): token[key] = _hash(token[key])
            for key in ('decimals', 'feed_decimals'):
                if integer(token[key], key) > 18: raise ValueError('Unsupported token/feed decimals')
            if not 1 <= integer(token['max_age'], 'feed max age') <= 86400:
                raise ValueError('Unsupported feed age')
            if token['address'] in self.tokens or token['address'] in addresses or token['feed'] in addresses:
                raise ValueError('Repeated token or protocol/dependency collision')
            self.tokens[token['address']] = token
        self.dependencies = {}
        for item in bounded(config['dependencies'], 64, 'dependency inventory', 1):
            _keys(item, {'address', 'code_hash'}, 'dependency')
            target = address(item['address'])
            if target in self.dependencies or target in addresses or target in self.tokens:
                raise ValueError('Repeated or colliding dependency')
            self.dependencies[target] = _hash(item['code_hash'])
        self.sources = {}
        for item in bounded(config['sources'], 64, 'source routes', 1):
            _keys(item, {'pool_id', 'source_asset', 'route_id', 'asset_policy_id'}, 'source route')
            pool = _hash(item['pool_id'])
            source = ZERO if item['source_asset'] == ZERO else address(item['source_asset'])
            route = ZERO_HASH if item['route_id'] == ZERO_HASH else _hash(item['route_id'])
            if (pool, source) in self.sources or source != ZERO and source not in self.tokens or source == ZERO and route != ZERO_HASH:
                raise ValueError('Ambiguous or unsupported source route')
            self.sources[(pool, source)] = (route, _hash(item['asset_policy_id']))
        _keys(config['sequencer'], {'address', 'policy_id'}, 'sequencer')
        self.sequencer = dict(config['sequencer'])
        if self.sequencer['address'] == ZERO:
            if self.sequencer['policy_id'] != ZERO_HASH: raise ValueError('Invalid absent sequencer policy')
        else:
            self.sequencer['address'] = address(self.sequencer['address'])
            self.sequencer['policy_id'] = _hash(self.sequencer['policy_id'])
            if self.sequencer['address'] not in self.dependencies: raise ValueError('Sequencer code pin is required')
        allowed = set(addresses) | set(self.tokens) | set(self.dependencies) | {t['feed'] for t in self.tokens.values()}
        self.call_pins = []
        for item in bounded(config['call_pins'], 128, 'call pins'):
            _keys(item, {'target', 'data', 'expected'}, 'call pin')
            pin = (address(item['target']), hex_bytes(item['data'], 1024), hex_bytes(item['expected'], 4096))
            if pin[0] not in allowed or len(pin[1]) < 10: raise ValueError('Unpinned call target or selector')
            self.call_pins.append(pin)
        self.storage_pins = []
        for item in bounded(config['storage_pins'], 64, 'storage pins'):
            _keys(item, {'target', 'slot', 'expected'}, 'storage pin')
            pin = (address(item['target']), _hash(item['slot']), hex_bytes(item['expected'], 32))
            if pin[0] not in allowed or len(pin[2]) != 66: raise ValueError('Invalid pinned storage word')
            self.storage_pins.append(pin)
        fee = config['fee_policy']; _keys(fee, {'estimate_includes_all_fees', 'review_hash', 'max_gas_price_wei'}, 'fee policy')
        if fee['estimate_includes_all_fees'] is not True:
            raise ValueError('Network fee semantics must be explicitly reviewed; no fee omission fallback')
        self.fee_review = _hash(fee['review_hash'])
        if not isinstance(fee['max_gas_price_wei'], str) or not re.fullmatch(r'[1-9][0-9]{0,19}', fee['max_gas_price_wei']):
            raise ValueError('A bounded reviewed gas price ceiling is required')
        self.max_gas_price = int(fee['max_gas_price_wei'])
        self.identity = hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',', ':')).encode()).hexdigest()

    def verify(self, p, block, used_tokens):
        """All reads use the parent's one confirmed canonical hash."""
        pins = {role: c.address for role, c in {**p.contracts, **self.contracts}.items()}
        def read(role, signature, *args, count=1):
            return p._call(pins[role], signature, *args, block=block, words=count)
        for role, contract in self.contracts.items():
            p._code(contract.address, contract.code_hash, block)
            if _address_word(read(role, 'access()')[0]) != pins['access']:
                raise ProjectionError('Activation controller binding changed')
            if role in MODULES and _address_word(read('access', 'module(bytes32)', '0x'+keccak256(MODULES[role].encode()).hex())[0]) != contract.address:
                raise ProjectionError('Activation module differs from sealed binding')
        bindings = [('pools', 'activationEntry()', 'entry'), ('pools','activationAssets()','activation_assets'),
                    ('entry','registry()','pools'), ('entry','activationAssets()','activation_assets'),
                    ('activation_assets','registry()','pools'), ('vault','migrationBudget()','budget'),
                    ('budget','vault()','vault')]
        for role, method, expected in bindings:
            if _address_word(read(role,method)[0]) != pins[expected]: raise ProjectionError('Activation helper binding changed')
        for target, digest in self.dependencies.items(): p._code(target, digest, block)
        for method, label in (('positionManager()','position_manager'), ('poolManager()','pool_manager'),
                              ('stateView()','state_view'), ('permit2()','permit2')):
            value = _address_word(read('liquidity',method)[0])
            if value not in self.dependencies: raise ProjectionError('Unreviewed liquidity venue dependency')
            pins[label] = value
        for role, method, expected in (('position_manager','poolManager()','pool_manager'),
                                       ('position_manager','permit2()','permit2'),('state_view','poolManager()','pool_manager')):
            if _address_word(read(role,method)[0]) != pins[expected]: raise ProjectionError('Liquidity venue binding changed')
        if (_address_word(read('oracle','sequencerFeed()')[0],native=True) != self.sequencer['address'] or
                '0x'+read('oracle','activeSequencerPolicy()')[0] != self.sequencer['policy_id']):
            raise ProjectionError('Reviewed sequencer policy changed')
        prices = {}
        for target in set(used_tokens):
            if target not in self.tokens: raise ProjectionError('Input/pool currency is not reviewed')
            t = self.tokens[target]
            p._code(target,t['code_hash'],block); p._code(t['feed'],t['feed_code_hash'],block)
            if int(p._call(target,'decimals()',block=block)[0],16) != t['decimals']:
                raise ProjectionError('Token decimals changed')
            feed = read('oracle','feeds(address)',target,count=4)
            if (_address_word(feed[0]) != t['feed'] or [int(x,16) for x in feed[1:]] != [t['max_age'],t['feed_decimals'],t['decimals']] or
                    int(p._call(t['feed'],'decimals()',block=block)[0],16) != t['feed_decimals']):
                raise ProjectionError('Price configuration differs from reviewed feed')
            price = int(read('oracle','price(address)',target)[0],16)
            if not 0 < price <= 10**36: raise ProjectionError('Invalid governed oracle price')
            prices[target] = price
        for target, data, expected in self.call_pins:
            if p.rpc.call('eth_call',[{'to':target,'data':data},block]) != expected:
                raise ProjectionError('Reviewed dependency getter changed')
        for target, slot, expected in self.storage_pins:
            if p.rpc.call('eth_getStorageAt',[target,slot,block]) != expected:
                raise ProjectionError('Reviewed proxy/storage pin changed')
        return pins, prices
