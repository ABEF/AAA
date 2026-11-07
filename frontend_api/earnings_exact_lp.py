"""Accounting7 exact LP replay; accounting6 retains its indexed handler."""
from collections import defaultdict
from frontend_api.earnings_replay import Replay, SCALE, require, TOPICS
from frontend_api.history import HistoryError, ZERO, _topic_address
from zzz_ops.abi import decode_words,keccak256
from zzz_ops.exact_lp import Tree,uint
from zzz_ops.work_budget import checkpoint

SPECS={
 'ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)':(2,4),
 'CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)':(1,4),
 'Claimed(uint256,address,address,uint256)':(3,1),
 'LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)':(2,4),
}
EXACT_TOPICS={'0x'+keccak256(sig.encode()).hex():(sig.split('(')[0],*shape) for sig,shape in SPECS.items()}


class ExactReplay(Replay):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.owner_trees={};self.collective_tree=Tree();self.direct=defaultdict(lambda:[0,0])
        self.pending_share_sync={};self.pending_member_sync={};self.ordinals={};self.lp_orphaned=defaultdict(int)

    def begin(self,emitters,lp_assets,royalty_assets,*args,**kwargs):
        require(len(lp_assets)==2 and lp_assets[0]==ZERO and lp_assets[1]!=ZERO,'Exact LP assets must be native ETH and fixed ZZZ')
        require(not hasattr(self,'pair') or self.pair==tuple(lp_assets),'Canonical exact LP currencies changed')
        self.pair=tuple(lp_assets)
        super().begin(emitters,lp_assets,royalty_assets,*args,**kwargs)

    def components(self,identifier,asset):
        ordinal=self.ordinals.get(identifier)
        if ordinal is None:return (0,0)
        book=self.pair.index(asset);bucket=self.shares.get(identifier,(0,0))[0]
        tree=self.owner_trees.get(bucket)
        direct=self.direct[identifier,asset]
        return ((tree.claimable(book,ordinal) if tree else 0)+direct[0],
                self.collective_tree.claimable(book,ordinal)+direct[1])

    def direct_liability(self,asset):return sum(sum(v) for (identifier,currency),v in self.direct.items() if currency==asset)

    def _take(self,identifier,asset):
        require(identifier in self.ordinals and asset in self.pair,'Unknown exact LP claim identity')
        ordinal=self.ordinals[identifier];book=self.pair.index(asset)
        bucket=self.shares.get(identifier,(0,0))[0];tree=self.owner_trees.get(bucket)
        values=[tree.take(book,ordinal) if tree else 0,self.collective_tree.take(book,ordinal)]
        direct=self.direct[identifier,asset]
        values=[values[i]+direct[i] for i in (0,1)];self.direct[identifier,asset]=[0,0]
        return values

    def __call__(self,emitter,topics,data,block,block_hash,timestamp,transaction,log_index):
        role=self.roles.get(emitter)
        exact=EXACT_TOPICS.get(topics[0].lower()) if role=='rewards' else None
        base=TOPICS.get((role,topics[0].lower()))
        if not self.started:
            return super().__call__(emitter,topics,data,block,block_hash,timestamp,transaction,log_index)
        try:
            if exact is not None or role=='rewards' and base and base[0]=='PoolRewardsCredited':
                checkpoint();require(not self.retired,'Exact LP event after retirement')
                require(self.last_timestamp<=timestamp<=self.timestamp,'Exact LP chronology differs')
                if self.pending_lp_credit:require(transaction==self.pending_lp_transaction,'Exact LP funding acknowledgment crossed transactions')
                self.last_timestamp=timestamp;self.events+=1
                if exact is None:
                    name,indexed,words=base
                else:name,indexed,words=exact
                require(len(topics)==indexed+1,'Exact LP indexed event layout differs')
                d=[int(x,16) for x in decode_words(data)]
                require(len(d)==words,'Exact LP event data layout differs')
                identifier=int(topics[1],16)
                if name=='ShareWeightSynchronized':
                    bucket=int(topics[2],16);ordinal,previous,weight,total=d
                    require(identifier in self.ordinals and self.ordinals[identifier]==ordinal and bucket!=0 and
                        identifier not in self.pending_share_sync and weight>previous,'Invalid exact LP share sync')
                    prior_bucket,prior=self.shares.get(identifier,(bucket,0))
                    require(prior_bucket==bucket and prior==previous,'Exact LP old share snapshot differs')
                    tree=self.owner_trees.setdefault(bucket,Tree())
                    require(len(self.owner_trees)<=4 and tree.weight_of(ordinal)==previous,'Exact LP bucket/leaf differs')
                    require(tree.set_weight(ordinal,weight)==total,'Exact LP new denominator differs')
                    self.pending_share_sync[identifier]=(bucket,previous,weight,total)
                elif name=='CollectiveWeightSynchronized':
                    ordinal,previous,weight,total=d
                    require(self.ordinals.get(identifier)==ordinal and identifier not in self.members and previous==0 and weight==1 and
                        identifier not in self.pending_member_sync,'Invalid exact LP collective sync')
                    require(self.collective_tree.weight_of(ordinal)==0 and self.collective_tree.set_weight(ordinal,1)==total and
                        total==len(self.members)+1,'Exact LP collective denominator differs')
                    self.pending_member_sync[identifier]=ordinal
                elif name=='PoolRewardsCredited':
                    bucket=identifier;asset=_topic_address(topics[2]);personal,shared=d
                    require(not self.pending_share_sync and not self.pending_member_sync and asset in self.pair and
                        bucket in self.owner_trees and self.supply[bucket]>0 and sum(d)>0,'Exact LP credit has incomplete weights')
                    key=bucket,asset
                    require(key not in self.pending_lp_credit,'Repeated exact LP funding credit')
                    self.pending_lp_credit[key]=(personal,shared);self.pending_lp_transaction=transaction
                    before={i:self.components(i,asset) for i in self.selected}
                    self.owner_trees[bucket].credit(self.pair.index(asset),personal)
                    if self.members:self.collective_tree.credit(self.pair.index(asset),shared)
                    else:self.lp_orphaned[asset]+=shared
                    n=self.pair.index(asset)
                    uint(self.direct_liability(asset)+self.collective_tree.outstanding[n]+
                         sum(t.outstanding[n] for t in self.owner_trees.values())+self.lp_orphaned[asset])
                    self.add('lp_owner_allocated',asset,personal,timestamp)
                    self.add('lp_collective_allocated' if self.members else 'lp_collective_quarantined',asset,shared,timestamp)
                    for i in self.selected:
                        after=self.components(i,asset)
                        for n,metric in enumerate(('lp_individual','lp_collective')):
                            require(after[n]>=before[i][n],'Exact LP old entitlement decreased')
                            self.earn(metric,asset,(after[n]-before[i][n])*SCALE,timestamp,i)
                elif name=='Claimed':
                    asset=_topic_address(topics[2]);require(sum(self._take(identifier,asset))==d[0],'Exact LP claim differs from assigned components')
                else:
                    source=_topic_address(topics[2]);require(source==self.pair[1] and sum(d[:2])>0,'Invalid exact LP conversion source')
                    require(self._take(identifier,source)==d[:2],'Exact LP conversion changed source rights')
                    self.direct[identifier,ZERO][0]=uint(self.direct[identifier,ZERO][0]+d[2])
                    self.direct[identifier,ZERO][1]=uint(self.direct[identifier,ZERO][1]+d[3])
                return
            if role=='vault' and base and base[0]=='SharesAdded':
                identifier=int(topics[1],16);bucket=int(topics[2],16);d=[int(x,16) for x in decode_words(data)]
                sync=self.pending_share_sync.get(identifier)
                require(sync is not None and len(d)==2 and sync[0]==bucket and sync[1]+d[0]==sync[2],
                    'Share addition lacks its exact LP synchronization')
                result=super().__call__(emitter,topics,data,block,block_hash,timestamp,transaction,log_index)
                require(self.supply[bucket]==sync[3],'Share addition denominator differs from exact tree')
                del self.pending_share_sync[identifier];return result
            if role=='membership' and base and base[0]=='MembershipActivated':
                identifier=int(topics[1],16)
                require(identifier in self.pending_member_sync,'Membership lacks its exact LP synchronization')
                result=super().__call__(emitter,topics,data,block,block_hash,timestamp,transaction,log_index)
                del self.pending_member_sync[identifier];return result
            result=super().__call__(emitter,topics,data,block,block_hash,timestamp,transaction,log_index)
            if role=='nft' and base and base[0]=='Transfer' and topics[1].lower()=='0x'+'0'*64:
                self.ordinals[int(topics[3],16)]=len(self.mints)
            return result
        except (ValueError,IndexError,KeyError) as exc:
            raise HistoryError('Malformed or inconsistent accounting7 exact LP event') from exc

    def finish(self):
        require(not self.pending_share_sync and not self.pending_member_sync,'Unacknowledged exact LP weight synchronization')
        super().finish()

    def report(self,descriptors):
        result=super().report(descriptors)
        result['rounding']='LP rewards use exact whole-unit hierarchical allocation with preserved high/low phase; royalties use exact rotating tickets.'
        result['lp_allocation_version']=1
        return result
