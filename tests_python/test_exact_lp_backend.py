"""Fresh accounting7 exact LP math/events; historical index handlers stay separate."""
import copy
from fractions import Fraction
import random
import unittest
from types import SimpleNamespace
from frontend_api.earnings import Earnings
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.history import HistoryError,ZERO
from indexer.events import decode
from zzz_ops.abi import keccak256
from zzz_ops.exact_lp import Tree,split,Q,UINT

ZZZ='0x'+'11'*20
ROLES={name:'0x'+f'{i:040x}' for i,name in enumerate(('nft','vault','membership','fees','rewards','royalties','handoff'),101)}
OWNER='0x'+'22'*20
OTHER='0x'+'33'*20
IDS=(2**255+1,2**255+2)


class Feed:
    def __init__(self,selected=IDS):
        self.roles=dict(ROLES)
        self.model=ExactReplay(10000,selected=selected)
        self.model.begin(self.roles,[ZERO,ZZZ],[ZERO],fee_intake_version=1,royalty_settlement_version=4)
        self.index=0;self.tx=1
        self.emit('royalties','AssetAdded(address,uint256)',[ZERO],[0])

    def emit(self,role,signature,indexed,data):
        self.index+=1
        def word(v):return f'{int(v,16) if isinstance(v,str) else v:064x}'
        topics=['0x'+keccak256(signature.encode()).hex()]+['0x'+word(v) for v in indexed]
        raw='0x'+''.join(word(v) for v in data)
        self.model(self.roles[role],topics,raw,1,'0x'+'aa'*32,100,'0x'+f'{self.tx:064x}',self.index)
        return {'topics':topics,'data':raw}

    def mint(self,identifier):self.emit('nft','Transfer(address,address,uint256)',[ZERO,OWNER,identifier],[])

    def activate(self,identifier,shares,bucket=7):
        previous=self.model.supply[bucket];ordinal=self.model.ordinals[identifier]
        self.emit('rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',[identifier,bucket],
            [ordinal,0,shares,previous+shares])
        self.emit('rewards','CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)',[identifier],
            [ordinal,0,1,len(self.model.members)+1])
        self.emit('membership','MembershipActivated(uint256)',[identifier],[])
        self.emit('royalties','Activated(uint256,uint256)',[identifier],[1])
        self.emit('vault','SharesAdded(uint256,uint256,uint256,uint256)',[identifier,bucket],[shares,100*10**18])

    def grow(self,identifier,delta):
        bucket,previous=self.model.shares[identifier];ordinal=self.model.ordinals[identifier]
        self.emit('rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',[identifier,bucket],
            [ordinal,previous,previous+delta,self.model.supply[bucket]+delta])
        self.emit('vault','SharesAdded(uint256,uint256,uint256,uint256)',[identifier,bucket],[delta,5*10**18])

    def fees(self,asset=ZERO,bucket=7,units=1):
        self.tx+=1
        self.emit('rewards','PoolRewardsCredited(uint256,address,uint256,uint256)',[bucket,asset],[16*units,2*units])
        self.emit('fees','FeesAllocated(uint256,address,uint256,uint256)',[bucket,asset],[20*units,0])


class ExactLPBackendTests(unittest.TestCase):
    def test_high_low_split_matches_independent_fraction_including_uintmax(self):
        rng=random.Random(719)
        for _ in range(64):
            total=rng.randrange(1,UINT+1);left=rng.randrange(total+1)
            amount=rng.randrange(UINT+1);high=rng.randrange(Q);low=rng.randrange(total)
            exact=Fraction(amount*left,total)+Fraction(high,Q)+Fraction(low,Q*total)
            whole=exact.numerator//exact.denominator;phase=exact-whole
            expected_high=int(phase*Q);remaining=phase*Q-expected_high
            expected_low=int(remaining*total)
            self.assertEqual((whole,amount-whole,expected_high,expected_low),split(amount,left,total,high,low))

    def test_actual_receipt_components_final_unit_and_claim_conservation(self):
        f=Feed((IDS[0],));f.mint(IDS[0]);f.activate(IDS[0],101)
        for asset in (ZERO,ZZZ):
            f.fees(asset);self.assertEqual((16,2),f.model.components(IDS[0],asset))
            f.emit('rewards','Claimed(uint256,address,address,uint256)',[IDS[0],asset,OWNER],[18])
            self.assertEqual((0,0),f.model.components(IDS[0],asset))
            self.assertEqual(0,f.model.owner_trees[7].outstanding[f.model.pair.index(asset)])
        f.model.finish()
        self.assertEqual(16,f.model.account_totals[IDS[0]]['lp_individual',ZERO])
        self.assertEqual(2,f.model.account_totals[IDS[0]]['lp_collective',ZERO])

    def test_growth_and_late_activation_preserve_old_currency_entitlements(self):
        f=Feed();f.mint(IDS[0]);f.mint(IDS[1]);f.activate(IDS[0],101)
        f.fees(ZERO);f.fees(ZZZ)
        f.activate(IDS[1],1000);f.grow(IDS[0],99)
        self.assertEqual((0,0),f.model.components(IDS[1],ZERO))
        self.assertEqual((16,2),f.model.components(IDS[0],ZERO))
        self.assertEqual((16,2),f.model.components(IDS[0],ZZZ))
        f.fees(ZERO);f.model.finish()
        self.assertEqual(36,sum(sum(f.model.components(i,ZERO)) for i in IDS))

    def test_individual_buckets_and_global_collective_remain_distinct(self):
        f=Feed();[f.mint(i) for i in IDS];f.activate(IDS[0],1,7);f.activate(IDS[1],1000,8)
        f.fees(ZERO,7)
        self.assertEqual((16,1),f.model.components(IDS[0],ZERO))
        self.assertEqual((0,1),f.model.components(IDS[1],ZERO));f.model.finish()

    def test_conversion_changes_backing_but_never_adds_income(self):
        f=Feed((IDS[0],));f.mint(IDS[0]);f.activate(IDS[0],101);f.fees(ZZZ)
        before=copy.deepcopy(f.model.account_totals)
        f.emit('rewards','LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',[IDS[0],ZZZ],[16,2,16,2])
        self.assertEqual((0,0),f.model.components(IDS[0],ZZZ))
        self.assertEqual((16,2),f.model.components(IDS[0],ZERO))
        self.assertEqual(18,f.model.direct_liability(ZERO));self.assertEqual(before,f.model.account_totals)
        f.emit('rewards','Claimed(uint256,address,address,uint256)',[IDS[0],ZERO,OWNER],[18])
        self.assertEqual(0,f.model.direct_liability(ZERO));self.assertEqual(before,f.model.account_totals)

    def test_claim_order_repeated_claims_and_transfer_callback_are_not_income(self):
        f=Feed();[f.mint(i) for i in IDS];f.activate(IDS[0],71);f.activate(IDS[1],30);f.fees()
        before=copy.deepcopy(f.model.account_totals)
        amounts={i:sum(f.model.components(i,ZERO)) for i in IDS}
        f.emit('nft','Transfer(address,address,uint256)',[OWNER,OTHER,IDS[0]],[])
        for identifier in reversed(IDS):
            f.emit('rewards','Claimed(uint256,address,address,uint256)',[identifier,ZERO,OWNER],[amounts[identifier]])
            f.emit('rewards','Claimed(uint256,address,address,uint256)',[identifier,ZERO,OTHER],[0])
        self.assertEqual(18,sum(amounts.values()));self.assertEqual(before,f.model.account_totals);f.model.finish()

    def test_missing_sync_or_wrong_ordinal_previous_and_total_reject(self):
        for variant in ('missing','ordinal','previous','total'):
            with self.subTest(variant=variant):
                f=Feed((IDS[0],));f.mint(IDS[0])
                with self.assertRaises(HistoryError):
                    if variant=='missing':f.emit('vault','SharesAdded(uint256,uint256,uint256,uint256)',[IDS[0],7],[101,100])
                    else:f.emit('rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',[IDS[0],7],
                        [2 if variant=='ordinal' else 1,1 if variant=='previous' else 0,101,102 if variant=='total' else 101])

    def test_sync_never_counts_twice_and_unacknowledged_sync_rejects(self):
        f=Feed((IDS[0],));f.mint(IDS[0])
        f.emit('rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',[IDS[0],7],[1,0,101,101])
        with self.assertRaises(HistoryError):f.model.finish()
        with self.assertRaises(HistoryError):f.emit('rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',[IDS[0],7],[1,0,101,101])

    def test_changed_claim_conversion_amount_and_third_currency_reject(self):
        for variant in ('claim','conversion','asset'):
            with self.subTest(variant=variant):
                f=Feed((IDS[0],));f.mint(IDS[0]);f.activate(IDS[0],101);f.fees(ZZZ)
                with self.assertRaises(HistoryError):
                    if variant=='claim':f.emit('rewards','Claimed(uint256,address,address,uint256)',[IDS[0],ZZZ,OWNER],[17])
                    elif variant=='conversion':f.emit('rewards','LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',[IDS[0],ZZZ],[15,3,16,2])
                    else:f.fees(OTHER)

    def test_indexer_decodes_exact_syncs_and_rejects_wrong_layout(self):
        f=Feed((IDS[0],));f.mint(IDS[0])
        raw=f.emit('rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',[IDS[0],7],[1,0,101,101])
        name,data=decode(raw);self.assertEqual('ShareWeightSynchronized',name);self.assertEqual('101',data['weight'])
        with self.assertRaises(ValueError):decode({**raw,'topics':raw['topics'][:-1]})

    def test_uintmax_zero_cohort_overflow_and_noop_are_bounded(self):
        tree=Tree()
        with self.assertRaises(ValueError):tree.credit(0,1)
        tree.set_weight(1,UINT);tree.credit(0,UINT);before=copy.deepcopy(tree.__dict__)
        tree.set_weight(1,UINT);self.assertEqual(before,tree.__dict__)
        with self.assertRaises(ValueError):tree.set_weight(2,1)
        with self.assertRaises(ValueError):tree.credit(0,1)
        self.assertEqual(UINT,tree.take(0,1));self.assertEqual([0,0],tree.outstanding)

    def test_reconciliation_checks_exact_components_and_totals_without_old_indices(self):
        f=Feed((IDS[0],));f.model.nft_id=IDS[0]
        f.mint(IDS[0]);f.activate(IDS[0],101);f.fees()
        access='0x'+'44'*20
        p=SimpleNamespace(accounting_version=7,fee_intake_version=1,royalty_reporting=SimpleNamespace(schema=5),
            contracts={r:SimpleNamespace(address=a) for r,a in dict(ROLES,access=access).items()})
        changed={}
        def call(target,signature,*args,**kwargs):
            if signature=='totalEligible()':values=(1,)
            elif signature=='dust(uint256,address)':values=(0,)
            elif signature=='allocationTree(uint256)':values=(101,16,0) if args[0]==7 else (1,2,0)
            elif signature=='claimableComponents(uint256,address)':values=(16,2) if args[1]==ZERO else (0,0)
            else:raise AssertionError('Unexpected or legacy exact LP getter '+signature)
            return [f'{x:064x}' for x in changed.get(signature,values)]
        def number(role,signature,*args,**kwargs):
            values={'bucketTotalShares(uint256)':101,'totalWeight()':1,'activationCount()':1,
                'allocationCursor(address)':0,'eligibleCount(address)':1,'eligibleWeight(address)':1,
                'sharesOf(uint256)':101,'nftBucket(uint256)':7,'rewardBucket(uint256)':7,'weightOf(uint256)':1,'ticketStart(uint256)':1,
                'directLiabilities(address)':0,'orphaned(address)':0}
            if signature=='liabilities(address)':return 18 if args[0]==ZERO else 0
            if signature not in values:raise AssertionError('Unexpected or legacy exact LP getter '+signature)
            return changed.get(signature,values[signature])
        p._call=call;p._uint=number
        engine=object.__new__(Earnings);engine.profiles={access:{r:SimpleNamespace(address=ROLES[r]) for r in ('fees','membership')}}
        engine.reconcile(p,f.model,{},[ZERO,ZZZ],[ZERO],1)
        changed['claimableComponents(uint256,address)']=(15,3)
        with self.assertRaises(HistoryError):engine.reconcile(p,f.model,{},[ZERO,ZZZ],[ZERO],1)
        changed.clear();changed['allocationTree(uint256)']=(100,16,0)
        with self.assertRaises(HistoryError):engine.reconcile(p,f.model,{},[ZERO,ZZZ],[ZERO],1)
        changed.clear();changed['rewardBucket(uint256)']=8
        with self.assertRaisesRegex(HistoryError,'bucket differs'):engine.reconcile(p,f.model,{},[ZERO,ZZZ],[ZERO],1)

    def test_same_v9_epoch_preserves_phase_and_does_not_recredit_imports(self):
        f=Feed((IDS[0],));f.mint(IDS[0]);f.activate(IDS[0],101);f.fees()
        handoff='0x'+f'{7:064x}';destination='0x'+'55'*20;root='0x'+f'{9:064x}'
        f.emit('handoff','Frozen(bytes32,address)',[handoff,destination],[])
        f.emit('handoff','Retired(bytes32,address,bytes32)',[handoff,destination],[root])
        f.model.finish();before=copy.deepcopy(f.model.account_totals)
        f.roles={r:'0x'+f'{i:040x}' for i,r in enumerate(ROLES,501)}
        f.model.begin(f.roles,[ZERO,ZZZ],[ZERO],(1,'0x'+f'{f.tx:064x}',handoff,root),fee_intake_version=1,royalty_settlement_version=4)
        f.emit('nft','Transfer(address,address,uint256)',[ZERO,OWNER,IDS[0]],[])
        f.emit('handoff','Activated(bytes32,address,bytes32)',[handoff,OTHER],[root])
        self.assertEqual(before,f.model.account_totals);self.assertEqual((16,2),f.model.components(IDS[0],ZERO))
        f.fees();f.model.finish();self.assertEqual((32,4),f.model.components(IDS[0],ZERO))


if __name__=='__main__':unittest.main()
