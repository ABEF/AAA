"""NEW constructor-read protocol checks; no historical test bodies selected."""
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from frontend_api import canonical_cache as cache
from frontend_api import read_batch as batch
from frontend_api.service import Projection, ProjectionError
from zzz_ops.abi import calldata, keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope

ROOT = Path(__file__).resolve().parents[1]
HEADER = {'blockHash':'0x'+'a1'*32,'requireCanonical':True}
MODULES = tuple('0x'+f'{v:040x}' for v in (10,11,12,13))
ETH = '0x'+'0'*40
ZZZ = '0x'+f'{40:040x}'
CURRENCIES = (ETH,'0x'+f'{41:040x}','0x'+f'{42:040x}','0x'+f'{43:040x}')
OWNER = '0x'+f'{99:040x}'


def integer(value):
    return int(value).to_bytes(32,'big')


def decode_creation(tx):
    """Independent ABI decoder, not the production argument encoder."""
    creation = bytes.fromhex(json.loads((ROOT/batch.FILES[1]).read_bytes())['creation_bytecode'][2:])
    raw = bytes.fromhex(tx['data'][2:])
    if raw[:len(creation)] != creation:
        raise AssertionError('Unexpected creation program')
    raw = raw[len(creation):]
    values = [int.from_bytes(raw[i:i+32],'big') for i in range(0,len(raw),32)]
    if len(raw)%32 or values[4]!=256:
        raise AssertionError('Noncanonical constructor arguments')
    modules = tuple('0x'+f'{x:040x}' for x in values[:4])
    n = values[8]
    ids = tuple(values[9:9+n])
    if values[7] != (9+n)*32:
        raise AssertionError('Unexpected royalty argument offset')
    royalty_index = values[7]//32
    count = values[royalty_index]
    royalties = tuple('0x'+f'{v:040x}' for v in values[royalty_index+1:])
    if len(royalties)!=count or len(raw)!=(royalty_index+1+count)*32:
        raise AssertionError('Unexpected trailing arguments')
    return raw,modules,ids,tuple('0x'+f'{x:040x}' for x in values[5:7]),royalties


def getter_rows(modules,ids,pair,royalties):
    for i in ids:
        ordinal=i+7
        yield modules[0],'ownerOf(uint256)',(i,),1,(int(OWNER,16),0)
        yield modules[0],'mintOrdinalOf(uint256)',(i,),1,(ordinal,0)
        yield modules[0],'tokenAtOrdinal(uint256)',(ordinal,),1,(i,0)
        yield modules[1],'sharesOf(uint256)',(i,),1,(i*10,0)
        yield modules[1],'nftBucket(uint256)',(i,),1,(1,0)
        yield modules[2],'weightOf(uint256)',(i,),1,(i%3+1,0)
        yield modules[3],'rewardBucket(uint256)',(i,),1,(1,0)
        for a in pair:
            yield modules[3],'claimableComponents(uint256,address)',(i,a),2,(13*i,7*i)
        for a in pair:
            yield modules[3],'claimable(uint256,address)',(i,a),1,(20*i,0)
        for a in royalties:
            yield modules[2],'claimable(uint256,address)',(i,a),1,(31*i+int(a,16),0)


class FixtureRPC:
    def __init__(self):
        self.calls=[]
        self.groups=[]
        self.fail=None
        self.malformed=None
        self.mutate_header=False

    def call(self,method,params=None):
        self.calls.append((method,params))
        if method!='eth_call' or set(params[0])!={'from','value','gas','data'}:
            raise AssertionError('Unexpected ordinary fallback or RPC method')
        tx,header=params
        if tx['from']!=ETH or tx['value']!='0x0' or tx['gas']!=hex(24_000_000) or header!=HEADER:
            raise AssertionError('Unexpected call envelope')
        arguments,modules,ids,pair,royalties=decode_creation(tx)
        if not 1<=len(ids)<=3 or len(royalties)>4:
            raise AssertionError('Batch input bound differs')
        self.groups.append(ids)
        rows=list(getter_rows(modules,ids,pair,royalties))
        result=keccak256(b'POPL_WALLET_STATIC_READ_BATCH_V1')+integer(31337)+keccak256(arguments)+integer(len(rows))
        for target,sig,args,words,values in rows:
            identity=(target,sig,args)
            status=0 if identity==self.fail else 2 if identity==self.malformed else 1
            result+=integer(status)+b''.join(integer(v if status==1 else 0) for v in values)
        if self.mutate_header:
            result=result[:32]+integer(1)+result[64:]
        return '0x'+result.hex()


class View:
    _call=Projection._call
    _uint=Projection._uint
    _addr=Projection._addr

    def __init__(self,rpc):
        self.rpc=BudgetedRPC(rpc)
        self.chain=31337
        self.accounting_version=7
        self.assets={a:None for a in (ZZZ,*CURRENCIES)}
        self.contracts={r:SimpleNamespace(address=a) for r,a in zip(('nft','vault','royalties','rewards'),MODULES)}


@contextmanager
def request(rpc=None):
    rpc=rpc or FixtureRPC()
    p=View(rpc)
    budget=Budget(seconds=25,calls=1024,posts=2048)
    with request_scope(budget),cache.scope(p):
        yield p,rpc,budget


class ReadBatchProtocolTests(unittest.TestCase):
    def test_constructor_artifact_is_exact_and_isolated_from_normal_graph(self):
        code=batch._creation()
        artifact=json.loads((ROOT/batch.FILES[1]).read_bytes())
        self.assertEqual(hashlib.sha256(code).hexdigest(),artifact['creation_sha256'])
        self.assertLess(len(code),49152)
        self.assertFalse(artifact['normal_F6_graph_changed'])
        self.assertFalse(artifact['deployment_authorized'])
        self.assertEqual([r['type'] for r in artifact['abi']],['constructor'])
        self.assertNotEqual(batch.MAGIC[0],0xef)

    def test_fixed_getters_seed_normal_projection_decoding_without_fallback(self):
        with request() as (p,rpc,budget):
            self.assertEqual(batch.prefetch_accounts(p,HEADER,(11,22),(ETH,ZZZ),CURRENCIES),1)
            self.assertEqual(p._addr('nft','ownerOf(uint256)',11,block=HEADER),OWNER)
            self.assertEqual(p._uint('nft','mintOrdinalOf(uint256)',22,block=HEADER),29)
            self.assertEqual(p._uint('nft','tokenAtOrdinal(uint256)',29,block=HEADER),22)
            self.assertEqual(tuple(int(w,16) for w in p._call(MODULES[3],
                'claimableComponents(uint256,address)',11,ETH,block=HEADER,words=2)),(143,77))
            self.assertEqual(p._uint('rewards','claimable(uint256,address)',11,ZZZ,block=HEADER),220)
            self.assertEqual(p._uint('royalties','claimable(uint256,address)',22,CURRENCIES[1],block=HEADER),723)
            self.assertEqual(len(rpc.calls),1)
            self.assertEqual(budget.calls,1023)

    def test_sixteen_accounts_are_six_bounded_calls_and_repeated_prefetch_is_zero(self):
        with request() as (p,rpc,budget):
            ids=tuple(range(1,17))
            self.assertEqual(batch.prefetch_accounts(p,HEADER,ids,(ETH,ZZZ),CURRENCIES),6)
            self.assertEqual(rpc.groups,[(1,2,3),(4,5,6),(7,8,9),(10,11,12),(13,14,15),(16,)])
            self.assertEqual(batch.prefetch_accounts(p,HEADER,ids,(ETH,ZZZ),CURRENCIES),0)
            self.assertEqual(len(rpc.calls),6)
            self.assertEqual(budget.calls,1018)
            self.assertEqual(p._uint('vault','sharesOf(uint256)',16,block=HEADER),160)

    def test_approved_child_budget_and_three_account_envelope_preserve_top_and_selection(self):
        self.assertEqual((batch.LP_GAS,batch.ACCOUNTS_PER_BATCH),(500_000,3))
        self.assertEqual((batch.CALL_GAS,batch.MAX_IDS,batch.PLAIN_GAS,batch.ROYALTY_GAS),
                         (24_000_000,16,50_000,1_000_000))
        children=3*(7*batch.PLAIN_GAS+4*batch.LP_GAS+4*batch.ROYALTY_GAS)
        returned=128+3*(11+4)*96
        self.assertEqual((children,returned),(19_050_000,4448))
        self.assertLess(children+returned*200, batch.CALL_GAS)

    def test_inner_revert_is_remembered_without_retry_and_cleared_at_scope_exit(self):
        rpc=FixtureRPC()
        rpc.fail=(MODULES[2],'claimable(uint256,address)',(11,CURRENCIES[1]))
        with request(rpc) as (p,_,budget):
            batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES)
            for _ in range(2):
                with self.assertRaisesRegex(RpcError,'batch getter failed'):
                    p._uint('royalties','claimable(uint256,address)',11,CURRENCIES[1],block=HEADER)
            self.assertEqual(batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES),0)
            self.assertEqual(len(rpc.calls),1)
        rpc.fail=None
        with request(rpc) as (p,_,budget):
            batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES)
            self.assertEqual(p._uint('royalties','claimable(uint256,address)',11,CURRENCIES[1],block=HEADER),382)
            self.assertEqual(len(rpc.calls),2)

    def test_malformed_getter_or_header_never_seeds_partial_answers(self):
        for kind in ('abi','header'):
            rpc=FixtureRPC()
            if kind=='abi':rpc.malformed=(MODULES[2],'weightOf(uint256)',(11,))
            else:rpc.mutate_header=True
            with self.subTest(kind=kind),request(rpc) as (p,_,budget):
                with self.assertRaises(ProjectionError):
                    batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES)
                self.assertFalse(cache.cached(p,HEADER,MODULES[0],calldata('ownerOf(uint256)',11))[0])
                self.assertEqual(len(rpc.calls),1)

    def test_cache_capacity_refuses_atomically_instead_of_uncached_fallback(self):
        with request() as (p,rpc,budget),patch.object(cache,'MAX_RETAINED_BYTES',16):
            with self.assertRaises(WorkLimit):
                batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES)
            self.assertFalse(cache.cached(p,HEADER,MODULES[0],calldata('ownerOf(uint256)',11))[0])
            self.assertEqual(len(rpc.calls),1)

    def test_existing_raw_reply_cannot_be_replaced_by_conflicting_batch(self):
        with request() as (p,rpc,budget):
            wire=calldata('ownerOf(uint256)',11)
            cache.prefetch(p,HEADER,[(MODULES[0],wire,'0x'+f'{100:064x}')])
            with self.assertRaisesRegex(ProjectionError,'Conflicting'):
                batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES)
            self.assertEqual(p._addr('nft','ownerOf(uint256)',11,block=HEADER),'0x'+f'{100:040x}')
            self.assertFalse(cache.cached(p,HEADER,MODULES[1],calldata('sharesOf(uint256)',11))[0])

    def test_invalid_selection_and_currency_order_refuse_before_rpc(self):
        invalid=[((11,11),CURRENCIES),(tuple(range(1,18)),CURRENCIES),((11,),CURRENCIES[::-1])]
        for ids,currencies in invalid:
            with self.subTest(ids=ids,currencies=currencies),request() as (p,rpc,budget):
                with self.assertRaises(ValueError):batch.prefetch_accounts(p,HEADER,ids,(ETH,ZZZ),currencies)
                self.assertEqual(rpc.calls,[])

    def test_artifact_tampering_refuses_without_any_rpc(self):
        original=Path.open
        def altered(path,*args,**kwargs):
            if str(path).replace('\\','/').endswith(batch.FILES[1]):return io.BytesIO(b'{}')
            return original(path,*args,**kwargs)
        batch._creation.cache_clear()
        try:
            with request() as (p,rpc,budget),patch.object(Path,'open',altered):
                with self.assertRaises(ProjectionError):batch.prefetch_accounts(p,HEADER,(11,),(ETH,ZZZ),CURRENCIES)
                self.assertEqual(rpc.calls,[])
        finally:
            batch._creation.cache_clear()
