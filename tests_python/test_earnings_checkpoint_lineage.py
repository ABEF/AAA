"""Lineage checkpoint composition on controlled fresh7/mint2 histories.

Projection, Lineage receipt checking, SQLite History, Earnings, exact replay,
checkpoint construction and publication are real code. Dependency/runtime and
getter truths are synthetic fixture observations, partly derived from full
replay; comparisons are differential, not an independent on-chain oracle.
No network, existing chain, source fixture rewrite, key or transaction is used.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from frontend_api.earnings_checkpoint import decode, encode
from frontend_api.earnings_checkpoint_build import build, publish_candidate
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.history import HistoryError, ZERO
from frontend_api.lineage import SHARED_DEPENDENCY_ROLES
from frontend_api.service import Projection
from indexer.monitor import Indexer
from tests_python.test_frontend_api import addr, words
from tests_python.test_seadrop_consumer import SeaDropAPI
from zzz_ops.abi import keccak256
from zzz_ops.rpc import RpcError


ORIGINAL_VERIFY = Projection._verify_deployment
ORIGINAL_ADMITTED = Projection._admitted
ORIGINAL_CALL = Projection._call


def digest(n):
    return '0x'+format(100000+n, '064x')


class EpochFixture:
    """Explicit mint2 epochs; no historical graph is relabelled current."""
    def __init__(self, case, count=2):
        self.case = case
        self.tmp = tempfile.TemporaryDirectory(); case.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        with patch.object(Projection,'_verify_deployment',ORIGINAL_VERIFY), \
                patch.object(Projection,'_admitted',ORIGINAL_ADMITTED), \
                patch.object(Projection,'_call',ORIGINAL_CALL):
            self.template = SeaDropAPI(case)
            self.original_life = self.template.p._verify_deployment(self.template.block())
        self.ids = (self.template.rpc.nft_id,
                    int.from_bytes(keccak256(b'lineage-checkpoint-second'), 'big'),
                    int.from_bytes(keccak256(b'lineage-checkpoint-dormant'), 'big'))
        self.pair, self.royalties = [ZERO, addr(20)], [ZERO, addr(21)]
        self.edges = [240] if count == 2 else [140, 240]
        self.starts = [10]+[n-20 for n in self.edges]
        self.head = 310; self.safe = 299
        self.rows = [[] for _ in range(count)]
        self.roles = []; self.configs = []; self.profiles = []
        self.address_epoch = {}; self.codes = {}; self.birth = {}
        self.receipts = {}; self.calls = []; self.reorg = None; self.unavailable = False
        self.retired_claims_unavailable = False
        self.late_assets = []
        self.getter_overrides = {}; self.indexes = []; self.model_cache = {}
        for epoch in range(count):
            cfg = copy.deepcopy(self.template.config)
            cfg['deployment_block'] = self.starts[epoch]
            cfg['deployment_block_hash'] = digest(self.starts[epoch])
            for role, item in cfg['contracts'].items():
                old = item['address']
                if role not in SHARED_DEPENDENCY_ROLES:
                    item['address'] = addr(int(old, 16)+100000*(epoch+1))
                target = item['address']
                self.codes[target] = self.template.rpc.codes[old]
                self.birth[target] = self.starts[epoch] if role not in SHARED_DEPENDENCY_ROLES else 0
                if role not in SHARED_DEPENDENCY_ROLES:
                    self.address_epoch[target] = epoch, role
            roles = {r: cfg['contracts'][r]['address'] for r in ('nft','vault','rewards','royalties','handoff')}
            extra = {}
            for n, role in enumerate(('fees','membership'), 40):
                target = addr(100000*(epoch+1)+n);code = bytes([0x60,n,epoch])
                self.codes[target] = '0x'+code.hex();self.birth[target] = self.starts[epoch]
                self.address_epoch[target] = epoch, role; roles[role] = target
                extra[role] = dict(address=target, code_hash='0x'+keccak256(code).hex())
            cfg['history'] = dict(database=str(self.root/f'epoch-{epoch}.sqlite'),
                start_block=self.starts[epoch], start_parent_hash=digest(self.starts[epoch]-1),
                contracts=sorted(roles.values()), max_events=1000)
            self.roles.append(roles); self.configs.append(cfg)
            self.profiles.append(dict(controller=cfg['contracts']['access']['address'], **extra))
        for asset in self.template.config['assets']:
            if asset['address']==ZERO:continue
            self.codes[asset['address']] = self.template.rpc.codes[asset['address']]
            self.birth[asset['address']] = 0
        self._populate()
        for epoch, cfg in enumerate(self.configs):
            writer = Indexer(dict(database=cfg['history']['database'], chain_id=31337,
                start_block=self.starts[epoch], start_parent_hash=digest(self.starts[epoch]-1),
                contracts=cfg['history']['contracts'], rpc_urls=['http://127.0.0.1:1']), self)
            case.addCleanup(writer.close);self.indexes.append(writer)
            through = self.edges[epoch] if epoch < len(self.edges) else self.safe
            with writer.db:
                for number in range(self.starts[epoch], through+1):
                    h = self.header(number)
                    writer.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                        (31337,number,h['hash'],h['parentHash'],int(h['timestamp'],16)))
                writer.db.execute('UPDATE cursors SET next_block=?',(through+1,))
                for row in self.rows[epoch]:
                    writer.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                        (31337,int(row['blockNumber'],16),row['blockHash'],row['transactionHash'],
                         int(row['logIndex'],16),row['address'],None,None,json.dumps(row)))
        self.config = copy.deepcopy(self.configs[-1])
        self.config['predecessors'] = [dict({k:c[k] for k in ('deployment_block','deployment_block_hash',
                'contracts','assets','history','accounting_version','custody_version','royalty_reporting',
                'mint_integration_version')}, retirement_transaction_hash=self.transition_tx(n))
            for n,c in enumerate(self.configs[:-1])]
        self.config['earnings_history'] = dict(schema=1, deployments=self.profiles, prices=None)
        # Only dependency lifecycle/admission/getter observations are substituted.
        # Receipt checks, canonical headers, code hashes, SQL and accounting stay real.
        for name, method in (('_verify_deployment', self.verify), ('_admitted', self.admitted), ('_call', self.read_call)):
            def wrapper(p,*args,_method=method,**kwargs):return _method(p,*args,**kwargs)
            active = patch.object(Projection,name,wrapper);active.start();case.addCleanup(active.stop)

    def transition_tx(self, epoch):return digest(10000+epoch)
    def handoff(self, epoch):return digest(20000+epoch)
    def state_root(self, epoch):return digest(30000+epoch)
    def timestamp(self, number):return 1000000+number*1200
    def header(self, number):
        return dict(number=hex(number), hash=digest(number) if self.reorg != number else digest(90000+number),
            parentHash=digest(number-1), timestamp=hex(self.timestamp(number)))

    def emit(self, epoch, role, signature, indexed=(), data=(), number=20, *, index=None, transaction=None):
        if index is None:index=sum(int(r['blockNumber'],16)==number for r in self.rows[epoch])
        row=dict(address=self.roles[epoch][role],blockNumber=hex(number),blockHash=digest(number),
            transactionHash=transaction or digest(1000+number),transactionIndex='0x0',logIndex=hex(index),
            removed=False,topics=['0x'+keccak256(signature.encode()).hex(),*[words(x) for x in indexed]],data=words(*data))
        self.rows[epoch].append(row);self.model_cache.clear()
        return row

    def _populate(self):
        for asset in self.royalties:self.emit(0,'royalties','AssetAdded(address,uint256)',(asset,),(0,),10)
        end=self.timestamp(14)
        self.emit(0,'royalties','MintEndConfigured(uint64,uint256)',(),(end,end+3600),10)
        for n,i in enumerate(self.ids):self.emit(0,'nft','Transfer(address,address,uint256)',(ZERO,addr(30+n),i),(),11)
        self.activate(0,self.ids[0],101,1,13)
        for asset in self.royalties:self.emit(0,'royalties','RoyaltiesReceived(address,uint256,bool)',(asset,),(7,0),14)
        self.emit(0,'royalties','RoyaltyOpeningFinalized(uint256,uint256,uint256)',(),(end+3600,1,1),20)
        for asset in self.pair:self.fees(0,asset,20)
        for asset in self.royalties:self.royalty(0,asset,7,20,initial=True)
        self.activate(0,self.ids[1],200,3,40);self.grow(0,self.ids[0],98,41)
        for asset in self.pair:self.fees(0,asset,43,3)
        for asset in self.royalties:self.royalty(0,asset,9,44)
        self.emit(0,'nft','Transfer(address,address,uint256)',(addr(30),addr(35),self.ids[0]),(),45)
        amount=self.model(0,45).components(self.ids[0],self.pair[1])
        self.emit(0,'rewards','LPRewardsConverted(uint256,address,uint256,uint256,uint256,uint256)',
            (self.ids[0],self.pair[1]),(*amount,*amount),46)
        amount=sum(self.model(0,46).components(self.ids[0],ZERO))
        self.emit(0,'rewards','Claimed(uint256,address,address,uint256)',(self.ids[0],ZERO,addr(35)),(amount,),47)
        amount=self.model(0,46).account_totals[self.ids[0]]['royalties',ZERO]
        self.emit(0,'royalties','Claimed(uint256,address,address,uint256)',(self.ids[0],ZERO,addr(35)),(amount,),47)
        for asset in self.pair:self.fees(0,asset,70)
        for epoch, boundary in enumerate(self.edges):
            for asset in self.pair:self.fees(epoch,asset,boundary-3,2)
            for asset in self.royalties:self.royalty(epoch,asset,11,boundary-2)
            self.emit(epoch,'handoff','Frozen(bytes32,address)',
                (self.handoff(epoch),self.configs[epoch+1]['contracts']['access']['address']),(),boundary-1)
            for asset in self.royalties:self.emit(epoch+1,'royalties','AssetAdded(address,uint256)',
                (asset,),(0,),self.starts[epoch+1])
            for identifier,owner in self.owners(epoch,boundary-1).items():
                self.emit(epoch+1,'nft','Transfer(address,address,uint256)',(ZERO,owner,identifier),(),boundary-1)
            activate=self.emit(epoch+1,'handoff','Activated(bytes32,address,bytes32)',
                (self.handoff(epoch),self.configs[epoch]['contracts']['access']['address']),
                (self.state_root(epoch),),boundary,index=90,transaction=self.transition_tx(epoch))
            retire=self.emit(epoch,'handoff','Retired(bytes32,address,bytes32)',
                (self.handoff(epoch),self.configs[epoch+1]['contracts']['access']['address']),
                (self.state_root(epoch),),boundary,index=91,transaction=self.transition_tx(epoch))
            self.receipts[self.transition_tx(epoch)]=dict(status='0x1',transactionHash=self.transition_tx(epoch),
                blockNumber=hex(boundary),blockHash=digest(boundary),transactionIndex='0x0',logs=[activate,retire])
            for asset in self.pair:self.fees(epoch+1,asset,boundary+10)
            self.grow(epoch+1,self.ids[1],7,boundary+11)
            for asset in self.royalties:self.royalty(epoch+1,asset,11,boundary+12)
            amount=sum(self.model(epoch+1,boundary+12).components(self.ids[1],self.pair[1]))
            self.emit(epoch+1,'rewards','Claimed(uint256,address,address,uint256)',
                (self.ids[1],self.pair[1],self.owners(epoch+1,boundary+12)[self.ids[1]]),(amount,),boundary+13)
            owner=self.owners(epoch+1,boundary+13)[self.ids[1]]
            recipient=addr(35) if epoch==len(self.edges)-1 else addr(36+epoch)
            self.emit(epoch+1,'nft','Transfer(address,address,uint256)',(owner,recipient,self.ids[1]),(),boundary+14)
            for asset in self.pair:self.fees(epoch+1,asset,boundary+15,2)
            for asset in self.royalties:self.royalty(epoch+1,asset,7,boundary+16)

    def model(self, epoch, through):
        key=epoch,through
        if key not in self.model_cache:
            m=ExactReplay(self.timestamp(through),track_all=True)
            lower=None
            for e in range(epoch+1):
                cutoff=self.edges[e] if e<epoch else through
                m.begin(self.roles[e],self.pair,self.royalty_assets(e,cutoff),lower,
                        fee_intake_version=1,royalty_settlement_version=4)
                for r in sorted(self.rows[e],key=lambda r:(int(r['blockNumber'],16),int(r['logIndex'],16))):
                    n=int(r['blockNumber'],16)
                    if n<=cutoff:m(r['address'],r['topics'],r['data'],n,r['blockHash'],self.timestamp(n),r['transactionHash'],int(r['logIndex'],16))
                m.finish()
                if e<len(self.edges):lower=(self.edges[e],self.transition_tx(e),self.handoff(e),self.state_root(e))
            self.model_cache[key]=m
        return self.model_cache[key]

    def owners(self, epoch, through):
        owners={}
        transfer='0x'+keccak256(b'Transfer(address,address,uint256)').hex()
        for r in sorted(self.rows[epoch],key=lambda r:(int(r['blockNumber'],16),int(r['logIndex'],16))):
            if int(r['blockNumber'],16)<=through and r['topics'][0]==transfer:
                owners[int(r['topics'][3],16)]='0x'+r['topics'][2][-40:]
        return owners

    def activate(self,e,i,shares,weight,n):
        m=self.model(e,n);ordinal=m.ordinals[i]
        self.emit(e,'rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
            (i,5),(ordinal,0,shares,m.supply[5]+shares),n)
        self.emit(e,'rewards','CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)',
            (i,),(ordinal,0,1,len(m.members)+1),n)
        self.emit(e,'membership','MembershipActivated(uint256)',(i,),(),n)
        self.emit(e,'royalties','Activated(uint256,uint256)',(i,),(weight,),n)
        self.emit(e,'vault','SharesAdded(uint256,uint256,uint256,uint256)',(i,5),(shares,100*10**18),n)

    def grow(self,e,i,shares,n):
        m=self.model(e,n);bucket,old=m.shares[i]
        self.emit(e,'rewards','ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)',
            (i,bucket),(m.ordinals[i],old,old+shares,m.supply[bucket]+shares),n)
        self.emit(e,'vault','SharesAdded(uint256,uint256,uint256,uint256)',(i,bucket),(shares,5*10**18),n)

    def fees(self,e,asset,n,units=1):
        self.emit(e,'rewards','PoolRewardsCredited(uint256,address,uint256,uint256)',(5,asset),(16*units,2*units),n)
        self.emit(e,'fees','FeesAllocated(uint256,address,uint256,uint256)',(5,asset),(20*units,0),n)

    def royalty(self,e,asset,amount,n,initial=False):
        m=self.model(e,n);cohort=m.cohorts[asset];weight=sum(m.weights[i] for i in cohort)
        before=m.royalty_cursors[asset];after=(before+amount)%weight
        self.emit(e,'royalties','RoyaltiesAllocated(address,uint256,uint256,uint256,uint256,uint256)',
            (asset,),(amount,len(cohort),weight,before,after),n)
        if initial:self.emit(e,'royalties','InitialRoyaltiesAllocated(address,uint256,uint256,uint256)',
            (asset,),(amount,len(cohort),weight),n)
        else:self.emit(e,'royalties','RoyaltiesReceived(address,uint256,bool)',(asset,),(amount,1),n)

    def _epoch(self,p):return next(i for i,c in enumerate(self.configs) if c['contracts']['access']['address']==p.contracts['access'].address)
    def _number(self,block):return int(block['blockHash'],16)-100000
    def verify(self,p,block,allow_locked=False):
        e=self._epoch(p);n=self._number(block)
        retired=e<len(self.edges) and n>=self.edges[e]
        state='retired' if retired else 'operating'
        life={**self.original_life,'state':state,'origin':self.configs[0]['contracts']['vault']['address'],
            'predecessor_controller':None if e==0 else self.configs[e-1]['contracts']['access']['address'],
            'successor_controller':self.configs[e+1]['contracts']['access']['address'] if retired else None}
        if not allow_locked and state!='operating':raise HistoryError('Synthetic locked epoch')
        # Code verification is still an actual canonical-hash RPC observation.
        for role in ('access','handoff'):
            c=p.contracts[role];p._code(c.address,c.code_hash,block)
        return life

    def royalty_assets(self,epoch,number):
        return self.royalties+[asset for e,n,asset in self.late_assets if e==epoch and n<=number]
    def admitted(self,p,block,**kwargs):
        self.case.assertTrue(set(kwargs)<={'historical_descriptors'})
        if kwargs:self.case.assertIs(kwargs['historical_descriptors'],True)
        return self.pair,self.royalty_assets(self._epoch(p),self._number(block))
    def read_call(self,p,target,signature,*args,block=None,words=None):
        e,role=self.address_epoch[target];n=self._number(block)
        if self.retired_claims_unavailable and e<len(self.edges) and n>=self.edges[e] and \
                role=='royalties' and signature in ('pending(address)','claimable(uint256,address)'):
            raise HistoryError('Synthetic retired royalty backing has been sent')
        n=min(n,self.edges[e]) if e<len(self.edges) else n
        m=self.model(e,n);owners=self.owners(e,n)
        key=e,role,signature,tuple(args)
        if key in self.getter_overrides:return self.getter_overrides[key]
        if signature=='access()':value=self.configs[e]['contracts']['access']['address']
        elif role=='access' and signature=='module(bytes32)':
            value=next(self.roles[e][r] for r,label in (('fees','ZZZFeeController'),('membership','ZZZMembership'))
                       if args[0]=='0x'+keccak256(label.encode()).hex())
        elif signature in ('FEE_INTAKE_VERSION()','LP_ALLOCATION_VERSION()'):value=1
        elif signature=='ROYALTY_SETTLEMENT_VERSION()':value=4
        elif signature=='mintedCount()':value=len(owners)
        elif signature=='mintOrdinalOf(uint256)':value=m.ordinals.get(args[0],0)
        elif signature=='tokenAtOrdinal(uint256)':value=m.mints[args[0]-1]
        elif signature=='ownerOf(uint256)':value=owners[args[0]]
        elif signature=='balanceOf(address)':value=sum(owner==args[0] for owner in owners.values())
        elif signature=='sharesOf(uint256)':value=m.shares.get(args[0],(0,0))[1]
        elif signature in ('nftBucket(uint256)','rewardBucket(uint256)'):value=m.shares.get(args[0],(0,0))[0]
        elif signature=='bucketTotalShares(uint256)':value=m.supply[args[0]]
        elif signature=='totalEligible()':value=len(m.members)
        elif signature=='totalWeight()':value=sum(m.weights.values())
        elif signature=='activationCount()':value=len(m.weights)
        elif signature=='weightOf(uint256)':value=m.weights.get(args[0],0)
        elif signature=='ticketStart(uint256)':value=m.ticket_offsets[args[0]]+1 if args[0] in m.weights else 0
        elif signature=='dust(uint256,address)':value=m.fee_dust[tuple(args)]
        elif signature=='allocationTree(uint256)':
            tree=m.collective_tree if args[0]==0 else m.owner_trees[args[0]];value=(tree.total,*tree.outstanding)
        elif signature=='directLiabilities(address)':value=m.direct_liability(args[0])
        elif signature=='liabilities(address)':
            book=self.pair.index(args[0]);value=m.direct_liability(args[0])+m.collective_tree.outstanding[book]+sum(t.outstanding[book]for t in m.owner_trees.values())
        elif signature=='orphaned(address)':value=m.lp_orphaned[args[0]]
        elif signature=='claimableComponents(uint256,address)':value=m.components(*args)
        elif signature=='claimable(uint256,address)':
            if role=='rewards':value=sum(m.components(*args))
            else:
                claimed=0;topic='0x'+keccak256(b'Claimed(uint256,address,address,uint256)').hex()
                for epoch in range(e+1):
                    for r in self.rows[epoch]:
                        if int(r['blockNumber'],16)<=n and r['address']==self.roles[epoch]['royalties'] and r['topics'][0]==topic and int(r['topics'][1],16)==args[0] and '0x'+r['topics'][2][-40:]==args[1]:claimed+=int(r['data'],16)
                value=m.account_totals[args[0]]['royalties',args[1]]-claimed
        elif signature=='eligibleCount(address)':value=len(m.cohorts[args[0]])
        elif signature=='eligibleWeight(address)':value=sum(m.weights[i]for i in m.cohorts[args[0]])
        elif signature=='allocationCursor(address)':value=m.royalty_cursors[args[0]]
        elif signature in ('pending(address)','openingPool(address)'):value=0
        elif signature=='royaltiesOpen()':value=1
        elif signature=='handoffId()':value=self.handoff(e)
        elif signature=='stateRoot()':value=self.state_root(e)
        else:raise AssertionError('Unimplemented synthetic getter '+role+'.'+signature)
        from tests_python.test_frontend_api import words as encode_words
        return [encode_words(x)[2:] for x in value] if isinstance(value,tuple) else [encode_words(value)[2:]]

    def call(self,method,params=None):
        self.calls.append((method,copy.deepcopy(params)))
        if self.unavailable:raise HistoryError('Synthetic unavailable provider')
        if method=='eth_chainId':return 31337
        if method=='eth_blockNumber':return hex(self.head)
        if method=='eth_getBlockByNumber':return self.header(int(params[0],16))
        if method=='eth_getTransactionReceipt':return copy.deepcopy(self.receipts.get(params[0]))
        if method=='eth_getCode':
            at=params[1];self.case.assertIs(at.get('requireCanonical'),True)
            n=self._number(at)
            return self.codes[params[0]] if n>=self.birth[params[0]] else '0x'
        raise AssertionError('Unexpected synthetic RPC '+method)

    def projection(self,config=None):return Projection(self.config if config is None else config,self,clock=lambda:self.timestamp(self.safe)+1)
    def candidate(self,number=21):return build(self.projection().earnings_history,number)
    def install(self,raw=None,name='lineage-checkpoint.json'):
        path=self.root/name;raw=self.candidate() if raw is None else raw
        pin=publish_candidate(path,raw)
        self.config['earnings_history']['checkpoint']=dict(path=str(path),sha256=pin)
        return path
    def append(self,epoch,row):
        with self.indexes[epoch].db:
            self.indexes[epoch].db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',
                (31337,int(row['blockNumber'],16),row['blockHash'],row['transactionHash'],
                 int(row['logIndex'],16),row['address'],None,None,json.dumps(row)))
    def extend(self,safe):
        old=self.safe;self.safe=safe;self.head=safe+11
        with self.indexes[-1].db:
            for n in range(old+1,safe+1):
                h=self.header(n)
                self.indexes[-1].db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',
                    (31337,n,h['hash'],h['parentHash'],int(h['timestamp'],16)))
            self.indexes[-1].db.execute('UPDATE cursors SET next_block=?',(safe+1,))
    def full_config(self):
        cfg=copy.deepcopy(self.config);cfg['earnings_history'].pop('checkpoint',None);return cfg


class EarningsCheckpointLineageTests(unittest.TestCase):
    def fixture(self,count=2):return EpochFixture(self,count)

    def equal_reports(self,f):
        p=f.projection();full=f.projection(f.full_config())
        for identifier in (None,*map(str,f.ids)):
            a=p.earnings(identifier);b=full.earnings(identifier)
            for key in ('all_time','last_24h','window','event_count'):
                self.assertEqual(a[key],b[key],(identifier,key))
        owner=f.owners(len(f.configs)-1,f.safe)[f.ids[0]]
        a=p.wallet_earnings(owner,f.safe);b=full.wallet_earnings(owner,f.safe)
        for key in ('all_time','last_24h','window','event_count','token_ids'):
            self.assertEqual(a[key],b[key],key)

    def test_original_epoch_cursor_survives_a_handoff_inside_the_rolling_day(self):
        f=self.fixture();path=f.install()
        self.assertEqual(3,json.loads(path.read_bytes())['schema'])
        self.assertGreater(f.timestamp(f.edges[-1]),f.timestamp(f.safe)-86400)
        self.equal_reports(f)
        # Literal conservation, separate from differential replay comparison.
        result=f.projection().earnings()
        for row in result['all_time']:
            if row['asset'] in f.pair:
                self.assertEqual(int(row['lp_processed_raw']),sum(int(row[k]) for k in
                    ('lp_owner_allocated_raw','lp_collective_allocated_raw','lp_compounding_allocated_raw','lp_buyback_allocated_raw')))

    def test_three_epochs_and_a_middle_epoch_cursor_keep_all_lifetime_income(self):
        f=self.fixture(3);f.install(f.candidate(161));self.equal_reports(f)

    def test_cursor_after_recent_handoff_cannot_hide_part_of_the_day(self):
        f=self.fixture();f.install(f.candidate(250))
        with self.assertRaisesRegex(HistoryError,'rolling day|complete.*day|86400'):
            f.projection().earnings(str(f.ids[0]))

    def test_checkpoint_restore_reads_are_independent_after_transfer_and_claims(self):
        f=self.fixture();path=f.install();raw=path.read_bytes();p=f.projection()
        first=p.earnings(str(f.ids[0]))
        with ThreadPoolExecutor(max_workers=3) as pool:
            values=list(pool.map(p.earnings,[str(f.ids[0]),str(f.ids[1]),str(f.ids[0])]))
        self.assertEqual(first,values[0]);self.assertEqual(values[0],values[2])
        self.assertEqual(first,f.projection().earnings(str(f.ids[0])))
        self.assertEqual(raw,path.read_bytes())
        dormant=p.earnings(str(f.ids[2]))
        self.assertTrue(all(int(v)==0 for r in dormant['all_time'] for k,v in r.items()if k.endswith('_raw')))

    def test_retirement_receipt_and_runtime_are_still_required_with_a_seed(self):
        f=self.fixture();f.install();tx=f.transition_tx(0);receipt=f.receipts.pop(tx)
        with self.assertRaisesRegex(HistoryError,'receipt|retirement'):f.projection().earnings()
        f.receipts[tx]=receipt
        target=f.configs[0]['contracts']['handoff']['address'];code=f.codes[target];f.codes[target]='0x6000'
        with self.assertRaises((HistoryError,RpcError)):f.projection().earnings()
        f.codes[target]=code

    def test_wrong_handoff_commitment_or_missing_middle_peer_is_rejected(self):
        f=self.fixture(3);f.install();receipt=f.receipts[f.transition_tx(0)]
        receipt['logs'][0]['data']=words(digest(99999))
        with self.assertRaises(HistoryError):f.projection().earnings()
        f=self.fixture(3);f.install();cfg=copy.deepcopy(f.config);cfg['predecessors']=cfg['predecessors'][1:]
        with self.assertRaises((HistoryError,ValueError)):f.projection(cfg).earnings()

    def test_corrupted_or_reorged_cursor_and_missing_suffix_block_fail_closed(self):
        f=self.fixture();path=f.install();raw=path.read_bytes();path.write_bytes(raw[:-1]+b' ')
        with self.assertRaises(HistoryError):f.projection()
        path.write_bytes(raw);f.reorg=21
        with self.assertRaises(HistoryError):f.projection().earnings()
        f.reorg=None
        with f.indexes[0].db:f.indexes[0].db.execute('DELETE FROM blocks WHERE number=42')
        with self.assertRaises(HistoryError):f.projection().earnings()

    def test_source_schema_two_cannot_be_relabelled_as_lineage_state(self):
        f=self.fixture();raw=json.loads(f.candidate());raw['schema']=2
        path=f.install((json.dumps(raw)+'\n').encode())
        with self.assertRaises(HistoryError):f.projection()
        self.assertTrue(path.is_file())

    def test_exclusive_publication_keeps_the_reviewed_previous_candidate(self):
        f=self.fixture();path=f.install();before=path.read_bytes()
        with self.assertRaises(FileExistsError):publish_candidate(path,before)
        self.assertEqual(before,path.read_bytes())

    def test_completed_prefix_is_not_rescanned_and_cursor_suffix_keeps_its_bound(self):
        f=self.fixture(3);f.install(f.candidate(161))
        expected=f.projection(f.full_config()).earnings(str(f.ids[0]))
        f.config['predecessors'][0]['history']['max_events']=1
        remaining=sum(int(r['blockNumber'],16)>161 for r in f.rows[1])
        self.assertGreater(remaining,1)
        f.config['predecessors'][1]['history']['max_events']=remaining
        actual=f.projection().earnings(str(f.ids[0]))
        for key in ('all_time','last_24h','window','event_count'):
            self.assertEqual(expected[key],actual[key],key)
        with self.assertRaisesRegex(HistoryError,'bound exceeded'):
            f.projection(f.full_config()).earnings(str(f.ids[0]))
        f.config['predecessors'][1]['history']['max_events']=remaining-1
        with self.assertRaisesRegex(HistoryError,'bound exceeded'):
            f.projection().earnings(str(f.ids[0]))

    def test_advancing_original_middle_current_cursor_retains_history_and_raw_future(self):
        f=self.fixture(3);first=f.install();first_pin=hashlib.sha256(first.read_bytes()).hexdigest()
        middle=f.candidate(161)
        self.assertEqual(first_pin,json.loads(middle)['previous_sha256'])
        second=f.install(middle,'middle.json');second_pin=hashlib.sha256(second.read_bytes()).hexdigest()
        latest=f.candidate(250)
        self.assertEqual(second_pin,json.loads(latest)['previous_sha256'])
        final=f.install(latest,'current.json');f.extend(399)
        for asset in f.pair:
            before=len(f.rows[-1]);f.fees(len(f.configs)-1,asset,350,2)
            for row in f.rows[-1][before:]:f.append(len(f.configs)-1,row)
        self.equal_reports(f)
        self.assertEqual(first_pin,hashlib.sha256(first.read_bytes()).hexdigest())
        self.assertEqual(second_pin,hashlib.sha256(second.read_bytes()).hexdigest())
        self.assertEqual(latest,final.read_bytes())

    def test_completed_retirement_reorg_remains_a_required_proof(self):
        f=self.fixture(3);f.install(f.candidate(161));f.reorg=f.edges[0]
        with self.assertRaises(HistoryError):f.projection().earnings(str(f.ids[0]))

    def test_semantic_source_change_never_automatically_adopts_or_falls_back(self):
        f=self.fixture();f.install()
        with patch('frontend_api.earnings_checkpoint_v3.sources',return_value={}):
            with self.assertRaisesRegex(HistoryError,'source changed'):f.projection()

    def test_rehashed_boolean_profile_or_malformed_completed_book_cannot_be_adopted(self):
        f=self.fixture(3);raw=f.candidate(161)
        for n,variant in enumerate(('mint','execution','claims','currency')):
            document=json.loads(raw)
            if variant in ('claims','currency'):
                state=decode(document['state'])
                claims=state['completed'][0]['history']['claims']
                if variant=='claims':claims[f.ids[0],ZERO]=(True,0)
                else:
                    # Keep a valid amount/descriptor and event/key count. Only
                    # the attribution of nonzero LP payout to a royalty-only
                    # currency is wrong, so the completed-ledger guard must act.
                    amount=claims.pop((f.ids[0],ZERO))
                    self.assertGreater(amount[0],0)
                    claims[f.ids[0],addr(21)]=amount
                document['state']=encode(state)
            else:
                bound=decode(document['identity'])
                bound[0]['mint_integration_version' if variant=='mint' else 'execution_price_version']=True if variant=='mint' else False
                document['identity']=encode(bound)
            f.install((json.dumps(document)+'\n').encode(),f'malformed-{n}.json')
            with self.subTest(variant=variant):
                if variant=='currency':
                    with self.assertRaisesRegex(HistoryError,'claim currency was not admitted'):f.projection()
                else:
                    with self.assertRaises(HistoryError):f.projection()

    def test_nft_minted_after_cursor_has_no_fabricated_predecessor_earnings(self):
        f=self.fixture();f.install();identifier=int.from_bytes(keccak256(b'new NFT after lineage cursor'),'big')
        row=f.emit(1,'nft','Transfer(address,address,uint256)',(ZERO,addr(35),identifier),(),270)
        f.append(1,row)
        a=f.projection().earnings(str(identifier));b=f.projection(f.full_config()).earnings(str(identifier))
        self.assertEqual(a['all_time'],b['all_time'])
        self.assertTrue(all(int(v)==0 for r in a['all_time']for k,v in r.items()if k.endswith('_raw')))
        a=f.projection().wallet_earnings(addr(35),f.safe)
        b=f.projection(f.full_config()).wallet_earnings(addr(35),f.safe)
        self.assertEqual(a['all_time'],b['all_time']);self.assertIn(str(identifier),a['token_ids'])

    def test_original_schema_one_and_two_build_read_without_lineage(self):
        from tests_python.test_earnings_checkpoints import CheckpointAPITests
        from tests_python.test_earnings_checkpoint_v2 import Checkpoint2APITests
        for cls,expected_schema in ((CheckpointAPITests,1),(Checkpoint2APITests,2)):
            fixture=cls('runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
            raw=fixture.candidate()
            self.assertEqual(expected_schema,json.loads(raw)['schema'])
            fixture.install(raw)
            actual=fixture.projection().earnings(str(fixture.i))
            cfg=copy.deepcopy(fixture.config);cfg['earnings_history'].pop('checkpoint')
            full=fixture.projection(cfg).earnings(str(fixture.i))
            for key in ('all_time','last_24h','window','event_count'):
                self.assertEqual(full[key],actual[key],(expected_schema,key))

    def test_retired_royalty_backing_getters_are_not_required_for_a_middle_cursor(self):
        f=self.fixture(3);f.retired_claims_unavailable=True
        f.install(f.candidate(161))
        self.equal_reports(f)

    def test_rehashed_cursor_cannot_precede_its_reviewed_deployment_anchor(self):
        f=self.fixture();document=json.loads(f.candidate(21))
        bound=decode(document['identity'])
        # History records NFT creation10; reviewed deployment/seal anchor22
        # is later. A repinned artifact may not place its economic cursor21
        # before that admitted deployment identity even though it has old logs.
        bound[0]['deployment']['deployment_block']=22
        bound[0]['deployment']['deployment_hash']=digest(22)
        document['identity']=encode(bound)
        f.config['predecessors'][0]['deployment_block']=22
        f.config['predecessors'][0]['deployment_block_hash']=digest(22)
        f.install((json.dumps(document)+'\n').encode(),'before-deployment.json')
        with self.assertRaisesRegex(HistoryError,'anchor'):f.projection()

    def test_later_royalty_currency_keeps_an_earlier_epoch_cursor_and_exact_suffix(self):
        f=self.fixture();asset=addr(22);code=b'\x60\x22'
        f.codes[asset]='0x'+code.hex();f.birth[asset]=0
        descriptor=dict(address=asset,symbol='LATE',decimals=18,code_hash='0x'+keccak256(code).hex())
        f.config['assets'].append(descriptor)
        f.configs[-1]['assets'].append(copy.deepcopy(descriptor))
        f.late_assets.append((1,270,asset))
        row=f.emit(1,'royalties','AssetAdded(address,uint256)',(asset,),(0,),270);f.append(1,row)
        before=len(f.rows[1]);f.royalty(1,asset,11,271)
        for row in f.rows[1][before:]:f.append(1,row)
        # Current descriptors include LATE, while both old cursor21 and the
        # retired source240 legitimately admit only their original currencies.
        f.install(f.candidate(21));self.equal_reports(f)
        collection=f.projection().earnings()
        self.assertEqual('11',next(r for r in collection['all_time']if r['asset']==asset)['royalties_allocated_raw'])
        amounts=[int(next(r for r in f.projection().earnings(str(i))['all_time']
                         if r['asset']==asset)['royalties_raw'])for i in f.ids]
        self.assertEqual(11,sum(amounts));self.assertEqual(0,amounts[2])

    def test_raw_default_lineage_caller_matches_explicit_unseeded_history_reader(self):
        for count in (2,3):
            f=self.fixture(count);p=f.projection()
            header,_,block=p._snapshot();life=p._verify_deployment(block)
            lp,royalties=p._admitted(block)
            local=p._history_snapshot(header,block,lp,royalties)
            epochs_a=[];histories_a={};epochs_b=[];histories_b={}
            writes=tuple(writer.db.total_changes for writer in f.indexes)
            default=p.lineage.financial(p,header,block,life,local,f.ids[0],1,
                verified_epochs=epochs_a,verified_histories=histories_a)
            explicit=p.lineage.financial(p,header,block,life,local,f.ids[0],1,
                verified_epochs=epochs_b,verified_histories=histories_b,
                history_reader=p.earnings_history.history_snapshot)
            with self.subTest(epochs=count):
                self.assertEqual(default,explicit)
                self.assertEqual(epochs_a,epochs_b);self.assertEqual(count,len(epochs_a))
                self.assertEqual(histories_a,histories_b)
                self.assertEqual({cfg['contracts']['access']['address']for cfg in f.configs},set(histories_a))
                self.assertTrue(all(history.provenance['minted_count']==3 for history in histories_a.values()))
                native=next(row for row in default['previously_claimed']['assets']if row['asset']==ZERO)
                # Literal controlled-fixture quantities: the original39+5 ZZZ
                # reward is converted1:1 and claimed with39+5 native rewards.
                self.assertEqual(('88','10'),(native['lp_raw'],native['royalties_raw']))
                converted=default['lp_conversions']
                self.assertEqual('44',converted['total_eth_credited_raw'])
                self.assertEqual([('44','44',1)],[(row['source_converted_raw'],row['eth_credited_raw'],
                    row['event_count'])for row in converted['assets']])
                self.assertEqual(writes,tuple(writer.db.total_changes for writer in f.indexes))
                self.assertFalse(any('sign' in method or 'send' in method for method,_ in f.calls))
            receipt=f.receipts[f.transition_tx(0)];receipt['status']='0x0'
            for reader in (None,p.earnings_history.history_snapshot):
                with self.subTest(epochs=count,raw_default=reader is None),self.assertRaises(HistoryError):
                    p.lineage.financial(p,header,block,life,local,f.ids[0],1,history_reader=reader)


if __name__=='__main__':unittest.main()
