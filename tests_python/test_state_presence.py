"""Filesystem absence must not manufacture a fresh recovery/configuration state."""
import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops.state import read_json


class StatePresenceTests(unittest.TestCase):
    def test_dangling_entry_is_not_a_missing_journal(self):
        # Model the link entry independently from its missing target. This also
        # runs on hosts whose accounts cannot create symbolic links.
        path = Path('synthetic-dangling-journal.json')
        with patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'lstat', return_value=object()), \
                patch.object(Path, 'read_text', side_effect=FileNotFoundError) as read:
            with self.assertRaises(FileNotFoundError):
                read_json(path, {'pending': None, 'next_nonce': None})
            read.assert_called_once()

    def test_access_failure_is_not_absence(self):
        with patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'lstat', side_effect=PermissionError('denied')), \
                patch.object(Path, 'read_text') as read:
            with self.assertRaises(PermissionError):
                read_json('unreadable-parent/state.json', {'pending': None})
            read.assert_not_called()

    def test_filesystem_failure_is_not_absence(self):
        with patch.object(Path, 'exists', return_value=False), \
                patch.object(Path, 'lstat', side_effect=OSError(errno.EIO, 'io failure')), \
                patch.object(Path, 'read_text') as read:
            with self.assertRaises(OSError) as caught:
                read_json('failed-volume/state.json', {})
            self.assertEqual(caught.exception.errno, errno.EIO)
            read.assert_not_called()

    def test_present_file_disappearing_during_read_fails_closed(self):
        with patch.object(Path, 'exists', return_value=True), \
                patch.object(Path, 'lstat', return_value=object()), \
                patch.object(Path, 'read_text', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                read_json('state.json', {'pending': None})

    def test_true_absence_keeps_the_explicit_default_and_creates_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'new-journal.json'
            default = {'pending': None}
            self.assertIs(read_json(path, default), default)
            self.assertEqual(list(path.parent.iterdir()), [])

    def link(self, path, target):
        try:
            path.symlink_to(target)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Host account cannot create Windows symbolic links; portable entry/target regression runs separately')
            raise

    def test_actual_dangling_symlink_retains_its_entry_and_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'missing-target.json'
            path = Path(directory) / 'journal.json'
            self.link(path, target)
            with self.assertRaises(FileNotFoundError):
                read_json(path, {'pending': None})
            self.assertTrue(path.is_symlink())
            self.assertFalse(target.exists())

    def test_actual_readable_config_symlink_keeps_compatibility(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'config.json'
            target.write_text('{"reviewed":true}', encoding='utf-8')
            path = Path(directory) / 'linked-config.json'
            self.link(path, target)
            self.assertEqual(read_json(path, {}, encoding='utf-8'), {'reviewed': True})
            self.assertTrue(path.is_symlink())
            self.assertEqual(target.read_text(encoding='utf-8'), '{"reviewed":true}')
