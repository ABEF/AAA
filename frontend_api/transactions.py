"""Typed unsigned mint/claim drafts, simulated at one confirmed canonical block.

No signing, broadcasting, approvals, arbitrary calls, user-selected destinations,
state overrides or activation quotes. A draft is NOT permission to submit it:
the wallet must validate the deployment, account, chain, calldata, expiry and
latest execution/gas immediately before asking its owner to sign.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from frontend_api.service import Projection, ProjectionError, UnknownNFT, ZERO, _bool, _hash, _keys, _quantity, token_id
from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.work_budget import bounded_request, expire_at

MINT_PRICE = 50_000_000_000_000_000
MAX_CLAIMS = 32
SIMULATION_GAS_LIMIT = 12_000_000
MAX_SNAPSHOT_AGE = 120
DRAFT_LIFETIME = 60
CLAIM_SIGNATURE = 'claimBatch((uint256,address,bool)[])'


class TransactionInputError(ValueError):
    """Invalid typed action; never includes a caller's raw payload."""


class TransactionConfig:
    """Operator policy bound to the exact reviewed read configuration."""
    def __init__(self, config, projection):
        _keys(config, {'schema', 'chain_id', 'projection_sha256', 'fee_policy'}, 'transaction configuration')
        if type(config['schema']) is not int or config['schema'] != 1:
            raise ValueError('Unsupported transaction configuration schema')
        if type(config['chain_id']) is not int or config['chain_id'] != projection.chain:
            raise ValueError('Transaction chain differs from the read configuration')
        if config['projection_sha256'] != projection.identity:
            raise ValueError('Transaction policy requires the exact reviewed read configuration')
        fee = config['fee_policy']
        _keys(fee, {'estimate_includes_all_fees', 'review_hash', 'max_gas_price_wei', 'max_network_fee_wei'}, 'fee policy')
        if fee['estimate_includes_all_fees'] is not True:
            raise ValueError('Complete network fee semantics must be reviewed')
        self.review = _hash(fee['review_hash'])
        for field in ('max_gas_price_wei', 'max_network_fee_wei'):
            if not isinstance(fee[field], str) or not re.fullmatch(r'[1-9][0-9]{0,19}', fee[field]):
                raise ValueError('A bounded positive decimal fee ceiling is required')
        self.max_price = int(fee['max_gas_price_wei'])
        self.max_fee = int(fee['max_network_fee_wei'])
        self.identity = hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True)
class Claim:
    token_id: int
    asset: str
    royalty: bool


def _fields(value: Any, expected: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise TransactionInputError('Unexpected or missing action fields')


def _parse(payload: Any) -> tuple[str, str, tuple[Claim, ...]]:
    if not isinstance(payload, dict) or payload.get('action') not in ('mint', 'claim'):
        raise TransactionInputError('Only typed mint and claim actions are supported')
    action = payload['action']
    _fields(payload, {'action', 'wallet'} | ({'claims'} if action == 'claim' else set()))
    try:
        owner = address(payload['wallet'])
    except ValueError as exc:
        raise TransactionInputError('Invalid wallet address') from exc
    claims = []
    if action == 'claim':
        raw = payload['claims']
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_CLAIMS:
            raise TransactionInputError('Select between one and 32 claim operations')
        for item in raw:
            _fields(item, {'token_id', 'asset', 'royalty'})
            # JSON numeric IDs can already have lost precision in a browser.
            if not isinstance(item['token_id'], str) or type(item['royalty']) is not bool:
                raise TransactionInputError('Claims require decimal string IDs and boolean royalty flags')
            try:
                identifier = token_id(item['token_id'])
                asset = ZERO if item['asset'] == ZERO else address(item['asset'])
            except ValueError as exc:
                raise TransactionInputError('Invalid claim identity or asset') from exc
            entry = Claim(identifier, asset, item['royalty'])
            if entry in claims:
                raise TransactionInputError('Duplicate claim operation')
            claims.append(entry)
    return action, owner, tuple(claims)


def claim_calldata(claims: tuple[Claim, ...]) -> str:
    """One dynamic array of STATIC tuples; no nested dynamic offsets or targets."""
    if not 1 <= len(claims) <= MAX_CLAIMS:
        raise TransactionInputError('Invalid claim array length')
    data = f'{32:064x}{len(claims):064x}'
    for entry in claims:
        data += f'{entry.token_id:064x}{int(entry.asset, 16):064x}{int(entry.royalty):064x}'
    return '0x' + keccak256(CLAIM_SIGNATURE.encode()).hex()[:8] + data


def _claim_results(raw: Any, count: int) -> list[int]:
    if not isinstance(raw, str) or len(raw) != 2 + 64 * (count + 2):
        raise ProjectionError('Unexpected claim simulation result size')
    try:
        words = decode_words(raw)
    except ValueError as exc:
        raise ProjectionError('Malformed claim simulation result') from exc
    if int(words[0], 16) != 32 or int(words[1], 16) != count:
        raise ProjectionError('Noncanonical claim result offset or count')
    return [int(word, 16) for word in words[2:]]


class Transactions:
    def __init__(self, projection: Projection, config):
        self.projection = projection
        self.config = TransactionConfig(config, projection)

    def _gas(self, tx, block):
        p = self.projection
        estimate = _quantity(p.rpc.call('eth_estimateGas', [{**tx, 'gas': hex(SIMULATION_GAS_LIMIT)}, block]))
        price = _quantity(p.rpc.call('eth_gasPrice', []))
        if not 21000 <= estimate <= SIMULATION_GAS_LIMIT or not 0 < price <= self.config.max_price:
            raise ProjectionError('Gas estimate or price exceeds the reviewed bound')
        limit = min(SIMULATION_GAS_LIMIT, (estimate * 120 + 99) // 100)
        if limit * price > self.config.max_fee:
            raise ProjectionError('Network fee exceeds the reviewed bound')
        balance = _quantity(p.rpc.call('eth_getBalance', [tx['from'], block]))
        if balance < int(tx['value'], 16) + limit * price:
            raise TransactionInputError('Wallet lacks native currency for value and separate estimated gas')
        return {'estimated_units': str(estimate), 'suggested_limit': str(limit), 'price_wei': str(price),
                'estimated_fee_wei': str(estimate * price), 'suggested_limit_cost_wei': str(limit * price),
                'currency': 'native', 'includes_all_network_components': True,
                'fee_policy_review_hash': self.config.review, 'wallet_must_refresh': True,
                'price_source': 'eth_gasPrice at preparation time'}

    def _fresh(self, header: dict[str, Any]) -> int:
        now = int(self.projection.clock())
        if header['timestamp'] > now + 30 or now - header['timestamp'] > MAX_SNAPSHOT_AGE:
            raise ProjectionError('Transaction snapshot is stale or in the future')
        return now

    @bounded_request
    def prepare(self, payload: Any) -> dict[str, Any]:
        action, owner, claims = _parse(payload)
        p = self.projection
        header, head, block = p._snapshot()
        self._fresh(header)
        expire_at(header['timestamp'] + min(p.max_age, MAX_SNAPSHOT_AGE), p.clock)
        lifecycle = p._verify_deployment(block)
        details = []
        mint_policy = None
        if action == 'mint':
            if not lifecycle['new_economic_work_available_by_lifecycle'] or _bool(p._call(
                    p.contracts['nft'].address, 'mintPaused()', block=block)[0]):
                raise TransactionInputError('Minting is unavailable')
            if p.accounting_version!=6 and p._uint('vault', 'MINT_PRICE()', block=block) != MINT_PRICE:
                raise ProjectionError('Mint price differs from reviewed product configuration')
            if p._uint('nft', 'MAX_SUPPLY()', block=block) != 1000:
                raise ProjectionError('NFT supply cap differs from reviewed configuration')
            if p._uint('nft', 'mintedCount()', block=block) >= 1000:
                raise TransactionInputError('Collection is fully minted')
            if p.accounting_version==6:
                from zzz_ops.protocol_policy import observe as observe_policy,observe_mint
                try:
                    sale=observe_policy(lambda target,method,*args,count:p._call(target,method,*args,block=block,words=count),
                        policy=p.contracts['protocol_policy'].address,access=p.contracts['access'].address,domain='sale')
                    mint=observe_mint(lambda target,method,*args,count:p._call(target,method,*args,block=block,words=count),
                        policy=p.contracts['protocol_policy'].address,access=p.contracts['access'].address)
                except (ValueError,TypeError,KeyError) as exc:
                    raise ProjectionError('Mint policy cannot be authenticated') from exc
                fingerprint='0x'+p._call(p.contracts['vault'].address,'mintPolicyFingerprint()',block=block)[0]
                if (fingerprint!=mint['fingerprint'] or p._uint('vault','mintPrice()',block=block)!=sale['mint_price_wei'] or
                        p._addr('vault','mintProceedsRecipient()',block=block)!=sale['recipient']):
                    raise ProjectionError('Vault mint terms differ from authenticated policy')
                target,data,value=p.contracts['vault'].address,calldata('mintDormant(bytes32)',fingerprint),sale['mint_price_wei']
                mint_policy={'fingerprint':fingerprint,'price_wei':str(value),
                    'recipient':sale['recipient'],'revision':str(sale['revision']),'vrf_revision':str(mint['vrf_revision'])}
            else:
                target, data, value = p.contracts['vault'].address, calldata('mintDormant()'), MINT_PRICE
        else:
            health = {}
            lp_assets, royalty_assets = p._admitted(block, asset_health=health)
            checked = set()
            inactive = set()
            for entry in claims:
                if entry.asset not in (royalty_assets if entry.royalty else lp_assets):
                    raise TransactionInputError('Asset is not admitted by the selected claim ledger')
                if not health[entry.asset]:
                    raise ProjectionError('Selected claim currency cannot be verified')
                if entry.token_id not in checked:
                    ordinal = p._uint('nft', 'mintOrdinalOf(uint256)', entry.token_id, block=block)
                    if ordinal == 0:
                        raise UnknownNFT('NFT has no canonical mint ordinal')
                    if ordinal > 1000 or p._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=block) != entry.token_id:
                        raise ProjectionError('Inconsistent NFT mint identity')
                    if p._addr('nft', 'ownerOf(uint256)', entry.token_id, block=block) != owner:
                        raise TransactionInputError('Wallet does not own every selected NFT')
                    if p.accounting_version in (3, 4, 5, 6):
                        # Current activation gives a permanent global royalty
                        # weight, even if one optional currency is deferred.
                        # Zero means never activated, not parked/outbound LP.
                        # Mirror the current read projection's integrity guard
                        # without querying optional currencies or historic codecs.
                        weight = p._uint('royalties', 'weightOf(uint256)', entry.token_id, block=block)
                        if weight > 3:
                            raise ProjectionError('NFT activation weight exceeds the reviewed bound')
                        if weight == 0:
                            inactive.add(entry.token_id)
                    checked.add(entry.token_id)
                role = 'royalties' if entry.royalty else 'rewards'
                amount = p._uint(role, 'claimable(uint256,address)', entry.token_id, entry.asset, block=block)
                if amount == 0:
                    raise TransactionInputError('Selected claim has no funded balance')
                if entry.token_id in inactive:
                    raise ProjectionError('Inactive NFT has reward entitlement')
                asset = p.assets[entry.asset]
                details.append({'token_id': str(entry.token_id), 'asset': entry.asset, 'royalty': entry.royalty,
                                'symbol': asset.symbol, 'decimals': asset.decimals, 'view_raw': str(amount)})
            target, data, value = p.contracts['claim_router'].address, claim_calldata(claims), 0
        tx = {'from': owner, 'to': target, 'data': data, 'value': hex(value)}
        # Explicit cap bounds RPC EVM work. It is NOT a gas estimate and is never
        # copied into the wallet draft. No state/balance/allowance override exists.
        raw = p.rpc.call('eth_call', [{**tx, 'gas': hex(SIMULATION_GAS_LIMIT)}, block])
        if action == 'mint':
            if not isinstance(raw, str) or len(raw) != 66:
                raise ProjectionError('Unexpected mint simulation result size')
            try:
                words = decode_words(raw)
            except ValueError as exc:
                raise ProjectionError('Malformed mint simulation result') from exc
            if len(words) != 1:
                raise ProjectionError('Unexpected mint simulation result size')
            # A simulated token ID is not reserved. Read the actual mint receipt.
        else:
            amounts = _claim_results(raw, len(claims))
            for detail, amount in zip(details, amounts):
                if amount == 0:
                    raise ProjectionError('Selected claim simulation returned no funded amount')
                detail['simulated_raw'] = str(amount)
        gas = self._gas(tx, block)
        p._finish(header)
        prepared_at = self._fresh(header)
        expires_at = min(prepared_at + DRAFT_LIFETIME, header['timestamp'] + min(p.max_age, MAX_SNAPSHOT_AGE))
        if expires_at <= prepared_at:
            raise ProjectionError('Transaction snapshot expires before draft publication')
        return {
            'schema': 1, 'kind': 'unsigned_transaction_draft', 'action': action,
            'transaction': {**tx, 'chainId': hex(p.chain)},
            'claim_operations': details, 'prepared_at': prepared_at, 'expires_at': expires_at,
            **({'mint_policy':mint_policy} if mint_policy is not None else {}),
            'provenance': {'block_number': header['number'], 'block_hash': header['hash'],
                           'block_timestamp': header['timestamp'], 'observed_head': head,
                           'confirmations': p.confirmations, 'protocol_finalized': False,
                           'eip1898_require_canonical': True, 'deployment_block': p.start,
                           'deployment_block_hash': p.start_hash, 'configuration_sha256': p.identity,
                           'transaction_configuration_sha256': self.config.identity},
            'network_gas': gas,
            'simulation': {'succeeded': True, 'gas_cap': str(SIMULATION_GAS_LIMIT),
                           'gas_estimate': gas['estimated_units'], 'balance_overrides': False},
            'wallet_revalidation_required': True, 'approvals_required': False,
            'scope': 'Unsigned confirmed-block simulation only. Expiry is a client rule, not an on-chain deadline. '
                     'Independently verify deployment/account/chain/calldata, re-simulate and estimate current gas before signing. '
                     'No pending transaction, future payout, mint identity or production readiness is guaranteed.',
        }
