"""Compact exact method/event/source evidence; do not copy large raw traces."""
from __future__ import annotations
from functools import lru_cache
import hashlib
import json
import mmap
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

EXPECTED={
 "test/LaunchClaimCapacity20261117.t.sol:LaunchClaimCapacityPending20261117Test.testLaunchNineteenPendingMixedLedgerClaimsAtTwelveMillionWithSafeRecovery()",
 "test/LaunchClaimCapacity20261117.t.sol:LaunchClaimCapacityStored20261117Test.testLaunchThirtyTwoStoredLPClaimsAtTwelveMillionAndExactCountLimit()",
 "test/LaunchClaimCapacity20261117.t.sol:LaunchClaimCapacityStored20261117Test.testLaunchLastRoyaltyFaultRollsBackMixedClaimsThenHealthySubsetAndRecoveryPayExactly()",
}
SCENARIOS=[
 "pending17royalty+2LP:1000active:claim12M",
 "stored17royalty+2LP:1000active:claim12M",
 "32storedLP:16currentownerNFT:4buckets:claim12M",
 "healthy18withoutfailedcurrency:claim12M",
 "recovered1originalcurrency:claim12M",
]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
@lru_cache(maxsize=None)
def keccak(data):return "0x"+keccak256(data).hex()

def source_proof(artifact:Path,override:Path|None=None):
    a=json.loads(artifact.read_text(encoding="utf-8"));m=a["metadata"];sources=[]
    for name,record in m["sources"].items():
        p=override if override is not None and name=="test/LaunchClaimCapacity20261117.t.sol" else ROOT/name
        raw=p.read_bytes();expected=record["keccak256"]
        if keccak(raw)==expected:form="exact raw bytes"
        elif b"\r\n" in raw and keccak(raw.replace(b"\r\n",b"\n"))==expected:form="exact CRLF-to-LF compiler input"
        else:raise ValueError(f"Compiled source mismatch: {name}")
        sources.append({"path":name,"sha256":sha(p),"compiled_keccak256":expected,"proof":form})
    return {"artifact_sha256":sha(artifact),"compiler":m["compiler"]["version"],"sources":sources}

def raw_prefixes(path:Path):
    result={}
    with path.open("rb") as handle,mmap.mmap(handle.fileno(),0,access=mmap.ACCESS_READ) as data:
        for match in re.finditer(rb'"(testLaunch[^"\n]*\(\))":\{',data):
            start=match.end()-1;end=data.find(b',"traces":',start)
            if end<0 or end-start>32_000_000:raise ValueError("Missing/big finite result prefix")
            name=match[1].decode()
            if name in result:raise ValueError("Repeated raw method")
            result[name]=json.loads(data[start:end]+b"}")
    return result

def main():
    base=Path(sys.argv[1]).resolve();final=base/"attempt02"
    start=json.loads((final/"START.json").read_text());outcome=json.loads((final/"RESULT.json").read_text())
    if {r["id"] for r in outcome["methods"]}!=EXPECTED or any(r["status"]!="Success" for r in outcome["methods"]):raise ValueError("Unexpected selected outcomes")
    if not outcome["source_unchanged"] or outcome["actual_test_methods"]!=3 or outcome["setup_failures"]!=0:raise ValueError("Invalid source/selection stage")
    raw=final/"forge.json"
    if sha(raw)!=outcome["raw_sha256"]:raise ValueError("Raw result hash differs")
    labels={}
    for name in SCENARIOS:
        key=keccak(name.encode());labels[key]=name
        for first in (0,8,16,24):labels[keccak(bytes.fromhex(key[2:])+first.to_bytes(32,"big"))]=f"{name} / functional chunk starting{first}"
    event=keccak(b"LaunchClaimEnvelope(bytes32,uint256,uint256,uint256,bool)")
    cold_event=keccak(b"LaunchClaimColdFootprint(uint256,uint256)")
    prefixes=raw_prefixes(raw);methods=[]
    for row in sorted(outcome["methods"],key=lambda r:r["id"]):
        name=row["id"].rsplit(".",1)[1]
        record=prefixes[name]
        if record["status"]!="Success":raise ValueError("Raw method is not successful")
        envelopes=[];footprints=[]
        for log in record.get("logs",[]):
            topics=log["topics"];data=bytes.fromhex(log["data"][2:])
            if topics and topics[0]==event:
                if len(topics)!=2 or len(data)!=128:raise ValueError("Envelope ABI differs")
                words=[int.from_bytes(data[i:i+32],"big") for i in range(0,len(data),32)]
                if words[1]!=12_000_000 or words[3] not in (0,1):raise ValueError("Envelope cap/status differs")
                envelopes.append({"scenario":labels[topics[1]],"entries":words[0],"gas_limit":words[1],
                                  "call_body_gas":words[2],"success":bool(words[3]),
                                  "body_only_20pct_arithmetic":(words[2]*120+99)//100,
                                  "arithmetic_is_not_RPC_estimate_or_full_transaction_approval":True})
            elif topics and topics[0]==cold_event:
                if len(data)!=64:raise ValueError("Cold footprint ABI differs")
                footprints.append({"accounts":int.from_bytes(data[:32],"big"),"recorded_slot_resets":int.from_bytes(data[32:],"big")})
        if not envelopes or not footprints:raise ValueError("Missing positive event evidence")
        methods.append({**row,"host_test_body_gas_not_transaction_gas":record["kind"]["Unit"]["gas"],"envelopes":envelopes,"cold_footprints":footprints})
    proofs={}
    for contract in ("LaunchClaimCapacityPending20261117Test","LaunchClaimCapacityStored20261117Test"):
        proofs[contract]=source_proof(final/(contract+".json"))
    initial=json.loads((base/"attempt01/RESULT.json").read_text())
    if any(".testLaunch" in r["id"] for r in initial["methods"]):raise ValueError("Initial setup failures were labelled tests")
    failed=[{"id":r["id"],"status":r["status"],"reason":r["reason"]} for r in initial["methods"]]
    result={"schema":1,"distinct_new_methods":3,"methods":methods,"command":start["command"],
            "forge_sha256":start["forge_sha256"],"solc_sha256":start["solc_sha256"],
            "final_raw_bytes":raw.stat().st_size,"final_raw_sha256":sha(raw),"final_source_bracket_stable":True,
            "compiled_source_proofs":proofs,"initial_setup_failures_not_executed_tests":failed,
            "initial_raw_sha256":initial["raw_sha256"],"production_source_changed":False,
            "unchanged_old_tests_run":False,"scope":"Test-only typed share writer; actual1000NFTs and financial/royalty/router code. Direct mint profile; no actualLP/OpenSea/source/provider/fee qualification. Initial cold funded-state calls vs later same-test functional recovery chunks stay separate."}
    target=Path(__file__).with_name("VERIFICATION.json");target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"methods":3,"source_checks":sum(len(p["sources"]) for p in proofs.values()),"envelopes":[{"method":m["id"],"measurements":m["envelopes"]} for m in methods]}))

if __name__=="__main__":main()
