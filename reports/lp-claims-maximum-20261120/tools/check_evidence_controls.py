"""Four NEW offline rejection controls; never replay the EVM or alter evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checker = Path(__file__).with_name("verify_evidence.py")
    spec = importlib.util.spec_from_file_location("new_evidence_controls", checker)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = module.load
    results = []
    for kind, expected in (("padding", "Full estimate headroom was not preserved"),
                           ("recipient", "Captured recipient balance delta differs from receipt payout"),
                           ("ledger", "Claim receipt ledger/owner/asset/amount differs"),
                           ("path", "Evidence pointer outside original captured root")):
        altered = []
        def changed(path):
            value = copy.deepcopy(original(path))
            p = Path(path)
            if kind == "padding" and p.parent.name == "operations" and p.name == "claim-tree-8.json":
                value["padded"] -= 1
                altered.append(str(p))
            elif kind == "recipient" and p.parent.name == "assertions" and p.name == "claim-tree-8.json":
                value["recipient_balances_after"]["0x" + "00" * 20] += 1
                altered.append(str(p))
            elif kind == "ledger" and p.parent.name == "assertions" and p.name == "healthy-subset-after-fault.json":
                value["entries"][-1][-1] = False
                altered.append(str(p))
            elif kind == "path" and p.name == "PUBLISHED_MANIFEST.json":
                value["original_root"] = str(args.campaign.resolve() / "not-the-captured-root")
                altered.append(str(p))
            return value
        module.load = changed
        try:
            module.verify(args.campaign)
        except ValueError as error:
            if str(error) != expected or not altered:
                raise
            results.append({"kind": kind, "rejected": True, "cause": str(error)})
        else:
            raise AssertionError("Corrupted evidence was accepted: " + kind)
        finally:
            module.load = original
    result = {"schema": 1, "new_offline_controls": results,
              "checker_sha256": hashlib.sha256(checker.read_bytes()).hexdigest(),
              "controller_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "evidence_files_modified": False, "evm_reexecuted": False, "production_approved": False}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"new_controls": len(results), "all_rejected": True, "evm_reexecuted": False}))


if __name__ == "__main__":
    main()
