"""Fresh local profile refusal only: no process, RPC, signing or deployment."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import local_fixture_profile as profile
from scripts.local_inputs import configure_inputs
from tests_python.test_local_stack import lab
from zzz_ops.abi import keccak256


class LocalPricingProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.artifacts=self.root/'artifacts'
        self.path=self.artifacts/'ZZZOracle.sol'/'ZZZOracle.json';self.path.parent.mkdir(parents=True)

    def artifact(self,abi=None,source=b'legacy Oracle fixture'):
        self.source=self.root/'repo'/'src'/'ZZZOracle.sol';self.source.parent.mkdir(parents=True,exist_ok=True)
        self.source.write_bytes(source)
        if abi is None:abi=[{'type':'function','name':'setFeed','inputs':[
            {'type':'address'},{'type':'address'},{'type':'uint32'}]}]
        artifact={'abi':abi,'metadata':{'sources':{'src/ZZZOracle.sol':{'keccak256':'0x'+keccak256(source).hex()}}}}
        self.path.write_text(json.dumps(artifact),encoding='utf-8')
        return artifact

    def current(self):self.artifact([{'type':'function','name':'PRICING_VERSION','inputs':[]}])

    def test_current_v2_artifact_refused_before_lab_state_or_process_creation(self):
        self.current();state=self.root/'new-state'
        with patch.object(lab.subprocess,'Popen') as process,patch.object(lab.Lab,'send') as send:
            with self.assertRaisesRegex(RuntimeError,'native/pricing V2'):
                lab.Lab(SimpleNamespace(artifacts=str(self.artifacts),state=str(state)))
            process.assert_not_called();send.assert_not_called()
        self.assertFalse(state.exists())

    def test_direct_start_cannot_bypass_the_profile_guard(self):
        self.current();instance=object.__new__(lab.Lab);instance.args=SimpleNamespace(artifacts=str(self.artifacts))
        with patch.object(lab.subprocess,'Popen') as process:
            with self.assertRaisesRegex(RuntimeError,'native/pricing V2'):instance.start()
            process.assert_not_called()
        self.assertFalse(hasattr(instance,'process'))

    def test_input_configuration_refused_before_any_contract_call(self):
        self.current();instance=SimpleNamespace(args=SimpleNamespace(artifacts=str(self.artifacts)),addr=Mock(),call=Mock())
        with self.assertRaisesRegex(RuntimeError,'native/pricing V2'):configure_inputs(instance)
        instance.addr.assert_not_called();instance.call.assert_not_called()

    def test_authentic_legacy_source_profile_is_explicit_and_read_only(self):
        self.artifact();before=self.path.read_bytes()
        with patch.object(profile,'ROOT',self.source.parents[1]):
            self.assertEqual(profile.require_legacy_fixture_artifacts(self.artifacts),1)
        self.assertEqual(self.path.read_bytes(),before)

    def test_stale_legacy_artifact_does_not_authorize_fresh_start(self):
        self.artifact();self.source.write_bytes(b'different source')
        with patch.object(profile,'ROOT',self.source.parents[1]):
            with self.assertRaisesRegex(ValueError,'Missing, stale or incompatible'):
                profile.require_legacy_fixture_artifacts(self.artifacts)

    def test_current_workspace_cannot_be_disguised_with_a_legacy_abi(self):
        self.artifact(source=b'uint256 constant PRICING_VERSION = 2;')
        with patch.object(profile,'ROOT',self.source.parents[1]):
            with self.assertRaisesRegex(RuntimeError,'native/pricing V2'):
                profile.require_legacy_fixture_artifacts(self.artifacts)

    def test_missing_or_malformed_artifact_fails_closed(self):
        for raw in (None,b'{}',b'[]',b'1',b'{"abi":[],"abi":[]}',b'{"abi":NaN}',b'\xff'):
            if raw is None:self.path.unlink(missing_ok=True)
            else:self.path.write_bytes(raw)
            with self.subTest(case=raw),self.assertRaisesRegex(ValueError,'Missing, stale or incompatible'):
                profile.require_legacy_fixture_artifacts(self.artifacts)

    def test_unbounded_artifact_is_rejected(self):
        self.path.write_bytes(b'x'*65)
        with patch.object(profile,'MAX_ARTIFACT_BYTES',64):
            with self.assertRaises(ValueError):profile.require_legacy_fixture_artifacts(self.artifacts)


if __name__=='__main__':unittest.main()
