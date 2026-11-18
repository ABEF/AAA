from pathlib import Path
import hashlib,json,os,subprocess,time,sys
O=Path(__file__).resolve().parent;R=Path("C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2");V=O.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
names=sorted([p.relative_to(R).as_posix()for p in(R/"src").rglob("*.sol")]+["foundry.toml","reports/source-checks.json","scripts/run-fork-checks.py","tests_python/test_fork_runner.py","tests_python/test_frontend_history.py"])
before={p:sha(R/p)for p in names};own={p.relative_to(O).as_posix():sha(p)for d in ["src","test","deps"]for p in(O/d).rglob("*.sol")}
E=O/sys.argv[1];E.mkdir(exist_ok=False)
forge=V/"foundry-v1.4.4/forge.exe";solc=V/"toolchain-0.8.26/solc.exe"
cmd=[str(forge),"test","--offline","--root",str(O),"--use",str(solc),"--match-contract","^FeedDifferential20261118Test$","--code-size-limit","1000000","--json","-vv"]
expected=int(sys.argv[3])if len(sys.argv)>3 else 6
if len(sys.argv)>2:cmd.extend(["--match-test",sys.argv[2]])
env={k:v for k,v in os.environ.items()if k.upper()in {"SYSTEMROOT","WINDIR","PATH","PATHEXT","TEMP","TMP","USERPROFILE","LOCALAPPDATA","APPDATA","COMSPEC"}};env["FOUNDRY_PROFILE"]="default"
(E/"START.json").write_text(json.dumps({"command":cmd,"root_before":before,"own_sources":own,"forge_sha256":sha(forge),"solc_sha256":sha(solc),"unchanged_old_test_methods_executed":0},indent=2)+"\n",encoding="utf-8")
t=time.monotonic()
with(E/"stdout.json").open("wb")as out,(E/"stderr.log").open("wb")as err:r=subprocess.run(cmd,cwd=O,env=env,stdout=out,stderr=err,timeout=300)
after={p:sha(R/p)for p in names};methods=[]
for line in(E/"stdout.json").read_text(encoding="utf-8-sig").splitlines():
 if line.startswith('{"test/'):
  suites=json.loads(line)
  methods=[{"id":k+":"+m,"status":v["status"],"reason":v.get("reason"),"logs":v.get("decoded_logs",[])}for k,s in suites.items()for m,v in s.get("test_results",{}).items()]
result={"returncode":r.returncode,"seconds":time.monotonic()-t,"root_source_unchanged":before==after,"methods":methods,"actual_count":len(methods),"pass":r.returncode==0 and len(methods)==expected and all(x["status"]=="Success"for x in methods) and before==after,"stdout_sha256":sha(E/"stdout.json"),"stderr_sha256":sha(E/"stderr.log")}
(E/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,indent=2));sys.exit(0 if result["pass"]else 1)
