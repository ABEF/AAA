"""NEW exact wallet aggregate checks; no historical TestCase bodies are selected.

The event fixture below is synthetic and has independent literal allocation
arithmetic. Original source-wire logs retain their separately labelled scope.
HTTP/provider/deployment qualification is not inferred from either fixture.
"""
import copy
from email.message import Message
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import time
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.earnings_checkpoint import SHARED, Seed, source_identity
from frontend_api.earnings_checkpoint_v2 import capture
from frontend_api.earnings_prices import value_report
from frontend_api.earnings import Earnings
from frontend_api.earnings_replay import COLLECTION, NFT, Replay
from frontend_api.history import HistoryError, ZERO
from frontend_api.service import Projection, ProjectionError
from tests_python import test_exact_lp_source_wire as source_wire
from zzz_ops.abi import keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope


def address(number):
    return '0x' + format(number, '040x')


ZZZ = address(20)
ALICE = address(9001)
BOB = address(9002)
ROLES = {name: address(100+n) for n, name in enumerate(
    ('nft', 'vault', 'rewards', 'fees', 'membership', 'royalties', 'handoff'))}
NOW = 90500
BOUNDARY = NOW - 86400


def word(value):
    return format(int(value, 16) if isinstance(value, str) else value, '064x')


def exact_books(model):
    return copy.deepcopy(dict(pair=model.pair, ordinals=model.ordinals,
        owner_trees={key:tree.__dict__ for key,tree in model.owner_trees.items()},
        collective_tree=model.collective_tree.__dict__, direct=dict(model.direct),
        orphaned=dict(model.lp_orphaned)))


class ExactEvents:
    """Deterministic current7/royalty4 events with independent whole-cycle sums."""
    def __init__(self, count, royalty_count=65, *, dormant_last=False,
                 timestamps=(BOUNDARY, BOUNDARY+1), unit_scale=1, royalty_assets=None):
        self.unit_scale = unit_scale
        self.ids = tuple((1 << 255) + (count-n)*19 + 3 for n in range(1, count+1))
        self.royalties = (tuple(royalty_assets) if royalty_assets is not None else
                          (ZERO,) + tuple(address(n) for n in range(21, 20+royalty_count)))
        self.assets = tuple(sorted({ZERO, ZZZ, *self.royalties}))
        self.weights = {identifier: ordinal % 3 + 1 for ordinal, identifier in enumerate(self.ids, 1)
                        if not (dormant_last and ordinal == count)}
        self.active = len(self.weights)
        self.supply = sum(self.weights.values())
        self.timestamps = timestamps
        self.rows = []
        self.counter = 0
        for asset in self.royalties:
            self.emit('royalties', 'AssetAdded(address,uint256)', (asset,), (0,), 0)
        self.emit('royalties', 'MintEndConfigured(uint64,uint256)', (), (100, 3700), 0)
        for identifier in self.ids:
            self.emit('nft', 'Transfer(address,address,uint256)', (ZERO, ALICE, identifier), (), 50)
        members = 0
        for ordinal, identifier in enumerate(self.ids, 1):
            if identifier not in self.weights:
                continue
            members += 1
            self.emit('rewards', 'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
                      (identifier, 5), (ordinal, 0, 1, members), 100)
            self.emit('rewards', 'CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)',
                      (identifier,), (ordinal, 0, 1, members), 100)
            self.emit('membership', 'MembershipActivated(uint256)', (identifier,), (), 100)
            self.emit('royalties', 'Activated(uint256,uint256)', (identifier,), (self.weights[identifier],), 100)
            self.emit('vault', 'SharesAdded(uint256,uint256,uint256,uint256)', (identifier, 5), (1, 100*10**18), 100)
        self.emit('royalties', 'RoyaltyOpeningFinalized(uint256,uint256,uint256)', (),
                  (3700, self.active, self.supply), 3700)
        for wave, timestamp in enumerate(timestamps):
            if not self.active:
                for asset in self.royalties:
                    if wave == 0:
                        self.emit('royalties', 'InitialRoyaltiesAllocated(address,uint256,uint256,uint256)',
                                  (asset,), (0, 0, 0), timestamp)
                continue
            for asset in (ZERO, ZZZ):
                tx = self.transaction()
                self.emit('rewards', 'PoolRewardsCredited(uint256,address,uint256,uint256)',
                          (5, asset), (16*self.active*unit_scale, 2*self.active*unit_scale), timestamp, transaction=tx)
                self.emit('fees', 'FeesAllocated(uint256,address,uint256,uint256)',
                          (5, asset), (20*self.active*unit_scale, 0), timestamp, transaction=tx)
            for index, asset in enumerate(self.royalties):
                amount = self.supply*(index+1)*unit_scale
                tx = self.transaction()
                self.emit('royalties', 'RoyaltiesAllocated(address,uint256,uint256,uint256,uint256,uint256)',
                          (asset,), (amount, self.active, self.supply, 0, 0), timestamp, transaction=tx)
                signature = ('InitialRoyaltiesAllocated(address,uint256,uint256,uint256)' if wave == 0 else
                             'RoyaltiesReceived(address,uint256,bool)')
                values = ((amount, self.active, self.supply) if wave == 0 else (amount, 1))
                self.emit('royalties', signature, (asset,), values, timestamp, transaction=tx)

    def transaction(self):
        self.counter += 1
        return '0x' + format(self.counter, '064x')

    def emit(self, role, signature, indexed, values, timestamp, *, transaction=None):
        if transaction is None:
            transaction = self.transaction()
        self.rows.append((ROLES[role], ['0x'+keccak256(signature.encode()).hex(),
                                     *['0x'+word(v) for v in indexed]],
                          '0x'+''.join(word(v) for v in values), timestamp, transaction))

    def replay(self, identifiers=None, assets=None):
        selected = tuple(sorted(self.ids if identifiers is None else identifiers))
        tracked = tuple(self.assets[:4] if assets is None else assets)
        model = ExactReplay(NOW, wallet_ids=selected, tracked_assets=tracked)
        model.begin(ROLES, [ZERO, ZZZ], self.royalties,
                    fee_intake_version=1, royalty_settlement_version=4)
        for index, (emitter, topics, data, timestamp, transaction) in enumerate(self.rows):
            model(emitter, topics, data, index+1, '0x'+format(index+1, '064x'),
                  timestamp, transaction, index)
        model.finish()
        return model

    def expected(self, identifiers, asset, metric, *, day=False):
        active = [i for i in identifiers if i in self.weights]
        waves = sum(BOUNDARY < ts <= NOW for ts in self.timestamps) if day else len(self.timestamps)
        if metric == 'royalties':
            return (sum(self.weights[i] for i in active)*(self.royalties.index(asset)+1)*waves*self.unit_scale
                    if asset in self.royalties else 0)
        return len(active)*waves*self.unit_scale*({'lp_individual': 16, 'lp_collective': 2}[metric]) if asset in (ZERO, ZZZ) else 0


@lru_cache(maxsize=128)
def selector(signature):
    return keccak256(signature.encode())[:4].hex()


def query(signature, *args):
    """Independent fixed-word test encoder; no production batch encoder used."""
    return '0x'+selector(signature)+''.join(word(v) for v in args)


class StaticBatchRPC:
    """Injected chain state and constructor result, not an EVM/provider proof.

    Every outer call is recorded and charged through the real BudgetedRPC.
    Constructor results are independently encoded from fixed scalar getter
    transcripts; normal callers still use the production parser/cache/proofs.
    """
    def __init__(self, events):
        from pathlib import Path
        artifact = json.loads((Path(__file__).resolve().parents[1]/
            'frontend_api/read_batch/WalletReadBatch.json').read_bytes())
        self.creation = bytes.fromhex(artifact['creation_bytecode'][2:])
        self.events = events
        self.values = {}
        self.failures = set()
        self.calls = []
        self.batch_sizes = []
        self.static_getters = 0
        self.chain = 31337
        self.header = {'number':99, 'hash':'0x'+'ab'*32, 'timestamp':NOW,
                       'parentHash':'0x'+'ac'*32}
        self.block = {'blockHash':self.header['hash'], 'requireCanonical':True}
        self.roles = dict(ROLES, access=address(250))
        self.codes = {target:'0x60'+format(index, '02x')+'00'
                      for index,target in enumerate(self.roles.values(), 1)}
        self.populate()

    def put(self, role, signature, args=(), values=(0,)):
        self.values[self.roles[role], query(signature,*args)] = '0x'+''.join(word(v) for v in values)

    def populate(self):
        events = self.events
        self.put('nft','balanceOf(address)',(ALICE,),(len(events.ids),))
        self.put('membership','totalEligible()',values=(events.active,))
        self.put('royalties','totalWeight()',values=(events.supply,))
        self.put('royalties','activationCount()',values=(events.active,))
        self.put('royalties','ROYALTY_SETTLEMENT_VERSION()',values=(4,))
        self.put('royalties','royaltiesOpen()',values=(1,))
        self.put('rewards','LP_ALLOCATION_VERSION()',values=(1,))
        self.put('fees','FEE_INTAKE_VERSION()',values=(1,))
        for role,label in (('fees','ZZZFeeController'),('membership','ZZZMembership')):
            self.put(role,'access()',values=(self.roles['access'],))
            self.put('access','module(bytes32)',('0x'+keccak256(label.encode()).hex(),),(self.roles[role],))
        waves = len(events.timestamps)
        self.put('vault','bucketTotalShares(uint256)',(5,),(events.active,))
        for bucket,amount in ((0,2),(5,16)):
            self.put('rewards','allocationTree(uint256)',(bucket,),
                     (events.active,amount*waves*events.active*events.unit_scale,amount*waves*events.active*events.unit_scale))
        for asset in (ZERO,ZZZ):
            for method,value in (('directLiabilities(address)',0),('liabilities(address)',18*waves*events.active*events.unit_scale),
                                 ('orphaned(address)',0)):
                self.put('rewards',method,(asset,),(value,))
            self.put('fees','dust(uint256,address)',(5,asset),(0,))
        for asset in events.royalties:
            for method,value in (('allocationCursor(address)',0),('eligibleCount(address)',events.active),
                                 ('eligibleWeight(address)',events.supply),('pending(address)',0),('openingPool(address)',0)):
                self.put('royalties',method,(asset,),(value,))
        for ordinal,identifier in enumerate(events.ids,1):
            active = identifier in events.weights
            self.put('nft','ownerOf(uint256)',(identifier,),(ALICE,))
            self.put('nft','mintOrdinalOf(uint256)',(identifier,),(ordinal,))
            self.put('nft','tokenAtOrdinal(uint256)',(ordinal,),(identifier,))
            self.put('vault','sharesOf(uint256)',(identifier,),(int(active),))
            self.put('vault','nftBucket(uint256)',(identifier,),(5 if active else 0,))
            self.put('rewards','rewardBucket(uint256)',(identifier,),(5 if active else 0,))
            self.put('royalties','weightOf(uint256)',(identifier,),(events.weights.get(identifier,0),))
            for asset in (ZERO,ZZZ):
                components=(16*waves*events.unit_scale,2*waves*events.unit_scale) if active else (0,0)
                self.put('rewards','claimableComponents(uint256,address)',(identifier,asset),components)
                self.put('rewards','claimable(uint256,address)',(identifier,asset),(sum(components),))
            for asset in events.royalties:
                self.put('royalties','claimable(uint256,address)',(identifier,asset),
                         (events.expected((identifier,),asset,'royalties'),))

    def scalar(self, target, data):
        key=target,data
        self.static_getters+=1
        if key in self.failures:
            raise RpcError('Controlled selected getter unavailable')
        if key not in self.values:
            raise AssertionError('Unspecified getter '+repr(key))
        return self.values[key]

    def constructor(self, tx):
        self_case = set(tx) == {'from','value','gas','data'}
        if not self_case or tx['from'] != ZERO or tx['value'] != '0x0' or tx['gas'] != hex(24_000_000):
            raise AssertionError('Unexpected constructor eth_call envelope')
        raw=bytes.fromhex(tx['data'][2:])
        if not raw.startswith(self.creation):
            raise AssertionError('Unexpected constructor program')
        arguments=raw[len(self.creation):]
        read=lambda offset:int.from_bytes(arguments[offset:offset+32],'big')
        modules=tuple(address(read(i*32)) for i in range(4))
        if modules != tuple(self.roles[r] for r in ('nft','vault','royalties','rewards')) or read(128) != 256:
            raise AssertionError('Unexpected constructor module/offset')
        pair=tuple(address(read(i*32)) for i in (5,6))
        count=read(256)
        ids=tuple(read(288+i*32) for i in range(count))
        royalty_offset=read(224)
        if not 1<=count<=3 or pair!=(ZERO,ZZZ) or royalty_offset!=288+count*32:
            raise AssertionError('Unexpected constructor selection')
        royalty_count=read(royalty_offset)
        royalties=tuple(address(read(royalty_offset+32+i*32)) for i in range(royalty_count))
        if royalty_count>4 or len(arguments)!=royalty_offset+32+royalty_count*32:
            raise AssertionError('Unexpected constructor currency tail')
        records=[]
        def take(role,signature,*args):
            try:
                value=self.scalar(self.roles[role],query(signature,*args))
            except RpcError:
                records.append((0,0,0));return None
            size=2 if signature.startswith('claimableComponents(') else 1
            if not isinstance(value,str) or len(value)!=2+64*size:
                records.append((2,0,0));return None
            words=[int(value[2+i*64:66+i*64],16) for i in range(size)]
            records.append((1,words[0],words[1] if size==2 else 0))
            return words[0]
        for identifier in ids:
            take('nft','ownerOf(uint256)',identifier)
            ordinal=take('nft','mintOrdinalOf(uint256)',identifier)
            if ordinal is not None:take('nft','tokenAtOrdinal(uint256)',ordinal)
            else:records.append((0,0,0))
            for role,signature in (('vault','sharesOf(uint256)'),('vault','nftBucket(uint256)'),
                                   ('royalties','weightOf(uint256)'),('rewards','rewardBucket(uint256)')):
                take(role,signature,identifier)
            for asset in pair:take('rewards','claimableComponents(uint256,address)',identifier,asset)
            for asset in pair:take('rewards','claimable(uint256,address)',identifier,asset)
            for asset in royalties:take('royalties','claimable(uint256,address)',identifier,asset)
        self.batch_sizes.append(count)
        header=keccak256(b'POPL_WALLET_STATIC_READ_BATCH_V1')+bytes.fromhex(word(self.chain))+keccak256(arguments)+bytes.fromhex(word(len(records)))
        return '0x'+(header+b''.join(bytes.fromhex(''.join(word(v) for v in row)) for row in records)).hex()

    def call(self, method, params=None):
        self.calls.append((method,copy.deepcopy(params)))
        if method=='eth_call':
            if params[1]!=self.block:raise AssertionError('Noncanonical aggregate call')
            return self.constructor(params[0]) if 'to' not in params[0] else self.scalar(params[0]['to'],params[0]['data'])
        if method=='eth_getCode':
            if params[1]!=self.block:raise AssertionError('Noncanonical aggregate code')
            return self.codes[params[0]]
        if method=='eth_getBlockByNumber':
            if params!=['0x63',False]:raise AssertionError('Unexpected aggregate header')
            return copy.deepcopy(self.header)
        raise AssertionError('Unexpected or state-changing RPC '+method)


class AggregateComposition:
    """Real aggregator/Replay/Earnings/read-batch/cache with explicit truth seams."""
    def __init__(self, count=17, *, royalty_count=65, unit_scale=1, events=None):
        self.events=events if events is not None else ExactEvents(count,royalty_count,dormant_last=True,unit_scale=unit_scale)
        self.transport=StaticBatchRPC(self.events)
        self.p=object.__new__(Projection)
        p=self.p
        p.accounting_version=7;p.wallet_read_batch=1;p.chain=self.transport.chain;p.start=1
        p.fee_intake_version=1;p.royalty_reporting=SimpleNamespace(schema=5)
        p.rpc=BudgetedRPC(self.transport);p.lineage=None;p.confirmations=12;p.max_age=120
        p.identity='e'*64;p.clock=lambda:NOW+1
        p.contracts={role:SimpleNamespace(address=target,code_hash='0x'+keccak256(bytes.fromhex(self.transport.codes[target][2:])).hex())
                     for role,target in self.transport.roles.items()}
        p.assets={a:SimpleNamespace(address=a,symbol='ASSET',decimals=18,code_hash=None) for a in self.events.assets}
        self.life={'state':'operating','predecessor_controller':None,'lp_exit_started':False}
        self.header_reads=0;self.final_reads=0;self.history_reads=0;self.replays=0
        def header(tag):
            self.header_reads+=1
            return p.rpc.call('eth_getBlockByNumber',[tag,False])
        p._header=header
        p._snapshot=lambda:(p._header('0x63'),111,copy.deepcopy(self.transport.block))
        def fresh(h):
            if not -30<=p.clock()-h['timestamp']<p.max_age:raise ProjectionError('Controlled snapshot stale')
        p._fresh=fresh
        p._verify_deployment=lambda _b:copy.deepcopy(self.life)
        p._admitted=lambda _b,**_kw:([ZERO,ZZZ],list(self.events.royalties))
        def finish(h):
            self.final_reads+=1
            if p._header('0x63')!=h:raise ProjectionError('Controlled final anchor changed')
            fresh(h)
        p._finish=finish
        engine=object.__new__(Earnings)
        engine.p=p;engine.checkpoint=None;engine.prices=None;engine.descriptors=p.assets
        engine.profiles={p.contracts['access'].address:{r:p.contracts[r] for r in ('fees','membership')}}
        provenance=dict(available=True,through_block=99,block_hash=self.transport.header['hash'],minted_count=len(self.events.ids),
            from_block=1,start_block_hash='0x'+'11'*32,start_parent_hash='0x'+'12'*32,indexer_next_block=100)
        self.history=SimpleNamespace(owners={i:ALICE for i in self.events.ids},provenance=provenance,
            claims={},conversions={},lp_conversions={})
        def snapshot(_p,_header,_block,_lp,_royalties,**kwargs):
            self.history_reads+=1
            model=kwargs.get('consumer')
            if model is not None:
                self.replays+=1
                for index,(emitter,topics,data,timestamp,transaction) in enumerate(self.events.rows):
                    model(emitter,topics,data,index+1,'0x'+format(index+1,'064x'),timestamp,transaction,index)
            return copy.deepcopy(self.history)
        engine.history_snapshot=snapshot
        p.earnings_history=engine

    def read(self, offset=0):
        from frontend_api.wallet_aggregate import read
        self.transport.calls.clear();self.transport.batch_sizes.clear();self.transport.static_getters=0
        budget=Budget()
        with request_scope(budget):
            result=read(self.p,ALICE,99,offset)
        self.last_post_observation=2048-budget.posts
        return result,1024-budget.calls


class WrappedConstructorRPC(StaticBatchRPC):
    """Add independently encoded constructor replies to an existing RPC fixture."""
    def __init__(self, inner, roles):
        artifact=json.loads((Path(__file__).resolve().parents[1]/
                            'frontend_api/read_batch/WalletReadBatch.json').read_bytes())
        self.creation=bytes.fromhex(artifact['creation_bytecode'][2:])
        self.inner=inner;self.roles=roles;self.chain=31337
        self.calls=[];self.batch_sizes=[];self.static_getters=0;self.active_block=None

    def scalar(self,target,data):
        self.static_getters+=1
        return self.inner.call('eth_call',[{'to':target,'data':data},copy.deepcopy(self.active_block)])

    def call(self,method,params=None):
        self.calls.append((method,copy.deepcopy(params)))
        if method=='eth_call' and 'to' not in params[0]:
            self.active_block=copy.deepcopy(params[1])
            return self.constructor(params[0])
        return self.inner.call(method,params)


class WalletAggregateExactModelTests(unittest.TestCase):
    def test_empty_wallet_stays_exact_zero_without_disabling_proofs_or_asset_coverage(self):
        events = ExactEvents(0, royalty_count=65)
        model = events.replay()
        self.assertTrue(model.wallet_selection)
        self.assertEqual(model.selected, ())
        report = model.report({a: SimpleNamespace(symbol='A', decimals=18) for a in events.assets[:4]})
        self.assertEqual(len(report['all_time']), 4)
        for period in ('all_time', 'last_24h'):
            for row in report[period]:
                self.assertTrue(all(row[name+'_raw'] == '0' for name in NFT))

    def test_aggregate_explicit_mode_keeps_ordinary_sixteen_id_limit(self):
        identifiers = tuple(range(1, 18))
        with self.assertRaises(HistoryError):
            Replay(NOW, selected=identifiers)
        model = ExactReplay(NOW, wallet_ids=identifiers, tracked_assets=(ZERO, ZZZ))
        self.assertTrue(model.wallet_selection)
        self.assertFalse(model.track_all)
        self.assertEqual(model.selected, identifiers)
        for bad in ([1], (True,), (0,), (1, 1), (2**256,), tuple(range(1, 1002))):
            with self.subTest(ids=str(bad)[:60]), self.assertRaises(HistoryError):
                ExactReplay(NOW, wallet_ids=bad, tracked_assets=(ZERO,))
        for bad in ((), (ZERO, ZERO), tuple(address(i) for i in range(5))):
            with self.subTest(assets=bad), self.assertRaises(HistoryError):
                ExactReplay(NOW, wallet_ids=(1,), tracked_assets=bad)
        for extra in ({'selected': (1,)}, {'nft_id': 1}, {'track_all': True}):
            with self.subTest(extra=extra), self.assertRaises(HistoryError):
                ExactReplay(NOW, wallet_ids=(1,), tracked_assets=(ZERO,), **extra)

    def test_literal_source_wire_keeps_eighteen_earned_units_after_the_actual_claim(self):
        self.assertEqual(hashlib.sha256(source_wire.FIXTURE.read_bytes()).hexdigest(), source_wire.FIXTURE_SHA256)
        template = source_wire.model_for()
        raw = json.loads(source_wire.FIXTURE.read_bytes())['raw_logs']
        frames = source_wire.frames()
        roles = {role: emitter for emitter, role in template.roles.items()}
        identifier = frames[0][2][6]
        identifiers = tuple(int(row['topics'][3], 16) for row in raw
                            if row['address'] == roles['nft'] and len(row['topics']) == 4
                            and row['topics'][1] == '0x'+'0'*64)
        model = ExactReplay(104, wallet_ids=tuple(sorted(set(identifiers))), tracked_assets=template.pair)
        model.begin(roles, list(template.pair), [ZERO], fee_intake_version=1, royalty_settlement_version=4)
        first = frames[0][1][0]
        for index, row in enumerate(raw[:raw.index(first)]):
            model(row['address'], row['topics'], row['data'], 1, '0x'+format(1, '064x'),
                  99, '0x'+format(9, '064x'), index)
        for stage, rows, witness in frames:
            source_wire.apply(model, stage, rows)
            self.assertEqual(source_wire.actual_state(model, witness), witness[12:26])
        descriptors = {a: SimpleNamespace(symbol='ETH' if a == ZERO else 'ZZZ', decimals=18) for a in model.pair}
        report = model.report(descriptors)
        for row in report['all_time']:
            self.assertEqual((row['lp_individual_raw'], row['lp_collective_raw']), ('16', '2'))
            self.assertEqual(model.components(identifier, row['asset']), (0, 0))
        self.assertFalse(report['claims_and_conversions_are_income'])
        self.assertEqual(report['lp_allocation_version'], 1)

    def test_thousand_nfts_sixty_six_assets_keep_exact_current_units_and_bounded_tracking(self):
        events = ExactEvents(1000, dormant_last=True)
        self.assertEqual(len(events.assets), 66)
        tracked = events.assets[:4]
        model = events.replay(assets=tracked)
        descriptors = {a: SimpleNamespace(symbol='A', decimals=18) for a in tracked}
        report = model.report(descriptors)
        self.assertEqual(len(model.selected), 1000)
        self.assertEqual(len(model.members), 999)
        self.assertFalse(model.track_all)
        for period in ('all_time', 'last_24h'):
            for row in report[period]:
                for metric in NFT:
                    self.assertEqual(int(row[metric+'_raw']), events.expected(events.ids, row['asset'], metric,
                                                                            day=period == 'last_24h'))
        self.assertEqual(report['window'], {'after_timestamp_exclusive': BOUNDARY,
                                            'through_timestamp_inclusive': NOW})
        self.assertTrue(all(asset in tracked for account in model.account_totals.values() for _, asset in account))
        self.assertEqual((1000+15)//16, 63)
        self.assertEqual((len(events.assets)+3)//4, 17)
        # This is request arithmetic, not a time/provider acceptance result.
        self.assertEqual(63*17, 1071)

    def test_wallet_subsets_and_dormant_nft_do_not_pool_or_duplicate_earnings(self):
        events = ExactEvents(17, dormant_last=True)
        subsets = (events.ids[::2], events.ids[1::2])
        tracked = events.assets[:4]
        reports = [events.replay(ids, tracked).report({a: SimpleNamespace(symbol='A', decimals=18) for a in tracked})
                   for ids in subsets]
        for period in ('all_time', 'last_24h'):
            for index, asset in enumerate(tracked):
                for metric in NFT:
                    total = sum(int(report[period][index][metric+'_raw']) for report in reports)
                    self.assertEqual(total, events.expected(events.ids, asset, metric, day=period == 'last_24h'))
        dormant = events.replay((events.ids[-1],), tracked)
        for row in dormant.report({a: SimpleNamespace(symbol='A', decimals=18) for a in tracked})['all_time']:
            self.assertTrue(all(row[metric+'_raw'] == '0' for metric in NFT))

    def test_claim_conversion_and_transfer_do_not_create_current_holdings_income(self):
        events = ExactEvents(3, royalty_count=3)
        identifier = events.ids[0]
        events.emit('rewards', 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
                    (identifier, ZZZ), (32, 4, 32, 4), 5000)
        events.emit('rewards', 'Claimed(uint256,address,address,uint256)',
                    (identifier, ZERO, ALICE), (72,), 5001)
        events.emit('royalties', 'Claimed(uint256,address,address,uint256)',
                    (identifier, ZERO, ALICE), (4,), 5001)
        events.emit('nft', 'Transfer(address,address,uint256)', (ALICE, BOB, identifier), (), 5002)
        model = events.replay((identifier,))
        self.assertEqual(model.components(identifier, ZERO), (0, 0))
        self.assertEqual(model.components(identifier, ZZZ), (0, 0))
        report = model.report({a: SimpleNamespace(symbol='A', decimals=18) for a in events.assets[:4]})
        for period in ('all_time', 'last_24h'):
            for row in report[period]:
                for metric in NFT:
                    self.assertEqual(int(row[metric+'_raw']), events.expected((identifier,), row['asset'], metric,
                                                                            day=period == 'last_24h'))
        self.assertFalse(report['claims_and_conversions_are_income'])

    def test_rotating_royalty_units_are_assigned_before_wallet_sum(self):
        events=ExactEvents(3,royalty_count=3)
        transaction=events.transaction()
        events.emit('royalties','RoyaltiesAllocated(address,uint256,uint256,uint256,uint256,uint256)',
                    (ZERO,),(11,3,6,0,5),5000,transaction=transaction)
        events.emit('royalties','RoyaltiesReceived(address,uint256,bool)',(ZERO,),(11,1),5000,transaction=transaction)
        # Weights2/3/1: one complete six-ticket cycle and the next five
        # assign4/6/1 extra indivisible units, not pooled fractional claims.
        for identifier,extra in zip(events.ids,(4,6,1)):
            model=events.replay((identifier,),(ZERO,))
            self.assertEqual(model.totals['royalties',ZERO],events.expected((identifier,),ZERO,'royalties')+extra)
            self.assertEqual(model.royalty_cursors[ZERO],5)
        wallet=events.replay(events.ids,(ZERO,))
        self.assertEqual(wallet.totals['royalties',ZERO],23)

    def test_exclusive_day_lower_boundary_and_inclusive_snapshot_boundary_are_exact(self):
        events = ExactEvents(3, royalty_count=3,
                             timestamps=(BOUNDARY-1, BOUNDARY, BOUNDARY+1, NOW))
        model = events.replay()
        report = model.report({a: SimpleNamespace(symbol='A', decimals=18) for a in events.assets[:4]})
        for period in ('all_time', 'last_24h'):
            for row in report[period]:
                for metric in NFT:
                    self.assertEqual(int(row[metric+'_raw']), events.expected(events.ids, row['asset'], metric,
                                                                            day=period == 'last_24h'))
        native = next(row for row in report['last_24h'] if row['asset'] == ZERO)
        self.assertEqual(native['lp_individual_raw'], str(3*16*2))

    def test_seeded_aggregate_keeps_full_day_and_raw_phase_without_track_all_bypass(self):
        events = ExactEvents(17, dormant_last=True)
        prefix = ExactReplay(BOUNDARY, track_all=True)
        prefix.begin(ROLES, [ZERO, ZZZ], events.royalties,
                     fee_intake_version=1, royalty_settlement_version=4)
        for index, (emitter, topics, data, timestamp, transaction) in enumerate(events.rows):
            if timestamp <= BOUNDARY:
                prefix(emitter, topics, data, index+1, '0x'+format(index+1, '064x'),
                       timestamp, transaction, index)
        prefix.finish()
        payload = dict(shared={name: copy.deepcopy(getattr(prefix, name)) for name in SHARED},
            accounts=copy.deepcopy(prefix.accounts),
            collection={key:value for key,value in prefix.totals.items() if key[0] in COLLECTION},
            emitters=ROLES, lp_assets=[ZERO, ZZZ], royalty_assets=list(events.royalties), exact_lp=capture(prefix))
        saved = copy.deepcopy(payload)
        tracked = events.assets[:4]
        model = ExactReplay(NOW, wallet_ids=tuple(sorted(events.ids)), tracked_assets=tracked)
        model.begin(ROLES, [ZERO, ZZZ], events.royalties,
                    fee_intake_version=1, royalty_settlement_version=4)
        Seed('', {'number':1, 'timestamp':BOUNDARY}, {}, payload, None, 2).restore(model)
        self.assertEqual(exact_books(model), exact_books(prefix))
        self.assertTrue(all(asset in tracked for account in model.accounts.values() for _,asset in account))
        for index, (emitter, topics, data, timestamp, transaction) in enumerate(events.rows):
            if timestamp > BOUNDARY:
                model(emitter, topics, data, index+1, '0x'+format(index+1, '064x'),
                      timestamp, transaction, index)
        model.finish()
        report = model.report({a: SimpleNamespace(symbol='A', decimals=18) for a in tracked})
        for period in ('all_time', 'last_24h'):
            for row in report[period]:
                for metric in NFT:
                    self.assertEqual(int(row[metric+'_raw']), events.expected(events.ids, row['asset'], metric,
                                                                            day=period == 'last_24h'))
        # Seed.restore consumes a request-owned decoded payload; a second reader
        # receives its own bytes/maps. This is a codec seam, not artifact admission.
        second = ExactReplay(NOW, wallet_ids=tuple(sorted(events.ids)), tracked_assets=tracked)
        second.begin(ROLES, [ZERO, ZZZ], events.royalties,
                     fee_intake_version=1, royalty_settlement_version=4)
        Seed('', {'number':1, 'timestamp':BOUNDARY}, {}, copy.deepcopy(saved), None, 2).restore(second)
        self.assertEqual(exact_books(second), exact_books(prefix))
        young = ExactReplay(NOW, wallet_ids=tuple(sorted(events.ids)), tracked_assets=tracked)
        young.begin(ROLES, [ZERO, ZZZ], events.royalties,
                    fee_intake_version=1, royalty_settlement_version=4)
        with self.assertRaisesRegex(HistoryError, 'rolling day'):
            Seed('', {'number':1, 'timestamp':BOUNDARY+1}, {}, copy.deepcopy(saved), None, 2).restore(young)

    def test_aggregate_semantic_sources_are_part_of_reviewed_checkpoint_identity(self):
        sources = source_identity(2)
        self.assertIn('frontend_api/wallet_aggregate.py', sources)
        self.assertIn('frontend_api/read_batch.py', sources)
        self.assertTrue(all(len(digest) == 64 for digest in sources.values()))

    def test_read_reports_and_current_usd_conversion_do_not_mutate_exact_books(self):
        events = ExactEvents(3, royalty_count=3)
        model = events.replay()
        before = exact_books(model)
        descriptors = {a: SimpleNamespace(symbol='A', decimals=6 if a == ZERO else 18) for a in events.assets[:4]}
        prices = {a: {'available': a != ZZZ, 'usd_per_token_18': '3333333333333333333' if a != ZZZ else None,
                      'reason': None if a != ZZZ else 'unavailable'} for a in descriptors}
        report = model.report(descriptors)
        value_report(report, descriptors, prices)
        for period in ('all_time', 'last_24h'):
            for row in report[period]:
                for metric in NFT:
                    raw = events.expected(events.ids, row['asset'], metric, day=period == 'last_24h')
                    expected = (str(raw*3333333333333333333//10**descriptors[row['asset']].decimals)
                                if row['asset'] != ZZZ else '0' if raw == 0 else None)
                    self.assertEqual(row['usd_at_current_price_18'][metric], expected)
        self.assertEqual(exact_books(model), before)


class WalletAggregateComposedTests(unittest.TestCase):
    def check_rows(self, fixture, output):
        self.assertTrue(output['available'])
        self.assertTrue(output['complete'])
        self.assertEqual(output['verified_count'],len(fixture.events.ids))
        self.assertEqual(output['token_ids'],list(map(str,sorted(fixture.events.ids))))
        self.assertEqual(output['inventory_sha256'],hashlib.sha256(','.join(output['token_ids']).encode('ascii')).hexdigest())
        self.assertEqual(output['earnings_error'],None)
        self.assertEqual(output['earnings']['scope'],'wallet')
        self.assertEqual(output['earnings']['token_ids'],output['token_ids'])
        self.assertEqual(output['earnings']['window'],{'after_timestamp_exclusive':BOUNDARY,'through_timestamp_inclusive':NOW})
        for period in ('all_time','last_24h'):
            self.assertEqual([r['asset'] for r in output['earnings'][period]],output['selected_asset_ids'])
            for row in output['earnings'][period]:
                for metric in NFT:
                    self.assertEqual(int(row[metric+'_raw']),fixture.events.expected(fixture.events.ids,row['asset'],metric,
                                                                                   day=period=='last_24h'))
        self.assertFalse(output['earnings']['claims_and_conversions_are_income'])

    def test_zero_typical_and_page_boundary_holdings_keep_real_batch_and_default_work_budget(self):
        from frontend_api.worker import MAX_RESULT
        for count in (0,1,17):
            with self.subTest(count=count):
                fixture=AggregateComposition(count,unit_scale=10**21)
                output,calls=fixture.read()
                self.check_rows(fixture,output)
                self.assertEqual(calls,len(fixture.transport.calls))
                self.assertLessEqual(calls,1024)
                self.assertLess(len(json.dumps({'ok':output},separators=(',',':'),allow_nan=False).encode()),MAX_RESULT)
                self.assertTrue(all(1<=n<=4 for n in fixture.transport.batch_sizes))
                self.assertEqual(sum(fixture.transport.batch_sizes),count)
                self.assertGreaterEqual(fixture.header_reads,3)
                self.assertEqual(fixture.final_reads,1)
                self.assertEqual(fixture.replays,1)
                self.assertIsInstance(fixture.p.rpc,BudgetedRPC)
                self.assertTrue(all(method in {'eth_call','eth_getCode','eth_getBlockByNumber'} for method,_ in fixture.transport.calls))

    def test_thousand_holdings_all_sixty_six_currencies_use_seventeen_complete_wallet_pages(self):
        from frontend_api.worker import MAX_RESULT
        fixture=AggregateComposition(1000,unit_scale=10**21)
        coverage=[];requests=[];maximum_calls=0;maximum_bytes=0;observed=[]
        for offset in range(0,len(fixture.events.assets),4):
            started=time.monotonic()
            output,calls=fixture.read(offset)
            elapsed=time.monotonic()-started
            self.check_rows(fixture,output)
            coverage.extend(output['selected_asset_ids']);requests.append(output)
            maximum_calls=max(maximum_calls,calls)
            maximum_bytes=max(maximum_bytes,len(json.dumps({'ok':output},separators=(',',':'),allow_nan=False).encode()))
            self.assertLessEqual(len(output['selected_asset_ids']),4)
            self.assertEqual(len(fixture.transport.batch_sizes),375)
            metric=dict(asset_offset=offset,logical_rpc=calls,
                injected_transport_posts=fixture.last_post_observation,
                constructor_calls=len(fixture.transport.batch_sizes),maximum_ids_per_constructor=max(fixture.transport.batch_sizes),
                response_bytes=len(json.dumps({'ok':output},separators=(',',':'),allow_nan=False).encode()),
                elapsed_seconds=round(elapsed,6))
            observed.append(metric)
            print('WALLET_AGGREGATE_PAGE='+json.dumps(metric,sort_keys=True),flush=True)
        self.assertEqual(len(requests),17)
        self.assertEqual(coverage,list(fixture.events.assets))
        self.assertEqual(len(set(coverage)),66)
        self.assertIsNone(requests[-1]['next_asset_offset'])
        self.assertEqual(len({p['inventory_sha256'] for p in requests}),1)
        self.assertEqual(fixture.replays,17)
        self.assertLessEqual(maximum_calls,1024)
        self.assertLess(maximum_bytes,MAX_RESULT)
        print('WALLET_AGGREGATE_MAXIMUM='+json.dumps(dict(nfts=1000,descriptors=66,
            aggregate_pages=17,maximum_rpc_per_request=maximum_calls,maximum_response_bytes=maximum_bytes,
            full_86400_window=True,actual_provider_or_full_journey_qualified=False,
            transport_scope='Injected constructor/scalar responses; no HTTP posts or actual EVM gas proof.',
            per_page=observed),sort_keys=True),flush=True)

    def test_late_getter_failure_discards_earnings_and_next_request_can_recover(self):
        fixture=AggregateComposition(17)
        failing=fixture.transport.roles['royalties'],query('claimable(uint256,address)',fixture.events.ids[-2],address(84))
        fixture.transport.failures.add(failing)
        output,calls=fixture.read(64)
        self.assertFalse(output['complete'])
        self.assertEqual(output['verified_count'],0)
        self.assertEqual(output['earnings_error'],'earnings_unavailable')
        self.assertIsNone(output['earnings'])
        self.assertEqual(output['count'],17)
        self.assertEqual(fixture.final_reads,1)
        self.assertLessEqual(calls,1024)
        fixture.transport.failures.clear()
        recovered,_=fixture.read(64)
        self.check_rows(fixture,recovered)
        self.assertEqual(fixture.final_reads,2)

    def test_many_nft_conversion_histories_keep_unselected_source_eth_credits_and_linear_maps(self):
        from frontend_api import wallet_aggregate
        original_report=wallet_aggregate.conversion_report
        events=ExactEvents(33,dormant_last=True,unit_scale=10**21,
                          royalty_assets=(ZERO,address(1),address(2),address(3),address(21)))
        fixture=AggregateComposition(events=events)
        outsider=events.ids[0]
        fixture.history.owners[outsider]=BOB
        events.emit('nft','Transfer(address,address,uint256)',(ALICE,BOB,outsider),(),4500)
        fixture.transport.put('nft','ownerOf(uint256)',(outsider,),(BOB,))
        fixture.transport.put('nft','balanceOf(address)',(ALICE,),(32,))
        converted=[identifier for index,identifier in enumerate(events.ids) if index%2==0 and identifier in events.weights]
        for index,identifier in enumerate(converted):
            amount=10**21
            tx=events.transaction()
            events.emit('rewards','LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
                        (identifier,ZZZ),(32*amount,4*amount,64*amount,8*amount),5000+index,transaction=tx)
            fixture.history.lp_conversions[identifier,ZZZ]=(36*amount,72*amount,1,
                {'block_number':5000+index,'log_index':index,'transaction_hash':tx})
            fixture.transport.put('rewards','claimableComponents(uint256,address)',(identifier,ZZZ),(0,0))
            fixture.transport.put('rewards','claimableComponents(uint256,address)',(identifier,ZERO),(96*amount,12*amount))
            fixture.transport.put('rewards','claimable(uint256,address)',(identifier,ZZZ),(0,))
            fixture.transport.put('rewards','claimable(uint256,address)',(identifier,ZERO),(108*amount,))
        amount=10**21;n=len(converted);active=events.active
        fixture.transport.put('rewards','allocationTree(uint256)',(0,),(active,4*active*amount,4*(active-n)*amount))
        fixture.transport.put('rewards','allocationTree(uint256)',(5,),(active,32*active*amount,32*(active-n)*amount))
        fixture.transport.put('rewards','directLiabilities(address)',(ZERO,),(72*n*amount,))
        fixture.transport.put('rewards','liabilities(address)',(ZERO,),((36*active+72*n)*amount,))
        fixture.transport.put('rewards','liabilities(address)',(ZZZ,),(36*(active-n)*amount,))
        before=copy.deepcopy(fixture.history.lp_conversions)
        inspected=[]
        def report(rows,identifier,descriptors,provenance):
            if rows:
                inspected.append((identifier,set(key[0] for key in rows),set(key[1] for key in rows)))
                self.assertEqual({key[0] for key in rows},{identifier})
            return original_report(rows,identifier,descriptors,provenance)
        with patch('frontend_api.wallet_aggregate.conversion_report',side_effect=report):
            output,calls=fixture.read(0)
        self.assertTrue(output['complete'])
        self.assertNotIn(ZZZ,output['selected_asset_ids'])
        self.assertEqual(output['count'],32)
        self.assertNotIn(str(outsider),output['token_ids'])
        native=next(row for row in output['earnings']['all_time'] if row['asset']==ZERO)
        held=tuple(i for i in events.ids if i!=outsider)
        self.assertEqual(int(native['lp_individual_raw']),events.expected(held,ZERO,'lp_individual'))
        self.assertEqual(int(native['lp_collective_raw']),events.expected(held,ZERO,'lp_collective'))
        self.assertTrue(inspected)
        self.assertTrue(all(ZZZ in assets for _,_,assets in inspected))
        self.assertEqual(fixture.history.lp_conversions,before)
        self.assertLessEqual(calls,1024)

    def test_conflicting_prefetched_identity_is_fatal_not_available_earnings_failure(self):
        from frontend_api import wallet_aggregate
        from frontend_api.canonical_cache import prefetch
        original=wallet_aggregate.prefetch_accounts
        fixture=AggregateComposition(17)
        def conflicting(p,block,ids,lp,royalties):
            result=original(p,block,ids,lp,royalties)
            prefetch(p,block,[(p.contracts['nft'].address,query('ownerOf(uint256)',ids[0]),'0x'+word(BOB))])
            return result
        with patch('frontend_api.wallet_aggregate.prefetch_accounts',side_effect=conflicting):
            with self.assertRaisesRegex(ProjectionError,'Conflicting'):
                fixture.read()
        self.assertEqual(fixture.final_reads,0)
        self.assertIsInstance(fixture.p.rpc,BudgetedRPC)

    def test_wrong_live_owner_ordinal_share_component_or_paid_balance_rejects(self):
        variants=(('nft','ownerOf(uint256)',(BOB,)),('nft','mintOrdinalOf(uint256)',(999,)),
                  ('vault','sharesOf(uint256)',(2,)),('rewards','claimableComponents(uint256,address)',(33,4)),
                  ('rewards','claimable(uint256,address)',(999,)))
        for role,signature,values in variants:
            with self.subTest(signature=signature):
                fixture=AggregateComposition(17)
                identifier=fixture.events.ids[-2]
                args=(identifier,ZERO) if signature.endswith(',address)') else (identifier,)
                fixture.transport.put(role,signature,args,values)
                if signature=='mintOrdinalOf(uint256)':
                    fixture.transport.put('nft','tokenAtOrdinal(uint256)',(999,),(identifier,))
                with self.assertRaises(HistoryError):fixture.read()

    def test_coherent_in_range_ordinal_swap_cannot_override_replayed_mint_order(self):
        fixture=AggregateComposition(17)
        first,second=fixture.events.ids[:2]
        fixture.transport.put('nft','mintOrdinalOf(uint256)',(first,),(2,))
        fixture.transport.put('nft','mintOrdinalOf(uint256)',(second,),(1,))
        fixture.transport.put('nft','tokenAtOrdinal(uint256)',(1,),(second,))
        fixture.transport.put('nft','tokenAtOrdinal(uint256)',(2,),(first,))
        with self.assertRaisesRegex(HistoryError,'ordinal|mint.order|identity'):
            fixture.read()

    def test_bad_coverage_final_anchor_and_deadline_cannot_publish_partial_success(self):
        from frontend_api.wallet_aggregate import read
        fixture=AggregateComposition(17)
        fixture.history.provenance['minted_count']=16
        with self.assertRaises(HistoryError):fixture.read()
        fixture=AggregateComposition(17)
        finish=fixture.p._finish
        def changed(header):
            fixture.transport.header['hash']='0x'+'ee'*32
            finish(header)
        fixture.p._finish=changed
        with self.assertRaises(ProjectionError):fixture.read()
        fixture=AggregateComposition(17)
        clock=[0]
        def advancing():
            clock[0]+=.2
            return clock[0]
        budget=Budget(seconds=1,clock=advancing)
        with self.assertRaises(WorkLimit),request_scope(budget):read(fixture.p,ALICE,99,0)
        self.assertIsInstance(fixture.p.rpc,BudgetedRPC)

    def test_actual_projection_sqlite_and_new_checkpoint_preserve_transfer_claim_and_conversion(self):
        from tests_python.test_earnings_checkpoint_v2 import Checkpoint2APITests
        fixture=Checkpoint2APITests('runTest')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.config['wallet_read_batch']=1
        path=fixture.install();original=path.read_bytes();fixture.suffix()
        transport=WrappedConstructorRPC(fixture.rpc,fixture.c)
        projection=Projection(fixture.config,transport,clock=lambda:fixture.now)
        budget=Budget()
        owner=address(32)
        with request_scope(budget):
            output=projection.wallet_aggregate(owner,99,0)
        legacy=fixture.projection().wallet_earnings(owner,99)
        self.assertEqual(output['count'],1)
        self.assertEqual(output['token_ids'],[str(fixture.i)])
        self.assertTrue(output['complete'])
        for key in ('all_time','last_24h','window'):
            self.assertEqual(output['earnings'][key],legacy[key])
        self.assertFalse(output['earnings']['claims_and_conversions_are_income'])
        self.assertEqual(path.read_bytes(),original)
        self.assertLessEqual(1024-budget.calls,1024)
        self.assertTrue(transport.batch_sizes)
        # This fixture executes real configured Projection/History/Checkpoint/
        # Earnings and typed batching. Runtime/getter state and clocks remain
        # injected; it does not establish a normal F6/provider/market release.

    def test_current7_legacy_wallet_reader_also_rejects_a_coherent_ordinal_swap(self):
        from tests_python.test_earnings_checkpoint_v2 import Checkpoint2APITests
        fixture=Checkpoint2APITests('runTest')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.put(fixture.c['nft'],'mintOrdinalOf(uint256)',(fixture.j,),(3,))
        fixture.put(fixture.c['nft'],'mintOrdinalOf(uint256)',(fixture.k,),(2,))
        fixture.put(fixture.c['nft'],'tokenAtOrdinal(uint256)',(2,),(fixture.k,))
        fixture.put(fixture.c['nft'],'tokenAtOrdinal(uint256)',(3,),(fixture.j,))
        with self.assertRaisesRegex(HistoryError,'ordinal|mint.order|identity'):
            fixture.projection().wallet_earnings(address(31),99)


class WalletAggregateIntegrationBoundaryTests(unittest.TestCase):
    def test_test_transcript_selector_cache_is_byte_equivalent_and_bounded(self):
        selector.cache_clear()
        self.assertEqual(query('ownerOf(uint256)',7),'0x6352211e'+word(7))
        self.assertEqual(query('balanceOf(address)',ALICE),'0x70a08231'+word(ALICE))
        signatures=('claimableComponents(uint256,address)','claimable(uint256,address)',
                    'mintOrdinalOf(uint256)','tokenAtOrdinal(uint256)','weightOf(uint256)',
                    'rewardBucket(uint256)','allocationTree(uint256)','pending(address)')
        for signature in signatures:
            self.assertEqual(selector(signature),keccak256(signature.encode())[:4].hex())
        misses=selector.cache_info().misses
        for _ in range(1000):
            for signature in signatures:selector(signature)
        self.assertEqual(selector.cache_info().misses,misses)
        self.assertEqual(selector.cache_info().maxsize,128)

    def test_opt_in_is_exact_integer_current_only_and_not_inherited_by_predecessor(self):
        from tests_python.test_exact_lp_profile7 import Fresh7API
        from tests_python.test_earnings_checkpoint_lineage import EpochFixture
        fresh=Fresh7API(self)
        for value in (True,False,None,'1',-1,2):
            config=copy.deepcopy(fresh.config);config['wallet_read_batch']=value
            with self.subTest(value=value),self.assertRaises(ValueError):Projection(config,fresh.rpc,clock=lambda:4000)
        config=copy.deepcopy(fresh.config);config['wallet_read_batch']=1
        with self.assertRaises(ValueError):Projection(config,fresh.rpc,clock=lambda:4000)
        self.assertEqual(Projection(fresh.config,fresh.rpc,clock=lambda:4000).wallet_read_batch,0)
        lineage=EpochFixture(self,2)
        config=copy.deepcopy(lineage.config);config['wallet_read_batch']=1
        projection=lineage.projection(config)
        self.assertEqual(projection.wallet_read_batch,1)
        self.assertTrue(all(peer.projection.wallet_read_batch==0 for peer in projection.lineage.entries))

    def test_exact_get_route_and_worker_dispatch_preserve_limits_and_sanitized_errors(self):
        from frontend_api.server import handler
        from frontend_api.worker import WorkerClient,WorkerPool,_run,MAX_RESULT
        projection=SimpleNamespace(wallet_aggregate=Mock(return_value={'aggregate':True}))
        Handler=handler(projection)
        def request(path):
            req=object.__new__(Handler)
            req.server=SimpleNamespace(server_address=('127.0.0.1',8787))
            req.headers=Message();req.headers['Host']='127.0.0.1:8787';req.path=path
            req.begin_work=Mock();req._json=Mock();req.do_GET();return req
        valid='/v1/wallets/'+ALICE+'/aggregate/99/64'
        req=request(valid)
        projection.wallet_aggregate.assert_called_once_with(ALICE,99,64)
        req._json.assert_called_once_with(200,{'aggregate':True})
        for suffix in ('099/64','99/064','99/3','99/2048','99/-4','99/0/extra','99/0?x=1'):
            projection.wallet_aggregate.reset_mock()
            req=request('/v1/wallets/'+ALICE+'/aggregate/'+suffix)
            projection.wallet_aggregate.assert_not_called();req.begin_work.assert_not_called()
            self.assertIn(req._json.call_args.args[0],(400,404))
        client=object.__new__(WorkerClient);client._request=Mock(return_value={'ok':True})
        self.assertEqual(client.wallet_aggregate(ALICE,99,64),{'ok':True})
        client._request.assert_called_once_with('wallet_aggregate',[ALICE,99,64])
        pool=object.__new__(WorkerPool);pool._dispatch=Mock(return_value={'ok':True})
        pool.wallet_aggregate(ALICE,99,64);pool._dispatch.assert_called_once_with('wallet_aggregate',ALICE,99,64)
        for payload,expected in (({'aggregate':True},{'ok':{'aggregate':True}}),
                                 ({'oversized':'x'*MAX_RESULT},{'error':'result_limit'})):
            with TemporaryDirectory() as directory,patch('frontend_api.worker.Projection',return_value=SimpleNamespace(wallet_aggregate=Mock(return_value=payload))):
                output=Path(directory)/'out.json';_run(output,{},None,'wallet_aggregate',[ALICE,99,64])
                self.assertEqual(json.loads(output.read_bytes()),expected)
        with TemporaryDirectory() as directory,patch('frontend_api.worker.Projection',return_value=SimpleNamespace(wallet_aggregate=Mock(side_effect=RpcError('secret endpoint')))):
            output=Path(directory)/'out.json';_run(output,{},None,'wallet_aggregate',[ALICE,99,64])
            self.assertEqual(json.loads(output.read_bytes()),{'error':'unavailable'})
        config=(Path(__file__).resolve().parents[1]/'config/nginx/popl-api-locations.conf').read_text()
        expression=re.search(r'location ~ "([^"\n]+)"',config).group(1)
        self.assertIsNotNone(re.fullmatch(expression,valid))
        self.assertIsNone(re.fullmatch(expression,valid+'/more'))
        self.assertIn('if ($request_method != GET) { return 405; }',config)

    def test_auditor_bundle_requires_and_preserves_exact_read_only_helper_inputs(self):
        from tests_python import test_review_bundle as fixtures
        from zzz_ops import review_bundle as bundle
        import io
        import zipfile
        root=Path(__file__).resolve().parents[1]
        names=('frontend_api/read_batch/WalletReadBatch.sol','frontend_api/read_batch/WalletReadBatch.json')
        files=fixtures.inputs();files['frontend_api/read_batch.py']=(root/'frontend_api/read_batch.py').read_bytes()
        for name in names:files[name]=(root/name).read_bytes()
        raw,manifest=fixtures.build(files,schema=4)
        checked=bundle.verify(raw,bundle.digest(raw))
        self.assertTrue(checked['ok']);self.assertFalse(manifest['production_approved']);self.assertFalse(manifest['tests_executed'])
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for name in names:self.assertEqual(archive.read('source/'+name),files[name])
        for name in names:
            missing=dict(files);missing.pop(name)
            with self.subTest(missing=name),self.assertRaisesRegex(bundle.BundleError,'source/artifact inputs'):
                fixtures.build(missing,schema=4)
        self.assertTrue(bundle.admitted(names[1],schema=4))
        for schema in (1,2,3):self.assertFalse(bundle.admitted(names[1],schema=schema))
        for other in ('frontend_api/read_batch/other.json','frontend_api/read_batch/WalletReadBatch.json.bak',
                      'frontend_api/read_batch/secrets/WalletReadBatch.json'):
            self.assertFalse(bundle.admitted(other,schema=4))


if __name__ == '__main__':
    unittest.main()
