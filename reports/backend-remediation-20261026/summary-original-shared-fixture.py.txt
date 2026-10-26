import unittest
from types import SimpleNamespace
from frontend_api.portfolio import read
from frontend_api.service import ProjectionError, ZERO
from frontend_api.history import HistoryError
from zzz_ops.errors import RpcError, WorkLimit

OWNER='0x'+'1'*40
OTHER='0x'+'2'*40
HASH='0x'+'a'*64

class Snapshot:
    def __init__(self,count=33):
        self.ids=list(range(1,count+1));self.history=True;self.chain=31337;self.start=1
        self.max_age=120;self.clock=lambda:1000;self.confirmations=1;self.identity='d'*64
        self.contracts={'nft':SimpleNamespace(address='0x'+'3'*40)}
        self.header=dict(number=90,hash=HASH,timestamp=990);self.calls=[]
        self.lp_missing=None;self.eth_missing=None;self.bad_owner=None;self.changed=False;self.limit=False
    def _snapshot(self):return dict(self.header,number=100),100,{}
    def _header(self,tag):return self.header
    def _fresh(self,h):
        if h['timestamp']<880:raise ProjectionError('stale')
    def _verify_deployment(self,block):return {'state':'operating'}
    def _admitted(self,block,**kwargs):return [ZERO],[ZERO]
    def _history_snapshot(self,*args):return SimpleNamespace(owners={i:OWNER for i in self.ids})
    def _uint(self,role,method,*args,block):
        self.calls.append((method,args,block));self.check(block)
        if method.startswith('balanceOf'):return len(self.ids)
        if args[0]==self.eth_missing:raise RpcError('unreadable')
        return args[0]*(2 if role=='rewards' else 3)
    def _addr(self,role,method,i,block):
        self.calls.append((method,(i,),block));self.check(block)
        return OTHER if i==self.bad_owner else OWNER
    def _call(self,target,method,i,block,words):
        self.calls.append((method,(i,),block));self.check(block)
        if self.limit:raise WorkLimit('rpc_budget')
        return [f'{int(i!=self.lp_missing):064x}',f'{i*100 if i!=self.lp_missing else 0:064x}']
    def check(self,block):
        assert block=={'blockHash':HASH,'requireCanonical':True}
    def _finish(self,h):
        if self.changed:raise ProjectionError('reorg')

class WalletSummaryTests(unittest.TestCase):
    def test_all_chunks_cover_every_holding_once(self):
        p=Snapshot();parts=[read(p,OWNER,90,i) for i in (0,16,32)]
        self.assertEqual([x['next_offset'] for x in parts],[16,32,None])
        self.assertEqual(sum(int(x['lp_usd_18']) for x in parts),sum(p.ids)*100)
        self.assertEqual(sum(int(x['claimable_eth_wei']) for x in parts),sum(p.ids)*5)
        self.assertEqual(len({x['inventory_sha256'] for x in parts}),1)
        self.assertEqual([i for x in parts for i in x['token_ids']],list(map(str,p.ids)))
    def test_one_chunk_work_is_bounded_at_collection_cap(self):
        p=Snapshot(1000);r=read(p,OWNER,90,992)
        self.assertEqual(len(r['token_ids']),8);self.assertIsNone(r['next_offset'])
        self.assertLessEqual(len(p.calls),1+8*4)
    def test_empty_wallet_is_verified_zero(self):
        r=read(Snapshot(0),OWNER,90,0)
        self.assertEqual((r['lp_usd_18'],r['claimable_eth_wei']),('0','0'))
        self.assertEqual(r['token_ids'],[]);self.assertIsNone(r['next_offset'])
    def test_unavailable_lp_does_not_mask_eth(self):
        p=Snapshot();p.lp_missing=1;r=read(p,OWNER,90,0)
        self.assertIsNone(r['lp_usd_18']);self.assertEqual(r['claimable_eth_wei'],str(sum(range(1,17))*5))
    def test_unavailable_eth_is_never_partial_or_zero(self):
        p=Snapshot();p.eth_missing=2;r=read(p,OWNER,90,0)
        self.assertIsNone(r['claimable_eth_wei']);self.assertIsNotNone(r['lp_usd_18'])
    def test_wrong_owner_fails_entire_chunk(self):
        p=Snapshot();p.bad_owner=8
        with self.assertRaises(HistoryError):read(p,OWNER,90,0)
    def test_reorg_fails_entire_chunk(self):
        p=Snapshot();p.changed=True
        with self.assertRaises(ProjectionError):read(p,OWNER,90,0)
    def test_stale_snapshot_rejected(self):
        p=Snapshot();p.header['timestamp']=1
        with self.assertRaises(ProjectionError):read(p,OWNER,90,0)
    def test_unconfirmed_block_rejected(self):
        with self.assertRaises(ProjectionError):read(Snapshot(),OWNER,101,0)
    def test_invalid_cursor_rejected(self):
        for offset in (-1,1,1000,False,'16'):
            with self.subTest(offset=offset),self.assertRaises(ValueError):read(Snapshot(),OWNER,90,offset)
    def test_budget_failure_not_swallowed_as_missing_price(self):
        p=Snapshot();p.limit=True
        with self.assertRaises(WorkLimit):read(p,OWNER,90,0)
    def test_past_end_rejected(self):
        with self.assertRaises(ValueError):read(Snapshot(1),OWNER,90,16)

if __name__=='__main__':unittest.main()
