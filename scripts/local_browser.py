"""Unsigned extension-wallet boundary for the owned, disposable Anvil fixture.

Holder transactions are never submitted here. A separate bounded journal stores
reviewed payloads and observes exact externally signed receipts. The only optional
operator transactions are the fixture's original MockVRF callback/finalization.
This module is not a public RPC proxy, a wallet, or a production service.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import time

from zzz_ops.abi import keccak256
from zzz_ops.ethereum_fees import fee_cap, execution_price, transaction_chain_id

CHAIN = 31337
ZERO = '0x' + '0' * 40
MAX_RECORDS = 256
MAX_JOURNAL_BYTES = 16 * 1024 * 1024
MAX_GAS = 30_000_000
MAX_PRICE = 100 * 10**9
MAX_NETWORK_FEE = 10**18
MAX_VALUE = 99_999 * 10**18
TRANSFER = '0x' + keccak256(b'Transfer(address,address,uint256)').hex()
HEX_HASH = re.compile(r'0x[0-9a-f]{64}')
HEX_ADDRESS = re.compile(r'0x[0-9a-f]{40}')
HEX_QUANTITY = re.compile(r'0x(?:0|[1-9a-f][0-9a-f]{0,63})')
IDENTIFIER = re.compile(r'[a-f0-9]{32}')


def _quantity(value):
    if not isinstance(value, str) or not HEX_QUANTITY.fullmatch(value):
        raise ValueError('Invalid browser transaction quantity')
    return int(value, 16)


def _hash(value):
    if not isinstance(value, str) or not HEX_HASH.fullmatch(value):
        raise ValueError('Invalid browser transaction hash')
    return value


def _transaction(tx):
    fields = {'from', 'to', 'data', 'value', 'nonce', 'gas', 'gasPrice'}
    if not isinstance(tx, dict) or set(tx) != fields:
        raise ValueError('Unexpected unsigned browser transaction fields')
    if any(not isinstance(tx[k], str) or not HEX_ADDRESS.fullmatch(tx[k]) for k in ('from', 'to')):
        raise ValueError('Invalid unsigned browser transaction address')
    if not isinstance(tx['data'], str) or not re.fullmatch(r'0x(?:[a-f0-9]{2}){4,16384}', tx['data']):
        raise ValueError('Invalid unsigned browser transaction calldata')
    values = {k: _quantity(tx[k]) for k in ('value', 'nonce', 'gas', 'gasPrice')}
    if (values['value'] > MAX_VALUE or not 21_000 <= values['gas'] <= MAX_GAS or
            not 0 < values['gasPrice'] <= MAX_PRICE or
            values['gas'] * values['gasPrice'] > MAX_NETWORK_FEE):
        raise ValueError('Browser transaction exceeds local fee/value policy')
    return tx


class LocalBrowser:
    def __init__(self, lab, save):
        self.lab, self.save = lab, save
        self.path = Path(lab.home) / 'browser-drafts.json'
        self.items = {}
        if self.path.exists():
            if self.path.stat().st_size > MAX_JOURNAL_BYTES:
                raise ValueError('Browser recovery journal exceeds its bound')
            document = json.loads(self.path.read_text(encoding='utf-8'))
            if (not isinstance(document, dict) or set(document) != {'schema', 'genesis', 'items'} or
                    document['schema'] != 1 or document['genesis'] != lab.genesis or
                    not isinstance(document['items'], dict) or len(document['items']) > MAX_RECORDS):
                raise ValueError('Browser recovery journal belongs to another deployment')
            for key, item in document['items'].items():
                if (not isinstance(key, str) or not IDENTIFIER.fullmatch(key) or not isinstance(item, dict) or
                        not isinstance(item.get('draft'), dict) or item['draft'].get('draft_id') != key or
                        item['draft'].get('account') not in lab.accounts[1:]):
                    raise ValueError('Malformed browser recovery record')
                _transaction({k: v for k, v in item['draft']['transaction'].items() if k != 'chainId'})
                if item.get('hash') is not None:
                    _hash(item['hash'])
            self.items = document['items']

    def persist(self):
        document = {'schema': 1, 'genesis': self.lab.genesis, 'items': self.items}
        if len(json.dumps(document)) > MAX_JOURNAL_BYTES:
            raise ValueError('Browser recovery journal is full; inspect records')
        self.save(self.path, document)

    def manifest(self):
        lab = self.lab
        lab.guard()
        contracts = {}
        allowed = {}
        targets = {role: lab.contracts[role] for role in ('vault', 'nft', 'entry', 'claim_router')}
        assets = copy.deepcopy(getattr(lab, 'input_assets', None) or [
            {'symbol': 'TEST-1', 'address': lab.tokens[0], 'decimals': 18,
             'route_id': '0x' + '0' * 64, 'enabled': True}])
        for index, item in enumerate(assets):
            if item['address'] != ZERO:
                targets['input_' + str(index)] = item['address']
        for role, target in targets.items():
            if not HEX_ADDRESS.fullmatch(target):
                raise ValueError('Invalid fixture target')
            code = lab.rpc('eth_getCode', [target, 'latest'])
            if not isinstance(code, str) or not re.fullmatch(r'0x(?:[a-f0-9]{2}){1,24576}', code):
                raise ValueError('Missing or oversized fixture runtime')
            contracts[role] = {'address': target, 'code_hash': '0x' + keccak256(bytes.fromhex(code[2:])).hex(),
                               'runtime_code': code}
            allowed[target] = code
        return {
            'schema': 1, 'mode': 'LOCAL ANVIL TEST ONLY',
            'chain_id': CHAIN, 'genesis_hash': lab.genesis, 'rpc_url': lab.rpc_url,
            'accounts': lab.accounts[1:], 'contracts': contracts, 'input_assets': assets,
            'pool': lab.pool, 'native_eth_atomic': bool(getattr(lab, 'native_input', False)),
            'mint_value_wei': str(50_000_000_000_000_000),
            'max_gas': MAX_GAS, 'max_gas_price_wei': str(MAX_PRICE),
            'max_network_fee_wei': str(MAX_NETWORK_FEE), 'confirmations': 1,
            'policy': {'chainId': hex(CHAIN), 'genesisHash': lab.genesis,
                       'allowedTargets': allowed, 'maxGas': hex(MAX_GAS), 'maxGasPrice': hex(MAX_PRICE),
                       'maxNetworkFee': hex(MAX_NETWORK_FEE), 'maxValue': hex(MAX_VALUE), 'confirmations': 1},
            'selectors': {name: '0x' + keccak256(signature.encode()).hex()[:8] for name, signature in {
                'mint': 'mintDormant()', 'approve': 'approve(address,uint256)',
                'entry': 'execute((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool))',
                'claim': 'claimBatch((uint256,address,bool)[])'}.items()},
        }

    def prepare(self, payload):
        if not isinstance(payload, dict) or payload.get('action') not in ('mint', 'activate', 'increase', 'claim', 'claim_all'):
            raise ValueError('Unsupported browser holder action')
        self.lab.guard()
        # Never evict a possibly submitted review just because its UI expired.
        if len(self.items) >= MAX_RECORDS:
            raise ValueError('Browser review journal is full; preserve it and inspect before starting another fixture')
        draft = self.lab.wallet.prepare(payload)
        # A browser review can never be executed by the local /action signer.
        self.lab.wallet.drafts.pop(draft['draft_id'])
        _transaction(draft['transaction'])
        now = int(time.time())
        draft = {**draft, 'origin': 'browser', 'requested': copy.deepcopy(payload),
                 'prepared_at': now, 'expires_at': now + draft['expires_in_seconds'],
                 'prepared_chain_at': self.lab.clock(),
                 'transaction': {**draft['transaction'], 'chainId': hex(CHAIN)}}
        self.items[draft['draft_id']] = {'draft': copy.deepcopy(draft), 'hash': None, 'outcome': None}
        try:
            self.persist()
        except Exception:
            del self.items[draft['draft_id']]
            raise
        return draft

    def _match(self, reviewed, transaction):
        if not isinstance(transaction, dict):
            raise ValueError('Transaction is unavailable; retain the saved hash')
        for field in ('from', 'to'):
            if transaction.get(field, '').lower() != reviewed[field]:
                raise ValueError('Observed transaction does not match the reviewed wallet/target')
        if transaction.get('input', '').lower() != reviewed['data']:
            raise ValueError('Observed transaction calldata differs from the review')
        for field in ('value', 'nonce'):
            if _quantity(transaction.get(field)) != _quantity(reviewed[field]):
                raise ValueError('Observed transaction value or nonce differs from the review')
        if transaction_chain_id(transaction) != CHAIN:
            raise ValueError('Observed transaction belongs to another chain')
        # Extensions may add gas-limit headroom without changing the call. The
        # submitted ceiling must still fit the hard local policy; actual paid
        # gas/price below is checked against the tighter original review.
        gas, price = _quantity(transaction.get('gas')), fee_cap(transaction)
        if (not 21_000 <= gas <= MAX_GAS or not 0 < price <= min(MAX_PRICE, _quantity(reviewed['gasPrice'])) or
                gas * price > MAX_NETWORK_FEE):
            raise ValueError('Observed transaction exceeds the hard local gas policy')

    def _receipt(self, transaction_hash, reviewed):
        lab = self.lab
        transaction = lab.rpc('eth_getTransactionByHash', [transaction_hash])
        if transaction is None:
            return None
        if transaction.get('hash') != transaction_hash:
            raise ValueError('RPC returned another transaction')
        self._match(reviewed, transaction)
        receipt = lab.rpc('eth_getTransactionReceipt', [transaction_hash])
        if receipt is None:
            return None
        if (receipt.get('transactionHash') != transaction_hash or
                receipt.get('from', '').lower() != reviewed['from'] or
                receipt.get('to', '').lower() != reviewed['to']):
            raise ValueError('Receipt does not match the reviewed transaction')
        height = _quantity(receipt.get('blockNumber'))
        block_hash = _hash(receipt.get('blockHash'))
        if transaction.get('blockHash') != block_hash or transaction.get('blockNumber') != receipt['blockNumber']:
            raise ValueError('Transaction and receipt disagree on inclusion')
        if _quantity(transaction.get('transactionIndex')) != _quantity(receipt.get('transactionIndex')):
            raise ValueError('Transaction and receipt disagree on transaction index')
        canonical = lab.rpc('eth_getBlockByNumber', [receipt['blockNumber'], False])
        head = lab.block()
        if (not isinstance(canonical, dict) or canonical.get('hash') != block_hash or
                _quantity(canonical.get('number')) != height or
                _quantity(head.get('number')) < height):
            raise ValueError('Receipt is not on the current canonical local chain')
        if receipt.get('status') not in ('0x0', '0x1'):
            raise ValueError('Receipt has no valid execution status')
        gas_used, paid_price = _quantity(receipt.get('gasUsed')), execution_price(transaction, canonical, receipt)
        if (gas_used > min(_quantity(reviewed['gas']), _quantity(transaction['gas'])) or
                paid_price > min(_quantity(reviewed['gasPrice']), fee_cap(transaction)) or
                gas_used * paid_price > _quantity(reviewed['gas']) * _quantity(reviewed['gasPrice'])):
            raise ValueError('Receipt exceeds the reviewed network fee')
        if _quantity(transaction.get('type', '0x0')) == 2:
            receipt = {**receipt, 'reportedEffectiveGasPrice': receipt.get('effectiveGasPrice'),
                       'effectiveGasPrice': hex(paid_price),
                       'feeBasis': 'eip1559-signed-caps-and-canonical-base'}
        return receipt

    def _record(self, item, receipt):
        lab = self.lab
        draft = item['draft']
        key = draft['draft_id']
        fingerprint = json.dumps(['browser', key, item['hash']], separators=(',', ':'))
        prior = lab.operations.items.get(key)
        if prior:
            if prior.get('fingerprint') != fingerprint:
                raise ValueError('Browser observation conflicts with an existing operation')
            if prior['outcome'].get('status') != ('confirmed' if receipt['status'] == '0x1' else 'failed'):
                raise ValueError('Previously observed execution changed; operator review required')
            return prior['outcome']
        if len(lab.operations.items) >= 256:
            raise ValueError('Local operation ledger full; receipt retained for operator recovery')
        # This receipt is already mined. Save its outcome before optional index
        # refresh or mock reveal work. Repeated observations never resubmit it.
        revision = lab.operations.revision + 1
        outcome = {'operation_id': key, 'status': 'confirmed' if receipt['status'] == '0x1' else 'failed',
                   'revision': revision, 'transactions': [item['hash']], 'uncertain': False}
        record = {'fingerprint': fingerprint, 'outcome': outcome}
        new_items = {**lab.operations.items, key: record}
        self.save(lab.operations.path, new_items)
        lab.operations.items = new_items
        lab.operations.revision = revision
        if not any(r['receipt'].get('transactionHash') == item['hash'] for r in lab.receipts):
            lab.receipts.append({'label': 'browser ' + draft['action'], 'transaction': draft['transaction'],
                                 'receipt': receipt, 'gas_quote': draft['network_gas'],
                                 'native_before': None, 'native_after': None})
            self.save(lab.home / 'receipts.json', lab.receipts)
        return outcome

    def _reveal(self, receipt, owner):
        """Complete original mock requests in mint order; never reroll or mint."""
        lab = self.lab
        nft = lab.contracts['nft']
        ids = []
        for log in receipt.get('logs', []):
            topics = log.get('topics')
            if log.get('address') == nft and isinstance(topics, list) and len(topics) == 4 and topics[0] == TRANSFER:
                if topics[1] == '0x' + '0' * 64 and topics[2] == '0x' + '0' * 24 + owner[2:]:
                    ids.append(int(_hash(topics[3]), 16))
        if len(ids) != 1:
            raise ValueError('Mint receipt must identify exactly one recipient NFT')
        identifier = ids[0]
        # Another wallet's transaction may have mined first. Finish existing
        # original requests in order, bounded by the local twenty-NFT fixture.
        end = lab.uint('nft', 'mintOrdinalOf(uint256)', identifier)
        start = lab.uint('nft', 'nextToFinalize()')
        if not 1 <= end <= 20 or not 1 <= start <= 21:
            raise ValueError('Fixture reveal bound exceeded')
        for ordinal in range(start, end + 1):
            current = lab.uint('nft', 'tokenAtOrdinal(uint256)', ordinal)
            if lab.uint('nft', 'traitsReady(uint256)', current):
                continue
            state = lab.read('nft', 'canonicalRandomness(uint256)', current)
            if len(state) != 5 or int(state[0], 16) != current or int(state[3], 16) != 1:
                raise ValueError('Original mock randomness request is unavailable')
            if int(state[4], 16) == 0:
                request = lab.uint('nft', 'requestOf(uint256)', current)
                lab.call(lab.vrf, 'fulfill(uint256,uint256,uint256)', request, ordinal * 721, 12345)
            lab.call('nft', 'finalizeTraits(uint256)', current)
        return str(identifier)

    def confirm(self, payload):
        if not isinstance(payload, dict) or set(payload) != {'draft_id', 'account', 'transaction_hash'}:
            raise ValueError('Expected the saved browser review and transaction hash')
        key = payload['draft_id']
        if not isinstance(key, str) or not IDENTIFIER.fullmatch(key):
            raise ValueError('Invalid browser review identifier')
        transaction_hash = _hash(payload['transaction_hash'])
        item = self.items.get(key)
        if not item or payload['account'] != item['draft']['account']:
            raise ValueError('Unknown browser review or wrong account')
        if item.get('hash') not in (None, transaction_hash):
            raise ValueError('This review is already bound to another transaction hash')
        if any(other_key != key and other.get('hash') == transaction_hash for other_key, other in self.items.items()):
            raise ValueError('Transaction hash is already attached to another review')
        self.lab.guard()
        receipt = self._receipt(transaction_hash, item['draft']['transaction'])
        if receipt is None:
            return {'status': 'pending', 'transaction_hash': transaction_hash, 'uncertain': False}
        old_receipt = item.get('receipt')
        if old_receipt is not None and any(
                old_receipt.get(field) != receipt.get(field)
                for field in ('transactionHash', 'blockHash', 'blockNumber', 'status', 'gasUsed', 'effectiveGasPrice')):
            raise ValueError('Previously observed receipt changed; retain it for operator recovery')
        # No review expiry here: inclusion may occur after the signing deadline.
        # Exact transaction/nonce/canonical checks remain mandatory on every read.
        item['hash'] = transaction_hash
        item['receipt'] = receipt
        self.persist()
        outcome = self._record(item, receipt)
        item['outcome'] = outcome
        self.persist()
        result = {**outcome, 'transaction_hash': transaction_hash, 'receipt': receipt, 'replayed': bool(item.get('observed'))}
        item['observed'] = True
        if outcome['status'] == 'confirmed' and item['draft']['action'] == 'mint' and not self.lab.uncertain:
            try:
                result['minted_token_id'] = self._reveal(receipt, payload['account'])
                result['mock_reveal'] = 'complete'
            except Exception:
                # The user's mint remains confirmed. Do not ask for another
                # mint because optional fixture operator work failed.
                result['mock_reveal'] = 'pending_operator'
        try:
            self.lab.sync()
            result['projection_sync'] = 'complete'
        except Exception:
            result['projection_sync'] = 'retry_read'
        result['uncertain'] = self.lab.uncertain
        self.persist()
        return result
