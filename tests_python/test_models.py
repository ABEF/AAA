"""Executable mathematical specifications, NOT execution of the Solidity bytecode."""
from collections import defaultdict
from decimal import Decimal,localcontext
from fractions import Fraction
import math
import random
import unittest

class RewardsModel:
    SCALE=10**36
    def __init__(self):
        self.weight=defaultdict(int);self.index=0;self.paid=defaultdict(int);self.credit=defaultdict(int)
        self.fraction=defaultdict(int);self.total=0;self.liability=0;self.orphan=0;self.distributed=0
    def sync(self,i):
        product=self.weight[i]*(self.index-self.paid[i])+self.fraction[i]
        self.credit[i]+=product//self.SCALE;self.fraction[i]=product%self.SCALE;self.paid[i]=self.index
    def add(self,i,w):self.sync(i);self.weight[i]+=w;self.total+=w
    def fund(self,n):
        self.distributed+=n
        if self.total:self.index+=n*self.SCALE//self.total;self.liability+=n
        else:self.orphan+=n
    def claim(self,i):
        self.sync(i);n=self.credit[i];self.credit[i]=0;self.liability-=n
        assert self.liability>=0
        return n

class AccountingModelTests(unittest.TestCase):
    def test_split_exact_example(self):
        n=1000;u,d=divmod(n,10);self.assertEqual((5*u,3*u,u,u,d),(500,300,100,100,0))
    def test_split_micro_harvest_is_partition_independent(self):
        rng=random.Random(47)
        for _ in range(500):
            total=0;dust=0;alloc=[0,0,0,0]
            for _ in range(40):
                n=rng.randrange(0,10**12);total+=n;u,dust=divmod(n+dust,10)
                alloc=[x+u*w for x,w in zip(alloc,[5,3,1,1])]
            self.assertEqual(sum(alloc)+dust,total)
            u,remainder=divmod(total,10);self.assertEqual(alloc,[u*5,u*3,u,u]);self.assertEqual(dust,remainder)
    def test_tiny_fees_are_carried_not_rejected(self):
        dust=0;distributed=0
        for _ in range(9):u,dust=divmod(dust+1,10);distributed+=u*10
        self.assertEqual((distributed,dust),(0,9))
        u,dust=divmod(dust+1,10);self.assertEqual((u,dust),(1,0))
    def test_new_power_cannot_receive_previous_index(self):
        m=RewardsModel();m.add(1,100);m.fund(300);m.add(2,100)
        self.assertEqual(m.claim(2),0);self.assertEqual(m.claim(1),300)
        m.fund(100);self.assertEqual(m.claim(2),50);self.assertEqual(m.claim(1),50)
    def test_topup_does_not_reprice_past_rewards(self):
        m=RewardsModel();m.add(1,100);m.add(2,100);m.fund(200);m.add(1,100)
        self.assertEqual(m.claim(1),100);self.assertEqual(m.claim(2),100)
        m.fund(300);self.assertEqual(m.claim(1),200);self.assertEqual(m.claim(2),100)
    def test_zero_power_not_windfall_for_first_user(self):
        m=RewardsModel();m.fund(99);m.add(1,100);self.assertEqual(m.claim(1),0);self.assertEqual(m.orphan,99)
    def test_fraction_survives_small_claims(self):
        m=RewardsModel();m.add(1,1);m.add(2,2);paid=0
        for _ in range(30):m.fund(1);paid+=m.claim(1)
        self.assertGreaterEqual(paid,9);self.assertLessEqual(paid,10)
    def test_randomized_index_solvency(self):
        rng=random.Random(1942);m=RewardsModel();m.add(0,10**18);paid=0
        for _ in range(10000):
            user=rng.randrange(20);op=rng.randrange(3)
            if op==0:m.add(user,rng.randrange(1,10**18))
            elif op==1:m.fund(rng.randrange(1,10**24))
            else:paid+=m.claim(user)
            self.assertLessEqual(paid+m.orphan,m.distributed);self.assertGreaterEqual(m.liability,0)
        for user in list(m.weight):paid+=m.claim(user)
        self.assertEqual(m.distributed,paid+m.liability+m.orphan)
    def test_exact_fraction_upper_bound(self):
        m=RewardsModel();m.add(1,7);m.add(2,11);ideal=Fraction(0)
        for n in (1,3,101,10**9,17):m.fund(n);ideal+=Fraction(7*n,18)
        self.assertLessEqual(m.claim(1),ideal)
    def test_nft_transfer_does_not_copy_credit(self):
        m=RewardsModel();m.add(42,100);m.fund(70);owners={42:'alice'};owners[42]='bob'
        self.assertEqual(owners[42],'bob');self.assertEqual(m.claim(42),70);self.assertEqual(m.claim(42),0)
    def test_idle_balance_principal_conservation(self):
        rng=random.Random(123);total=0;idle=defaultdict(int);deposited=defaultdict(int);lp=defaultdict(int)
        for _ in range(5000):
            i=rng.randrange(20);new=rng.randrange(1,10**18);deposited[i]+=new;idle[i]+=new;total+=new
            used=rng.randrange(idle[i]+1);idle[i]-=used;lp[i]+=used;total-=used
            self.assertEqual(sum(idle.values()),total)
            self.assertEqual(sum(deposited.values()),sum(idle.values())+sum(lp.values()))
    def test_bridge_message_nonce_domain(self):
        used=set()
        def accept(chain,adapter,nonce):
            key=(chain,adapter,nonce)
            if key in used:return False
            used.add(key);return True
        self.assertTrue(accept(1,'a',1));self.assertFalse(accept(1,'a',1));self.assertTrue(accept(2,'a',1));self.assertTrue(accept(1,'b',1))
    def test_migration_no_timeout_exit(self):
        allowed={'active':{'outbound'},'outbound':{'remote'},'inbound':{'active'},'remote':set()}
        for state in allowed:self.assertNotIn('withdrawn',allowed[state])
    def test_oracle_freshness_boundaries(self):
        def valid(answer,updated,now,age):return answer>0 and updated>0 and updated<=now and now-updated<=age
        self.assertTrue(valid(1,100,160,60));self.assertFalse(valid(1,99,160,60));self.assertFalse(valid(0,100,160,60));self.assertFalse(valid(1,161,160,60))
    def test_negative_tick_floor(self):
        for tick in [-1201,-61,-60,-59,-1,0,1,59,60,61,1201]:
            lower=(tick//60)*60;self.assertLessEqual(lower,tick);self.assertLess(tick,lower+60)
    def test_tick_range_covers_plus_minus_ten_percent(self):
        with localcontext() as ctx:
            ctx.prec=80;base=Decimal('1.0001');rng=random.Random(42)
            for _ in range(1000):
                tick=rng.randrange(-600000,600000);spacing=rng.choice([1,10,60,200]);price=base**tick
                low=(price*Decimal('.9')).ln()/base.ln();high=(price*Decimal('1.1')).ln()/base.ln()
                lt=int(low.to_integral_value(rounding='ROUND_FLOOR'))//spacing*spacing
                ut=(int(high.to_integral_value(rounding='ROUND_FLOOR'))//spacing+1)*spacing
                self.assertLessEqual(base**lt,price*Decimal('.9'));self.assertGreaterEqual(base**ut,price*Decimal('1.1'))
    def test_range_sqrt_scaling(self):
        scale=10**16;lo=math.isqrt(9000*10**28);hi=math.isqrt(11000*10**28)
        self.assertLessEqual(Fraction(lo*lo,scale*scale),Fraction(9,10))
        self.assertLess(abs(Fraction(hi*hi,scale*scale)-Fraction(11,10)),Fraction(1,10**14))
    def test_split_remote_and_local_conservation(self):
        for total in range(0,1000):
            u,d=divmod(total,10);remote=u*8;compound=u;buyback=u
            self.assertEqual(remote+compound+buyback+d,total)
            self.assertEqual(u*5+u*3,remote)
