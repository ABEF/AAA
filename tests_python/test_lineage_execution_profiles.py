"""Each explicitly pinned V10 peer retains its own execution-read capability."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.lineage import Lineage, Predecessor
from frontend_api.portfolio_v6 import verify_profile
from frontend_api.service import Projection, ProjectionError
from tests_python import test_seadrop_consumer as mint
from tests_python.test_frontend_api import addr, words
from zzz_ops.abi import decode_words


class LineageExecutionProfileTests(unittest.TestCase):
    def config(self, current, peer=None):
        fixture = mint.SeaDropAPI(self)
        config = mint.SeaDropConsumerTests._lineage_config(self, fixture, 2)
        config['execution_price_version'] = current
        if peer is not None:
            config['predecessors'][0]['execution_price_version'] = peer
        return fixture, config

    def test_omitted_predecessor_never_inherits_successor_execution_profile(self):
        fixture, config = self.config(1)
        projection = Projection(config, fixture.rpc, clock=lambda: 4000)
        peer = projection.lineage.entries[0].projection
        self.assertEqual(1, projection.execution_price_version)
        self.assertEqual(0, peer.execution_price_version)
        self.assertEqual(2, peer.mint_integration_version)
        self.assertEqual(7, peer.accounting_version)
        self.assertEqual(projection.contracts['seadrop'], peer.contracts['seadrop'])

    def test_each_explicit_zero_or_one_is_independent_of_successor(self):
        for current in (0, 1):
            for previous in (0, 1):
                with self.subTest(current=current, previous=previous):
                    fixture, config = self.config(current, previous)
                    projection = Projection(config, fixture.rpc, clock=lambda: 4000)
                    self.assertEqual(current, projection.execution_price_version)
                    self.assertEqual(previous, projection.lineage.entries[0].projection.execution_price_version)

    def test_invalid_predecessor_capability_is_not_coerced_or_inherited(self):
        for value in (True, False, '1', 1.0, 2, -1, None):
            with self.subTest(value=value):
                fixture, config = self.config(1)
                config['predecessors'][0]['execution_price_version'] = value
                before = len(fixture.rpc.calls)
                with self.assertRaises(ValueError): Projection(config, fixture.rpc, clock=lambda: 4000)
                self.assertEqual(before, len(fixture.rpc.calls))

    def test_each_peer_checks_its_own_routing_and_fixed_helper_not_the_successors(self):
        for previous in (0, 1):
            with self.subTest(previous=previous):
                fixture, config = self.config(1-previous, previous)
                projection = Projection(config, fixture.rpc, clock=lambda: 4000)
                peer = projection.lineage.entries[0].projection
                old = fixture.old.p
                inverse = {c.address: old.contracts[role].address for role, c in peer.contracts.items()
                    if role in old.contracts}
                forward = {value: key for key, value in inverse.items()}
                methods = []; routing = [3 if previous else 2]
                def read(target, method, *args, **kwargs):
                    methods.append(method)
                    if method == 'LP_ROUTING_VERSION()': return decode_words(words(routing[0]))
                    if method == 'EXECUTION_PRICE_VERSION()':
                        if not previous: self.fail('Historical peer must not require new execution capability')
                        return decode_words(words(1))
                    if method == 'executionStrategy()':
                        return decode_words(words(peer.contracts['lp_balance_math'].address))
                    result = old._call(inverse.get(target, target), method, *args, **kwargs)
                    # Only lower-case address getters in verify_profile are
                    # remapped; all numeric capability getters remain exact.
                    if method[0].islower() and len(result) == 1:
                        address = '0x'+result[0][-40:]
                        if address in forward: return decode_words(words(forward[address]))
                    return result
                peer._call = read
                verify_profile(peer, fixture.old.block(), accounting_version=7)
                self.assertEqual(previous == 1, 'EXECUTION_PRICE_VERSION()' in methods)
                routing[0] = 2 if previous else 3
                with self.assertRaises(ProjectionError):
                    verify_profile(peer, fixture.old.block(), accounting_version=7)

    def test_receipt_metadata_marks_only_explicit_one_without_changing_claim_totals(self):
        # Isolated serializer/replay composition, not an admission or receipt-
        # authentication test. Existing lineage tests cover the actual verifier.
        zero = '0x'+'0'*40; identifier = 7; state = '0x'+'a'*64; handoff = '0x'+'b'*64
        headers = {i: dict(number=i, hash='0x'+f'{i+1:064x}', timestamp=100+i) for i in (0, 1, 5, 10)}
        contracts = lambda start: {role: SimpleNamespace(address=addr(start+i), code_hash=state)
            for i, role in enumerate(('access', 'handoff'))}
        for previous in (0, 1):
            with self.subTest(previous=previous):
                source = SimpleNamespace(start=1, start_hash=headers[1]['hash'],
                    history=SimpleNamespace(start=1, parent=headers[0]['hash']), contracts=contracts(10),
                    mint_integration_version=2, execution_price_version=previous)
                current = SimpleNamespace(contracts=contracts(20))
                lifecycle = dict(origin=addr(99), predecessor_controller=source.contracts['access'].address)
                source._header = current._header = lambda n: headers[int(n, 16)]
                source._verify_deployment = lambda *_, **__: dict(state='retired', origin=addr(99),
                    predecessor_controller=None, successor_controller=current.contracts['access'].address)
                source._call = lambda target, method, **_: decode_words(words(handoff if method == 'handoffId()' else state))
                source._code = current._code = lambda *_: None
                source._admitted = lambda *_: ([zero], [zero])
                source._uint = lambda role, method, *_, **__: 1 if method == 'mintOrdinalOf(uint256)' else identifier
                history = SimpleNamespace(owners={identifier: addr(30)}, claims={(identifier, zero): (5, 2)},
                    conversions={}, lp_conversions={}, provenance=dict(minted_count=1, start_block_hash=headers[1]['hash']))
                source._history_snapshot = lambda *_: history
                local = SimpleNamespace(claims={(identifier, zero): (7, 0)}, conversions={}, lp_conversions={}, provenance={})
                lineage = object.__new__(Lineage)
                lineage.entries = [Predecessor(source, state)]
                lineage.descriptors = {zero: SimpleNamespace(symbol='ETH', decimals=18)}
                with patch.object(Lineage, '_receipt', return_value=(headers[5], (5, 0, 2), handoff, state)):
                    result = lineage.financial(current, headers[10], {}, lifecycle, local, identifier, 1)
                receipt = result['previously_claimed']['provenance']['predecessors'][0]
                self.assertEqual(previous == 1, 'execution_price_version' in receipt)
                if previous: self.assertEqual(1, receipt['execution_price_version'])
                self.assertEqual('12', result['previously_claimed']['assets'][0]['lp_raw'])
                self.assertEqual('2', result['previously_claimed']['assets'][0]['royalties_raw'])
