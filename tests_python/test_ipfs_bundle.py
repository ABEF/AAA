import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_ipfs_bundle import expected_ids, prepare, validate_svg


class IPFSBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir(); (self.source / "metadata").mkdir()
        self.catalog = self.root / "catalog.json"
        value = {"paletteOrder": [{"id": "cyan"}], "patternOrder": ["arcs"]}
        self.catalog.write_text(json.dumps(value))
        variants = []
        for art_id in expected_ids(value):
            data = b'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/webp;base64,AAAA"/></svg>\n'
            (self.source / (art_id + ".svg")).write_bytes(data)
            (self.source / "metadata" / (art_id + ".json")).write_text(json.dumps({"image": f"../{art_id}.svg"}))
            variants.append({"id": art_id, "image_sha256": hashlib.sha256(data).hexdigest()})
        self.manifest = {"variants": variants}
        self.save_manifest()

    def save_manifest(self):
        (self.source / "manifest.json").write_text(json.dumps(self.manifest))

    def test_complete_archive_is_reproducible_and_not_published(self):
        first = prepare(self.source, self.root / "one", self.catalog)
        second = prepare(self.source, self.root / "two", self.catalog)
        self.assertEqual(first, second)
        self.assertEqual(first["artwork_states"], 12)
        self.assertEqual(first["archive_files_verified"], 27)
        self.assertFalse(first["uploaded"]); self.assertFalse(first["pinned"])
        self.assertIsNone(first["root_cid"])

    def test_tampered_svg_is_rejected_before_output(self):
        (self.source / "cyan-arcs-commun-dormant.svg").write_text('<svg/>')
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            prepare(self.source, self.root / "output", self.catalog)
        self.assertFalse((self.root / "output").exists())

    def test_duplicate_or_missing_manifest_entries_are_rejected(self):
        self.manifest["variants"].append(self.manifest["variants"][0]); self.save_manifest()
        with self.assertRaisesRegex(ValueError, "complete contract catalogue"):
            prepare(self.source, self.root / "output", self.catalog)
        self.manifest["variants"] = self.manifest["variants"][:-2]; self.save_manifest()
        with self.assertRaises(ValueError):
            prepare(self.source, self.root / "output", self.catalog)

    def test_wrong_metadata_image_and_external_svg_resources_are_rejected(self):
        (self.source / "metadata/cyan-arcs-commun-dormant.json").write_text('{"image":"https://example.com/egg.svg"}')
        with self.assertRaisesRegex(ValueError, "reference metadata"):
            prepare(self.source, self.root / "output", self.catalog)
        for payload in (b'<svg><image href="https://example.com/image"/></svg>',
                        b'<svg onload="alert(1)"/>', b'<svg><script/></svg>',
                        b'<svg fill="url(#safe) url(https://evil.example/x)"/>',
                        b'<!DOCTYPE svg><svg/>', b'<svg><set attributeName="href"/></svg>'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validate_svg(payload)

    def test_output_cannot_overwrite_source_or_prior_bundle(self):
        with self.assertRaises(ValueError):
            prepare(self.source, self.source / "bundle", self.catalog)
        with self.assertRaises(ValueError):
            prepare(self.source, self.root, self.catalog)
        output = self.root / "output"
        prepare(self.source, output, self.catalog)
        sentinel = output / "keep.txt"; sentinel.write_text("keep")
        with self.assertRaises(ValueError):
            prepare(self.source, output, self.catalog)
        self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
