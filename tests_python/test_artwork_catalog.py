"""Cross-language checks for the finite visual inventory, not mint randomness."""
import collections
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'design/nft-metadata/palette-system-v1'

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

GENERATOR = module('artwork_generator', ROOT / 'scripts/generate-artwork-library.py')
GATE = module('artwork_production_gate', ROOT / 'scripts/validate-production-config.py')

class ArtworkCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((DIRECTORY / 'inventory.json').read_text(encoding='utf-8'))
        cls.packed = json.loads((DIRECTORY / 'packed-catalog.json').read_text(encoding='utf-8'))

    def test_generated_solidity_is_exactly_the_committed_catalogue(self):
        self.assertEqual(GENERATOR.TARGET.read_text(encoding='utf-8'), GENERATOR.generate())

    def test_palette_rules_have_exactly_eight_22_and_28_unique_palettes(self):
        colors = [color['id'] for color in self.catalog['colors']]
        self.assertEqual(colors, list(GATE.ARTWORK_COLORS))
        palettes = self.catalog['palettes']
        self.assertEqual(collections.Counter(len(p['colorIds']) for p in palettes), {1:8, 2:22, 3:28})
        self.assertEqual([p['id'] for p in palettes], list(GATE.ARTWORK_PALETTES))
        self.assertEqual(len({p['id'] for p in palettes}), 58)
        for palette, packed in zip(palettes, self.packed['paletteOrder']):
            self.assertEqual(palette['id'], packed['id'])
            self.assertEqual(palette['colorIds'], packed['colorIds'])
            self.assertEqual(sum(1 << colors.index(color) for color in palette['colorIds']), packed['mask'])
            self.assertEqual(len(set(palette['colorIds'])), len(palette['colorIds']))

    def test_all_1000_inventory_entries_round_trip_the_solidity_encoding(self):
        inventory = self.catalog['inventory']
        palettes = [palette['id'] for palette in self.catalog['palettes']]
        patterns = [pattern['id'] for pattern in self.catalog['patterns']]
        self.assertEqual(patterns, list(GATE.ARTWORK_PATTERNS))
        self.assertEqual([entry['tokenId'] for entry in inventory], list(range(1,1001)))
        for rarity, expected in (('commun',600), ('rare',300), ('legendary',100)):
            entries = [entry for entry in inventory if entry['rarity']==rarity]
            self.assertEqual(len(entries), expected)
            actual = [palettes.index(entry['paletteId'])*4 + patterns.index(entry['pattern']) for entry in entries]
            self.assertEqual(actual, self.packed['codes'][rarity])
            self.assertEqual(b''.join(code.to_bytes(2,'big') for code in actual).hex(), self.packed['hex'][rarity])

    def test_exact_style_rarity_quotas_and_four_copy_cap(self):
        inventory = self.catalog['inventory']
        counts = collections.Counter((entry['colorStyle'],entry['rarity']) for entry in inventory)
        self.assertEqual(counts, {
            ('monochrome','commun'):120, ('monochrome','rare'):60, ('monochrome','legendary'):20,
            ('bicolor','commun'):300, ('bicolor','rare'):150, ('bicolor','legendary'):50,
            ('tricolor','commun'):180, ('tricolor','rare'):90, ('tricolor','legendary'):30,
        })
        copies = collections.Counter((entry['paletteId'],entry['pattern'],entry['rarity']) for entry in inventory)
        self.assertEqual(max(copies.values()), 4)
        self.assertTrue(all(count==1 for key,count in copies.items() if key[2]=='legendary'))
        self.assertEqual(len(copies), 542)

    def test_every_palette_and_pattern_is_available_across_all_rarities(self):
        inventory = self.catalog['inventory']
        for rarity in ('commun','rare','legendary'):
            entries = [entry for entry in inventory if entry['rarity']==rarity]
            self.assertEqual({entry['paletteId'] for entry in entries}, {p['id'] for p in self.catalog['palettes']})
            self.assertEqual({entry['pattern'] for entry in entries}, set(GATE.ARTWORK_PATTERNS))

    def test_production_publication_requires_every_2784_svg_state(self):
        expected = {f'{palette["id"]}-{pattern["id"]}-{rarity["id"]}-{stage}.svg'
            for palette,pattern,rarity,stage in itertools.product(self.catalog['palettes'], self.catalog['patterns'],
                self.catalog['rarities'], ('dormant','activated','enhanced','singularity'))}
        self.assertEqual(len(expected), 2784)
        self.assertEqual(set(GATE.ARTWORK_FILES), expected)
        self.assertNotIn('cyan-commun-dormant.png', expected)

if __name__ == '__main__':
    unittest.main()
