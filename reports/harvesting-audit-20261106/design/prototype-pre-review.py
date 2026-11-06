"""NONPRODUCTION design model: exact-unit hierarchical LP allocation.

This isolated prototype is not imported by production code. It establishes no
deployment, Solidity implementation, gas qualification or flat-proportional
fairness claim. Slots are immutable one-based mint ordinals, not ERC721 IDs.
The eager oracle deliberately uses the SAME declared hierarchical rounding rule.
"""
import copy
import random
import unittest


UINT256=(1<<256)-1
LEAVES=1024
MAX_NFTS=1000
ASSETS=('ETH','ZZZ')


def _uint(value):
    if type(value) is not int or not 0<=value<=UINT256:
        raise ValueError('uint256 required')
    return value


def _add(left,right):
    return _uint(_uint(left)+_uint(right))


def _split(amount,left,total,carry):
    """FullMath quotient/remainder model with overflow-safe carry addition."""
    for value in (amount,left,total,carry):_uint(value)
    if total==0 or left>total or carry>=total:raise ValueError('invalid node')
    # Solidity must use reviewed full-precision mulDiv/mulmod, not amount*left.
    quotient,remainder=divmod(amount*left,total)
    gap=total-carry
    if remainder>=gap:
        quotient=_add(quotient,1);remainder-=gap
    else:
        remainder=_add(remainder,carry)
    return quotient,amount-quotient,remainder


class _LazyTree:
    """Design only: root credit O(1), claim/update O(log1024) per admitted asset."""
    def __init__(self):
        self.weights=[0]*(2*LEAVES)
        self.books={asset:{'pending':[0]*(2*LEAVES),'carry':[0]*LEAVES,
            'liability':0,'credited':0,'paid':0} for asset in ASSETS}
        self.last_pushes=0

    @staticmethod
    def leaf(ordinal):
        if type(ordinal) is not int or not 1<=ordinal<=MAX_NFTS:
            raise ValueError('mint ordinal outside1..1000')
        return LEAVES+ordinal-1

    @classmethod
    def path(cls,ordinal):
        node=cls.leaf(ordinal);reverse=[]
        while node>1:
            node//=2;reverse.append(node)
        return list(reversed(reverse))

    def _push(self,asset,node):
        self.last_pushes+=1
        book=self.books[asset];amount=book['pending'][node]
        if not amount:return
        left,right,carry=_split(amount,self.weights[node*2],self.weights[node],book['carry'][node])
        new_left=_add(book['pending'][node*2],left)
        new_right=_add(book['pending'][node*2+1],right)
        book['pending'][node*2]=new_left;book['pending'][node*2+1]=new_right
        book['carry'][node]=carry;book['pending'][node]=0

    def set_weight(self,ordinal,weight):
        leaf=self.leaf(ordinal);_uint(weight)
        old=self.weights[leaf]
        # Validate total before changing any book. Solidity revert semantics are
        # still required if a later dependency or invariant fails in real code.
        _uint(self.weights[1]-old+weight)
        if old==weight:return
        path=self.path(ordinal);self.last_pushes=0
        for asset in ASSETS:
            for node in path:self._push(asset,node)
        self.weights[leaf]=weight
        for node in reversed(path):
            self.weights[node]=_add(self.weights[node*2],self.weights[node*2+1])
        # Old pending was assigned under old weights FIRST. Only subsequent
        # credit streams use the new denominator and reset fairness remainder.
        for asset in ASSETS:
            for node in path:self.books[asset]['carry'][node]=0

    def credit(self,asset,amount):
        _uint(amount);book=self.books[asset]
        if amount and self.weights[1]==0:raise ValueError('no eligible cohort')
        liability=_add(book['liability'],amount)
        pending=_add(book['pending'][1],amount)
        book['liability']=liability;book['pending'][1]=pending
        book['credited']+=amount  # test-only ghost total, not proposed storage
        self.last_pushes=0

    def claim(self,ordinal,asset):
        leaf=self.leaf(ordinal);self.last_pushes=0
        for node in self.path(ordinal):self._push(asset,node)
        book=self.books[asset];amount=book['pending'][leaf]
        book['pending'][leaf]=0;book['liability']-=amount;book['paid']+=amount
        return amount

    def balances(self,asset):
        # Materialize on a COPY: production claimable views must simulate their
        # path without modifying real allocation or paying the requested owner.
        snapshot=copy.deepcopy(self)
        return [snapshot.claim(i,asset) for i in range(1,MAX_NFTS+1)]

    def invariant(self):
        for asset,book in self.books.items():
            assert sum(book['pending'])==book['liability']
            assert book['credited']==book['paid']+book['liability']
            for node in range(1,LEAVES):
                assert self.weights[node]==self.weights[node*2]+self.weights[node*2+1]
                assert 0<=book['carry'][node]<max(1,self.weights[node])
            assert not any(book['pending'][LEAVES+MAX_NFTS:])


class _EagerReference:
    """Independent eager traversal via cumulative-left differences, no lazy push."""
    def __init__(self):
        self.weights=[0]*(2*LEAVES)
        self.balances={asset:[0]*(MAX_NFTS+1) for asset in ASSETS}
        self.stream={asset:{} for asset in ASSETS}

    def set_weight(self,ordinal,weight):
        node=_LazyTree.leaf(ordinal)
        self.weights[node]=weight
        while node>1:
            node//=2
            self.weights[node]=self.weights[node*2]+self.weights[node*2+1]
            for asset in ASSETS:self.stream[asset].pop(node,None)

    def credit(self,asset,amount):
        if amount and not self.weights[1]:raise ValueError('no eligible cohort')
        def distribute(node,amount):
            if not amount:return
            if node>=LEAVES:
                self.balances[asset][node-LEAVES+1]+=amount;return
            incoming,prior_left=self.stream[asset].get(node,(0,0))
            incoming+=amount
            total_left=(incoming*self.weights[node*2])//self.weights[node]
            left=total_left-prior_left
            self.stream[asset][node]=(incoming,total_left)
            distribute(node*2,left);distribute(node*2+1,amount-left)
        distribute(1,amount)

    def claim(self,ordinal,asset):
        amount=self.balances[asset][ordinal];self.balances[asset][ordinal]=0
        return amount


class _FeeDesign:
    """One-bucket model; membership equal, individual LP weights arbitrary shares."""
    def __init__(self):
        self.owner=_LazyTree();self.collective=_LazyTree();self.owners={}
        self.cash={};self.reserves={asset:[0,0,0] for asset in ASSETS}  # dust/compound/buyback
        self.received={asset:0 for asset in ASSETS}

    def activate(self,ordinal,shares,wallet):
        if ordinal in self.owners or shares<=0:raise ValueError('activation invalid')
        self.owner.set_weight(ordinal,shares);self.collective.set_weight(ordinal,1)
        self.owners[ordinal]=wallet

    def grow(self,ordinal,delta):
        if ordinal not in self.owners or delta<=0:raise ValueError('growth invalid')
        self.owner.set_weight(ordinal,self.owner.weights[self.owner.leaf(ordinal)]+delta)

    def harvest(self,asset,amount):
        if not self.owners:raise ValueError('no activated cohort')
        dust,compound,buyback=self.reserves[asset]
        units,remainder=divmod(dust+amount,20)
        self.owner.credit(asset,16*units);self.collective.credit(asset,2*units)
        self.reserves[asset]=[remainder,compound+units,buyback+units]
        self.received[asset]+=amount

    def claim(self,ordinal,asset,wallet):
        if self.owners.get(ordinal)!=wallet:raise ValueError('current owner only')
        amount=self.owner.claim(ordinal,asset)+self.collective.claim(ordinal,asset)
        self.cash[wallet,asset]=self.cash.get((wallet,asset),0)+amount
        return amount

    def invariant(self):
        self.owner.invariant();self.collective.invariant()
        for asset in ASSETS:
            holder_total=sum(amount for (wallet,currency),amount in self.cash.items() if currency==asset)
            pending=self.owner.books[asset]['liability']+self.collective.books[asset]['liability']
            assert self.received[asset]==holder_total+pending+sum(self.reserves[asset])


class ExactLPTreeDesignTests(unittest.TestCase):
    def paired(self,weights):
        lazy,eager=_LazyTree(),_EagerReference()
        for ordinal,weight in weights.items():
            lazy.set_weight(ordinal,weight);eager.set_weight(ordinal,weight)
        return lazy,eager

    def equal_reference(self,lazy,eager):
        lazy.invariant()
        for asset in ASSETS:
            self.assertEqual(eager.balances[asset][1:],lazy.balances(asset))

    def test_final_one_unit_with101_shares_is_fully_claimable(self):
        scale=10**27
        self.assertEqual(0,(101*(scale//101))//scale)  # current index counterexample
        tree=_LazyTree();tree.set_weight(1,101);tree.credit('ETH',1)
        self.assertEqual(1,tree.claim(1,'ETH'));self.assertEqual(0,tree.books['ETH']['liability'])
        tree.invariant()

    def test_split_matches_full_precision_without_unsafe_carry_overflow(self):
        total=UINT256;carry=UINT256-1;left=UINT256//2;amount=UINT256-1
        _,remainder=divmod(amount*left,total)
        self.assertGreater(remainder+carry,UINT256)
        expected,next_carry=divmod(amount*left+carry,total)
        self.assertEqual((expected,amount-expected,next_carry),_split(amount,left,total,carry))

    def test_empty_left_or_right_branch_routes_every_unit(self):
        for ordinal in (1,1000):
            tree=_LazyTree();tree.set_weight(ordinal,17);tree.credit('ZZZ',1)
            self.assertEqual(1,tree.claim(ordinal,'ZZZ'));tree.invariant()

    def test_fixed_weights_batching_and_claim_order_match_eager_reference(self):
        weights={1:101,2:7,24:9,513:31,1000:2}
        lazy,eager=self.paired(weights)
        for amount in (1,1,2,17,23,101,1,1001):
            lazy.credit('ETH',amount);eager.credit('ETH',amount)
        self.equal_reference(lazy,eager)
        expected={i:eager.claim(i,'ETH') for i in weights}
        for order in (list(weights),list(reversed(weights))):
            tree,_=self.paired(weights);tree.credit('ETH',1147)
            self.assertEqual(expected,{i:tree.claim(i,'ETH') for i in order})
            self.assertEqual(0,tree.books['ETH']['liability']);tree.invariant()

    def test_hierarchical_rounding_is_explicitly_not_flat_proportional_rounding(self):
        tree,reference=self.paired({1:2,2:1,1000:2})
        tree.credit('ETH',3);reference.credit('ETH',3)
        actual=[tree.claim(i,'ETH') for i in (1,2,1000)]
        self.assertEqual([0,1,2],actual)
        flat=[(3*2)//5,(3*3)//5-(3*2)//5,3-(3*3)//5]
        self.assertEqual([1,0,2],flat);self.assertNotEqual(flat,actual)
        self.assertEqual(3,sum(actual));self.assertEqual(actual,[reference.claim(i,'ETH') for i in (1,2,1000)])

    def test_intermediate_claims_do_not_change_later_allocation(self):
        lazy,eager=self.paired({1:1,99:3,1000:7})
        for n in range(31):
            for asset in ASSETS:
                lazy.credit(asset,n+1);eager.credit(asset,n+1)
                if n%3==0:self.assertEqual(eager.claim(99,asset),lazy.claim(99,asset))
        self.equal_reference(lazy,eager)

    def test_new_activation_never_receives_old_pending_funds(self):
        lazy,eager=self.paired({1:3})
        for asset,amount in (('ETH',1),('ZZZ',19)):
            lazy.credit(asset,amount);eager.credit(asset,amount)
        lazy.set_weight(1000,300);eager.set_weight(1000,300)
        for asset in ASSETS:self.assertEqual(0,lazy.claim(1000,asset))
        self.equal_reference(lazy,eager)

    def test_growth_pushes_old_weights_for_both_assets_and_preserves_sibling(self):
        lazy,eager=self.paired({1:1,2:1,1000:3})
        for asset in ASSETS:lazy.credit(asset,103);eager.credit(asset,103)
        before={asset:eager.balances[asset][2] for asset in ASSETS}
        lazy.set_weight(1,1001);eager.set_weight(1,1001)
        for asset in ASSETS:
            self.assertEqual(before[asset],lazy.claim(2,asset));eager.claim(2,asset)
            lazy.credit(asset,107);eager.credit(asset,107)
        self.equal_reference(lazy,eager)

    def test_counterexample_updating_weights_before_push_gives_old_money_to_newcomer(self):
        correct=_LazyTree();correct.set_weight(1,1);correct.credit('ETH',1)
        correct.set_weight(1000,1)
        broken=_LazyTree();broken.set_weight(1,1);broken.credit('ETH',1)
        node=broken.leaf(1000);broken.weights[node]=1
        while node>1:
            node//=2;broken.weights[node]=broken.weights[node*2]+broken.weights[node*2+1]
        self.assertEqual(0,correct.claim(1000,'ETH'))
        self.assertEqual(1,broken.claim(1000,'ETH'))

    def test_raw_weight_ticket_array_is_not_bounded_by1000_nfts(self):
        tree=_LazyTree();tree.set_weight(1,10**30);tree.set_weight(1000,1)
        self.assertEqual(10**30+1,tree.weights[1]);self.assertEqual(2048,len(tree.weights))
        tree.credit('ETH',1);self.assertEqual(0,tree.last_pushes)
        tree.claim(1,'ETH');self.assertEqual(10,tree.last_pushes)

    def test_fee_components_exact_split_and_reserved_dust_stay_separate(self):
        design=_FeeDesign();design.activate(1,1,'A');design.activate(2,100,'B')
        for asset in ASSETS:
            design.harvest(asset,19);self.assertEqual([19,0,0],design.reserves[asset])
            design.harvest(asset,1);self.assertEqual([0,1,1],design.reserves[asset])
            self.assertEqual(16,design.owner.books[asset]['liability'])
            self.assertEqual(2,design.collective.books[asset]['liability'])
            paid=sum(design.claim(i,asset,wallet) for i,wallet in ((1,'A'),(2,'B')))
            self.assertEqual(18,paid)
        design.invariant()

    def test_collective_equal_membership_ignores_lp_share_growth(self):
        design=_FeeDesign();design.activate(1,1,'A');design.activate(2,1000000,'B')
        design.harvest('ETH',200);design.grow(1,10**20)
        self.assertEqual(10,design.collective.claim(1,'ETH'))
        self.assertEqual(10,design.collective.claim(2,'ETH'))
        design.collective.invariant()

    def test_transfer_preserves_unclaimed_rights_for_current_owner_and_repeat_claims_zero(self):
        design=_FeeDesign();design.activate(1,101,'A');design.harvest('ETH',20)
        design.owners[1]='B'
        with self.assertRaises(ValueError):design.claim(1,'ETH','A')
        self.assertEqual(18,design.claim(1,'ETH','B'))
        self.assertEqual(0,design.claim(1,'ETH','B'));design.invariant()

    def test_activation_then_growth_then_harvest_preserves_all_components(self):
        design=_FeeDesign();design.activate(1,17,'A');design.harvest('ETH',400)
        design.activate(1000,91,'B');design.grow(1,101);design.harvest('ETH',600)
        self.assertGreater(design.claim(1,'ETH','A'),0)
        self.assertGreater(design.claim(1000,'ETH','B'),0)
        self.assertEqual(0,design.owner.books['ETH']['liability'])
        self.assertEqual(0,design.collective.books['ETH']['liability']);design.invariant()

    def test1000_nft_bound_all_units_assignable_no_padding_payee(self):
        lazy,eager=self.paired({i:(i%13)+1 for i in range(1,1001)})
        lazy.credit('ETH',1234567);eager.credit('ETH',1234567)
        paid=0
        for ordinal in range(1000,0,-1):
            amount=lazy.claim(ordinal,'ETH');self.assertEqual(eager.claim(ordinal,'ETH'),amount)
            paid+=amount
        self.assertEqual(1234567,paid);self.assertEqual(0,lazy.books['ETH']['liability'])
        lazy.invariant()

    def test_invalid_ordinal_and_uint_bounds_reject_without_mutating_tree(self):
        tree=_LazyTree();tree.set_weight(1,UINT256)
        for ordinal,weight in ((0,1),(1001,1),(True,1),(2,1),(1,UINT256+1),(1,-1)):
            before=copy.deepcopy(tree.__dict__)
            with self.subTest(ordinal=ordinal,weight=weight),self.assertRaises(ValueError):tree.set_weight(ordinal,weight)
            self.assertEqual(before,tree.__dict__)

    def test_pending_and_node_arithmetic_overflow_rejected_before_credit(self):
        tree=_LazyTree();tree.set_weight(1,1);tree.credit('ZZZ',UINT256)
        before=copy.deepcopy(tree.__dict__)
        with self.assertRaises(ValueError):tree.credit('ZZZ',1)
        self.assertEqual(before,tree.__dict__)
        with self.assertRaises(ValueError):_add(UINT256,1)
        self.assertEqual(UINT256,tree.claim(1,'ZZZ'));tree.invariant()

    def test_no_cohort_credit_rejected_no_later_activation_steals_it(self):
        tree=_LazyTree();before=copy.deepcopy(tree.__dict__)
        with self.assertRaises(ValueError):tree.credit('ETH',1)
        self.assertEqual(before,tree.__dict__)
        tree.set_weight(1,1);self.assertEqual(0,tree.claim(1,'ETH'))

    def test_deterministic_mixed_sequence_matches_eager_at_every_checkpoint(self):
        rng=random.Random(61106);lazy,eager=self.paired({1:5,2:7,513:11})
        active=[1,2,513]
        for step in range(90):
            asset=ASSETS[step%2]
            if step in (5,31,70):
                ordinal=(37,700,1000)[(5,31,70).index(step)];active.append(ordinal)
                weight=rng.randrange(1,1000);lazy.set_weight(ordinal,weight);eager.set_weight(ordinal,weight)
            elif step%7==0:
                ordinal=rng.choice(active);new=lazy.weights[lazy.leaf(ordinal)]+rng.randrange(1,100)
                lazy.set_weight(ordinal,new);eager.set_weight(ordinal,new)
            elif step%5==0:
                ordinal=rng.choice(active)
                self.assertEqual(eager.claim(ordinal,asset),lazy.claim(ordinal,asset))
            else:
                amount=rng.randrange(1,10000);lazy.credit(asset,amount);eager.credit(asset,amount)
            if step%15==0:self.equal_reference(lazy,eager)
        self.equal_reference(lazy,eager)


if __name__=='__main__':unittest.main()
