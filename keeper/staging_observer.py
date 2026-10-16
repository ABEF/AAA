"""Export health and a secret-free snapshot for the isolated staging monitor.

No network requests or signing. The exporter is deliberately restricted to the
local fixture configuration. Read access to its export gives no keeper authority.
"""
import datetime as dt
import json
from pathlib import Path
import sys
import time
from keeper.monitor import error_context
from keeper.ops import create_snapshot, health_check
from zzz_ops.state import atomic_json

CONFIG=Path('/var/lib/zzz-keeper-staging/keeper/config.json')
EXPORT=Path('/var/lib/zzz-stage-monitor/export/status.json')
BACKUPS=Path('/var/lib/zzz-keeper-staging/backups')


def main():
    config=json.loads(CONFIG.read_text())
    if config['chain_id']!=31337 or config['rpc_urls']!=['http://127.0.0.1:18545']:
        raise ValueError('Exporter only supports isolated staging')
    report={'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'staging_only':True,'chain_id':31337}
    try:report['health']=health_check(config,max_age=180)
    except Exception as exc:report['health']={'ok':False,'reasons':['health_unavailable'],**error_context(exc)}
    # Finite local retention budget. Never silently overwrite/delete old recovery evidence.
    if sum(1 for _ in BACKUPS.glob('observer-*.json'))>=10000:
        report['backup']={'ok':False,'reason':'retention_budget_requires_operator_review'}
    else:
        path=BACKUPS/f'observer-{time.time_ns()}.json'
        try:
            result=create_snapshot(config,path)
            report['backup']={**result,'snapshot':json.loads(path.read_text())}
        except Exception as exc:report['backup']={'ok':False,**error_context(exc)}
    atomic_json(EXPORT,report);EXPORT.chmod(0o640)
    print(json.dumps({'staging_export_written':True,'health_ok':report['health']['ok'],'backup_ok':report['backup']['ok']}))


if __name__=='__main__':
    try:main()
    except Exception as exc:print(json.dumps({'staging_export_written':False,**error_context(exc)}));sys.exit(1)
