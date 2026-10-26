"""Source-bound offline before/after harvest and intent-isolation regressions."""
from pathlib import Path
import contextlib, hashlib, importlib.util, io, json, subprocess, sys, tempfile, time, unittest

R = Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
E = Path(__file__).parent
REV = 'da7ec983394d94d7812e054260398eca71418ff7'
MODE = sys.argv[1]
assert MODE in ('before', 'after', 'affected')
sys.path.insert(0, str(R))
with tempfile.TemporaryDirectory() as directory:
    if MODE == 'before':
        original = subprocess.check_output(['git', 'show', REV+':keeper/monitor.py'], cwd=R)
        path = Path(directory) / 'monitor_before.py'; path.write_bytes(original)
        import keeper
        spec = importlib.util.spec_from_file_location('keeper.monitor', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules['keeper.monitor'] = module; keeper.monitor = module
        spec.loader.exec_module(module)
    import tests_python.test_keeper_harvest_isolation as tests
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    if MODE == 'affected':
        import tests_python.test_keeper_maintenance_policy as maintenance
        suite = unittest.TestSuite((suite, unittest.defaultTestLoader.loadTestsFromModule(maintenance)))
    expected_methods = 33 if MODE == 'affected' else 16
    inputs = {}
    for name, module in list(sys.modules.items()):
        if name.startswith(('keeper.', 'zzz_ops.', 'tests_python.')) and getattr(module, '__file__', None):
            path = Path(module.__file__).resolve()
            if path.is_relative_to(R) and path.suffix == '.py':
                inputs[path.relative_to(R).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    stream = io.StringIO(); started = time.monotonic()
    with contextlib.redirect_stdout(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    changed = [name for name, expected in inputs.items() if hashlib.sha256((R / name).read_bytes()).hexdigest() != expected]
    (E / (MODE+'.log')).write_text(stream.getvalue(), encoding='utf-8', newline='\n')
    record = {'mode': MODE, 'original_revision': REV if MODE == 'before' else None,
        'source_sha256': inputs, 'source_changes_during_run': changed,
        'original_monitor_sha256': hashlib.sha256(original).hexdigest() if MODE == 'before' else None,
        'candidate_monitor_sha256': hashlib.sha256((R / 'keeper/monitor.py').read_bytes()).hexdigest(),
        'tests_run': result.testsRun, 'failures': [item.id() for item, text in result.failures],
        'errors': [item.id() for item, text in result.errors], 'skips': [(item.id(), reason) for item, reason in result.skipped],
        'elapsed_seconds': round(time.monotonic() - started, 3), 'no_signing_or_services': True}
    (E / (MODE+'.json')).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'mode': MODE, 'tests_run': result.testsRun, 'failure_records': len(result.failures),
        'errors': len(result.errors), 'skips': len(result.skipped), 'source_changes': changed}))
    assert result.testsRun == expected_methods and not result.errors and not result.skipped and not changed
    assert len(result.failures) == (13 if MODE == 'before' else 0)
