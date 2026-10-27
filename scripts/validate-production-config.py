#!/usr/bin/env python3
"""Current native LP-only inventory gate. Never signs, deploys or reads a chain.

The default path evaluates only the explicit current native profile. Historical
bridge/creator inventory code is imported lazily only when the operator requests
--historical-consistency; its output never qualifies the current release.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def validate(config: Any, *, expected_commit: str | None = None, now: int | None = None) -> dict[str,Any]:
    """Evaluate current release only; old configuration never enters legacy code."""
    # Accounting4 changes terminal rights and removes external custody. The
    # historical accounting3 inventory/observer cannot qualify that new ABI.
    # Keep this explicit release gate closed until the new inventory acceptance
    # is independently implemented and reviewed; never reuse a historical ready.
    return {'schema_version':6,'status':'blocked','ready':False,'deployment_authorized':False,
        'current_release_gate':True,'production_qualification_supported':False,
        'issues':[{'code':'holder_exit_qualification_pending','path':'current_release_profile',
            'message':'Fresh source requires accounting4/custody3/canonical holder-exit V5. Its production inventory and operating qualification remain open. Accounting3 is historical; use explicit --historical-consistency only for inspection.'}],
        'limitations':['Source implementation and focused tests do not qualify actual release bindings, services or deployment.']}


def read_config(path: Path) -> Any:
    with path.open('rb') as source:
        raw=source.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:raise ValueError('Inventory exceeds bounded file size')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('Repeated inventory key')
            result[key]=value
        return result
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))

def write_report(path: Path,encoded: str) -> None:
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='\n',
                dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp',delete=False) as report:
            temporary=Path(report.name);report.write(encoded);report.flush();os.fsync(report.fileno())
        os.replace(temporary,path);temporary=None
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True);parser.add_argument('--expected-commit');parser.add_argument('--output')
    parser.add_argument('--historical-consistency',action='store_true',
        help='Lazily inspect historical consistency only; never qualify the current release')
    args=parser.parse_args()
    try:
        config=read_config(Path(args.config))
        if args.historical_consistency:
            from zzz_ops.historical_production import validate as validate_historical
            result=validate_historical(config,expected_commit=args.expected_commit,now=int(time.time()))
            result.update(current_release_gate=False,approval_scope='historical_manifest_consistency_only',
                production_qualification_supported=False,deployment_authorized=False)
        else:
            result=validate(config,expected_commit=args.expected_commit,now=int(time.time()))
    except (OSError,UnicodeError,ValueError,RecursionError,TypeError,KeyError,OverflowError) as exc:
        result={'schema_version':4 if args.historical_consistency else 5,'status':'blocked','ready':False,
            'deployment_authorized':False,'current_release_gate':not args.historical_consistency,
            'production_qualification_supported':False,
            'issues':[{'code':'config.unreadable','path':'config','message':type(exc).__name__}]}
    if args.output and Path(args.output).resolve()==Path(args.config).resolve():
        result.update(status='blocked',ready=False,deployment_authorized=False,
            issues=[{'code':'output.path_conflict','path':'output','message':'Report must not overwrite the inventory input'}])
        result.pop('blockers',None)
    encoded=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output and not any(i['code']=='output.path_conflict' for i in result['issues']):
        try:write_report(Path(args.output),encoded)
        except OSError:
            print(json.dumps({'status':'blocked','ready':False,'deployment_authorized':False,
                'current_release_gate':not args.historical_consistency,
                'production_qualification_supported':False,
                'issues':[{'code':'output.unavailable','path':'output','message':'Report could not be replaced atomically'}]}))
            return 1
    print(encoded,end='');return 0 if result['ready'] else 1


if __name__=='__main__':sys.exit(main())
