"""Bounded accounting7 LP tree semantics; no RPC, assets, owners or signing.

This models ExactLPAllocation's high/low phase, not the earlier reset-carry
prototype. Production callers authenticate immutable ordinals and funding.
"""
from zzz_ops.work_budget import checkpoint

UINT=(1<<256)-1
Q=1<<128
LEAVES=1024
MAX_ORDINAL=1000


def uint(value):
    if type(value) is not int or not 0<=value<=UINT:raise ValueError('Invalid exact LP uint256')
    return value


def split(amount,left,weight,high=0,low=0):
    for value in (amount,left,weight,low):uint(value)
    if weight==0 or left>weight or type(high) is not int or not 0<=high<Q or low>=weight:raise ValueError('Invalid exact LP split')
    whole,remainder=divmod(amount*left,weight)
    phase,next_low=divmod(remainder*Q,weight)
    phase, next_low = (phase+1,next_low-(weight-low)) if next_low>=weight-low else (phase,next_low+low)
    phase+=high
    if phase>=Q:whole+=1;phase-=Q
    if whole>amount:raise ValueError('Invalid exact LP split output')
    return whole,amount-whole,phase,next_low


class Tree:
    def __init__(self):
        self.weights={}
        self.pending=({}, {})
        self.carry=({}, {})
        self.outstanding=[0,0]

    @staticmethod
    def leaf(ordinal):
        if type(ordinal) is not int or not 1<=ordinal<=MAX_ORDINAL:raise ValueError('Invalid exact LP ordinal')
        return LEAVES+ordinal-1

    def weight_of(self,ordinal):return self.weights.get(self.leaf(ordinal),0)
    @property
    def total(self):return self.weights.get(1,0)

    def _path(self,asset,ordinal,mutate):
        if type(asset) is not int or asset not in (0,1):raise ValueError('Invalid exact LP book')
        self.leaf(ordinal);node=1;incoming=0;mask=LEAVES>>1
        pending,carry=self.pending[asset],self.carry[asset]
        while mask:
            checkpoint();incoming=uint(incoming+pending.get(node,0))
            if mutate:pending.pop(node,None)
            right=bool((ordinal-1)&mask)
            if incoming:
                left,other,high,low=split(incoming,self.weights.get(node*2,0),
                    self.weights.get(node,0),*carry.get(node,(0,0)))
                if mutate:
                    sibling=node*2+(0 if right else 1);amount=left if right else other
                    if amount:pending[sibling]=uint(pending.get(sibling,0)+amount)
                    carry[node]=(high,low)
                incoming=other if right else left
            node=node*2+int(right);mask>>=1
        return uint(incoming+pending.get(node,0)),node

    def set_weight(self,ordinal,weight):
        uint(weight);leaf=self.leaf(ordinal);old=self.weights.get(leaf,0)
        if old==weight:return self.total
        total=uint(self.total-old+weight)
        for asset in (0,1):
            amount,_=self._path(asset,ordinal,True)
            if amount:self.pending[asset][leaf]=amount
        self.weights[leaf]=weight;node=leaf>>1
        while node:
            before=self.weights.get(node,0);after=uint(self.weights.get(node*2,0)+self.weights.get(node*2+1,0))
            self.weights[node]=after
            for asset in (0,1):
                high,low=self.carry[asset].get(node,(0,0))
                if low:self.carry[asset][node]=(high,low*after//before if before and after else 0)
            node>>=1
        return total

    def credit(self,asset,amount):
        uint(amount)
        if type(asset) is not int or asset not in (0,1):raise ValueError('Invalid exact LP book')
        if not amount:return
        if self.total==0:raise ValueError('Empty exact LP cohort')
        outstanding=uint(self.outstanding[asset]+amount)
        pending=uint(self.pending[asset].get(1,0)+amount)
        self.outstanding[asset]=outstanding;self.pending[asset][1]=pending

    def claimable(self,asset,ordinal):return self._path(asset,ordinal,False)[0]

    def take(self,asset,ordinal):
        amount,leaf=self._path(asset,ordinal,True)
        if amount>self.outstanding[asset]:raise ValueError('Exact LP outstanding underflow')
        self.pending[asset].pop(leaf,None);self.outstanding[asset]-=amount
        return amount
