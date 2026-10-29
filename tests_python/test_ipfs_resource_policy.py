"""Reference artwork must stay self-contained independently of a matching hash."""
import hashlib
import unittest

from scripts.prepare_ipfs_bundle import prepare, validate_svg
from tests_python import test_ipfs_bundle as fixtures


class IPFSResourcePolicyTests(unittest.TestCase):
    def test_css_escapes_cannot_hide_external_presentation_resources(self):
        for data in (br'<svg><path fill="u\72l(https://example.invalid/a.svg)"/></svg>',
                     br'<svg><path style="fill:u\72l(https://example.invalid/a.svg)"/></svg>'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_svg(data)

    def test_other_animation_and_css_style_channels_are_not_static(self):
        for data in (b'<svg><animateMotion path="M0 0 L1 1"/></svg>',
                     b'<svg><animateColor attributeName="fill"/></svg>',
                     b'<svg><path style="animation:move 1s infinite"/></svg>'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_svg(data)

    def test_stylesheet_and_other_processing_instructions_are_rejected_everywhere(self):
        # These are inert byte strings: no browser or network request is used.
        for data in (
            b'<?xml-stylesheet type="text/css" href="https://example.invalid/a.css"?><svg/>',
            b'<svg><?xml-stylesheet href="https://example.invalid/a.css"?></svg>',
            b'<svg/><?xml-stylesheet href="https://example.invalid/a.css"?>',
            b'<svg><?custom target="external"?></svg>',
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_svg(data)

    def test_xml_base_cannot_redirect_fragment_resources(self):
        for attribute in ('xml:base="https://example.invalid/other.svg"', 'xml:base="../other.svg"'):
            for body in (f'<svg {attribute}><use href="#part"/></svg>',
                         f'<svg><g {attribute}><use href="#part"/></g></svg>'):
                with self.subTest(body=body), self.assertRaises(ValueError):
                    validate_svg(body.encode())

    def test_encoded_doctype_cannot_bypass_ascii_resource_screen(self):
        text='<!DOCTYPE svg [<!ENTITY sample "not external">]><svg><title>&sample;</title></svg>'
        for encoding in ('utf-16','utf-16-be','utf-16-le'):
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                validate_svg(text.encode(encoding))

    def test_xml_declaration_comments_and_approved_local_resources_remain_valid(self):
        validate_svg(b'<?xml version="1.0" encoding="UTF-8"?>\n'
                     b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
                     b'<!-- approved static content -->'
                     b'<defs><linearGradient id="g"/><image id="part" href="data:image/webp;base64,AAAA"/></defs>'
                     b'<use xlink:href="#part" fill="url(#g)"/></svg>')

    def test_rehashed_external_stylesheet_rejects_before_bundle_creation(self):
        fixture=fixtures.IPFSBundleTests('runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
        variant=fixture.manifest['variants'][0]
        data=b'<?xml-stylesheet href="https://example.invalid/a.css"?><svg/>'
        (fixture.source/(variant['id']+'.svg')).write_bytes(data)
        variant['image_sha256']=hashlib.sha256(data).hexdigest();fixture.save_manifest()
        output=fixture.root/'blocked'
        with self.assertRaises(ValueError):prepare(fixture.source,output,fixture.catalog)
        self.assertFalse(output.exists())

    def test_duplicate_json_cannot_hide_conflicting_image_or_catalogue(self):
        for target in ('metadata','manifest','catalog'):
            with self.subTest(target=target):
                fixture=fixtures.IPFSBundleTests('runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
                if target=='metadata':
                    art=fixture.manifest['variants'][0]['id']
                    path=fixture.source/'metadata'/(art+'.json')
                    path.write_text('{"image":"https://example.invalid/x","image":"../'+art+'.svg"}')
                else:
                    path=fixture.source/'manifest.json' if target=='manifest' else fixture.catalog
                    original=path.read_text();field='variants' if target=='manifest' else 'paletteOrder'
                    path.write_text('{"'+field+'":[], '+original[1:])
                output=fixture.root/'blocked'
                with self.assertRaises(ValueError):prepare(fixture.source,output,fixture.catalog)
                self.assertFalse(output.exists())

    def test_nonfinite_json_is_not_a_publishable_reference(self):
        for constant in ('NaN','Infinity','-Infinity','1e9999'):
            with self.subTest(constant=constant):
                fixture=fixtures.IPFSBundleTests('runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
                art=fixture.manifest['variants'][0]['id']
                (fixture.source/'metadata'/(art+'.json')).write_text(
                    '{"image":"../'+art+'.svg","unexpected":'+constant+'}')
                output=fixture.root/'blocked'
                with self.assertRaises(ValueError):prepare(fixture.source,output,fixture.catalog)
                self.assertFalse(output.exists())
