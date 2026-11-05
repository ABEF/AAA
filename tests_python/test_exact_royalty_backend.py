"""Independent exact-unit royalty replay and current checkpoint integration.

No public RPC, signing, running service, existing database or wallet is used.
"""
from collections import defaultdict
import copy
import json
from math import gcd
from itertools import product
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api.earnings import Earnings
from frontend_api.earnings_checkpoint import decode, encode, SHARED
from frontend_api.earnings_replay import Replay, SCALE, ticket_amount
from frontend_api.history import HistoryError, ZERO
from frontend_api.royalty_reporting import Reporting
from frontend_api.service import ProjectionError
from frontend_api.service import Projection
from tests_python import test_royalty_backend_audit as previous
from tests_python import test_portfolio_lineage_admission as lineage_fixtures
from tests_python.test_earnings import event, consume, activate, ROLES
from tests_python.test_frontend_api import addr
from zzz_ops.abi import calldata, keccak256


def tickets(order, weights):
    return [identifier for identifier in order for _ in range(weights[identifier])]


def independent(amount, order, weights, cursor):
    unit=gcd(*weights.values())
    normalized={identifier:weight//unit for identifier,weight in weights.items()}
    owners = tickets(order, normalized)
    q, r = divmod(amount, len(owners))
    paid = {identifier: q*weight for identifier, weight in normalized.items()}
    for n in range(r):
        paid[owners[(cursor//unit+n) % len(owners)]] += 1
    return paid, ((cursor//unit+r) % len(owners))*unit


class ExactReplayTests(unittest.TestCase):
    def model(self, order=(22,11,33), weights=(2,1,3), *, track_all=True, version=4):
        m = Replay(100000,track_all=track_all,nft_id=None if track_all else 11)
        m.begin(ROLES,[addr(20)],[ZERO,addr(21)],royalty_settlement_version=version)
        for n,a in enumerate((ZERO,addr(21))):consume(m,event('royalties','AssetAdded',(a,),(0,),10,n))
        consume(m,event('royalties','MintEndConfigured',(),(1000,4600),10,2))
        for n,i in enumerate(sorted(set(order)|{11,22,33})):
            consume(m,event('nft','Transfer',(ZERO,addr(30+n%30),i),(),11+n))
        for n,(i,w) in enumerate(zip(order,weights)):
            activate(m,i,100,w,20+n)
        return m

    def open(self,m,amount=0,asset=ZERO,block=30):
        count=len(m.activation_order);weight=sum(m.weights.values())
        consume(m,event('royalties','RoyaltyOpeningFinalized',(),(4600,count,weight),block),timestamp=5000)
        if amount:
            consume(m,event('royalties','RoyaltiesReceived',(asset,),(amount,0),block,1),timestamp=5000)
            self.credit(m,asset,amount,block,2,timestamp=5000)
        consume(m,event('royalties','InitialRoyaltiesAllocated',(asset,),(amount,count,weight),block,3),timestamp=5000)

    def credit(self,m,asset,amount,block,index=0,*,timestamp=6000):
        cohort=m.cohorts[asset];supply=sum(m.weights[i] for i in cohort)
        unit=gcd(*(m.weights[i] for i in cohort))
        cursor=m.royalty_cursors[asset]
        consume(m,event('royalties','RoyaltiesAllocated',(asset,),
            (amount,len(cohort),supply,cursor,((cursor//unit+amount%(supply//unit))%(supply//unit))*unit),block,index),timestamp=timestamp)

    def receipt(self,m,asset,amount,block,*,timestamp=6000):
        self.credit(m,asset,amount,block,timestamp=timestamp)
        consume(m,event('royalties','RoyaltiesReceived',(asset,),(amount,1),block,1),timestamp=timestamp)

    def activate_late(self,m,identifier,weight,block,*,deferred=False,timestamp=6000):
        rows=[event('membership','MembershipActivated',(identifier,),(),block)]
        if deferred:rows.append(event('royalties','RoyaltyAssetDeferred',(identifier,addr(21)),(),block,1))
        rows += [event('royalties','Activated',(identifier,),(weight,),block,2),
                 event('vault','SharesAdded',(identifier,5),(100,100),block,3)]
        for row in rows:consume(m,row,timestamp=timestamp)

    def test_every_smallest_unit_is_earned_for_indivisible_receipts_and_weights(self):
        for weights in ((1,1,1),(1,2,3),(3,3,3),(2,2,2)):
            for amount in (1,2,5,7,13,101,2**256-1):
                m=self.model(weights=weights);self.open(m,amount)
                expected,cursor=independent(amount,m.activation_order,m.weights,0)
                actual={i:m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order}
                self.assertEqual(actual,expected)
                self.assertEqual(sum(actual.values()),amount)
                self.assertEqual(m.royalty_cursors[ZERO],cursor)
                self.assertTrue(all(v%SCALE==0 for account in m.accounts.values() for k,v in account.items() if k[0]=='royalties'))

    def test_split_receipts_and_one_combined_receipt_have_identical_final_entitlements(self):
        split=self.model();self.open(split,0)
        for n in range(17):self.receipt(split,ZERO,1,40+n)
        combined=self.model();self.open(combined,17)
        self.assertEqual(dict(split.accounts),dict(combined.accounts))
        self.assertEqual(split.royalty_cursors[ZERO],combined.royalty_cursors[ZERO])
        self.assertEqual(split.totals['royalties_allocated',ZERO],17)
        self.assertEqual(split.totals['royalties_received',ZERO],17)

    def test_three_equal_legendary_nfts_receive_one_unit_each_from_three_units(self):
        m=self.model(weights=(3,3,3));self.open(m,3)
        self.assertEqual([m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order],[1,1,1])
        self.assertEqual(m.royalty_cursors[ZERO],0)

    def test100_equal_legendary_nfts_receive_one_unit_each_from100_units(self):
        m=Replay(100000,track_all=True)
        m.begin(ROLES,[addr(20)],[ZERO],royalty_settlement_version=4)
        consume(m,event('royalties','AssetAdded',(ZERO,),(0,),10))
        consume(m,event('royalties','MintEndConfigured',(),(1000,4600),10,1))
        for n in range(100):
            consume(m,event('nft','Transfer',(ZERO,addr(30+n%37),n+1),(),11,n),timestamp=902)
        for n in range(100):activate(m,n+1,100,3,12+n)
        self.open(m,100,block=120)
        self.assertEqual([m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order],[1]*100)

    def test_all_integral_ideal_shares_are_exact_and_every_raw_unit_is_conserved(self):
        for length in range(1,5):
            for weights in product((1,2,3),repeat=length):
                unit=gcd(*weights);supply=sum(weights)
                for amount in range(1,33):
                    for cursor in {0,unit if unit<supply else 0,supply-unit}:
                        paid=[];start=0
                        for weight in weights:
                            paid.append(ticket_amount(amount,supply,cursor,start,weight,unit=unit));start+=weight
                        self.assertEqual(sum(paid),amount)
                        if all(amount*weight%supply==0 for weight in weights):
                            self.assertEqual(paid,[amount*weight//supply for weight in weights])

    def test_late_activation_cannot_take_initial_units_or_get_weight_twice(self):
        m=self.model(order=(11,22),weights=(1,2));self.open(m,2)
        self.activate_late(m,33,3,41)
        prior={i:m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order}
        self.assertEqual(prior[33],0)
        expected,cursor=independent(5,m.activation_order,m.weights,m.royalty_cursors[ZERO])
        self.receipt(m,ZERO,5,50)
        self.assertEqual({i:m.accounts[i]['royalties',ZERO]//SCALE-prior[i] for i in m.activation_order},expected)
        self.assertEqual(m.royalty_cursors[ZERO],cursor)

    def test_deferred_currency_settles_old_prefix_before_new_member_receives_future_units(self):
        m=self.model(order=(11,22),weights=(1,2));self.open(m,0)
        consume(m,event('royalties','InitialRoyaltiesAllocated',(addr(21),),(0,2,3),31),timestamp=5001)
        self.activate_late(m,33,3,41,deferred=True)
        self.receipt(m,addr(21),2,50)
        self.assertEqual(m.accounts[33]['royalties',addr(21)],0)
        consume(m,event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(3,3),50,2),timestamp=6000)
        before={i:m.accounts[i]['royalties',addr(21)]//SCALE for i in m.activation_order}
        expected,_=independent(7,m.activation_order,m.weights,m.royalty_cursors[addr(21)])
        self.receipt(m,addr(21),7,51,timestamp=6001)
        self.assertEqual({i:m.accounts[i]['royalties',addr(21)]//SCALE-before[i] for i in m.activation_order},expected)

    def test_deferred_prefix_gcd_changes_only_after_old_receipts_are_allocated(self):
        m=self.model(order=(11,),weights=(3,));self.open(m,0)
        consume(m,event('royalties','InitialRoyaltiesAllocated',(addr(21),),(0,1,3),31),timestamp=5001)
        self.activate_late(m,22,2,41,deferred=True)
        self.receipt(m,addr(21),2,50)
        self.assertEqual(m.accounts[11]['royalties',addr(21)]//SCALE,2)
        self.assertEqual(m.accounts[22]['royalties',addr(21)],0)
        consume(m,event('royalties','RoyaltyEligibilityRecovered',(addr(21),),(2,2),50,2),timestamp=6000)
        self.receipt(m,addr(21),5,51,timestamp=6001)
        self.assertEqual(m.accounts[11]['royalties',addr(21)]//SCALE,5)
        self.assertEqual(m.accounts[22]['royalties',addr(21)]//SCALE,2)

    def test_unallocated_recovery_and_initial_markers_do_not_double_count_income(self):
        m=self.model();self.open(m,7)
        self.credit(m,ZERO,11,40)
        consume(m,event('royalties','UnallocatedRoyaltiesAllocated',(ZERO,),(11,6,1),40,1),timestamp=6000)
        self.assertEqual(m.totals['royalties_allocated',ZERO],18)
        self.assertEqual(m.totals['royalties_recovered',ZERO],11)
        self.assertEqual(m.totals['royalties_received',ZERO],7)
        self.assertEqual(sum(m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order),18)

    def test_new_credit_rejects_historical_profile_bad_cursor_and_unmatched_acknowledgement(self):
        old=self.model(version=3)
        with self.assertRaisesRegex(HistoryError,'historical'):
            self.credit(old,ZERO,1,40)
        for data in ((1,3,6,1,2),(1,2,6,0,1),(1,3,5,0,1),(1,3,6,0,2)):
            m=self.model();self.open(m,0)
            with self.assertRaises(HistoryError):
                consume(m,event('royalties','RoyaltiesAllocated',(ZERO,),data,40),timestamp=6000)
        m=self.model();self.open(m,0);self.credit(m,ZERO,1,40)
        with self.assertRaisesRegex(HistoryError,'Incomplete'):
            m.finish()
        with self.assertRaisesRegex(HistoryError,'receipt'):
            consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(2,1),40,1),timestamp=6000)

    def test_zero_telemetry_cannot_acknowledge_a_positive_exact_credit(self):
        m=self.model();self.open(m,0)
        consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(0,1),40),timestamp=6000)
        self.assertEqual(m.totals['royalties_allocated',ZERO],0)
        self.credit(m,ZERO,1,41)
        with self.assertRaisesRegex(HistoryError,'unmatched'):
            consume(m,event('royalties','RoyaltiesReceived',(ZERO,),(0,1),41,1),timestamp=6000)

    def test_v8_replacement_preserves_non_mint_activation_order_and_rotation(self):
        m=self.model();self.open(m,7)
        consume(m,event('royalties','InitialRoyaltiesAllocated',(addr(21),),(0,3,6),31),timestamp=5001)
        consume(m,event('handoff','Frozen',(1,addr(1)),(),40),timestamp=6000)
        consume(m,event('handoff','Retired',(1,addr(1)),(2,),41),timestamp=6001)
        starts=dict(m.ticket_offsets);cursor=m.royalty_cursors[ZERO]
        activation=event('handoff','Activated',(1,addr(1)),(2,),50)
        lower=(50,activation['transactionHash'],activation['topics'][1],'0x'+activation['data'][2:])
        m.begin(ROLES,[addr(20)],[ZERO,addr(21)],lower,royalty_settlement_version=4)
        consume(m,activation,timestamp=7000)
        self.assertEqual(m.activation_order,[22,11,33])
        self.assertEqual(m.ticket_offsets,starts)
        self.assertEqual(m.royalty_cursors[ZERO],cursor)
        self.receipt(m,ZERO,5,51,timestamp=7001)
        self.assertEqual(sum(m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order),12)

    def test_full1000_nft_quota_cohort_conserves_indivisible_units(self):
        m=Replay(100000,track_all=True)
        m.begin(ROLES,[addr(20)],[ZERO],royalty_settlement_version=4)
        consume(m,event('royalties','AssetAdded',(ZERO,),(0,),10))
        consume(m,event('royalties','MintEndConfigured',(),(1000,4600),10,1))
        for n in range(1000):
            consume(m,event('nft','Transfer',(ZERO,addr(30+n%37),n+1),(),11,n),timestamp=902)
        for n in range(1000):
            w=1 if n<600 else 2 if n<900 else 3
            activate(m,n+1,5+n,w,12+n)
        self.open(m,1009,block=1100)
        self.assertEqual(len(m.accounts),1000)
        self.assertEqual(sum(m.weights.values()),1500)
        self.assertEqual(sum(m.accounts[i]['royalties',ZERO]//SCALE for i in m.activation_order),1009)


class ExactCheckpointTests(unittest.TestCase):
    def setUp(self):
        base=previous.RoyaltyOpeningCheckpointTests('runTest');base.setUp()
        self.addCleanup(base.doCleanups);self.f=base.f
        f=self.f;f.config['royalty_reporting']={'schema':5,'converter':None}
        f.put(addr(5),'ROYALTY_SETTLEMENT_VERSION()',values=(4,))
        f.put(f.c['handoff'],'SCHEMA()',values=('0x'+keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_ROYALTIES_V8').hex(),))
        for a in (ZERO,addr(21)):f.put(addr(5),'allocationCursor(address)',(a,),(0,))
        for i in (f.i,f.j):f.put(addr(5),'ticketStart(uint256)',(i,),(1 if i==f.i else 0,))
        with f.index.db:f.index.db.execute('DELETE FROM logs WHERE address=? AND block_number=21 AND log_index>=2',(addr(5),))
        for ev in (
            event('royalties','RoyaltiesAllocated',(ZERO,),(100,1,1,0,0),21,2),
            event('royalties','InitialRoyaltiesAllocated',(ZERO,),(100,1,1),21,3),
            event('royalties','InitialRoyaltiesAllocated',(addr(21),),(0,1,1),21,4),
        ):f.insert(ev)

    def test_exact_checkpoint_suffix_and_full_replay_agree_without_removed_getters(self):
        f=self.f;original=self.f.inner.call
        removed={calldata('SCALE()')[:10],calldata('index(address)',addr(1))[:10]}
        def no_old_getters(method,params=None):
            if method=='eth_call' and params[0]['to']==addr(5) and params[0]['data'][:10] in removed:
                raise AssertionError('Fresh4 reader attempted a removed scaled-index getter')
            return original(method,params)
        with patch.object(f.inner,'call',side_effect=no_old_getters):
            f.install()
            for ev in (
                event('rewards','PoolRewardsCredited',(5,addr(20)),(160,20),40),
                event('fees','FeesAllocated',(5,addr(20)),(200,0),40,1),
                event('royalties','RoyaltiesAllocated',(ZERO,),(200,1,1,0,0),41),
                event('royalties','RoyaltiesReceived',(ZERO,),(200,1),41,1),
            ):f.insert(ev)
            f.set_earnings(240,30,300)
            full=copy.deepcopy(f.config);del full['earnings_history']['checkpoint']
            for identifier in (None,str(f.i),str(f.j)):
                seeded=f.projection().earnings(identifier);raw=f.projection(full).earnings(identifier)
                self.assertEqual(seeded['all_time'],raw['all_time'])
                self.assertEqual(seeded['last_24h'],raw['last_24h'])
            state=decode(json.loads(self.f.candidate(41))['state'])
            self.assertEqual(state['shared']['royalty_settlement_version'],4)
            self.assertIn('royalty_cursors',SHARED)

    def test_checkpoint_rejects_wrong_exact_cursor_or_ticket_ownership(self):
        for sig,args,value in [('allocationCursor(address)',(ZERO,),1),('ticketStart(uint256)',(self.f.i,),2)]:
            f=self.f;f.put(addr(5),sig,args,(value,))
            with self.assertRaisesRegex(HistoryError,'cursor|ticket'):
                f.candidate()
            f.put(addr(5),sig,args,(1 if sig=='ticketStart(uint256)' else 0,))

    def test_reapproved_exact_checkpoint_cannot_invent_fractional_royalty_rights(self):
        data=json.loads(self.f.candidate())
        state=decode(data['state'])
        state['accounts'][self.f.i]['royalties',ZERO]+=1
        data['state']=encode(state)
        self.f.install(json.dumps(data).encode(),name='fractional.json')
        with self.assertRaisesRegex(HistoryError,'fractional'):
            self.f.projection()


class ExactPendingTests(unittest.TestCase):
    def test_pending_preview_uses_the_current_rotating_cursor_not_a_floor(self):
        for identifier,start,weight,expected in [(11,0,1,0),(22,1,2,1),(33,3,3,0)]:
            model=SimpleNamespace(nft_id=identifier,weights={11:1,22:2,33:3},cohorts={ZERO:{11,22,33}},
                activation_order=[11,22,33],royalty_opening=(4600,3,6),initial_royalty_allocations={ZERO},
                ticket_offsets={11:0,22:1,33:3},royalty_cursors={ZERO:2},totals=defaultdict(int),scaled=defaultdict(int))
            amounts={'pending(address)':1,'claimable(uint256,address)':expected}
            p=SimpleNamespace(royalty_reporting=SimpleNamespace(schema=5),contracts={'royalties':SimpleNamespace(address=addr(5))},
                _uint=lambda role,sig,*a,**kw:amounts[sig],_call=lambda *a,**kw:['0'*63+'1'])
            financial={'previously_claimed':{'assets':[{'asset':ZERO,'lp_raw':'0','royalties_raw':'0'}]},
                'royalty_conversions':{'assets':[],'total_eth_credited_raw':'0'},
                'lp_conversions':{'assets':[],'total_eth_credited_raw':'0'}}
            Earnings.check_paid(p,model,financial,{},[],[ZERO])

    def test_pending_preview_preserves_integral_equal_legendary_entitlements(self):
        for identifier in (11,22,33):
            model=SimpleNamespace(nft_id=identifier,weights={11:3,22:3,33:3},cohorts={ZERO:{11,22,33}},
                activation_order=[11,22,33],royalty_opening=(4600,3,9),initial_royalty_allocations={ZERO},
                ticket_offsets={11:0,22:3,33:6},royalty_cursors={ZERO:0},totals=defaultdict(int),scaled=defaultdict(int))
            amounts={'pending(address)':3,'claimable(uint256,address)':1}
            p=SimpleNamespace(royalty_reporting=SimpleNamespace(schema=5),contracts={'royalties':SimpleNamespace(address=addr(5))},
                _uint=lambda role,sig,*a,**kw:amounts[sig],_call=lambda *a,**kw:['0'*63+'1'])
            financial={'previously_claimed':{'assets':[{'asset':ZERO,'lp_raw':'0','royalties_raw':'0'}]},
                'royalty_conversions':{'assets':[],'total_eth_credited_raw':'0'},
                'lp_conversions':{'assets':[],'total_eth_credited_raw':'0'}}
            Earnings.check_paid(p,model,financial,{},[],[ZERO])


class ExactReportingTests(unittest.TestCase):
    def fixture(self):
        ints={'ROYALTY_SETTLEMENT_VERSION()':4,'mintEnd()':1200,'royaltiesOpenAt()':4800,
              'activationCount()':3,'activationOrdinal(uint256)':2,'ticketStart(uint256)':2,'totalWeight()':6}
        def read(role,sig,*args,**kw):
            if sig=='effectiveEligibleCount(address)':return 3 if args[0]==ZERO else 1
            if sig=='eligibleWeight(address)':return 6 if args[0]==ZERO else 1
            if sig=='allocationCursor(address)':return 5 if args[0]==ZERO else 0
            if sig=='claimable(uint256,address)':return 7 if args[1]==ZERO else 0
            return ints[sig]
        def call(target,sig,*args,**kw):
            result=1 if sig=='royaltiesOpen()' or sig=='eligibleFor(uint256,address)' and args[1]==ZERO else 0
            return [f'{result:064x}']
        p=SimpleNamespace(accounting_version=6,assets={ZERO:SimpleNamespace(symbol='ETH',decimals=18),
            addr(21):SimpleNamespace(symbol='USDC',decimals=6)},contracts={'royalties':SimpleNamespace(address=addr(5)),
            'access':SimpleNamespace(address=addr(1))},_uint=read,_call=call,_addr=lambda *a,**kw:addr(1))
        return p,ints

    def test_reporting5_preserves_exact_currency_eligibility_and_ticket_identity(self):
        p,_=self.fixture()
        value=Reporting({'schema':5,'converter':None},p).read(22,2,[ZERO,addr(21)],{ZERO:True,addr(21):True},{},timestamp=4800)
        self.assertEqual(value['ticket_start'],2)
        self.assertEqual(value['allocation_method'],'whole_unit_rotating_tickets')
        self.assertEqual(value['balances'][0]['raw'],'7')
        self.assertEqual(value['balances'][0]['allocation_cursor'],5)
        self.assertEqual(value['balances'][1]['eligibility'],'deferred')
        self.assertFalse(value['balances'][1]['conversion_required'])

    def test_source_one_based_ticket_starts_are_not_zero_based_internal_offsets(self):
        for identifier,ordinal,start,weight in ((30,1,1,3),(10,2,4,2),(20,3,6,1)):
            p,ints=self.fixture()
            ints['activationOrdinal(uint256)']=ordinal
            ints['ticketStart(uint256)']=start
            value=Reporting({'schema':5,'converter':None},p).read(identifier,weight,[ZERO],{ZERO:True},{},timestamp=4800)
            self.assertEqual(value['ticket_start'],start)
        p,ints=self.fixture();ints['activationOrdinal(uint256)']=1;ints['ticketStart(uint256)']=0
        with self.assertRaisesRegex(ProjectionError,'ticket'):
            Reporting({'schema':5,'converter':None},p).read(30,3,[ZERO],{ZERO:True},{},timestamp=4800)

    def test_reporting5_rejects_old_capability_or_invalid_ticket_identity(self):
        for sig,value in [('ROYALTY_SETTLEMENT_VERSION()',3),('ticketStart(uint256)',6)]:
            p,ints=self.fixture();ints[sig]=value
            with self.assertRaises(ProjectionError):
                Reporting({'schema':5,'converter':None},p).read(22,2,[ZERO],{ZERO:True},{},timestamp=4800)
        p,_=self.fixture();p.accounting_version=5
        with self.assertRaisesRegex(ValueError,'accounting6'):
            Reporting({'schema':5,'converter':None},p)


class ExactLineageAdmissionTests(unittest.TestCase):
    def test_each_v8_peer_requires_its_own_explicit_matching_royalty_profile(self):
        config,rpc=lineage_fixtures.configuration(6)
        config['royalty_reporting']={'schema':5,'converter':None}
        with self.assertRaises(ValueError):Projection(config,rpc,clock=lambda:1000)
        config['predecessors'][0]['royalty_reporting']={'schema':4,'converter':None}
        with self.assertRaisesRegex(ValueError,'matching royalty'):
            Projection(config,rpc,clock=lambda:1000)
        config['predecessors'][0]['royalty_reporting']={'schema':5,'converter':None}
        p=Projection(config,rpc,clock=lambda:1000)
        self.assertEqual(p.lineage.entries[0].projection.royalty_reporting.schema,5)

    def test_malformed_peer_input_is_rejected_without_implicit_profile_adoption(self):
        config,rpc=lineage_fixtures.configuration(6)
        config['royalty_reporting']={'schema':5,'converter':None}
        config['predecessors']=[None]
        with self.assertRaises(ValueError):Projection(config,rpc,clock=lambda:1000)


if __name__=='__main__':unittest.main()
