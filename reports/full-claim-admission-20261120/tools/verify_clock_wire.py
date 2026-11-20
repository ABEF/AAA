"""Clock-only supplement: ordered original wire, no API/EVM replay or node."""
from __future__ import annotations
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

MAX_BYTES = 128 * 1024 * 1024
WIRES = {
    "failure": "ba64c6cee949ac39867a2a419966a12c838e71a988dc50dabb2c7c07e3c605b9",
    "continuation": "f4a88b3087a3ba865b0f5632df1b858f958845aa63223b8da7c0ad7253068613",
}
MANIFEST = "3cc6bc33b754995e149af837c853a8984b1fe6a8d0f3c621dd2ea4a1652bc69a"
ROYALTIES_OPEN = "0x1c58ff95"  # Ethereum selector of royaltiesOpen().


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "Duplicate clock-evidence JSON field")
        result[key] = value
    return result


def loads(raw):
    require(len(raw) <= MAX_BYTES, "Clock-evidence JSON bound exceeded")
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: require(False, "Nonfinite clock evidence"))


def load(path):
    with Path(path).open("rb") as stream:
        return loads(stream.read(MAX_BYTES + 1))


def frozen_wire(folder, stage):
    path = Path(folder) / "node/rpc-records.json.gz"
    with path.open("rb") as stream:
        compressed = stream.read(MAX_BYTES + 1)
    require(len(compressed) <= MAX_BYTES and hashlib.sha256(compressed).hexdigest() == WIRES[stage],
            "Frozen original clock wire differs: " + stage)
    with gzip.open(path, "rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    rows = loads(raw)
    require(type(rows) is list and 0 < len(rows) <= 100000, "Invalid finite original clock wire")
    return rows


def check_order(rows, clock, manifest):
    owner, royalties = manifest["owner"], manifest["contracts"]["royalties"]
    def matches(row, method, params, expected):
        return (row.get("request", {}).get("method") == method and
            row["request"].get("params") == params and
            row.get("response", {}).get("result") == expected and "error" not in row["response"])
    def next_match(after, method, params, expected):
        for index in range(after + 1, len(rows)):
            if matches(rows[index], method, params, expected):
                return index
        raise ValueError("Missing ordered original clock observation: " + method)
    sent = [i for i, row in enumerate(rows) if row["request"]["method"] == "eth_sendTransaction"]
    require(len(sent) == 1, "Expected exactly one subsequent actual claim send")
    before, after, pending = clock["before_latest"], clock["after_latest"], clock["after_pending"]
    require(before["stateRoot"] == after["stateRoot"] and after["parentHash"] == before["hash"] and
        int(after["number"], 16) == int(before["number"], 16) + 1 and after["transactions"] == [] and
        int(after["timestamp"], 16) == int(before["timestamp"], 16) + 1 and
        int(pending["timestamp"], 16) >= int(after["timestamp"], 16),
        "Empty local clock block altered state or violated timestamp/ancestry")
    call = {"to": royalties, "data": ROYALTIES_OPEN}
    zero, one = "0x" + "0" * 64, "0x" + f"{1:064x}"
    observed = {}
    observed["before_latest"] = next_match(-1, "eth_getBlockByNumber", ["latest", False], before)
    observed["before_pending_closed"] = next_match(observed["before_latest"], "eth_call", [call, "pending"], zero)
    observed["set_next_timestamp"] = next_match(observed["before_pending_closed"], "evm_setNextBlockTimestamp",
                                                [int(after["timestamp"], 16)], None)
    observed["empty_mine"] = next_match(observed["set_next_timestamp"], "evm_mine", [], "0x0")
    observed["after_latest"] = next_match(observed["empty_mine"], "eth_getBlockByNumber", ["latest", False], after)
    observed["after_pending_header"] = next_match(observed["after_latest"], "eth_getBlockByNumber", ["pending", False], pending)
    observed["after_pending_open"] = next_match(observed["after_pending_header"], "eth_call", [call, "pending"], one)
    observed["after_mine_nonce444"] = next_match(observed["after_pending_open"], "eth_getTransactionCount", [owner, "latest"], hex(444))
    observed["first_actual_send"] = sent[0]
    require(observed["after_mine_nonce444"] < sent[0] and
        list(observed.values()) == sorted(set(observed.values())),
        "Pending-open/nonce evidence is not ordered after mine and before actual send")
    require(clock["before_pending_royalties_open"] == 0 and clock["after_pending_royalties_open"] == 1,
            "Clock summary differs from independently bound actual pending observations")
    return observed


def verify(failure, continuation):
    old = frozen_wire(failure, "failure")
    require(not any(row["request"]["method"] == "eth_sendTransaction" for row in old),
            "Original pending-clock refusal was relabelled as a sent transaction")
    later = frozen_wire(continuation, "continuation")
    manifest_path = Path(continuation) / "FIXTURE_MANIFEST.json"
    require(hashlib.sha256(manifest_path.read_bytes()).hexdigest() == MANIFEST,
            "Frozen clock fixture manifest differs")
    manifest, clock = load(manifest_path), load(Path(continuation) / "RESTORE_CLOCK.json")
    observations = check_order(later, clock, manifest)
    checks = []
    missing_open = copy.deepcopy(later)
    missing_open[observations["after_pending_open"]]["response"]["result"] = "0x" + "0" * 64
    stale_nonce = copy.deepcopy(later)
    for row in stale_nonce[observations["empty_mine"] + 1:observations["first_actual_send"]]:
        if row["request"]["method"] == "eth_getTransactionCount" and row["request"]["params"] == [manifest["owner"], "latest"]:
            row["response"]["result"] = hex(445)
    early_open = copy.deepcopy(later)
    value = early_open.pop(observations["after_pending_open"])
    early_open.insert(observations["empty_mine"], value)
    for name, changed in (("missing_after_pending_open_wire", missing_open),
                          ("nonce444_only_before_mine", stale_nonce),
                          ("pending_open_before_empty_mine", early_open)):
        try:
            check_order(changed, clock, manifest)
        except ValueError:
            checks.append({"control": name, "rejected": True})
        else:
            raise ValueError("Corrupted ordered clock wire was accepted: " + name)
    return {"schema": 1, "complete": True, "production_approved": False,
        "original_wire_sha256": WIRES, "ordered_wire_indices_zero_based": observations,
        "after_pending_open_bound_to_actual_wire": True,
        "nonce444_bound_after_mine_before_first_send": True,
        "empty_block_state_root_unchanged": True, "new_corruption_controls": checks,
        "api_replays": 0, "evm_calls": 0, "node_starts": 0,
        "scope": "Clock-only ordered-wire supplement to retained LATE_TAX_VERIFICATION_FINAL.json; "
                 "source results and original evidence remain unchanged"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("failure", type=Path)
    parser.add_argument("continuation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.failure, args.continuation)
    result["checker_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"complete": True, "ordered_observations": len(result["ordered_wire_indices_zero_based"]),
                      "corruption_controls": len(result["new_corruption_controls"]), "output": str(args.output)}), flush=True)


if __name__ == "__main__":
    main()
