"""Real Vault/Rewards LP logs and literal getters consumed by exact7 replay.

Production NFT/Vault/Fees/Rewards/Membership ran in an isolated EVM. Venue,
authority/VRF and correlated normalized price feeds were controlled fixtures.
Raw emitter/topics/data are original. Consumer block/time/hash embedding is
synthetic: this checks LP accounting, not provider, market or timestamp honesty.
Royalty4 has separate actual-source fixtures; no royalty balances are invented.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.history import ZERO,HistoryError
from zzz_ops.abi import keccak256

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=Path(__file__).parent/'fixtures/exact-lp-source7-wire.json'
FIXTURE_SHA256='4543f84910b6cdaaac6f64e10dee1099fddbf5b869af36260d94ad59b9593876'
WIRE='0x'+keccak256(b'ExactLPWire(uint8,bytes,bytes)').hex()
SYNC='0x'+keccak256(b'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)').hex()
ACK='0x'+keccak256(b'SharesAdded(uint256,uint256,uint256,uint256)').hex()
CLAIM='0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex()
ROYALTY_ADDED='0x'+keccak256(b'AssetAdded(address,uint256)').hex()


def uint(raw,at):
    if at%32 or at<0 or at+32>len(raw):raise ValueError('Malformed test ABI offset')
    return int.from_bytes(raw[at:at+32])

def dynamic(raw,at):
    size=uint(raw,at);end=at+32+size;padded=(end+31)//32*32
    if padded>len(raw) or any(raw[end:padded]):raise ValueError('Malformed test ABI bytes')
    return raw[at+32:end]

def logs(raw):
    start=uint(raw,0);count=uint(raw,start);base=start+32
    if start!=32 or count>128:raise ValueError('Unbounded test Vm.Log array')
    result=[]
    for n in range(count):
        at=base+uint(raw,base+32*n);topics=at+uint(raw,at);size=uint(raw,topics)
        if size>4:raise ValueError('Malformed test topics')
        emitter=uint(raw,at+64)
        if emitter>=1<<160:raise ValueError('Malformed test emitter')
        result.append(dict(address='0x'+format(emitter,'040x'),
            topics=['0x'+raw[topics+32+32*k:topics+64+32*k].hex() for k in range(size)],
            data='0x'+dynamic(raw,at+uint(raw,at+32)).hex()))
    return result

def frames():
    value=json.loads(FIXTURE.read_bytes());result=[]
    for row in value['raw_logs']:
        if row['topics'][0]!=WIRE:continue
        raw=bytes.fromhex(row['data'][2:]);captured=logs(dynamic(raw,uint(raw,0)));snapshot=dynamic(raw,uint(raw,32))
        if len(snapshot)!=26*32:raise ValueError('Malformed literal getter snapshot')
        words=[uint(snapshot,i*32) for i in range(26)]
        result.append((int(row['topics'][1],16),captured,words))
    return result

def model_for(selected=None):
    snapshot=frames()[0][2];addr=lambda i:'0x'+format(snapshot[i],'040x')
    roles={role:addr(i) for i,role in enumerate(('nft','vault','membership','rewards','fees'))}
    raw=json.loads(FIXTURE.read_bytes())['raw_logs']
    ledgers={r['address'] for r in raw if r['topics'][0]==ROYALTY_ADDED}
    if len(ledgers)!=1:raise ValueError('Ambiguous actual royalty constructor emitter')
    roles['royalties']=next(iter(ledgers))
    model=ExactReplay(104,snapshot[6] if selected is None else selected)
    model.begin(roles,[ZERO,addr(5)],[ZERO],fee_intake_version=1,royalty_settlement_version=4)
    # The 13 literal constructor/config logs predate recordLogs stage0. Preserve
    # the real royalty currency/cohort events; never seed invented zero weights.
    first=frames()[0][1][0];index=raw.index(first)
    for i,row in enumerate(raw[:index]):
        model(row['address'],row['topics'],row['data'],1,'0x'+format(1,'064x'),99,
            '0x'+format(9,'064x'),i)
    return model

def apply(model,stage,records):
    for i,row in enumerate(records):
        model(row['address'],row['topics'],row['data'],stage+1,'0x'+format(stage+1,'064x'),100+stage,
            '0x'+format(stage+11,'064x'),i)
    model.finish()

def actual_state(model,w):
    identifier,bucket=w[6],w[7];zzz='0x'+format(w[5],'040x')
    return [*model.components(identifier,ZERO),*model.components(identifier,zzz),
        model.owner_trees[bucket].total,*model.owner_trees[bucket].outstanding,
        model.collective_tree.total,*model.collective_tree.outstanding,
        model.direct_liability(ZERO),model.direct_liability(zzz),
        sum(sum(model.components(i,ZERO)) for i in model.mints),
        sum(sum(model.components(i,zzz)) for i in model.mints)]


class ExactLPSourceWireTests(unittest.TestCase):
    def test_actual_source_bytes_closure_and_four_recorded_frames_are_frozen(self):
        raw=FIXTURE.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),FIXTURE_SHA256)
        fixture=json.loads(raw);self.assertEqual(fixture['status'],'Success')
        self.assertEqual(len(fixture['raw_logs']),77);self.assertEqual(len(fixture['complete_raw_closure']),95)
        for name,digest in fixture['complete_raw_closure'].items():
            if name.startswith('src/'):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        self.assertEqual([stage for stage,_,_ in frames()],[0,1,2,3])
        self.assertEqual(sum(len(rows) for _,rows,_ in frames()),60)
        self.assertIn('syntheticnativevenue',fixture['actual_production_boundary'])

    def test_actual_vault_enrollment_harvest_growth_and_claim_match_literal_getters(self):
        model=model_for();paid={};before_growth=None
        for stage,rows,w in frames():
            apply(model,stage,rows)
            self.assertEqual(actual_state(model,w),w[12:26])
            self.assertEqual(model.shares[w[6]],(w[7],w[8]));self.assertEqual(model.ordinals[w[6]],w[11])
            self.assertEqual(len(model.members),w[9])
            if stage==1:before_growth=(model.components(w[6],ZERO),model.components(w[6],'0x'+format(w[5],'040x')))
            if stage==2:
                self.assertEqual(before_growth,(model.components(w[6],ZERO),model.components(w[6],'0x'+format(w[5],'040x'))))
                dormant=next(i for i in model.mints if i!=w[6])
                self.assertEqual((0,0),model.components(dormant,ZERO));self.assertNotIn(dormant,model.members)
            for row in rows:
                if row['topics'][0]==CLAIM:
                    currency='0x'+row['topics'][2][-40:];paid[currency]=paid.get(currency,0)+int(row['data'],16)
        last=frames()[-1][2];zzz='0x'+format(last[5],'040x')
        self.assertEqual(paid,{ZERO:18,zzz:18})
        for currency in (ZERO,zzz):
            self.assertEqual(model.account_totals[last[6]]['lp_individual',currency],16)
            self.assertEqual(model.account_totals[last[6]]['lp_collective',currency],2)
            self.assertEqual(model.totals['lp_compounding_allocated',currency],1)
            self.assertEqual(model.totals['lp_buyback_allocated',currency],1)

    def test_removed_actual_ack_and_wrong_real_sync_denominator_reject(self):
        stage,original,_=frames()[0]
        for variant in ('missing_ack','total'):
            rows=copy.deepcopy(original)
            if variant=='missing_ack':rows=[row for row in rows if row['topics'][0]!=ACK]
            else:
                row=next(row for row in rows if row['topics'][0]==SYNC)
                old=row['data'];row['data']=old[:-64]+format(int(old[-64:],16)+1,'064x')
            with self.subTest(variant=variant),self.assertRaises(HistoryError):apply(model_for(),stage,rows)

    def test_changed_actual_claim_or_getter_component_cannot_match(self):
        model=model_for()
        for stage,rows,_ in frames()[:3]:apply(model,stage,rows)
        stage,rows,w=copy.deepcopy(frames()[-1]);row=next(row for row in rows if row['topics'][0]==CLAIM)
        row['data']='0x'+format(17,'064x')
        with self.assertRaises(HistoryError):apply(model,stage,rows)
        model=model_for()
        for stage,rows,w in frames()[:2]:apply(model,stage,rows)
        wrong=w[12:26];wrong[0]-=1;wrong[1]+=1
        self.assertNotEqual(actual_state(model,w),wrong)

if __name__=='__main__':unittest.main()
