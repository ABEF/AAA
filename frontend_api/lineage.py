"""Bounded, explicitly pinned same-chain predecessor claim history.

This verifies the recorded handoff against canonical RPC observations, not a
cryptographic consensus proof. No peer discovery, new endpoint or asset movement.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from frontend_api.history import HistoryError, merge_conversions, conversion_report
from zzz_ops.abi import address, decode_words, keccak256

MAX_PREDECESSORS = 8
MAX_TOTAL_EVENTS = 1_000_000
MAX_RECEIPT_LOGS = 4096
RETIRED = '0x' + keccak256(b'Retired(bytes32,address,bytes32)').hex()
ACTIVATED = '0x' + keccak256(b'Activated(bytes32,address,bytes32)').hex()


@dataclass(frozen=True)
class Predecessor:
    projection: Any
    transaction: str


class Lineage:
    def __init__(self, items, current, config):
        from frontend_api.service import Projection, _hash, _keys

        if not isinstance(items, list) or not 1 <= len(items) <= MAX_PREDECESSORS or current.history is None:
            raise ValueError('Predecessors require current history and one to eight reviewed deployments')
        self.entries = []
        self.descriptors = dict(current.assets)
        contracts = {c.address for c in current.contracts.values()}
        total_events = current.history.max_events
        for item in items:
            _keys(item, {'deployment_block', 'deployment_block_hash', 'contracts', 'assets',
                         'history', 'retirement_transaction_hash'}, 'predecessor')
            # Do not inherit a successor's new ledger ABI/profile or converter
            # into an older deployment. Historical event replay needs no new getters.
            previous_config = {k: v for k, v in config.items() if k not in ('predecessors', 'history', 'royalty_reporting')}
            previous_config.update({k: v for k, v in item.items() if k != 'retirement_transaction_hash'})
            previous = Projection(previous_config, current.rpc, clock=current.clock)
            addresses = {c.address for c in previous.contracts.values()}
            if addresses & contracts:
                raise ValueError('Repeated or overlapping deployment identities in predecessor inventory')
            contracts.update(addresses)
            total_events += previous.history.max_events
            for asset, descriptor in previous.assets.items():
                if asset in self.descriptors and descriptor.decimals != self.descriptors[asset].decimals:
                    raise ValueError('Historical asset decimals differ; raw claim units cannot be combined')
                self.descriptors.setdefault(asset, descriptor)
            self.entries.append(Predecessor(previous, _hash(item['retirement_transaction_hash'])))
        if total_events > MAX_TOTAL_EVENTS:
            raise ValueError('Combined current/predecessor replay exceeds the total event budget')
        # Asset descriptors may vary across epochs, but never impersonate a
        # pinned protocol module in another deployment.
        if set(self.descriptors) & contracts:
            raise ValueError('Historical asset collides with a pinned deployment contract')

    @staticmethod
    def _receipt(current, entry, destination, header):
        from frontend_api.service import _address_word, _hash, _quantity

        raw = current.rpc.call('eth_getTransactionReceipt', [entry.transaction])
        if not isinstance(raw, dict):
            raise HistoryError('Canonical retirement receipt is unavailable')
        try:
            number = _quantity(raw['blockNumber'])
            tx_index = _quantity(raw['transactionIndex'])
            digest = _hash(raw['blockHash'])
            if (_quantity(raw['status']) != 1 or _hash(raw['transactionHash']) != entry.transaction or
                    not entry.projection.start <= number <= header['number'] or destination.start > number):
                raise ValueError('Retirement receipt is not confirmed within deployment bounds')
            cutoff = current._header(hex(number))
            if cutoff['hash'] != digest or cutoff['timestamp'] > header['timestamp']:
                raise ValueError('Retirement receipt is orphaned or has invalid timing')
            logs = raw['logs']
            if not isinstance(logs, list) or not 2 <= len(logs) <= MAX_RECEIPT_LOGS:
                raise ValueError('Retirement receipt log count is outside bounds')
            source = entry.projection
            expected = {(source.contracts['handoff'].address, RETIRED): destination.contracts['access'].address,
                        (destination.contracts['handoff'].address, ACTIVATED): source.contracts['access'].address}
            found = {}
            last_index = -1
            for log in logs:
                if not isinstance(log, dict) or log.get('removed', False) is not False:
                    raise ValueError('Malformed or removed retirement log')
                index = _quantity(log['logIndex'])
                if (index <= last_index or _quantity(log['blockNumber']) != number or
                        _hash(log['blockHash']) != digest or _hash(log['transactionHash']) != entry.transaction or
                        _quantity(log['transactionIndex']) != tx_index):
                    raise ValueError('Retirement log does not belong to the receipt')
                last_index = index
                emitter = address(log['address'])
                topics = log['topics']
                if not isinstance(topics, list) or len(topics) > 4:
                    raise ValueError('Invalid receipt topics')
                # All topics are fixed 32-byte words; zero is valid for unrelated events.
                for topic in topics:
                    if not isinstance(topic, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', topic):
                        raise ValueError('Invalid receipt topic')
                key = (emitter, topics[0].lower() if topics else None)
                if key not in expected:
                    continue
                if key in found or len(topics) != 3 or _address_word(topics[2][2:]) != expected[key]:
                    raise ValueError('Ambiguous or mismatched handoff event')
                data = decode_words(log['data'])
                if len(data) != 1:
                    raise ValueError('Unexpected handoff event data')
                found[key] = (_hash(topics[1]), _hash('0x' + data[0]), index)
            retired = found[(source.contracts['handoff'].address, RETIRED)]
            activated = found[(destination.contracts['handoff'].address, ACTIVATED)]
            if retired[:2] != activated[:2] or activated[2] >= retired[2]:
                raise ValueError('Retirement and activation do not commit the same ordered handoff')
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise HistoryError('Retirement receipt or handoff events failed verification') from exc
        return cutoff, (number, tx_index, retired[2]), retired[0], retired[1]

    def claimed(self, current, header, block, lifecycle, local_history, nft_id, ordinal):
        return self.financial(current, header, block, lifecycle, local_history, nft_id, ordinal)['previously_claimed']

    def financial(self, current, header, block, lifecycle, local_history, nft_id, ordinal):
        from frontend_api.service import _hash

        if local_history is None or lifecycle['predecessor_controller'] is None:
            raise HistoryError('Predecessor inventory does not match the current deployment')
        projections = [entry.projection for entry in self.entries] + [current]
        lives = []
        anchors = []
        for entry in self.entries:
            p = entry.projection
            anchor = p._header(hex(p.start))
            if anchor['hash'] != p.start_hash or p.start > header['number']:
                raise HistoryError('Predecessor deployment anchor is not canonical')
            anchors.append((p.start, anchor))
            life = p._verify_deployment(block, allow_locked=True)
            if life['state'] != 'retired' or life['origin'] != lifecycle['origin']:
                raise HistoryError('Predecessor is not retired in the same original identity namespace')
            lives.append(life)
        lives.append(lifecycle)
        if lives[0]['predecessor_controller'] is not None:
            raise HistoryError('Predecessor inventory omits the original deployment')

        totals = {asset: amounts for (identifier, asset), amounts in local_history.claims.items()
                  if identifier == nft_id}
        conversions = {}
        merge_conversions(conversions, local_history.conversions, nft_id)
        receipts = []
        previous_order = None
        for index, entry in enumerate(self.entries):
            source, destination = projections[index:index + 2]
            if (lives[index]['successor_controller'] != destination.contracts['access'].address or
                    lives[index + 1]['predecessor_controller'] != source.contracts['access'].address):
                raise HistoryError('Predecessor order does not match both sealed handoff directions')
            cutoff, order, handoff_id, state_root = self._receipt(current, entry, destination, header)
            if previous_order is not None and order <= previous_order:
                raise HistoryError('Retirement chronology is reversed or duplicated')
            previous_order = order
            for signature, expected in (('handoffId()', handoff_id), ('stateRoot()', state_root)):
                actual = _hash('0x' + source._call(source.contracts['handoff'].address, signature, block=block)[0])
                if actual != expected:
                    raise HistoryError('Retirement event differs from the terminal source commitment')
            at_cutoff = {'blockHash': cutoff['hash'], 'requireCanonical': True}
            # The event emitter/controller code must also match at the historical
            # transition, not merely at the current projection block.
            for peer in (source, destination):
                for role in ('access', 'handoff'):
                    contract = peer.contracts[role]
                    peer._code(contract.address, contract.code_hash, at_cutoff)
            lp_assets, royalty_assets = source._admitted(at_cutoff)
            history = source._history_snapshot(cutoff, at_cutoff, lp_assets, royalty_assets)
            merge_conversions(conversions, history.conversions, nft_id)
            old_ordinal = source._uint('nft', 'mintOrdinalOf(uint256)', nft_id, block=at_cutoff)
            if old_ordinal:
                if (old_ordinal != ordinal or nft_id not in history.owners or
                        source._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=at_cutoff) != nft_id):
                    raise HistoryError('Historical NFT identity differs from the successor')
            elif nft_id in history.owners or ordinal <= history.provenance['minted_count']:
                raise HistoryError('Historical NFT absence contradicts the mint inventory')
            for (identifier, asset), (lp, royalties) in history.claims.items():
                if identifier == nft_id:
                    old_lp, old_royalties = totals.get(asset, (0, 0))
                    totals[asset] = (old_lp + lp, old_royalties + royalties)
            anchors.append((cutoff['number'], cutoff))
            parent = source._header(hex(source.history.start - 1))
            created = source._header(hex(source.history.start))
            if (parent['hash'] != source.history.parent or
                    created['hash'] != history.provenance['start_block_hash']):
                raise HistoryError('Historical creation anchor changed during replay')
            anchors.append((source.history.start - 1, parent))
            anchors.append((source.history.start, created))
            receipts.append({'controller': source.contracts['access'].address,
                             'successor_controller': destination.contracts['access'].address,
                             'retirement_transaction_hash': entry.transaction,
                             'retirement_block': cutoff['number'], 'retirement_block_hash': cutoff['hash'],
                             'handoff_id': handoff_id, 'state_root': state_root,
                             'history': dict(history.provenance)})

        # Never return a total based on an orphaned archival header after a
        # provider failover. The caller then checks current depth/freshness.
        for number, expected in anchors:
            if current._header(hex(number)) != expected:
                raise HistoryError('Historical lineage anchor changed during replay')
        assets = []
        for asset, descriptor in sorted(self.descriptors.items()):
            lp, royalties = totals.get(asset, (0, 0))
            assets.append({'asset': asset, 'symbol': descriptor.symbol, 'decimals': descriptor.decimals,
                           'lp_raw': str(lp), 'royalties_raw': str(royalties), 'total_raw': str(lp + royalties)})
        claimed = {'available': True, 'assets': assets,
                'scope': 'Lifetime NFT claims across the complete pinned same-chain deployment lineage, '
                         'including LP and royalties paid to every past/current owner.',
                'provenance': {'current_history': dict(local_history.provenance), 'predecessors': receipts,
                               'lineage_complete': True, 'verification': 'Pinned code, canonical RPC receipts and indexed history; not a consensus proof.',
                               'protocol_finalized': False}}
        return {'previously_claimed': claimed,
                'royalty_conversions': conversion_report(conversions, nft_id, self.descriptors, claimed['provenance'])}
