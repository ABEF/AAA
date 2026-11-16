"""New offline history recovery checks; no live database, provider or signing.

Real temporary SQLite/Indexer files exercise WAL snapshots and exact row
preservation. Existing history/checkpoint helpers may be reused but no historical
test method is selected. This does not qualify archive completeness or hosting.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
from types import SimpleNamespace
import unittest
from contextlib import closing
from unittest.mock import patch
from urllib.parse import urlsplit

from tests_python.test_earnings_checkpoint_lineage import EpochFixture
from zzz_ops.errors import RpcError, WorkLimit
from frontend_api.earnings_checkpoint_build import BuildBudget, publish_candidate
from frontend_api.service import Projection
from zzz_ops.work_budget import request_scope


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class HistoryRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix='popl-history-recovery-')
        self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)

    def fixture(self, count=2):
        return EpochFixture(self,count)

    def module(self):
        from frontend_api import history_recovery
        return history_recovery

    def histories(self, config):
        return [p['history'] for p in config.get('predecessors',[])]+[config['history']]

    def profile(self, directory):
        return json.loads((Path(directory)/'profile.json').read_bytes())

    def rebound(self, config, directory):
        config=copy.deepcopy(config)
        for history in self.histories(config):
            history['database']=str((Path(directory)/history['database']).resolve())
        checkpoint=config.get('earnings_history',{}).get('checkpoint')
        if checkpoint is not None:
            checkpoint['path']=str((Path(directory)/checkpoint['path']).resolve())
        return config

    def snapshot_rows(self, writer):
        return {table:writer.db.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()
                for table in ('cursors','blocks','logs')}

    def copied_rows(self, directory):
        result=[]
        for history in self.histories(self.profile(directory)):
            path=Path(directory)/history['database']
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
                result.append({table:db.execute(f'SELECT * FROM {table} ORDER BY rowid').fetchall()
                               for table in ('cursors','blocks','logs')})
        return result

    def source_bytes(self, fixture):
        return {str(p):p.read_bytes() for h in self.histories(fixture.config)
                for p in (Path(h['database']),Path(h['database']+'-wal')) if p.exists()}

    def backup(self, fixture, name='bundle', config=None, **kwargs):
        path=self.root/name
        original=copy.deepcopy(fixture.config if config is None else config)
        config=copy.deepcopy(original)
        result,pin=self.module().backup(config,path,**kwargs)
        self.assertEqual(original,config)
        self.assertEqual(pin,digest((path/'manifest.json').read_bytes()))
        self.assertEqual(result,self.module().verify(path,pin))
        return path,result,pin

    def assert_reports_equal(self, fixture, config):
        original=fixture.projection()
        recovered=fixture.projection(config)
        for identifier in (None,*map(str,fixture.ids)):
            a,b=original.earnings(identifier),recovered.earnings(identifier)
            for key in ('all_time','last_24h','window','event_count'):
                self.assertEqual(a[key],b[key],(identifier,key))
        owner=fixture.owners(len(fixture.configs)-1,fixture.safe)[fixture.ids[0]]
        a,b=original.wallet_earnings(owner,fixture.safe),recovered.wallet_earnings(owner,fixture.safe)
        for key in ('all_time','last_24h','window','event_count','token_ids'):
            self.assertEqual(a[key],b[key],key)

    def test_wal_committed_rows_full_day_and_uint256_data_are_preserved_without_source_writes(self):
        f=self.fixture(3)
        for index in f.indexes:index.db.execute('PRAGMA wal_autocheckpoint=0')
        before=self.source_bytes(f);rows=[self.snapshot_rows(i) for i in f.indexes]
        self.assertTrue(any(name.endswith('-wal') for name in before))
        path,_,_=self.backup(f)
        self.assertEqual(rows,self.copied_rows(path))
        self.assertEqual(before,self.source_bytes(f))
        for history in self.histories(self.profile(path)):
            self.assertFalse(Path(history['database']).is_absolute())
        self.assert_reports_equal(f,self.rebound(self.profile(path),path))

    def test_uncommitted_source_changes_are_not_part_of_the_recovery_snapshot(self):
        f=self.fixture();expected=[self.snapshot_rows(i) for i in f.indexes]
        db=f.indexes[-1].db
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE logs SET raw=?',('UNCOMMITTED-MUST-NOT-ESCAPE',))
        try:
            path,_,_=self.backup(f)
            self.assertEqual(expected,self.copied_rows(path))
        finally:db.rollback()

    def test_committed_writer_between_snapshot_pin_and_backup_cannot_mix_row_versions(self):
        f=self.fixture();expected=[self.snapshot_rows(i) for i in f.indexes]
        original_connect=sqlite3.connect;case=self;mutations=[]
        class ReadConnection:
            def __init__(self,connection):self.connection=connection
            def __getattr__(self,name):return getattr(self.connection,name)
            def __enter__(self):self.connection.__enter__();return self
            def __exit__(self,*args):return self.connection.__exit__(*args)
            def backup(self,target,*args,**kwargs):
                if not mutations:
                    # A real second WAL connection commits after the recovery
                    # reader's BEGIN/read pin, before SQLite starts copying.
                    writer=f.indexes[-1];number=writer.next_block;header=f.header(number)
                    with writer.db:
                        writer.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                            (31337,number,header['hash'],header['parentHash'],int(header['timestamp'],16)))
                        writer.db.execute('UPDATE cursors SET next_block=?',(number+1,))
                    mutations.append(number)
                return self.connection.backup(target,*args,**kwargs)
        def connect(path,*args,**kwargs):
            value=original_connect(path,*args,**kwargs)
            return ReadConnection(value) if str(path).startswith(Path(f.config['history']['database']).as_uri()) else value
        with patch.object(sqlite3,'connect',connect):
            path,_,_=self.backup(f)
        case.assertEqual([f.safe+1],mutations)
        case.assertEqual(expected,self.copied_rows(path))
        case.assertEqual(f.safe+2,f.indexes[-1].next_block)

    def test_restore_into_new_directory_preserves_every_row_and_exact_reporting(self):
        f=self.fixture(3);path,_,pin=self.backup(f)
        restored=self.root/'restored'
        result,receipt=self.module().restore(path,pin,restored)
        self.assertIsInstance(result,dict)
        self.assertRegex(receipt,r'^[0-9a-f]{64}$')
        self.assertEqual(self.copied_rows(path),self.copied_rows(restored))
        self.assertEqual((path/'profile.json').read_bytes(),(restored/'profile.json').read_bytes())
        self.assert_reports_equal(f,self.rebound(self.profile(restored),restored))

    def test_checkpoint_three_raw_phase_and_reviewed_bytes_survive_backup_and_restore(self):
        f=self.fixture(3)
        raw=f.candidate(161)
        checkpoint=f.root/'reviewed-checkpoint.json'
        pin=publish_candidate(checkpoint,raw)
        f.config['earnings_history']['checkpoint']=dict(path=str(checkpoint),sha256=pin)
        before=checkpoint.read_bytes()
        path,_,bundle_pin=self.backup(f)
        cp=self.profile(path)['earnings_history']['checkpoint']
        self.assertFalse(Path(cp['path']).is_absolute())
        self.assertEqual(raw,(path/cp['path']).read_bytes())
        restored=self.root/'restored-checkpoint'
        self.module().restore(path,bundle_pin,restored)
        self.assertEqual(raw,(restored/cp['path']).read_bytes())
        self.assertEqual(before,checkpoint.read_bytes())
        self.assert_reports_equal(f,self.rebound(self.profile(restored),restored))

    def test_original_checkpoint_two_and_initialized_empty_original_history_recover_explicitly(self):
        from tests_python import test_earnings_checkpoint_prefix_import as helper
        from indexer.monitor import Indexer
        f=self.fixture()
        # EpochFixture(count=1) is not supported. Select its actual original
        # deployment configuration and prehandoff records; no lineage is faked.
        original=helper.prefix_configuration(f,0)
        safe=f.edges[0]-20
        with f.indexes[0].db:
            f.indexes[0].db.execute('DELETE FROM blocks WHERE number>?',(safe,))
            f.indexes[0].db.execute('UPDATE cursors SET next_block=?',(safe+1,))
        prefix,raw=helper.approved_prefix(f,0,46)
        self.assertEqual(2,json.loads(raw)['schema'])
        original['earnings_history']['checkpoint']=prefix
        before=self.source_bytes(f)
        with patch.object(f,'safe',safe),patch.object(f,'head',safe+11):
            path,manifest,pin=self.backup(f,config=original,name='original2-bundle')
            self.assertEqual(1,len(manifest['databases']))
            self.assertEqual(2,manifest['checkpoint']['schema'])
            restored=self.root/'original2-restored'
            self.module().restore(path,pin,restored)
            self.assertEqual(raw,(restored/'checkpoint.json').read_bytes())
            recovered=self.rebound(self.profile(restored),restored)
            left,right=f.projection(original),f.projection(recovered)
            self.assertIsNone(left.lineage);self.assertIsNone(right.lineage)
            for identifier in (None,*map(str,f.ids)):
                a,b=left.earnings(identifier),right.earnings(identifier)
                for key in ('all_time','last_24h','window','event_count'):
                    self.assertEqual(a[key],b[key],(identifier,key))
            owner=f.owners(0,safe)[f.ids[0]]
            a,b=left.wallet_earnings(owner,safe),right.wallet_earnings(owner,safe)
            for key in ('all_time','last_24h','window','event_count','token_ids'):
                self.assertEqual(a[key],b[key],key)
            empty=copy.deepcopy(original);empty['earnings_history'].pop('checkpoint')
            history=empty['history'];history['database']=str(f.root/'initialized-empty-original.sqlite')
            writer=Indexer(dict(database=history['database'],chain_id=empty['chain_id'],
                start_block=history['start_block'],start_parent_hash=history['start_parent_hash'],
                contracts=history['contracts'],rpc_urls=['https://offline.invalid']),self.module().NoNetwork())
            self.addCleanup(writer.close)
            empty_bundle,empty_manifest,empty_pin=self.backup(f,config=empty,name='empty-original-bundle')
            snapshot=empty_manifest['databases'][0]['snapshot']
            self.assertEqual((0,0,None,None),tuple(snapshot[k] for k in ('block_count','log_count','first','tip')))
            self.assertEqual('unverified',empty_manifest['raw_retention']['serving_eligibility'])
            empty_restored=self.root/'empty-original-restored'
            self.module().restore(empty_bundle,empty_pin,empty_restored)
            self.assertEqual(self.copied_rows(empty_bundle),self.copied_rows(empty_restored))
            with self.assertRaises(RpcError):
                f.projection(self.rebound(self.profile(empty_restored),empty_restored)).earnings()
        self.assertEqual(before,self.source_bytes(f))

    def test_backup_copies_all_raw_rows_without_raising_or_using_the_api_event_cap(self):
        f=self.fixture();config=copy.deepcopy(f.config)
        for history in self.histories(config):history['max_events']=1
        expected=[self.snapshot_rows(i) for i in f.indexes]
        self.assertTrue(any(len(r['logs'])>1 for r in expected))
        path,_,_=self.backup(f,config=config)
        self.assertEqual(expected,self.copied_rows(path))
        self.assertEqual([1,1],[h['max_events'] for h in self.histories(self.profile(path))])

    def test_portable_profile_and_public_manifest_do_not_include_rpc_credentials(self):
        f=self.fixture();config=copy.deepcopy(f.config)
        marker='FAKE_TEST_CREDENTIAL_NEVER_A_REAL_KEY'
        config['rpc_urls']=['https://example.invalid/'+marker]
        path,_,_=self.backup(f,config=config)
        for name in ('profile.json','manifest.json'):
            self.assertNotIn(marker,(path/name).read_text())
        self.assertEqual(['offline.invalid'],[urlsplit(url).hostname for url in self.profile(path)['rpc_urls']])

    def test_existing_backup_or_restore_directory_is_not_overwritten_even_if_empty(self):
        f=self.fixture();path=self.root/'already-present';path.mkdir()
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(f.config,path)
        self.assertEqual([],list(path.iterdir()))
        bundle,_,pin=self.backup(f)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().restore(bundle,pin,path)
        self.assertEqual([],list(path.iterdir()))

    def test_source_roots_and_database_paths_cannot_be_used_as_restore_outputs(self):
        f=self.fixture();bundle,_,pin=self.backup(f)
        before=self.source_bytes(f)
        for path in (f.root,Path(f.config['history']['database']),bundle):
            with self.subTest(path=path),self.assertRaises((OSError,ValueError,RpcError)):
                self.module().restore(bundle,pin,path)
        self.assertEqual(before,self.source_bytes(f))

    def test_missing_input_database_is_not_created_and_never_produces_a_complete_manifest(self):
        f=self.fixture();config=copy.deepcopy(f.config)
        missing=f.root/'absent.sqlite'
        config['history']['database']=str(missing)
        out=self.root/'failed-missing'
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(config,out)
        self.assertFalse(missing.exists())
        self.assertFalse((out/'manifest.json').exists())

    def test_empty_database_schema_is_rejected_without_initialization(self):
        f=self.fixture();config=copy.deepcopy(f.config)
        empty=f.root/'empty.sqlite';empty.write_bytes(b'')
        config['history']['database']=str(empty)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(config,self.root/'failed-empty')
        self.assertEqual(b'',empty.read_bytes())

    def test_foreign_chain_or_inconsistent_tip_cursor_rejects(self):
        for mutation in ('foreign-chain','tip'):
            with self.subTest(mutation=mutation):
                f=self.fixture()
                db=f.indexes[-1].db
                with db:
                    if mutation=='foreign-chain':db.execute('UPDATE cursors SET chain=1')
                    else:db.execute('UPDATE cursors SET next_block=next_block-1')
                before=self.source_bytes(f)
                with self.assertRaises((OSError,ValueError,RpcError)):
                    self.module().backup(f.config,self.root/f'failed-{mutation}')
                self.assertEqual(before,self.source_bytes(f))

    def test_different_forks_in_overlapping_lineage_database_snapshots_are_rejected(self):
        from tests_python.test_earnings_checkpoint_lineage import digest as chain_hash
        f=self.fixture();db=f.indexes[-1].db
        first=f.starts[-1]+1;last=f.edges[-1]-1
        replacement={number:chain_hash(900000+number) for number in range(first,last+1)}
        with db:
            for number,new_hash in replacement.items():
                db.execute('UPDATE blocks SET hash=? WHERE chain=? AND number=?',(new_hash,31337,number))
                db.execute('UPDATE blocks SET parent=? WHERE chain=? AND number=?',(new_hash,31337,number+1))
                rows=db.execute('SELECT transaction_hash,log_index,raw FROM logs WHERE block_number=?',(number,)).fetchall()
                for transaction,index,raw in rows:
                    event=json.loads(raw);event['blockHash']=new_hash
                    db.execute('UPDATE logs SET block_hash=?,raw=? WHERE transaction_hash=? AND log_index=?',
                        (new_hash,json.dumps(event),transaction,index))
        # Each local chain retains its creation anchor, contiguous parent links,
        # tip/cursor and matching raw logs, but peers disagree in shared blocks.
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(f.config,self.root/'incoherent-lineage')

    def test_extra_table_or_trigger_is_not_silently_adopted_as_indexer_schema(self):
        for kind in ('table','trigger'):
            with self.subTest(kind=kind):
                f=self.fixture()
                with f.indexes[-1].db:
                    f.indexes[-1].db.execute('CREATE TABLE extra(secret TEXT)' if kind=='table' else
                        'CREATE TRIGGER extra AFTER UPDATE ON cursors BEGIN SELECT 1; END')
                with self.assertRaises((OSError,ValueError,RpcError)):
                    self.module().backup(f.config,self.root/f'failed-schema-{kind}')

    def test_missing_manifest_wrong_pin_or_tampered_manifest_fails_closed(self):
        f=self.fixture();path,_,pin=self.backup(f)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,'0'*64)
        original=(path/'manifest.json').read_bytes()
        (path/'manifest.json').write_bytes(original+b' ')
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,pin)
        (path/'manifest.json').unlink()
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,pin)

    def test_corrupt_or_missing_database_in_bundle_is_not_restored(self):
        f=self.fixture();path,_,pin=self.backup(f)
        database=path/self.profile(path)['history']['database']
        raw=database.read_bytes();database.write_bytes(b'corrupt!'+raw[8:])
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().restore(path,pin,self.root/'rejected-corrupt')
        database.unlink()
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,pin)

    def test_corrupt_portable_profile_does_not_fall_back_to_source_configuration(self):
        f=self.fixture();path,_,pin=self.backup(f)
        (path/'profile.json').write_bytes(b'{"chain_id":1,"chain_id":31337}\n')
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,pin)

    def test_repinned_database_with_bad_cursor_fails_structural_checks_beyond_digest(self):
        f=self.fixture();path,manifest,_=self.backup(f)
        relative=self.profile(path)['history']['database'];database=path/relative
        with closing(sqlite3.connect(database)) as db:
            with db:db.execute('UPDATE cursors SET next_block=next_block-1')
        raw=database.read_bytes()
        for item in manifest['files']:
            if item['path']==relative:item.update(bytes=len(raw),sha256=digest(raw))
        changed=(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode()
        (path/'manifest.json').write_bytes(changed)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,digest(changed))

    def test_unknown_files_and_manifest_path_traversal_are_rejected(self):
        f=self.fixture();path,manifest,pin=self.backup(f)
        extra=path/'not-in-inventory.txt';extra.write_bytes(b'not reviewed')
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,pin)
        extra.unlink()
        outside=self.root/'outside.sqlite';outside.write_bytes(b'external untouched')
        manifest['files'][0]['path']='../outside.sqlite'
        changed=(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode()
        (path/'manifest.json').write_bytes(changed)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().verify(path,digest(changed))
        self.assertEqual(b'external untouched',outside.read_bytes())

    def test_manifest_scope_remains_unapproved_full_retention_and_not_atomic_graph(self):
        f=self.fixture();path,manifest,pin=self.backup(f)
        for flag in ('approved','production_approved','installed','ready_for_submission'):
            self.assertIs(manifest[flag],False)
        self.assertEqual('individual_sqlite_snapshots_not_atomic_graph',manifest['snapshot_consistency'])
        self.assertEqual(dict(mode='all_retained_rows',window_seconds=86400,pruned=False,
                              serving_eligibility='unverified'),manifest['raw_retention'])
        for field,value in (('approved',True),('schema',True),('max_bytes',True)):
            changed=copy.deepcopy(manifest);changed[field]=value
            raw=(json.dumps(changed,sort_keys=True,separators=(',',':'))+'\n').encode()
            (path/'manifest.json').write_bytes(raw)
            with self.subTest(field=field),self.assertRaises((OSError,ValueError,RpcError)):
                self.module().verify(path,digest(raw))
        # Explicit caller pin to original bytes still cannot bless edited state.
        with self.assertRaises((OSError,ValueError,RpcError)):self.module().verify(path,pin)

    def test_late_backup_failure_retains_partial_outputs_and_requires_a_new_directory(self):
        f=self.fixture();module=self.module();original=module._write
        path=self.root/'interrupted-backup';before=self.source_bytes(f)
        def interrupt(target,raw):
            if target.name=='manifest.json':
                original(target,b'{"incomplete":')
                raise OSError('injected publication interruption')
            return original(target,raw)
        with patch.object(module,'_write',interrupt),self.assertRaises(OSError):
            module.backup(f.config,path)
        retained={str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}
        self.assertIn('manifest.json',retained)
        with self.assertRaises((OSError,ValueError,RpcError)):module.verify(path,'0'*64)
        with self.assertRaises((OSError,ValueError,RpcError)):module.backup(f.config,path)
        self.assertEqual(retained,{str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()})
        self.assertEqual(before,self.source_bytes(f))
        self.backup(f,name='fresh-after-interruption')

    def test_interrupted_restore_keeps_previous_bundle_and_unapproved_partial_copy(self):
        f=self.fixture();bundle,_,pin=self.backup(f)
        original={str(p.relative_to(bundle)):p.read_bytes() for p in bundle.rglob('*') if p.is_file()}
        module=self.module();copy_file=module._copy;path=self.root/'interrupted-restore'
        def interrupt(source,target,expected):
            copy_file(source,target,expected)
            if target.name=='001.sqlite':raise OSError('injected copy interruption')
        with patch.object(module,'_copy',interrupt),self.assertRaises(OSError):
            module.restore(bundle,pin,path)
        self.assertFalse((path/'restore.json').exists())
        with self.assertRaises((OSError,ValueError,RpcError)):module.verify(path,pin)
        with self.assertRaises((OSError,ValueError,RpcError)):module.restore(bundle,pin,path)
        self.assertEqual(original,{str(p.relative_to(bundle)):p.read_bytes() for p in bundle.rglob('*') if p.is_file()})
        module.restore(bundle,pin,self.root/'fresh-restore')

    def test_source_symlink_reparse_and_hardlink_aliases_are_not_adopted(self):
        f=self.fixture();source=Path(f.config['history']['database']);original_lstat=Path.lstat
        for kind in ('symlink','reparse'):
            def fake_lstat(path,*args,**kwargs):
                if path==source:
                    return SimpleNamespace(st_mode=stat.S_IFLNK if kind=='symlink' else stat.S_IFREG,
                        st_file_attributes=0 if kind=='symlink' else 0x400)
                return original_lstat(path,*args,**kwargs)
            with self.subTest(kind=kind),patch.object(Path,'lstat',fake_lstat), \
                    self.assertRaises((OSError,ValueError,RpcError)):
                self.module().backup(f.config,self.root/f'rejected-{kind}')
        alias=f.root/'hardlinked-history.sqlite'
        os.link(f.config['predecessors'][0]['history']['database'],alias)
        config=copy.deepcopy(f.config);config['history']['database']=str(alias)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(config,self.root/'rejected-hardlink')

    def test_restore_receipt_cannot_claim_approval_or_a_different_manifest_inventory(self):
        f=self.fixture();bundle,_,pin=self.backup(f);restored=self.root/'receipt-restored'
        _,receipt_pin=self.module().restore(bundle,pin,restored)
        path=restored/'restore.json';original=path.read_bytes()
        self.assertEqual(receipt_pin,digest(original))
        value=json.loads(original)
        for field,replacement in (('approved',True),('manifest_sha256','0'*64),('schema',True),('files',[])):
            changed=copy.deepcopy(value);changed[field]=replacement
            path.write_bytes((json.dumps(changed,sort_keys=True,separators=(',',':'))+'\n').encode())
            with self.subTest(field=field),self.assertRaises((OSError,ValueError,RpcError)):
                self.module().verify(restored,pin)

    def test_actual_import_review_and_checkpoint_are_preserved_as_exact_bound_files(self):
        from tests_python import test_earnings_checkpoint_prefix_import as helper
        from frontend_api.earnings_checkpoint_import import prepare
        f=helper.EarningsCheckpointPrefixImportTests.fixture(self,3)
        prefix,_=helper.approved_prefix(f)
        raw,review=prepare(f.projection().earnings_history,161,prefix)
        cp=f.root/'imported-checkpoint.json';cp.write_bytes(raw)
        sidecar=f.root/'import-review.json';sidecar.write_bytes(review)
        f.config['earnings_history']['checkpoint']=dict(path=str(cp),sha256=digest(raw))
        path,_,pin=self.backup(f,review=dict(path=str(sidecar),sha256=digest(review)))
        self.assertEqual(review,(path/'import-review.json').read_bytes())
        self.assertEqual(raw,(path/'checkpoint.json').read_bytes())
        restored=self.root/'import-review-restored'
        self.module().restore(path,pin,restored)
        self.assertEqual(review,(restored/'import-review.json').read_bytes())
        self.assertEqual(raw,(restored/'checkpoint.json').read_bytes())
        self.assert_reports_equal(f,self.rebound(self.profile(restored),restored))

    def test_repinned_import_review_cannot_detach_the_full_day_graph_or_producer_shape(self):
        from tests_python import test_earnings_checkpoint_prefix_import as helper
        from frontend_api.earnings_checkpoint_import import prepare
        f=helper.EarningsCheckpointPrefixImportTests.fixture(self,3)
        prefix,_=helper.approved_prefix(f)
        raw,review=prepare(f.projection().earnings_history,161,prefix)
        cp=f.root/'review-bound-checkpoint.json';cp.write_bytes(raw)
        f.config['earnings_history']['checkpoint']=dict(path=str(cp),sha256=digest(raw))
        original=json.loads(review)
        for number,field in enumerate(('earliest_served_timestamp','target_graph_length','producer_sources')):
            changed=copy.deepcopy(original)
            if field=='earliest_served_timestamp':changed[field]-=86400
            elif field=='target_graph_length':changed[field]-=1
            else:changed[field][next(iter(changed[field]))]='not-a-source-hash'
            data=(json.dumps(changed,sort_keys=True,separators=(',',':'))+'\n').encode()
            sidecar=f.root/f'detached-import-review-{number}.json';sidecar.write_bytes(data)
            with self.subTest(field=field),self.assertRaises((OSError,ValueError,RpcError)):
                self.module().backup(f.config,self.root/f'rejected-review-{number}',
                                      review=dict(path=str(sidecar),sha256=digest(data)))

    def test_exhausted_outer_deadline_cannot_be_refilled_by_backup_verify_or_restore(self):
        f=self.fixture();path,_,pin=self.backup(f)
        actions=(lambda:self.module().backup(f.config,self.root/'expired-backup'),
                 lambda:self.module().verify(path,pin),
                 lambda:self.module().restore(path,pin,self.root/'expired-restore'))
        for action in actions:
            budget=BuildBudget();budget.deadline=0
            with self.assertRaises(WorkLimit):
                with request_scope(budget):action()

    def test_explicit_small_byte_ceiling_rejects_instead_of_truncating_history(self):
        f=self.fixture();before=self.source_bytes(f)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(f.config,self.root/'byte-bound',max_bytes=4096)
        self.assertEqual(before,self.source_bytes(f))

    def test_checkpoint_and_profile_bytes_cannot_be_written_beyond_the_package_ceiling(self):
        f=self.fixture(3)
        raw=f.candidate(161);cp=f.root/'byte-bound-checkpoint.json';cp.write_bytes(raw)
        f.config['earnings_history']['checkpoint']=dict(path=str(cp),sha256=digest(raw))
        database_bytes=sum(index.db.execute('PRAGMA page_count').fetchone()[0]*
                           index.db.execute('PRAGMA page_size').fetchone()[0] for index in f.indexes)
        # All database copies fit, so this exposes late ancillary-payload writes
        # rather than merely exercising the already present DB preflight guard.
        limit=database_bytes+len(raw)-1;out=self.root/'bounded-complete-payload'
        self.assertGreater(limit,database_bytes)
        with self.assertRaises((OSError,ValueError,RpcError)):
            self.module().backup(f.config,out,max_bytes=limit)
        written=sum(path.stat().st_size for path in out.rglob('*') if path.is_file()) if out.exists() else 0
        self.assertLessEqual(written,limit,'Rejected backup exceeded its byte limit before reporting failure')
        self.assertEqual(raw,cp.read_bytes())

    def test_backup_verify_restore_never_call_rpc_or_live_contract_readers(self):
        f=self.fixture()
        with patch.object(Projection,'_header',side_effect=AssertionError('Network header read')), \
             patch.object(Projection,'_call',side_effect=AssertionError('Live contract read')), \
             patch.object(Projection,'_verify_deployment',side_effect=AssertionError('Live binding read')):
            path,_,pin=self.backup(f)
            self.module().verify(path,pin)
            self.module().restore(path,pin,self.root/'no-rpc-restore')


if __name__=='__main__':
    unittest.main()
