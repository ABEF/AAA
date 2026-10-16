import datetime as dt
import importlib.util
from pathlib import Path
import time
import unittest
import json
import subprocess
import tempfile
from unittest.mock import patch
from keeper.ops import digest
from keeper import staging_observer as observer

spec=importlib.util.spec_from_file_location('staging_monitor',Path(__file__).resolve().parents[1]/'scripts/check-staging-monitor.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)


class StagingMonitorTests(unittest.TestCase):
    def setUp(self):
        self.now=int(time.time());stamp=dt.datetime.fromtimestamp(self.now,dt.timezone.utc).isoformat()
        payload={'created_at':stamp,'state':{'chain_id':31337}}
        self.data={'created_at':stamp,'staging_only':True,'chain_id':31337,'health':{'ok':True},
            'backup':{'ok':True,'snapshot':{'payload':payload,'sha256':digest(payload)}}}
    def test_good_export(self):self.assertTrue(monitor.validate_export(self.data,self.now)[0]['ok'])
    def test_stale_or_future_export(self):
        self.assertFalse(monitor.validate_export(self.data,self.now+901)[0]['ok'])
        self.assertFalse(monitor.validate_export(self.data,self.now-31)[0]['ok'])
    def test_failed_health_or_backup(self):
        self.data['health']['ok']=False;self.assertFalse(monitor.validate_export(self.data,self.now)[0]['ok'])
        self.data['health']['ok']=True;self.data['backup']['ok']=False
        self.assertFalse(monitor.validate_export(self.data,self.now)[0]['ok'])
    def test_corrupt_snapshot(self):
        self.data['backup']['snapshot']['sha256']='0'*64
        with self.assertRaises(ValueError):monitor.validate_export(self.data,self.now)
    def test_wrong_chain(self):
        self.data['chain_id']=4663
        with self.assertRaises(ValueError):monitor.validate_export(self.data,self.now)
    def test_missing_snapshot(self):
        self.data['backup'].pop('snapshot')
        self.assertFalse(monitor.validate_export(self.data,self.now)[0]['ok'])

    def test_stopped_service_overrides_a_fresh_healthy_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config=root/'config.json';export=root/'export.json';backups=root/'backups';backups.mkdir()
            config.write_text(json.dumps({'chain_id':31337,'rpc_urls':['http://127.0.0.1:18545']}))
            def create(config,path):path.write_text(json.dumps(self.data['backup']['snapshot']));return {'ok':True}
            with patch.object(observer,'CONFIG',config),patch.object(observer,'EXPORT',export),patch.object(observer,'BACKUPS',backups), \
                    patch.object(observer,'health_check',return_value={'ok':True,'reasons':[]}), \
                    patch.object(observer,'create_snapshot',side_effect=create), \
                    patch.object(observer.subprocess,'run',return_value=subprocess.CompletedProcess([],3,'inactive','')) as systemctl, \
                    patch('builtins.print'):
                observer.main()
            report=json.loads(export.read_text());self.assertFalse(report['health']['ok']);self.assertTrue(report['backup']['ok'])
            self.assertEqual(len(systemctl.call_args_list),2)
            self.assertTrue(all(c.args[0][:2]==['/usr/bin/systemctl','is-active'] for c in systemctl.call_args_list))

    def test_observer_refuses_public_chain_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'config.json';config.write_text(json.dumps({'chain_id':4663,'rpc_urls':['https://rpc.invalid']}))
            with patch.object(observer,'CONFIG',config),patch.object(observer,'create_snapshot') as snapshot:
                with self.assertRaises(ValueError):observer.main()
                snapshot.assert_not_called()
