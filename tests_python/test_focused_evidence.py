"""New offline admission checks only; no historical test execution."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zzz_ops import focused_evidence as evidence

ROOT=Path(__file__).resolve().parents[1]

class FocusedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=evidence._load(ROOT,{"path":evidence.MANIFEST,"sha256":evidence.MANIFEST_SHA256})
        cls.group=next(x for x in cls.manifest["groups"] if x["id"]=="impact-rights")
        cls.raw=evidence._load(ROOT,cls.group["raw"])
        cls.proof=evidence._load(ROOT,cls.group["proof"])
        cls.artifact=evidence._load(ROOT,cls.group["artifact"])

    def test_genuine_seven_groups_admit_original_scope_without_new_execution(self):
        result=evidence.check(ROOT)
        self.assertTrue(result["integrity_admitted"])
        self.assertEqual(len(result["groups"]),7)
        self.assertEqual(result["historical_method_records"],78)
        self.assertEqual(result["new_EVM_executions"],0)
        self.assertFalse(result["production_approved"])
        self.assertTrue(all(not x["current_source_adopted"] for x in result["groups"]))
        input_group=next(x for x in result["groups"] if x["id"]=="input-tools")
        self.assertIn("no_independent_raw_log",input_group["evidence_level"])

    def test_wrong_successful_id_cannot_substitute_for_expected_method(self):
        raw=copy.deepcopy(self.raw);suite=next(iter(raw));methods=raw[suite]["test_results"]
        entry=methods.pop(next(iter(methods)));methods["testUnrelatedPassingMethod()"] = entry
        with self.assertRaisesRegex(evidence.EvidenceError,"exact_method_ids_differ"):
            evidence._forge_methods(raw,self.group["expected_ids"])

    def test_missing_extra_and_duplicate_method_ids_refuse(self):
        expected=self.group["expected_ids"]
        for actual in (expected[:-1],expected+["unrelated"],expected+[expected[0]]):
            with self.subTest(actual=actual),self.assertRaisesRegex(evidence.EvidenceError,"exact_method_ids_differ"):
                evidence._exact_ids(actual,expected)

    def test_failure_skip_or_counterexample_is_never_admitted(self):
        for change in ({"status":"Failure"},{"status":"Skipped"},{"reason":"failure"},{"counterexample":{}}):
            raw=copy.deepcopy(self.raw);record=next(iter(next(iter(raw.values()))["test_results"].values()));record.update(change)
            with self.subTest(change=change),self.assertRaises(evidence.EvidenceError):
                evidence._forge_methods(raw,self.group["expected_ids"])

    def test_compiled_method_selector_and_target_must_match(self):
        signature=self.group["expected_ids"][0].rsplit(".",1)[1]
        for target in (False,True):
            artifact=copy.deepcopy(self.artifact)
            if target:artifact["metadata"]["settings"]["compilationTarget"]={"test/Other.t.sol":"Other"}
            else:artifact["methodIdentifiers"][signature]="00000000"
            with self.subTest(target=target),self.assertRaises(evidence.EvidenceError):
                evidence._artifact(artifact,self.proof,self.group)

    def test_compiled_source_set_or_identity_cannot_be_relabelled(self):
        for missing in (False,True):
            artifact=copy.deepcopy(self.artifact);sources=artifact["metadata"]["sources"];name=next(iter(sources))
            if missing:del sources[name]
            else:sources[name]["keccak256"]="0x"+"00"*32
            with self.subTest(missing=missing),self.assertRaises(evidence.EvidenceError):
                evidence._artifact(artifact,self.proof,self.group)

    def test_changed_raw_or_artifact_bytes_fail_original_digest(self):
        for field in ("raw","artifact"):
            spec=self.group[field]
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=root/spec["path"];path.parent.mkdir(parents=True);data=(ROOT/spec["path"]).read_bytes();path.write_bytes(data+b" ")
                with self.assertRaisesRegex(evidence.EvidenceError,"historical_evidence_changed"):
                    evidence._bytes(root,spec)

    def test_recomputed_caller_manifest_cannot_approve_changed_results(self):
        manifest=copy.deepcopy(self.manifest);manifest["groups"][0]["raw"]["sha256"]="00"*32
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/evidence.MANIFEST;path.parent.mkdir(parents=True);path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(evidence.EvidenceError,"historical_evidence_changed"):
                evidence.check(root)

    def test_duplicate_keys_nonfinite_values_and_deep_json_refuse(self):
        malformed=[b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1e999}',b'['*50+b'0'+b']'*50]
        for raw in malformed:
            with self.subTest(raw=raw[:30]),self.assertRaises(evidence.EvidenceError):evidence._decode(raw)

    def test_gzip_and_stored_byte_limits_are_enforced(self):
        for expanded in (False,True):
            with self.subTest(expanded=expanded),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=root/("input.gz" if expanded else "input.json")
                data=gzip.compress(b"x"*(evidence.MAX_EXPANDED+1),mtime=0) if expanded else b"x"*(evidence.MAX_STORED+1)
                path.write_bytes(data);spec={"path":path.name,"sha256":hashlib.sha256(data).hexdigest()}
                with self.assertRaisesRegex(evidence.EvidenceError,"expanded_evidence_limit|stored_evidence_limit"):evidence._bytes(root,spec)

    def test_invalid_gzip_and_parent_path_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/"bad.gz";data=b"not-gzip";path.write_bytes(data)
            with self.assertRaisesRegex(evidence.EvidenceError,"invalid_gzip"):
                evidence._bytes(root,{"path":"bad.gz","sha256":hashlib.sha256(data).hexdigest()})
            with self.assertRaises(evidence.EvidenceError):
                evidence._bytes(root,{"path":"../outside.json","sha256":"00"*32})

    def test_unittest_log_requires_exact_ids_summary_and_no_skip(self):
        valid=b"test_a (module.Case.test_a) ... ok\n\nRan 1 test in 0.1s\n\nOK\n"
        evidence._python_log(valid,["module.Case.test_a"])
        for raw in (valid.replace(b"test_a)",b"test_b)"),valid.replace(b"... ok",b"... skipped 'reason'"),valid.replace(b"Ran 1",b"Ran 2"),valid+b"test_a (module.Case.test_a) ... ok\n"):
            with self.subTest(raw=raw),self.assertRaises(evidence.EvidenceError):evidence._python_log(raw,["module.Case.test_a"])

    def test_extra_failed_python_row_cannot_hide_behind_ok_summary(self):
        raw=(b"test_a (module.Case.test_a) ... ok\n"
             b"test_extra (module.Case.test_extra) ... FAIL\n"
             b"\nRan 1 test in 0.1s\n\nOK\n")
        with self.assertRaises(evidence.EvidenceError):evidence._python_log(raw,["module.Case.test_a"])

    def test_corrupted_deflate_normalizes_to_evidence_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/"corrupt.gz"
            damaged=bytearray(gzip.compress(b"original"*100,mtime=0));damaged[10]=7
            data=bytes(damaged);path.write_bytes(data)
            with self.assertRaises(evidence.EvidenceError):
                evidence._bytes(root,{"path":path.name,"sha256":hashlib.sha256(data).hexdigest()})

    def test_cli_has_no_root_manifest_network_or_execution_arguments(self):
        result=subprocess.run([sys.executable,str(ROOT/"scripts/check-focused-evidence.py"),"--rpc","FAKE_SECRET_DO_NOT_ECHO"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertNotIn("FAKE_SECRET_DO_NOT_ECHO",result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout),{"integrity_admitted":False,"reason":"no_arguments_supported"})

if __name__=="__main__":unittest.main()
