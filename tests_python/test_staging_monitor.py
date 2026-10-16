import datetime as dt
import importlib.util
from pathlib import Path
import time
import unittest
from keeper.ops import digest

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
