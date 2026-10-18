"""Claim continuity through real local indexer databases and canonical RPC fixtures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from frontend_api.history import CLAIMED, TRANSFER, HistoryError, ZERO
from frontend_api.lineage import ACTIVATED, RETIRED
from frontend_api.service import Projection, ProjectionError
from indexer.monitor import Indexer
from tests_python.test_frontend_api import MockRPC, addr, configuration, words
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError


def h(n):
    return '0x' + f'{100000 + n:064x}'


class LineageRPC:
    def __init__(self, directory, count=3):
        self.head = 110
        self.calls = []
        self.logs = []
        self.receipts = {}
        self.responses = {}
        self.codes = {}
        self.birth = {}
        self.configs = []
        self.indexes = []
        template = MockRPC()
        self.nft_id = template.nft_id
        roles = tuple(configuration()['contracts'])
        for index in range(count):
            config = configuration()
            start = 10 + index * 10
            mapping = {addr(n): addr(n + 100 * index) for n in range(1, 9)}
            config['deployment_block'] = start
            config['deployment_block_hash'] = h(start)
            for n, role in enumerate(roles, 1):
                target = mapping[addr(n)]
                code = bytes([0x60, n, index])
                config['contracts'][role] = {'address': target, 'code_hash': '0x' + keccak256(code).hex()}
                self.codes[target] = '0x' + code.hex()
                self.birth[target] = start
            for (target, data), result in template.responses.items():
                translated = [mapping.get('0x' + result[n + 24:n + 64], None) if len(result[n:n + 64]) == 64 else None
                              for n in range(2, len(result), 64)]
                chunks = [words(value)[2:] if value else result[2 + i * 64:2 + (i + 1) * 64]
                          for i, value in enumerate(translated)]
                # Only ABI address return words are translated. Tiny integer
                # status/trait words are left unchanged below by explicit setup.
                self.responses[(mapping.get(target, target), data)] = '0x' + ''.join(chunks)
            self.configs.append(config)
            get = lambda role: config['contracts'][role]['address']
            self.put(get('access'), 'isSealed()', 1)
            for signature in ('canonicalSettling()', 'paused()'):
                self.put(get('access'), signature, 0)
            self.put(get('access'), 'canonicalState()', 0 if index == count - 1 else 3)
            self.put(get('access'), 'preparationActive()', int(index != count - 1))
            self.put(get('handoff'), 'phase()', 5 if index == count - 1 and index else 3 if count > 1 else 0)
            self.put(get('handoff'), 'incomingSource()', ZERO if not index else addr(1 + 100 * (index - 1)))
            self.put(get('handoff'), 'destinationController()', addr(1 + 100 * (index + 1)) if index < count - 1 else ZERO)
            self.put(get('vault_canonical'), 'originChain()', 31337)
            self.put(get('vault_canonical'), 'originVault()', addr(3))
            self.put(get('vault'), 'canonicalChainId()', 31337)
            self.put(get('nft'), 'mintedCount()', 1)
            for signature, result in (('mintOrdinalOf(uint256)', 1), ('traitsReady(uint256)', 1),
                                       ('rarityOf(uint256)', 1), ('paletteOf(uint256)', 24), ('patternOf(uint256)', 2)):
                self.put(get('nft'), signature, result, self.nft_id)
            self.put(get('nft'), 'tokenAtOrdinal(uint256)', self.nft_id, 1)
            self.put(get('nft'), 'ownerOf(uint256)', addr(30), self.nft_id)
            for signature, result in (('nftStatus(uint256)', 1), ('nftBucket(uint256)', 5), ('sharesOf(uint256)', 10**36)):
                self.put(get('vault'), signature, result, self.nft_id)
            self.put(get('royalties'), 'weightOf(uint256)', 2, self.nft_id)
            # Integer status words must not be mistaken for translated addresses.
            # Imported local custody uses the successor Vault, not originVault.
            self.responses[(get('vault'), calldata('group(uint256)', 5))] = words(
                444,9,0,0,2000*10**18,2**96,990,1,31337,get('vault'),get('handoff'),addr(20),addr(21),31337,get('vault'))
            self.responses[(get('nft'), calldata('currentLPValue(uint256)', self.nft_id))] = words(1, 1432 * 10**18)
            for target, assets in ((get('rewards'), [addr(20), addr(21)]), (get('royalties'), [ZERO, addr(21)])):
                self.put(target, 'assetCount()', len(assets))
                for n, asset in enumerate(assets): self.put(target, 'assets(uint256)', asset, n)
            # Import transfers are not economic claims. Each deployment has
            # different owners claiming before a final transfer back to owner30.
            minted_at = 11 if not index else 30 * index - 1
            owner = addr(30 + index)
            self.log(get('nft'), minted_at, [TRANSFER, words(ZERO), words(owner), words(self.nft_id)])
            self.log(get('rewards'), minted_at + 2, [CLAIMED, words(self.nft_id), words(addr(20)), words(owner)], words(10 + index * 20))
            self.log(get('royalties'), minted_at + 3, [CLAIMED, words(self.nft_id), words(ZERO), words(owner)], words(20 + index * 20))
            if owner != addr(30):
                self.log(get('nft'), minted_at + 4, [TRANSFER, words(owner), words(addr(30)), words(self.nft_id)])
            config['history'] = {'database': str(directory / f'history-{index}.sqlite'),
                                  'start_block': start, 'start_parent_hash': h(start - 1),
                                  'contracts': [get('nft'), get('rewards'), get('royalties')], 'max_events': 1000}

        self.codes.update({addr(20): '0x' + b'ZZZ'.hex(), addr(21): '0x' + b'USDC'.hex()})
        self.birth.update({addr(20): 0, addr(21): 0})
        for target, decimals in ((20, 18), (21, 6)): self.put(addr(target), 'decimals()', decimals)
        for index in range(count - 1):
            source, dest = self.configs[index:index + 2]
            block = 30 * (index + 1)
            tx = h(2000 + index)
            handoff, state = h(3000 + index), h(4000 + index)
            source_handoff = source['contracts']['handoff']['address']
            destination_handoff = dest['contracts']['handoff']['address']
            self.put(source_handoff, 'handoffId()', handoff)
            self.put(source_handoff, 'stateRoot()', state)
            events = [self.raw(destination_handoff, block, 100, [ACTIVATED, handoff, words(source['contracts']['access']['address'])], words(state), tx),
                      self.raw(source_handoff, block, 101, [RETIRED, handoff, words(dest['contracts']['access']['address'])], words(state), tx)]
            self.receipts[tx] = {'status': '0x1', 'transactionHash': tx, 'blockHash': h(block),
                                 'blockNumber': hex(block), 'transactionIndex': '0x0', 'logs': events}
        for index, config in enumerate(self.configs):
            target = 30 * (index + 1) if index < count - 1 else 99
            self.head = target + 11
            settings = dict(config['history'], chain_id=31337, rpc_urls=['http://127.0.0.1:8545'],
                            confirmations=12, block_chunk=200, max_reorg_depth=100, poll_seconds=1)
            settings.pop('max_events')
            writer = Indexer(settings, self)
            self.indexes.append(writer)
            writer.step()
        self.head = 110
        self.config = copy.deepcopy(self.configs[-1])
        self.config['predecessors'] = [dict({k: c[k] for k in ('deployment_block', 'deployment_block_hash', 'contracts', 'assets', 'history')},
                                           retirement_transaction_hash=h(2000 + index))
                                       for index, c in enumerate(self.configs[:-1])]

    def close(self):
        for writer in self.indexes: writer.close()

    def put(self, target, signature, result, *args):
        self.responses[(target, calldata(signature, *args))] = words(result)

    def raw(self, emitter, number, index, topics, data='0x', tx=None):
        return {'address': emitter, 'blockNumber': hex(number), 'blockHash': h(number),
                'transactionHash': tx or h(1000 + number), 'transactionIndex': '0x0',
                'logIndex': hex(index), 'topics': topics, 'data': data, 'removed': False}

    def log(self, emitter, number, topics, data='0x'):
        index = sum(int(log['blockNumber'], 16) == number for log in self.logs)
        self.logs.append(self.raw(emitter, number, index, topics, data))

    def call(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        if method == 'eth_chainId': return 31337
        if method == 'eth_blockNumber': return hex(self.head)
        if method == 'eth_getBlockByNumber':
            n = int(params[0], 16)
            return {'number': hex(n), 'hash': h(n), 'parentHash': h(n - 1), 'timestamp': hex(891 + n)}
        if method == 'eth_getLogs':
            q = params[0]; low, high = int(q['fromBlock'], 16), int(q['toBlock'], 16)
            return copy.deepcopy([l for l in self.logs if low <= int(l['blockNumber'], 16) <= high and l['address'] in q['address']])
        if method == 'eth_getTransactionReceipt': return copy.deepcopy(self.receipts.get(params[0]))
        if method in ('eth_call', 'eth_getCode'):
            selector = params[-1]
            assert set(selector) == {'blockHash', 'requireCanonical'} and selector['requireCanonical'] is True
            n = int(selector['blockHash'], 16) - 100000
            if method == 'eth_getCode': return self.codes[params[0]] if n >= self.birth[params[0]] else '0x'
            return self.responses[(params[0]['to'], params[0]['data'])]
        raise AssertionError('Unexpected RPC method ' + method)


class ClaimLineageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.rpc = LineageRPC(Path(self.temp.name))
        self.p = Projection(self.rpc.config, self.rpc, clock=lambda: 1000)

    def tearDown(self):
        self.rpc.close(); self.temp.cleanup()

    def read(self): return self.p.nft(str(self.rpc.nft_id))

    def test_two_handoffs_sum_both_ledgers_and_all_past_owners(self):
        result = self.read()
        claimed = result['previously_claimed']
        self.assertTrue(claimed['available'])
        assets = {x['asset']: x for x in claimed['assets']}
        self.assertEqual(assets[addr(20)]['lp_raw'], '90')
        self.assertEqual(assets[ZERO]['royalties_raw'], '120')
        self.assertEqual(assets[addr(21)]['total_raw'], '0')
        self.assertEqual(len(claimed['provenance']['predecessors']), 2)
        self.assertTrue(claimed['provenance']['lineage_complete'])
        self.assertNotIn('previously_claimed', result['unavailable_metrics'])
        # Closed predecessor indexes are sufficient; they do not ingest empty
        # blocks forever after their terminal retirement receipt.
        self.assertEqual(claimed['provenance']['predecessors'][0]['history']['through_block'], 30)
        self.assertEqual(claimed['provenance']['predecessors'][1]['history']['through_block'], 60)

    def test_no_configuration_preserves_explicit_unavailable_balance(self):
        config = copy.deepcopy(self.rpc.config); del config['predecessors']
        result = Projection(config, self.rpc, clock=lambda: 1000).nft(str(self.rpc.nft_id))
        self.assertFalse(result['previously_claimed']['available'])
        self.assertIsNone(result['previously_claimed']['assets'])
        self.assertGreater(int(result['claimable']['lp'][0]['raw']), 0)

    def test_history_totals_do_not_change_claimable_balances(self):
        config = copy.deepcopy(self.rpc.config); del config['predecessors']
        local = Projection(config, self.rpc, clock=lambda: 1000).nft(str(self.rpc.nft_id))
        self.assertEqual(self.read()['claimable'], local['claimable'])

    def insert(self, deployment, log):
        with self.rpc.indexes[deployment].db:
            self.rpc.indexes[deployment].db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                (31337, int(log['blockNumber'], 16), log['blockHash'], log['transactionHash'],
                 int(log['logIndex'], 16), log['address'], 'UNTRUSTED_LABEL', '{}', json.dumps(log)))

    def test_nft_minted_after_handoff_has_no_fabricated_predecessor_claims(self):
        new_id = int.from_bytes(keccak256(b'later NFT identity'), 'big')
        old_word, new_word = f'{self.rpc.nft_id:064x}', f'{new_id:064x}'
        current_addresses = {x['address'] for x in self.rpc.config['contracts'].values()}
        for (target, data), result in list(self.rpc.responses.items()):
            if target in current_addresses and old_word in data:
                self.rpc.responses[(target, data.replace(old_word, new_word))] = result
        self.rpc.put(addr(202), 'mintedCount()', 2)
        self.rpc.put(addr(202), 'mintOrdinalOf(uint256)', 2, new_id)
        self.rpc.put(addr(202), 'tokenAtOrdinal(uint256)', new_id, 2)
        for target in (2, 102): self.rpc.put(addr(target), 'mintOrdinalOf(uint256)', 0, new_id)
        self.insert(2, self.rpc.raw(addr(202), 80, 0, [TRANSFER, words(ZERO), words(addr(30)), words(new_id)]))
        self.insert(2, self.rpc.raw(addr(204), 81, 0, [CLAIMED, words(new_id), words(addr(20)), words(addr(30))], words(5)))
        result = self.p.nft(str(new_id))['previously_claimed']
        assets = {x['asset']: x for x in result['assets']}
        self.assertEqual(assets[addr(20)]['lp_raw'], '5')
        self.assertEqual(assets[ZERO]['royalties_raw'], '0')

    def test_old_claim_asset_is_retained_even_when_not_in_current_admission(self):
        self.insert(0, self.rpc.raw(addr(5), 15, 0, [CLAIMED, words(self.rpc.nft_id), words(addr(21)), words(addr(30))], words(77)))
        config = copy.deepcopy(self.rpc.config)
        config['assets'] = [a for a in config['assets'] if a['address'] != addr(21)]
        self.rpc.put(addr(204), 'assetCount()', 1)
        self.rpc.put(addr(205), 'assetCount()', 1)
        result = Projection(config, self.rpc, clock=lambda: 1000).nft(str(self.rpc.nft_id))
        assets = {x['asset']: x for x in result['previously_claimed']['assets']}
        self.assertEqual(assets[addr(21)]['royalties_raw'], '77')
        self.assertEqual(assets[addr(21)]['decimals'], 6)
        self.assertNotIn(addr(21), {x['asset'] for x in result['claimable']['lp']})

    def test_omitted_original_or_reordered_predecessor_is_rejected(self):
        for entries in (self.rpc.config['predecessors'][1:], list(reversed(self.rpc.config['predecessors']))):
            config = copy.deepcopy(self.rpc.config); config['predecessors'] = entries
            with self.assertRaises(HistoryError): Projection(config, self.rpc, clock=lambda: 1000).nft(str(self.rpc.nft_id))

    def test_duplicate_unknown_and_unbounded_configuration_is_rejected(self):
        changes = [[], self.rpc.config['predecessors'] * 2, self.rpc.config['predecessors'] * 5]
        for entries in changes:
            config = copy.deepcopy(self.rpc.config); config['predecessors'] = entries
            with self.assertRaises(ValueError): Projection(config, self.rpc)
        for key in ('rpc_urls', 'chain_id', 'predecessors'):
            config = copy.deepcopy(self.rpc.config); config['predecessors'][0][key] = []
            with self.assertRaises(ValueError): Projection(config, self.rpc)
        config = copy.deepcopy(self.rpc.config); config['predecessors'][0]['history']['max_events'] = 1_000_000
        with self.assertRaises(ValueError): Projection(config, self.rpc)

    def test_inconsistent_asset_units_are_rejected(self):
        config = copy.deepcopy(self.rpc.config); config['predecessors'][0]['assets'][1]['decimals'] = 6
        with self.assertRaisesRegex(ValueError, 'decimals'): Projection(config, self.rpc)

    def test_missing_or_unsuccessful_or_orphaned_receipt_is_rejected(self):
        tx = h(2000); original = copy.deepcopy(self.rpc.receipts[tx])
        variants = [None, dict(original, status='0x0'), dict(original, blockHash=h(300)),
                    dict(original, transactionHash=h(333)), dict(original, blockNumber=hex(100)),
                    dict(original, logs=[])]
        for receipt in variants:
            with self.subTest(receipt=receipt and receipt.get('status')):
                self.rpc.receipts[tx] = receipt
                with self.assertRaises((HistoryError, ProjectionError)): self.read()
        self.rpc.receipts[tx] = original

    def test_mismatched_roots_peers_and_receipt_log_identity_are_rejected(self):
        original = copy.deepcopy(self.rpc.receipts[h(2000)])
        for field, value in (('data', words(h(999))), ('blockHash', h(999)), ('transactionHash', h(999)),
                             ('transactionIndex', '0x1'), ('removed', True), ('logIndex', '0x64')):
            with self.subTest(field=field):
                receipt = copy.deepcopy(original); receipt['logs'][1][field] = value
                self.rpc.receipts[h(2000)] = receipt
                with self.assertRaises(HistoryError): self.read()
        receipt = copy.deepcopy(original); receipt['logs'][1]['topics'][2] = words(addr(999))
        self.rpc.receipts[h(2000)] = receipt
        with self.assertRaises(HistoryError): self.read()

    def test_duplicate_retirement_or_activation_is_rejected(self):
        receipt = self.rpc.receipts[h(2000)]
        duplicate = copy.deepcopy(receipt['logs'][1]); duplicate['logIndex'] = '0x66'
        receipt['logs'].append(duplicate)
        with self.assertRaises(HistoryError): self.read()

    def test_current_source_commitment_and_successor_binding_are_required(self):
        for signature, value in (('stateRoot()', h(999)), ('handoffId()', h(999)), ('destinationController()', addr(999))):
            with self.subTest(signature=signature):
                key = (addr(7), calldata(signature)); original = self.rpc.responses[key]
                self.rpc.put(addr(7), signature, value)
                with self.assertRaises(HistoryError): self.read()
                self.rpc.responses[key] = original

    def test_nonretired_source_and_wrong_origin_are_rejected(self):
        for target, signature, value in ((1, 'canonicalState()', 0), (8, 'originVault()', addr(999)), (108, 'originVault()', addr(999))):
            with self.subTest(signature=signature):
                key = (addr(target), calldata(signature)); original = self.rpc.responses[key]
                self.rpc.put(addr(target), signature, value)
                with self.assertRaises((HistoryError, ProjectionError)): self.read()
                self.rpc.responses[key] = original

    def test_wrong_archival_code_or_unavailable_archive_fails_closed(self):
        original = self.rpc.call
        def changed(method, args):
            if method == 'eth_getCode' and args[0] == addr(107) and args[1]['blockHash'] == h(30): return '0x6000'
            return original(method, args)
        self.rpc.call = changed
        with self.assertRaises(ProjectionError): self.read()
        def unavailable(method, args):
            if method == 'eth_getCode' and args[1]['blockHash'] == h(30): raise RpcError('archive unavailable')
            return original(method, args)
        self.rpc.call = unavailable
        with self.assertRaises(RpcError): self.read()

    def test_old_ordinal_mismatch_is_rejected(self):
        self.rpc.put(addr(2), 'mintOrdinalOf(uint256)', 2, self.rpc.nft_id)
        with self.assertRaises(HistoryError): self.read()

    def test_missing_predecessor_ingestion_fails_without_partial_total(self):
        with self.rpc.indexes[0].db:
            self.rpc.indexes[0].db.execute('DELETE FROM blocks WHERE number=20')
        with self.assertRaises(HistoryError): self.read()

    def test_final_historical_anchor_change_is_rejected(self):
        original = self.rpc.call; count = 0
        def reorg(method, args):
            nonlocal count
            result = original(method, args)
            if method == 'eth_getBlockByNumber' and args[0] == hex(30):
                count += 1
                if count >= 4: result['hash'] = h(999)
            return result
        self.rpc.call = reorg
        with self.assertRaises((HistoryError, ProjectionError)): self.read()


if __name__ == '__main__': unittest.main()
