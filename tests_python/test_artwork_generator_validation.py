"""Offline catalogue admission must remain effective under Python optimization.

Only generate() is called; no catalogue/library asset is written or regenerated.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'scripts/generate-artwork-library.py'
CATALOGUE = ROOT / 'design/nft-metadata/palette-system-v1/packed-catalog.json'
PROBE = '''import hashlib,importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('artwork_generator_admission',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.CATALOG=Path(sys.argv[2])
try: result=module.generate()
except (ValueError,AssertionError,KeyError,TypeError,OverflowError):
 print(json.dumps({'accepted':False}))
else: print(json.dumps({'accepted':True,'sha256':hashlib.sha256(result.encode()).hexdigest()}))
'''


class ArtworkGeneratorValidationTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = json.loads(CATALOGUE.read_text())

    def probe(self, catalogue, *, optimized, source_bytes=None):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'catalogue.json'
            path.write_bytes(source_bytes if source_bytes is not None else json.dumps(catalogue).encode())
            command = [sys.executable] + (['-O'] if optimized else [])
            process = subprocess.run(command + ['-c', PROBE, str(GENERATOR), str(path)],
                capture_output=True, text=True, timeout=20)
            self.assertEqual(0, process.returncode, process.stderr)
            return json.loads(process.stdout)

    def reject_both(self, catalogue):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertFalse(self.probe(catalogue, optimized=optimized)['accepted'])

    def test_valid_catalogue_is_identical_in_normal_and_optimized_generation(self):
        original = CATALOGUE.read_bytes()
        target = ROOT / 'src/libraries/ZZZArtwork.sol'
        before = target.read_bytes()
        expected = hashlib.sha256(target.read_text(encoding='utf-8').encode()).hexdigest()
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertEqual({'accepted': True, 'sha256': expected},
                    self.probe(self.catalogue, optimized=optimized, source_bytes=original))
        self.assertEqual(original, CATALOGUE.read_bytes())
        self.assertEqual(before, target.read_bytes())

    def test_palette_count_and_pattern_identity_cannot_be_optimized_away(self):
        for field, value in (('paletteOrder', self.catalogue['paletteOrder'][:-1]),
                             ('patternOrder', list(reversed(self.catalogue['patternOrder'])))):
            catalogue = copy.deepcopy(self.catalogue)
            catalogue[field] = value
            with self.subTest(field=field):
                self.reject_both(catalogue)

    def test_each_rarity_supply_stays_exact_even_with_self_consistent_hash_and_codes(self):
        for rarity in ('commun', 'rare', 'legendary'):
            catalogue = copy.deepcopy(self.catalogue)
            data = bytes.fromhex(catalogue['hex'][rarity])[:-2]
            catalogue['hex'][rarity] = data.hex()
            catalogue['sha256'][rarity] = hashlib.sha256(data).hexdigest()
            catalogue['codes'][rarity] = catalogue['codes'][rarity][:-1]
            with self.subTest(rarity=rarity):
                self.reject_both(catalogue)

    def test_digest_and_decoded_code_agreement_stay_mandatory(self):
        bad_hash = copy.deepcopy(self.catalogue)
        bad_hash['sha256']['commun'] = '0' * 64
        self.reject_both(bad_hash)
        bad_codes = copy.deepcopy(self.catalogue)
        bad_codes['codes']['rare'][0] = (bad_codes['codes']['rare'][0] + 1) % 232
        self.reject_both(bad_codes)

    def test_out_of_range_code_with_matching_hash_and_inventory_is_rejected(self):
        catalogue = copy.deepcopy(self.catalogue)
        data = bytearray.fromhex(catalogue['hex']['legendary'])
        data[:2] = (232).to_bytes(2, 'big')
        catalogue['hex']['legendary'] = data.hex()
        catalogue['sha256']['legendary'] = hashlib.sha256(data).hexdigest()
        catalogue['codes']['legendary'][0] = 232
        self.reject_both(catalogue)


if __name__ == '__main__':
    unittest.main()
