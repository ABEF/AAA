"""NEW unsigned keeper recovery tests; prepared for review before selection.

These use only new temporary files and published c811 vectors as static data.
They do not construct Keeper, reuse an old test body, touch an operating journal,
contact a provider or launch Cast. Whole-byte equality is the primary oracle.
"""
import copy
import builtins
from contextlib import redirect_stderr, redirect_stdout
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import socket
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

from keeper import recovery_bundle as subject


ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'reports/ubuntu-daemon-storage-20261126/evidence/fetched'
NOW=1795700000
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
CANONICAL=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


class KeeperRecoveryBundleTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='popl-new-keeper-recovery-')
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.work=self.root/'working';self.work.mkdir(mode=0o700)
        (self.work/'runtime').mkdir(mode=0o700)
        self.key=self.work/'keystore.secret';self.password=self.work/'password.secret'
        self.key_marker='DISPOSABLE-KEY-SENTINEL-NOT-A-KEY'
        self.password_marker='DISPOSABLE-PASSWORD-SENTINEL'
        self.key.write_text(self.key_marker);self.password.write_text(self.password_marker)
        self.key.chmod(0o600);self.password.chmod(0o600)
        self.accepted=json.loads((STATIC/'case-HASH_SAVE_FAULT_ARMED.json').read_bytes())
        self.raw=self.accepted['journal_raw_utf8'].encode()
        self.state=json.loads(self.raw)
        self.journal=self.work/'runtime'/'journal.json'
        self.journal.write_bytes(self.raw)
        self.journal.chmod(0o600)
        # Synthetic secret-bearing configuration: no genuine endpoint or key.
        self.credential='synthetic-user'+':'+'DO-NOT-EXPOSE'
        self.config={
            'chain_id':4663,'accounting_model':'shared-pools-v2','sender':self.state['sender'],
            'contracts':copy.deepcopy(self.state['contracts']),
            'accounting_version':7,'custody_version':5,'fee_intake_version':1,
            'royalty_settlement_version':4,'portfolio_version':2,'maintenance_policy_version':3,
            'rebalance_confirmation_version':3,'execution_quality_version':1,
            'protocol_policy_version':1,'lp_routing_version':3,'execution_price_version':1,
            'rpc_urls':['https://'+self.credential+'@offline.invalid/path'],
            'state_path':'runtime/journal.json','health_path':'runtime/health.json',
            'lock_path':'runtime/keeper.lock','keystore':'keystore.secret','password_file':'password.secret',
            'reviewed_for_live_use':False,'interval_seconds':240,'confirmations':12,
            'max_gas_limit':24000000,'max_gas_price_wei':'5000000000',
            'max_transaction_cost_wei':'10000000000000000','max_daily_cost_wei':'50000000000000000',
            'l1_fee_allowance_wei':'0','receipt_fee_policy':'included',
            'code_hashes':{name:'0x'+'11'*32 for name in self.state['contracts']},
            'idle_compounding_budget':'0x'+'ab'*20,
            'maintenance':{'compound':False,'compound_idle':False,'harvest':True,
                           'minimum_liquidity':1,'harvest_interval_seconds':3600},
            'metadata_refresh':{'enabled':False},'royalty_conversion':{'enabled':False},
            'lp_conversion':{'enabled':False},'principal_distribution':{'enabled':False},
            'adaptive_range':{'enabled':False},'bucket_overrides':{},'buybacks':[],
        }
        self.config['code_hashes']['idle_compounding_budget']='0x'+'11'*32
        self.config_path=self.root/'private-config.json'
        self.write_config()
        for target in ('socket.create_connection','socket.socket.connect','subprocess.Popen'):
            guard=patch(target,side_effect=AssertionError('Forbidden unsigned recovery side effect'))
            guard.start();self.addCleanup(guard.stop)

    def write_config(self):
        # Deliberately differs from canonical digest spelling.
        self.config_path.write_bytes((json.dumps(self.config,indent=3,ensure_ascii=False)+'\n').encode())
        self.config_path.chmod(0o600)

    def write_state(self,value):
        self.state=copy.deepcopy(value)
        self.raw=(json.dumps(value,indent=1,ensure_ascii=False)+'\n').encode()
        self.journal.write_bytes(self.raw)

    def backup(self,name='bundle',**kwargs):
        output=self.root/name
        before=(self.journal.read_bytes(),self.config_path.read_bytes())
        manifest,pin=subject.backup(self.config_path,output,working_directory=self.work,now=NOW,**kwargs)
        self.assertEqual(before,(self.journal.read_bytes(),self.config_path.read_bytes()))
        self.assertEqual(pin,SHA((output/'manifest.json').read_bytes()))
        self.assertEqual(manifest,json.loads((output/'manifest.json').read_bytes()))
        self.assertEqual(self.raw,(output/'journal.json').read_bytes())
        self.assertEqual({'journal.json','manifest.json'},{p.name for p in output.iterdir()})
        return output,manifest,pin

    def verify(self,bundle,pin,**kwargs):
        return subject.verify(bundle,pin,self.config_path,max_age_seconds=60,now=NOW+30,**kwargs)

    def restore(self,bundle,pin,name='restored',**kwargs):
        output=self.root/name
        plan,digest=subject.restore(bundle,pin,self.config_path,output,max_age_seconds=60,now=NOW+30,**kwargs)
        self.assertEqual(self.raw,(output/'keeper-state.json').read_bytes())
        self.assertEqual({'keeper-state.json','RESTORE_PLAN.json'},{p.name for p in output.iterdir()})
        self.assertEqual(plan,json.loads((output/'RESTORE_PLAN.json').read_bytes()))
        self.assertEqual(digest,SHA((output/'RESTORE_PLAN.json').read_bytes()))
        return output,plan,digest

    def copy_bundle(self,source,name):
        result=self.root/name;result.mkdir(mode=0o700)
        for path in source.iterdir():
            (result/path.name).write_bytes(path.read_bytes())
            (result/path.name).chmod(0o600)
        return result

    def assert_source_preserved(self,before):
        self.assertEqual(before,(self.journal.read_bytes(),self.config_path.read_bytes()))

    def test_captured_hashless_pending_round_trip_is_exact_bytes(self):
        before=(self.journal.read_bytes(),self.config_path.read_bytes())
        bundle,manifest,pin=self.backup()
        self.assertEqual(manifest,self.verify(bundle,pin))
        restored,_,_=self.restore(bundle,pin)
        after=json.loads((restored/'keeper-state.json').read_bytes())
        self.assertEqual(self.state,after)
        self.assertIsNone(after['pending']['hash'])
        self.assertEqual(0,after['next_nonce'])
        self.assertEqual(self.state['observed_adjustment_v3'],after['observed_adjustment_v3'])
        self.assert_source_preserved(before)

    def test_known_hash_and_zero_tip_fee_review_survive_without_repricing(self):
        state=copy.deepcopy(self.state)
        state['pending']['hash']='0x'+'23'*32
        fee=state['pending']['fee_review']
        fee.update(schema=2,execution_fee_model='eip1559_zero_tip',l1_fee_allowance_wei=0,
                   receipt_fee_policy='included')
        self.write_state(state)
        self.config['submission_fee_profile']=2;self.write_config()
        bundle,_,pin=self.backup();restored,_,_=self.restore(bundle,pin)
        result=json.loads((restored/'keeper-state.json').read_bytes())
        self.assertEqual(state['pending'],result['pending'])
        self.assertEqual(self.raw,(bundle/'journal.json').read_bytes())

    def test_settled_anchor_and_large_historical_spend_preserve_exact_values(self):
        record=json.loads((STATIC/'case-FINAL_JOURNAL.json').read_bytes())
        state=copy.deepcopy(record['state'])
        state['spent']['2026-11-25']=2**255-1
        self.write_state(state)
        bundle,_,pin=self.backup();restored,_,_=self.restore(bundle,pin)
        result=json.loads((restored/'keeper-state.json').read_bytes())
        self.assertEqual(state['receipt_anchor'],result['receipt_anchor'])
        self.assertEqual(state['last_fee_observation'],result['last_fee_observation'])
        self.assertEqual(2**255-1,result['spent']['2026-11-25'])
        self.assertEqual(state['next_nonce'],result['next_nonce'])

    def test_legacy_missing_fee_review_is_preserved_for_manual_reconciliation(self):
        state=copy.deepcopy(self.state);del state['pending']['fee_review'];self.write_state(state)
        bundle,manifest,pin=self.backup();restored,plan,_=self.restore(bundle,pin)
        self.assertNotIn('fee_review',json.loads((restored/'keeper-state.json').read_bytes())['pending'])
        summary=json.dumps([manifest,plan]).lower()
        self.assertIn('manual',summary)
        self.assertIn('fee',summary)
        state['pending']['fee_review']=None;self.write_state(state)
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.root/'explicit-null-fees',working_directory=self.work,now=NOW)

    def test_backup_and_restore_flags_never_approve_signing_fencing_or_installation(self):
        bundle,manifest,pin=self.backup();_,plan,_=self.restore(bundle,pin)
        expected={'unsigned':True,'live_ready':False,'canonical_state_verified':False,
                  'old_keeper_fenced':False,'signer_material_included':False,
                  'configuration_installed':False,'service_restarted':False}
        for value in (manifest,plan):
            for key,expected_value in expected.items():
                self.assertIs(value[key],expected_value,(key,value[key]))

    def test_supported_worker_and_schedule_inventory_round_trips_without_timer_reset(self):
        # Independently written current/historical shapes from the daemon's
        # validators; preserving dormant worker cursors does not enable them.
        state=copy.deepcopy(self.state);h='0x'+'67'*32;controller=state['contracts']['access']
        nft=state['contracts']['nft'];asset='0x'+'cd'*20
        state.update({
            'retry_after':{'harvest:7':1795697800},'buyback_priority':True,'buyback_cursor':3,
            'principal_distribution_first':False,'principal_distribution_cursor':1000,
            'outside_rebalance_v2':{'7':{'identity':h,'observed_at':1000,'next_check_at':4600,'execute_after':0}},
            'observed_rebalance_v1':{'7':{'identity':h,'observed_at':1000,'last_checked_at':1300,
                                        'next_check_at':1600,'execute_after':0}},
            'confirmation_reset_v1':{'7':True},
            'confirmation_clear_v1':{'7':{'number':99,'hash':h,'timestamp':1000,'nonce':0,
                                         'awaiting_healthy_read':True}},
            'adjustment_jitter_last_v3':{'7':61},
            'metadata_refresh':{'identity':{'chain_id':4663,'controller':controller,'nft':nft},
                'cursor':2,'next_first':False,'notified':{'1':{'ordinal':1,'token_id':'1',
                    'available':True,'traits_ready':True,'stage':2,'observed_number':10,
                    'observed_hash':h,'notification_number':11,'notification_hash':'0x'+'78'*32}}},
            'lp_conversion':{'identity':{'ledger':state['contracts']['rewards'],'nft':nft,
                                        'assets':[asset],'profile':'v4_native',
                                        'executor':state['contracts']['lp_position_executor']},
                             'asset':0,'ordinal':1000,'next_first':False},
            'royalty_conversion':{'identity':{'ledger':state['contracts']['fees'],'nft':nft,'assets':[asset]},
                                  'asset':0,'ordinal':999,'next_first':True},
        })
        self.write_state(state)
        bundle,_,pin=self.backup();restored,_,_=self.restore(bundle,pin)
        self.assertEqual(self.raw,(restored/'keeper-state.json').read_bytes())
        self.assertEqual(state,json.loads((restored/'keeper-state.json').read_bytes()))

    def test_secret_named_fields_nested_in_known_state_are_refused_without_disclosure(self):
        baseline=copy.deepcopy(self.state);sentinel='SYNTHETIC-NESTED-SECRET'
        for index,field in enumerate(('metadata_refresh','lp_conversion','royalty_conversion','pending')):
            state=copy.deepcopy(baseline)
            state[field]={**(state[field]if isinstance(state.get(field),dict)else{}),
                          'identity':{'password':sentinel}}
            self.write_state(state);output=self.root/('nested-secret-'+str(index))
            with self.subTest(field=field),self.assertRaises(ValueError)as caught:
                subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
            self.assertNotIn(sentinel,str(caught.exception))
            self.assertFalse(output.exists());self.assertEqual(self.raw,self.journal.read_bytes())

    def test_signer_files_and_credentialed_config_are_not_opened_or_exported(self):
        original_open=Path.open;original_os_open=os.open
        original_builtin_open=builtins.open;original_io_open=io.open
        def secret_path(path):
            return isinstance(path,(str,bytes,os.PathLike)) and os.fsdecode(os.fspath(path)).replace('\\','/').split('/')[-1]in ('keystore.secret','password.secret')
        def guarded(path,*args,**kwargs):
            if path.absolute()in (self.key.absolute(),self.password.absolute()):
                raise AssertionError('Recovery attempted to read a signer secret')
            return original_open(path,*args,**kwargs)
        def guarded_os(path,*args,**kwargs):
            if secret_path(path):
                raise AssertionError('Recovery attempted to open a signer secret')
            return original_os_open(path,*args,**kwargs)
        def guarded_builtin(path,*args,**kwargs):
            if secret_path(path):raise AssertionError('Recovery attempted to read a signer secret')
            return original_builtin_open(path,*args,**kwargs)
        def guarded_io(path,*args,**kwargs):
            if secret_path(path):raise AssertionError('Recovery attempted to read a signer secret')
            return original_io_open(path,*args,**kwargs)
        before=(self.journal.read_bytes(),self.config_path.read_bytes())
        with patch.object(Path,'open',guarded),patch.object(os,'open',guarded_os), \
                patch.object(builtins,'open',guarded_builtin),patch.object(io,'open',guarded_io):
            bundle,_,pin=self.backup()
            restored,_,_=self.restore(bundle,pin)
        public=b''.join(path.read_bytes()for folder in (bundle,restored)for path in folder.iterdir())
        for marker in (self.key_marker,self.password_marker,self.credential,'offline.invalid/path'):
            self.assertNotIn(marker.encode(),public)
        self.assert_source_preserved(before)

    def test_configuration_file_and_semantic_identities_cannot_be_substituted(self):
        bundle,_,pin=self.backup()
        original=self.config_path.read_bytes()
        variants=[{**self.config,'chain_id':4664},{**self.config,'sender':'0x'+'34'*20},
                  {**self.config,'contracts':{**self.config['contracts'],'vault':'0x'+'45'*20}}]
        for index,config in enumerate(variants):
            self.config_path.write_bytes((json.dumps(config,sort_keys=True)+'\n').encode())
            with self.subTest(index=index),self.assertRaises(ValueError):self.verify(bundle,pin)
        # Equal decoded configuration with different raw bytes still differs.
        self.config_path.write_bytes(CANONICAL(self.config)+b'\n')
        with self.assertRaises(ValueError):self.verify(bundle,pin)
        self.config_path.write_bytes(original)
        self.assertIsInstance(self.verify(bundle,pin),dict)

    def test_trusted_manifest_pin_rejects_changed_manifest_and_journal(self):
        bundle,_,pin=self.backup()
        variants=(('manifest.json',b' '),('journal.json',b' '))
        for index,(name,suffix)in enumerate(variants):
            changed=self.copy_bundle(bundle,'changed-'+str(index))
            (changed/name).write_bytes((changed/name).read_bytes()+suffix)
            with self.subTest(name=name),self.assertRaises(ValueError):self.verify(changed,pin)
        for wrong in ('0'*64,pin.upper(),'0x'+pin,pin[:-1],pin+'\n'):
            with self.subTest(pin=wrong),self.assertRaises(ValueError):self.verify(bundle,wrong)

    def test_recomputed_manifest_pin_does_not_authorize_boolean_integer_substitutions(self):
        bundle,manifest,_=self.backup()
        for index,mutation in enumerate(('identity','pending-nonce','pending-present','schema','payload-path')):
            changed=self.copy_bundle(bundle,'typed-'+str(index));value=copy.deepcopy(manifest)
            if mutation=='identity':value['identity']['execution_price_version']=True
            elif mutation=='pending-nonce':value['pending_summary']['next_nonce']=False
            elif mutation=='pending-present':value['pending_summary']['present']=1
            elif mutation=='schema':value['schema']=True
            else:value['files'][0]['path']='../journal.json'
            raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
            (changed/'manifest.json').write_bytes(raw)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.verify(changed,SHA(raw))

    def test_missing_extra_and_nonfile_package_entries_are_refused(self):
        bundle,_,pin=self.backup()
        for index,change in enumerate(('missing','extra','directory')):
            changed=self.copy_bundle(bundle,'inventory-'+str(index))
            if change=='missing':(changed/'journal.json').unlink()
            elif change=='extra':(changed/'unreviewed.json').write_bytes(b'{}')
            else:(changed/'journal.json').unlink();(changed/'journal.json').mkdir()
            with self.subTest(change=change),self.assertRaises(ValueError):self.verify(changed,pin)

    def test_package_inventory_stops_at_first_unexpected_entry(self):
        bundle,_,pin=self.backup();original_scandir=os.scandir;seen=[]
        class Entries:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def __iter__(self):return self
            def __next__(self):
                names=('manifest.json','journal.json','unexpected.json')
                if len(seen)>=len(names):raise AssertionError('Inventory consumed unbounded extra entries')
                name=names[len(seen)];seen.append(name)
                return type('Entry',(),{'name':name})()
        def scan(path):return Entries()if Path(path)==bundle else original_scandir(path)
        with patch.object(os,'scandir',side_effect=scan),self.assertRaises(ValueError):self.verify(bundle,pin)
        self.assertEqual(['manifest.json','journal.json','unexpected.json'],seen)

    def test_duplicate_nonfinite_malformed_and_unknown_secret_fields_refuse_backup(self):
        original=self.journal.read_bytes()
        valid=original.rstrip()
        cases=[valid[:-1]+b',"pending":null}',valid[:-1]+b',"\\u0070ending":null}',b'{"pending":NaN}',
               b'{"pending":1e999}',b'\xff',b'[0,1]',original[:-1]+b'BROKEN',
               (json.dumps({**self.state,'private_key':'SYNTHETIC-UNSUPPORTED-SECRET'})+'\n').encode()]
        for index,raw in enumerate(cases):
            self.journal.write_bytes(raw)
            output=self.root/('bad-json-'+str(index))
            with self.subTest(index=index),self.assertRaises(ValueError):
                subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
            self.assertEqual(raw,self.journal.read_bytes())
            self.assertFalse(output.exists())
        self.journal.write_bytes(original)

    def test_source_compatible_producer_provenance_is_retained_without_reader_relabelling(self):
        bundle,manifest,_=self.backup();changed=self.copy_bundle(bundle,'prior-producer')
        prior=copy.deepcopy(manifest)
        prior['producer_files_sha256']={name:'9'*64 for name in prior['producer_files_sha256']}
        raw=(json.dumps(prior,sort_keys=True,separators=(',',':'))+'\n').encode()
        (changed/'manifest.json').write_bytes(raw)
        # The separately supplied trusted pin deliberately selects this prior
        # compatible producer record; runtime source identity remains exact.
        verified=self.verify(changed,SHA(raw))
        self.assertEqual(prior['producer_files_sha256'],verified['producer_files_sha256'])
        self.assertEqual(manifest['source_files_sha256'],verified['source_files_sha256'])
        self.assertEqual(self.raw,(changed/'journal.json').read_bytes())

    def test_current_profile_pairs_and_unsupported_combinations_are_explicit(self):
        for key,value in (('accounting_version',6),('custody_version',4),('fee_intake_version',0),
                          ('rebalance_confirmation_version',2),('lp_routing_version',2)):
            old=self.config[key];self.config[key]=value;self.write_config()
            output=self.root/('profile-'+key)
            with self.subTest(key=key),self.assertRaises(ValueError):
                subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
            self.assertFalse(output.exists());self.config[key]=old
        self.write_config()
        state=copy.deepcopy(self.state);state['execution_price_version']=0
        self.config['execution_price_version']=0;self.config['lp_routing_version']=2
        self.write_config();self.write_state(state)
        bundle,_,pin=self.backup('execution-zero')
        self.assertIsInstance(self.verify(bundle,pin),dict)

    def test_age_and_reviewed_floors_are_explicit_without_latest_state_claim(self):
        bundle,_,pin=self.backup()
        self.assertIsInstance(subject.verify(bundle,pin,self.config_path,max_age_seconds=60,
            minimum_created_at=NOW,minimum_next_nonce=0,now=NOW+60),dict)
        cases=({'now':NOW+61},{'now':NOW-1},{'minimum_created_at':NOW+1},
               {'minimum_next_nonce':1})
        for case in cases:
            options={'max_age_seconds':60,'now':NOW+30,**case}
            with self.subTest(case=case),self.assertRaises(ValueError):
                subject.verify(bundle,pin,self.config_path,**options)

    def test_occupied_outputs_and_source_overlap_never_overwrite_existing_truth(self):
        bundle,_,pin=self.backup()
        occupied=self.root/'occupied';occupied.mkdir();sentinel=occupied/'keep'
        sentinel.write_bytes(b'ORIGINAL')
        for output in (occupied,self.journal,self.work,self.config_path,bundle):
            with self.subTest(output=output.name),self.assertRaises(ValueError):
                subject.restore(bundle,pin,self.config_path,output,max_age_seconds=60,now=NOW+30)
        self.assertEqual(b'ORIGINAL',sentinel.read_bytes())
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,bundle,working_directory=self.work,now=NOW)
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.work/'runtime'/'nested',working_directory=self.work,now=NOW)

    def test_state_aliases_to_configuration_or_signer_files_are_refused(self):
        original=dict(self.config)
        for index,key in enumerate(('keystore','password_file','health_path','lock_path')):
            self.config={**original,key:original['state_path']};self.write_config()
            output=self.root/('alias-'+str(index))
            with self.subTest(key=key),self.assertRaises(ValueError):
                subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
            self.assertFalse(output.exists())
        self.config={**original,'state_path':str(self.config_path)};self.write_config()
        original_config=self.config_path.read_bytes()
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.root/'config-as-state',working_directory=self.work,now=NOW)
        self.assertEqual(original_config,self.config_path.read_bytes())
        self.config=original;self.write_config()

    def test_hardlink_journal_and_bundle_payload_are_refused(self):
        if not hasattr(os,'link'):self.skipTest('Hardlinks unavailable on this platform')
        alias=self.work/'runtime'/'journal-alias.json'
        try:os.link(self.journal,alias)
        except OSError:self.skipTest('Hardlink creation is not permitted')
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.root/'hardlink-source',working_directory=self.work,now=NOW)
        alias.unlink()
        bundle,_,pin=self.backup();os.link(bundle/'journal.json',self.root/'payload-alias')
        with self.assertRaises(ValueError):self.verify(bundle,pin)

    def test_symlink_source_parent_and_package_payload_are_refused(self):
        link=self.root/'journal-link'
        try:link.symlink_to(self.journal)
        except (OSError,NotImplementedError):self.skipTest('Symlink creation is not permitted')
        self.config['state_path']=str(link);self.write_config()
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.root/'linked-source',working_directory=self.work,now=NOW)
        directory_link=self.root/'working-link';directory_link.symlink_to(self.work,target_is_directory=True)
        self.config['state_path']=str(directory_link/'runtime'/'journal.json');self.write_config()
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.root/'linked-parent',working_directory=self.work,now=NOW)
        self.config['state_path']='runtime/journal.json';self.write_config()
        bundle,_,pin=self.backup();(bundle/'journal.json').unlink();(bundle/'journal.json').symlink_to(self.journal)
        with self.assertRaises(ValueError):self.verify(bundle,pin)

    def test_tool_limits_do_not_mutate_financial_configuration(self):
        before=self.config_path.read_bytes()
        for options in ({'max_bytes':0},{'max_bytes':64*1024*1024+1},
                        {'max_bytes':True},{'max_seconds':0},{'max_seconds':301},
                        {'max_seconds':True},{'now':True}):
            with self.subTest(options=options),self.assertRaises(ValueError):
                subject.backup(self.config_path,self.root/'invalid-limit',working_directory=self.work,
                               **{'now':NOW,**options})
            self.assertFalse((self.root/'invalid-limit').exists())
        with self.assertRaises(ValueError):
            subject.backup(self.config_path,self.root/'small-limit',working_directory=self.work,max_bytes=1,now=NOW)
        self.assertEqual(before,self.config_path.read_bytes())

    def test_source_release_drift_is_detected_without_mutating_originals(self):
        bundle,_,pin=self.backup()
        # Only the digest provider is changed, not a project source file.
        original=subject.source_hashes()
        changed={**original,next(iter(original)):'0'*64}
        before=(self.journal.read_bytes(),self.config_path.read_bytes())
        with patch.object(subject,'source_hashes',return_value=changed),self.assertRaises(ValueError):
            self.verify(bundle,pin)
        self.assert_source_preserved(before)

    def test_selected_refusal_codes_are_actionable_and_never_echo_private_values(self):
        bundle,_,pin=self.backup()
        def refused(code,operation):
            with self.assertRaises(subject.RecoveryRefusal)as caught:operation()
            self.assertEqual(code,caught.exception.code)
            self.assertNotIn(self.credential,str(caught.exception)+caught.exception.code)
            self.assertNotIn(str(self.config_path),str(caught.exception))
            self.assertLess(len(str(caught.exception)),200)
        refused('trusted_pin',lambda:self.verify(bundle,'0'*64))
        refused('backup_age_or_floor',lambda:subject.verify(bundle,pin,self.config_path,
            max_age_seconds=60,now=NOW+61))
        original=self.config_path.read_bytes();self.config_path.write_bytes(original+b' ')
        refused('config_identity',lambda:self.verify(bundle,pin))
        self.config_path.write_bytes(original)
        extra=bundle/'unexpected.json';extra.write_bytes(b'{}');extra.chmod(0o600)
        refused('package_inventory',lambda:self.verify(bundle,pin));extra.unlink()
        bogus=subject.RecoveryRefusal(self.credential)
        self.assertEqual('invalid_input',bogus.code)
        self.assertNotIn(self.credential,str(bogus))

    def test_atomic_source_change_after_capture_refuses_publication_without_rollback(self):
        original_read=subject._read;replacement=self.journal.with_name('next-journal.json')
        next_bytes=self.raw+b'\n';replacement.write_bytes(next_bytes);replacement.chmod(0o600)
        changed=[];config_before=self.config_path.read_bytes()
        def replacing(path,*args,**kwargs):
            result=original_read(path,*args,**kwargs)
            if Path(path)==self.journal and not changed:
                os.replace(replacement,self.journal);changed.append(True)
            return result
        output=self.root/'raced-backup'
        with patch.object(subject,'_read',side_effect=replacing),self.assertRaises(ValueError):
            subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
        self.assertEqual([True],changed)
        self.assertEqual(next_bytes,self.journal.read_bytes())
        self.assertEqual(config_before,self.config_path.read_bytes())
        self.assertFalse(output.exists())

    def test_mid_publication_fsync_refusal_preserves_source_and_no_complete_bundle(self):
        output=self.root/'interrupted';before=(self.journal.read_bytes(),self.config_path.read_bytes())
        original_sync=os.fsync;failed=[]
        def fail_journal(fd):
            target=output/'journal.json'
            if target.exists()and (os.fstat(fd).st_dev,os.fstat(fd).st_ino)==(target.stat().st_dev,target.stat().st_ino)and not failed:
                failed.append(True);raise OSError(errno.ENOSPC,'SYNTHETIC-INJECTED-FAILURE')
            return original_sync(fd)
        with patch.object(os,'fsync',side_effect=fail_journal),self.assertRaises(ValueError):
            subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
        self.assertEqual([True],failed);self.assert_source_preserved(before)
        self.assertFalse((output/'manifest.json').exists())
        if output.exists():
            with self.assertRaises(ValueError):self.verify(output,'a'*64)

    def test_cli_real_backup_verify_restore_round_trip_stays_offline_unsigned(self):
        spec=importlib.util.spec_from_file_location('new_keeper_recovery_cli_actions',ROOT/'scripts/keeper-recovery.py')
        cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
        output=self.root/'cli-bundle';restored=self.root/'cli-restored'
        def invoke(args):
            out,err=io.StringIO(),io.StringIO()
            with redirect_stdout(out),redirect_stderr(err):result=cli.main(args)
            self.assertEqual(0,result,err.getvalue());self.assertEqual('',err.getvalue())
            self.assertNotIn(self.credential,out.getvalue());self.assertNotIn(self.key_marker,out.getvalue())
            return out.getvalue()
        first=invoke(['backup','--config',str(self.config_path),'--working-directory',str(self.work),'--output',str(output)])
        pin=SHA((output/'manifest.json').read_bytes());self.assertIn(pin,first)
        args=['--bundle',str(output),'--manifest-sha256',pin,'--config',str(self.config_path),'--max-age-seconds','60']
        self.assertIn(pin,invoke(['verify',*args]))
        last=invoke(['restore',*args,'--output',str(restored)])
        self.assertIn(SHA((restored/'RESTORE_PLAN.json').read_bytes()),last)
        self.assertEqual(self.raw,(restored/'keeper-state.json').read_bytes())
        self.assertEqual(self.raw,self.journal.read_bytes())

    @unittest.skipUnless(os.name=='posix','Selected separately on Ubuntu only')
    def test_posix_private_output_modes_and_writable_parent_refusal(self):
        bundle,_,pin=self.backup();restored,_,_=self.restore(bundle,pin)
        for folder in (bundle,restored):
            self.assertEqual(0o700,stat.S_IMODE(folder.stat().st_mode))
            for path in folder.iterdir():self.assertEqual(0o600,stat.S_IMODE(path.stat().st_mode))
        before=(self.journal.read_bytes(),self.config_path.read_bytes())
        self.journal.parent.chmod(0o777)
        try:
            with self.assertRaises(ValueError):
                subject.backup(self.config_path,self.root/'unsafe-source',working_directory=self.work,now=NOW)
        finally:self.journal.parent.chmod(0o700)
        unsafe=self.root/'unsafe-output-parent';unsafe.mkdir(mode=0o777);unsafe.chmod(0o777)
        try:
            with self.assertRaises(ValueError):
                subject.backup(self.config_path,unsafe/'new-bundle',working_directory=self.work,now=NOW)
        finally:unsafe.chmod(0o700)
        self.assert_source_preserved(before)

    @unittest.skipUnless(os.name=='posix','Selected separately on Ubuntu only')
    def test_posix_atomic_source_replace_during_open_fd_capture_refuses_without_rollback(self):
        replacement=self.journal.with_name('new-atomic-journal.json')
        next_bytes=self.raw+b'\n';replacement.write_bytes(next_bytes);replacement.chmod(0o600)
        original_read=os.read;identity=(self.journal.stat().st_dev,self.journal.stat().st_ino)
        changed=[];config_before=self.config_path.read_bytes()
        def replacing(fd,size):
            value=original_read(fd,size)
            if value and not changed and (os.fstat(fd).st_dev,os.fstat(fd).st_ino)==identity:
                os.replace(replacement,self.journal);changed.append(True)
            return value
        output=self.root/'fd-race'
        with patch.object(os,'read',side_effect=replacing),self.assertRaises(ValueError):
            subject.backup(self.config_path,output,working_directory=self.work,now=NOW)
        self.assertEqual([True],changed);self.assertEqual(next_bytes,self.journal.read_bytes())
        self.assertEqual(config_before,self.config_path.read_bytes());self.assertFalse(output.exists())


class KeeperRecoveryCliTests(unittest.TestCase):
    def cli(self):
        spec=importlib.util.spec_from_file_location('new_keeper_recovery_cli',ROOT/'scripts/keeper-recovery.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_no_signing_installation_replacement_or_private_key_option_exists(self):
        cli=self.cli()
        with tempfile.TemporaryDirectory(prefix='popl-new-keeper-cli-')as temp:
            root=Path(temp)
            required=['verify','--bundle',str(root/'not-a-bundle'),'--manifest-sha256','a'*64,
                      '--config',str(root/'not-a-config'),'--max-age-seconds','60']
            for flag in ('--live','--broadcast','--install','--replace','--private-key','--rpc-url'):
                suffix=[flag]+(['SYNTHETIC-SECRET-ARGUMENT']if flag in ('--private-key','--rpc-url')else[])
                with self.subTest(flag=flag),redirect_stderr(io.StringIO()),self.assertRaises(SystemExit)as raised:
                    cli.main(required+suffix)
                self.assertEqual(2,raised.exception.code)

    def test_rejected_argument_values_are_not_echoed(self):
        cli=self.cli();secret='SYNTHETIC-CLI-SECRET-DO-NOT-ECHO'
        out,err=io.StringIO(),io.StringIO()
        with tempfile.TemporaryDirectory(prefix='popl-new-keeper-cli-')as temp:
            root=Path(temp)
            args=['backup','--config',str(root/'config.json'),'--working-directory',str(root),
                  '--output',str(root/'new-output'),'--unknown-option',secret]
            with redirect_stdout(out),redirect_stderr(err),self.assertRaises(SystemExit)as raised:
                cli.main(args)
        self.assertEqual(2,raised.exception.code)
        self.assertNotIn(secret,out.getvalue()+err.getvalue())

    def test_bad_private_input_error_does_not_echo_value_path_or_traceback(self):
        cli=self.cli();secret='SYNTHETIC-PRIVATE-INPUT-SENTINEL'
        with tempfile.TemporaryDirectory(prefix='popl-new-keeper-cli-')as temp:
            root=Path(temp);config=root/(secret+'.json')
            raw=('{"'+secret+'":BROKEN}').encode();config.write_bytes(raw);config.chmod(0o600)
            output=root/'new-output';out,err=io.StringIO(),io.StringIO()
            with redirect_stdout(out),redirect_stderr(err):
                result=cli.main(['backup','--config',str(config),'--working-directory',str(root),
                                 '--output',str(output)])
            self.assertEqual(1,result)
            self.assertNotIn(secret,out.getvalue()+err.getvalue())
            self.assertNotIn(str(config),out.getvalue()+err.getvalue())
            self.assertNotIn('Traceback',out.getvalue()+err.getvalue())
            self.assertEqual(raw,config.read_bytes());self.assertFalse(output.exists())

    def test_cli_starts_without_importing_daemon_or_any_network_signing_operation(self):
        # A fresh interpreter proves that importing the unsigned command does
        # not transitively import the daemon or launch an external process.
        launcher='''
import importlib.util,pathlib,socket,subprocess,sys
def denied(*args,**kwargs): raise AssertionError('Forbidden unsigned CLI side effect')
socket.socket.connect=denied
socket.create_connection=denied
subprocess.Popen=denied
path=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('unsigned_cli_probe',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert 'keeper.monitor' not in sys.modules
try: module.main(['--help'])
except SystemExit as exc: assert exc.code==0
'''
        result=subprocess.run([sys.executable,'-B','-c',launcher,str(ROOT/'scripts/keeper-recovery.py')],
            cwd=ROOT,capture_output=True,timeout=15,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertIn('keeper',result.stdout.lower())


if __name__=='__main__':unittest.main()
