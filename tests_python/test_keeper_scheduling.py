"""NEW unsigned scheduling checks; no old test body or real process is run.

The old alert fixture supplies public JSON vectors and setup helpers only. Each
method composes the new scheduler with the real backup and observer validators.
The native systemd/timer proof is separate and must not be inferred from this.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from keeper import alerts, recovery_bundle, scheduling as subject
from tests_python import test_keeper_alerts as fixture_module
from zzz_ops.state import process_lock


ROOT = Path(__file__).resolve().parents[1]
NOW = fixture_module.NOW


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class KeeperSchedulingTests(unittest.TestCase):
    def setUp(self):
        # Composition, not inheritance: none of the old test methods is selected.
        self.fixture = fixture_module.KeeperAlertsTests(methodName='runTest')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.root = self.fixture.root
        self.policy_path = self.root / 'schedule-policy.json'
        self.scheduler = self.root / 'schedule-state'
        self.backups = self.root / 'scheduled-backups'
        self.observer = self.root / 'scheduled-alerts'
        source_names = tuple(dict.fromkeys((*recovery_bundle.SOURCE_FILES,
            *alerts.OBSERVER_SOURCE_FILES, 'keeper/scheduling.py', 'scripts/keeper-schedule.py')))
        self.policy = {
            'schema': 1, 'kind': 'popl-keeper-schedule',
            'configuration': str(self.fixture.config_path),
            'configuration_sha256': digest(self.fixture.config_path.read_bytes()),
            'working_directory': str(self.fixture.work),
            'scheduler_directory': str(self.scheduler),
            'backup_directory': str(self.backups), 'alert_directory': str(self.observer),
            'source_files_sha256': {name: digest((ROOT / name).read_bytes()) for name in source_names},
            'max_backups': 8, 'max_health_age_seconds': 600,
            'max_backup_age_seconds': 900, 'pending_max_age_seconds': 120,
            'receiver': None, 'allow_dry_run': False,
            'max_bytes': 16 * 1024 * 1024, 'max_seconds': 60,
        }
        self.write_policy()

    def write_policy(self):
        raw = (json.dumps(self.policy, sort_keys=True, separators=(',', ':')) + '\n').encode()
        self.policy_path.write_bytes(raw)
        self.policy_path.chmod(0o600)
        self.policy_pin = digest(raw)

    def run_action(self, action, *, now=NOW, pin=None, **kwargs):
        # Secret files are never opened by scheduled calls. The fixture's global
        # process/network guards independently prevent signing and public IO.
        original_open = os.open
        protected = {self.fixture.key.absolute(), self.fixture.password.absolute()}

        def checked_open(path, *args, **kwargs):
            if isinstance(path, (str, bytes, os.PathLike)):
                self.assertNotIn(Path(os.fsdecode(path)).absolute(), protected)
            return original_open(path, *args, **kwargs)

        with patch('os.open', checked_open):
            return subject.run_once(action, self.policy_path,
                self.policy_pin if pin is None else pin, now=now, **kwargs)

    def observer_state(self):
        return json.loads((self.observer / 'state.json').read_bytes())

    def test_initialization_rotation_and_observation_preserve_exact_journal_and_config(self):
        original = (self.fixture.journal.read_bytes(), self.fixture.config_path.read_bytes())
        initialized = self.run_action('init')
        self.assertIs(initialized['unsigned'], True)
        self.assertIs(initialized['readiness_approved'], False)
        self.assertEqual(1, len(list(self.backups.iterdir())))
        self.run_action('backup', now=NOW + 1)
        self.assertEqual(2, len(list(self.backups.iterdir())))
        observed = self.run_action('observe', now=NOW + 2)
        self.assertIs(observed['unsigned'], True)
        self.assertIs(observed['readiness_approved'], False)
        self.assertEqual(original, (self.fixture.journal.read_bytes(), self.fixture.config_path.read_bytes()))
        self.assertEqual(0, len(self.observer_state()['outbox']))
        for output in (initialized, observed):
            for marker in self.fixture.secret_markers:
                self.assertNotIn(marker, json.dumps(output))

    def test_unreviewed_policy_configuration_source_and_overlapping_paths_refuse_before_output(self):
        original = copy.deepcopy(self.policy)
        variants = [
            ('wrong_policy_pin', lambda: None),
            ('wrong_configuration_pin', lambda: self.policy.update(configuration_sha256='11' * 32)),
            ('wrong_source_pin', lambda: self.policy['source_files_sha256'].update({'keeper/alerts.py': '22' * 32})),
            ('bool_capacity', lambda: self.policy.update(max_backups=True)),
            ('unknown_source', lambda: self.policy['source_files_sha256'].update({'extra.py': '33' * 32})),
            ('journal_parent_overlap', lambda: self.policy.update(scheduler_directory=str(self.fixture.runtime))),
            ('nested_output', lambda: self.policy.update(alert_directory=str(self.scheduler / 'nested'))),
        ]
        for name, change in variants:
            with self.subTest(name=name):
                self.policy = copy.deepcopy(original)
                change()
                self.write_policy()
                with self.assertRaises(subject.ScheduleRefusal):
                    self.run_action('init', pin='44' * 32 if name == 'wrong_policy_pin' else None)
                self.assertFalse(self.backups.exists())
                self.assertFalse(self.scheduler.exists())
                self.assertFalse(self.observer.exists())

    def test_missing_observer_commit_and_orphan_temp_never_reinitialize_history(self):
        self.run_action('init')
        committed = (self.observer / 'state.json').read_bytes()
        scheduler_before = {p.name: p.read_bytes() for p in self.scheduler.iterdir()}
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('init')
        self.assertEqual(committed, (self.observer / 'state.json').read_bytes())
        (self.observer / 'state.json').unlink()
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('observe')
        self.assertFalse((self.observer / 'state.json').exists())
        self.assertEqual(scheduler_before, {p.name: p.read_bytes() for p in self.scheduler.iterdir()})
        (self.observer / 'state.json').write_bytes(committed)
        (self.observer / 'state.json').chmod(0o600)
        residue = self.observer / '.state.json.interrupted.tmp'
        residue.write_bytes(b'preserve-unpublished-residue')
        residue.chmod(0o600)
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('observe')
        self.assertEqual(committed, (self.observer / 'state.json').read_bytes())
        self.assertEqual(b'preserve-unpublished-residue', residue.read_bytes())

    def test_missing_health_and_journal_remain_alertable_without_resetting_pending_clock(self):
        self.fixture.set_pending(now=NOW)
        self.run_action('init')
        first = self.observer_state()['pending']
        self.assertIsNotNone(first)
        health_path = Path(self.fixture.config['health_path'])
        health_path.rename(health_path.with_suffix('.saved'))
        self.run_action('observe', now=NOW + 30)
        missing_health = self.observer_state()
        self.assertEqual(first, missing_health['pending'])
        self.assertIn('health_unavailable', missing_health['active'])
        original_journal = self.fixture.journal.read_bytes()
        self.fixture.journal.unlink()
        self.run_action('observe', now=NOW + 60)
        missing_both = self.observer_state()
        self.assertEqual(first, missing_both['pending'])
        self.assertIn('journal_unavailable', missing_both['active'])
        self.assertFalse(self.fixture.journal.exists())
        self.assertTrue(original_journal)

    def test_competing_schedule_lock_cannot_rotate_or_mutate_observer_state(self):
        self.run_action('init')
        original_selection = (self.scheduler / subject.SELECTION_NAME).read_bytes()
        original_observer = (self.observer / 'state.json').read_bytes()
        original_generations = sorted(p.name for p in self.backups.iterdir())
        with process_lock(self.scheduler / subject.LOCK_NAME):
            for action in ('backup', 'observe'):
                with self.subTest(action=action):
                    with self.assertRaises(subject.ScheduleRefusal) as caught:
                        self.run_action(action, now=NOW + 1)
                    self.assertEqual('scheduler_lock', caught.exception.code)
        self.assertEqual(original_selection, (self.scheduler / subject.SELECTION_NAME).read_bytes())
        self.assertEqual(original_observer, (self.observer / 'state.json').read_bytes())
        self.assertEqual(original_generations, sorted(p.name for p in self.backups.iterdir()))

    def test_failed_verified_rotation_retains_selection_counts_partial_and_allows_observation(self):
        self.policy['max_backups'] = 2
        self.write_policy()
        self.run_action('init')
        original_selection = (self.scheduler / subject.SELECTION_NAME).read_bytes()
        original_observer = (self.observer / 'state.json').read_bytes()
        with patch.object(recovery_bundle, 'verify',
                side_effect=recovery_bundle.RecoveryRefusal('package_inventory')):
            with self.assertRaises(subject.ScheduleRefusal) as caught:
                self.run_action('backup', now=NOW + 1)
        self.assertEqual('backup_verification', caught.exception.code)
        self.assertEqual(2, len(list(self.backups.iterdir())))
        self.assertEqual(original_selection, (self.scheduler / subject.SELECTION_NAME).read_bytes())
        self.assertEqual(original_observer, (self.observer / 'state.json').read_bytes())
        with self.assertRaises(subject.ScheduleRefusal) as caught:
            self.run_action('backup', now=NOW + 2)
        self.assertEqual('capacity', caught.exception.code)
        self.assertEqual(2, len(list(self.backups.iterdir())))
        observed = self.run_action('observe', now=NOW + 3)
        self.assertIs(observed['observation']['observation']['backup_ok'], True)
        self.assertEqual(original_selection, (self.scheduler / subject.SELECTION_NAME).read_bytes())

    def test_selected_integrity_failure_is_reported_without_guessing_another_generation(self):
        self.run_action('init')
        self.run_action('backup', now=NOW + 1)
        selected_path = self.scheduler / subject.SELECTION_NAME
        selected = json.loads(selected_path.read_bytes())
        selected['manifest_sha256'] = '99' * 32
        selected_path.write_bytes((json.dumps(selected, sort_keys=True) + '\n').encode())
        selected_path.chmod(0o600)
        corrupted = selected_path.read_bytes()
        result = self.run_action('observe', now=NOW + 2)
        self.assertIs(result['observation']['observation']['backup_ok'], False)
        self.assertIn('backup_invalid', result['observation']['observation']['reason_codes'])
        self.assertEqual(corrupted, selected_path.read_bytes())
        self.assertEqual(2, len(list(self.backups.iterdir())))
        observer_before = (self.observer / 'state.json').read_bytes()
        selected['generation'] = '../outside'
        selected_path.write_bytes((json.dumps(selected, sort_keys=True) + '\n').encode())
        selected_path.chmod(0o600)
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('observe', now=NOW + 3)
        self.assertEqual(observer_before, (self.observer / 'state.json').read_bytes())

    def test_backup_and_observation_do_not_inherit_each_others_unrelated_storage_fault(self):
        self.run_action('init')
        committed = (self.observer / 'state.json').read_bytes()
        (self.observer / 'state.json').unlink()
        # Backup never edits observer state and must still capture the journal.
        self.run_action('backup', now=NOW + 1)
        self.assertFalse((self.observer / 'state.json').exists())
        (self.observer / 'state.json').write_bytes(committed)
        (self.observer / 'state.json').chmod(0o600)
        unrelated = self.backups / 'unreviewed-partial-folder'
        unrelated.mkdir(mode=0o700)
        # This cannot become a backup candidate or block checking the already
        # explicit selection. Subsequent backup refuses its bounded inventory.
        result = self.run_action('observe', now=NOW + 2)
        self.assertIs(result['observation']['observation']['backup_ok'], True)
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('backup', now=NOW + 3)
        self.assertTrue(unrelated.is_dir())

    def test_reviewed_rebind_changes_only_policy_pin_and_preserves_pending_outbox_and_old_capture(self):
        self.fixture.set_pending(now=NOW)
        self.run_action('init')
        self.fixture.unhealthy()
        self.run_action('observe', now=NOW + 5)
        original_observer = (self.observer / 'state.json').read_bytes()
        self.assertTrue(self.observer_state()['outbox'])
        self.assertIsNotNone(self.observer_state()['pending'])
        selected_path = self.scheduler / subject.SELECTION_NAME
        original_selection = json.loads(selected_path.read_bytes())
        previous = self.root / 'previous-reviewed-policy.json'
        previous.write_bytes(self.policy_path.read_bytes())
        previous.chmod(0o600)
        previous_pin = self.policy_pin
        self.policy.update(max_backups=9, max_backup_age_seconds=1800,
            pending_max_age_seconds=180, receiver='http://127.0.0.1:54321/alerts')
        self.write_policy()
        # No receiver is allowed by the fixture: rebind must never deliver.
        # The old backup is deliberately stale; rebind must not create one.
        rebound = self.run_action('rebind', now=NOW + 10000,
            previous_policy_path=previous, previous_policy_sha256=previous_pin)
        self.assertIs(rebound['policy_rebound'], True)
        self.assertEqual({**original_selection, 'policy_sha256': self.policy_pin},
            json.loads(selected_path.read_bytes()))
        self.assertEqual(original_observer, (self.observer / 'state.json').read_bytes())
        self.assertEqual(1, len(list(self.backups.iterdir())))
        self.assertEqual(NOW, rebound['created_at'])

    def test_rebind_requires_previous_proof_and_cannot_change_runtime_identity_or_paths(self):
        self.run_action('init')
        selected_path = self.scheduler / subject.SELECTION_NAME
        original_selection = selected_path.read_bytes()
        original_observer = (self.observer / 'state.json').read_bytes()
        previous = self.root / 'previous-reviewed-policy.json'
        previous.write_bytes(self.policy_path.read_bytes())
        previous.chmod(0o600)
        previous_pin = self.policy_pin
        self.policy['max_backups'] = 9
        self.write_policy()
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('rebind')
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('rebind', previous_policy_path=previous,
                previous_policy_sha256='99' * 32)
        self.policy['working_directory'] = str(self.root)
        self.write_policy()
        with self.assertRaises(subject.ScheduleRefusal):
            self.run_action('rebind', previous_policy_path=previous,
                previous_policy_sha256=previous_pin)
        self.assertEqual(original_selection, selected_path.read_bytes())
        self.assertEqual(original_observer, (self.observer / 'state.json').read_bytes())
        self.assertEqual(1, len(list(self.backups.iterdir())))
