from pathlib import Path
import hashlib,importlib.util,json,re,sys
R=Path.cwd();E=Path(__file__).resolve().parent
sys.path.insert(0,str(R))
s=importlib.util.spec_from_file_location('review',R/'scripts/check-slither-review.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
old=json.loads((R/'reports/opensea-integration-20261109/static-review.json').read_text(encoding='utf-8'))
before={x['fingerprint']:x for x in old['findings']}
report=json.loads((E/'static-417c118f1d/detectors-only.json').read_text(encoding='utf-8'))
changed={p.relative_to(R).as_posix() for p in (R/'src').rglob('*.sol') if m.source_hash(p)!=old['source_sha256_lf'].get(p.relative_to(R).as_posix())}
assert changed=={'src/ZZZMigrationBudget.sol'}
fresh=[];reuse=[]
for finding in report['results']['detectors']:
    fp=m.fingerprint(finding);desc=m.normalized_description(finding);paths=set(re.findall(r'src/[^\s()#]+\.sol',desc))
    if fp in before and not paths&changed:
        reuse.append({'fingerprint':fp,'prior':before[fp],'referenced_paths':sorted(paths)})
    else:
        fresh.append({'fingerprint':fp,'check':finding['check'],'impact':finding['impact'],'confidence':finding['confidence'],'description':desc,'referenced_paths':sorted(paths),'prior':before.get(fp)})
for name,obj in [('static-current-contexts.json',fresh),('static-exact-reuse.json',reuse)]:
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({'changed':sorted(changed),'fresh':len(fresh),'exact_reuse':len(reuse),'new_fingerprints':sum(x['prior']is None for x in fresh)}))
for i,x in enumerate(fresh):
    print(i,x['check'],x['description'])
    if x['prior']:print('PRIOR:',x['prior']['rationale'])
