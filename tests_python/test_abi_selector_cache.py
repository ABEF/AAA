"""NEW selector-only cache checks against the preceding uncached ABI behavior."""
from concurrent.futures import ThreadPoolExecutor
import re
import unittest

from zzz_ops import abi


def uncached_calldata(signature, *args):
    """The original public algorithm, with no old test/scenario body invoked."""
    match = re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\(([^()]*)\)', signature)
    if not match:
        raise ValueError('Only flat static ABI signatures are supported')
    types = match[1].split(',') if match[1] else []
    if len(types) != len(args):
        raise ValueError('Argument count mismatch')
    return '0x' + abi.keccak256(signature.encode()).hex()[:8] + ''.join(
        abi.word(value, typ) for value, typ in zip(args, types))


class SelectorCacheTests(unittest.TestCase):
    def setUp(self):
        abi._selector.cache_clear()

    def tearDown(self):
        abi._selector.cache_clear()

    def same_result(self, signature, *args):
        try:
            expected = uncached_calldata(signature, *args)
        except Exception as before:
            with self.assertRaises(type(before)) as current:
                abi.calldata(signature, *args)
            self.assertEqual(str(current.exception), str(before))
        else:
            self.assertEqual(abi.calldata(signature, *args), expected)

    def test_new_valid_signatures_match_original_codec(self):
        for signature, args in (
            ('mint()', ()), ('ownerOf(uint256)', (2**255 + 1,)),
            ('approve(address,uint256)', ('0x' + '12'*20, '10000')),
            ('set(bytes32,bool,uint8)', ('0x' + 'ab'*32, True, 255)),
            ('set(uint256,uint256)', (0, 2**256 - 1)),
        ):
            with self.subTest(signature=signature):
                self.same_result(signature, *args)
                self.same_result(signature, *args)

    def test_new_invalid_signatures_and_counts_preserve_errors(self):
        for signature, args in (
            ('', ()), ('1bad()', ()), ('x(())', ()), ('x()junk', ()),
            ('x(uint256)', ()), ('x()', (1,)), (None, ()),
            (b'x()', ()), (1, ()), ('x(uint256,uint256)', (1,)),
        ):
            with self.subTest(signature=signature):
                self.same_result(signature, *args)
        self.assertEqual(abi._selector.cache_info().currsize, 0)

    def test_new_repeated_selector_never_reuses_argument_values(self):
        signature = 'claimableComponents(uint256,address)'
        outputs = []
        for identifier in (1, 2, 2**255 + 1, 2**256 - 1):
            target = '0x' + f'{identifier % (2**160 - 1) + 1:040x}'
            outputs.append(abi.calldata(signature, identifier, target))
            self.assertEqual(outputs[-1], uncached_calldata(signature, identifier, target))
        self.assertEqual(len(set(outputs)), 4)
        self.assertEqual(abi._selector.cache_info().hits, 3)
        self.assertEqual(abi._selector.cache_info().misses, 1)

    def test_new_invalid_words_still_fail_after_cache_hit(self):
        for signature, valid, invalid in (
            ('x(uint8)', 1, (-1, 256, 1.5, True, '1.5', b'1')),
            ('x(address)', '0x' + '01'*20, ('0x'+'00'*20, 'invalid')),
            ('x(bytes32)', '0x'+'11'*32, ('0x11', 1)),
            ('x(bool)', True, (2, 'true', None)),
        ):
            abi.calldata(signature, valid)
            for value in invalid:
                with self.subTest(signature=signature, value=value):
                    self.same_result(signature, value)

    def test_new_long_signatures_are_not_retained(self):
        signature = 'f'*257 + '(uint256)'
        for value in (0, 99):
            self.same_result(signature, value)
        info = abi._selector.cache_info()
        self.assertEqual((info.hits, info.misses, info.currsize), (0, 0, 0))

    def test_new_ascii_length_boundary_is_exact(self):
        signature = 'f'*254 + '()'
        self.assertEqual(len(signature), 256)
        self.same_result(signature)
        self.same_result(signature)
        self.assertEqual(abi._selector.cache_info().hits, 1)
        self.same_result('f' + signature)
        self.assertEqual(abi._selector.cache_info().currsize, 1)

    def test_new_unicode_and_string_subclass_keep_original_behavior(self):
        for signature, args in (('é()', ()), ('x(é)', (1,)), ('x(😀)', (1,))):
            self.same_result(signature, *args)
        self.assertEqual(abi._selector.cache_info().currsize, 0)

        class CustomSignature(str):
            def encode(self):
                return b'custom()'

        signature = CustomSignature('x()')
        self.same_result(signature)
        self.same_result(signature)
        self.assertEqual(abi._selector.cache_info().currsize, 0)
        self.assertNotEqual(abi.calldata(signature), abi.calldata('x()'))

    def test_new_cache_bound_and_eviction_preserve_bytes(self):
        for number in range(300):
            abi.calldata(f'function{number}(uint256)', number)
        self.assertEqual(abi._selector.cache_info().maxsize, 256)
        self.assertEqual(abi._selector.cache_info().currsize, 256)
        before = abi._selector.cache_info()
        self.same_result('function0(uint256)', 999)
        self.assertEqual(abi._selector.cache_info().misses, before.misses + 1)
        self.same_result('function299(uint256)', 17)
        self.assertEqual(abi._selector.cache_info().hits, before.hits + 1)
        self.assertEqual(abi._selector.cache_info().currsize, 256)

    def test_new_concurrent_callers_keep_independent_exact_arguments(self):
        rows = [(f'concurrent{n % 7}(uint256,address)', n, '0x' + f'{n+1:040x}')
                for n in range(64)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            outputs = list(pool.map(lambda row: abi.calldata(*row), rows))
        self.assertEqual(outputs, [uncached_calldata(*row) for row in rows])
        self.assertLessEqual(abi._selector.cache_info().currsize, 7)


if __name__ == '__main__':
    unittest.main()
