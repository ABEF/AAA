"""Shared lineage codec seams; no old methods, provider or contract execution."""
import copy
from types import SimpleNamespace
import unittest

from frontend_api import earnings_checkpoint as common
from frontend_api import earnings_checkpoint_v2 as exact
from frontend_api.history import HistoryError, ZERO
from tests_python.test_earnings_checkpoint_v2_codec import populated
from tests_python.test_frontend_api import addr


def history_fixture():
    anchor = {'number': 20, 'hash': '0x'+'20'*32, 'timestamp': 200000}
    contracts = {role: SimpleNamespace(address=addr(n)) for role, n in
                 (('rewards', 5), ('royalties', 6))}
    projection = SimpleNamespace(contracts=contracts,
        history=SimpleNamespace(start=10, parent='0x'+'09'*32))
    engine = SimpleNamespace(p=projection, descriptors={ZERO: object(), addr(21): object()})
    history = dict(owners={101: addr(30)}, claims={(101, ZERO): (7, 3)},
        conversions={}, lp_conversions={}, provenance=dict(logs_examined=10, claim_events=2,
        royalty_conversion_events=0, lp_conversion_events=0, through_block=20,
        block_hash=anchor['hash'], from_block=10, start_parent_hash=projection.history.parent,
        minted_count=1, start_block_hash='0x'+'10'*32))
    return history, anchor, engine, [101]


class EarningsCheckpointEpochHelperTests(unittest.TestCase):
    def test_later_operating_epoch_preserves_raw_phase_without_mutating_source(self):
        model = populated().model
        old = exact.capture(model)
        model.lower = (10, '0x'+'11'*32, '0x'+'12'*32, '0x'+'13'*32)
        model.started = True
        raw = exact._capture_epoch(model)
        self.assertEqual(raw, old)
        self.assertTrue(any(phase != (0, 0) for tree in model.owner_trees.values()
                            for book in tree.carry for phase in book.values()))
        raw['owner_trees'][7]['outstanding'][0] += 1
        self.assertEqual(exact._capture_epoch(model), old)

    def test_epoch_capture_rejects_incomplete_or_nonoperating_models(self):
        model = populated().model
        invalid = [('started', False), ('frozen', True), ('retired', True),
                   ('track_all', False), ('fee_intake_version', 0),
                   ('pending_lp_transaction', 'unacknowledged')]
        invalid.extend((name, {1}) for name in exact.TRANSIENT_FIELDS)
        for name, value in invalid:
            candidate = copy.deepcopy(model)
            candidate.lower = (10, 'transaction', 'handoff', 'root')
            setattr(candidate, name, value)
            with self.subTest(field=name), self.assertRaises(HistoryError):
                exact._capture_epoch(candidate)

    def test_public_checkpoint2_capture_keeps_original_epoch_restriction(self):
        model = populated().model
        model.lower = (10, 'transaction', 'handoff', 'root')
        with self.assertRaisesRegex(HistoryError, 'complete original exact LP replay'):
            exact.capture(model)

    def test_shared_history_validation_accepts_exact_local_epoch(self):
        history, anchor, engine, mints = history_fixture()
        self.assertIsNone(common.validate_history_payload(history, anchor, engine, mints))
        history['lp_conversions'][101, addr(21)] = (3, 2, 1, dict(
            ledger=engine.p.contracts['rewards'].address, block_number=15,
            block_hash='0x'+'15'*32, timestamp=190000,
            transaction_hash='0x'+'30'*32, log_index=2))
        self.assertIsNone(common.validate_history_payload(history, anchor, engine, mints))

    def test_shared_history_validation_retains_local_identity_and_cutoff_guards(self):
        for mutation in ('owner', 'mint', 'claims', 'count', 'anchor', 'start', 'conversion'):
            history, anchor, engine, mints = history_fixture()
            if mutation == 'owner': history['owners'][101] = 'invalid'
            elif mutation == 'mint': history['owners'][102] = addr(31)
            elif mutation == 'claims': history['claims'][102, ZERO] = (1, 0)
            elif mutation == 'count': history['provenance']['claim_events'] = -1
            elif mutation == 'anchor': history['provenance']['block_hash'] = '0x'+'31'*32
            elif mutation == 'start': history['provenance']['from_block'] = 11
            else:
                history['lp_conversions'][101, addr(21)] = (3, 2, 1, dict(
                    ledger=engine.p.contracts['royalties'].address, block_number=15,
                    block_hash='0x'+'15'*32, timestamp=190000,
                    transaction_hash='0x'+'30'*32, log_index=2))
            with self.subTest(mutation=mutation), self.assertRaises((HistoryError, ValueError)):
                common.validate_history_payload(history, anchor, engine, mints)


if __name__ == '__main__':
    unittest.main()
