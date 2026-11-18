"""Copy the affected exact host recovery fixture to a fresh isolated project."""
from pathlib import Path
import hashlib, json, shutil

R=Path(__file__).resolve().parents[2]
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
B=V/'activation-gas-20261118/lp-packed-canonical'
O=V/'activation-final-six-20261118/lp-canonical'
O.mkdir(parents=True,exist_ok=False)
manifest=json.loads((B/'SOURCE_CLOSURE.json').read_bytes())
root_sources=manifest['root_sources']
for folder in ('src','test','node_modules'):
    shutil.copytree(B/folder,O/folder)
for name in ('foundry.toml','run_actual.py'):
    (O/name).write_bytes((B/name).read_bytes())
pins={}
for name in root_sources:
    raw=(R/name).read_bytes()
    (O/name).parent.mkdir(parents=True,exist_ok=True)
    (O/name).write_bytes(raw)
    pins[name]=hashlib.sha256(raw).hexdigest()
runner=(O/'run_actual.py').read_text(encoding='utf-8')
runner=runner.replace("'new_methods_expected':2,'old_test_methods_selected':False", "'affected_existing_methods_expected':2,'unchanged_methods_selected':False")
(O/'run_actual.py').write_text(runner,encoding='utf-8',newline='\n')
manifest['root_sources']=pins
manifest['scope']='Two affected existing actual Rewards/immutable codec methods; fresh sentinel source, no whole coordinator qualification'
(O/'SOURCE_CLOSURE.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
(O/'FIXTURE_REUSE.json').write_text(json.dumps({
    'original_project':str(B),
    'test_file_sha256':{p.relative_to(B).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in(B/'test').rglob('*.sol')},
    'tests_byte_identical':all((O/p.relative_to(B)).read_bytes()==p.read_bytes()for p in(B/'test').rglob('*.sol')),
    'methods_reexecuted_because_actual_private_carry_codec_changes':True,
    'old_failed_raw_inspectors_not_selected':True,
    'existing_chain_or_journal_input':False,
},indent=2)+'\n',encoding='utf-8')
print(O)
