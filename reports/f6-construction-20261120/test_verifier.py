"""New tamper controls for report-only F6 wire verification; no node or EVM."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('f6_wire_verification', Path(__file__).with_name('verify_execution.py'))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

SENDER = '0x' + 'a0' * 20
FACTORIES = ['0x' + 'b0' * 20, '0x' + 'c0' * 20]
GENESIS = '0x' + '01' * 32
BLOCK = '0x' + '02' * 32
HASH = '0x' + '03' * 32


def example(binding=False):
    accounts = [SENDER] + FACTORIES
    nonces = dict(zip(accounts, ('0x0', '0x3', '0x1')))
    tx = {'hash': HASH, 'from': SENDER, 'to': FACTORIES[0] if binding else None,
          'input': '0x6000', 'gas': hex(125_000), 'nonce': '0x0', 'gasPrice': '0x2',
          'value': '0x0', 'blockNumber': '0x1', 'blockHash': BLOCK, 'transactionIndex': '0x0'}
    receipt = {'transactionHash': HASH, 'blockNumber': '0x1', 'blockHash': BLOCK,
               'transactionIndex': '0x0', 'gasUsed': hex(90_000), 'status': '0x1'}
    row = {'label': 'bind:example' if binding else 'create:example', 'transaction': tx,
           'receipt': receipt, 'estimated_gas': 100_000, 'padded_gas': 125_000,
           'padding_bps': 12_500, 'simulation_return': '0x' if binding else '0x6000',
           'nonce_before': nonces, 'simulation_nonce_unchanged': True}
    header = {'number': '0x1', 'hash': BLOCK, 'parentHash': GENESIS,
              'transactions': [HASH], 'gasUsed': hex(90_000)}
    wire = []

    def add(method, params, result):
        ident = len(wire) + 1
        wire.append(copy.deepcopy({'request': {'jsonrpc': '2.0', 'id': ident, 'method': method, 'params': params},
                                   'response': {'jsonrpc': '2.0', 'id': ident, 'result': result}}))
    for account in accounts:
        add('eth_getTransactionCount', [account, 'latest'], nonces[account])
    full = V.preflight_body(tx, V.CAP)
    padded = V.preflight_body(tx, 125_000)
    add('eth_call', [full, 'latest'], row['simulation_return'])
    add('eth_estimateGas', [full], hex(100_000))
    add('eth_call', [padded, 'latest'], row['simulation_return'])
    for account in accounts:
        add('eth_getTransactionCount', [account, 'latest'], nonces[account])
    add('eth_gasPrice', [], '0x2')
    add('eth_chainId', [], hex(4663))
    add('eth_sendTransaction', [dict(padded, nonce='0x0', gasPrice='0x2')], HASH)
    add('eth_getTransactionReceipt', [HASH], receipt)
    add('eth_getTransactionByHash', [HASH], tx)
    add('eth_getBlockByNumber', ['0x1', False], header)
    add('eth_getBlockByNumber', ['latest', False], header)
    captured = {'schema': 1, 'chain_id': 4663, 'genesis_hash': GENESIS,
                'headers': [copy.deepcopy(header)], 'closing_head': copy.deepcopy(header)}
    return row, wire, accounts, captured


def check_case(row, wire, accounts):
    send = next(i for i, r in enumerate(wire) if r['request']['method'] == 'eth_sendTransaction')
    return V.check_preflight(row, wire, send, -1, accounts)


class CurrentF6WireControls(unittest.TestCase):
    def test_current_build_controls_require_complete_exact_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pins = {}
            for name in V.BUILD_CONTROLS:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(name.encode())
                pins[name] = V.sha(p.read_bytes())
            V.check_build_controls(pins, root)
            with self.assertRaisesRegex(ValueError, 'inventory differs'):
                V.check_build_controls({**pins, '../unreviewed': '0' * 64}, root)
            (root / 'foundry.toml').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                V.check_build_controls(pins, root)

    def test_positive_creation_and_binding_prove_exact_three_stage_review(self):
        for binding in (False, True):
            with self.subTest(binding=binding):
                row, wire, accounts, captured = example(binding)
                result = check_case(row, wire, accounts)
                self.assertEqual(result['preflight_indices'], [3, 4, 5])
                self.assertTrue(result['exact_preflight_nonce_send_and_wire_receipt_verified'])
                self.assertTrue(V.check_headers([row], wire, captured, GENESIS)['all_numbered_headers_and_closing_tip_wire_bound'])

    def test_missing_or_reordered_preflight_is_rejected(self):
        for mutation in ('remove', 'reorder'):
            with self.subTest(mutation=mutation):
                row, wire, accounts, _ = example()
                if mutation == 'remove':
                    del wire[4]
                else:
                    wire[3], wire[4] = wire[4], wire[3]
                with self.assertRaisesRegex(ValueError, 'preflight stages|stage order'):
                    check_case(row, wire, accounts)

    def test_wrong_cap_stale_estimate_and_padded_fields_are_rejected(self):
        for stage in (3, 4, 5):
            with self.subTest(stage=stage):
                row, wire, accounts, _ = example()
                wire[stage]['request']['params'][0]['gas'] = '0x1'
                with self.assertRaisesRegex(ValueError, 'preflight fields differ'):
                    check_case(row, wire, accounts)
        row, wire, accounts, _ = example()
        wire[4]['response']['result'] = hex(100_001)
        with self.assertRaisesRegex(ValueError, 'Estimate differs'):
            check_case(row, wire, accounts)

    def test_sender_and_factory_nonce_changes_are_rejected(self):
        for index in (6, 7, 8):
            with self.subTest(nonce_read=index):
                row, wire, accounts, _ = example()
                wire[index]['response']['result'] = '0x4'
                with self.assertRaisesRegex(ValueError, 'simulation nonce changed'):
                    check_case(row, wire, accounts)

    def test_missing_reordered_or_pending_nonce_reads_are_rejected(self):
        for mutation in ('pending', 'reordered', 'missing'):
            with self.subTest(mutation=mutation):
                row, wire, accounts, _ = example()
                if mutation == 'pending':
                    wire[0]['request']['params'][1] = 'pending'
                elif mutation == 'reordered':
                    wire[0], wire[1] = wire[1], wire[0]
                else:
                    del wire[0]
                with self.assertRaisesRegex(ValueError, 'Nonce read identity|bracketed nonce'):
                    check_case(row, wire, accounts)

    def test_gasprice_nonce_and_submission_freeze_cannot_drift(self):
        for mutation in ('gasprice_read', 'nonce', 'unexpected_field', 'included_gas'):
            with self.subTest(mutation=mutation):
                row, wire, accounts, _ = example()
                if mutation == 'gasprice_read':
                    wire[9]['response']['result'] = '0x3'
                elif mutation == 'nonce':
                    wire[11]['request']['params'][0]['nonce'] = '0x1'
                elif mutation == 'unexpected_field':
                    wire[11]['request']['params'][0]['maxFeePerGas'] = '0x2'
                else:
                    row['transaction']['gas'] = '0x1'
                with self.assertRaisesRegex(ValueError, 'Submission fields differ|Included transaction envelope'):
                    check_case(row, wire, accounts)

    def test_detached_transaction_or_receipt_is_rejected(self):
        for index in (12, 13):
            with self.subTest(index=index):
                row, wire, accounts, _ = example()
                wire[index]['response']['result']['blockHash'] = '0x' + '04' * 32
                with self.assertRaisesRegex(ValueError, 'detached from original wire'):
                    check_case(row, wire, accounts)

    def test_forked_receipt_or_header_chain_is_rejected(self):
        for mutation in ('receipt', 'parent', 'latest', 'missing_wire', 'header_order'):
            with self.subTest(mutation=mutation):
                row, wire, _, captured = example()
                if mutation == 'receipt':
                    row['receipt']['blockHash'] = '0x' + '04' * 32
                elif mutation == 'parent':
                    captured['headers'][0]['parentHash'] = '0x' + '04' * 32
                elif mutation == 'latest':
                    captured['closing_head']['hash'] = '0x' + '04' * 32
                elif mutation == 'missing_wire':
                    wire[14]['response']['result']['hash'] = '0x' + '04' * 32
                else:
                    captured['headers'][0]['number'] = '0x2'
                with self.assertRaisesRegex(ValueError, 'different canonical block|missing/reordered/forked|Closing tip differs|absent/reordered'):
                    V.check_headers([row], wire, captured, GENESIS)

    def test_wrong_block_transaction_inventory_gas_and_tip_are_rejected(self):
        for mutation in ('transactions', 'gas', 'tip_wire'):
            with self.subTest(mutation=mutation):
                row, wire, _, captured = example()
                if mutation == 'transactions':
                    captured['headers'][0]['transactions'] = []
                elif mutation == 'gas':
                    captured['headers'][0]['gasUsed'] = '0x1'
                else:
                    wire[15]['response']['result']['hash'] = '0x' + '04' * 32
                with self.assertRaisesRegex(ValueError, 'transaction inventory|block gas|tip missing'):
                    V.check_headers([row], wire, captured, GENESIS)

    def test_duplicate_json_and_noncanonical_quantities_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            V.loads(b'{"schema":1,"schema":2}')
        for value in ('0x00', True, 1, '1', '-1', '0x' + '1' * 65):
            with self.subTest(value=value), self.assertRaises(ValueError):
                V.quantity(value)


if __name__ == '__main__':
    unittest.main()
