"""Isolated, offline runner for the three new launch claim workload methods."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--evidence",required=True,type=Path)
    parser.add_argument("--stage",required=True)
    parser.add_argument("--tests",default="^testLaunch")
    args=parser.parse_args()
    base=args.evidence.resolve()
    stage=base/args.stage
    stage.mkdir(parents=True,exist_ok=False)
    tool_root=base.parents[1]
    forge=tool_root/"foundry-v1.4.4/forge.exe"
    solc=tool_root/"toolchain-0.8.26/solc.exe"
    names=subprocess.check_output(["git","ls-files","src","test"],cwd=ROOT,text=True).splitlines()
    names.append("test/LaunchClaimCapacity20261117.t.sol")
    names.append("foundry.toml")
    names=sorted(set(names))
    before={name:digest(ROOT/name) for name in names}
    selected=ROOT/"test/LaunchClaimCapacity20261117.t.sol"
    (stage/selected.name).write_bytes(selected.read_bytes())
    command=[str(forge),"test","--root",str(ROOT),"--offline","--use",str(solc),
             "--match-path","test/LaunchClaimCapacity20261117.t.sol",
             "--match-contract","LaunchClaimCapacity.*Test","--match-test",args.tests,
             "--code-size-limit","1000000","--out",str(base/"out"),
             "--cache-path",str(base/"cache"),"-vvv","--json"]
    # Construct an OS-only environment; do not inherit keys, RPC endpoints,
    # FOUNDRY/DAPP overrides, credentials or wallet options, and do not log it.
    allow={"SystemRoot","WINDIR","PATH","PATHEXT","TEMP","TMP","USERPROFILE","LOCALAPPDATA","APPDATA","COMSPEC"}
    env={k:v for k,v in os.environ.items() if k.upper() in {a.upper() for a in allow}}
    env["FOUNDRY_PROFILE"]="default"
    start={"command":command,"forge_sha256":digest(forge),"solc_sha256":digest(solc),
           "environment":"OS-only allowlist plus explicit default profile; no RPC/wallet variables",
           "source_sha256":before,"test_code_size_limit_is_not_production_gate":True}
    (stage/"START.json").write_text(json.dumps(start,indent=2)+"\n",encoding="utf-8")
    t=time.monotonic()
    with (stage/"forge.json").open("wb") as output,(stage/"stderr.log").open("wb") as error:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=output,stderr=error,check=False)
    after={name:digest(ROOT/name) for name in names}
    suites={}
    for line in (stage/"forge.json").read_text(encoding="utf-8-sig").splitlines():
        if line.startswith('{"test/'):
            suites=json.loads(line)
    methods=[]
    for suite,record in suites.items():
        for method,recorded in record.get("test_results",{}).items():
            methods.append({"id":f"{suite}.{method}","status":recorded["status"],"reason":recorded["reason"]})
    for contract in ("LaunchClaimCapacityPending20261117Test","LaunchClaimCapacityStored20261117Test"):
        artifact=base/"out/LaunchClaimCapacity20261117.t.sol"/(contract+".json")
        if artifact.exists():(stage/(contract+".json")).write_bytes(artifact.read_bytes())
    final={"exit_code":result.returncode,"elapsed_seconds":time.monotonic()-t,
           "source_after_sha256":after,"source_unchanged":after==before,"methods":methods,
           "actual_test_methods":sum(".testLaunch" in m["id"] for m in methods),
           "setup_failures":sum(".setUp()" in m["id"] and m["status"]!="Success" for m in methods),
           "nonzero_selection":bool(methods),"raw_sha256":digest(stage/"forge.json")}
    (stage/"RESULT.json").write_text(json.dumps(final,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"stage":args.stage,"exit_code":result.returncode,"records":len(methods),
                      "actual_test_methods":final["actual_test_methods"],"setup_failures":final["setup_failures"],
                      "source_unchanged":after==before,"methods":methods}))
    return result.returncode if after==before else 3

if __name__=="__main__":
    raise SystemExit(main())
