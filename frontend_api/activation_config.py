"""Explicit operator-reviewed activation configuration; no symbol-based admission."""
from __future__ import annotations

import hashlib
import json
import re

from frontend_api.service import Contract, ProjectionError, ZERO, _address_word, _bool, _hash, _keys
from zzz_ops.abi import address, calldata, keccak256
from zzz_ops.state import integer

ZERO_HASH = '0x' + '0' * 64
NATIVE_ASSET_CODE_HASH = '0x' + keccak256(b'ZZZ_NATIVE_ETH_V1').hex()
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
        fields = {'schema', 'contracts', 'tokens', 'dependencies', 'sources', 'sequencer',
                  'call_pins', 'storage_pins', 'fee_policy'}
        self.pricing_version = config.get('pricing_version', 1)
        if type(self.pricing_version) is not int or self.pricing_version not in (1, 2):
            raise ValueError('Unsupported explicit activation pricing profile')
        if 'pricing_version' in config: fields.add('pricing_version')
        self.routing_version = config.get('routing_version', 1)
        if type(self.routing_version) is not int or self.routing_version not in (1, 2):
            raise ValueError('Unsupported explicit activation routing profile')
        if 'routing_version' in config: fields.add('routing_version')
        self.review_policy_version = config.get('review_policy_version', 0)
        if type(self.review_policy_version) is not int or self.review_policy_version not in (0,1):
            raise ValueError('Unsupported explicit activation review-policy profile')
        if 'review_policy_version' in config: fields.add('review_policy_version')
        if self.pricing_version == 2 and self.review_policy_version != 1:
            raise ValueError('Dual-price activation preparation requires explicit review_policy_version 1; update the reviewed Entry/Pricing bindings')
        if self.review_policy_version == 1 and self.pricing_version != 2:
            raise ValueError('Reviewed Entry requires explicit dual pricing version 2')
        self.range_policy_version = config.get('range_policy_version', 0)
        if type(self.range_policy_version) is not int or self.range_policy_version not in (0,1):
            raise ValueError('Unsupported explicit activation range-policy profile')
        if 'range_policy_version' in config: fields.add('range_policy_version')
        if self.range_policy_version == 1: fields.add('range_policies')
        _keys(config, fields, 'activation configuration')
        if type(config['schema']) is not int or config['schema'] != 1:
            raise ValueError('Unsupported activation configuration schema')
        if self.pricing_version == 2 and (self.routing_version != 2 or projection.accounting_version != 2):
            raise ValueError('Dual pricing requires explicit native accounting and typed routing profiles')
        if self.routing_version == 2 and projection.accounting_version != 2:
            raise ValueError('Typed routing requires native accounting version 2')
        _keys(config['contracts'], set(MODULES) | HELPERS |
              ({'v4_executor'} if self.routing_version == 2 else set()) |
              ({'contribution_pricing'} if self.pricing_version == 2 else set()), 'activation contracts')
        self.contracts = {}
        for role, item in config['contracts'].items():
            _keys(item, {'address', 'code_hash'}, 'activation contract')
            self.contracts[role] = Contract(address(item['address']), _hash(item['code_hash']))
        addresses = [c.address for c in self.contracts.values()] + [c.address for c in projection.contracts.values()]
        if len(addresses) != len(set(addresses)):
            raise ValueError('Activation protocol bindings must have distinct addresses')
        self.accounting_version = projection.accounting_version
        self.tokens = {}
        for token in bounded(config['tokens'], 33 if self.accounting_version == 2 else 32, 'token inventory', 2):
            _keys(token, {'address', 'code_hash', 'decimals'} | ({'price_policy'} if self.pricing_version == 2 else
                {'feed', 'feed_code_hash', 'feed_decimals', 'max_age'}), 'activation token')
            token = dict(token)
            native = self.accounting_version == 2 and token['address'] == ZERO
            token['address'] = ZERO if native else address(token['address'])
            if self.pricing_version == 1: token['feed'] = address(token['feed'])
            if native:
                if token['code_hash'] is not None or token['decimals'] != 18:
                    raise ValueError('Native ETH requires 18 decimals and no token runtime pin')
            else:
                token['code_hash'] = _hash(token['code_hash'])
            if self.pricing_version == 1: token['feed_code_hash'] = _hash(token['feed_code_hash'])
            for key in (('decimals', 'feed_decimals') if self.pricing_version == 1 else ('decimals',)):
                if integer(token[key], key) > 18: raise ValueError('Unsupported token/feed decimals')
            if self.pricing_version == 1 and not 1 <= integer(token['max_age'], 'feed max age') <= 86400:
                raise ValueError('Unsupported feed age')
            if self.pricing_version == 2:
                from zzz_ops.price_policy import record
                token['price_policy'] = record(token['price_policy'], token['address'], token['decimals'], self.contracts['oracle'].address)
                if any(token['price_policy']['policy'][role]['source'] in addresses for role in ('primary','secondary')):
                    raise ValueError('Price source collides with protocol contract')
            if token['address'] in self.tokens or token['address'] in addresses or self.pricing_version == 1 and token['feed'] in addresses:
                raise ValueError('Repeated token or protocol/dependency collision')
            self.tokens[token['address']] = token
        if len(set(self.tokens) - {ZERO}) > 32:
            raise ValueError('At most 32 ERC20 input currencies are supported')
        self.dependencies = {}
        for item in bounded(config['dependencies'], 64, 'dependency inventory', 1):
            _keys(item, {'address', 'code_hash'}, 'dependency')
            target = address(item['address'])
            if target in self.dependencies or target in addresses or target in self.tokens:
                raise ValueError('Repeated or colliding dependency')
            self.dependencies[target] = _hash(item['code_hash'])
        self.sources = {}
        self.route_kinds = {}
        for item in bounded(config['sources'], 64, 'source routes', 1):
            _keys(item, {'pool_id', 'source_asset', 'route_id', 'asset_policy_id'} |
                  ({'route_kind'} if self.routing_version == 2 else set()), 'source route')
            pool = _hash(item['pool_id'])
            source = ZERO if item['source_asset'] == ZERO else address(item['source_asset'])
            route = ZERO_HASH if item['route_id'] == ZERO_HASH else _hash(item['route_id'])
            kind = item['route_kind'] if self.routing_version == 2 else (0 if route == ZERO_HASH else 1)
            if type(kind) is not int or kind not in (0, 1, 2) or ((kind == 0) != (route == ZERO_HASH)):
                raise ValueError('Invalid explicit route kind')
            if ((pool, source) in self.sources or source != ZERO and source not in self.tokens or
                    source == ZERO and route != ZERO_HASH and kind != 2):
                raise ValueError('Ambiguous or unsupported source route')
            self.sources[(pool, source)] = (route, _hash(item['asset_policy_id']))
            self.route_kinds[(pool, source)] = kind
        self.fee_intake_version = getattr(projection, 'fee_intake_version', 0)
        self.zzz_input = None
        if self.fee_intake_version == 1:
            currencies = {source for _pool, source in self.sources}
            if ZERO not in currencies or len(currencies) != 2:
                raise ValueError('Current activation sources must contain only native ETH and one reviewed ZZZ identity')
            self.zzz_input = next(source for source in currencies if source != ZERO)
        self.range_policies = {}
        if self.range_policy_version == 1:
            from zzz_ops.range_policy import intended
            for item in bounded(config['range_policies'],16,'range policies',1):
                _keys(item, {'pool_id','orientation','keeper'}, 'range policy')
                pool = _hash(item['pool_id'])
                if pool in self.range_policies: raise ValueError('Repeated range-policy pool')
                self.range_policies[pool] = intended({key:item[key] for key in ('orientation','keeper')})
            if set(self.range_policies) != {pool for pool,_source in self.sources}:
                raise ValueError('Every reviewed activation pool needs its explicit range policy')
        _keys(config['sequencer'], {'address', 'policy_id'}, 'sequencer')
        self.sequencer = dict(config['sequencer'])
        if self.sequencer['address'] == ZERO:
            if self.sequencer['policy_id'] != ZERO_HASH: raise ValueError('Invalid absent sequencer policy')
        else:
            self.sequencer['address'] = address(self.sequencer['address'])
            self.sequencer['policy_id'] = _hash(self.sequencer['policy_id'])
            if self.sequencer['address'] not in self.dependencies: raise ValueError('Sequencer code pin is required')
        price_sources = ({t['feed'] for t in self.tokens.values()} if self.pricing_version == 1 else
            {t['price_policy']['policy'][role]['source'] for t in self.tokens.values() for role in ('primary','secondary')})
        allowed = set(addresses) | set(self.tokens) | set(self.dependencies) | price_sources
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

    def verify(self, p, block, used_tokens, *, include_bounds=False, timestamp=None):
        """All reads use the parent's one confirmed canonical hash."""
        pins = {role: c.address for role, c in {**p.contracts, **self.contracts}.items()}
        def read(role, signature, *args, count=1):
            return p._call(pins[role], signature, *args, block=block, words=count)
        for role, contract in self.contracts.items():
            p._code(contract.address, contract.code_hash, block)
            if role != 'v4_executor' and _address_word(read(role, 'access()')[0]) != pins['access']:
                raise ProjectionError('Activation controller binding changed')
            if role in MODULES and _address_word(read('access', 'module(bytes32)', '0x'+keccak256(MODULES[role].encode()).hex())[0]) != contract.address:
                raise ProjectionError('Activation module differs from sealed binding')
        bindings = [('pools', 'activationEntry()', 'entry'), ('pools','activationAssets()','activation_assets'),
                    ('entry','registry()','pools'), ('entry','activationAssets()','activation_assets'),
                    ('activation_assets','registry()','pools'), ('vault','migrationBudget()','budget'),
                    ('budget','vault()','vault')]
        if self.routing_version == 2:
            bindings += [('entry', 'v4Executor()', 'v4_executor'), ('v4_executor', 'parent()', 'entry')]
        for role, method, expected in bindings:
            if _address_word(read(role,method)[0]) != pins[expected]: raise ProjectionError('Activation helper binding changed')
        if self.fee_intake_version == 1:
            if int(read('activation_assets', 'SOURCE_POLICY_VERSION()')[0],16) != 1 or \
                    _address_word(read('activation_assets', 'zzz()')[0]) != self.zzz_input:
                raise ProjectionError('ETH/ZZZ contribution identity differs from the reviewed source policy')
            for token in {source for _pool, source in self.sources}:
                if not _bool(read('activation_assets', 'isContributionAsset(address)',token)[0]):
                    raise ProjectionError('Contribution currency is not admitted by the ETH/ZZZ-only policy')
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
        if self.pricing_version == 2:
            bindings += [('oracle','contributionPricing()','contribution_pricing'),('contribution_pricing','oracle()','oracle')]
            for role,method,expected in bindings[-2:]:
                if _address_word(read(role,method)[0]) != pins[expected]: raise ProjectionError('Contribution pricing helper binding differs')
            if _bool(read('contribution_pricing','active()')[0]): raise ProjectionError('Contribution pricing context is unexpectedly active')
        if self.review_policy_version == 1:
            for role,method in (('entry','REVIEW_POLICY_VERSION()'),('contribution_pricing','ENTRY_REVIEW_VERSION()')):
                if int(read(role,method)[0],16) != 1:
                    raise ProjectionError('Reviewed Entry/Pricing version is unsupported; no legacy fallback is permitted')
        prices = {}; bounds = {}
        for target in set(used_tokens):
            if target not in self.tokens: raise ProjectionError('Input/pool currency is not reviewed')
            t = self.tokens[target]
            if target != ZERO:
                p._code(target,t['code_hash'],block)
            if self.pricing_version == 1: p._code(t['feed'],t['feed_code_hash'],block)
            if target != ZERO and int(p._call(target,'decimals()',block=block)[0],16) != t['decimals']:
                raise ProjectionError('Token decimals changed')
            if self.pricing_version == 2:
                from zzz_ops.price_policy import observe
                def read_price(contract, method, *args, count=1):
                    return p._call(contract, method, *args, block=block, words=count)
                try:
                    observed = observe(read_price, lambda contract, digest: p._code(contract,digest,block),
                        pins['oracle'],target,t['decimals'],t['price_policy'],p.chain,self.sequencer['policy_id'],timestamp)
                except (ValueError, TypeError, KeyError) as exc:
                    raise ProjectionError('Dual-price policy or confirmed observation differs') from exc
                price = observed['lower']; bounds[target] = observed
            else:
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
        return (pins,prices,bounds) if include_bounds else (pins,prices)
