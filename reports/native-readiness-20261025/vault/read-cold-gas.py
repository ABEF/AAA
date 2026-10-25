from pathlib import Path
import subprocess,time,json,os,re
E=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9');B=E/'vault-headroom-20261025';P=B/'scoped-profile'
cmd=[str(E/'foundry-v1.4.4/forge.exe'),'test','--root',str(P),'--use',str(E/'toolchain-0.8.26/solc.exe'),'--match-contract','CombinedCapacityGasTest','--match-test','^testColdActivationWithEveryHistoricalRewardIndexPopulated','-vv']
env=os.environ.copy();env['RAYON_NUM_THREADS']='2';t=time.monotonic();p=subprocess.run(cmd,capture_output=True,env=env,timeout=300)
(B/'cold-gas.log').write_bytes(p.stdout);(B/'cold-gas.stderr.log').write_bytes(p.stderr)
match=re.search(rb'combined\.4-buckets\.32-indexed-assets\.activation:\s*(\d+)',p.stdout)
report={'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-t,'command':cmd,'cold_activation_gas':int(match[1]) if match else None,'unchanged_budget':12000000,'budget_margin':12000000-int(match[1]) if match else None,'scope':'Same cached test/source/profile, one repeated case only to retain named gas log. Not an additional distinct test and not real maximal-market gas qualification.'}
(B/'cold-gas.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(p.stdout.decode(errors='replace'));print(json.dumps(report,indent=2));assert p.returncode==0 and match and report['cold_activation_gas']<report['unchanged_budget']
