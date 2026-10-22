"""Confirmed single-NFT projection using the deployed contracts' actual view ABI.

All contract reads use EIP-1898 requireCanonical block hashes. There is no
latest-state fallback, balance cache, inferred USD reward value or write RPC.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import time
from typing import Any, Callable

from frontend_api.history import History, HistoryError
from frontend_api.lifecycle import read_lifecycle
from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.rpc import Rpc, RpcError
from zzz_ops.state import integer
from zzz_ops.work_budget import BudgetedRPC, bounded_request, expire_at
from zzz_ops.errors import WorkLimit

ZERO = '0x' + '0' * 40
ROLES = ('access', 'nft', 'vault', 'rewards', 'royalties', 'claim_router', 'handoff', 'vault_canonical')
STATUS = ('none', 'active', 'outbound', 'remote', 'inbound', 'dormant', 'parked')
EVOLUTION = ('dormant', 'activated', 'enhanced', 'singularity')
UNAVAILABLE = {
    'wallet_inventory': 'Confirmed indexer history is not configured; no empty wallet inventory is inferred.',
    'previously_claimed': 'Confirmed indexer history is not configured; no zero lifetime total is inferred.',
    'fees_all_time': 'Requires funded-receipt history and attribution; current balances are not lifetime revenue.',
    'fees_last_24h': 'Requires timestamped funded-receipt history and attribution; no volume-based estimate is substituted.',
    'reward_usd': 'No reviewed historical/current reward-asset USD conversion is configured.',
    'individual_collective_breakdown': 'LP claimable is the exact contract total; unsettled component projections are not reconstructed.',
}


class ProjectionError(RpcError):
    """A fail-closed read; never serve an unverified or partial position."""


class UnknownNFT(ValueError):
    """The pinned NFT reports no mint ordinal for this token ID."""


def _keys(item: Any, expected: set[str], name: str) -> None:
    if not isinstance(item, dict) or set(item) != expected:
        raise ValueError(f'{name} has missing or unexpected fields')


def _hash(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', value):
        raise ValueError('Expected a 32-byte hash')
    if int(value, 16) == 0:
        raise ValueError('Zero hash is not a deployment pin')
    return value.lower()


def token_id(value: Any) -> int:
    """No float, hex, sign, bool, oversized or ambiguous leading-zero IDs."""
    if isinstance(value, str) and not re.fullmatch(r'0|[1-9][0-9]{0,77}', value):
        raise ValueError('Expected canonical decimal uint256 token ID')
    number = integer(value, 'token_id')
    if number >= 1 << 256:
        raise ValueError('Token ID exceeds uint256')
    return number


def _quantity(value: Any) -> int:
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value):
        raise ProjectionError('Malformed RPC quantity')
    return int(value, 16)


def _bool(word: str) -> bool:
    value = int(word, 16)
    if value not in (0, 1):
        raise ProjectionError('Noncanonical ABI boolean')
    return bool(value)


def _address_word(word: str, *, native: bool = False) -> str:
    if int(word[:24], 16) != 0:
        raise ProjectionError('Noncanonical ABI address')
    result = '0x' + word[24:]
    if result == ZERO and native:
        return result
    try:
        return address(result)
    except ValueError as exc:
        raise ProjectionError('Unexpected zero ABI address') from exc


@dataclass(frozen=True)
class Contract:
    address: str
    code_hash: str


@dataclass(frozen=True)
class Asset:
    address: str
    decimals: int
    symbol: str
    code_hash: str | None


class Projection:
    """One canonical deployment, approved assets and immutable code identities.

    Construction validates configuration only. Actual deployment, seal, asset
    admission and code checks run at the selected block on EVERY request.
    """

    def __init__(self, config: dict[str, Any], rpc: Rpc | None = None,
                 clock: Callable[[], float] = time.time):
        expected = {'schema', 'chain_id', 'rpc_urls', 'deployment_block',
                    'deployment_block_hash', 'confirmations', 'max_block_age_seconds', 'contracts', 'assets'}
        if isinstance(config, dict) and 'history' in config:
            expected.add('history')
        if isinstance(config, dict) and 'predecessors' in config:
            expected.add('predecessors')
        if isinstance(config, dict) and 'royalty_reporting' in config:
            expected.add('royalty_reporting')
        if isinstance(config, dict) and 'earnings_history' in config:
            expected.add('earnings_history')
        _keys(config, expected, 'configuration')
        if type(config['schema']) is not int or config['schema'] != 2:
            raise ValueError('Unsupported frontend API configuration schema')
        self.chain = integer(config['chain_id'], 'chain_id', minimum=1)
        self.start = integer(config['deployment_block'], 'deployment_block')
        self.start_hash = _hash(config['deployment_block_hash'])
        self.confirmations = integer(config['confirmations'], 'confirmations', minimum=1)
        self.max_age = integer(config['max_block_age_seconds'], 'max_block_age_seconds', minimum=1)
        if self.confirmations > 10000 or self.max_age > 86400:
            raise ValueError('Unbounded confirmations or accepted block age')
        urls = config['rpc_urls']
        if not isinstance(urls, list) or not 1 <= len(urls) <= 4 or any(not isinstance(x, str) for x in urls):
            raise ValueError('One to four fixed RPC URLs are required')
        validated_rpc = Rpc(urls, self.chain, timeout=5, retries=2)
        chosen_rpc = rpc or validated_rpc
        self.rpc = chosen_rpc if isinstance(chosen_rpc, BudgetedRPC) else BudgetedRPC(chosen_rpc)
        self.clock = clock
        _keys(config['contracts'], set(ROLES), 'contracts')
        self.contracts = {}
        for role in ROLES:
            item = config['contracts'][role]
            _keys(item, {'address', 'code_hash'}, f'contract {role}')
            self.contracts[role] = Contract(address(item['address']), _hash(item['code_hash']))
        if len({x.address for x in self.contracts.values()}) != len(ROLES):
            raise ValueError('Each configured contract must have a distinct address')
        if not isinstance(config['assets'], list) or len(config['assets']) > 49:
            raise ValueError('Bounded asset descriptor list is required')
        self.assets = {}
        for item in config['assets']:
            _keys(item, {'address', 'decimals', 'symbol', 'code_hash'}, 'asset')
            addr = ZERO if item['address'] == ZERO else address(item['address'])
            decimals = integer(item['decimals'], 'decimals')
            if decimals > 36 or addr == ZERO and decimals != 18:
                raise ValueError('Unsupported asset decimals')
            if not isinstance(item['symbol'], str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,16}', item['symbol']):
                raise ValueError('Asset symbols must be bounded ASCII display labels')
            code_hash = None if addr == ZERO else _hash(item['code_hash'])
            if addr == ZERO and item['code_hash'] is not None:
                raise ValueError('Native ETH has no token runtime code pin')
            if addr in self.assets or addr in {x.address for x in self.contracts.values()}:
                raise ValueError('Repeated asset or asset/contract collision')
            self.assets[addr] = Asset(addr, decimals, item['symbol'], code_hash)
        self.royalty_reporting = None
        if 'royalty_reporting' in config:
            from frontend_api.royalty_reporting import Reporting
            self.royalty_reporting = Reporting(config['royalty_reporting'], self)
        self.history = None
        if 'history' in config:
            self.history = History(config['history'], chain_id=self.chain,
                                   nft=self.contracts['nft'].address, rewards=self.contracts['rewards'].address,
                                   royalties=self.contracts['royalties'].address)
            if self.history.start > self.start:
                raise ValueError('History must start no later than the deployment anchor')
        self.identity = hashlib.sha256(json.dumps({k: v for k, v in config.items() if k != 'rpc_urls'},
                                                  sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.lineage = None
        if 'predecessors' in config:
            from frontend_api.lineage import Lineage
            self.lineage = Lineage(config['predecessors'], self, config)
        self.earnings_history = None
        if 'earnings_history' in config:
            from frontend_api.earnings import Earnings
            self.earnings_history = Earnings(config['earnings_history'], self)

    def _header(self, tag: str) -> dict[str, Any]:
        raw = self.rpc.call('eth_getBlockByNumber', [tag, False])
        if not isinstance(raw, dict):
            raise ProjectionError('Missing confirmed block header')
        try:
            header = {'number': _quantity(raw['number']), 'hash': _hash(raw['hash']),
                      'timestamp': _quantity(raw['timestamp'])}
        except (KeyError, ValueError) as exc:
            raise ProjectionError('Malformed block header') from exc
        if header['number'] != int(tag, 16):
            raise ProjectionError('Requested block header has the wrong number')
        return header

    def _call(self, target: str, signature: str, *args: Any, block: dict[str, Any], words: int = 1) -> list[str]:
        # The common ABI helper intentionally rejects zero addresses for most
        # operations. Here zero is a legitimate native reward asset, never a
        # target. Keep its selector/uint validation and replace only that word.
        native_methods = {'claimable(uint256,address)', 'eligibleFor(uint256,address)', 'ownerIndex(uint256,address)'}
        if signature in native_methods and len(args) == 2 and args[1] == ZERO:
            data = calldata(signature, args[0], '0x' + '0' * 39 + '1')[:-64] + '0' * 64
        elif signature in {'eligibleCount(address)', 'eligibleWeight(address)', 'index(address)', 'pending(address)'} and args == (ZERO,):
            data = calldata(signature, '0x' + '0' * 39 + '1')[:-64] + '0' * 64
        else:
            data = calldata(signature, *args)
        raw = self.rpc.call('eth_call', [{'to': target, 'data': data}, block])
        try:
            result = decode_words(raw)
        except ValueError as exc:
            raise ProjectionError('Malformed static ABI result') from exc
        if len(result) != words:
            raise ProjectionError('Unexpected static ABI result length')
        return result

    def _uint(self, role: str, signature: str, *args: Any, block: dict[str, Any]) -> int:
        return int(self._call(self.contracts[role].address, signature, *args, block=block)[0], 16)

    def _addr(self, role: str, signature: str, *args: Any, block: dict[str, Any], native: bool = False) -> str:
        return _address_word(self._call(self.contracts[role].address, signature, *args, block=block)[0], native=native)

    def _code(self, addr: str, expected: str, block: dict[str, Any]) -> None:
        result = self.rpc.call('eth_getCode', [addr, block])
        if not isinstance(result, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', result):
            raise ProjectionError('Missing or malformed pinned runtime code')
        if '0x' + keccak256(bytes.fromhex(result[2:])).hex() != expected:
            raise ProjectionError('Runtime code differs from deployment pin')

    def _verify_deployment(self, block: dict[str, Any], *, allow_locked: bool = False) -> dict[str, Any]:
        for item in self.contracts.values():
            self._code(item.address, item.code_hash, block)
        access = self.contracts['access'].address
        sealed = _bool(self._call(access, 'isSealed()', block=block)[0])
        if not sealed:
            raise ProjectionError('Deployment is not sealed')
        for role, label in (('nft', 'ZZZNFT'), ('vault', 'ZZZVault'), ('rewards', 'ZZZRewards')):
            if self._addr(role, 'access()', block=block) != access:
                raise ProjectionError('Inconsistent module access controller')
            module_id = '0x' + keccak256(label.encode()).hex()
            if self._addr('access', 'module(bytes32)', module_id, block=block) != self.contracts[role].address:
                raise ProjectionError('Module is not the sealed canonical binding')
        if self._uint('vault', 'canonicalChainId()', block=block) != self.chain:
            raise ProjectionError('Configured chain is not the NFT canonical home')
        bindings = (('nft', 'royaltyRewards()', 'royalties'), ('royalties', 'nft()', 'nft'),
                    ('nft', 'claimRouter()', 'claim_router'), ('claim_router', 'nft()', 'nft'),
                    ('claim_router', 'royalties()', 'royalties'), ('claim_router', 'access()', 'access'))
        for role, method, expected in bindings:
            if self._addr(role, method, block=block) != self.contracts[expected].address:
                raise ProjectionError('Immutable NFT/helper binding differs from deployment pins')
        lifecycle = read_lifecycle(self, block)
        if not allow_locked and lifecycle['state'] != 'operating':
            raise ProjectionError('Canonical deployment is locked; use the protocol status endpoint')
        return lifecycle

    @bounded_request
    def mint_readiness(self) -> dict[str, Any]:
        from frontend_api.mint_readiness import inspect
        return inspect(self)

    @bounded_request
    def protocol(self) -> dict[str, Any]:
        """Lifecycle remains readable without touching frozen reward ledgers."""
        header, head, block = self._snapshot()
        lifecycle = self._verify_deployment(block, allow_locked=True)
        mint_paused = _bool(self._call(self.contracts['nft'].address, 'mintPaused()', block=block)[0])
        self._finish(header)
        return {'schema': 2, 'chain_id': self.chain, 'lifecycle': lifecycle,
                'minting': {'paused': mint_paused,
                            'available_by_controls': not mint_paused and lifecycle['new_economic_work_available_by_lifecycle']},
                'contracts': {role: item.address for role, item in self.contracts.items()},
                'provenance': {'block_number': header['number'], 'block_hash': header['hash'],
                               'block_timestamp': header['timestamp'], 'observed_head': head,
                               'confirmations': self.confirmations, 'protocol_finalized': False,
                               'finality': 'confirmation_depth_only', 'eip1898_require_canonical': True,
                               'deployment_block': self.start, 'deployment_block_hash': self.start_hash,
                               'configuration_sha256': self.identity}}

    def _admitted(self, block: dict[str, Any], *, asset_health=None) -> tuple[list[str], list[str]]:
        admitted = []
        for role, maximum in (('rewards', 33), ('royalties', 17)):
            count = self._uint(role, 'assetCount()', block=block)
            if count > maximum:
                raise ProjectionError('Contract asset count exceeds reviewed bound')
            addresses = [self._addr(role, 'assets(uint256)', n, block=block, native=True)
                         for n in range(count)]
            if len(set(addresses)) != count or role == 'royalties' and (not addresses or addresses[0] != ZERO):
                raise ProjectionError('Malformed admitted asset inventory')
            if role == 'rewards' and (len(set(addresses)-{ZERO}) > 32 or (ZERO in addresses and addresses[0] != ZERO)):
                raise ProjectionError('Malformed LP native settlement inventory')
            admitted.append(addresses)
        if set().union(*map(set, admitted)) != set(self.assets):
            raise ProjectionError('Admitted assets differ from the reviewed descriptor allowlist')
        for item in self.assets.values():
            if item.address == ZERO:
                if asset_health is not None:
                    asset_health[item.address] = True
                continue
            try:
                self._code(item.address, item.code_hash, block)
                decimals = int(self._call(item.address, 'decimals()', block=block)[0], 16)
                if decimals != item.decimals:
                    raise ProjectionError('Asset decimals differ from the reviewed descriptor')
            except WorkLimit:
                raise
            except RpcError:
                if asset_health is None:
                    raise
                asset_health[item.address] = False
            else:
                if asset_health is not None:
                    asset_health[item.address] = True
        return admitted[0], admitted[1]

    def _balance(self, role: str, nft_id: int, asset: str, block: dict[str, Any]) -> dict[str, Any]:
        item = self.assets[asset]
        return {'asset': item.address, 'symbol': item.symbol, 'decimals': item.decimals,
                'raw': str(self._uint(role, 'claimable(uint256,address)', nft_id, asset, block=block))}

    def _snapshot(self):
        if self.rpc.call('eth_chainId', []) != self.chain:
            raise ProjectionError('Configured RPC chain differs from deployment')
        head = _quantity(self.rpc.call('eth_blockNumber', []))
        safe = head - self.confirmations + 1
        if safe < self.start:
            raise ProjectionError('Insufficient confirmation depth after deployment')
        if self._header(hex(self.start))['hash'] != self.start_hash:
            raise ProjectionError('Deployment anchor is no longer canonical')
        header = self._header(hex(safe))
        if header['number'] != safe:
            raise ProjectionError('Confirmed header has the wrong block number')
        self._fresh(header)
        expire_at(header['timestamp'] + self.max_age, self.clock)
        block = {'blockHash': header['hash'], 'requireCanonical': True}
        return header, head, block

    def _fresh(self, header):
        now = self.clock()
        if header['timestamp'] > now + 30 or now - header['timestamp'] > self.max_age:
            raise ProjectionError('Confirmed header timestamp is stale or in the future')

    def _finish(self, header):
        # Long asset/history reads must not release an expired snapshot. A
        # provider failover can also retain this block while dropping enough
        # descendants that the configured confirmation depth is no longer met.
        head = _quantity(self.rpc.call('eth_blockNumber', []))
        if head < header['number'] + self.confirmations - 1:
            raise ProjectionError('Confirmed projection lost its required confirmation depth')
        if self._header(hex(header['number'])) != header or self._header(hex(self.start))['hash'] != self.start_hash:
            raise ProjectionError('Canonical chain changed during the projection')
        if self.rpc.call('eth_chainId', []) != self.chain:
            raise ProjectionError('RPC chain changed during the projection')
        # Check after the final network response, not before a potentially slow
        # retry or history replay. No partial result is returned on expiry.
        self._fresh(header)

    def _history_snapshot(self, header, block, lp_assets, royalty_assets, *, consumer=None, extra_emitters=()):
        if self.history is None:
            return None
        # The reviewed coverage start is the NFT's actual creation block, not
        # an arbitrary later seal/checkpoint that could omit earlier ownership.
        previous = self._header(hex(self.history.start - 1))
        if previous['hash'] != self.history.parent:
            raise HistoryError('History creation-parent anchor is no longer canonical')
        nft = self.contracts['nft']
        before = self.rpc.call('eth_getCode', [nft.address, {'blockHash': previous['hash'], 'requireCanonical': True}])
        if before != '0x':
            raise HistoryError('History starts after the NFT already existed')
        created = self._header(hex(self.history.start))
        self._code(nft.address, nft.code_hash, {'blockHash': created['hash'], 'requireCanonical': True})
        count = self._uint('nft', 'mintedCount()', block=block)
        history = self.history.read(block_number=header['number'], block_hash=header['hash'],
                                    block_timestamp=header['timestamp'], minted_count=count,
                                    lp_assets=set(lp_assets), royalty_assets=set(royalty_assets),
                                    consumer=consumer, extra_emitters=extra_emitters)
        if history.provenance['start_block_hash'] != created['hash']:
            raise HistoryError('Indexed creation block differs from its canonical RPC anchor')
        return history

    def _claimed(self, history, nft_id):
        if history is None:
            return {'available': False, 'assets': None, 'reason': UNAVAILABLE['previously_claimed']}
        assets = history.claimed(nft_id, set(self.assets))
        for item in assets:
            descriptor = self.assets[item['asset']]
            item.update(symbol=descriptor.symbol, decimals=descriptor.decimals)
        return {'available': True, 'assets': assets, 'scope': 'All-time NFT claims, including LP and royalties paid to every past/current owner.',
                'provenance': dict(history.provenance)}

    @bounded_request
    def earnings(self, identifier=None):
        if self.earnings_history is None:
            raise HistoryError('Reviewed earnings-history profile is not configured')
        return self.earnings_history.read(None if identifier is None else token_id(identifier))

    @bounded_request
    def nft(self, identifier: Any) -> dict[str, Any]:
        nft_id = token_id(identifier)
        header, head, block = self._snapshot()
        safe = header['number']
        lifecycle = self._verify_deployment(block)
        health = {} if self.royalty_reporting is not None else None
        lp_assets, royalty_assets = self._admitted(block, asset_health=health)
        ordinal = self._uint('nft', 'mintOrdinalOf(uint256)', nft_id, block=block)
        if ordinal == 0:
            raise UnknownNFT('NFT has no canonical mint ordinal')
        if ordinal > 1000 or self._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=block) != nft_id:
            raise ProjectionError('Inconsistent canonical mint identity')
        owner = self._addr('nft', 'ownerOf(uint256)', nft_id, block=block)
        ready = _bool(self._call(self.contracts['nft'].address, 'traitsReady(uint256)', nft_id, block=block)[0])
        traits = None
        if ready:
            rarity = self._uint('nft', 'rarityOf(uint256)', nft_id, block=block)
            palette = self._uint('nft', 'paletteOf(uint256)', nft_id, block=block)
            pattern = self._uint('nft', 'patternOf(uint256)', nft_id, block=block)
            if rarity > 2 or palette > 57 or pattern > 3:
                raise ProjectionError('Traits exceed the immutable artwork catalogue')
            traits = {'rarity': ('Commun', 'Rare', 'Legendary')[rarity], 'palette': palette, 'pattern': pattern}
        status = self._uint('vault', 'nftStatus(uint256)', nft_id, block=block)
        if status == 0 or status >= len(STATUS):
            raise ProjectionError('Missing or unsupported canonical vault state')
        bucket = self._uint('vault', 'nftBucket(uint256)', nft_id, block=block)
        shares = self._uint('vault', 'sharesOf(uint256)', nft_id, block=block)
        weight = self._uint('royalties', 'weightOf(uint256)', nft_id, block=block)
        if weight > 3 or (weight > 0) != (shares > 0) or (shares > 0) != (bucket > 0):
            raise ProjectionError('Inconsistent activation/royalty/share state')
        if weight > 0 and (not ready or weight != rarity + 1) or (status == 5) != (shares == 0):
            raise ProjectionError('Activation differs from the canonical revealed NFT state')
        custody = None
        if status in (1, 6):
            group = self._call(self.contracts['vault'].address, 'group(uint256)', bucket, block=block, words=15)
            supply = self._uint('vault', 'bucketTotalShares(uint256)', bucket, block=block)
            if (int(group[0], 16) == 0 or (int(group[1], 16) == 0) != (status == 6) or int(group[7], 16) != status or
                    int(group[8], 16) != self.chain or _address_word(group[9]) != self.contracts['vault'].address or
                    int(group[13], 16) != self.chain or _address_word(group[14]) != self.contracts['vault'].address or
                    supply < shares):
                raise ProjectionError('Local principal differs from its canonical custody state')
            custody = {'pool_id': '0x' + group[0],
                       'lp_token_id': str(int(group[1], 16)) if status == 1 else None,
                       'bucket_total_shares_raw': str(supply),
                       'share_numerator_raw': str(shares), 'share_denominator_raw': str(supply),
                       'last_rebalance_at': int(group[6], 16),
                       'identity_source': 'Vault.group at the confirmed snapshot'}
        contribution = self._uint('vault', 'contributionUSD(uint256)', nft_id, block=block)
        value = self._call(self.contracts['nft'].address, 'currentLPValue(uint256)', nft_id, block=block, words=2)
        available = _bool(value[0])
        raw_usd = int(value[1], 16)
        if status not in (1, 5) and available:
            raise ProjectionError('Unavailable custody cannot report an active LP valuation')
        if status == 5 and (not available or raw_usd != 0 or contribution != 0):
            raise ProjectionError('Dormant NFT must have verified zero LP and contributions')
        if not available and raw_usd != 0:
            raise ProjectionError('Unavailable valuation contains a fabricated amount')
        lp_value = {'available': available, 'raw': str(raw_usd) if available else None, 'decimals': 18,
                    'unit': 'USD', 'source': 'NFT.currentLPValue',
                    'reason': None if available else 'Principal is parked in the Vault; current LP valuation is unavailable.'
                    if status == 6 else 'Remote/in-flight custody or unavailable valuation dependency.'}
        # Derive precisely the same four-state display from the single current
        # value read. Activation eligibility persists independently of its mark.
        stage = 0 if weight == 0 else 3 if available and raw_usd >= 10000 * 10**18 else 2 if available and raw_usd >= 1000 * 10**18 else 1
        settlement = None
        if self.royalty_reporting is not None:
            settlement = self.royalty_reporting.read(nft_id, weight, royalty_assets, health, block)
            lp_balances = [self.royalty_reporting.balance('rewards', nft_id, a, health, block) for a in lp_assets]
            royalty_balances = settlement.pop('balances')
        else:
            lp_balances = [self._balance('rewards', nft_id, a, block) for a in lp_assets]
            royalty_balances = [self._balance('royalties', nft_id, a, block) for a in royalty_assets]
        result = {
            'schema': 2, 'chain_id': self.chain, 'token_id': str(nft_id), 'mint_ordinal': ordinal,
            'lifecycle': lifecycle,
            'owner': owner, 'traits_ready': ready, 'traits': traits,
            'position': {'status': STATUS[status], 'bucket_id': str(bucket), 'shares_raw': str(shares),
                         'local_custody': custody,
                         'cumulative_gross_contribution_usd_18': str(contribution),
                         'activated': weight != 0, 'royalty_weight': weight, 'current_lp_value': lp_value,
                         'evolution': EVOLUTION[stage], 'evolution_value_available': available,
                         'principal_redeemable': False},
            'claimable': {'lp': lp_balances,
                          'default_settlement': 'native_eth' if ZERO in lp_assets else 'source_assets',
                          'royalties': royalty_balances,
                          'lp_scope': 'Already allocated funded rewards; pending creator inbox receipts are not simulated.',
                          'royalty_scope': 'Contract view includes pending admitted receipts at this currency\'s eligible membership weights. ETH also includes unclaimed conversion credits.'},
            'royalty_reporting': settlement or {'available': False,
                'reason': 'Current royalty-ledger reporting profile is not configured; no per-currency eligibility or conversion status is inferred.'},
            'unavailable_metrics': dict(UNAVAILABLE),
            'contracts': {role: item.address for role, item in self.contracts.items()},
            'provenance': {'block_number': safe, 'block_hash': header['hash'], 'block_timestamp': header['timestamp'],
                           'observed_head': head, 'confirmations': self.confirmations,
                           'finality': 'confirmation_depth_only', 'protocol_finalized': False,
                           'eip1898_require_canonical': True, 'deployment_block': self.start,
                           'deployment_block_hash': self.start_hash, 'configuration_sha256': self.identity},
        }
        history = self._history_snapshot(header, block, lp_assets, royalty_assets)
        if history is not None:
            if history.owners.get(nft_id) != owner:
                raise HistoryError('Indexed NFT owner differs from canonical ownerOf')
            if lifecycle['predecessor_controller'] is None:
                result['unavailable_metrics'].pop('previously_claimed')
            result['unavailable_metrics'].pop('wallet_inventory')
            result['wallet_inventory_endpoint'] = f'/v1/wallets/{owner}/nfts'
        if self.lineage is not None:
            result.update(self.lineage.financial(self, header, block, lifecycle, history, nft_id, ordinal))
            result['unavailable_metrics'].pop('previously_claimed', None)
        elif lifecycle['predecessor_controller'] is not None:
            reason = 'Complete verified predecessor claim history is not configured; lifetime totals are unavailable.'
            result['previously_claimed'] = {'available': False, 'assets': None, 'reason': reason}
            result['royalty_conversions'] = {'available': False, 'assets': None, 'total_eth_credited_raw': None, 'reason': reason}
            result['lp_conversions'] = {'available': False, 'assets': None, 'total_eth_credited_raw': None, 'reason': reason}
            result['unavailable_metrics']['previously_claimed'] = reason
        else:
            result['previously_claimed'] = self._claimed(history, nft_id)
            from frontend_api.history import conversion_report
            result['royalty_conversions'] = conversion_report(history.conversions if history else None,
                nft_id, self.assets, dict(history.provenance) if history else None)
            result['lp_conversions'] = conversion_report(history.lp_conversions if history else None,
                nft_id, self.assets, dict(history.provenance) if history else None)
        # No partial response is released if ancestry/chain changes during the
        # serial reads, including provider failover to a competing fork.
        self._finish(header)
        return result

    @bounded_request
    def wallet_summary(self, wallet_address, block_number, offset=0):
        from frontend_api.portfolio import read
        return read(self, wallet_address, block_number, offset)

    @bounded_request
    def wallet_earnings(self, wallet_address, block_number, offset=0):
        from frontend_api.wallet_earnings import read
        if self.earnings_history is None:
            raise HistoryError('Reviewed earnings-history profile is not configured')
        return read(self.earnings_history, wallet_address, block_number, offset)

    @bounded_request
    def wallet(self, wallet_address: Any) -> dict[str, Any]:
        wallet = address(wallet_address)
        if self.history is None:
            raise HistoryError('Confirmed wallet inventory requires configured history')
        header, head, block = self._snapshot()
        lifecycle = self._verify_deployment(block)
        lp_assets, royalty_assets = self._admitted(block)
        history = self._history_snapshot(header, block, lp_assets, royalty_assets)
        identifiers = sorted(nft_id for nft_id, owner in history.owners.items() if owner == wallet)
        count = self._uint('nft', 'balanceOf(address)', wallet, block=block)
        if count != len(identifiers) or count > 1000:
            raise HistoryError('Indexed wallet inventory differs from canonical ERC721 balance')
        for nft_id in identifiers:
            if self._addr('nft', 'ownerOf(uint256)', nft_id, block=block) != wallet:
                raise HistoryError('Indexed wallet token is not owned by the canonical wallet')
        self._finish(header)
        return {'schema': 2, 'chain_id': self.chain, 'wallet': wallet, 'available': True,
                'lifecycle': lifecycle,
                'count': len(identifiers), 'token_ids': [str(nft_id) for nft_id in identifiers],
                'nft_contract': self.contracts['nft'].address,
                'provenance': {'block_number': header['number'], 'block_hash': header['hash'],
                               'block_timestamp': header['timestamp'], 'observed_head': head,
                               'confirmations': self.confirmations, 'finality': 'confirmation_depth_only',
                               'protocol_finalized': False, 'eip1898_require_canonical': True,
                               'configuration_sha256': self.identity},
                'history': dict(history.provenance),
                'scope': 'Complete current wallet NFT inventory at this block; fetch each NFT endpoint for balances/history and compare snapshot provenance.'}
