"""NEW exact sidecar-state recovery checks, prepared for isolated Ubuntu only.

Published scheduling/alert setup is helper composition, not old test execution.
The new APIs use real validators and files; no process, RPC or signer is allowed.
"""
import copy
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import unittest
from unittest.mock import patch

from keeper import recovery_bundle, sidecar_recovery as subject
from tests_python import test_keeper_scheduling as fixture_module
from zzz_ops.state import process_lock


NOW = fixture_module.NOW
CAPTURED = NOW + 2000  # Existing selected bundle is deliberately older than900s.


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


@unittest.skipUnless(os.name == 'posix', 'Requires POSIX sidecar locking and permissions')
class KeeperSidecarRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.seed = fixture_module.KeeperSchedulingTests(methodName='runTest')
        self.addCleanup(self.seed.doCleanups)
        self.seed.setUp()
        self.fixture = self.seed.fixture
        self.root = self.seed.root
        self.seed.run_action('init')
        # New observed intent legitimately postdates the selected journal copy.
        # Recovery must preserve both moments rather than forcing them equal.
        self.fixture.set_pending(now=NOW + 1)
        self.fixture.unhealthy()
        self.seed.run_action('observe', now=NOW + 5)
        self.selection_path = self.seed.scheduler / 'selected.json'
        self.alert_path = self.seed.observer / 'state.json'
        self.selection = json.loads(self.selection_path.read_bytes())
        self.alert = json.loads(self.alert_path.read_bytes())
        self.assertTrue(self.alert['outbox'])
        self.assertIsNotNone(self.alert['pending'])
        self.generation = self.seed.backups / self.selection['generation']
        self.bundle = self.root / 'sidecar-recovery-001'

    def guarded(self, function, *args, **kwargs):
        # Check every Python/open entry point, not just an expected reader path.
        protected = {self.fixture.key.absolute(), self.fixture.password.absolute()}
        original_path, original_os = Path.open, os.open
        import builtins
        original_builtin, original_io = builtins.open, io.open

        def secret(path):
            return isinstance(path, (str, bytes, os.PathLike)) and Path(os.fsdecode(path)).absolute() in protected

        def path_open(path, *a, **kw):
            self.assertFalse(secret(path), 'Sidecar recovery opened signer material')
            return original_path(path, *a, **kw)

        def os_open(path, *a, **kw):
            self.assertFalse(secret(path), 'Sidecar recovery opened signer material')
            return original_os(path, *a, **kw)

        def builtin_open(path, *a, **kw):
            self.assertFalse(secret(path), 'Sidecar recovery opened signer material')
            return original_builtin(path, *a, **kw)

        def io_open(path, *a, **kw):
            self.assertFalse(secret(path), 'Sidecar recovery opened signer material')
            return original_io(path, *a, **kw)

        with patch.object(Path, 'open', path_open), patch('os.open', os_open), \
                patch('builtins.open', builtin_open), patch('io.open', io_open):
            return function(*args, **kwargs)

    def capture(self, *, output=None, now=CAPTURED, **kwargs):
        return self.guarded(subject.backup, self.seed.policy_path, self.seed.policy_pin,
            self.bundle if output is None else output, now=now, **kwargs)

    def verify(self, pin, *, bundle=None, now=CAPTURED, **kwargs):
        options = {'max_age_seconds': 60, 'now': now}
        options.update(kwargs)
        return self.guarded(subject.verify, self.bundle if bundle is None else bundle,
            pin, self.seed.policy_path, self.seed.policy_pin, **options)

    def restore(self, pin, output, *, now=CAPTURED, **kwargs):
        options = {'max_age_seconds': 60, 'now': now}
        options.update(kwargs)
        return self.guarded(subject.restore, self.bundle, pin,
            self.seed.policy_path, self.seed.policy_pin, output, **options)

    def source_bytes(self):
        files = [self.seed.policy_path, self.fixture.config_path, self.fixture.journal,
            Path(self.fixture.config['health_path'])]
        for folder in (self.seed.scheduler, self.seed.observer, self.seed.backups):
            files += [path for path in folder.rglob('*') if path.is_file()]
        return {str(path.relative_to(self.root)): path.read_bytes() for path in files}

    def test_stale_selected_generation_roundtrip_preserves_all_bytes_and_pending_outbox(self):
        original = self.source_bytes()
        manifest, pin = self.capture()
        self.assertEqual(manifest, self.verify(pin, now=CAPTURED + 10))
        destination = self.root / 'fresh-review-restore'
        plan, plan_pin = self.restore(pin, destination, now=CAPTURED + 10)
        self.assertEqual(original, self.source_bytes())
        self.assertEqual(self.selection_path.read_bytes(), (destination / 'scheduler/selected.json').read_bytes())
        restored_alert = (destination / 'alerts/state.json').read_bytes()
        self.assertEqual(self.alert_path.read_bytes(), restored_alert)
        restored_value = json.loads(restored_alert)
        self.assertEqual(self.alert['sequence'], restored_value['sequence'])
        self.assertEqual(self.alert['pending'], restored_value['pending'])
        self.assertEqual(self.alert['outbox'], restored_value['outbox'])
        for name in ('manifest.json', 'journal.json'):
            self.assertEqual((self.generation / name).read_bytes(),
                (destination / 'backups' / self.selection['generation'] / name).read_bytes())
        self.assertEqual(NOW, json.loads((self.generation / 'manifest.json').read_bytes())['created_at'])
        self.assertIsNone(json.loads((self.generation / 'journal.json').read_bytes())['pending'])
        self.assertIsNotNone(json.loads(self.fixture.journal.read_bytes())['pending'])
        self.assertEqual(digest((destination / 'RESTORE_PLAN.json').read_bytes()), plan_pin)
        for result in (manifest, plan):
            self.assertIs(result['unsigned'], True)
            for key in ('readiness_approved', 'old_sidecars_fenced', 'canonical_state_verified',
                    'signer_material_included', 'policy_or_configuration_installed',
                    'services_restarted', 'runtime_paths_mapped',
                    'lock_ownership_restored', 'selected_generation_freshness_approved'):
                self.assertIs(result[key], False)
        for source, restored in ((self.seed.scheduler / 'schedule.lock', destination / 'scheduler/schedule.lock'),
                (self.seed.observer / 'alert.lock', destination / 'alerts/alert.lock')):
            self.assertEqual(b'', restored.read_bytes())
            self.assertNotEqual((source.stat().st_dev, source.stat().st_ino),
                (restored.stat().st_dev, restored.stat().st_ino))
            self.assertEqual(0o600, stat.S_IMODE(restored.stat().st_mode))
        for path in (*self.bundle.rglob('*'), *destination.rglob('*')):
            if path.is_file():
                for marker in self.fixture.secret_markers:
                    self.assertNotIn(marker.encode(), path.read_bytes())
        self.assertEqual(self.seed.policy_pin, self.selection['policy_sha256'])

    def test_schedule_and_alert_locks_refuse_contention_or_absence_without_recreation(self):
        original = self.source_bytes()
        for index, source_lock in enumerate((self.seed.scheduler / 'schedule.lock', self.seed.observer / 'alert.lock')):
            with self.subTest(lock=source_lock.name, state='held'):
                output = self.root / ('busy-' + str(index))
                with process_lock(source_lock):
                    with self.assertRaises(subject.SidecarRefusal):
                        self.capture(output=output)
                self.assertFalse(output.exists())
                self.assertEqual(original, self.source_bytes())
            with self.subTest(lock=source_lock.name, state='missing'):
                saved = self.root / ('preserved-lock-' + str(index))
                source_lock.rename(saved)
                try:
                    with self.assertRaises(subject.SidecarRefusal):
                        self.capture(output=self.root / ('missing-lock-' + str(index)))
                    self.assertFalse(source_lock.exists())
                    self.assertEqual(b'', saved.read_bytes())
                finally:
                    saved.rename(source_lock)
                self.assertEqual(original, self.source_bytes())
        # Failure acquiring the second lock must release the first one.
        with process_lock(self.seed.scheduler / 'schedule.lock'):
            pass
        import fcntl
        real_flock = fcntl.flock
        failed_descriptor = []

        def failed_unlock(descriptor, operation):
            if operation == fcntl.LOCK_UN and not failed_descriptor:
                failed_descriptor.append(descriptor)
                raise OSError(errno.EIO, 'injected-unlock-error')
            return real_flock(descriptor, operation)

        # A completed packet may remain unapproved after cleanup failure. The
        # actual descriptor must close even when explicit unlocking raises.
        with patch.object(fcntl, 'flock', failed_unlock):
            with self.assertRaises(subject.SidecarRefusal):
                self.capture(output=self.root / 'unapproved-unlock-error')
        self.assertEqual(1, len(failed_descriptor))
        with self.assertRaises(OSError) as closed:
            os.fstat(failed_descriptor[0])
        self.assertEqual(errno.EBADF, closed.exception.errno)
        with process_lock(self.seed.scheduler / 'schedule.lock'), process_lock(self.seed.observer / 'alert.lock'):
            pass
        self.assertEqual(original, self.source_bytes())

    def test_wrong_pins_tampered_payload_and_extra_package_entries_refuse_without_restore(self):
        _, pin = self.capture()
        original = self.source_bytes()
        with self.assertRaises(subject.SidecarRefusal):
            self.verify('44' * 32)
        for index, relative in enumerate(('selection.json', 'alert-state.json', 'selected/journal.json', 'manifest.json')):
            with self.subTest(payload=relative):
                path = self.bundle / relative
                saved = path.read_bytes()
                path.write_bytes(saved + b' ')
                target = self.root / ('bad-restore-' + str(index))
                try:
                    with self.assertRaises(subject.SidecarRefusal):
                        self.restore(pin, target)
                    self.assertFalse(target.exists())
                finally:
                    path.write_bytes(saved)
        extra = self.bundle / 'unexpected.json'
        extra.write_bytes(b'{}\n')
        extra.chmod(0o600)
        with self.assertRaises(subject.SidecarRefusal):
            self.verify(pin)
        self.assertEqual(original, self.source_bytes())

    def test_capture_bounds_and_output_separation_refuse_before_source_mutation(self):
        original = self.source_bytes()
        variants = [
            ('inside-scheduler', self.seed.scheduler / 'capture', {}),
            ('inside-observer', self.seed.observer / 'capture', {}),
            ('inside-generations', self.seed.backups / 'capture', {}),
            ('inside-journal-parent', self.fixture.runtime / 'capture', {}),
            ('tiny-total', self.root / 'too-small', {'max_bytes': 1}),
            ('bool-seconds', self.root / 'bad-clock-budget', {'max_seconds': True}),
        ]
        for name, output, options in variants:
            with self.subTest(case=name):
                with self.assertRaises(subject.SidecarRefusal):
                    self.capture(output=output, **options)
                self.assertFalse(output.exists())
                self.assertEqual(original, self.source_bytes())

    def test_unreviewed_policy_profile_or_source_identity_cannot_capture(self):
        original_policy = self.seed.policy_path.read_bytes()
        original = self.source_bytes()
        variants = [
            ('unsupported-schema', lambda policy: policy.update(schema=2)),
            ('configuration-pin', lambda policy: policy.update(configuration_sha256='11' * 32)),
            ('source-pin', lambda policy: policy['source_files_sha256'].update({'keeper/alerts.py': '22' * 32})),
        ]
        for index, (name, change) in enumerate(variants):
            with self.subTest(case=name):
                policy = copy.deepcopy(self.seed.policy)
                change(policy)
                self.seed.policy_path.write_bytes(encoded(policy))
                candidate_pin = digest(self.seed.policy_path.read_bytes())
                output = self.root / ('invalid-policy-' + str(index))
                try:
                    with self.assertRaises(subject.SidecarRefusal):
                        self.guarded(subject.backup, self.seed.policy_path, candidate_pin, output, now=CAPTURED)
                    self.assertFalse(output.exists())
                finally:
                    self.seed.policy_path.write_bytes(original_policy)
        self.assertEqual(original, self.source_bytes())

    def test_missing_or_partial_commits_never_initialize_or_publish_a_complete_capture(self):
        original = self.source_bytes()
        for index, source in enumerate((self.selection_path, self.alert_path, self.generation / 'manifest.json')):
            with self.subTest(missing=source.name):
                saved = self.root / ('saved-committed-' + str(index))
                source.rename(saved)
                output = self.root / ('missing-commit-' + str(index))
                try:
                    with self.assertRaises(subject.SidecarRefusal):
                        self.capture(output=output)
                    self.assertFalse(source.exists())
                    self.assertFalse(output.exists())
                finally:
                    saved.rename(source)
        residue = self.seed.observer / '.state.json.orphan.tmp'
        residue.write_bytes(b'unpublished-retain-for-review')
        residue.chmod(0o600)
        with self.assertRaises(subject.SidecarRefusal):
            self.capture()
        self.assertEqual(b'unpublished-retain-for-review', residue.read_bytes())
        self.assertFalse(self.bundle.exists())
        residue.unlink()  # Test-owned injection only; production never deletes it.
        self.assertEqual(original, self.source_bytes())

    def test_restore_is_exclusive_and_capture_age_never_refreshes_old_entitlements(self):
        _, pin = self.capture()
        original = self.source_bytes()
        existing = self.root / 'existing-review'
        existing.mkdir(mode=0o700)
        marker = existing / 'preserve-original.txt'
        marker.write_bytes(b'never-overwrite-this-review')
        marker.chmod(0o600)
        with self.assertRaises(subject.SidecarRefusal):
            self.restore(pin, existing)
        self.assertEqual(b'never-overwrite-this-review', marker.read_bytes())
        with self.assertRaises(subject.SidecarRefusal):
            self.restore(pin, self.root / 'expired-review', now=CAPTURED + 61)
        self.assertFalse((self.root / 'expired-review').exists())
        with self.assertRaises(subject.SidecarRefusal):
            self.verify(pin, minimum_created_at=CAPTURED + 1)
        self.assertEqual(original, self.source_bytes())

    def test_noncooperating_state_and_lock_changes_block_complete_capture_publication(self):
        original = self.source_bytes()
        original_alert = self.alert_path.read_bytes()
        real_read = recovery_bundle._read
        changed = []

        def concurrent_read(path, maximum, budget):
            raw = real_read(path, maximum, budget)
            if Path(path) == self.alert_path and not changed:
                # Deliberately simulate a same-UID writer ignoring advisory
                # locks. Whitespace keeps valid JSON but changes exact bytes.
                self.alert_path.write_bytes(raw + b' ')
                changed.append(True)
            return raw

        with patch.object(recovery_bundle, '_read', concurrent_read):
            with self.assertRaises(subject.SidecarRefusal) as caught:
                self.capture()
        self.assertTrue(changed)
        self.assertEqual('source_snapshot_changed', caught.exception.code)
        self.assertFalse((self.bundle / 'manifest.json').exists())
        self.assertEqual(original_alert + b' ', self.alert_path.read_bytes())
        after = self.source_bytes()
        key = str(self.alert_path.relative_to(self.root))
        self.assertEqual({k: v for k, v in original.items() if k != key},
            {k: v for k, v in after.items() if k != key})
        self.alert_path.write_bytes(original_alert)
        real_same = subject._same_capture
        source_lock = self.seed.scheduler / 'schedule.lock'
        original_inode = source_lock.stat().st_ino
        saved = self.root / 'preserved-replaced-schedule-lock'
        replaced = []
        destination = self.root / 'replacement-refused'

        def replaced_lock(*args, **kwargs):
            result = real_same(*args, **kwargs)
            if not replaced:
                source_lock.rename(saved)
                source_lock.write_bytes(b'')
                source_lock.chmod(0o600)
                replaced.append(True)
            return result

        try:
            with patch.object(subject, '_same_capture', replaced_lock):
                with self.assertRaises(subject.SidecarRefusal) as caught:
                    self.capture(output=destination)
            self.assertTrue(replaced)
            self.assertEqual('source_lock', caught.exception.code)
            self.assertFalse(destination.exists())
            self.assertEqual(original_inode, saved.stat().st_ino)
        finally:
            if replaced:
                source_lock.unlink()  # Remove only this test-created replacement.
                saved.rename(source_lock)
        self.assertEqual(original, self.source_bytes())

