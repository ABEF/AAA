"""New isolated collection-scale composition rehearsal, never a live indexer.

Only controlled dependency/getter observations reuse EpochFixture. Production
SQL, replay, checkpoint/import and recovery code remain real and unchanged.
No old unittest method is selected. This script writes a new owned directory.
Divisible LP credits give an independent per-NFT arithmetic oracle; exact raw
state/royalty remainder/claim and conversion preservation are checked separately.
Synthetic lifecycle/admission calls do not qualify actual provider work or gas.
"""
from collections import defaultdict
from contextlib import closing
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import socket
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from frontend_api import history_recovery as recovery
from frontend_api.earnings_checkpoint import decode
from frontend_api.earnings_checkpoint_build import BuildBudget, build, publish_candidate
from frontend_api.earnings_checkpoint_import import prepare, publish
from frontend_api.history import ZERO
from frontend_api.service import Projection
from tests_python.test_earnings_checkpoint_lineage import EpochFixture, digest
from tests_python.test_earnings_checkpoint_prefix_import import prefix_configuration
from tests_python.test_frontend_api import addr
from zzz_ops.abi import keccak256
from zzz_ops.errors import WorkLimit
from zzz_ops.work_budget import Budget, consume, request_scope

COUNT = 1000
ACTIVE = 900
HISTORY_EVENT_BOUND = 10000  # Explicit fixture setting; accepted production cap is 1,000,000.


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'))+'\n').encode()


class LiteralLedger:
    """Independent divisible arithmetic and literal rotating ticket recipients.

    No replay, Tree, split, ticket_amount or checkpoint codec computes expected
    earnings. Claims/conversions alter available balances, never earned totals.
    """
    def __init__(self, ids, pair, royalties, timestamp, snapshot):
        self.ids, self.pair, self.royalties = ids, pair, royalties
        self.timestamp, self.snapshot = timestamp, snapshot
        self.shares = {}; self.weights = {}; self.owners = {}
        self.lp = defaultdict(lambda: [0, 0]); self.royalty = defaultdict(int)
        self.earned = defaultdict(int); self.day = defaultdict(int)
        self.collection = defaultdict(int); self.collection_day = defaultdict(int)
        self.cursor = defaultdict(int); self.paid = defaultdict(lambda: [0, 0])
        self.converted = defaultdict(lambda: [0, 0]); self.actions = defaultdict(int)

    def income(self, identifier, metric, asset, amount, number):
        self.earned[identifier, metric, asset] += amount
        if self.timestamp(number) > self.timestamp(self.snapshot)-86400:
            self.day[identifier, metric, asset] += amount

    def total(self, metric, asset, amount, number):
        self.collection[metric, asset] += amount
        if self.timestamp(number) > self.timestamp(self.snapshot)-86400:
            self.collection_day[metric, asset] += amount

    def fees(self, asset, number):
        supply = sum(self.shares.values()); count = len(self.shares)
        units = supply*count
        for identifier, weight in self.shares.items():
            personal, shared = 16*count*weight, 2*supply
            self.lp[identifier, asset][0] += personal
            self.lp[identifier, asset][1] += shared
            self.income(identifier, 'lp_individual', asset, personal, number)
            self.income(identifier, 'lp_collective', asset, shared, number)
        for metric, amount in (('lp_processed', 20*units), ('lp_owner_allocated', 16*units),
                ('lp_collective_allocated', 2*units), ('lp_compounding_allocated', units),
                ('lp_buyback_allocated', units)):
            self.total(metric, asset, amount, number)
        self.actions['fee_receipts'] += 1
        return 16*units, 2*units, 20*units

    def royalties_credit(self, asset, amount, number):
        # Enumerate the finite rarity tickets directly. This is intentionally
        # distinct from production's interval arithmetic and gcd normalization.
        tickets = [identifier for identifier, weight in self.weights.items() for _ in range(weight)]
        before = self.cursor[asset]; base, remainder = divmod(amount, len(tickets))
        assigned = defaultdict(int)
        for identifier in tickets: assigned[identifier] += base
        for n in range(remainder): assigned[tickets[(before+n) % len(tickets)]] += 1
        for identifier, units in assigned.items():
            self.royalty[identifier, asset] += units
            self.income(identifier, 'royalties', asset, units, number)
        self.cursor[asset] = (before+amount) % len(tickets)
        self.total('royalties_allocated', asset, amount, number)
        self.actions['royalty_allocations'] += 1
        assert sum(assigned.values()) == amount
        return before, self.cursor[asset]


class ScaleFixture(EpochFixture):
    def emit(self, *args, index=None, **kwargs):
        # logIndex belongs to the entire canonical block, not one database.
        number = args[5] if len(args) > 5 else kwargs.get('number', 20)
        if index is None:
            index = sum(int(row['blockNumber'], 16) == number for epoch in self.rows for row in epoch)
        self._owner_cache = {}
        return super().emit(*args, index=index, **kwargs)

    def owners(self, epoch, through):
        # Synthetic getter observations are immutable after population. The
        # older three-NFT fixture rescans its whole log list for EACH getter;
        # caching this fixture-only truth avoids measuring that quadratic
        # harness cost as production/provider latency. Emission invalidates it.
        key = epoch, through
        if key not in self._owner_cache:
            self._owner_cache[key] = super().owners(epoch, through)
        return dict(self._owner_cache[key])

    def read_call(self, *args, **kwargs):
        # The old fixture replaces _call. Charge every substituted semantic
        # eth_call; actual fixture header/code/receipt reads already use
        # Projection's BudgetedRPC. No HTTP posts occur in this transport.
        consume('calls'); self.controlled_getters += 1
        return super().read_call(*args, **kwargs)

    def verify(self, p, block, allow_locked=False):
        result = super().verify(p, block, allow_locked)
        result['origin'] = dict(chain_id=p.chain, vault=self.configs[0]['contracts']['vault']['address'])
        return result

    def _populate(self):
        self.controlled_getters = 0
        self.ids = tuple(int.from_bytes(keccak256(('scale-nft-'+str(n)).encode()), 'big') for n in range(COUNT))
        for cfg in self.configs: cfg['history']['max_events'] = HISTORY_EVENT_BOUND
        self.literal = LiteralLedger(self.ids, self.pair, self.royalties, self.timestamp, self.safe)
        l = self.literal
        for asset in self.royalties:
            self.emit(0, 'royalties', 'AssetAdded(address,uint256)', (asset,), (0,), 10)
        end = self.timestamp(14)
        self.emit(0, 'royalties', 'MintEndConfigured(uint64,uint256)', (), (end, end+3600), 10)
        for n, identifier in enumerate(self.ids):
            owner = addr(900 if n < 800 else 901+n % 10)
            l.owners[identifier] = owner
            self.emit(0, 'nft', 'Transfer(address,address,uint256)', (ZERO, owner, identifier), (), 11)
        for n, identifier in enumerate(self.ids[:ACTIVE]):
            shares, weight = 100+n % 10, 1+n % 3
            l.shares[identifier] = shares; l.weights[identifier] = weight
            self.emit(0, 'rewards', 'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
                (identifier, 5), (n+1, 0, shares, sum(l.shares.values())), 13)
            self.emit(0, 'rewards', 'CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)',
                (identifier,), (n+1, 0, 1, n+1), 13)
            self.emit(0, 'membership', 'MembershipActivated(uint256)', (identifier,), (), 13)
            self.emit(0, 'royalties', 'Activated(uint256,uint256)', (identifier,), (weight,), 13)
            self.emit(0, 'vault', 'SharesAdded(uint256,uint256,uint256,uint256)',
                (identifier, 5), (shares, 100*10**18), 13)
        initial = sum(l.weights.values())*3+1
        for asset in self.royalties:
            self.emit(0, 'royalties', 'RoyaltiesReceived(address,uint256,bool)', (asset,), (initial, 0), 14)
            l.total('royalties_received', asset, initial, 14)
            l.total('royalties_quarantined', asset, initial, 14)
        self.emit(0, 'royalties', 'RoyaltyOpeningFinalized(uint256,uint256,uint256)',
            (), (end+3600, ACTIVE, sum(l.weights.values())), 20)
        for asset in self.royalties: self.literal_royalty(0, asset, initial, 20, initial=True)
        for asset in self.pair: self.literal_fees(0, asset, 22)
        # First indivisible owner unit follows an all-zero phase tree to its
        # rightmost active leaf900. Flushing that path before its weight grows
        # preserves nonzero high/low phase independently of divisible receipts.
        last_active = self.ids[ACTIVE-1]
        self.emit(0, 'fees', 'FeesAllocated(uint256,address,uint256,uint256)', (5, ZERO), (0, 1), 30)
        self.emit(0, 'rewards', 'PoolRewardsCredited(uint256,address,uint256,uint256)', (5, ZERO), (1, 0), 31)
        self.emit(0, 'fees', 'MembershipDustSettled(uint256,address,uint256)', (5, ZERO), (1,), 31)
        l.lp[last_active, ZERO][0] += 1
        l.income(last_active, 'lp_individual', ZERO, 1, 31)
        l.total('lp_processed', ZERO, 1, 30); l.total('lp_owner_allocated', ZERO, 1, 31)
        self.literal_grow(0, last_active, 1, 31)
        for identifier in self.ids[100:110]: self.literal_grow(0, identifier, 10, 41)
        for asset in self.pair: self.literal_fees(0, asset, 43)
        for asset in self.royalties: self.literal_royalty(0, asset, 1807, 44)
        for identifier in self.ids[:20]: self.literal_transfer(0, identifier, addr(950), 45)
        for identifier in self.ids[:16]: self.literal_convert(0, identifier, 46)
        for identifier in self.ids[:8]: self.literal_claim(0, identifier, ZERO, 47)
        for identifier in self.ids[:8]: self.literal_claim(0, identifier, self.royalties[1], 48, royalty=True)
        for asset in self.pair: self.literal_fees(0, asset, 70)
        for epoch, boundary in enumerate(self.edges):
            if epoch == 1:
                # safe299*1200 minus86400 is exactly block227. Receipts at
                #226/227 must be excluded;228 must enter the complete day.
                for number in (226, 227, 228):
                    for asset in self.pair: self.literal_fees(epoch, asset, number)
                    for asset in self.royalties: self.literal_royalty(epoch, asset, 1801, number)
            for asset in self.pair: self.literal_fees(epoch, asset, boundary-3)
            for asset in self.royalties: self.literal_royalty(epoch, asset, 1811, boundary-2)
            self.emit(epoch, 'handoff', 'Frozen(bytes32,address)',
                (self.handoff(epoch), self.configs[epoch+1]['contracts']['access']['address']), (), boundary-1)
            for asset in self.royalties:
                self.emit(epoch+1, 'royalties', 'AssetAdded(address,uint256)', (asset,), (0,), self.starts[epoch+1])
            for identifier, owner in l.owners.items():
                self.emit(epoch+1, 'nft', 'Transfer(address,address,uint256)', (ZERO, owner, identifier), (), boundary-1)
            activated = self.emit(epoch+1, 'handoff', 'Activated(bytes32,address,bytes32)',
                (self.handoff(epoch), self.configs[epoch]['contracts']['access']['address']),
                (self.state_root(epoch),), boundary, index=2000, transaction=self.transition_tx(epoch))
            retired = self.emit(epoch, 'handoff', 'Retired(bytes32,address,bytes32)',
                (self.handoff(epoch), self.configs[epoch+1]['contracts']['access']['address']),
                (self.state_root(epoch),), boundary, index=2001, transaction=self.transition_tx(epoch))
            self.receipts[self.transition_tx(epoch)] = dict(status='0x1', transactionHash=self.transition_tx(epoch),
                blockNumber=hex(boundary), blockHash=digest(boundary), transactionIndex='0x0', logs=[activated, retired])
            for asset in self.pair: self.literal_fees(epoch+1, asset, boundary+10)
            for identifier in self.ids[200:210]: self.literal_grow(epoch+1, identifier, 7, boundary+11)
            for asset in self.royalties: self.literal_royalty(epoch+1, asset, 1807, boundary+12)
            for identifier in self.ids[20:28]: self.literal_claim(epoch+1, identifier, self.pair[1], boundary+13)
            for identifier in self.ids[20:28]: self.literal_transfer(epoch+1, identifier, addr(951+epoch), boundary+14)
            for asset in self.pair: self.literal_fees(epoch+1, asset, boundary+15)
            for asset in self.royalties: self.literal_royalty(epoch+1, asset, 1801, boundary+16)

    def literal_fees(self, epoch, asset, number):
        personal, shared, gross = self.literal.fees(asset, number)
        self.emit(epoch, 'rewards', 'PoolRewardsCredited(uint256,address,uint256,uint256)', (5, asset), (personal, shared), number)
        self.emit(epoch, 'fees', 'FeesAllocated(uint256,address,uint256,uint256)', (5, asset), (gross, 0), number)

    def literal_royalty(self, epoch, asset, amount, number, initial=False):
        before, after = self.literal.royalties_credit(asset, amount, number)
        self.emit(epoch, 'royalties', 'RoyaltiesAllocated(address,uint256,uint256,uint256,uint256,uint256)',
            (asset,), (amount, ACTIVE, sum(self.literal.weights.values()), before, after), number)
        self.emit(epoch, 'royalties', 'InitialRoyaltiesAllocated(address,uint256,uint256,uint256)' if initial else
            'RoyaltiesReceived(address,uint256,bool)', (asset,),
            (amount, ACTIVE, sum(self.literal.weights.values())) if initial else (amount, 1), number)
        if not initial: self.literal.total('royalties_received', asset, amount, number)

    def literal_grow(self, epoch, identifier, amount, number):
        l = self.literal; previous = l.shares[identifier]; l.shares[identifier] += amount
        self.emit(epoch, 'rewards', 'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
            (identifier, 5), (self.ids.index(identifier)+1, previous, previous+amount, sum(l.shares.values())), number)
        self.emit(epoch, 'vault', 'SharesAdded(uint256,uint256,uint256,uint256)', (identifier, 5), (amount, 5*10**18), number)
        l.actions['growths'] += 1

    def literal_transfer(self, epoch, identifier, owner, number):
        previous = self.literal.owners[identifier]; self.literal.owners[identifier] = owner
        self.emit(epoch, 'nft', 'Transfer(address,address,uint256)', (previous, owner, identifier), (), number)
        self.literal.actions['transfers'] += 1

    def literal_convert(self, epoch, identifier, number):
        l = self.literal; source = l.lp[identifier, self.pair[1]][:]
        self.emit(epoch, 'rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
            (identifier, self.pair[1]), (*source, *source), number)
        l.lp[identifier, self.pair[1]] = [0, 0]
        for n in (0, 1): l.lp[identifier, ZERO][n] += source[n]
        l.converted[identifier, self.pair[1]][0] += sum(source)
        l.converted[identifier, self.pair[1]][1] += sum(source)
        l.actions['conversions'] += 1

    def literal_claim(self, epoch, identifier, asset, number, royalty=False):
        l = self.literal
        amount = l.royalty[identifier, asset] if royalty else sum(l.lp[identifier, asset])
        self.emit(epoch, 'royalties' if royalty else 'rewards', 'Claimed(uint256,address,address,uint256)',
            (identifier, asset, l.owners[identifier]), (amount,), number)
        if royalty: l.royalty[identifier, asset] = 0
        else: l.lp[identifier, asset] = [0, 0]
        l.paid[identifier, asset][int(royalty)] += amount
        l.actions['royalty_claims' if royalty else 'lp_claims'] += 1


def report_matches(report, literal, identifiers=None):
    collection = identifiers is None
    for period, expected in (('all_time', literal.collection if collection else literal.earned),
                             ('last_24h', literal.collection_day if collection else literal.day)):
        for row in report[period]:
            asset = row['asset']
            for field, raw in row.items():
                if not field.endswith('_raw'): continue
                metric = field[:-4]
                units = expected[metric, asset] if collection else sum(expected[i, metric, asset] for i in identifiers)
                assert int(raw) == units, (period, identifiers, asset, field, raw, units)
    assert report['window']['after_timestamp_exclusive'] == literal.timestamp(literal.snapshot)-86400
    assert report['claims_and_conversions_are_income'] is False


def histories(config):
    return [x['history'] for x in config.get('predecessors', [])]+[config['history']]


def materialize(folder):
    config = json.loads((folder/'profile.json').read_bytes())
    for history in histories(config): history['database'] = str(folder/history['database'])
    if config['earnings_history'].get('checkpoint'):
        item = config['earnings_history']['checkpoint']; item['path'] = str(folder/item['path'])
    return config


def table_digest(path):
    with closing(sqlite3.connect(Path(path).as_uri()+'?mode=ro', uri=True)) as db:
        rows = {t: db.execute('SELECT * FROM '+t+' ORDER BY rowid').fetchall() for t in ('cursors', 'blocks', 'logs')}
    return {t: dict(rows=len(values), sha256=sha(json_bytes(values))) for t, values in rows.items()}


def physical_source_hashes(paths):
    return {str(item): sha(item.read_bytes()) for path in paths
            for item in (Path(path), Path(str(path)+'-wal')) if item.exists()}


def run(output, *, prior_refusal=None, prior_refusal_sha256=None):
    output = output.absolute(); output.mkdir(exist_ok=False)
    result = dict(kind='isolated-1000-nft-history-recovery', production_approved=False,
        network_performed=False, existing_databases_used=False, stages=[], successful=False,
        fixture_scope='Synthetic dependency/getter/lifecycle observations; actual production SQL/replay/codecs/recovery.',
        limits=dict(history_max_events=HISTORY_EVENT_BOUND, http_seconds=25, http_calls=1024,
            http_posts=2048, offline_default_seconds=60, offline_default_calls=4096,
            offline_default_posts=8192, explicit_offline_calls=65536, explicit_offline_posts=65536,
            recovery_max_bytes=recovery.DEFAULT_BYTES))
    case = unittest.TestCase(); started = time.perf_counter()
    from tests_python import test_earnings_checkpoint_lineage as fixture_module
    class OwnedDirectory:
        counter = 0
        def __init__(self, *args, **kwargs):
            type(self).counter += 1
            self.name = str(output/('fixture-'+format(type(self).counter, '03d'))); Path(self.name).mkdir()
        def cleanup(self): pass  # Preserve this new rehearsal's evidence, not an existing directory.
    temporary = patch.object(fixture_module.tempfile, 'TemporaryDirectory', OwnedDirectory)
    temporary.start(); case.addCleanup(temporary.stop)
    def forbidden_network(*args, **kwargs): raise AssertionError('Network access is forbidden in this isolated rehearsal')
    network = patch.object(socket.socket, 'connect', forbidden_network)
    network.start(); case.addCleanup(network.stop)
    def stage(name, action, budget=None, expected_failure=None):
        begin = time.perf_counter()
        cpu = time.process_time()
        before = None if budget is None else (budget.calls, budget.posts)
        entry = dict(name=name, successful=False)
        try:
            value = action()
            assert expected_failure is None, 'Expected explicit existing-limit refusal'
            entry['successful'] = True
            return value
        except expected_failure or () as exc:
            assert exc.reason == 'rpc_budget' and budget.calls == 0, ('Unexpected existing-limit refusal', exc.reason)
            entry.update(successful=True, expected_refusal=type(exc).__name__, reason=str(exc))
            return None
        finally:
            entry['elapsed_seconds'] = time.perf_counter()-begin
            entry['process_cpu_seconds'] = time.process_time()-cpu
            if budget is not None:
                entry.update(calls_limit=before[0], posts_limit=before[1],
                    calls_consumed=before[0]-budget.calls, posts_consumed=before[1]-budget.posts,
                    calls_remaining=budget.calls, posts_remaining=budget.posts)
            result['stages'].append(entry)
            (output/'progress.json').write_bytes(json_bytes(result))
    def http_stage(name, action, validator=None):
        budget = Budget()
        def read():
            with request_scope(budget):
                value = action()
                if validator is not None: validator(value)
                return value
        return stage(name, read, budget)
    try:
        f = ScaleFixture(case, 3)
        # Only fixture allocation is redirected. Production importer's actual
        # TemporaryDirectory context manager remains the standard library one.
        temporary.stop()
        result.update(nft_count=len(f.ids), active_count=ACTIVE, dormant_count=COUNT-ACTIVE,
            epochs=len(f.configs), raw_logs=[len(rows) for rows in f.rows], actions=dict(f.literal.actions),
            full_history_seconds=f.timestamp(f.safe)-f.timestamp(f.starts[0]),
            rolling_day_includes_last_handoff=f.timestamp(f.edges[-1]) > f.timestamp(f.safe)-86400,
            exact_day_boundary_block=227, explicit_boundary_receipt_blocks=[226, 227, 228])
        original_paths = [h['database'] for h in histories(f.config)]
        original_rows = [table_digest(path) for path in original_paths]
        result['source_rows'] = original_rows
        physical_before = physical_source_hashes(original_paths)
        changes_before = [index.db.total_changes for index in f.indexes]
        def prefix(budget):
            with patch.object(f, 'safe', 120), patch.object(f, 'head', 131):
                return build(f.projection(prefix_configuration(f, 0)).earnings_history, 46, budget=budget)
        if prior_refusal is None:
            assert prior_refusal_sha256 is None
            default = BuildBudget()
            stage('default-4096-offline-checkpoint-refusal', lambda: prefix(default), default, WorkLimit)
        else:
            previous_raw = Path(prior_refusal).read_bytes()
            assert sha(previous_raw) == prior_refusal_sha256
            previous = json.loads(previous_raw)
            assert previous['kind'] == result['kind'] and previous['limits'] == result['limits']
            for key in ('nft_count', 'active_count', 'dormant_count', 'epochs', 'raw_logs', 'actions',
                        'full_history_seconds', 'exact_day_boundary_block', 'explicit_boundary_receipt_blocks'):
                assert previous[key] == result[key], ('Reused default refusal workload differs', key)
            for before, now in zip(previous['source_rows'], original_rows, strict=True):
                assert all(before[table] == now[table] for table in ('blocks', 'logs'))
            retained = [x for x in previous['stages'] if x['name'] == 'default-4096-offline-checkpoint-refusal']
            assert len(retained) == 1
            accepted = retained[0]
            assert accepted['successful'] is True and accepted['expected_refusal'] == 'WorkLimit'
            assert accepted['reason'] == 'Request work limit: rpc_budget'
            assert accepted['calls_limit'] == accepted['calls_consumed'] == 4096 and accepted['calls_remaining'] == 0
            result['reused_default_refusal'] = dict(source_result_sha256=prior_refusal_sha256, stage=accepted,
                scope='Exact same raw block/log workload and call-budget control; not a repeated run or timing qualification.')
        high = BuildBudget(calls=65536, posts=65536)
        raw_prefix = stage('explicit-existing-offline-prefix-build', lambda: prefix(high), high)
        exact_prefix = decode(json.loads(raw_prefix)['state'])['exact_lp']
        phases = [phase for tree in exact_prefix['owner_trees'].values() for book in tree['carry'] for phase in book.values()]
        assert any(high for high, low in phases) and any(low for high, low in phases)
        result['prefix_contains_nonzero_high_and_low_phase'] = True
        prefix_path = output/'original-prefix.json'; prefix_pin = publish_candidate(prefix_path, raw_prefix)
        high = BuildBudget(calls=65536, posts=65536)
        raw, review = stage('prefix-import-into-three-epoch-checkpoint3',
            lambda: prepare(f.projection().earnings_history, 161,
                dict(path=str(prefix_path), sha256=prefix_pin), budget=high), high)
        candidate, sidecar = output/'checkpoint.json', output/'import-review.json'
        stage('exclusive-checkpoint-and-review-publication', lambda: publish(candidate, sidecar, raw, review))
        f.config['earnings_history']['checkpoint'] = dict(path=str(candidate), sha256=sha(raw))
        result.update(prefix_bytes=len(raw_prefix), checkpoint_bytes=len(raw), review_bytes=len(review),
            checkpoint_anchor=json.loads(raw)['anchor'], checkpoint_sha256=sha(raw), prefix_sha256=prefix_pin)
        assert len(raw) <= 32*1024*1024
        # All1000 raw end balances are independently checked, separate from the
        # RPC fixture's use of this model to supply synthetic chain observations.
        def all_entitlements():
            model = f.model(2, f.safe)
            for identifier in f.ids:
                for asset in f.pair:
                    assert tuple(model.components(identifier, asset)) == tuple(f.literal.lp[identifier, asset])
                    for metric in ('lp_individual', 'lp_collective'):
                        assert model.account_totals[identifier][metric, asset] == f.literal.earned[identifier, metric, asset]
                    assert sum(f.literal.lp[identifier, asset]) == (
                        f.literal.earned[identifier, 'lp_individual', asset]+f.literal.earned[identifier, 'lp_collective', asset]
                        -f.literal.paid[identifier, asset][0]
                        -f.literal.converted[identifier, asset][0]
                        +(f.literal.converted[identifier, f.pair[1]][1] if asset == ZERO else 0))
                for asset in f.royalties:
                    assert model.account_totals[identifier]['royalties', asset] == f.literal.earned[identifier, 'royalties', asset]
                    assert f.literal.royalty[identifier, asset] == f.literal.earned[identifier, 'royalties', asset]-f.literal.paid[identifier, asset][1]
            return model
        stage('all-1000-exact-raw-entitlement-oracle', all_entitlements)
        result['all_1000_entitlements_match_independent_arithmetic'] = True
        def history_claims_and_conversions():
            from frontend_api.earnings_checkpoint_v3 import peers
            engine = f.projection().earnings_history
            claims = defaultdict(lambda: [0, 0]); conversions = defaultdict(lambda: [0, 0])
            for n, q in enumerate(peers(engine)):
                number = f.edges[n] if n < len(f.edges) else f.safe
                header = q._header(hex(number)); at = dict(blockHash=header['hash'], requireCanonical=True)
                lp, royalties = q._admitted(at)
                snap = engine.history_snapshot(q, header, at, lp, royalties)
                for key, amounts in snap.claims.items():
                    for kind in (0, 1): claims[key][kind] += amounts[kind]
                for key, amounts in snap.lp_conversions.items():
                    conversions[key][0] += amounts[0]; conversions[key][1] += amounts[1]
            for identifier in f.ids:
                for asset in set(f.pair+f.royalties):
                    assert claims[identifier, asset] == f.literal.paid[identifier, asset]
                    assert conversions[identifier, asset] == f.literal.converted[identifier, asset]
            return dict(nfts=COUNT, local_books=len(f.configs))
        http_stage('all-1000-local-claims-and-conversions-independent-oracle', history_claims_and_conversions)
        config_before = copy.deepcopy(f.config)
        review_arg = dict(path=str(sidecar), sha256=sha(review))
        bundle = output/'bundle'
        manifest, pin = stage('backup-all-retained-rows', lambda: recovery.backup(f.config, bundle, review=review_arg))
        assert config_before == f.config
        stage('verify-sealed-backup', lambda: recovery.verify(bundle, pin))
        restored = output/'restored'
        stage('restore-new-separate-files', lambda: recovery.restore(bundle, pin, restored))
        stage('verify-restored-package', lambda: recovery.verify(restored, pin))
        rebound = materialize(restored)
        copied = [table_digest(h['database']) for h in histories(rebound)]
        assert copied == original_rows == [table_digest(path) for path in original_paths]
        assert physical_before == physical_source_hashes(original_paths)
        assert changes_before == [index.db.total_changes for index in f.indexes]
        (output/'source-preservation.json').write_bytes(json_bytes(dict(
            before=physical_before, after=physical_source_hashes(original_paths),
            sql_changes_before=changes_before, sql_changes_after=[index.db.total_changes for index in f.indexes],
            checked_before_owned_writer_close=True)))
        assert (restored/'checkpoint.json').read_bytes() == raw
        assert (restored/'import-review.json').read_bytes() == review
        result.update(manifest_sha256=pin, payload_bytes=sum(x['bytes'] for x in manifest['files']),
            bundle_bytes=sum(p.stat().st_size for p in bundle.rglob('*') if p.is_file()),
            restored_bytes=sum(p.stat().st_size for p in restored.rglob('*') if p.is_file()),
            all_source_and_restored_rows_identical=True, checkpoint_and_review_bytes_identical=True)
        result['source_main_and_wal_hashes_unchanged'] = True
        reports = {}; wallets = sorted(set(f.literal.owners.values())); copy_coverage = {}
        for label, cfg in (('source', f.config), ('restored', rebound)):
            p = f.projection(cfg)
            covered = set()
            collection = http_stage(label+'-collection-default-http-budget', p.earnings,
                lambda response: report_matches(response, f.literal))
            reports[label] = dict(collection=collection, wallets=[], nfts=[])
            for wallet in wallets:
                offset = 0
                expected_ids = sorted(i for i, owner in f.literal.owners.items() if owner == wallet)
                while offset is not None:
                    def validate_wallet(response):
                        ids = tuple(map(int, response['token_ids']))
                        assert list(ids) == expected_ids[offset:offset+16]
                        assert not covered.intersection(ids)
                        assert response['count'] == len(expected_ids) and response['offset'] == offset
                        assert response['provenance']['block_number'] == f.safe
                        assert response['inventory_sha256'] == sha(','.join(map(str, expected_ids)).encode('ascii'))
                        assert response['next_offset'] == (offset+len(ids) if offset+len(ids) < len(expected_ids) else None)
                        report_matches(response, f.literal, ids)
                    response = http_stage(label+'-wallet-'+wallet[-4:]+'-'+str(offset),
                        lambda w=wallet, o=offset: p.wallet_earnings(w, f.safe, o), validate_wallet)
                    ids = tuple(map(int, response['token_ids']))
                    assert len(ids) <= 16
                    covered.update(ids); reports[label]['wallets'].append(response)
                    offset = response['next_offset']
            for identifier in (f.ids[0], f.ids[1], f.ids[899], f.ids[900], f.ids[999]):
                response = http_stage(label+'-nft-'+str(f.ids.index(identifier)), lambda i=identifier: p.earnings(str(i)),
                    lambda response, i=identifier: report_matches(response, f.literal, (i,)))
                reports[label]['nfts'].append(response)
            assert covered == set(f.ids)
            copy_coverage[label] = len(covered)
        def stable(report): return {k: report[k] for k in ('all_time', 'last_24h', 'window', 'event_count')}
        assert stable(reports['source']['collection']) == stable(reports['restored']['collection'])
        assert [stable(x) for x in reports['source']['wallets']] == [stable(x) for x in reports['restored']['wallets']]
        assert [stable(x) for x in reports['source']['nfts']] == [stable(x) for x in reports['restored']['nfts']]
        (output/'reports.json').write_bytes(json_bytes(reports))
        result.update(successful=True, wallets=len(wallets), wallet_chunks_per_copy=len(reports['source']['wallets']),
            wallet_coverage_nfts=copy_coverage, reports_sha256=sha((output/'reports.json').read_bytes()),
            controlled_getter_calls=f.controlled_getters, fixture_rpc_calls=len(f.calls),
            no_unchanged_tests_executed=True, source_configuration_sha256=sha(json_bytes(config_before)))
        return result
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        result.update(elapsed_seconds=time.perf_counter()-started)
        (output/'result.json').write_bytes(json_bytes(result)); case.doCleanups()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prior-refusal', type=Path,
                        help='Exact earlier result carrying this unchanged workload default-budget refusal.')
    parser.add_argument('--prior-refusal-sha256', help='Externally reviewed SHA-256 of that earlier result.')
    args = parser.parse_args()
    value = run(args.output, prior_refusal=args.prior_refusal, prior_refusal_sha256=args.prior_refusal_sha256)
    print(json.dumps({k: value[k] for k in ('successful', 'nft_count', 'epochs', 'elapsed_seconds')}))
