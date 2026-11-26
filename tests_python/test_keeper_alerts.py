"""NEW keeper-alert checks, prepared for one isolated Ubuntu execution.

Fixtures use published JSON vectors as data, real health/backup validators and
new temporary files. They never import old tests, construct Keeper, run Cast,
read operating journals or permit non-local network/process activity.
"""
import copy
import builtins
import datetime as dt
import errno
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import os
from pathlib import Path
import socket
from socketserver import TCPServer
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from keeper import alerts as subject
from keeper import recovery_bundle
from keeper.health import source_hashes
from keeper.ops import health_check


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'reports/ubuntu-backup-recovery-20261126/evidence/c814'
JOURNAL_VECTOR = ROOT / 'reports/ubuntu-daemon-storage-20261126/evidence/fetched/case-HASH_SAVE_FAULT_ARMED.json'
NOW = 1795705352


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


class LocalReceiver(HTTPServer):
    def server_bind(self):
        # Avoid HTTPServer's unrelated reverse-DNS discovery for a fixed listener.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = '127.0.0.1', self.server_address[1]


class KeeperAlertsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-new-alerts-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.work = self.root / 'working'; self.work.mkdir(mode=0o700)
        self.runtime = self.work / 'runtime'; self.runtime.mkdir(mode=0o700)
        self.key = self.work / 'keystore.secret'
        self.password = self.work / 'password.secret'
        self.secret_markers = ('NEW-ALERTS-DISPOSABLE-KEY-SENTINEL', 'NEW-ALERTS-DISPOSABLE-PASSWORD-SENTINEL',
                               'NEW-ALERTS-CREDENTIAL-MUST-NOT-LEAK')
        for path, marker in zip((self.key, self.password), self.secret_markers):
            path.write_text(marker, encoding='utf8'); path.chmod(0o600)
        snapshot = json.loads(JOURNAL_VECTOR.read_bytes())
        self.pending_vector = json.loads(snapshot['journal_raw_utf8'])
        self.state = copy.deepcopy(self.pending_vector)
        self.state.update(sender='0x' + '35' * 20, pending=None, next_nonce=0, receipt_anchor=None, spent={})
        self.journal = self.runtime / 'journal.json'
        self.config = {
            'chain_id': 4663, 'accounting_model': 'shared-pools-v2', 'sender': self.state['sender'],
            'contracts': copy.deepcopy(self.state['contracts']),
            'accounting_version': 7, 'custody_version': 5, 'fee_intake_version': 1,
            'royalty_settlement_version': 4, 'portfolio_version': 2, 'maintenance_policy_version': 3,
            'rebalance_confirmation_version': 3, 'execution_quality_version': 1,
            'protocol_policy_version': 1, 'lp_routing_version': 3, 'execution_price_version': 1,
            'rpc_urls': ['https://synthetic-user:' + self.secret_markers[2] + '@offline.invalid/private'],
            'state_path': str(self.journal), 'health_path': str(self.runtime / 'health.json'),
            'lock_path': str(self.runtime / 'keeper.lock'),
            'keystore': str(self.key), 'password_file': str(self.password),
            'reviewed_for_live_use': False, 'interval_seconds': 240, 'confirmations': 12,
            'max_gas_limit': 24000000, 'max_gas_price_wei': '5000000000',
            'max_transaction_cost_wei': '10000000000000000', 'max_daily_cost_wei': '50000000000000000',
            'l1_fee_allowance_wei': '0', 'receipt_fee_policy': 'included',
            'idle_compounding_budget': '0x596b344ab09a470bc468753e7bd3dc0a9fc5ebc1',
            'maintenance': {'compound': False, 'compound_idle': False, 'harvest': True,
                            'minimum_liquidity': 1, 'harvest_interval_seconds': 3600},
            'metadata_refresh': {'enabled': False}, 'royalty_conversion': {'enabled': False},
            'lp_conversion': {'enabled': False}, 'principal_distribution': {'enabled': False},
            'adaptive_range': {'enabled': False}, 'bucket_overrides': {}, 'buybacks': [],
        }
        self.health = copy.deepcopy(json.loads((PUBLIC / 'model-DRY.json').read_bytes())['health'])
        self.config['code_hashes'] = {name: '0x' + '11' * 32 for name in self.state['contracts']}
        for observation in self.observations():
            self.config['code_hashes'].update(observation['runtime_code_hashes'])
        self.config_path = self.root / 'keeper-config.json'
        self.write_state()
        self.write_config()
        self.make_health(live=True)
        self.alert_dir = self.root / 'alert-only'
        self.allowed_receiver_port = None
        original_connect = socket.socket.connect
        original_connection = socket.create_connection
        original_getaddrinfo = socket.getaddrinfo

        def permitted(address):
            return (isinstance(address, tuple) and len(address) >= 2 and address[0] == '127.0.0.1'
                    and self.allowed_receiver_port is not None and address[1] == self.allowed_receiver_port)

        def guarded_connect(sock, address):
            if not permitted(address):
                raise AssertionError('Alerts attempted a non-receiver connection')
            return original_connect(sock, address)

        def guarded_connection(address, *args, **kwargs):
            if not permitted(address):
                raise AssertionError('Alerts attempted a non-receiver connection')
            return original_connection(address, *args, **kwargs)

        def guarded_dns(host, port, *args, **kwargs):
            if not permitted((host, port)):
                raise AssertionError('Alerts attempted unrelated DNS')
            return original_getaddrinfo(host, port, *args, **kwargs)

        for target, replacement in (('socket.socket.connect', guarded_connect),
                                    ('socket.create_connection', guarded_connection),
                                    ('socket.getaddrinfo', guarded_dns)):
            guard = patch(target, replacement); guard.start(); self.addCleanup(guard.stop)
        process_guard = patch('subprocess.Popen', side_effect=AssertionError('Alerts attempted a subprocess'))
        process_guard.start(); self.addCleanup(process_guard.stop)
        self.bundle = self.root / 'backup-001'
        _, self.backup_pin = recovery_bundle.backup(self.config_path, self.bundle,
                                                    working_directory=self.work, now=NOW)

    def observations(self):
        return [self.health['lp_execution_health']['last_confirmed'],
                self.health['rebalance_confirmation_health']['policy']['last_observed']]

    def write_config(self):
        self.config_path.write_bytes((json.dumps(self.config, indent=3) + '\n').encode())
        self.config_path.chmod(0o600)

    def write_state(self):
        self.journal.write_bytes((json.dumps(self.state, indent=1) + '\n').encode())
        self.journal.chmod(0o600)

    def write_health(self):
        path = Path(self.config['health_path'])
        path.write_bytes((json.dumps(self.health, indent=1) + '\n').encode())
        path.chmod(0o600)

    def make_health(self, *, live=True, now=NOW):
        stamp = dt.datetime.fromtimestamp(now, dt.timezone.utc).isoformat()
        self.health.update(time=stamp, last_success_at=stamp, chain_id=self.config['chain_id'],
                           sender=self.config['sender'], status='healthy_v2' if live else 'dry_run_v2',
                           live=live, pending=False, pending_action=None, pending_day=None,
                           configuration_sha256=digest(self.config), strategy_paused=False,
                           canonical_state=0, preparation_active=False, consecutive_failures=0,
                           skipped_buckets=0, blocked_actions=0, confirmed_reverts=0,
                           active_revert_cooldowns=0, next_revert_retry_after=None)
        for observation in self.observations():
            observation.update(configuration_sha256=digest(self.config), source_files_sha256=source_hashes(),
                               block_timestamp=now - 2, observed_at_unix=now - 1)
        self.write_health()

    def once(self, **kwargs):
        options = dict(working_directory=self.work, backup_bundle=self.bundle,
                       backup_manifest_sha256=self.backup_pin, backup_config_path=self.config_path,
                       directory=self.alert_dir, max_health_age_seconds=600,
                       max_backup_age_seconds=900, pending_max_age_seconds=120, now=NOW)
        options.update(kwargs)
        original = (self.journal.read_bytes(), self.config_path.read_bytes())
        original_path_open, original_os_open = Path.open, os.open
        original_builtin_open, original_io_open = builtins.open, io.open

        def secret(path):
            return (isinstance(path, (str, bytes, os.PathLike)) and
                    Path(os.fsdecode(path)).absolute() in (self.key.absolute(), self.password.absolute()))

        def guarded_path(path, *args, **kw):
            if secret(path):
                raise AssertionError('Alerts read signer material')
            return original_path_open(path, *args, **kw)

        def guarded_os(path, *args, **kw):
            if secret(path):
                raise AssertionError('Alerts opened signer material')
            return original_os_open(path, *args, **kw)

        def guarded_builtin(path, *args, **kw):
            if secret(path):
                raise AssertionError('Alerts read signer material')
            return original_builtin_open(path, *args, **kw)

        def guarded_io(path, *args, **kw):
            if secret(path):
                raise AssertionError('Alerts read signer material')
            return original_io_open(path, *args, **kw)

        with patch.object(Path, 'open', guarded_path), patch('os.open', guarded_os), \
                patch('builtins.open', guarded_builtin), patch('io.open', guarded_io):
            result = subject.run_once(self.config_path, **options)
        self.assertEqual(original, (self.journal.read_bytes(), self.config_path.read_bytes()))
        self.assertNotIn(self.secret_markers[2], json.dumps(result))
        return result

    def receiver(self, mode='accept'):
        records = []
        server_owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.0'

            def log_message(self, *_args):
                pass

            def do_POST(self):
                size = int(self.headers['Content-Length'])
                server_owner.assertLessEqual(size, 16384)
                raw = self.rfile.read(size)
                body = json.loads(raw)
                records.append({'path': self.path, 'body': body, 'raw': raw})
                selected = server_owner.receiver_mode
                if selected == 'slow-headers':
                    end = time.monotonic() + 2.5
                    try:
                        self.connection.sendall(b'HTTP/1.0 200 OK\r\nX-Slow: ')
                        while time.monotonic() < end:
                            self.connection.sendall(b' ')
                            time.sleep(0.04)
                    except OSError:
                        pass
                    return
                if selected == 'drop':
                    self.connection.close(); return
                if selected == 'redirect':
                    self.send_response(307)
                    self.send_header('Location', '/redirected')
                    self.end_headers(); return
                reply = {'accepted': True,
                         'event_id': body.get('event_id') if selected == 'accept' else 'wrong-event'}
                payload = encoded(reply)
                self.send_response(200); self.send_header('Content-Length', str(len(payload)))
                self.end_headers(); self.wfile.write(payload)

        server = LocalReceiver(('127.0.0.1', 0), Handler)
        self.allowed_receiver_port = server.server_port
        self.receiver_mode = mode
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.02}, daemon=True)
        thread.start()

        def close():
            server.shutdown(); server.server_close(); thread.join(timeout=2)
            self.assertFalse(thread.is_alive())

        self.addCleanup(close)
        return 'http://127.0.0.1:' + str(server.server_port) + '/alerts', records

    def alert_state(self):
        return json.loads((self.alert_dir / 'state.json').read_bytes())

    def unhealthy(self):
        self.health['consecutive_failures'] = 1
        self.write_health()

    def set_pending(self, *, known=True, now=NOW):
        self.state['pending'] = copy.deepcopy(self.pending_vector['pending'])
        self.state['pending']['hash'] = '0x' + '29' * 32 if known else None
        self.write_state()
        self.make_health(now=now)
        self.health.update(status='awaiting_receipt', pending=True,
                           pending_action=self.state['pending']['key'], pending_day=self.state['pending']['day'])
        self.write_health()

    def test_real_current_health_and_backup_validators_compose_without_side_effects(self):
        self.assertTrue(health_check(self.config, now=NOW)['ok'])
        manifest = recovery_bundle.verify(self.bundle, self.backup_pin, self.config_path,
                                           max_age_seconds=900, now=NOW)
        self.assertFalse(manifest['live_ready'])
        result = self.once()
        self.assertTrue(result['observation']['health_ok'])
        self.assertTrue(result['observation']['backup_ok'])
        self.assertEqual(0, result['outbox_count'])
        self.assertEqual(0, result['active_incident_count'])
        self.assertTrue(result['unsigned'])
        self.assertFalse(result['readiness_approved'])

    def test_snapshot_adapter_has_identical_checks_without_rereading_health_file(self):
        original = health_check(self.config, now=NOW)
        path = Path(self.config['health_path']); raw = path.read_bytes(); path.unlink()
        try:
            self.assertEqual(original, health_check(self.config, now=NOW, snapshot=copy.deepcopy(self.health)))
            for value in (None, [], True, 'not-a-health-record'):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    health_check(self.config, now=NOW, snapshot=value)
            bad = copy.deepcopy(self.health); bad['configuration_sha256'] = '0' * 64
            self.assertFalse(health_check(self.config, now=NOW, snapshot=bad)['ok'])
        finally:
            path.write_bytes(raw); path.chmod(0o600)

    def test_dry_health_requires_explicit_alert_mode(self):
        self.make_health(live=False)
        self.assertFalse(health_check(self.config, now=NOW)['ok'])
        self.assertFalse(self.once()['observation']['health_ok'])
        other = self.root / 'dry-alert-only'
        result = self.once(directory=other, allow_dry_run=True)
        self.assertTrue(result['observation']['health_ok'])
        self.assertEqual(0, result['active_incident_count'])

    def test_known_pending_grace_tracks_first_observation_across_restarts(self):
        self.set_pending()
        first = self.once()
        self.assertEqual(0, first['active_incident_count'])
        checkpoint = self.alert_state()['pending']
        self.assertEqual(NOW, checkpoint['first_seen'])
        self.set_pending(now=NOW + 119)
        second = self.once(now=NOW + 119)
        self.assertEqual(0, second['active_incident_count'])
        self.assertEqual(checkpoint, self.alert_state()['pending'])
        self.set_pending(now=NOW + 121)
        expired = self.once(now=NOW + 121)
        self.assertGreater(expired['active_incident_count'], 0)
        self.assertGreaterEqual(expired['observation']['pending_observed_seconds'], 121)

    def test_hashless_pending_and_mismatched_health_never_receive_known_hash_grace(self):
        self.set_pending(known=False)
        ambiguous = self.once()
        self.assertGreater(ambiguous['active_incident_count'], 0)
        self.set_pending(known=True)
        self.health['pending_action'] = 'harvest:999'
        self.write_health()
        mismatch = self.once(directory=self.root / 'mismatch-alerts')
        self.assertGreater(mismatch['active_incident_count'], 0)
        for index, malformed in enumerate(('null_fee_review', 'execution_profile_drift')):
            self.set_pending(known=True)
            if malformed == 'null_fee_review':
                self.state['pending']['fee_review'] = None
            else:
                self.state['execution_price_version'] = 0
            self.write_state()
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    recovery_bundle.backup(self.config_path, self.root / ('refused-backup-' + str(index)),
                                           working_directory=self.work, now=NOW)
                result = self.once(directory=self.root / ('malformed-pending-' + str(index)))
                self.assertGreater(result['active_incident_count'], 0)
                self.assertNotEqual('pending_grace', result['observation']['classification'])

    def test_pending_grace_cannot_mask_wrong_configuration_or_source(self):
        self.set_pending()
        for index, alteration in enumerate(('configuration', 'source')):
            self.set_pending()
            if alteration == 'configuration':
                self.health['configuration_sha256'] = '0' * 64
            else:
                self.observations()[0]['source_files_sha256']['keeper/monitor.py'] = '0' * 64
            self.write_health()
            result = self.once(directory=self.root / ('pending-invalid-' + str(index)))
            self.assertGreater(result['active_incident_count'], 0)

    def test_health_and_backup_age_failures_are_independently_visible(self):
        stale_health = self.once(now=NOW + 601)
        self.assertFalse(stale_health['observation']['health_ok'])
        self.assertTrue(stale_health['observation']['backup_ok'])
        fresh_health = self.root / 'old-backup-alerts'
        result = self.once(directory=fresh_health, now=NOW + 61, max_backup_age_seconds=60)
        self.assertTrue(result['observation']['health_ok'])
        self.assertFalse(result['observation']['backup_ok'])
        self.unhealthy()
        (self.bundle / 'journal.json').write_bytes(b'{"corrupt":true}\n')
        both = self.once(directory=self.root / 'both-invalid-alerts')
        self.assertFalse(both['observation']['health_ok'])
        self.assertFalse(both['observation']['backup_ok'])

    def test_corrupt_health_is_sanitized_and_does_not_hide_backup_result(self):
        for index, raw in enumerate((b'{"pending":false,"pending":true}', b'not-json',
                                     ('{"time":"' + self.secret_markers[2] + '"}').encode())):
            Path(self.config['health_path']).write_bytes(raw)
            result = self.once(directory=self.root / ('bad-health-' + str(index)))
            self.assertFalse(result['observation']['health_ok'])
            self.assertTrue(result['observation']['backup_ok'])
            self.assertNotIn(self.secret_markers[2], json.dumps(result))
        health_path = Path(self.config['health_path'])
        health_path.unlink(); os.mkfifo(health_path, mode=0o600)
        try:
            started = time.monotonic()
            result = self.once(directory=self.root / 'fifo-health-alerts')
            self.assertLess(time.monotonic() - started, 2.0)
            self.assertFalse(result['observation']['health_ok'])
            self.assertTrue(result['observation']['backup_ok'])
        finally:
            health_path.unlink(); self.write_health()

    def test_incident_dedup_is_durable_across_repeated_one_shots(self):
        self.unhealthy()
        first = self.once(); queued = copy.deepcopy(self.alert_state()['outbox'])
        self.assertGreater(first['active_incident_count'], 0)
        second = self.once()
        self.assertEqual(queued, self.alert_state()['outbox'])
        self.assertEqual(first['outbox_count'], second['outbox_count'])
        self.assertEqual([], second['event_ids'])

    def test_real_local_receiver_acknowledges_incident_and_later_recovery(self):
        receiver, records = self.receiver()
        self.unhealthy()
        incident = self.once(receiver=receiver)
        self.assertTrue(incident['delivery']['acknowledged'])
        self.assertEqual(0, incident['outbox_count'])
        self.make_health()
        recovery = self.once(receiver=receiver)
        self.assertTrue(recovery['delivery']['acknowledged'])
        self.assertEqual(['incident', 'recovery'], [row['body']['type'] for row in records])
        self.assertEqual(0, recovery['active_incident_count'])
        for row in records:
            self.assertEqual('/alerts', row['path'])
            self.assertEqual({'schema', 'event_id', 'type', 'reason_code', 'sequence', 'observed_at',
                              'scope_sha256', 'unsigned', 'readiness_approved'}, set(row['body']))
            self.assertTrue(row['body']['unsigned'])
            self.assertFalse(row['body']['readiness_approved'])

    def test_wrong_ack_keeps_event_for_identical_retry(self):
        receiver, records = self.receiver('bad-ack')
        self.unhealthy()
        failed = self.once(receiver=receiver)
        self.assertFalse(failed['delivery']['acknowledged'])
        self.assertEqual(1, failed['outbox_count'])
        self.receiver_mode = 'accept'
        retried = self.once(receiver=receiver)
        self.assertTrue(retried['delivery']['acknowledged'])
        self.assertEqual(records[0]['raw'], records[1]['raw'])
        self.assertEqual(0, retried['outbox_count'])

    def test_dropped_ack_is_at_least_once_with_same_event_id(self):
        receiver, records = self.receiver('drop')
        self.unhealthy()
        result = self.once(receiver=receiver)
        self.assertFalse(result['delivery']['acknowledged'])
        self.assertEqual(1, result['outbox_count'])
        self.receiver_mode = 'accept'
        retried = self.once(receiver=receiver)
        self.assertTrue(retried['delivery']['acknowledged'])
        self.assertEqual(records[0]['body']['event_id'], records[1]['body']['event_id'])
        self.assertEqual(records[0]['raw'], records[1]['raw'])

    def test_redirect_is_not_followed_and_environment_proxies_are_ignored(self):
        receiver, records = self.receiver('redirect')
        self.unhealthy()
        proxy = 'http://DO-NOT-CONTACT.invalid:1/' + self.secret_markers[2]
        with patch.dict(os.environ, {'HTTP_PROXY': proxy, 'HTTPS_PROXY': proxy, 'ALL_PROXY': proxy,
                                    'http_proxy': proxy, 'https_proxy': proxy, 'all_proxy': proxy,
                                    'NO_PROXY': '', 'no_proxy': ''}):
            result = self.once(receiver=receiver)
            self.assertFalse(result['delivery']['acknowledged'])
            self.assertEqual(1, len(records))
            self.assertEqual('/alerts', records[0]['path'])
            self.receiver_mode = 'accept'
            self.assertTrue(self.once(receiver=receiver)['delivery']['acknowledged'])

    def test_backup_rotation_and_hash_publication_preserve_pending_age_and_outbox(self):
        self.set_pending(known=False)
        initial = self.once()
        old_events = copy.deepcopy(self.alert_state()['outbox'])
        first_seen = self.alert_state()['pending']['first_seen']
        self.assertGreater(initial['active_incident_count'], 0)
        self.set_pending(known=True, now=NOW + 30)
        rotated = self.root / 'backup-002'
        _, pin = recovery_bundle.backup(self.config_path, rotated, working_directory=self.work, now=NOW + 30)
        result = self.once(backup_bundle=rotated, backup_manifest_sha256=pin, now=NOW + 30)
        state = self.alert_state()
        self.assertEqual(first_seen, state['pending']['first_seen'])
        self.assertEqual(30, result['observation']['pending_observed_seconds'])
        self.assertTrue({event['event_id'] for event in old_events} <= {event['event_id'] for event in state['outbox']})
        self.assertNotIn('monitor_identity_changed', result['observation']['reason_codes'])

    def test_recovery_requires_fresh_health_and_a_verified_backup(self):
        receiver, records = self.receiver()
        self.unhealthy(); self.once(receiver=receiver)
        self.make_health()
        raw = (self.bundle / 'journal.json').read_bytes()
        (self.bundle / 'journal.json').write_bytes(b'{"tampered":true}\n')
        blocked = self.once(receiver=receiver)
        self.assertFalse(blocked['observation']['backup_ok'])
        self.assertNotIn('recovery', [row['body']['type'] for row in records])
        (self.bundle / 'journal.json').write_bytes(raw)
        recovered = self.once(receiver=receiver)
        self.assertTrue(recovered['observation']['health_ok'])
        self.assertTrue(recovered['observation']['backup_ok'])
        self.assertEqual(0, recovered['active_incident_count'])
        self.assertIn('recovery', [row['body']['type'] for row in records])

    def test_slow_trickle_headers_obey_absolute_delivery_budget(self):
        receiver, records = self.receiver('slow-headers')
        self.unhealthy()
        started = time.monotonic()
        result = self.once(receiver=receiver, max_seconds=1)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 2.0)
        self.assertFalse(result['delivery']['acknowledged'])
        self.assertEqual(1, result['outbox_count'])
        self.assertEqual(1, len(records))

    def test_failed_durable_publication_sends_nothing_and_keeps_original_outbox(self):
        self.once()
        state_path = self.alert_dir / 'state.json'
        original = state_path.read_bytes()
        receiver, records = self.receiver()
        self.unhealthy()
        with patch('keeper.alerts.os.fsync', side_effect=OSError(errno.EIO, self.secret_markers[2])):
            with self.assertRaises(subject.AlertRefusal) as failure:
                self.once(receiver=receiver)
        self.assertEqual('publication', failure.exception.code)
        self.assertEqual(original, state_path.read_bytes())
        self.assertEqual([], records)
        self.assertNotIn(self.secret_markers[2], str(failure.exception))

    def test_competing_sidecar_lock_refuses_without_mutating_state(self):
        import fcntl
        self.once()
        original = (self.alert_dir / 'state.json').read_bytes()
        with (self.alert_dir / 'alert.lock').open('a+b') as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                with self.assertRaises(subject.AlertRefusal) as failure:
                    self.once()
                self.assertEqual('sidecar_lock', failure.exception.code)
                self.assertEqual(original, (self.alert_dir / 'state.json').read_bytes())
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        self.assertTrue(self.once()['observation']['health_ok'])

    def test_unsafe_receiver_resource_bounds_and_input_aliases_fail_without_secret_echo(self):
        baseline = (self.journal.read_bytes(), self.config_path.read_bytes())
        bad_options = [
            {'receiver': 'https://127.0.0.1:1/alerts'},
            {'receiver': 'http://127.0.0.1:1/alerts?' + self.secret_markers[2]},
            {'receiver': 'http://synthetic:' + self.secret_markers[2] + '@127.0.0.1:1/alerts'},
            {'receiver': 'http://localhost:1/alerts'},
            {'max_seconds': True}, {'max_seconds': 0}, {'max_bytes': 0},
            {'max_health_age_seconds': 0}, {'pending_max_age_seconds': False},
            {'backup_manifest_sha256': 'not-a-pin-' + self.secret_markers[2]},
            {'directory': self.runtime}, {'directory': self.config_path},
        ]
        for options in bad_options:
            with self.subTest(options=list(options)), self.assertRaises(subject.AlertRefusal) as failure:
                self.once(**options)
            self.assertNotIn(self.secret_markers[2], str(failure.exception))
        self.assertEqual(baseline, (self.journal.read_bytes(), self.config_path.read_bytes()))
        bounded = self.once(directory=self.root / 'bounded-read-alerts', max_bytes=1)
        self.assertFalse(bounded['observation']['backup_ok'])
        self.assertIn('journal_unavailable', bounded['observation']['reason_codes'])
        receiver, records = self.receiver()
        self.unhealthy(); result = self.once(receiver=receiver)
        self.assertTrue(result['delivery']['acknowledged'])
        serialized = json.dumps(result) + (self.alert_dir / 'state.json').read_text()
        serialized += b''.join(row['raw'] for row in records).decode()
        for marker in self.secret_markers:
            self.assertNotIn(marker, serialized)
        self.assertNotIn('offline.invalid', serialized)
        self.assertNotIn(str(self.key), serialized)

    def test_configuration_race_preserves_outbox_and_cannot_emit_recovery(self):
        self.unhealthy(); self.once()
        old_events = copy.deepcopy(self.alert_state()['outbox'])
        self.make_health()
        original_config, original_journal = self.config_path.read_bytes(), self.journal.read_bytes()
        actual_check = subject.health_check

        def raced(config, **kwargs):
            result = actual_check(config, **kwargs)
            self.config_path.write_bytes(original_config + b'\n')
            return result

        try:
            with patch.object(subject, 'health_check', raced):
                result = subject.run_once(self.config_path, working_directory=self.work,
                    backup_bundle=self.bundle, backup_manifest_sha256=self.backup_pin,
                    backup_config_path=self.config_path, directory=self.alert_dir,
                    max_health_age_seconds=600, max_backup_age_seconds=900,
                    pending_max_age_seconds=120, now=NOW)
            self.assertIn('input_identity_invalid', result['observation']['reason_codes'])
            state = self.alert_state()
            self.assertTrue({event['event_id'] for event in old_events} <= {event['event_id'] for event in state['outbox']})
            self.assertNotIn('recovery', [event['type'] for event in state['outbox']])
            self.assertEqual(original_journal, self.journal.read_bytes())
        finally:
            self.config_path.write_bytes(original_config)
            self.config_path.chmod(0o600)

    def test_full_publicly_generated_outbox_drains_without_pruning_or_reset(self):
        # Every event is produced by actual observations, not a reconstructed
        # internal event/hash model. Alternating one fault and recovery fills
        # the reviewed capacity while delivery is deliberately disabled.
        for index in range(64):
            self.make_health()
            if index % 2 == 0:
                self.unhealthy()
            result = self.once()
            self.assertEqual(index + 1, result['outbox_count'])
        full = copy.deepcopy(self.alert_state())
        before_ids = [row['event_id'] for row in full['outbox']]
        receiver, records = self.receiver()
        self.unhealthy()
        progressed = self.once(receiver=receiver)
        delivered_ids = [row['body']['event_id'] for row in records]
        after = self.alert_state()
        self.assertGreater(len(delivered_ids), 0)
        self.assertLessEqual(len(delivered_ids), 8)
        self.assertEqual(before_ids[:len(delivered_ids)], delivered_ids)
        remaining_ids = [row['event_id'] for row in after['outbox']]
        self.assertTrue(set(before_ids) <= set(delivered_ids + remaining_ids))
        self.assertEqual(64 - len(delivered_ids) + 1, progressed['outbox_count'])
        self.assertGreater(progressed['active_incident_count'], 0)
        self.assertGreater(after['sequence'], full['sequence'])
        self.assertTrue(any(event_id not in before_ids for event_id in remaining_ids))

