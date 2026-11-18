"""Only eleven NEW payload methods plus six specifically changed regressions."""
from pathlib import Path
import hashlib,importlib,inspect,json,re,sys,time,unittest

R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
V=Path(r'C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
BUILD=(
 'test_default_planner_accepts_current_metadata_build_and_tags_identity',
 'test_seal_fix_keeps_previous_objects_historical_without_automatic_fallback',
 'test_current_complete_graph_has_exact_objects_and_original_size_limits')
HISTORICAL=(
 'test_current_template_explicit7_v9_has_no_observations_or_approval',
 'test_old15_cannot_enter_current_gate_or_observer',
 'test_cli_requires_explicit_historical_selector_for_schema16_and15')
PROTECTED={
 'reports/source-checks.json':'049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4',
 'scripts/run-fork-checks.py':'875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b',
 'tests_python/test_fork_runner.py':'6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9',
 'tests_python/test_frontend_history.py':'361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def inputs():
    paths={Path(__file__).resolve()}
    for directory in ('zzz_ops','frontend_api','keeper','scripts','tests_python'):
        paths.update((R/directory).rglob('*.py'))
    paths.update((R/'config').glob('*.json'))
    return {p.relative_to(R).as_posix():sha(p) for p in sorted(paths) if '__pycache__' not in p.parts}


class Results(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.executed=[]
    def startTest(self,test):self.executed.append(test.id());super().startTest(test)


def main():
    stage=sys.argv[1]
    if re.fullmatch(r'consumer-final\d{2}',stage) is None:raise ValueError('New owned stage required')
    E=V/'q03-activation-gas-20261117'/stage;E.mkdir()
    before=inputs()
    assert all(sha(R/p)==h for p,h in PROTECTED.items())
    from zzz_ops import deployment_plan as D
    if D.DEFAULT_BUILD_PROFILE!='q03-allocation-20261117':raise ValueError('Final new default is not yet admitted')
    definitions=[('tests_python.test_factory_payload4','FactoryPayload4Tests',None),
        ('tests_python.test_deployment_build_profiles','DeploymentBuildProfileTests',BUILD),
        ('tests_python.test_exact_lp_inventory','ExactLPInventoryTests',HISTORICAL)]
    selected=[]
    for name,cls_name,methods in definitions:
        module=importlib.import_module(name);cls=getattr(module,cls_name)
        assert cls.__module__==name
        names=list(methods) if methods else unittest.defaultTestLoader.getTestCaseNames(cls)
        if methods is None:assert len(names)==11
        for method in names:
            assert method in cls.__dict__ and inspect.isfunction(cls.__dict__[method])
            selected.append(cls(method))
    assert len(selected)==17 and len({t.id() for t in selected})==17
    (E/'START.json').write_text(json.dumps(dict(source_before_sha256=before,selected=[t.id() for t in selected],
        trusted_default=D.DEFAULT_BUILD_PROFILE,old_unchanged_methods_selected=0),indent=2)+'\n',encoding='utf-8')
    started=time.monotonic()
    with (E/'unittest.log').open('w',encoding='utf-8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Results).run(unittest.TestSuite(selected))
    after=inputs();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
    protected_ok=all(sha(R/p)==h for p,h in PROTECTED.items())
    success=result.wasSuccessful() and result.testsRun==17 and result.executed==[t.id() for t in selected] and not changed and protected_ok
    report=dict(stage=stage,success=success,tests_run=result.testsRun,new_payload_methods=11,
        changed_build_methods=3,changed_historical_methods=3,failures=len(result.failures),errors=len(result.errors),
        skipped=len(result.skipped),executed=result.executed,
        failure_methods=[t.id() for t,_ in result.failures],error_methods=[t.id() for t,_ in result.errors],
        source_before_sha256=before,source_after_sha256=after,source_changes=changed,
        protected_four_unchanged=protected_ok,
        duration_seconds=time.monotonic()-started,log_sha256=sha(E/'unittest.log'),
        scope='Offline source-owned compiled payload/current-default/explicit-historical compatibility. No network, signing, deployment, sealing, old suite or independent approval.')
    (E/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('stage','success','tests_run','failures','errors','skipped','duration_seconds')},indent=2))
    return 0 if success else 1


if __name__=='__main__':raise SystemExit(main())
