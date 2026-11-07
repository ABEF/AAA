"""Checkpoint2 through source-wire replay and the real SQLite/API boundary.

The first scope keeps the original 77-log producer fixture and 26-word getter
witnesses. Its block/time embedding remains synthetic. The API scope deliberately
uses synthetic fresh7 RPC identities/views, never a relabelled deployed runtime.
Neither scope qualifies a provider, live deployment, workload or archive service.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from frontend_api.earnings_checkpoint import COLLECTION, SHARED, Seed, decode, encode
from frontend_api.earnings_checkpoint_build import build, publish_candidate, BuildBudget
from frontend_api.earnings_checkpoint_v2 import capture
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.earnings_replay import SCALE
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import Projection
from indexer.monitor import Indexer
from tests_python.test_earnings import native_put
from tests_python.test_earnings_checkpoints import MarketRPC, block_hash
from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python import test_exact_lp_source_wire as actual_wire
from tests_python.test_frontend_api import addr, words
from zzz_ops.abi import keccak256
from zzz_ops.errors import WorkLimit


def replay(rows, roles, pair, royalties, through=1118800):
    model = ExactReplay(through, track_all=True)
    model.begin(roles, pair, royalties, fee_intake_version=1, royalty_settlement_version=4)
    for row in rows:
        n = int(row['blockNumber'], 16)
        model(row['address'], row['topics'], row['data'], n, row['blockHash'],
              1000000+n*1200, row['transactionHash'], int(row['logIndex'], 16))
    model.finish()
    return model


class ActualCheckpoint2WireTests(unittest.TestCase):
    def test_original_growth_and_claim_suffix_preserves_raw_phase_and_literal_rights(self):
        self.assertEqual(hashlib.sha256(actual_wire.FIXTURE.read_bytes()).hexdigest(), actual_wire.FIXTURE_SHA256)
        original = actual_wire.model_for()
        roles = {role: emitter for emitter, role in original.roles.items()}
        pair = list(original.pair)
        whole = ExactReplay(104, track_all=True)
        whole.begin(roles, pair, [ZERO], fee_intake_version=1, royalty_settlement_version=4)
        raw = json.loads(actual_wire.FIXTURE.read_bytes())['raw_logs']
        first = actual_wire.frames()[0][1][0]
        for i, row in enumerate(raw[:raw.index(first)]):
            whole(row['address'], row['topics'], row['data'], 1, '0x'+f'{1:064x}',
                  99, '0x'+f'{9:064x}', i)
        for stage, rows, witness in actual_wire.frames()[:2]:
            actual_wire.apply(whole, stage, rows)
            self.assertEqual(actual_wire.actual_state(whole, witness), witness[12:26])
        payload = dict(shared={name: copy.deepcopy(getattr(whole, name)) for name in SHARED},
            accounts=copy.deepcopy(whole.accounts),
            collection={k: v for k, v in whole.totals.items() if k[0] in COLLECTION},
            emitters=roles, lp_assets=pair, royalty_assets=[ZERO], exact_lp=capture(whole))
        # Primitive Seed integration is distinct from full artifact admission
        # below; no fabricated deployment proof is attached to these actual logs.
        payload = decode(encode(payload))
        resumed = ExactReplay(104, track_all=True)
        resumed.begin(roles, pair, [ZERO], fee_intake_version=1, royalty_settlement_version=4)
        Seed('', {'number': 2, 'timestamp': 101}, {}, payload, None, 2).restore(resumed)
        self.assertEqual(capture(whole), capture(resumed))
        for stage, rows, witness in actual_wire.frames()[2:]:
            actual_wire.apply(whole, stage, rows)
            actual_wire.apply(resumed, stage, rows)
            self.assertEqual(actual_wire.actual_state(whole, witness), witness[12:26])
            self.assertEqual(actual_wire.actual_state(resumed, witness), witness[12:26])
            self.assertEqual(capture(whole), capture(resumed))
            self.assertEqual(whole.account_totals, resumed.account_totals)
        self.assertEqual(77, len(raw))
        self.assertEqual(18, whole.account_totals[witness[6]]['lp_individual', ZERO] +
                         whole.account_totals[witness[6]]['lp_collective', ZERO])
        self.assertEqual((0, 0), resumed.components(witness[6], ZERO))


class Checkpoint2APITests(unittest.TestCase):
    """Controlled fresh7 RPC plus actual builder, SQLite History and Earnings."""
    def setUp(self):
        fresh = Fresh7API(self)
        self.inner = fresh.rpc
        self.config = copy.deepcopy(fresh.config)
        self.c = dict(fresh.c)
        self.c.update(fees=addr(40), membership=addr(41))
        self.roles = {r: self.c[r] for r in ('nft', 'vault', 'rewards', 'royalties', 'handoff', 'fees', 'membership')}
        self.pair, self.royalties = [ZERO, addr(20)], [ZERO, addr(21)]
        self.i = self.inner.nft_id
        self.j = int.from_bytes(keccak256(b'checkpoint2 late activation'), 'big')
        self.k = int.from_bytes(keccak256(b'checkpoint2 dormant'), 'big')
        self.ids = (self.i, self.j, self.k)
        self.owners = {self.i: addr(30), self.j: addr(31), self.k: addr(31)}
        self.rpc = MarketRPC(self.inner, self.c['nft'])
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'raw.sqlite'
        contracts = sorted(self.roles.values())
        self.config['history'] = dict(database=str(self.path), start_block=10,
            start_parent_hash=block_hash(9), contracts=contracts, max_events=1000)
        extra = {}
        for role, label in (('fees', 'ZZZFeeController'), ('membership', 'ZZZMembership')):
            code = bytes([0x60, int(self.c[role], 16), 0])
            self.inner.codes[self.c[role]] = '0x'+code.hex()
            extra[role] = dict(address=self.c[role], code_hash='0x'+keccak256(code).hex())
            self.put(self.c[role], 'access()', values=(self.c['access'],))
            self.put(self.c['access'], 'module(bytes32)', ('0x'+keccak256(label.encode()).hex(),), (self.c[role],))
        self.config['earnings_history'] = dict(schema=1,
            deployments=[dict(controller=self.c['access'], **extra)], prices=None)
        self.put(self.c['fees'], 'FEE_INTAKE_VERSION()', values=(1,))
        cfg = dict(database=str(self.path), chain_id=31337, start_block=10,
            start_parent_hash=block_hash(9), contracts=contracts, rpc_urls=['http://127.0.0.1:1'])
        self.index = Indexer(cfg, self.rpc); self.addCleanup(self.index.db.close)
        with self.index.db:
            for n in range(10, 100):
                h = self.rpc.header(n)
                self.index.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                    (31337, n, h['hash'], h['parentHash'], int(h['timestamp'], 16)))
            self.index.db.execute('UPDATE cursors SET next_block=100')
        self.rows = []; self.indices = {}
        for asset in self.royalties:
            self.emit('royalties', 'AssetAdded(address,uint256)', (asset,), (0,), 10)
        end = 1000000+14*1200
        self.emit('royalties', 'MintEndConfigured(uint64,uint256)', (), (end, end+3600), 10)
        for identifier in self.ids:
            self.emit('nft', 'Transfer(address,address,uint256)', (ZERO, self.owners[identifier], identifier), (), 11)
        self.activate(self.i, 101, 1, 13)
        for asset in self.royalties:
            self.emit('royalties', 'RoyaltiesReceived(address,uint256,bool)', (asset,), (7, 0), 14)
        self.emit('royalties', 'RoyaltyOpeningFinalized(uint256,uint256,uint256)', (), (end+3600, 1, 1), 20)
        for asset in self.pair:
            self.fees(asset, 20)
        for asset in self.royalties:
            self.royalty(asset, 7, 20, initial=True)
        self.sync_views()
        self.now = 1118801

    def put(self, target, signature, args=(), values=(0,)):
        native_put(self.inner, target, signature, args, values)

    def emit(self, role, signature, indexed=(), data=(), block=20):
        log_index = self.indices.get(block, 0); self.indices[block] = log_index+1
        row = dict(address=self.roles[role], blockNumber=hex(block), blockHash=self.rpc.hash(block),
            transactionHash=block_hash(1000+block), logIndex=hex(log_index), removed=False,
            topics=['0x'+keccak256(signature.encode()).hex(), *[words(v) for v in indexed]], data=words(*data))
        self.rows.append(row)
        with self.index.db:
            self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                (31337, block, row['blockHash'], row['transactionHash'], log_index, row['address'], None, None, json.dumps(row)))
        return row

    def model(self):
        through = max([1118800, *[1000000+int(r['blockNumber'], 16)*1200 for r in self.rows]])
        return replay(self.rows, self.roles, self.pair, self.royalties, through)

    def activate(self, identifier, shares, weight, block):
        m = self.model(); ordinal = m.ordinals[identifier]
        self.emit('rewards', 'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
            (identifier, 5), (ordinal, 0, shares, m.supply[5]+shares), block)
        self.emit('rewards', 'CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)',
            (identifier,), (ordinal, 0, 1, len(m.members)+1), block)
        self.emit('membership', 'MembershipActivated(uint256)', (identifier,), (), block)
        self.emit('royalties', 'Activated(uint256,uint256)', (identifier,), (weight,), block)
        self.emit('vault', 'SharesAdded(uint256,uint256,uint256,uint256)', (identifier, 5), (shares, 100*10**18), block)

    def grow(self, identifier, shares, block):
        m = self.model(); bucket, old = m.shares[identifier]
        self.emit('rewards', 'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
            (identifier, bucket), (m.ordinals[identifier], old, old+shares, m.supply[bucket]+shares), block)
        self.emit('vault', 'SharesAdded(uint256,uint256,uint256,uint256)', (identifier, bucket), (shares, 5*10**18), block)

    def fees(self, asset, block, units=1):
        self.emit('rewards', 'PoolRewardsCredited(uint256,address,uint256,uint256)', (5, asset), (16*units, 2*units), block)
        self.emit('fees', 'FeesAllocated(uint256,address,uint256,uint256)', (5, asset), (20*units, 0), block)

    def royalty(self, asset, amount, block, initial=False):
        m = self.model(); supply = sum(m.weights[i] for i in m.cohorts[asset]); before = m.royalty_cursors[asset]
        # Cohorts in this fixture are weight1 initially, then weights1+3.
        after = (before+amount) % supply
        self.emit('royalties', 'RoyaltiesAllocated(address,uint256,uint256,uint256,uint256,uint256)',
            (asset,), (amount, len(m.cohorts[asset]), supply, before, after), block)
        if initial:
            self.emit('royalties', 'InitialRoyaltiesAllocated(address,uint256,uint256,uint256)',
                (asset,), (amount, len(m.cohorts[asset]), supply), block)
        else:
            self.emit('royalties', 'RoyaltiesReceived(address,uint256,bool)', (asset,), (amount, 1), block)

    def sync_views(self):
        m = self.model()
        self.put(self.c['nft'], 'mintedCount()', values=(len(m.mints),))
        self.put(self.c['membership'], 'totalEligible()', values=(len(m.members),))
        for sig, value in (('totalWeight()', sum(m.weights.values())), ('activationCount()', len(m.weights)),
                ('mintEnd()', m.royalty_mint_end), ('royaltiesOpenAt()', m.royalty_mint_end+3600), ('royaltiesOpen()', 1)):
            self.put(self.c['royalties'], sig, values=(value,))
        for bucket, tree in [(0, m.collective_tree), *m.owner_trees.items()]:
            self.put(self.c['rewards'], 'allocationTree(uint256)', (bucket,), (tree.total, *tree.outstanding))
        for bucket, supply in m.supply.items():
            self.put(self.c['vault'], 'bucketTotalShares(uint256)', (bucket,), (supply,))
        for asset in self.pair:
            n = self.pair.index(asset)
            liability = m.direct_liability(asset)+m.collective_tree.outstanding[n]+sum(t.outstanding[n] for t in m.owner_trees.values())
            for sig, value in (('directLiabilities(address)', m.direct_liability(asset)),
                    ('liabilities(address)', liability), ('orphaned(address)', m.lp_orphaned[asset])):
                self.put(self.c['rewards'], sig, (asset,), (value,))
            for bucket in m.supply:
                self.put(self.c['fees'], 'dust(uint256,address)', (bucket, asset), (m.fee_dust[bucket, asset],))
        for identifier in self.ids:
            bucket, shares = m.shares.get(identifier, (0, 0))
            for sig, args, value in (('ownerOf(uint256)', (identifier,), self.owners[identifier]),
                    ('mintOrdinalOf(uint256)', (identifier,), m.ordinals[identifier]),
                    ('tokenAtOrdinal(uint256)', (m.ordinals[identifier],), identifier)):
                self.put(self.c['nft'], sig, args, (value,))
            self.put(self.c['vault'], 'sharesOf(uint256)', (identifier,), (shares,))
            self.put(self.c['vault'], 'nftBucket(uint256)', (identifier,), (bucket,))
            self.put(self.c['rewards'], 'rewardBucket(uint256)', (identifier,), (bucket,))
            self.put(self.c['royalties'], 'weightOf(uint256)', (identifier,), (m.weights.get(identifier, 0),))
            self.put(self.c['royalties'], 'ticketStart(uint256)', (identifier,),
                (m.ticket_offsets[identifier]+1 if identifier in m.weights else 0,))
            for asset in self.pair:
                components = m.components(identifier, asset)
                self.put(self.c['rewards'], 'claimableComponents(uint256,address)', (identifier, asset), components)
                self.put(self.c['rewards'], 'claimable(uint256,address)', (identifier, asset), (sum(components),))
            for asset in self.royalties:
                paid = sum(int(r['data'], 16) for r in self.rows if r['address']==self.c['royalties'] and
                    r['topics'][0]=='0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex() and
                    int(r['topics'][1], 16)==identifier and '0x'+r['topics'][2][-40:]==asset)
                value = m.account_totals[identifier]['royalties', asset]-paid
                self.put(self.c['royalties'], 'claimable(uint256,address)', (identifier, asset), (value,))
        for owner in {*self.owners.values(), addr(30), addr(32)}:
            self.put(self.c['nft'], 'balanceOf(address)', (owner,),
                (sum(value==owner for value in self.owners.values()),))
        for asset in self.royalties:
            for sig, value in (('eligibleCount(address)', len(m.cohorts[asset])),
                    ('eligibleWeight(address)', sum(m.weights[i] for i in m.cohorts[asset])),
                    ('allocationCursor(address)', m.royalty_cursors[asset]), ('pending(address)', 0), ('openingPool(address)', 0)):
                self.put(self.c['royalties'], sig, (asset,), (value,))
        return m

    def projection(self, config=None):
        return Projection(self.config if config is None else config, self.rpc, clock=lambda:self.now)

    def candidate(self, block=21):
        return build(self.projection().earnings_history, block)

    def install(self, raw=None, name='checkpoint2.json'):
        path = Path(self.tmp.name)/name
        digest = publish_candidate(path, self.candidate() if raw is None else raw)
        self.config['earnings_history']['checkpoint'] = dict(path=str(path), sha256=digest)
        return path

    def suffix(self):
        self.emit('nft', 'Transfer(address,address,uint256)', (self.owners[self.i], addr(32), self.i), (), 40)
        self.owners[self.i] = addr(32)
        self.activate(self.j, 200, 3, 41); self.grow(self.i, 98, 42)
        for asset in self.pair:
            self.fees(asset, 43, 3)
        for asset in self.royalties:
            self.royalty(asset, 9, 44)
        m = self.model(); source = m.components(self.i, addr(20))
        self.emit('rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
            (self.i, addr(20)), (*source, *source), 45)
        self.emit('rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
            (self.k, addr(20)), (0, 0, 0, 0), 45)
        amount = sum(self.model().components(self.i, ZERO))
        self.emit('rewards', 'Claimed(uint256,address,address,uint256)', (self.i, ZERO, addr(32)), (amount,), 46)
        self.emit('rewards', 'Claimed(uint256,address,address,uint256)', (self.i, ZERO, addr(32)), (0,), 46)
        earned = self.model().account_totals[self.i]['royalties', ZERO]
        self.emit('royalties', 'Claimed(uint256,address,address,uint256)', (self.i, ZERO, addr(32)), (earned,), 46)
        self.sync_views()

    def full_config(self):
        cfg = copy.deepcopy(self.config); cfg['earnings_history'].pop('checkpoint', None)
        return cfg

    def test_funded_prefix_and_raw_suffix_match_full_collection_nft_wallet_and_dormant(self):
        path = self.install(); self.suffix()
        self.assertEqual(2, json.loads(path.read_bytes())['schema'])
        for identifier in (None, *map(str, self.ids)):
            with self.subTest(identifier=identifier):
                seeded = self.projection().earnings(identifier)
                full = self.projection(self.full_config()).earnings(identifier)
                for key in ('all_time', 'last_24h', 'window', 'event_count'):
                    self.assertEqual(full[key], seeded[key])
        result = self.projection().earnings(str(self.i))
        self.assertEqual(addr(32), result['owner'])
        rows = {r['asset']: r for r in result['all_time']}
        self.assertGreater(int(rows[ZERO]['lp_individual_raw']), 16)
        self.assertGreater(int(rows[addr(21)]['royalties_raw']), 7)
        for asset in self.royalties:
            self.assertEqual(10, self.model().account_totals[self.i]['royalties', asset])
            self.assertEqual(6, self.model().account_totals[self.j]['royalties', asset])
        self.assertEqual((0, 0), self.model().components(self.i, ZERO))
        dormant = self.projection().earnings(str(self.k))
        self.assertTrue(all(int(v)==0 for r in dormant['all_time'] for k, v in r.items() if k.endswith('_raw')))
        self.assertEqual(result['all_time'], self.projection().wallet_earnings(addr(32), 99)['all_time'])
        self.assertIsNone(result['all_time_usd_at_current_price_18']['lp_individual'])

    def test_conversions_claims_and_zero_rows_do_not_add_lifetime_income(self):
        self.install(); self.suffix(); model = self.model()
        result = self.projection().earnings(str(self.i))
        for asset in self.pair:
            self.assertEqual(72, model.totals['lp_owner_allocated', asset]+model.totals['lp_collective_allocated', asset])
        self.assertEqual(0, sum(model.components(self.i, addr(20))))
        history = self.projection().earnings_history.checkpoint.seed().history
        self.assertEqual({}, dict(history.lp_conversions))
        epochs = result['provenance']['epochs']
        # A zero batch row remains an observed event, never monetary income.
        self.assertEqual(2, epochs[0]['history']['lp_conversion_events'])
        self.assertEqual(3, epochs[0]['history']['claim_events'])
        seeded = self.projection().earnings_history
        header = self.rpc.header(99)
        snapshot = seeded.history_snapshot(seeded.p,
            dict(number=99, hash=header['hash'], timestamp=int(header['timestamp'], 16)),
            {'blockHash':header['hash'], 'requireCanonical':True}, self.pair, self.royalties)
        self.assertEqual((0, 0, 1), snapshot.lp_conversions[self.k, addr(20)][:3])

    def test_restart_concurrent_requests_and_seed_mutation_are_isolated(self):
        path = self.install(); self.suffix(); before = path.read_bytes(); p = self.projection()
        seed = p.earnings_history.checkpoint.seed()
        seed.payload['exact_lp']['owner_trees'][5]['pending'][0].clear()
        seed.payload['shared']['shares'].clear()
        first = p.earnings(str(self.i))
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(p.earnings, [str(self.i), str(self.j), str(self.k), str(self.i)]))
        self.assertEqual(first, results[0]); self.assertEqual(results[0], results[3])
        self.assertEqual(first, self.projection().earnings(str(self.i)))
        self.assertEqual(before, path.read_bytes())

    def test_bound_applies_to_actual_suffix_without_truncating_lifetime_or_day(self):
        self.install(); self.suffix(); suffix = sum(int(r['blockNumber'], 16)>21 for r in self.rows)
        self.config['history']['max_events'] = suffix
        self.assertTrue(self.projection().earnings(str(self.i))['available'])
        with self.assertRaisesRegex(HistoryError, 'bound exceeded'):
            self.projection(self.full_config()).earnings(str(self.i))
        self.config['history']['max_events'] = suffix-1
        with self.assertRaisesRegex(HistoryError, 'bound exceeded'):
            self.projection().earnings(str(self.i))

    def test_advanced_checkpoint_retains_claims_direct_credits_phase_and_new_day(self):
        first = self.install(); self.suffix()
        source = self.model().components(self.j, addr(20))
        self.assertGreater(sum(source), 0)
        self.emit('rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
            (self.j, addr(20)), (*source, *source), 47)
        self.sync_views()
        advanced = self.candidate(47); data = json.loads(advanced)
        self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), data['previous_sha256'])
        state = decode(data['state'])
        self.assertGreater(sum(state['exact_lp']['direct'][self.j, ZERO]), 0)
        phases = state['exact_lp']['owner_trees'][5]['carry']
        self.assertTrue(any(high or low for book in phases for high, low in book.values()))
        self.assertGreater(state['history']['claims'][self.i, ZERO][0], 0)
        self.assertEqual(3, len(state['history']['lp_conversions']))
        self.install(advanced, 'advanced.json')
        # Advance only the synthetic clock and indexed headers. No recorded
        # producer time is changed, and every new day event remains raw.
        with self.index.db:
            for n in range(100, 200):
                h = self.rpc.header(n)
                self.index.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                    (31337, n, h['hash'], h['parentHash'], int(h['timestamp'], 16)))
            self.index.db.execute('UPDATE cursors SET next_block=200')
        self.rpc.head = 210; self.now = 1238801
        for asset in self.pair:
            self.fees(asset, 130, 2)
        for asset in self.royalties:
            self.royalty(asset, 5, 131)
        self.sync_views()
        for identifier in (None, *map(str, self.ids)):
            seeded = self.projection().earnings(identifier)
            full = self.projection(self.full_config()).earnings(identifier)
            for key in ('all_time', 'last_24h', 'window', 'event_count'):
                self.assertEqual(full[key], seeded[key])

    def test_missing_acknowledgement_or_receipt_rejects_builder_before_publication(self):
        for signature in ('SharesAdded(uint256,uint256,uint256,uint256)',
                          'FeesAllocated(uint256,address,uint256,uint256)'):
            topic = '0x'+keccak256(signature.encode()).hex()
            row = next(r for r in self.rows if r['topics'][0]==topic)
            with self.index.db:
                self.index.db.execute('DELETE FROM logs WHERE transaction_hash=? AND log_index=?',
                    (row['transactionHash'], int(row['logIndex'], 16)))
            with self.subTest(signature=signature), self.assertRaises(HistoryError): self.candidate()
            with self.index.db:
                self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                    (31337, int(row['blockNumber'],16), row['blockHash'], row['transactionHash'],
                     int(row['logIndex'],16), row['address'], None, None, json.dumps(row)))
        self.assertEqual([], list(Path(self.tmp.name).glob('*.json')))

    def test_duplicate_prefix_transaction_and_missing_suffix_header_are_rejected(self):
        self.install()
        row = self.emit('nft', 'Transfer(address,address,uint256)',
            (addr(31), addr(33), self.k), (), 40)
        prefix = next(r for r in self.rows if int(r['blockNumber'], 16)==11)
        row = dict(row, transactionHash=prefix['transactionHash'], logIndex=hex(1000))
        with self.index.db:
            self.index.db.execute('DELETE FROM logs WHERE block_number=40')
            self.index.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                (31337, 40, row['blockHash'], row['transactionHash'], 1000, row['address'], None, None, json.dumps(row)))
        with self.assertRaisesRegex(HistoryError, 'prefix'): self.projection().earnings(str(self.i))
        with self.index.db:
            self.index.db.execute('DELETE FROM logs WHERE block_number=40')
            self.index.db.execute('DELETE FROM blocks WHERE number=42')
        with self.assertRaisesRegex(HistoryError, 'gaps'): self.projection().earnings(str(self.i))

    def test_checkpoint_inside_rolling_day_rejects_instead_of_hiding_earlier_income(self):
        self.install(self.candidate(28))
        with self.assertRaisesRegex(HistoryError, 'rolling day'):
            self.projection().earnings(str(self.i))

    def test_all_nft_builder_checks_components_even_when_global_roots_match(self):
        self.put(self.c['rewards'], 'claimableComponents(uint256,address)', (self.j, ZERO), (1, 0))
        with self.assertRaisesRegex(HistoryError, 'components differ'):
            self.candidate()
        self.sync_views()
        self.put(self.c['rewards'], 'rewardBucket(uint256)', (self.k,), (5,))
        with self.assertRaisesRegex(HistoryError, 'bucket differs'):
            self.candidate()

    def test_corrupt_exact_state_or_old_schema_is_rejected_even_with_new_file_pin(self):
        raw = self.candidate()
        def weight(s): s['exact_lp']['owner_trees'][5]['weights'][1] += 1
        def pending(s): s['exact_lp']['owner_trees'][5]['outstanding'][0] += 1
        def phase(s): s['exact_lp']['owner_trees'][5]['carry'][0][1] = (2**128, 0)
        def fraction(s): s['accounts'][self.i]['lp_individual', ZERO] += 1
        for n, mutate in enumerate((weight, pending, phase, fraction)):
            doc = json.loads(raw); state = decode(doc['state']); mutate(state); doc['state'] = encode(state)
            self.install((json.dumps(doc)+'\n').encode(), f'bad-{n}.json')
            with self.subTest(case=n), self.assertRaises(HistoryError): self.projection()
        doc = json.loads(raw); doc['schema'] = 1
        self.install((json.dumps(doc)+'\n').encode(), 'old.json')
        with self.assertRaisesRegex(HistoryError, 'Checkpoint2'): self.projection()

    def test_anchor_reorg_rpc_fault_and_foreign_identity_fail_closed(self):
        raw = self.candidate(); self.install(raw); self.rpc.reorg = 21
        with self.assertRaisesRegex(HistoryError, 'anchor'): self.projection().earnings(str(self.i))
        self.rpc.reorg = None; self.rpc.fail = True
        with self.assertRaises(HistoryError): self.projection().earnings(str(self.i))
        self.rpc.fail = False
        doc = json.loads(raw); bound = decode(doc['identity']); bound['chain'] = '0x1'; doc['identity'] = encode(bound)
        self.install((json.dumps(doc)+'\n').encode(), 'foreign.json')
        with self.assertRaisesRegex(HistoryError, 'identity changed'): self.projection()

    def test_truncation_source_drift_and_checkpoint_hash_mismatch_never_fall_back(self):
        path = self.install(); raw = path.read_bytes()
        path.write_bytes(raw[:-1])
        with self.assertRaisesRegex(HistoryError, 'bytes differ'): self.projection()
        path.write_bytes(raw)
        with patch('frontend_api.earnings_checkpoint.source_identity', return_value={}):
            with self.assertRaisesRegex(HistoryError, 'source changed'): self.projection()
        path.unlink()
        with self.assertRaises(HistoryError): self.projection()

    def test_exclusive_publication_failure_leaves_no_partial_or_replaced_candidate(self):
        raw = self.candidate(); target = Path(self.tmp.name)/'interrupted.json'
        with patch('frontend_api.earnings_checkpoint_build.os.link', side_effect=OSError('interrupted publication')):
            with self.assertRaisesRegex(OSError, 'interrupted'): publish_candidate(target, raw)
        self.assertFalse(target.exists()); self.assertEqual([], list(Path(self.tmp.name).glob('*.partial')))
        publish_candidate(target, raw)
        with self.assertRaises(FileExistsError): publish_candidate(target, raw+b' ')
        self.assertEqual(raw, target.read_bytes())

    def test_budget_exhaustion_and_anchor_drift_publish_no_candidate(self):
        with self.assertRaises(WorkLimit):
            build(self.projection().earnings_history, 21, budget=BuildBudget(calls=1))
        self.assertEqual([], list(Path(self.tmp.name).glob('*.json')))
        original = self.rpc.call; reads = []
        def change(method, params=None):
            if method=='eth_getBlockByNumber' and params[0]=='0x15':
                reads.append(1)
                if len(reads)>1: self.rpc.reorg = 21
            return original(method, params)
        with patch.object(self.rpc, 'call', side_effect=change):
            with self.assertRaisesRegex(HistoryError, 'anchor'): self.candidate()
        self.assertEqual([], list(Path(self.tmp.name).glob('*.json')))

    def test_reviewed_royalty_currency_append_preserves_exact_state_and_old_descriptors(self):
        path = self.install(); original = path.read_bytes(); self.suffix()
        asset = addr(60)
        self.config['assets'].append(dict(address=asset, symbol='ROY', decimals=18,
            code_hash='0x'+keccak256(b'checkpoint2 new royalty').hex()))
        self.inner.codes[asset] = '0x'+b'checkpoint2 new royalty'.hex()
        self.put(asset, 'decimals()', values=(18,))
        self.put(self.c['royalties'], 'assetCount()', values=(3,))
        self.put(self.c['royalties'], 'assets(uint256)', (2,), (asset,))
        self.royalties.append(asset)
        self.emit('royalties', 'AssetAdded(address,uint256)', (asset,), (0,), 50)
        self.royalty(asset, 13, 51)
        self.emit('royalties', 'Claimed(uint256,address,address,uint256)',
            (self.j, asset, self.owners[self.j]), (9,), 52)
        self.sync_views()
        for identifier in (None, *map(str, self.ids)):
            seeded = self.projection().earnings(identifier)
            full = self.projection(self.full_config()).earnings(identifier)
            for key in ('all_time', 'last_24h', 'window', 'event_count'):
                self.assertEqual(full[key], seeded[key])
        for identifier, expected in ((self.i, '4'), (self.j, '9'), (self.k, '0')):
            result = self.projection().earnings(str(identifier))
            for period in ('all_time', 'last_24h'):
                row = next(r for r in result[period] if r['asset']==asset)
                self.assertEqual(expected, row['royalties_raw'])
        self.assertEqual(original, path.read_bytes())
        self.assertNotIn(asset, decode(json.loads(original)['state'])['royalty_assets'])
        changed = copy.deepcopy(self.config)
        changed['assets'][0]['symbol'] = 'OTHERETH'
        with self.assertRaisesRegex(HistoryError, 'identity changed'):
            self.projection(changed)


if __name__ == '__main__':
    unittest.main()
