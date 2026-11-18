"""Final readonly artifact/source/docs integrity; runs no test/compiler/RPC."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
sys.path.insert(0,str(R))
from zzz_ops import deployment_plan as D,factory_code_v6 as F6

O=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/activation-final-six-20261118')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
freeze=json.loads((O/'SOURCE_FREEZE.json').read_bytes())
assert freeze['source_sha256']=={p.relative_to(R).as_posix():sha(p.read_bytes())for p in(R/'src').rglob('*.sol')}
assert all(sha((R/n).read_bytes())==pin for n,pin in freeze['protected_sha256'].items())
assert sha((R/'foundry.toml').read_bytes())==freeze['foundry_toml_sha256']
assert sha((R/'test/RoyaltyRoundsCapacity20261118.t.sol').read_bytes())==freeze['fixture_sha256']
artifacts=D.Artifacts();artifacts.check_sources();assert artifacts.profile=='activation-final-six-20261118'
assert F6.verify_compiler_output(artifacts.output)
summary=json.loads((O/'full01/local-rpc/SUMMARY.json').read_bytes())
assert summary['verification_complete']and len(summary['results'])==len(summary['meets_20m_cases'])==13
assert not summary['fails_20m_cases']and all(r['owned_node_stopped']for r in summary['results'])
assert max(r['padded_gas']for r in summary['results'])==19_753_079
consumer=json.loads((P/'consumer/RESULT.json').read_bytes())
static=json.loads((P/'static/STATIC_RESULT.json').read_bytes())
assert consumer['pass']is True and consumer['source_brackets_stable']is True
assert (consumer['new_distinct_methods'],consumer['affected_distinct_methods'],consumer['distinct_methods_with_passing_evidence'])==(7,5,12)
assert consumer['test_source_restored_exact_final02']is True and consumer['discarded_extra_class_removed']is True
assert all(sha((P/'consumer'/name).read_bytes())==pin for name,pin in consumer['evidence'].items())
assert static['actual_analyzer_completed']and static['all601_records_covered']and static['default_current']
assert sha((R/'scripts/check-slither-review.py').read_bytes())==static['default_checker_sha256']
assert sha((R/'tests_python/test_slither_current_default.py').read_bytes())==static['new_test_sha256']
changed=subprocess.check_output(['git','diff','HEAD','--name-only','-z'],cwd=R).decode().split('\0')
owned=[p for p in changed if p and p not in freeze['protected_sha256']]
extra=['zzz_ops/factory_code_v6.py','tests_python/factory_payload_archive.py','tests_python/test_factory_payload6.py','tests_python/test_slither_current_default.py']
python_paths=sorted(set(n for n in owned+extra if n.endswith('.py'))|{p.relative_to(R).as_posix()for p in P.rglob('*.py')})
for name in python_paths:ast.parse((R/name).read_text(encoding='utf-8-sig'),filename=name)
markdown=[R/n for n in owned if n.endswith('.md')]+list(P.rglob('*.md'))
broken=[];checked=0
for p in markdown:
    for raw in re.findall(r'(?<!!)\[[^\]]*\]\(([^\n]+?)\)',p.read_text(encoding='utf-8')):
        target=raw.split(' "',1)[0].strip('<> ')
        if not target or target.startswith('#')or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
        target=unquote(target.split('#',1)[0]);q=(p.parent/target).resolve();checked+=1
        if not q.exists():broken.append({'file':p.relative_to(R).as_posix(),'target':target})
assert not broken,broken
result={'schema':1,'source_freeze_61_matches':True,'all100_trusted_sources_match':True,'protected_four_native_hashes':freeze['protected_sha256'],
 'foundry_and_fixture_unchanged':True,'F6_matches_trusted_output':True,'all13_complete_and_full_margin_pass':True,
 'all13_owned_nodes_stopped':True,'syntax_parsed_python_files':python_paths,'checked_relative_markdown_file_links':checked,'broken_relative_file_links':broken,
 'scope':'Final readonly integrity and affected-document file targets; not test execution, all historical anchors, public CI or release approval.',
 'test_compiler_rpc_or_signing_execution':False,'production_approved':False}
(P/'FINAL_INTEGRITY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k not in ('syntax_parsed_python_files','protected_four_native_hashes')},indent=2))
