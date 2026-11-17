"""Package selected existing observations; never rerun tests or mutate chain state."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/operator-behavior-followup-20261117')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    (REPORT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    baseline = json.loads((REPORT / 'BASELINE.json').read_text())
    assert git('rev-parse', 'HEAD').decode().strip() == baseline['baseline_commit']
    changed_sources = git('diff', '--name-only', 'HEAD', '--', 'src').decode().splitlines()
    assert changed_sources == ['src/ZZZAccessController.sol'], changed_sources
    protected = {}
    for name, expected in baseline['protected'].items():
        actual = sha((ROOT / name).read_bytes())
        assert actual == expected, name
        protected[name] = actual
    prior = {}
    names = git('ls-tree', '-r', '--name-only', 'HEAD', 'reports/operator-input-audit-20261116').decode().splitlines()
    for name in names:
        old = git('show', 'HEAD:' + name)
        current = (ROOT / name).read_bytes()
        assert current == old, name
        prior[name] = sha(current)
    report_diffs = git('diff', '--name-only', 'HEAD', '--', 'reports').decode().splitlines()
    assert report_diffs == ['reports/README.md', 'reports/source-checks.json'], report_diffs
    save('PRESERVATION.json', {
        'baseline_commit': baseline['baseline_commit'],
        'changed_production_sources': changed_sources,
        'protected_dirty_files_byte_identical': protected,
        'previous_operator_report_files_byte_identical': prior,
        'other_tracked_report_differences': report_diffs,
        'report_index_intentionally_updated': True,
        'source_checks_is_preexisting_protected_dirty_work': True,
        'existing_environment_actions_performed': [],
        'heartbeat_remains_user_paused': True,
        'public_signing_or_deployment_authorized': False,
        'production_approved': False,
    })

    deployment = (ROOT / 'zzz_ops/deployment_plan.py').read_bytes()
    final_warning = b'Empty metadata URI is constructor-valid, but Access.seal rejects until bootstrap sets a nonempty NFT.setBaseURI root. Verify NFT.artworkBaseURI and reviewed content before sealing; this plan emits neither that setup call nor seal.'
    prior_warning = b'Empty metadata URI is constructor-valid but does not qualify artwork availability.'
    assert deployment.count(final_warning) == 1
    previous_stage = deployment.replace(final_warning, prior_warning)
    new_log = EXTERNAL / 'preseal-root-prerequisite.log'
    assert new_log.is_file()
    save('PLANNER_CHECKS.json', {
        'baseline_commit': baseline['baseline_commit'],
        'observed_passed_methods': {
            'adapted': [
                'tests_python.test_deployment_build_profiles.DeploymentBuildProfileTests.test_default_planner_accepts_current_metadata_build_and_tags_identity',
                'tests_python.test_deployment_build_profiles.DeploymentBuildProfileTests.test_current_complete_graph_has_exact_objects_and_original_size_limits',
            ],
            'new_build': ['tests_python.test_deployment_build_profiles.DeploymentBuildProfileTests.test_seal_fix_keeps_previous_objects_historical_without_automatic_fallback'],
            'new_final_warning': ['tests_python.test_preseal_plan.PresealPlanTests.test_empty_constructor_root_requires_explicit_setup_in_both_unsigned_plans'],
        },
        'unique_methods': 4,
        'earlier_build_method_source_stage': {
            'zzz_ops/deployment_plan.py_sha256': sha(previous_stage),
            'stage_reconstruction': 'Final warning-only line replaced with exact preceding text; no other deployment source edit followed those three observed checks.',
            'terminal_results': '2 adapted methods pass, then 1 new method passes in tool session; raw terminal logs were not retained.',
        },
        'final_warning_case': {
            'raw_log_sha256': sha(new_log.read_bytes()),
            'zzz_ops/deployment_plan.py_sha256': sha(deployment),
            'zzz_ops/preseal_plan.py_sha256': sha((ROOT / 'zzz_ops/preseal_plan.py').read_bytes()),
            'tests_python/test_preseal_plan.py_sha256': sha((ROOT / 'tests_python/test_preseal_plan.py').read_bytes()),
            'outcome': 'one new method pass; no old method rerun',
        },
        'signing_rpc_deployment_sealing': False,
    })

    sources = sorted(ROOT.glob('src/**/*.sol'))
    additional = [
        'keeper/monitor.py', 'scripts/run-keeper-tests.py', 'scripts/check-slither-review.py',
        'zzz_ops/deployment_plan.py', 'zzz_ops/preseal_plan.py',
        'test/OperatorSealArtwork20261117.t.sol', 'test/AccessController.t.sol',
        'test/CanonicalPreparation.t.sol', 'test/OperatorControls.t.sol',
        'test/OptionalPortfolioCore.t.sol', 'test/RoyaltyRecovery.t.sol', 'test/mocks/Mocks.sol',
        'tests_python/test_deployment_build_profiles.py', 'tests_python/test_preseal_plan.py',
        'tests_python/test_keeper_maintenance_clock.py', 'tests_python/test_keeper_standalone_harvest_review.py',
    ]
    sources.extend(ROOT / name for name in additional)
    save('SOURCE_SNAPSHOT.json', {
        'production_sources': 61,
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources},
        'compiler_lf_source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes().replace(b'\r\n', b'\n')) for p in sources if p.suffix == '.sol'},
        'production_approved': False,
    })

    selected = sorted(p for p in (EXTERNAL / 'static-exclusive').rglob('*') if p.is_file())
    selected += sorted(p for p in EXTERNAL.iterdir() if p.is_file())
    archive = REPORT / 'supporting-evidence.zip'
    rows = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for path in selected:
            name = path.relative_to(EXTERNAL).as_posix()
            raw = path.read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, raw, compresslevel=6)
            rows.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        for row in rows:
            assert sha(check.read(row['path'])) == row['sha256']
    save('SUPPORTING_EVIDENCE.json', {
        'archive': archive.name, 'bytes': archive.stat().st_size,
        'sha256': sha(archive.read_bytes()), 'entries': rows,
        'excluded': 'Giant test output/cache trees and existing environment files; accepted normal compiler input/output are separate tracked compressed build files.',
        'tests_rerun_for_packaging': 0,
    })
    print(json.dumps({'packaged_files': len(rows), 'archive_bytes': archive.stat().st_size,
                      'protected_files': len(protected), 'prior_report_files': len(prior),
                      'test_methods_executed': 0}))


if __name__ == '__main__':
    main()
