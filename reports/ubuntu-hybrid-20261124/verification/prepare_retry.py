from pathlib import Path
import ast,hashlib,json
base=Path(__file__).resolve().parent
old=base/'hybrid';new=base/'hybrid-retry';new.mkdir(exist_ok=False)
changes=[]
for name in ('keeper_runtime.py','keeper_jobs.py','job_cases.py','run_jobs.py'):
    raw=(old/name).read_bytes();text=raw.decode()
    text=text.replace('popl-ubuntu-hybrid-20261124-c7ff','popl-ubuntu-hybrid-20261124-c800')
    if name=='run_jobs.py':
        needle="c.stage='stock_configuration';c.configure()"
        assert text.count(needle)==1
        text=text.replace(needle,"c.stage='stock_configuration';c.owner_on();c.configure()")
        needle='need(released>=0 and new[\'buyback\']'
        assert text.count(needle)==1
        text=text.replace(needle,'need(new[\'compound\']==0 and released==old[\'compound\']+units and new[\'buyback\']')
    ast.parse(text);output=text.encode();(new/name).write_bytes(output)
    changes.append({'file':name,'before':hashlib.sha256(raw).hexdigest(),'after':hashlib.sha256(output).hexdigest(),'bytes':len(output)})
pack=(base/'package_lab.py').read_text()
pack=pack.replace("TARGETS={'hybrid':'c7ff'}","TARGETS={'hybrid-retry':'c800'}")
pack=pack.replace("feature=args.feature.removesuffix('-fee-retry')","feature=args.feature.removesuffix('-retry')")
ast.parse(pack);(base/'package_retry.py').write_text(pack)
(new/'CHANGES.json').write_text(json.dumps({'prior_original_preserved':True,'production_changes':False,'changes':['fixed new setup owner impersonation before configure only','tightened post-replacement compound reserve assertion','new fixed isolated c800 path'], 'helpers':changes},indent=2)+'\n')
print(json.dumps(changes))
