"""Focused offline regressions for the selected-pool evidence reader; no RPC access."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'hookless_observer', Path(__file__).resolve().parents[1] / 'scripts/verify-hookless-pool.py')
OBSERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OBSERVER)


def encoded(*values):
    return '0x' + ''.join(f'{v:064x}' for v in values)


def reply(identifier, result):
    return dict(jsonrpc='2.0', id=identifier, result=result)


class HooklessObserverTests(unittest.TestCase):
    block = 96427989
    block_hash = '0x' + 'ab' * 32

    def fixture(self):
        header = dict(number=hex(self.block), hash=self.block_hash)
        topic = '0x' + OBSERVER.keccak256(
            b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
        log = dict(address=OBSERVER.ADDRESSES['core'], removed=False,
                   blockNumber=hex(OBSERVER.INITIALIZATION_BLOCK),
                   transactionHash=OBSERVER.INITIALIZATION_TX,
                   topics=[topic, OBSERVER.POOL, encoded(0), encoded(int(OBSERVER.ZZZ, 16))],
                   data=encoded(10020, 200, 0, 1 << 96, 0))
        code = '0x6000'
        result = [[log]] + [code] * 6 + [
            encoded(1 << 96, 0, 1000 | (1000 << 12), 10020), encoded(123),
            encoded(int(OBSERVER.ADDRESSES['core'], 16)),
            encoded(int(OBSERVER.ADDRESSES['permit2'], 16)),
            encoded(int(OBSERVER.ADDRESSES['weth'], 16)),
            encoded(int(OBSERVER.ADDRESSES['core'], 16)), encoded(1), encoded(2)]
        hashes = {name: '0x' + OBSERVER.keccak256(bytes.fromhex(code[2:])).hex()
                  for name in OBSERVER.ADDRESSES}
        return header, result, hashes

    def observe(self, *, change=None, ending=None):
        header, result, hashes = self.fixture()
        if change:
            change(result)
        with patch.object(OBSERVER, 'EXPECTED_RUNTIME_HASHES', hashes), patch.object(
            OBSERVER, 'rpc', side_effect=[['0x1237', header], result,
                                          [ending if ending is not None else header]]) as rpc:
            observed = OBSERVER.observe('https://rpc.invalid', self.block, self.block_hash)
        return observed, rpc.call_args_list

    def test_hash_pinned_reads_and_real_fee_composition(self):
        observed, calls = self.observe()
        reads = calls[1].args[1]
        for method, params in reads:
            if method in ('eth_getCode', 'eth_call'):
                self.assertEqual(params[-1], dict(blockHash=self.block_hash, requireCanonical=True))
        self.assertEqual(observed['combined_fee_pips'], [11010, 11010])
        self.assertFalse(observed['release_approved'])

    def test_changed_dependency_runtime_is_rejected(self):
        for index in range(1, 7):
            with self.subTest(dependency=index), self.assertRaisesRegex(ValueError, 'runtime'):
                self.observe(change=lambda r: r.__setitem__(index, '0x6001'))

    def test_initialization_origin_and_reorg_are_rejected(self):
        for field, value in [('removed', True), ('address', '0x' + '12' * 20),
                             ('transactionHash', '0x' + '00' * 32), ('blockNumber', '0x1')]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.observe(change=lambda r: r[0][0].__setitem__(field, value))
        with self.assertRaisesRegex(ValueError, 'Canonical block'):
            self.observe(ending=dict(number=hex(self.block), hash='0x' + 'cd' * 32))

    def test_malformed_abi_or_fee_state_is_rejected(self):
        for field, value in [(7, '0x'), (7, encoded(1 << 96, 0, 1001, 10020)),
                             (7, encoded(1 << 96, 0, 0, 3000)), (8, encoded(1 << 128)),
                             (13, encoded(1 << 160)), (14, encoded(1, 2))]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.observe(change=lambda r: r.__setitem__(field, value))

    def test_rpc_reorders_exact_ids_and_rejects_ambiguous_envelopes(self):
        calls = [('eth_chainId', []), ('eth_getBlockByNumber', ['0x1', False])]
        with patch.object(OBSERVER.urllib.request, 'urlopen', return_value=io.BytesIO(
            json.dumps([reply(1, 'second'), reply(0, 'first')]).encode())):
            self.assertEqual(OBSERVER.rpc('https://rpc.invalid', calls), ['first', 'second'])
        invalid = [[reply(False, 'x'), reply(1, 'y')], [reply('0', 'x'), reply(1, 'y')],
                   [reply(0, 'x'), reply(0, 'y')], [reply(2, 'x'), reply(0, 'y')],
                   [dict(id=0, result='x'), reply(1, 'y')],
                   [dict(jsonrpc='2.0', id=0, result='x', error={}), reply(1, 'y')],
                   [reply(0, 'x')], {'not': 'a batch'}]
        for response in invalid:
            with self.subTest(response=response), patch.object(
                OBSERVER.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(response).encode())), \
                    self.assertRaises(ValueError):
                OBSERVER.rpc('https://rpc.invalid', calls)

    def test_rpc_limits_and_read_only_method_guard(self):
        with patch.object(OBSERVER.urllib.request, 'urlopen') as transport:
            with self.assertRaises(ValueError):
                OBSERVER.rpc('https://rpc.invalid', [('eth_sendTransaction', [{}])])
            transport.assert_not_called()
        with patch.object(OBSERVER, 'MAX_RESPONSE', 32), patch.object(
            OBSERVER.urllib.request, 'urlopen', return_value=io.BytesIO(b' ' * 33)), \
                self.assertRaisesRegex(ValueError, 'limit'):
            OBSERVER.rpc('https://rpc.invalid', [('eth_chainId', [])])

    def test_expected_hash_and_block_are_validated_before_network(self):
        with patch.object(OBSERVER, 'rpc') as transport:
            for block, block_hash in [(True, self.block_hash), (1, self.block_hash),
                                      (self.block, 'not-a-hash')]:
                with self.subTest(block=block), self.assertRaises(ValueError):
                    OBSERVER.observe('https://rpc.invalid', block, block_hash)
            transport.assert_not_called()

    def test_cli_sanitizes_failure_and_preserves_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observation.json'
            output.write_text('old evidence', encoding='utf-8')
            stderr, stdout = io.StringIO(), io.StringIO()
            with patch.object(OBSERVER, 'observe', side_effect=RuntimeError('private-rpc-secret')), \
                    contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                status = OBSERVER.main(['--block', str(self.block), '--output', str(output)])
            self.assertEqual(status, 1)
            self.assertNotIn('private-rpc-secret', stderr.getvalue() + stdout.getvalue())
            self.assertEqual(output.read_text(encoding='utf-8'), 'old evidence')

    def test_failed_output_replacement_preserves_old_record_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observation.json'
            output.write_text('old evidence', encoding='utf-8')
            stderr = io.StringIO()
            with patch.object(OBSERVER, 'observe', return_value={'release_approved': False}), \
                    patch.object(OBSERVER.os, 'replace', side_effect=OSError('private-disk-detail')), \
                    contextlib.redirect_stderr(stderr):
                status = OBSERVER.main(['--block', str(self.block), '--output', str(output)])
            self.assertEqual(status, 1)
            self.assertNotIn('private-disk-detail', stderr.getvalue())
            self.assertEqual(output.read_text(encoding='utf-8'), 'old evidence')
            self.assertEqual(list(Path(directory).iterdir()), [output])


if __name__ == '__main__':
    unittest.main()
