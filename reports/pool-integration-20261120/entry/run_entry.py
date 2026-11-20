"""New finite Entry/NFT partition against the supplied real-core pool fork.

No production source changes, public transactions or existing-node access. The
full F6 graph is new integration setup; source/VRF/SeaDrop/depth seams are explicit.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,importlib.util,json,os,sys,time,zipfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
HERE=Path(__file__).resolve().parent
def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
L=mod(ROOT/'reports/pool-lifecycle-20261120/run/run_pool.py','entry_prior_physical')
N=mod(ROOT/'reports/full-claim-admission-20261120/tools/native_fixture.py','entry_prior_normal_fixture')
W=mod(ROOT/'reports/pool-integration-20261120/swap/warm_cache.py','entry_prior_warm_cache')
from zzz_ops.deployment_plan import Artifacts
from zzz_ops.abi import keccak256

ZERO=L.ZERO;ZZZ=L.ZZZ;OWNER=L.OWNER;POOL=L.POOL;UNIT=10**18
REVIEW='0x'+keccak256(b'FINITE REAL CORE ENTRY NFT PARTITION; CORRELATED FIXTURE PRICES').hex()
def save(path,value):return N.save(path,value)
def sha(raw):return hashlib.sha256(raw).hexdigest()

class Node(L.Node):
    def __init__(self,*args):
        super().__init__(*args);self.phase='construction';self.reviewed=None;self.code_pins={};self.ownership=[]
    @property
    def proc(self):return self.process
    @property
    def records(self):return self.wire
    def guard(self):
        assert self.process is not None and self.process.poll()is None
        assert self.owner()=={self.process.pid}
        assert int(self.call('eth_chainId'),16)==4663
        assert self.call('eth_getBlockByNumber',[hex(L.BLOCK),False])['hash']==L.HASH
    def mutate(self,method,params):
        self.guard()
        if method=='eth_sendTransaction':
            assert len(params)==1 and params[0]['from']==OWNER
            if self.phase=='construction':assert params[0]['value']=='0x0'
            else:assert self.reviewed==params[0];self.reviewed=None
        elif method=='anvil_impersonateAccount':assert params==[OWNER]
        elif method=='evm_mine':assert params==[]
        else:raise ValueError('Mutation outside closed integration envelope')
        return self.call(method,params)

class WireAdapter:
    """Expose the unmodified constructor runner's interface to our PID owner."""
    def __init__(self,node):self.node=node
    def __getattr__(self,name):return getattr(self.node,name)
    def __setattr__(self,name,value):
        if name=='node':object.__setattr__(self,name,value)
        else:setattr(self.node,name,value)
    def wire(self,method,params=None,mutation=False):return self.node.call(method,params or [])

class Fixture(N.NativeF6Fixture):
    def __init__(self,out,node):
        self.output=out;self.node=WireAdapter(node);self.rpc=self.node;self.receipts=[];self.ids=[];self.contracts={};self.runtime_pins={};self.owner=OWNER;self.assets=[];self.helpers={};self.created=True
        self.artifacts=Artifacts();self.deadlines=[];self.states=[]
    def helpers_from_evidence(self):
        prior=V/'full-claim-admission-20261120/attempt02/helper-source.json';prior_raw=prior.read_bytes()
        assert sha(prior_raw)=='ba2175535ed6bf7554acceb0ec32e2d281a42ce55b2fbf520c1e3acafa63817c'
        trusted=json.loads(prior_raw)
        old=ROOT/'reports/source9-actual-entry-20261109/campaign-evidence.zip'
        assert sha(old.read_bytes())==trusted['depth']['archive_sha256']
        with zipfile.ZipFile(old)as z:
            raw=z.read('source9-depth-seeder-compile-attempt1/Source9DepthSeeder.object.json');obj=json.loads(raw)
            assert sha(raw)==trusted['depth']['member_sha256']
            source=ROOT/'test/local/Source9DepthSeeder.sol';assert sha(source.read_bytes())==obj['source_sha256']
            self.helpers['Source9DepthSeeder']=obj['artifact'];depth={'archive_sha256':sha(old.read_bytes()),'member_sha256':sha(raw),'source_sha256':sha(source.read_bytes())}
        path=V/'fresh-entry3-rehearsal-fixture-compile-subagent1'
        inp=json.loads((path/'fixture-compiler-input.json').read_bytes());raw=(path/'fixture-compiler-stdout.json').read_bytes();compiled=json.loads(raw)
        assert sha((path/'fixture-compiler-input.json').read_bytes())==trusted['fixtures']['input_sha256']and sha(raw)==trusted['fixtures']['output_sha256']
        source='test/local/Source9RehearsalFixtures.sol'
        assert inp['sources'][source]['content'].replace('\r\n','\n')==(ROOT/source).read_text().replace('\r\n','\n')
        assert not any(x.get('severity')=='error'for x in compiled.get('errors',[]))
        self.helpers.update(compiled['contracts'][source])
        save(self.output/'HELPER_REUSE.json',{'depth':depth,'fixture_input_sha256':sha((path/'fixture-compiler-input.json').read_bytes()),'fixture_output_sha256':sha(raw),'source_sha256':sha((ROOT/source).read_bytes()),'compiler_run':False})
    def construct(self):
        out=self.output/'construction';out.mkdir()
        case=N.M.Rehearsal(self.node,self.artifacts,out);result=case.run();save(out/'RESULT.json',result)
        self.construction=case;rows=json.loads((out/'instances.json').read_bytes())
        self.contracts={x['role']:x['address']for x in rows};self.runtime_pins={x['role']:x['runtime_keccak256']for x in rows}
        self.contracts.update(N.P.NATIVE);self.contracts['seadrop']=N.P.SEADROP
        self.contracts['royalties']=self.contracts['royalty_rewards']
        self.node.phase='setup'
    def deadline(self):
        assert self.node.pending is None
        self.node.mutate('evm_mine',[]);head=self.rpc.call('eth_getBlockByNumber',['latest',False]);now=int(head['timestamp'],16)
        expiry=now+300;self.deadlines.append({'header':head,'deadline':expiry,'ttl_seconds':300});return expiry
    def configure_fork(self):
        slot=N.words(self.rpc.call('eth_call',[{'to':L.STATE,'data':L.abi('getSlot0(bytes32)',POOL)},'latest']))
        assert slot[0]>0 and slot[3]==10020
        self.priceETH=2000*UNIT;self.priceZZZ=self.priceETH*(1<<192)//slot[0]**2
        self.initial_slot=slot
        # Explicit local token balance substitute, not token issuance/supply proof.
        key='0x'+keccak256(L.word(OWNER)+L.word(0)).hex();amount=100_000_000*UNIT
        before=self.rpc.call('eth_getStorageAt',[ZZZ,key,'latest'])
        assert int(before,16)==self.read(ZZZ,'balanceOf(address)',OWNER)[0]
        self.rpc.call('anvil_setStorageAt',[ZZZ,key,'0x'+L.word(amount).hex()])
        assert self.read(ZZZ,'balanceOf(address)',OWNER)==[amount]
        save(self.output/'LOCAL_TOKEN_FUNDING.json',{'token':ZZZ,'owner':OWNER,'verified_slot':key,'before':before,'after':str(amount),'local_only':True,'supply_proof':False})
        # Three separately owned, non-PoPL synthetic core positions. Their price
        # is unchanged by mint, and they remain outside PoPL NAV/accounting.
        seederL=20*UNIT*slot[0]//(1<<96)
        for i in range(3):
            role='external_depth_'+str(i);seeder=self.deploy(role,'Source9DepthSeeder')
            tokenBudget=(seederL*slot[0]+(1<<96)-1)//(1<<96)+1
            assert 0<tokenBudget<=100_000_000*UNIT and tokenBudget<=self.read(ZZZ,'balanceOf(address)',OWNER)[0]
            self.configure('zzz','approve(address,uint256)',seeder,tokenBudget)
            self.configure(role,'seed(uint128,uint256)',seederL,tokenBudget,value=100*UNIT)
            assert self.read(ZZZ,'allowance(address,address)',OWNER,seeder)==[0]
            self.configure('zzz','approve(address,uint256)',seeder,0)
            assert self.read(ZZZ,'allowance(address,address)',OWNER,seeder)==[0]
        self.externalL=self.read(L.STATE,'getLiquidity(bytes32)',POOL)[0]
        assert self.externalL==3*seederL
        for asset,price,role in ((ZERO,self.priceETH,'eth'),(ZZZ,self.priceZZZ,'zzz')):
            pair=[]
            for suffix in ('a','b'):
                f=self.deploy(role+'_feed_'+suffix,'Source9RehearsalFeed',price)
                pair.extend((f,self.codehash(f),N.bytes_hash(('CORRELATED '+role+suffix).encode()),86400,18))
            self.configure('oracle','setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)',asset,*pair,300,REVIEW)
        self.configure('activation_assets','configureZZZ(address,bytes32,bytes32)',ZZZ,'0x'+L.PINS[ZZZ],REVIEW)
        self.configure('activation_assets','setAsset(address,bool,bytes32,bytes32)',ZERO,1,N.bytes_hash(b'ZZZ_NATIVE_ETH_V1'),REVIEW)
        self.configure('rewards','addAsset(address)',ZZZ)
        self.configure('migration','configureZZZ(address,bytes32,bytes32)',ZZZ,'0x'+L.PINS[ZZZ],REVIEW)
        vrf=self.deploy('vrf','Source9RehearsalVRF')
        self.configure('protocol_policy','configureRandomness(address,bytes32,bytes32,uint256,uint16,uint32,bool,bytes32)',vrf,self.codehash(vrf),1,1,3,500000,0,REVIEW)
        now=int(self.rpc.call('eth_getBlockByNumber',['latest',False])['timestamp'],16);self.sale_end=now+1800
        config=[0,0,1000,1000,10,1,2,3,4,5,self.sale_end,1,0,N.FEE,N.bytes_hash(bytes.fromhex(N.word(32)+N.word(0)))]
        self.configure('seadrop_mint','configure((uint16,uint16,uint16,uint16,uint8,uint48,uint48,uint48,uint48,uint48,uint48,bool,bytes32,address,bytes32),uint128,bytes32)',*config,5*10**16,REVIEW)
        self.configure('nft','setMintEnd(uint64)',self.sale_end)
        self.configure('nft','updatePublicDrop(address,(uint80,uint48,uint48,uint16,uint16,bool))',N.P.SEADROP,5*10**16,5,self.sale_end,1000,1000,1)
        body=N.word(N.P.SEADROP)+N.word(64)+N.word(0)+N.word(96)+N.word(128)+N.word(0)+N.word(0)
        self.send('configure:nft:updateAllowList','nft','0x'+keccak256(b'updateAllowList(address,(bytes32,string[],string))')[:4].hex()+body)
        self.configure('nft','updateCreatorPayoutAddress(address,address)',N.P.SEADROP,N.M.PAYEE)
        self.configure('nft','updateAllowedFeeRecipient(address,address,bool)',N.P.SEADROP,N.FEE,1)
        key=[ZERO,ZZZ,10020,200,ZERO];config=[*key,1,1,5000,500,100,200,43200,5*UNIT,1_000_000*UNIT]
        self.configure('pools','configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))',*config)
        self.send('configure:balancer:executionPools','balancing_router',N.encode('configureExecutionPools(bytes32[],bytes32)',64,REVIEW,1,POOL))
        self.configure('strategy','setRangeOrientation(bytes32,uint8)',POOL,1)
        self.configure('rebalance_confirmation','configure(uint32,uint32,bytes32)',600,300,REVIEW)
        self.configure('access','setKeeper(address,bool)',OWNER,1)
        self.node.guard();assert self.codehash(self.contracts['access'])==self.runtime_pins['access']
        local_seal=self.configure('access','seal()')
        assert self.read('access','isSealed()')==[1]and self.read('access','bootstrap()')==[0]
        save(self.output/'LOCAL_SEAL.json',{'access':self.contracts['access'],'owned_pid':self.node.proc.pid,'owned_port':self.node.port,'transaction_hash':local_seal['receipt']['transactionHash'],'receipt_status':local_seal['receipt']['status'],'new_fixture_only':True,'public_or_existing_sealing':False})
    def state(self,label):
        bucket=self.read('vault','poolBucket(bytes32)',POOL)[0]
        row={'label':label,'header':self.rpc.call('eth_getBlockByNumber',['latest',False]),'bucket':str(bucket),'ids':list(map(str,self.ids)),
             'eligible_total':self.read('membership','totalEligible()')[0],'activation_count':self.read('royalties','activationCount()')[0],
             'owner':[self.read('nft','ownerOf(uint256)',i)[0]for i in self.ids],
             'eligible':[self.read('membership','eligible(uint256)',i)[0]for i in self.ids],
             'shares':[self.read('vault','sharesOf(uint256)',i)[0]for i in self.ids],
             'contribution_usd':[self.read('vault','contributionUSD(uint256)',i)[0]for i in self.ids],
             'lp_claim_ETH':[self.read('rewards','claimable(uint256,address)',i,ZERO)[0]for i in self.ids],
             'lp_claim_ZZZ':[self.read('rewards','claimable(uint256,address)',i,ZZZ)[0]for i in self.ids],
             'entry_balances':[int(self.rpc.call('eth_getBalance',[self.contracts['activation_entry'],'latest']),16),self.read(ZZZ,'balanceOf(address)',self.contracts['activation_entry'])[0]],
             'vault_balances':[int(self.rpc.call('eth_getBalance',[self.contracts['vault'],'latest']),16),self.read(ZZZ,'balanceOf(address)',self.contracts['vault'])[0]]}
        if bucket:
            group=self.read('vault','group(uint256)',bucket);main=group[1]
            row.update(group=group,main=str(main),mainL=self.read(L.POSM,'getPositionLiquidity(uint256)',main)[0],ticks=self.read('liquidity','ticks(uint256)',main),secondary=self.read('liquidity','secondaryId(uint256)',main)[0],total_shares=self.read('vault','bucketTotalShares(uint256)',bucket)[0],main_owner=self.read(L.POSM,'ownerOf(uint256)',main)[0],amounts=self.read('liquidity','amounts(uint256)',main),allocation_tree=self.read('rewards','allocationTree(uint256)',bucket))
        self.states.append(row);save(self.output/f'state-{len(self.states):02d}.json',row);return row
    def contribution(self,label,index,asset,amount,increase):
        before=self.state(label+':before');id=self.ids[index];fingerprint=self.read('protocol_policy','entryFingerprint()')[0]
        if asset!=ZERO:
            self.configure('zzz','approve(address,uint256)',self.contracts['activation_entry'],amount)
            assert self.read(ZZZ,'allowance(address,address)',OWNER,self.contracts['activation_entry'])==[amount]
        deadline=self.deadline()
        row=self.send(label,'activation_entry',N.encode('executeReviewed((uint256,bytes32,address,uint256,uint128,uint256,bool),uint16,bytes32)',id,POOL,asset,amount,1,deadline,int(increase),300,fingerprint),value=amount if asset==ZERO else 0,cap=32_000_000,padding=2000)
        after=self.state(label+':after');assert after['shares'][index]>before['shares'][index]
        trace=self.rpc.call('debug_traceTransaction',[row['receipt']['transactionHash'],{'tracer':'callTracer'}])
        frames=[]
        def visit(frame):
            frames.append(frame)
            for child in frame.get('calls',[]):visit(child)
        visit(trace)
        selector='0x'+keccak256(b'contributionResult(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint32)')[:4].hex()
        results=[f for f in frames if f.get('to','').lower()==self.contracts['migration_budget']and f.get('input','').startswith(selector)]
        assert len(results)==1
        args=N.words('0x'+results[0]['input'][10:]);actual=N.words(results[0]['output'])
        bucket,inputUSD,supply,incumbentNAV,incumbentDeployed,deployed,idle,limits=args
        net=deployed+idle-incumbentNAV;issued=net if supply==0 else supply*net//incumbentNAV
        assert supply==sum(before['shares'])and actual==[issued,net]and issued==after['shares'][index]-before['shares'][index]
        assert deployed-incumbentDeployed>=inputUSD-(inputUSD*300//10000)and net>=inputUSD-(inputUSD*300//10000)
        assert limits>>16==300 and idle<=(deployed+idle)*500//10000
        row['independent_share_replay']={'budget_arguments':list(map(str,args)),'actual_return':list(map(str,actual)),'recomputed_net_usd':str(net),'recomputed_issued_shares':str(issued),'source_loss_bps':300,'idle_cap_bps':500}
        save(self.output/(label+'-trace.json'),trace);save(self.output/(label+'-share-replay.json'),row['independent_share_replay'])
        assert after['owner']==[int(OWNER,16)]*2 and after['main_owner']==int(self.contracts['vault'],16)
        assert after['total_shares']==sum(after['shares'])and after['allocation_tree'][0]==after['total_shares']
        assert after['secondary']==0 and after['entry_balances']==[0,0]
        assert self.read(ZZZ,'allowance(address,address)',OWNER,self.contracts['activation_entry'])==[0]
        for a,b in ((self.contracts['activation_entry'],self.contracts['vault']),(self.contracts['vault'],self.contracts['liquidity']),(self.contracts['vault'],self.contracts['lp_position_executor']),(self.contracts['liquidity'],L.PERMIT2),(self.contracts['lp_position_executor'],L.PERMIT2)):
            assert self.read(ZZZ,'allowance(address,address)',a,b)==[0]
        if before.get('main'):
            assert after['main']==before['main']and after['mainL']>before['mainL']and after['ticks']==before['ticks']
            assert after['group'][5:7]==before['group'][5:7]
            for j in range(2):
                if j!=index:assert after['shares'][j]==before['shares'][j]
        if not increase:
            assert after['eligible_total']==before['eligible_total']+1 and after['activation_count']==before['activation_count']+1
            assert after['lp_claim_ETH'][index]==0 and after['lp_claim_ZZZ'][index]==0
        else:assert after['eligible_total']==before['eligible_total']and after['activation_count']==before['activation_count']
        return row

def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);args=p.parse_args()
    assert args.attempt.isalnum();out=V/'pool-integration-20261120/entry'/args.attempt;out.mkdir(parents=True,exist_ok=False)
    L.OUT=out;L.READS|={'debug_traceTransaction'};L.LOCAL|={'anvil_setCode'}
    fixture=None
    try:
        with W.cached_fork_provider(L.PUBLIC_ENDPOINT,L.BLOCK,L.HASH,out/'relay',requests_per_second=.5)as relay:
          with Node(relay.url)as n:
            assert all('0x'+keccak256(bytes.fromhex(n.call('eth_getCode',[a,'latest'])[2:])).hex()=='0x'+h for a,h in L.PINS.items())
            assert int(n.read(L.STATE,'getLiquidity(bytes32)',POOL),16)==0
            save(out/'PRISTINE.json',{'block':L.BLOCK,'hash':L.HASH,'active_L':'0','pool':POOL,'real_dependencies':L.PINS,'local_mutations_not_started':True})
            n.guard();n.call('anvil_impersonateAccount',[OWNER]);n.call('anvil_setBalance',[OWNER,hex(1000*UNIT)])
            # Exact official runtime, but this is controlled local materialization,
            # not a claim that Robinhood/OpenSea supports this release.
            runtime=(ROOT/'reports/opensea-integration-20261109/official-seadrop/derived/deployed-runtime.hex').read_text().strip()
            assert '0x'+keccak256(bytes.fromhex(runtime.removeprefix('0x'))).hex()==N.P.SEADROP_HASH
            prior=n.call('eth_getCode',[N.P.SEADROP,'latest']);n.call('anvil_setCode',[N.P.SEADROP,runtime])
            n.call('anvil_setStorageAt',[N.P.SEADROP,'0x'+L.word(0).hex(),'0x'+L.word(1).hex()])
            save(out/'SEADROP_SEAM.json',{'address':N.P.SEADROP,'previous_runtime_sha256':sha(bytes.fromhex(prior.removeprefix('0x'))),'materialized_runtime_keccak':N.P.SEADROP_HASH,'guard_slot0':1,'actual_platform_qualified':False})
            fixture=Fixture(out,n);fixture.helpers_from_evidence();fixture.construct();fixture.configure_fork()
            fixture.configure('seadrop','mintPublic(address,address,address,uint256)',fixture.contracts['nft'],N.FEE,ZERO,2,value=10**17,cap=32_000_000)
            for ordinal in (1,2):
                identifier=fixture.read('nft','tokenAtOrdinal(uint256)',ordinal)[0];fixture.ids.append(identifier)
                req=fixture.read('nft','requestOf(uint256)',identifier)[0]
                fixture.configure('vrf','fulfill(uint256,uint256,uint256)',req,0,ordinal)
                fixture.configure('nft','finalizeTraits(uint256)',identifier)
            # All calls use current defaults, including 3% source contribution cap.
            fixture.contribution('new_ETH_activation',0,ZERO,55*10**15,False)
            zzz_activation=(110*UNIT*UNIT+fixture.priceZZZ-1)//fixture.priceZZZ
            fixture.contribution('new_ZZZ_activation',1,ZZZ,zzz_activation,False)
            fixture.contribution('new_ETH_growth',0,ZERO,10**16,True)
            zzz_growth=(20*UNIT*UNIT+fixture.priceZZZ-1)//fixture.priceZZZ
            fixture.contribution('new_ZZZ_growth',1,ZZZ,zzz_growth,True)
            fixture.artifacts.check_sources()
            save(out/'RESULT.json',{'successful':True,'finite_nfts':2,'current_normal_instances':39,'contributions':4,'activation_assets':['ETH','fixedZZZ'],'growth_assets':['ETH','fixedZZZ'],'production_approved':False,'source_unchanged':True,'seams':['exact archived SeaDrop local code/guard materialization','controlled VRF','correlated fixed USD feed pairs','local ETH/ZZZ balance substitute','three synthetic non-PoPL core positions'],'excluded':['independent price sources','actual external depth','VRF cryptography/service','actual OpenSea acceptance','hybrid/1000NFT/64currency workload','target fees/provider/release']})
            save(out/'DEADLINES.json',fixture.deadlines);save(out/'STATES.json',fixture.states)
    except BaseException as exc:
        save(out/'FAILED.json',{'type':type(exc).__name__,'reason':str(exc),'automatic_retry':False,'production_approved':False});raise
    finally:
        if fixture:
            save(out/'ALL_SETUP_SCENARIO_RECEIPTS.json',fixture.receipts)
            save(out/'SOURCE_STAGE.json',{'driver_sha256':sha(Path(__file__).read_bytes()),'normal_build':fixture.artifacts.profile,'source_pins':fixture.artifacts.source_pins,'build_pins':fixture.artifacts.file_pins,'prior_node_source_sha256':sha((ROOT/'reports/pool-lifecycle-20261120/run/run_pool.py').read_bytes()),'prior_native_fixture_sha256':sha((ROOT/'reports/full-claim-admission-20261120/tools/native_fixture.py').read_bytes()),'compiler_run':False})
    return 0
if __name__=='__main__':raise SystemExit(main())
