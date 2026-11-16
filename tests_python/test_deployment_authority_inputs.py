"""Fresh planner authority admission: offline only, no compiler/RPC/deployment."""
from __future__ import annotations
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zzz_ops import deployment_plan as D


def reviewed_input():
    value = D.template()
    value['planned_addresses'] = {
        role: '0x' + f'{0x190000 + i:040x}'
        for i, (role, _name, _args) in enumerate(D.TOP)
    }
    value['inputs']['governance'] = '0x' + 'a1' * 20
    return value


class DeploymentAuthorityInputTests(unittest.TestCase):
    def test_every_other_planned_protocol_contract_is_not_governance(self):
        for role, _name, _args in D.TOP:
            if role == 'access':
                continue
            with self.subTest(role=role):
                value = reviewed_input()
                value['inputs']['governance'] = value['planned_addresses'][role]
                with self.assertRaisesRegex(D.PlanError, '^governance_is_protocol_address$'):
                    D.validate(value)

    def test_known_native_dependencies_and_seadrop_are_not_governance(self):
        for target in (*D.NATIVE.values(), D.SEADROP):
            with self.subTest(target=target):
                value = reviewed_input()
                value['inputs']['governance'] = target
                with self.assertRaisesRegex(D.PlanError, '^governance_is_external_dependency$'):
                    D.validate(value)

    def test_controller_collision_keeps_existing_diagnostic(self):
        value = reviewed_input()
        value['inputs']['governance'] = value['planned_addresses']['access']
        with self.assertRaisesRegex(D.PlanError, '^governance_is_controller$'):
            D.validate(value)

    def test_partial_plan_and_case_normalization_do_not_hide_collision(self):
        value = D.template()
        value['planned_addresses']['nft'] = '0x' + 'aB' * 20
        value['inputs']['governance'] = '0x' + 'Ab' * 20
        with self.assertRaisesRegex(D.PlanError, '^governance_is_protocol_address$'):
            D.validate(value)

    def test_shared_human_authority_and_unknown_wallet_remain_admissible(self):
        value = reviewed_input()
        wallet = value['inputs']['governance']
        value['inputs'].update(keeper=wallet, guardian=wallet, mint_recipient=wallet)
        result = D.validate(value)
        self.assertEqual(result['inputs']['governance'], wallet)
        self.assertEqual(result['inputs']['keeper'], wallet)
        self.assertEqual(result['inputs']['guardian'], wallet)
        # Offline input validation cannot prove this address is a usable EOA,
        # Safe or delegated account. Actual wallet qualification stays separate.
        self.assertEqual(D.validate(D.template()), D.template())

    def test_invalid_authority_refuses_before_build_or_output_publication(self):
        with tempfile.TemporaryDirectory(prefix='popl-authority-input-') as folder:
            root = Path(folder)
            source, output = root / 'input.json', root / 'never-created.json'
            value = reviewed_input()
            value['inputs']['governance'] = value['planned_addresses']['nft']
            source.write_text(json.dumps(value), encoding='utf-8')
            captured = io.StringIO()
            with patch.object(D, 'Artifacts', side_effect=AssertionError('Build must not be read')), \
                    contextlib.redirect_stderr(captured):
                code = D.main(['--input', str(source), '--output', str(output)])
            report = json.loads(captured.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(report['reason'], 'governance_is_protocol_address')
            self.assertEqual(report['stage'], 'offline_preparation')
            self.assertFalse(report['transaction_submitted'])
            self.assertFalse(report['output_may_exist'])
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
