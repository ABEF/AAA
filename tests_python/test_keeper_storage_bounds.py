"""NEW publication-bound checks; no old test bodies, network or service calls.

Only private temporary files and the real atomic writer are used. Scheduler
identity guards are isolated so these checks run without POSIX ownership APIs;
the existing guard behavior is outside this focused encoding boundary.
"""
from contextlib import ExitStack
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper import scheduling, staging_observer


def persisted(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').replace(
        '\n', os.linesep).encode('ascii')


class KeeperStorageBoundsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='popl-new-publication-bounds-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def scheduler_value(self):
        return {'schema': 1, 'kind': 'popl-keeper-selected-backup',
            'policy_sha256': '11' * 32, 'configuration_sha256': '22' * 32,
            'generation': 'snapshot-' + '33' * 16, 'manifest_sha256': '44' * 32,
            'created_at': 1795790241,
            'identity': {'chain_id': 4663, 'sender': '0x' + '55' * 20,
                'contracts': {'vault': '0x' + '66' * 20}}}

    def publish_selection(self, value):
        context = {'directories': {'scheduler_directory': self.root}}
        with ExitStack() as guards:
            guards.enter_context(patch.object(scheduling, '_private_inventory', return_value=(1, 2)))
            guards.enter_context(patch.object(scheduling, '_private_directory', return_value=(1, 2)))
            guards.enter_context(patch.object(scheduling, '_stable'))
            guards.enter_context(patch.object(scheduling, '_selection', return_value=value))
            writer = guards.enter_context(patch.object(scheduling, 'atomic_json', wraps=scheduling.atomic_json))
            scheduling._publish(context, value)
            return writer.call_count

    def test_indented_selection_overflow_preserves_committed_files(self):
        target = self.root / scheduling.SELECTION_NAME
        original = persisted(self.scheduler_value())
        target.write_bytes(original)
        lock = self.root / scheduling.LOCK_NAME
        lock.write_bytes(b'')
        value = self.scheduler_value()
        value['identity']['contracts'].update({
            f'extra_{index:04d}': '0x' + '77' * 20 for index in range(1050)})
        compact = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
        self.assertLessEqual(len(compact), scheduling.MAX_SELECTION_BYTES)
        self.assertGreater(len(persisted(value)), scheduling.MAX_SELECTION_BYTES)
        with patch.object(scheduling, 'atomic_json', wraps=scheduling.atomic_json) as writer:
            with self.assertRaises(scheduling.ScheduleRefusal) as caught:
                self.publish_selection(value)
            writer.assert_not_called()
        self.assertEqual('resource_budget', caught.exception.code)
        self.assertEqual(original, target.read_bytes())
        self.assertEqual(b'', lock.read_bytes())
        self.assertEqual({scheduling.SELECTION_NAME, scheduling.LOCK_NAME},
            {path.name for path in self.root.iterdir()})

    def test_fitting_selection_keeps_atomic_writer_format(self):
        value = self.scheduler_value()
        expected = persisted(value)
        self.assertLessEqual(len(expected), scheduling.MAX_SELECTION_BYTES)
        self.assertEqual(1, self.publish_selection(value))
        self.assertEqual(expected, (self.root / scheduling.SELECTION_NAME).read_bytes())

    def test_indented_export_overflow_preserves_export_and_snapshot(self):
        target = self.root / 'status.json'
        original = b'{"original_export":true}\n'
        target.write_bytes(original)
        snapshot = self.root / 'observer-original.json'
        snapshot_raw = b'{"original_snapshot":true}\n'
        snapshot.write_bytes(snapshot_raw)
        report = {'staging_only': True, 'backup': {'snapshot': {'rows': ['abcd'] * 80000}}}
        compact = json.dumps(report, separators=(',', ':')).encode()
        self.assertLessEqual(len(compact), staging_observer.MAX_EXPORT_BYTES)
        self.assertGreater(len(persisted(report)), staging_observer.MAX_EXPORT_BYTES)
        with patch.object(staging_observer, 'EXPORT', target), \
                patch.object(staging_observer, 'atomic_json', wraps=staging_observer.atomic_json) as writer:
            with self.assertRaises(ValueError):
                staging_observer._publish_export(report)
            writer.assert_not_called()
        self.assertEqual(original, target.read_bytes())
        self.assertEqual(snapshot_raw, snapshot.read_bytes())
        self.assertEqual({'status.json', 'observer-original.json'},
            {path.name for path in self.root.iterdir()})

    def test_exact_export_limit_and_ascii_escaping_roundtrip_then_one_byte_refusal(self):
        target = self.root / 'status.json'
        report = {'staging_only': True, 'label': '\u00e9\U0001f680', 'padding': ''}
        report['padding'] = 'x' * (staging_observer.MAX_EXPORT_BYTES - len(persisted(report)))
        expected = persisted(report)
        self.assertEqual(staging_observer.MAX_EXPORT_BYTES, len(expected))
        self.assertIn(b'\\u00e9\\ud83d\\ude80', expected)
        with patch.object(staging_observer, 'EXPORT', target):
            staging_observer._publish_export(report)
            self.assertEqual(expected, target.read_bytes())
            oversized = copy.deepcopy(report)
            oversized['padding'] += 'x'
            with self.assertRaises(ValueError):
                staging_observer._publish_export(oversized)
        self.assertEqual(expected, target.read_bytes())
        self.assertEqual(report, json.loads(expected))


if __name__ == '__main__':
    unittest.main()
