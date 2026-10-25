"""Bounded, read-only production inventory observations; never release approval.

Every state/code read uses one canonical EIP-1898 block hash. A supplied list of
routes is a declared list, not proof that no other route exists. Independent
creation-to-anchor history evidence remains necessary for completeness.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from zzz_ops.abi import decode_words, keccak256
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope

ZERO = '0x' + '00' * 20
ZERO_HASH = '0x' + '00' * 32
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_CODE_BYTES = 128 * 1024
MAX_GETTER_GAS = 1_000_000
READ_METHODS = frozenset(('eth_chainId', 'eth_getBlockByNumber', 'eth_getCode', 'eth_call'))
POOL_FIELDS = ('currency0', 'currency1', 'fee', 'tickSpacing', 'hooks', 'depositsEnabled',
               'operationsEnabled', 'rangeBps', 'triggerBps', 'maxSpotDeviationBps',
               'maxSlippageBps', 'minRebalanceInterval', 'minDepositUSD', 'maxPositionUSD')
V4_FIELDS = ('source', 'output', 'currency0', 'currency1', 'fee', 'tickSpacing', 'hooks',
             'poolManager', 'stateView', 'sourceCodeHash', 'outputCodeHash',
             'poolManagerCodeHash', 'stateViewCodeHash', 'reviewHash')
V3_ENTRY_FIELDS = ('source', 'output', 'router', 'factory', 'pool', 'fee', 'routerCodeHash',
                   'factoryCodeHash', 'poolCodeHash', 'sourceCodeHash', 'outputCodeHash', 'reviewHash')
V3_CONVERTER_FIELDS = ('source', 'router', 'factory', 'pool', 'fee', 'sourceCodeHash',
                       'routerCodeHash', 'factoryCodeHash', 'poolCodeHash', 'reviewHash')
ASSET_FIELDS = ('token', 'enabled', 'expectedCodeHash', 'reviewHash', 'decimals', 'poolAdmission')
ADDRESS_FIELDS = frozenset(('source','output','currency0','currency1','hooks','poolManager','stateView',
                           'router','factory','pool','token','admin','implementation','adminOwner'))
BOOLEAN_FIELDS = frozenset(('depositsEnabled','operationsEnabled','enabled','poolAdmission','bootstrapAdmission'))
MODULE_IDS = {
    'vault': 'ZZZVault', 'nft': 'ZZZNFT', 'liquidity': 'ZZZLiquidityManager',
    'rewards': 'ZZZRewards', 'membership': 'ZZZMembership', 'fees': 'ZZZFeeController',
    'strategy': 'ZZZStrategy', 'compounder': 'ZZZCompounder', 'buyback': 'ZZZBuyback',
    'migration': 'ZZZMigration', 'oracle': 'ZZZOracle', 'pools': 'ZZZPoolRegistry',
    'canonical': 'ZZZCanonicalHandoff', 'nft_canonical': 'ZZZNFTCanonical',
    'vault_canonical': 'ZZZVaultCanonical', 'fees_canonical': 'ZZZFeesCanonical',
    'bridge': 'ZZZBridgeAdapter', 'receiver': 'ZZZMigrationReceiver',
    'routes': 'ZZZMigrationRegistry', 'transport': 'ZZZBridgeRouter',
}
BOOL_GETTERS = frozenset(('isSealed', 'canonicalSettling', 'preparationActive',
                         'randomnessConfigured', 'nativePayment', 'enabled', 'paused', 'mintPaused', 'active'))
UINT_GETTERS = frozenset(('getMinDelay', 'canonicalState', 'ACCOUNTING_VERSION', 'canonicalChainId',
    'MAX_SUPPLY', 'subscriptionId', 'requestConfirmations', 'callbackGasLimit', 'outstandingCount',
    'maxTradeUSD', 'operatingTradeUSD', 'phase', 'originChain', 'MAX_LOSS_BPS',
    'contributionLossBps', 'maintenanceLossBps', 'MAX_CLAIMS', 'conversionLossBps',
    'rewardReceiverCount', 'custodyCount', 'PRICING_VERSION', 'RANGE_POLICY_VERSION',
    'REVIEW_POLICY_VERSION', 'ENTRY_REVIEW_VERSION'))
HASH_GETTERS = frozenset(('keyHash', 'zzzCodeHash', 'contributionPool', 'SCHEMA'))
ADDRESS_GETTERS = frozenset(('access', 'canonicalHandoff', 'bootstrap', 'royaltyFactory',
    'migrationBudget', 'mintProceedsRecipient', 'royaltyRewards', 'claimRouter', 'metadataRenderer',
    'randomnessCoordinator', 'positionManager', 'stateView', 'poolManager', 'permit2', 'converter',
    'receiverFactory', 'validation', 'currentZZZ', 'activationAssets', 'activationEntry', 'sequencerFeed',
    'zzz', 'incomingSource', 'nft', 'vault', 'originVault', 'fees', 'registry', 'v4Executor',
    'migration', 'canonicalController', 'royalties', 'controller', 'parent', 'ledger', 'wrapper',
    'factory', 'token0', 'token1', 'owner', 'oracle', 'contributionPricing'))


def _address(value: Any, *, native=False) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{40}', value):
        raise ValueError('Invalid public address')
    value = value.lower()
    if value == ZERO and not native:
        raise ValueError('Zero is not a contract address')
    return value


def _hash(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value) or int(value, 16) == 0:
        raise ValueError('Invalid nonzero hash')
    return value.lower()


def _quantity(value: Any) -> int:
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value):
        raise ValueError('Noncanonical RPC quantity')
    number = int(value, 16)
    if number >= 1 << 256:
        raise ValueError('Oversized RPC quantity')
    return number


def _uint(value: Any, maximum=(1 << 256)-1) -> int:
    if type(value) is int:
        number = value
    elif isinstance(value, str) and re.fullmatch(r'0|[1-9][0-9]{0,77}', value):
        number = int(value)
    else:
        raise ValueError('Invalid integer')
    if not 0 <= number <= maximum:
        raise ValueError('Integer exceeds bound')
    return number


def _chain_id(value):
    # Rpc.call deliberately returns a checked integer for eth_chainId; injected
    # transports may return the canonical wire quantity instead.
    return _uint(value, (1 << 64)-1) if type(value) is int else _quantity(value)


def _word(value: Any) -> str:
    if isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{40}|0x[0-9a-fA-F]{64}', value):
        return value[2:].lower().rjust(64, '0')
    return format(_uint(value), '064x')


def _decode(word: str, expected: Any) -> Any:
    number = int(word, 16)
    if type(expected) is bool:
        if number not in (0, 1):
            raise ValueError('Noncanonical ABI boolean')
        return bool(number)
    if isinstance(expected, str) and re.fullmatch(r'0x[0-9a-fA-F]{40}', expected):
        if number >= 1 << 160:
            raise ValueError('Noncanonical ABI address')
        return '0x' + word[-40:]
    if isinstance(expected, str) and re.fullmatch(r'0x[0-9a-fA-F]{64}', expected):
        return '0x' + word
    _uint(expected)
    return str(number) if isinstance(expected, str) else number


def _string(encoded: str) -> str:
    if not isinstance(encoded, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', encoded):
        raise ValueError('Malformed string ABI')
    raw = bytes.fromhex(encoded[2:])
    if len(raw) < 64 or len(raw) > 4160 or int.from_bytes(raw[:32], 'big') != 32:
        raise ValueError('Invalid string ABI offset or bound')
    length = int.from_bytes(raw[32:64], 'big')
    if length > 4096 or len(raw) != 64 + ((length + 31)//32)*32 or any(raw[64+length:]):
        raise ValueError('Invalid string ABI length/padding')
    return raw[64:64+length].decode('utf-8')


def _same(actual, expected):
    if type(expected) in (bool, int):
        return type(actual) is type(expected) and actual == expected
    if isinstance(expected, str) and expected.startswith('0x'):
        return isinstance(actual, str) and actual.lower() == expected.lower()
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(_same(actual[k],v) for k,v in expected.items())
    return actual == expected


def _normalized(fields, expected):
    return {key: expected[key].lower() if key in ADDRESS_FIELDS or key.endswith('CodeHash') or key in ('reviewHash','expectedCodeHash','codeHash')
            else expected[key] if key in BOOLEAN_FIELDS else _uint(expected[key]) for key in fields}


class Observer:
    def __init__(self, rpc, chain):
        self.rpc = BudgetedRPC(rpc)
        self.chain = chain
        self.errors = []
        self.block = None
        self.codes = {}

    def request(self, method, params):
        if method not in READ_METHODS:
            raise ValueError('Not a read-only observation method')
        return self.rpc.call(method, params)

    def header(self, tag):
        raw = self.request('eth_getBlockByNumber', [tag, False])
        if not isinstance(raw, dict):
            raise ValueError('Missing canonical block')
        result = {'number': _quantity(raw.get('number')), 'hash': _hash(raw.get('hash')),
                  'timestamp': _quantity(raw.get('timestamp'))}
        if tag != 'latest' and result['number'] != _quantity(tag):
            raise ValueError('Wrong block number')
        return result

    def anchor(self):
        chain_id = _uint(self.chain['chain_id'], (1 << 64)-1)
        if chain_id == 0 or _chain_id(self.request('eth_chainId', [])) != chain_id:
            raise ValueError('Wrong chain')
        anchor = self.chain['observed_block']
        number = _uint(anchor['number'], (1 << 64)-1)
        expected = _hash(anchor['hash'])
        genesis = self.header('0x0')
        if genesis['hash'] != _hash(self.chain['genesis_hash']):
            raise ValueError('Wrong genesis')
        self.head = self.header('latest')
        self.start = self.header(hex(number))
        confirmations = _uint(self.chain['minimum_confirmations'], 1024)
        if confirmations == 0 or self.start['hash'] != expected or self.head['number'] < number + confirmations:
            raise ValueError('Wrong canonical anchor')
        if 'timestamp' in anchor and _uint(anchor['timestamp']) != self.start['timestamp']:
            raise ValueError('Wrong anchor timestamp')
        self.block = {'blockHash': expected, 'requireCanonical': True}
        return chain_id, genesis['hash']

    def finish(self):
        if self.header(hex(self.start['number'])) != self.start or self.header('0x0')['hash'] != self.chain['genesis_hash'].lower():
            raise ValueError('Canonical anchor changed')
        if _chain_id(self.request('eth_chainId', [])) != self.chain['chain_id']:
            raise ValueError('Chain identity changed')

    def attempt(self, path, code, action):
        try:
            return action()
        except Exception:
            # Public paths/codes only; provider exceptions may contain credentials.
            self.errors.append({'path': path, 'code': code})
            return None

    def read(self, target, signature, *args, count=1):
        target = _address(target)
        if not (re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\((?:bytes32|address|uint256|uint8)?\)', signature) and len(args) <= 1 or
                signature == 'getPool(address,address,uint24)' and len(args) == 3 or
                signature == 'royaltyInfo(uint256,uint256)' and len(args) == 2 or
                signature == 'hasRole(bytes32,address)' and len(args) == 2):
            raise ValueError('Unsupported inventory getter')
        data = '0x' + keccak256(signature.encode()).hex()[:8] + ''.join(_word(a) for a in args)
        encoded = self.request('eth_call', [{'to': target, 'data': data, 'gas': hex(MAX_GETTER_GAS)}, self.block])
        if count == 'string':
            return _string(encoded)
        words = decode_words(encoded)
        if len(words) != count:
            raise ValueError('Wrong getter ABI length')
        return words

    def typed(self, target, getter, expected):
        # Decode types are code-owned even when an intended value is missing;
        # absent pins must not change which ABI is interpreted.
        if getter == 'artworkBaseURI':
            return self.read(target, getter+'()', count='string')
        if getter in BOOL_GETTERS:
            typ = False
        elif getter in ADDRESS_GETTERS:
            typ = ZERO
        elif getter in HASH_GETTERS:
            typ = ZERO_HASH
        elif getter in UINT_GETTERS:
            typ = '0' if isinstance(expected, str) and re.fullmatch(r'0|[1-9][0-9]*', expected) else 0
        else:
            raise ValueError('Unsupported binding getter')
        return _decode(self.read(target, getter+'()')[0], typ)

    def code(self, target):
        target = _address(target)
        if target not in self.codes:
            raw = self.request('eth_getCode', [target, self.block])
            if (not isinstance(raw, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', raw) or
                    len(raw) > 2 + MAX_CODE_BYTES*2):
                raise ValueError('Missing or oversized contract runtime')
            self.codes[target] = '0x' + keccak256(bytes.fromhex(raw[2:])).hex()
        return self.codes[target]

    def records(self, expected):
        for group in ('modules', 'helpers'):
            for role, record in self.chain[group].items():
                path = group+'.'+role
                actual = self.attempt(path, 'runtime.unavailable', lambda: self.code(record['address']))
                record['observed_runtime_hash'] = actual
                if actual is not None and not _same(actual, record.get('runtime_hash')):
                    self.errors.append({'path': path, 'code': 'runtime.mismatch'})
                record['observed_bindings'] = {}
                for getter, wanted in expected[group].get(role, {}).items():
                    value = self.attempt(path+'.'+getter, 'binding.unavailable',
                        lambda g=getter, w=wanted: self.typed(record['address'], g, w))
                    record['observed_bindings'][getter] = value
                    if value is not None and not _same(value, wanted):
                        self.errors.append({'path': path+'.'+getter, 'code': 'binding.mismatch'})
        access = self.chain['modules']['access']['address']
        self.chain['observed_modules'] = {}
        for role, identifier in MODULE_IDS.items():
            wanted = self.chain['modules'].get(role, {}).get('address', ZERO)
            value = self.attempt('observed_modules.'+role, 'module.unavailable', lambda i=identifier:
                _decode(self.read(access, 'module(bytes32)', '0x'+keccak256(i.encode()).hex())[0], ZERO))
            self.chain['observed_modules'][role] = value
            if value is not None and not _same(value, wanted):
                self.errors.append({'path': 'observed_modules.'+role, 'code': 'module.mismatch'})

    def dependencies(self):
        for role, record in self.chain['dependencies'].items():
            path = 'dependencies.'+role
            actual = self.attempt(path, 'runtime.unavailable', lambda: self.code(record['address']))
            record['observed_runtime_hash'] = actual
            if actual is not None and not _same(actual, record.get('runtime_hash')):
                self.errors.append({'path': path, 'code': 'runtime.mismatch'})
            record['observed_bindings'] = {}
            for getter, expected in record.get('bindings', {}).items():
                # Only the code-owned dependency graph may select getter names.
                if getter not in ('poolManager', 'permit2', 'factory'):
                    self.errors.append({'path': path, 'code': 'binding.unknown'})
                    continue
                value = self.attempt(path+'.'+getter, 'binding.unavailable',
                    lambda g=getter, w=expected: self.typed(record['address'], g, w))
                record['observed_bindings'][getter] = value
                if value is not None and not _same(value, expected):
                    self.errors.append({'path': path+'.'+getter, 'code': 'binding.mismatch'})

    def tokens(self):
        oracle = self.chain['modules']['oracle']['address']
        for index, token in enumerate(self.chain['tokens']):
            path = 'tokens.'+str(index)
            native = token['address'] == ZERO
            token['observed_runtime_hash'] = None if native else self.attempt(path, 'runtime.unavailable', lambda: self.code(token['address']))
            if not native and token['observed_runtime_hash'] is not None and not _same(token['observed_runtime_hash'], token.get('runtime_hash')):
                self.errors.append({'path': path, 'code': 'runtime.mismatch'})
            token['observed_decimals'] = 18 if native else self.attempt(path, 'decimals.unavailable',
                lambda: int(self.read(token['address'], 'decimals()')[0], 16))
            if token['observed_decimals'] != token.get('decimals'):
                self.errors.append({'path': path, 'code': 'decimals.mismatch'})
            if self.pricing_version == 2:
                self.dual_price(token,path,oracle)
                continue
            feed = token['feed']
            feed['observed_runtime_hash'] = self.attempt(path+'.feed', 'runtime.unavailable', lambda: self.code(feed['source']))
            if feed['observed_runtime_hash'] is not None and not _same(feed['observed_runtime_hash'], feed.get('runtime_hash')):
                self.errors.append({'path': path+'.feed', 'code': 'runtime.mismatch'})
            values = self.attempt(path+'.feed', 'feed.unavailable', lambda: self.read(feed['source'], 'latestRoundData()', count=5))
            for key in ('round_id', 'answer', 'updated_at', 'answered_in_round'):
                feed[key] = None
            if values is not None:
                round_id, answer, _started, updated, answered = map(lambda w: int(w, 16), values)
                answer = answer - (1 << 256) if answer >= 1 << 255 else answer
                if round_id >= 1 << 80 or answered >= 1 << 80:
                    self.errors.append({'path': path+'.feed', 'code': 'feed.noncanonical'})
                else:
                    feed.update(round_id=str(round_id), answer=str(answer), updated_at=updated, answered_in_round=str(answered))
            actual_decimals = self.attempt(path+'.feed', 'decimals.unavailable', lambda: int(self.read(feed['source'], 'decimals()')[0], 16))
            if actual_decimals != feed.get('decimals'):
                self.errors.append({'path': path+'.feed', 'code': 'decimals.mismatch'})
            wanted = {'source': feed['source'], 'maxAge': _uint(feed['maximum_age_seconds']),
                      'feedDecimals': _uint(feed['decimals']), 'assetDecimals': _uint(token['decimals'])}
            raw = self.attempt(path+'.feed', 'oracle_feed.unavailable', lambda: self.read(oracle, 'feeds(address)', token['address'], count=4))
            feed['observed_oracle_feed'] = None if raw is None else self.attempt(path+'.feed', 'oracle_feed.noncanonical',
                lambda: {key: _decode(value, wanted[key]) for key, value in zip(wanted, raw)})
            if feed['observed_oracle_feed'] is not None and not _same(feed['observed_oracle_feed'], wanted):
                self.errors.append({'path': path+'.feed', 'code': 'oracle_feed.mismatch'})

    def dual_price(self, token, path, oracle):
        from zzz_ops import price_policy as codec
        approved = token.get('price_policy')
        if not isinstance(approved,dict):
            self.errors.append({'path':path+'.price_policy','code':'pricing.policy_missing'})
            return
        # Failed reads must never retain copied healthy observations.
        for key in ('observed_pricing_version','observed_policy_id','observed_policy',
                    'observed_policy_count','observed_ordinal_id','observed_bounds'):
            approved[key] = None
        sources = approved.get('sources')
        if isinstance(sources,list):
            for observed in sources:
                if isinstance(observed,dict):
                    for key in ('observed_runtime_hash','decimals','round_id','answer','started_at','updated_at','answered_in_round'):
                        observed[key] = None
        def observe_price():
            record = {key:approved.get(key) for key in ('policy_id','ordinal','policy')}
            parsed = codec.record(record,token['address'],token['decimals'],oracle)
            def checked_code(target, expected):
                actual = self.code(target)
                if not _same(actual,expected): raise ValueError('Price source runtime differs')
            sequence = '0x'+self.read(oracle,'activeSequencerPolicy()')[0]
            observed = codec.observe(self.read,checked_code,oracle,token['address'],token['decimals'],
                parsed,self.chain['chain_id'],sequence,self.start['timestamp'])
            return parsed,observed
        result = self.attempt(path+'.price_policy','pricing.unavailable_or_changed',observe_price)
        if result is None: return
        parsed,observed = result
        approved.update(observed_pricing_version=2,observed_policy_id=observed['policy_id'],
            observed_policy=parsed['policy'],observed_policy_count=observed['policy_count'],
            observed_ordinal_id=observed['ordinal_id'],observed_bounds={key:observed[key] for key in ('lower','upper','fingerprint')})
        if not isinstance(sources,list) or len(sources)!=2:
            self.errors.append({'path':path+'.price_policy.sources','code':'pricing.source_inventory'})
            return
        for index,role in enumerate(('primary','secondary')):
            expected = parsed['policy'][role]; actual = sources[index]
            if not isinstance(actual,dict) or not _same(actual.get('source'),expected['source']) or not _same(actual.get('runtime_hash'),expected['expectedCodeHash']):
                self.errors.append({'path':path+'.price_policy.sources','code':'pricing.source_pin_mismatch'})
                continue
            actual.update(observed['sources'][index],observed_runtime_hash=expected['expectedCodeHash'],
                decimals=expected['feedDecimals'])

    def descriptor(self, target, signature, identifier, fields, expected):
        raw = self.read(target, signature, identifier, count=len(fields))
        return {key: _decode(value, ZERO if key in ADDRESS_FIELDS else False if key in BOOLEAN_FIELDS else
                            ZERO_HASH if key.endswith('CodeHash') or key in ('reviewHash','expectedCodeHash','codeHash') else 0)
                for key, value in zip(fields, raw)}

    def wrappers(self):
        fields = ('codeHash','admin','implementation','adminOwner','adminCodeHash','implementationCodeHash','reviewHash')
        for role in ('lp_converter','royalty_converter'):
            record = self.chain['helpers'][role]
            wrapper = record['bindings']['wrapper']
            if wrapper == ZERO:
                continue
            policy = record['wrapper_policy']
            path = 'helpers.'+role+'.wrapper_policy'
            def read_policy():
                raw = self.read(record['address'],'wrapperPolicy()',count=7)
                return {key:_decode(value,ZERO if key in ADDRESS_FIELDS else ZERO_HASH) for key,value in zip(fields,raw)}
            record['observed_wrapper_policy'] = self.attempt(path,'wrapper.unavailable',read_policy)
            if record['observed_wrapper_policy'] is not None and not _same(record['observed_wrapper_policy'],_normalized(fields,policy)):
                self.errors.append({'path':path,'code':'wrapper.mismatch'})
            actual = self.attempt(path,'runtime.unavailable',lambda:self.code(wrapper))
            if actual is not None and not _same(actual,policy['codeHash']):
                self.errors.append({'path':path,'code':'runtime.mismatch'})
            if policy['admin'] != ZERO:
                def admin_state():
                    admin = policy['admin']
                    return {'admin':_decode(self.read(admin,'getProxyAdmin(address)',wrapper)[0],ZERO),
                        'implementation':_decode(self.read(admin,'getProxyImplementation(address)',wrapper)[0],ZERO),
                        'adminOwner':self.typed(admin,'owner',ZERO)}
                record['wrapper_policy_observation'] = self.attempt(path,'wrapper_authority.unavailable',admin_state)
                for key, hash_key in (('admin','adminCodeHash'),('implementation','implementationCodeHash')):
                    runtime = self.attempt(path+'.'+key,'runtime.unavailable',lambda k=key:self.code(policy[k]))
                    if runtime is not None and not _same(runtime,policy[hash_key]):
                        self.errors.append({'path':path+'.'+key,'code':'runtime.mismatch'})

    def slot(self, state, pool):
        raw = self.read(state, 'getSlot0(bytes32)', pool, count=4)
        price, tick, protocol, fee = map(lambda w: int(w, 16), raw)
        tick = tick-(1 << 256) if tick >= 1 << 255 else tick
        if price >= 1 << 160 or not -(1 << 23) <= tick < 1 << 23 or protocol >= 1 << 24 or fee >= 1 << 24:
            raise ValueError('Noncanonical slot0 ABI')
        return dict(sqrt_price_x96=str(price), tick=tick, protocol_fee=protocol, lp_fee=fee)

    def liquidity(self, state, pool=None):
        raw = self.read(state, 'getLiquidity(bytes32)', pool)[0] if pool is not None else self.read(state, 'liquidity()')[0]
        value = int(raw, 16)
        if value >= 1 << 128:
            raise ValueError('Noncanonical liquidity ABI')
        return str(value)

    def pools(self):
        registry = self.chain['modules']['pools']['address']
        state = self.chain['dependencies']['state_view']['address']
        for index, pool in enumerate(self.chain['pools']):
            path = 'pools.'+str(index)
            pool['observed_config'] = self.attempt(path, 'pool.unavailable', lambda:
                self.descriptor(registry, 'get(bytes32)', pool['pool_id'], POOL_FIELDS, pool))
            raw = self.attempt(path, 'accounting.unavailable', lambda: self.read(registry, 'accounting(bytes32)', pool['pool_id'], count=14))
            pool['observed_accounting'] = None if raw is None else self.attempt(path, 'accounting.noncanonical', lambda:
                {'currency0': _decode(raw[0], ZERO), 'currency1': _decode(raw[1], ZERO)})
            pool['slot0'] = self.attempt(path, 'slot0.unavailable', lambda: self.slot(state, pool['pool_id']))
            pool['liquidity'] = self.attempt(path, 'liquidity.unavailable', lambda: self.liquidity(state, pool['pool_id']))
            wanted = _normalized(POOL_FIELDS,pool)
            if pool['observed_config'] is not None and any(not _same(pool['observed_config'][key], wanted[key]) for key in POOL_FIELDS):
                self.errors.append({'path': path, 'code': 'pool.mismatch'})
            if getattr(self,'range_policy_version',0) == 1:
                from zzz_ops.range_policy import observe
                strategy = self.chain['modules']['strategy']['address']
                pool['observed_range_policy'] = self.attempt(path+'.range_policy','range_policy.unavailable',lambda:
                    observe(lambda method,*args,count: self.read(strategy,method,*args,count=count),pool['pool_id']))

    def sequencer(self):
        sequence = self.chain['sequencer']
        if sequence['mode'] == 'not_applicable':
            return
        if sequence['mode'] != 'uptime_feed':
            raise ValueError('Unknown sequencer profile')
        path = 'sequencer'
        source = sequence['address']
        sequence['observed_runtime_hash'] = self.attempt(path,'runtime.unavailable',lambda:self.code(source))
        if sequence['observed_runtime_hash'] is not None and not _same(sequence['observed_runtime_hash'],sequence.get('runtime_hash')):
            self.errors.append({'path':path,'code':'runtime.mismatch'})
        for field in ('round_id','answer','started_at','updated_at','answered_in_round'):
            sequence[field] = None
        raw = self.attempt(path,'sequencer.unavailable',lambda:self.read(source,'latestRoundData()',count=5))
        if raw is not None:
            round_id, answer, start, updated, answered = (int(value,16) for value in raw)
            answer = answer-(1 << 256) if answer >= 1 << 255 else answer
            if round_id >= 1 << 80 or answered >= 1 << 80:
                self.errors.append({'path':path,'code':'sequencer.noncanonical'})
            else:
                sequence.update(round_id=str(round_id),answer=answer,started_at=start,updated_at=updated,answered_in_round=str(answered))
        sequence['observed_decimals'] = self.attempt(path,'decimals.unavailable',lambda:int(self.read(source,'decimals()')[0],16))
        if sequence['observed_decimals'] is not None and sequence['observed_decimals'] != 0:
            self.errors.append({'path':path,'code':'decimals.mismatch'})
        oracle = self.chain['modules']['oracle']['address']
        sequence['observed_active_policy_id'] = self.attempt(path,'sequencer_policy.unavailable',lambda:
            '0x'+self.read(oracle,'activeSequencerPolicy()')[0])
        fields = ('source','expectedCodeHash','reviewHash','bootstrapAdmission')
        sequence['observed_policy'] = self.attempt(path,'sequencer_policy.unavailable',lambda:
            self.descriptor(oracle,'sequencerPolicies(bytes32)',sequence['active_policy_id'],fields,sequence['policy']))
        if (sequence['observed_active_policy_id'] is not None and not _same(sequence['observed_active_policy_id'],sequence['active_policy_id']) or
                sequence['observed_policy'] is not None and not _same(sequence['observed_policy'],sequence['policy'])):
            self.errors.append({'path':path,'code':'sequencer_policy.mismatch'})

    def governance(self):
        governance = self.chain['governance']
        access = self.chain['modules']['access']['address']
        for key in ('proposers','executors'):
            if not isinstance(governance.get(key),list) or not 1 <= len(governance[key]) <= 64:
                raise ValueError('Unbounded governance role inventory')
        def has_role(role, account):
            identifier = ZERO_HASH if role == 'DEFAULT_ADMIN_ROLE' else '0x'+keccak256(role.encode()).hex()
            # Never trust a copied list to manufacture observed grants.
            return _decode(self.read(access,'hasRole(bytes32,address)',identifier,_address(account,native=True))[0],False)
        def granted(role, accounts):
            return [account for account in accounts if has_role(role,account)]
        observed = {}
        for key, role, accounts in (('proposers','PROPOSER_ROLE',governance['proposers']),
                ('executors','EXECUTOR_ROLE',governance['executors']),
                ('cancellers','CANCELLER_ROLE',governance['proposers'])):
            observed[key] = self.attempt('governance.'+key,'authority.unavailable',lambda r=role,a=accounts:granted(r,a))
            if observed[key] is not None and observed[key] != accounts:
                self.errors.append({'path':'governance.'+key,'code':'authority.mismatch'})
        for role, getter in (('keeper','keepers'),('guardian','guardians')):
            observed[role] = governance[role]
            observed[role+'_enabled'] = self.attempt('governance.'+role,'authority.unavailable',lambda g=getter,r=role:
                _decode(self.read(access,g+'(address)',governance[r])[0],False))
            if observed[role+'_enabled'] is not None and observed[role+'_enabled'] is not True:
                self.errors.append({'path':'governance.'+role,'code':'authority.mismatch'})
        observed['controller_admin'] = self.attempt('governance.controller_admin','authority.unavailable',lambda:
            has_role('DEFAULT_ADMIN_ROLE',access))
        if observed['controller_admin'] is not None and observed['controller_admin'] is not True:
            self.errors.append({'path':'governance.controller_admin','code':'authority.mismatch'})
        governance['observed_roles'] = observed

    def sources(self):
        assets = self.chain['helpers']['activation_assets']['address']
        for index, source in enumerate(self.chain['activation_sources']):
            path = 'activation_sources.'+str(index)
            source['observed_asset_policy'] = self.attempt(path, 'asset_policy.unavailable', lambda:
                self.descriptor(assets, 'policies(bytes32)', source['asset_policy_id'], ASSET_FIELDS, source['asset_policy']))
            source['observed_asset_policy_id'] = self.attempt(path, 'asset_policy.unavailable', lambda:
                '0x'+self.read(assets, 'activePolicy(address)', source['source_asset'])[0])
            source['observed_asset_policy_count'] = self.attempt(path, 'asset_policy.unavailable', lambda:
                int(self.read(assets, 'policyCount()')[0],16))
            source['observed_asset_policy_ordinal_id'] = self.attempt(path, 'asset_policy.unavailable', lambda:
                '0x'+self.read(assets, 'policyAt(uint256)', source['asset_policy_ordinal'])[0])
            if (source['observed_asset_policy'] is not None and not _same(source['observed_asset_policy'], _normalized(ASSET_FIELDS,source['asset_policy'])) or
                    source['observed_asset_policy_id'] is not None and not _same(source['observed_asset_policy_id'], source['asset_policy_id']) or
                    source['observed_asset_policy_ordinal_id'] is not None and not _same(source['observed_asset_policy_ordinal_id'], source['asset_policy_id'])):
                self.errors.append({'path': path, 'code': 'asset_policy.mismatch'})

    def ledgers(self):
        for name, inventory, ledger, maximum in (
                ('reward_assets', self.chain['reward_assets'], self.chain['modules']['rewards']['address'], 33),
                ('royalty_assets', self.chain['nft_inventory']['royalty_assets'], self.chain['helpers']['royalty_rewards']['address'], 17)):
            if not isinstance(inventory,dict) or not isinstance(inventory.get('assets'),list) or len(inventory['assets']) > maximum:
                raise ValueError('Unbounded ledger asset inventory')
            count = self.attempt(name, 'ledger_assets.unavailable', lambda: int(self.read(ledger,'assetCount()')[0],16))
            inventory['observed_asset_count'] = count
            if count is not None and (count > maximum or count != len(inventory['assets']) or count != inventory.get('asset_count')):
                self.errors.append({'path': name, 'code': 'ledger_assets.mismatch'})
            for index, record in enumerate(inventory['assets']):
                path = name+'.'+str(index)
                record['observed_asset'] = self.attempt(path, 'ledger_asset.unavailable', lambda:
                    _decode(self.read(ledger,'assets(uint256)',index)[0],ZERO))
                record['observed_is_asset'] = self.attempt(path, 'ledger_asset.unavailable', lambda:
                    _decode(self.read(ledger,'isAsset(address)',record['address'])[0],False))
                if (record['observed_asset'] is not None and not _same(record['observed_asset'],record['address']) or
                        record['observed_is_asset'] is not None and record['observed_is_asset'] is not True):
                    self.errors.append({'path': path, 'code': 'ledger_asset.mismatch'})
                if name == 'royalty_assets':
                    record['custody_amount'] = self.attempt(path, 'ledger_custody.unavailable', lambda:
                        str(int(self.read(ledger,'custodyAmount(address)',record['address'])[0],16)))

    def nft(self):
        inventory = self.chain['nft_inventory']
        nft = self.chain['modules']['nft']['address']
        observed = {}
        royalty = self.attempt('nft_inventory','nft.royalty_unavailable',lambda:
            self.read(nft,'royaltyInfo(uint256,uint256)',0,10000,count=2))
        observed['royaltyReceiver'] = None if royalty is None else self.attempt('nft_inventory','nft.royalty_noncanonical',lambda:
            _decode(royalty[0],ZERO))
        observed['royaltyBps'] = None if royalty is None else int(royalty[1],16)
        for getter in ('mintedCount','nextToFinalize','remainingToReveal'):
            observed[getter] = self.attempt('nft_inventory.'+getter,'nft.inventory_unavailable',lambda g=getter:
                int(self.read(nft,g+'()')[0],16))
        observed['rarityRemaining'] = self.attempt('nft_inventory.rarityRemaining','nft.inventory_unavailable',lambda:
            [int(self.read(nft,'rarityRemaining(uint256)',i)[0],16) for i in range(3)])
        inventory['observed_bindings'] = observed
        randomness = inventory['randomness']
        randomness['observed_runtime_hash'] = self.attempt('nft_inventory.randomness','runtime.unavailable',lambda:
            self.code(randomness['coordinator']))
        if randomness['observed_runtime_hash'] is not None and not _same(randomness['observed_runtime_hash'],randomness.get('runtime_hash')):
            self.errors.append({'path':'nft_inventory.randomness','code':'runtime.mismatch'})

    def route_venue(self, policy, kind, role):
        if kind == 2:
            raw = b''.join(bytes.fromhex(_word(policy[key])) for key in ('currency0','currency1','fee','tickSpacing','hooks'))
            pool_id = '0x'+keccak256(raw).hex()
            state, manager = policy['stateView'], policy['poolManager']
            actual = self.typed(state, 'poolManager', ZERO)
            if actual != manager:
                raise ValueError('Wrong v4 state binding')
            return {'pool_id': pool_id, 'slot0': self.slot(state, pool_id), 'liquidity': self.liquidity(state, pool_id),
                    'poolManager': actual, 'stateView': state}
        pool = policy['pool']
        factory = self.typed(pool, 'factory', ZERO)
        token0, token1 = (self.typed(pool, key, ZERO) for key in ('token0', 'token1'))
        fee = int(self.read(pool, 'fee()')[0], 16)
        if fee >= 1 << 24:
            raise ValueError('Noncanonical v3 fee ABI')
        factory_pool = _decode(self.read(policy['factory'], 'getPool(address,address,uint24)', token0, token1, fee)[0], ZERO)
        return {'factory': factory, 'token0': token0, 'token1': token1, 'fee': fee,
                'liquidity': self.liquidity(pool), 'pool_address': pool,
                'router_factory': self.typed(policy['router'], 'factory', ZERO), 'factory_pool': factory_pool}

    def routes(self):
        helpers = self.chain['helpers']
        for index, route in enumerate(self.chain['conversion_routes']):
            path = 'conversion_routes.'+str(index)
            role, kind, identifier = route['role'], route['route_kind'], route['route_id']
            parent_role = 'activation_entry' if role == 'entry' else role+'_converter'
            parent = helpers[parent_role]['address']
            route['observed_enabled'] = self.attempt(path, 'route.unavailable', lambda:
                _decode(self.read(parent, 'routeEnabled(bytes32)', identifier)[0], False))
            actual_kind = self.attempt(path, 'route.unavailable', lambda:
                int(self.read(parent, 'routeKind(bytes32)', identifier)[0], 16))
            route['observed_kind'] = actual_kind
            route['observed_exists'] = self.attempt(path,'route.unavailable',lambda:
                _decode(self.read(parent,'routeExists(bytes32)',identifier)[0],False))
            fields = V4_FIELDS if kind == 2 else V3_ENTRY_FIELDS if role == 'entry' else V3_CONVERTER_FIELDS
            route['observed_policy'] = self.attempt(path, 'route.unavailable', lambda:
                self.descriptor(parent, 'v4Route(bytes32)' if kind == 2 else 'route(bytes32)', identifier, fields, route['policy']))
            same = _same(route['observed_policy'], _normalized(fields,route['policy']))
            if (route['observed_exists'] is not None and route['observed_exists'] is not True or
                    actual_kind is not None and actual_kind != kind or
                    route['observed_enabled'] is not None and route['observed_enabled'] != route['enabled'] or
                    route['observed_policy'] is not None and not same):
                self.errors.append({'path': path, 'code': 'route.mismatch'})
            route['venue_observation'] = None
            if not same:
                continue
            if kind == 2:
                helper = helpers[role+'_v4_executor']['address']
                child = self.attempt(path, 'route_helper.unavailable', lambda:
                    self.descriptor(helper, 'route(bytes32)', identifier, fields, route['policy']))
                if not _same(child, route['observed_policy']):
                    self.errors.append({'path': path, 'code': 'route_helper.mismatch'})
                identity = keccak256(b'ZZZ_TYPED_V4_ROUTE_V1') + self.chain['chain_id'].to_bytes(32,'big') + bytes.fromhex(_word(helper)) + bytes.fromhex(_word(parent))
                identity += b''.join(bytes.fromhex(_word(route['policy'][key])) for key in fields)
                if not _same('0x'+keccak256(identity).hex(), identifier):
                    self.errors.append({'path': path, 'code': 'route.identity'})
                if route['observed_enabled'] is True:
                    valid = self.attempt(path, 'route_validation.unavailable', lambda:
                        self.descriptor(helper, 'validate(bytes32)', identifier, fields, route['policy']))
                    if not _same(valid, route['observed_policy']):
                        self.errors.append({'path': path, 'code': 'route_validation.mismatch'})
            else:
                identity = b''.join(bytes.fromhex(_word(route['policy'][key])) for key in fields)
                if not _same('0x'+keccak256(identity).hex(),identifier):
                    self.errors.append({'path':path,'code':'route.identity'})
            if route['observed_enabled'] is not True:
                # A disabled historical venue may be broken; raw append-only
                # identity and its explicit stop remain observable without it.
                continue
            route['venue_observation'] = self.attempt(path, 'route_venue.unavailable', lambda:
                self.route_venue(route['policy'], kind, role))
            for key, hash_key in (('source','sourceCodeHash'), ('output','outputCodeHash'), ('router','routerCodeHash'),
                                  ('factory','factoryCodeHash'), ('pool','poolCodeHash'),
                                  ('poolManager','poolManagerCodeHash'), ('stateView','stateViewCodeHash')):
                if key not in route['policy'] or hash_key not in route['policy'] or route['policy'][key] == ZERO:
                    continue
                runtime = self.attempt(path+'.'+key, 'runtime.unavailable', lambda k=key: self.code(route['policy'][k]))
                if runtime is not None and not _same(runtime, route['policy'][hash_key]):
                    self.errors.append({'path': path+'.'+key, 'code': 'runtime.mismatch'})


def observe(config, rpc):
    """Return a copied manifest with observations only; anchor failure raises.

    Unknown individual getter values are null and the observation is incomplete.
    Existing review evidence, approved pins and inventory-history assertions are
    never upgraded, fabricated or inferred from a successful RPC response.
    """
    from zzz_ops.production_v2 import expected_bindings
    if (not isinstance(config, dict) or type(config.get('schema_version')) is not int or config.get('schema_version') != 5 or
            not isinstance(config.get('chains'), list) or len(config['chains']) != 1):
        raise ValueError('Current observer requires the explicit single-chain schema 5')
    if type(config.get('review_policy_version')) is not int or config.get('review_policy_version') != 1:
        raise ValueError('Current schema-5 observation requires explicit review_policy_version 1')
    output = copy.deepcopy(config)
    chain = output['chains'][0]
    if not isinstance(chain.get('modules'), dict) or not isinstance(chain.get('helpers'), dict) or len(chain['modules']) > 17 or len(chain['helpers']) > 24:
        raise ValueError('Invalid bounded contract inventory')
    range_version = config.get('range_policy_version',0)
    if type(range_version) is not int or range_version not in (0,1):
        raise ValueError('Unsupported explicit range-policy observation profile')
    expected = expected_bindings(chain,range_policy_version=range_version)
    for field, limit in (('dependencies', 32), ('tokens', 33), ('pools', 16),
                         ('activation_sources', 64), ('conversion_routes', 64)):
        value = chain.get(field)
        if not isinstance(value, dict if field == 'dependencies' else list) or len(value) > limit:
            raise ValueError('Unbounded inventory list')
    pricing_version = config.get('pricing_version', 1)
    if type(pricing_version) is not int or pricing_version not in (1,2):
        raise ValueError('Unsupported explicit pricing observation profile')
    observer = Observer(rpc, chain)
    observer.pricing_version = pricing_version
    observer.range_policy_version = range_version
    with request_scope(Budget(seconds=60, calls=1024, posts=2048)):
        chain_id, genesis = observer.anchor()
        observer.records(expected)
        observer.dependencies()
        observer.tokens()
        observer.sequencer()
        observer.governance()
        observer.pools()
        observer.sources()
        observer.ledgers()
        observer.nft()
        observer.wrappers()
        observer.routes()
        observer.finish()
        chain['observation'] = {
            'chain_id': chain_id, 'genesis_hash': genesis, 'block_number': observer.start['number'],
            'block_hash': observer.start['hash'], 'observed_head': observer.head['number'],
            'complete': not observer.errors, 'errors': observer.errors,
        }
    return output


def read_manifest(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_INPUT_BYTES+1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError('Inventory input exceeds bound')
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON field')
            result[key] = value
        return result
    def nonfinite(_value):
        raise ValueError('Nonfinite JSON numbers are not inventory values')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def write_observation(path, value):
    """Atomic replacement; preserve the previous output if writing fails."""
    raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode('utf-8')
    if len(raw) > MAX_OUTPUT_BYTES:
        raise ValueError('Inventory output exceeds bound')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.popl-inventory-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
