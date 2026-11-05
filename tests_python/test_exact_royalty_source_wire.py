"""Actual isolated-EVM royalty getter/event observations consumed by Python.

The production royalty ledger and allocator produced the fixture. Its NFT,
access and ERC20 were controlled mocks; this is not LP/OpenSea/RPC qualification.
The reader scaffolds only the observed NFT inventory, without inventing ledger
credits, ticket starts or claimable values from its own expected model.
"""
from collections import defaultdict
from itertools import groupby
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from frontend_api.earnings_checkpoint import decode, encode
from frontend_api.earnings_replay import Replay, SCALE, ZERO
from frontend_api.history import CLAIMED
from frontend_api.royalty_reporting import Reporting
from zzz_ops.abi import address, decode_words, keccak256

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=Path(__file__).parent/'fixtures/exact-royalty-source4-wire.json'
FIXTURE_SHA256='99b47685f87eb7be945ead8cb74845fb4e5a2d3a737f47477d03ce1023fbb1e9'


def source_cases():return json.loads(FIXTURE.read_bytes())['cases']


def replay_case(case):
    meta=case['metadata'][0];asset=address(meta['asset'])
    ids=tuple(int(i) for i in case['snapshots'][-1]['token_ids'])
    model=Replay(max(int(e['timestamp']) for e in case['events']),selected=ids)
    model.begin({'royalties':address(meta['ledger'])},[],[ZERO,asset],royalty_settlement_version=4)
    # The mock NFT emits no ERC721 mint logs. Seed observed inventory only;
    # all weights, order, allocations and payouts below come from EVM logs.
    model.mints=list(ids);model.minted=set(ids)
    paid=defaultdict(int);states={};snapshots={s['phase']:s for s in case['snapshots']}
    for phase,entries in groupby(case['events'],key=lambda e:e['phase']):
        entries=list(entries)
        transaction='0x'+keccak256((meta['case']+phase).encode()).hex()
        for n,e in enumerate(entries):
            words=decode_words(e['data'])
            if e['topics'][0].lower()==CLAIMED:
                identifier=int(e['topics'][1],16);currency='0x'+e['topics'][2][-40:].lower()
                paid[identifier,currency]+=int(words[0],16)
            else:
                block=int(e['block_number'])
                model(address(e['emitter']),e['topics'],e['data'],block,
                      '0x'+keccak256(str(block).encode()).hex(),int(e['timestamp']),transaction,n)
        states[phase]=dict(
            activation_order=list(model.activation_order),ticket_offsets=dict(model.ticket_offsets),
            royalty_cursors=dict(model.royalty_cursors),weights=dict(model.weights),paid=dict(paid),
            earnings={i:model.accounts[i]['royalties',asset]//SCALE for i in ids})
        if phase in snapshots:
            snapshot=snapshots[phase]
            assert int(snapshot['allocation_cursor'])==model.royalty_cursors[asset]
            for i,raw_start,ordinal,weight,claimable in zip(
                    snapshot['token_ids'],snapshot['ticket_starts'],snapshot['activation_ordinals'],
                    snapshot['weights'],snapshot['claimable_units']):
                i=int(i);active=i in model.weights
                assert int(raw_start)==model.ticket_offsets[i]+1 if active else int(raw_start)==0
                assert int(ordinal)==model.activation_order.index(i)+1 if active else int(ordinal)==0
                assert int(weight)==model.weights.get(i,0)
                assert int(claimable)==states[phase]['earnings'][i]-paid[i,asset]
            assert not model.pending_exact_allocations
    return model,states


class ExactSourceWireTests(unittest.TestCase):
    def test_fixture_is_actual_source_bound_evm_evidence_with_explicit_mock_limits(self):
        raw=FIXTURE.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),FIXTURE_SHA256)
        fixture=json.loads(raw)
        for name in ('src/ZZZRoyaltyRewards.sol','src/libraries/ExactRoyaltyAllocation.sol',
                     'src/base/ZZZCanonicalLedger.sol','src/libraries/ExactToken.sol'):
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),fixture['source_sha256'][name])
        self.assertEqual(sum(len(c['events']) for c in fixture['cases'].values()),34)
        self.assertEqual(sum(len(c['snapshots']) for c in fixture['cases'].values()),6)
        for case in fixture['cases'].values():
            meta=case['metadata'][0]
            self.assertTrue(meta['real_royalty_ledger']);self.assertTrue(meta['synthetic_nft_access_token'])
            self.assertFalse(meta['public_chain']);self.assertEqual(meta['settlement_version'],'4')

    def test_all_actual_allocation_and_claim_events_reconcile_to_actual_getter_snapshots(self):
        for name,case in source_cases().items():
            model,states=replay_case(case)
            asset=address(case['metadata'][0]['asset'])
            for snapshot in case['snapshots']:
                self.assertEqual(int(snapshot['accounted']),sum(int(snapshot[k]) for k in ('liabilities','orphaned','opening_pool')))
                self.assertGreaterEqual(int(snapshot['raw_balance']),int(snapshot['accounted']))
                self.assertEqual(sum(map(int,snapshot['claimable_units'])),int(snapshot['liabilities']))
            last=case['snapshots'][-1]
            self.assertEqual(last['phase'],'claimed-all')
            self.assertEqual(int(last['raw_balance']),0);self.assertEqual(int(last['liabilities']),0)
            self.assertEqual(sum(states['claimed-all']['paid'].values()),model.totals['royalties_allocated',asset])
            self.assertEqual(sum(states['claimed-all']['earnings'].values()),model.totals['royalties_allocated',asset])

    def test_reporting5_accepts_the_actual_one_based_wire_including_first_and_dormant_nfts(self):
        for case in source_cases().values():
            meta=case['metadata'][0];asset=address(meta['asset'])
            times={e['phase']:int(e['timestamp']) for e in case['events']}
            for snapshot in case['snapshots']:
                observed={int(i):dict(start=int(start),ordinal=int(ordinal),weight=int(weight),claimable=int(claimable))
                    for i,start,ordinal,weight,claimable in zip(snapshot['token_ids'],snapshot['ticket_starts'],
                        snapshot['activation_ordinals'],snapshot['weights'],snapshot['claimable_units'])}
                def read(role,sig,*args,**kwargs):
                    scalar={'ROYALTY_SETTLEMENT_VERSION()':int(meta['settlement_version']),
                        'mintEnd()':int(meta['mint_end']),'royaltiesOpenAt()':int(meta['claims_open_at']),
                        'activationCount()':int(snapshot['activation_count']),'totalWeight()':int(snapshot['total_weight']),
                        'effectiveEligibleCount(address)':int(snapshot['eligible_count']),
                        'eligibleWeight(address)':int(snapshot['eligible_weight']),
                        'allocationCursor(address)':int(snapshot['allocation_cursor'])}
                    if sig in scalar:return scalar[sig]
                    field={'ticketStart(uint256)':'start','activationOrdinal(uint256)':'ordinal',
                           'claimable(uint256,address)':'claimable'}[sig]
                    return observed[args[0]][field]
                def call(target,sig,*args,**kwargs):
                    value=(times[snapshot['phase']]>=int(meta['claims_open_at']) if sig=='royaltiesOpen()' else
                           0<observed[args[0]]['ordinal']<=int(snapshot['eligible_count']))
                    return [f'{int(value):064x}']
                p=SimpleNamespace(accounting_version=6,_uint=read,_call=call,
                    _addr=lambda *a,**kw:address(meta['controller']),
                    assets={asset:SimpleNamespace(symbol='OBSERVED_MOCK_TOKEN',decimals=0)},
                    contracts={'royalties':SimpleNamespace(address=address(meta['ledger'])),
                               'access':SimpleNamespace(address=address(meta['controller']))})
                for identifier,values in observed.items():
                    result=Reporting({'schema':5,'converter':None},p).read(identifier,values['weight'],[asset],
                        {asset:True},{},timestamp=times[snapshot['phase']])
                    self.assertEqual(result['ticket_start'],values['start'])
                    self.assertEqual(int(result['balances'][0]['raw']),values['claimable'])

    def test_actual_v8_export_rows_preserve_one_based_starts_and_non_mint_activation_order(self):
        case=source_cases()['mixed-nonmint-order'];_model,states=replay_case(case)
        captured=states['frozen-settled'];rows=[decode_words(row['record']) for row in case['canonical_v8_rows']]
        asset_count,nft_count,total_weight,end,capacity=[int(w,16) for w in rows[0]]
        self.assertEqual((asset_count,nft_count,total_weight,end,capacity),(2,3,6,1200,16))
        asset_rows=rows[1:1+asset_count]
        nft_rows=rows[1+asset_count:]
        weight_rows=nft_rows[::1+asset_count]
        self.assertTrue(all(len(row)==6 for row in asset_rows))
        self.assertTrue(all(len(row)==4 for row in weight_rows))
        raw={int(row[0],16):tuple(int(w,16) for w in row[1:]) for row in weight_rows}
        actual_mint_order=[int(row[0],16) for row in weight_rows]
        actual_activation_order=sorted(raw,key=lambda i:raw[i][1])
        self.assertNotEqual(actual_mint_order,actual_activation_order)
        self.assertEqual(actual_activation_order,captured['activation_order'])
        for i,(weight,ordinal,start) in raw.items():
            self.assertEqual(weight,captured['weights'][i])
            self.assertEqual(ordinal,captured['activation_order'].index(i)+1)
            self.assertEqual(start,captured['ticket_offsets'][i]+1)
        self.assertEqual(decode(encode(captured['ticket_offsets'])),captured['ticket_offsets'])
        liabilities={('0x'+row[0][-40:]):int(row[3],16) for row in asset_rows}
        claims=defaultdict(int)
        asset_nft_rows=[row for n,row in enumerate(nft_rows) if n%(1+asset_count)]
        self.assertTrue(all(len(row)==3 for row in asset_nft_rows))
        for row in asset_nft_rows:claims['0x'+row[1][-40:]]+=int(row[2],16)
        self.assertEqual(dict(claims),liabilities)


if __name__=='__main__':unittest.main()
