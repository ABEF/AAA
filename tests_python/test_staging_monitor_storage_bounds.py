"""New desktop archive bounds only; no monitor, SSH, keeper cycle or old tests."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec=importlib.util.spec_from_file_location('bounded_staging_monitor',
    Path(__file__).resolve().parents[1]/'scripts/check-staging-monitor.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)


class StagingMonitorStorageBoundsTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.folder=self.root/'archive'
        payload={'created_at':'2026-11-27T12:00:00+00:00','state':{'chain_id':31337}}
        self.snapshot={'payload':payload,'sha256':monitor.digest(payload)}
        self.raw=(json.dumps(self.snapshot,sort_keys=True,indent=2)+'\n').encode()
        self.target=self.folder/(self.snapshot['sha256']+'.json')
        forbidden=patch.object(monitor,'run_read_process',side_effect=AssertionError('Transport must not run'))
        forbidden.start();self.addCleanup(forbidden.stop)

    def existing(self,raw=None):
        self.folder.mkdir();self.target.write_bytes(self.raw if raw is None else raw)

    def test_new_snapshot_preserves_format_and_syncs_private_exclusive_file(self):
        real_open=os.open
        with patch.object(monitor.os,'open',wraps=real_open)as opened, \
                patch.object(monitor.os,'fsync',wraps=os.fsync)as synced:
            result=monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(self.target.read_bytes(),self.raw)
        self.assertEqual(result,hashlib.sha256(self.raw).hexdigest())
        call=opened.call_args
        self.assertTrue(call.args[1]&os.O_EXCL);self.assertEqual(call.args[2],0o600)
        self.assertEqual(synced.call_count,1)
        if os.name=='posix':self.assertEqual(stat.S_IMODE(self.target.stat().st_mode),0o600)

    def test_identical_existing_snapshot_verifies_without_scanning_a_full_archive(self):
        self.existing();before=self.target.stat()
        with patch.object(monitor.os,'scandir',side_effect=AssertionError('Existing snapshots need no new slot')):
            result=monitor.archive_snapshot(self.snapshot,self.folder)
        after=self.target.stat()
        self.assertEqual(result,hashlib.sha256(self.raw).hexdigest())
        self.assertEqual((before.st_ino,before.st_mtime_ns),(after.st_ino,after.st_mtime_ns))

    def test_full_archive_scan_stops_at_real_cap_and_preserves_every_existing_entry(self):
        self.folder.mkdir();retained=self.folder/'retained';retained.write_bytes(b'old')
        class Entries:
            count=0
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def __iter__(self):return self
            def __next__(self):
                self.count+=1
                if self.count>10000:raise AssertionError('Directory enumeration exceeded its cap')
                return object()
        entries=Entries()
        with patch.object(monitor.os,'scandir',return_value=entries):
            with self.assertRaisesRegex(ValueError,'retention budget'):
                monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(entries.count,10000);self.assertFalse(self.target.exists())
        self.assertEqual(retained.read_bytes(),b'old')

    def test_archive_with_one_remaining_slot_accepts_exactly_one_new_file(self):
        self.folder.mkdir();retained=self.folder/'retained';retained.write_bytes(b'old')
        with patch.object(monitor,'MAX_ARCHIVE_FILES',2):
            monitor.archive_snapshot(self.snapshot,self.folder)
            other={'payload':{'state':{'chain_id':31337,'version':2}}}
            other['sha256']=monitor.digest(other['payload'])
            with self.assertRaisesRegex(ValueError,'retention budget'):
                monitor.archive_snapshot(other,self.folder)
        self.assertEqual(len(list(self.folder.iterdir())),2)
        self.assertEqual(retained.read_bytes(),b'old');self.assertEqual(self.target.read_bytes(),self.raw)

    def test_malformed_or_mismatched_digest_refuses_before_creating_any_directory(self):
        for digest in ('../escape','A'*64,'0'*64,'a'*63,'C:\\escape'):
            with self.subTest(digest=digest):
                snapshot=dict(self.snapshot,sha256=digest)
                with self.assertRaisesRegex(ValueError,'snapshot digest'):
                    monitor.archive_snapshot(snapshot,self.folder)
                self.assertFalse(self.folder.exists())

    def test_oversized_new_snapshot_refuses_before_creating_any_directory(self):
        payload={'state':{'chain_id':31337},'extra':'x'*1048576}
        snapshot={'payload':payload,'sha256':monitor.digest(payload)}
        with self.assertRaisesRegex(ValueError,'storage bound'):
            monitor.archive_snapshot(snapshot,self.folder)
        self.assertFalse(self.folder.exists())

    def test_oversized_existing_target_is_not_opened_or_modified(self):
        self.existing(b'x'*1048577)
        with patch.object(monitor.os,'open',side_effect=AssertionError('Oversized file must not be opened')):
            with self.assertRaisesRegex(ValueError,'Invalid existing'):
                monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(self.target.stat().st_size,1048577)

    def test_different_existing_bytes_are_preserved(self):
        different=self.raw[:-1]+b' ';self.existing(different)
        with self.assertRaisesRegex(ValueError,'differs or changed'):
            monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(self.target.read_bytes(),different)

    def test_existing_read_is_limited_to_expected_length_plus_one(self):
        self.existing();sizes=[];real_fdopen=os.fdopen
        class Reader:
            def __init__(self,fd,mode):self.stream=real_fdopen(fd,mode)
            def __enter__(self):return self
            def __exit__(self,*args):return self.stream.__exit__(*args)
            def fileno(self):return self.stream.fileno()
            def read(self,size):sizes.append(size);return self.stream.read(size)
        with patch.object(monitor.os,'fdopen',side_effect=Reader), \
                patch.object(Path,'read_bytes',side_effect=AssertionError('Unbounded reads are forbidden')):
            monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(sizes,[len(self.raw)+1])

    def test_hardlink_and_directory_targets_are_preserved_and_refused(self):
        self.existing();other=self.folder/'linked';os.link(self.target,other)
        with self.assertRaisesRegex(ValueError,'Invalid existing'):
            monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(other.read_bytes(),self.raw);self.assertEqual(self.target.read_bytes(),self.raw)
        other.unlink();self.target.unlink();self.target.mkdir()
        with self.assertRaisesRegex(ValueError,'Invalid existing'):
            monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertTrue(self.target.is_dir())

    def test_symlink_metadata_and_windows_archive_reparse_point_are_refused(self):
        self.existing();real_lstat=Path.lstat
        for alias in ('target_symlink','directory_reparse'):
            def metadata(path,*args,**kwargs):
                if alias=='target_symlink'and path==self.target:
                    return SimpleNamespace(st_mode=stat.S_IFLNK|0o777,st_nlink=1,st_size=len(self.raw))
                if alias=='directory_reparse'and path==self.folder:
                    return SimpleNamespace(st_mode=stat.S_IFDIR|0o700,st_file_attributes=0x400)
                return real_lstat(path,*args,**kwargs)
            with self.subTest(alias=alias),patch.object(Path,'lstat',metadata):
                with self.assertRaises(ValueError):monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(self.target.read_bytes(),self.raw)

    def test_replacement_between_metadata_and_open_is_refused_without_reading(self):
        self.existing();real_open=os.open;retained=self.folder/'original';different=self.raw[:-1]+b' '
        def replace_then_open(path,*args,**kwargs):
            if path==self.target:
                self.target.rename(retained);self.target.write_bytes(different)
            return real_open(path,*args,**kwargs)
        with patch.object(monitor.os,'open',side_effect=replace_then_open):
            with self.assertRaisesRegex(ValueError,'snapshot changed'):
                monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(retained.read_bytes(),self.raw);self.assertEqual(self.target.read_bytes(),different)

    def test_stable_different_path_and_descriptor_change_times_are_accepted(self):
        self.existing();real_fstat=os.fstat;descriptor_ctime=self.target.lstat().st_ctime_ns+100
        fields=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns')
        def descriptor(fd):
            item=real_fstat(fd);values={name:getattr(item,name)for name in fields}
            return SimpleNamespace(**values,st_ctime_ns=descriptor_ctime)
        with patch.object(monitor.os,'fstat',side_effect=descriptor):
            result=monitor.archive_snapshot(self.snapshot,self.folder)
        self.assertEqual(result,hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(self.target.read_bytes(),self.raw)

    def test_change_time_drift_from_either_api_is_refused(self):
        self.existing();real_fstat=os.fstat;real_lstat=Path.lstat
        fields=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
        for api in ('fd','path'):
            counts={'fd':0,'path':0}
            def changed(kind,item):
                counts[kind]+=1
                if kind==api and counts[kind]==2:
                    values={name:getattr(item,name)for name in fields};values['st_ctime_ns']+=1
                    return SimpleNamespace(**values)
                return item
            def descriptor(fd):return changed('fd',real_fstat(fd))
            def metadata(path,*args,**kwargs):
                item=real_lstat(path,*args,**kwargs)
                return changed('path',item)if path==self.target else item
            with self.subTest(api=api),patch.object(monitor.os,'fstat',side_effect=descriptor), \
                    patch.object(Path,'lstat',new=metadata):
                with self.assertRaisesRegex(ValueError,'differs or changed'):
                    monitor.archive_snapshot(self.snapshot,self.folder)
            self.assertEqual(self.target.read_bytes(),self.raw)


if __name__=='__main__':unittest.main()
