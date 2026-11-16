"""Explicit historical checkout for the original planner boundary properties.

Keeps their accepted constructor-size assertions historical while the normal
planner defaults to metadata2. No source/build is downloaded or compiled.
"""
import functools,gzip,hashlib,importlib.util,json,shutil,tempfile
from pathlib import Path
from zzz_ops import deployment_plan as current

_temporary=tempfile.TemporaryDirectory(prefix='popl-legacy-deployment-fixture-')
_root=Path(_temporary.name)
_spec=current.trusted_build(current.LEGACY_BUILD_PROFILE)
for _name,_pin in _spec['files'].items():
    _source=current.ROOT/_spec['directory']/_name;_raw=_source.read_bytes()
    if hashlib.sha256(_raw).hexdigest()!=_pin:raise ValueError('Legacy fixture build pin mismatch')
    _target=_root/_spec['directory']/_name;_target.parent.mkdir(parents=True,exist_ok=True);_target.write_bytes(_raw)
_input=json.loads(gzip.decompress((_root/_spec['directory']/'compiler-input.json.gz').read_bytes()))
for _name,_entry in _input['sources'].items():
    _target=(_root/_name).resolve()
    if not _target.is_relative_to(_root):raise ValueError('Unsafe legacy fixture source path')
    _target.parent.mkdir(parents=True,exist_ok=True);_target.write_bytes(_entry['content'].encode('utf8'))
for _name in ('zzz_ops/deployment_plan.py','config/deployment-preparation.example.json'):
    _target=_root/_name;_target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current.ROOT/_name,_target)
_loader=importlib.util.spec_from_file_location('explicit_legacy_deployment_plan',_root/'zzz_ops/deployment_plan.py')
deployment_plan=importlib.util.module_from_spec(_loader);_loader.loader.exec_module(deployment_plan)
_prepare=deployment_plan.prepare;_main=deployment_plan.main
deployment_plan.prepare=functools.partial(_prepare,build_profile=current.LEGACY_BUILD_PROFILE)
def _legacy_main(argv):
    return _main([*argv,'--build-profile',current.LEGACY_BUILD_PROFILE])
deployment_plan.main=_legacy_main
