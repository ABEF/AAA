"""Inspect local Forge configuration without building, testing, RPC or signing.

Shares the current fork runner's normal-profile validator. This records effective
settings and the Forge file identity, not compiler authenticity or release approval.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
_spec=importlib.util.spec_from_file_location('_normal_profile_policy',ROOT/'scripts/run-current-pool-fork.py')
_policy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_policy)
SAFE_DIAGNOSTICS=frozenset({
    'Normal verification requires the default profile','Reviewed Forge release required',
    'Cannot inspect effective Forge configuration','Effective Forge configuration exceeds review limit',
    'Normal verification requires the pinned compiler selection','Malformed effective Forge configuration',
    'Effective Forge configuration differs from reviewed normal profile','Malformed optimizer policy',
    'Effective Forge runtime-size gate differs from normal','Malformed effective remappings',
    'Effective remappings differ from pinned sources','Effective compiler differs from reviewed executable',
    'Effective verification paths or permissions differ from normal',
    'Filtered tests cannot constitute full verification','Normal fuzz settings differ','Normal invariant settings differ',
})


def _local_review(command,*,env,timeout):
    # Metadata only: keep raw config in memory, never a temporary output log.
    # This is a trusted local tool invocation, not an arbitrary provider command.
    return subprocess.run(command,env=env,cwd=ROOT,timeout=timeout,
                          capture_output=True,text=True,encoding='utf-8',
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)


def inspect_profile(forge='forge',environment=None,run=None):
    environment=dict(os.environ if environment is None else environment)
    run=run or _local_review
    if environment.get('FOUNDRY_PROFILE','default')!='default':
        raise ValueError('Normal verification requires the default profile')
    version=run([forge,'--version'],env=environment,timeout=30)
    if version.returncode or not re.search(r'\bVersion:\s*1\.4\.4(?:-v1\.4\.4)?(?:\s|$)',version.stdout) or _policy.FORGE_COMMIT not in version.stdout:
        raise ValueError('Reviewed Forge release required')
    response=run([forge,'config','--json','--root',str(ROOT)],env=environment,timeout=30)
    if response.returncode:raise ValueError('Cannot inspect effective Forge configuration')
    if len(response.stdout)>4*1024*1024:raise ValueError('Effective Forge configuration exceeds review limit')
    config=_policy.strict_json_loads(response.stdout)
    if not isinstance(config,dict) or config.get('solc')!='0.8.26':
        raise ValueError('Normal verification requires the pinned compiler selection')
    reviewed=_policy.reviewed_effective_config(config,'0.8.26')
    extra={'out':'out','cache_path':'cache','skip':[],
           'fs_permissions':[{'access':'write','path':'./deployments'}]}
    for key,value in extra.items():
        if key not in config or type(config[key]) is not type(value) or config[key]!=value:
            raise ValueError('Effective verification paths or permissions differ from normal')
    for key in ('match_test','no_match_test','match_contract','no_match_contract','match_path','no_match_path'):
        if key not in config or config[key] is not None:
            raise ValueError('Filtered tests cannot constitute full verification')
    fuzz=config.get('fuzz');invariant=config.get('invariant')
    if not isinstance(fuzz,dict) or type(fuzz.get('runs')) is not int or fuzz['runs']!=1000:
        raise ValueError('Normal fuzz settings differ')
    expected={'runs':32,'depth':128,'fail_on_revert':True}
    if not isinstance(invariant,dict) or any(type(invariant.get(k)) is not type(v) or invariant.get(k)!=v for k,v in expected.items()):
        raise ValueError('Normal invariant settings differ')
    executable=Path(shutil.which(forge) or forge)
    return {'kind':'local_effective_normal_profile','configuration':{**reviewed,**extra},
            'fuzz_runs':1000,'invariant':expected,
            'forge_commit':_policy.FORGE_COMMIT,
            'forge_file_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'source_compiler_selection':'0.8.26','compiler_binary_authenticated':False,
            'build_or_tests_executed':False,'production_approved':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--forge',default='forge');args=parser.parse_args(argv)
    try:report=inspect_profile(args.forge)
    except Exception as exc:
        # Forge configuration/stderr may contain keys or credentialed URLs.
        message=str(exc) if type(exc) is ValueError and str(exc) in SAFE_DIAGNOSTICS else 'Effective normal verification profile could not be validated; review the local toolchain and settings.'
        print('BLOCKED: '+message,file=sys.stderr)
        return 1
    print(json.dumps(report,sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
