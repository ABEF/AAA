"""NEW focused alert regressions; no old test body is selected or inherited.

Reuse only the already published fixture/setup helpers. Each scenario calls the
public one-shot observer and checks original input bytes, not a mock state machine.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from keeper import alerts, recovery_bundle
from tests_python import test_keeper_alerts as fixtures


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


class KeeperAlertAuditTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.KeeperAlertsTests()
        self.addCleanup(self.f.doCleanups)
        self.f.setUp()

    def state(self):
        return json.loads((self.f.alert_dir/'state.json').read_bytes())

    def once(self,**overrides):
        f=self.f
        options=dict(working_directory=f.work,backup_bundle=f.bundle,
            backup_manifest_sha256=f.backup_pin,backup_config_path=f.config_path,
            directory=f.alert_dir,max_health_age_seconds=600,max_backup_age_seconds=900,
            pending_max_age_seconds=120,now=fixtures.NOW)
        options.update(overrides)
        paths=(f.config_path,f.journal,Path(f.config['health_path']),
               f.bundle/'manifest.json',f.bundle/'journal.json')
        def raw(path):
            try:return path.read_bytes()
            except FileNotFoundError:return None
        before=[raw(path)for path in paths]
        actual_open=os.open
        def no_signer(path,*args,**kwargs):
            if isinstance(path,(str,bytes,os.PathLike)):
                self.assertNotIn(Path(os.fsdecode(path)).absolute(),(f.key.absolute(),f.password.absolute()))
            return actual_open(path,*args,**kwargs)
        with patch('os.open',no_signer):
            result=alerts.run_once(f.config_path,**options)
        self.assertEqual(before,[raw(path)for path in paths])
        self.assertFalse(result['readiness_approved'])
        for marker in f.secret_markers:
            self.assertNotIn(marker,json.dumps(result))
        return result

    def original_backup_config(self):
        path=self.f.root/'original-backup-config.json'
        path.write_bytes(self.f.config_path.read_bytes());path.chmod(0o600)
        return path

    def test_missing_health_preserves_pending_clock_and_prolonged_alert(self):
        f=self.f;f.set_pending();self.once()
        original=copy.deepcopy(self.state()['pending'])
        path=Path(f.config['health_path']);path.unlink()
        unavailable=self.once(now=fixtures.NOW+60)
        self.assertIn('health_unavailable',unavailable['observation']['reason_codes'])
        self.assertEqual(original,self.state()['pending'])
        f.set_pending(now=fixtures.NOW+121)
        restored=self.once(now=fixtures.NOW+121)
        self.assertEqual(original,self.state()['pending'])
        self.assertEqual(121,restored['observation']['pending_observed_seconds'])
        self.assertIn('pending_prolonged',restored['observation']['reason_codes'])
        self.assertEqual('incident',restored['observation']['classification'])

    def test_missing_or_invalid_journal_preserves_last_known_pending_clock(self):
        f=self.f
        for index,raw in enumerate((None,b'{"invalid":true}\n')):
            f.alert_dir=f.root/('journal-outage-'+str(index))
            start=fixtures.NOW+index*200
            f.set_pending(now=start);self.once(now=start)
            original=copy.deepcopy(self.state()['pending'])
            saved=f.journal.read_bytes()
            if raw is None:f.journal.unlink()
            else:f.journal.write_bytes(raw)
            try:
                refused=self.once(now=start+60)
                self.assertIn('journal_unavailable',refused['observation']['reason_codes'])
                self.assertEqual(original,self.state()['pending'])
            finally:
                f.journal.write_bytes(saved);f.journal.chmod(0o600)
            f.set_pending(now=start+121)
            result=self.once(now=start+121)
            self.assertEqual(original,self.state()['pending'])
            self.assertEqual(121,result['observation']['pending_observed_seconds'])
            self.assertIn('pending_prolonged',result['observation']['reason_codes'])

    def test_missing_configuration_does_not_erase_pending_observation(self):
        f=self.f;f.set_pending();self.once()
        original=copy.deepcopy(self.state()['pending'])
        saved=f.config_path.read_bytes();f.config_path.unlink()
        try:
            result=self.once(now=fixtures.NOW+60)
            self.assertIn('configuration_unavailable',result['observation']['reason_codes'])
            self.assertEqual(original,self.state()['pending'])
        finally:
            f.config_path.write_bytes(saved);f.config_path.chmod(0o600)
        f.set_pending(now=fixtures.NOW+121)
        result=self.once(now=fixtures.NOW+121)
        self.assertEqual(121,result['observation']['pending_observed_seconds'])
        self.assertIn('pending_prolonged',result['observation']['reason_codes'])

    def test_invalidated_snapshot_cannot_replace_the_last_known_intent_clock(self):
        f=self.f;f.set_pending();self.once()
        original=copy.deepcopy(self.state()['pending'])
        original_journal=f.journal.read_bytes()
        candidate=copy.deepcopy(f.state);candidate['pending']['key']='harvest:999'
        actual_health_check=alerts.health_check
        actual_sources=recovery_bundle.source_hashes
        restored=False
        def expose_candidate(config,**kwargs):
            result=actual_health_check(config,**kwargs)
            f.journal.write_bytes(encoded(candidate))
            return result
        def restore_original(*args,**kwargs):
            nonlocal restored
            if not restored:
                f.journal.write_bytes(original_journal);restored=True
            return actual_sources(*args,**kwargs)
        with patch.object(alerts,'health_check',expose_candidate), \
                patch.object(recovery_bundle,'source_hashes',restore_original):
            result=self.once(now=fixtures.NOW+60)
        self.assertTrue(restored)
        self.assertIn('input_identity_invalid',result['observation']['reason_codes'])
        self.assertEqual(original,self.state()['pending'])
        self.assertIsNone(result['observation']['pending_observed_seconds'])
        self.assertEqual(original_journal,f.journal.read_bytes())
        f.set_pending(now=fixtures.NOW+121)
        later=self.once(now=fixtures.NOW+121)
        self.assertEqual(121,later['observation']['pending_observed_seconds'])
        self.assertIn('pending_prolonged',later['observation']['reason_codes'])

    def test_valid_new_intent_restarts_clock_and_valid_empty_journal_clears_it(self):
        f=self.f;f.set_pending();self.once()
        first=self.state()['pending']
        f.set_pending(now=fixtures.NOW+60)
        f.state['pending']['key']='harvest:999'
        f.state['pending']['data']='0x12345678'
        f.write_state();f.health['pending_action']='harvest:999';f.write_health()
        result=self.once(now=fixtures.NOW+60)
        current=self.state()['pending']
        self.assertNotEqual(first['intent_sha256'],current['intent_sha256'])
        self.assertEqual(fixtures.NOW+60,current['first_seen'])
        self.assertEqual(0,result['observation']['pending_observed_seconds'])
        f.state['pending']=None;f.write_state()
        Path(f.config['health_path']).unlink()
        result=self.once(now=fixtures.NOW+80)
        self.assertIn('health_unavailable',result['observation']['reason_codes'])
        self.assertIsNone(self.state()['pending'])

    def test_unrecognized_pending_envelope_cannot_clear_last_known_clock(self):
        f=self.f;f.set_pending();self.once()
        original=copy.deepcopy(self.state()['pending'])
        # The backup envelope can preserve a fee-consistent payable intent,
        # while normal keeper-grace admission deliberately supports value0.
        f.state['pending']['value']=1
        f.state['pending']['fee_review']['maximum_cost_wei']+=1
        f.write_state()
        result=self.once(now=fixtures.NOW+60)
        self.assertIn('pending_ambiguous',result['observation']['reason_codes'])
        self.assertEqual(original,self.state()['pending'])
        self.assertIsNone(result['observation']['pending_observed_seconds'])
        f.set_pending(now=fixtures.NOW+121)
        recovered=self.once(now=fixtures.NOW+121)
        self.assertEqual(121,recovered['observation']['pending_observed_seconds'])
        self.assertIn('pending_prolonged',recovered['observation']['reason_codes'])

    def test_default_model_identity_matches_backup_and_preserves_same_intent_age(self):
        f=self.f;f.config.pop('accounting_model');f.write_config();f.set_pending()
        f.bundle=f.root/'omitted-model-backup'
        _,f.backup_pin=recovery_bundle.backup(f.config_path,f.bundle,working_directory=f.work,now=fixtures.NOW)
        original_config=self.original_backup_config()
        initial=self.once();self.assertTrue(initial['observation']['backup_ok'])
        first_seen=self.state()['pending']['first_seen']
        f.config['accounting_model']='shared-pools-v2';f.write_config()
        f.set_pending(now=fixtures.NOW+30)
        current=self.once(backup_config_path=original_config,now=fixtures.NOW+30)
        self.assertTrue(current['observation']['backup_ok'])
        self.assertNotIn('backup_identity_mismatch',current['observation']['reason_codes'])
        self.assertEqual(first_seen,self.state()['pending']['first_seen'])
        self.assertEqual(30,current['observation']['pending_observed_seconds'])
        self.assertIn('monitor_identity_changed',current['observation']['reason_codes'])

    def test_legacy_omitted_model_fingerprint_keeps_existing_first_seen(self):
        f=self.f;f.config.pop('accounting_model');f.write_config();f.set_pending()
        f.bundle=f.root/'legacy-model-backup'
        _,f.backup_pin=recovery_bundle.backup(f.config_path,f.bundle,working_directory=f.work,now=fixtures.NOW)
        original_config=self.original_backup_config();self.once()
        state=self.state();pending=f.state['pending']
        identity={key:f.config.get(key,0 if key.endswith('_version')else None)for key in (
            'chain_id','sender','contracts','accounting_model','accounting_version','custody_version',
            'protocol_policy_version','portfolio_version','maintenance_policy_version',
            'rebalance_confirmation_version','fee_intake_version','lp_routing_version',
            'execution_quality_version','execution_price_version','royalty_settlement_version')}
        legacy=hashlib.sha256(encoded([identity,pending['key'],pending['nonce'],pending['to'].lower(),
                                      pending['data'].lower(),pending['value']])).hexdigest()
        state['pending']={'intent_sha256':legacy,'first_seen':fixtures.NOW}
        (f.alert_dir/'state.json').write_bytes(encoded(state))
        f.config['accounting_model']='shared-pools-v2';f.write_config()
        f.set_pending(now=fixtures.NOW+30)
        result=self.once(backup_config_path=original_config,now=fixtures.NOW+30)
        migrated=self.state()['pending']
        self.assertEqual(fixtures.NOW,migrated['first_seen'])
        self.assertNotEqual(legacy,migrated['intent_sha256'])
        self.assertEqual(30,result['observation']['pending_observed_seconds'])

    def test_pending_grace_can_lack_observations_but_cannot_mask_invalid_present_proof(self):
        f=self.f;f.set_pending()
        original_health=copy.deepcopy(f.health)
        f.health['lp_execution_health'].update(state='pending_recovery',last_confirmed=None)
        f.health['rebalance_confirmation_health']['policy'].update(state='pending_recovery',last_observed=None)
        f.health['last_success_at']=None;f.write_health()
        grace=self.once()
        self.assertEqual('pending_grace',grace['observation']['classification'])
        self.assertFalse(grace['observation']['health_ok'])
        self.assertEqual(0,grace['active_incident_count'])
        f.health=original_health
        f.set_pending(now=fixtures.NOW+30)
        f.observations()[0]['source_files_sha256']['keeper/monitor.py']='0'*64
        f.write_health()
        incident=self.once(now=fixtures.NOW+30)
        self.assertEqual('incident',incident['observation']['classification'])
        self.assertFalse(incident['observation']['health_ok'])
        f.set_pending(now=fixtures.NOW+60)
        receiver,records=f.receiver()
        still_pending=self.once(now=fixtures.NOW+60,receiver=receiver)
        self.assertEqual('pending_grace',still_pending['observation']['classification'])
        self.assertFalse(still_pending['observation']['health_ok'])
        self.assertGreater(still_pending['active_incident_count'],0)
        self.assertNotIn('recovery',[row['body']['type']for row in records])

    def test_actual_observer_source_change_alerts_without_resetting_pending_age(self):
        f=self.f
        source_root=f.root/'reviewed-copy';source_root.mkdir(mode=0o700)
        for name in alerts.OBSERVER_SOURCE_FILES:
            destination=source_root/name;destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            destination.write_bytes((recovery_bundle.ROOT/name).read_bytes());destination.chmod(0o600)
        actual_sources=recovery_bundle._sources
        def observer_sources(names,budget):
            # Only this exact new observer identity uses the private copy.
            # Daemon13 and original backup verification keep their real root.
            if tuple(names)!=alerts.OBSERVER_SOURCE_FILES:
                return actual_sources(names,budget)
            with patch.object(recovery_bundle,'ROOT',source_root):
                return actual_sources(names,budget)
        with patch.object(recovery_bundle,'_sources',observer_sources):
            f.set_pending();self.once()
            original=copy.deepcopy(self.state()['pending'])
            path=source_root/'keeper/alerts.py';path.write_bytes(path.read_bytes()+b'\n# Test-only copied source identity.\n')
            f.set_pending(now=fixtures.NOW+30)
            changed=self.once(now=fixtures.NOW+30)
            self.assertTrue(changed['observation']['backup_ok'])
            self.assertIn('monitor_identity_changed',changed['observation']['reason_codes'])
            self.assertEqual(original,self.state()['pending'])
            self.assertEqual(30,changed['observation']['pending_observed_seconds'])
            f.state['pending']=None;f.write_state();f.make_health(now=fixtures.NOW+60)
            stable=self.once(now=fixtures.NOW+60)
            self.assertTrue(stable['observation']['health_ok'])
            self.assertTrue(stable['observation']['backup_ok'])
            self.assertEqual('healthy',stable['observation']['classification'])
            self.assertEqual(0,stable['active_incident_count'])
            self.assertTrue(any(event['type']=='recovery'for event in self.state()['outbox']))
