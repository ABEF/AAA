"""Explicitly synthetic V10/current7 website producer scaffolding.

Every value here is controlled offline data. The production Projection,
ActivationConfig, ActivationTransactions and exact trace decoder remain real.
No historical actual EVM trace is copied, retagged or rewritten.
"""
from __future__ import annotations

import copy

from frontend_api.activation import ActivationTransactions
from frontend_api import activation_trace as T
from frontend_api.service import Projection, ZERO
from tests_python.test_seadrop_consumer import SeaDropAPI, V10
from tests_python.test_frontend_api import addr, words
from tests_python.test_dual_price_integration import make_policy, source_round, bounds
from zzz_ops import price_policy as D
from zzz_ops.abi import keccak256

USD = 10**18
ZERO_HASH = '0x' + '0'*64


def data(signature, *args):
    return T.static_data(signature, *args)


def bind_mint2(rpc, config, contracts, put):
    """Construct new controlled identity evidence, never mutate an old artifact."""
    config['mint_integration_version'] = 2
    for number, role in enumerate(('seadrop_mint', 'seadrop'), 15000):
        target, code = addr(number), '0x6002' + f'{number:04x}'
        contracts[role] = target
        rpc.codes[target] = code
        config['contracts'][role] = dict(address=target,
            code_hash='0x'+keccak256(bytes.fromhex(code[2:])).hex())
    for role, signature, value in (
            ('nft','seaDropMint()',contracts['seadrop_mint']),
            ('seadrop_mint','access()',contracts['access']),
            ('seadrop_mint','nft()',contracts['nft']),
            ('seadrop_mint','seaDrop()',contracts['seadrop']),
            ('seadrop_mint','MINT_INTEGRATION_VERSION()',1),
            ('seadrop_mint','seaDropCodeHash()',config['contracts']['seadrop']['code_hash']),
            ('handoff','SCHEMA()',V10)):
        put(contracts[role],signature,(),(value,))


class Current7Activation:
    """Complete current7/direct Entry3 preparation using a new synthetic trace.

    The fake pair uses equal $1 fixture prices and exact fixed geometry. This is
    intentionally not a claim about real ETH/ZZZ prices, liquidity or execution.
    """
    def __init__(self, case, *, increase=False, asset=ZERO, approval=False,
                 residual=False, loss_bps=300):
        self.f = SeaDropAPI(case)
        self.inner = self.f.rpc
        self.q = self.f.old.q
        self.c = {role:item['address'] for role,item in self.f.config['contracts'].items()}
        self.config = copy.deepcopy(self.f.config)
        self.codes = self.inner.codes
        self.responses = {}
        self.rows = []
        self.trace_count = 0
        self.increase = increase
        self.source = asset
        self.amount = (5 if increase else 100)*USD
        self.loss = loss_bps
        self.approval = approval
        self.bucket = 7
        self.main = 123
        self.pool = self.q.pool
        self.q.now = 4000
        self.q.tick = 0
        self.q.physical_side = self.q.reference = 0
        self.q.config[12] = USD
        self.q.config[13] = 1_000_000*USD
        if residual:
            self.q.secondary = 124
            self.q.secondary_count = 1
        # New typed helper identities are distinct from all read/currency pins.
        for n, role in enumerate(('oracle','entry','activation_assets','contribution_pricing','fees','membership'),20001):
            target, code = addr(n), '0x600a'+f'{n:04x}'
            self.c[role] = target
            self.codes[target] = code
        self.c['migration'] = self.c['principal_exit']
        self.pins = self.c
        for role in ('oracle','entry','activation_assets','contribution_pricing','fees','membership'):
            self.put(self.c[role],'access()',values=(self.c['access'],))
        for role,label in (('oracle','ZZZOracle'),('fees','ZZZFeeController'),('membership','ZZZMembership'),('migration','ZZZMigration')):
            self.put(self.c['access'],'module(bytes32)',('0x'+keccak256(label.encode()).hex(),),(self.c[role],))
        for role,method,target in (
                ('pools','activationEntry()','entry'),('pools','activationAssets()','activation_assets'),
                ('entry','registry()','pools'),('entry','activationAssets()','activation_assets'),
                ('activation_assets','registry()','pools'),('oracle','contributionPricing()','contribution_pricing'),
                ('contribution_pricing','oracle()','oracle')):
            self.put(self.c[role],method,values=(self.c[target],))
        for role,method,value in (
                ('entry','ENTRY_ROUTING_VERSION()',3),('entry','REVIEW_POLICY_VERSION()',2),
                ('contribution_pricing','ENTRY_REVIEW_VERSION()',2),('contribution_pricing','active()',0),
                ('oracle','PRICING_VERSION()',2),('oracle','sequencerFeed()',ZERO),
                ('oracle','activeSequencerPolicy()',ZERO_HASH),('oracle','policyCount()',2),
                ('activation_assets','SOURCE_POLICY_VERSION()',1),('activation_assets','zzz()',addr(20)),
                ('budget','MAX_LOSS_BPS()',1000),('budget','contributionLossBps()',loss_bps),
                ('liquidity','EXECUTION_QUALITY_VERSION()',1),('balancing_router','EXECUTION_QUALITY_VERSION()',1),
                ('strategy','EXECUTION_QUALITY_VERSION()',1),('balancing_router','MAX_ADDITIONAL_LOSS_BPS()',1000),
                ('strategy','MAX_ADDITIONAL_LOSS_BPS()',1000),('balancing_router','additionalLossBps()',100),
                ('strategy','additionalLossBps()',100),('strategy','executionQualityRevision()',1),
                ('portfolio_policy','thresholdBps()',8500),('portfolio_policy','revision()',1),
                ('balancing_router','executionRevision()',1),('pools','configurationRevision()',1),
                ('balancing_router','MAX_EXECUTION_POOLS()',4),('balancing_router','executionPoolCount()',1),
                ('balancing_router','searchIterations()',8),('balancing_router','quoteGasLimit()',200000)):
            self.put(self.c[role],method,values=(value,))
        self.put(self.c['balancing_router'],'executionPoolAt(uint256)',(0,),(self.pool,))
        self.put(self.c['pools'],'isNativePool(bytes32)',(self.pool,),(1,))
        self.put(self.c['strategy'],'RANGE_POLICY_VERSION()',values=(1,))
        self.put(self.c['strategy'],'rangeOrientation(bytes32)',(self.pool,),(1,))
        self.put(self.c['strategy'],'keeperRangePolicy(bytes32)',(self.pool,),(0,0,0,0,0,0,0))
        self.put(self.c['strategy'],'keeperRangeTarget(bytes32)',(self.pool,),(0,))
        self.put(self.c['portfolio_policy'],'controlFingerprint(bytes32)',(self.pool,),(101,))
        self.put(self.c['strategy'],'validatePrice(bytes32)',(self.pool,),(2**96,))
        self.put(self.c['strategy'],'needsRebalance(uint256)',(self.bucket,),(0,))
        self.put(self.c['strategy'],'rangeUpdatePending(uint256)',(self.bucket,),(0,))
        self.put(self.c['rebalance_confirmation'],'condition(uint256)',(self.bucket,),(0,0,0))
        self.put(self.c['rebalance_confirmation'],'observations(uint256)',(self.bucket,),(0,0,0,0))
        self.put(self.c['rebalance_confirmation'],'ready(uint256)',(self.bucket,),(0,))
        self.put(self.c['budget'],'rebalanceReady(uint256)',(self.bucket,),(0,))
        self.put(self.c['strategy'],'rebalanceReady(uint256)',(self.bucket,),(0,))
        for method, value in (('duration()',600),('MAX_DURATION()',604800),('maxObservationGap()',300),
                ('policyRevision()',1),('reviewHash()',1),('requireReferenceExit()',1),('referenceReviewHash()',0)):
            self.put(self.c['rebalance_confirmation'],method,values=(value,))
        self.put(self.c['nft'],'currentLPValue(uint256)',(self.inner.nft_id,),(1,1000*USD if increase else 0))
        self.put(self.c['vault'],'nftStatus(uint256)',(self.inner.nft_id,),(1 if increase else 3,))
        self.put(self.c['vault'],'contributionUSD(uint256)',(self.inner.nft_id,),(100*USD if increase else 0,))
        if not increase:
            for role,method in (('vault','nftBucket(uint256)'),('vault','sharesOf(uint256)'),
                    ('royalties','weightOf(uint256)'),('royalties','activationOrdinal(uint256)'),('royalties','ticketStart(uint256)')):
                self.put(self.c[role],method,(self.inner.nft_id,),(0,))
            for role,assets in (('rewards',(ZERO,addr(20))),('royalties',(ZERO,addr(21)))):
                for token in assets:
                    self.put(self.c[role],'claimable(uint256,address)',(self.inner.nft_id,token),(0,))
                    if role=='royalties':self.put(self.c[role],'eligibleFor(uint256,address)',(self.inner.nft_id,token),(0,))
        self.put(self.c['nft'],'mintedCount()',values=(444,))
        self.put(self.c['royalties'],'mintEndRevision()',values=(1,))
        terms=self.f.old.f.policy
        terms.set('entry',(100*USD,5*USD,500,2))
        for method in ('entryPolicy()','entryFingerprint()'):
            self.put(self.c['protocol_policy'],method,values=tuple(int(w,16) for w in terms.values[method]))
        self.tokens = []
        self.price_bounds = {}
        sources = []
        for i, token in enumerate((ZERO,addr(20))):
            admission = '0x'+keccak256(('synthetic-v10-admission-'+str(i)).encode()).hex()
            digest = None if token == ZERO else self.config['assets'][1]['code_hash']
            record = make_policy(token,18,self.c['oracle'],i,21000+2*i,
                '0x'+keccak256(b'synthetic-v10-dual-price').hex())
            record['policy']['maxDeviationBps'] = 300
            record['policy_id'] = D.policy_id(self.c['oracle'],i,record['policy'])
            self.tokens.append(dict(address=token,code_hash=digest,decimals=18,price_policy=record))
            self.put(self.c['oracle'],'activePolicy(address)',(token,),(record['policy_id'],))
            self.put(self.c['oracle'],'policyAt(uint256)',(i,),(record['policy_id'],))
            self.put(self.c['oracle'],'policy(bytes32)',(record['policy_id'],),D.flat(record['policy']))
            observed = bounds(record,self.c['oracle'],stamp=3980)
            self.price_bounds[token] = observed
            self.put(self.c['oracle'],'priceBounds(address)',(token,),tuple(observed[k] for k in ('lower','upper','fingerprint')))
            for role in ('primary','secondary'):
                feed = record['policy'][role]['source']
                self.codes[feed] = '0x'+b'synthetic-v10-dual-price'.hex()
                self.put(feed,'decimals()',values=(8,))
                self.put(feed,'latestRoundData()',values=source_round(10**8,3980))
            from frontend_api.activation_config import NATIVE_ASSET_CODE_HASH
            self.put(self.c['activation_assets'],'activePolicy(address)',(token,),(admission,))
            self.put(self.c['activation_assets'],'policies(bytes32)',(admission,),
                (token,1,NATIVE_ASSET_CODE_HASH if token==ZERO else digest,'0x'+'e'*64,18,1))
            self.put(self.c['activation_assets'],'isContributionAsset(address)',(token,),(1,))
            self.put(self.c['activation_assets'],'value(address,uint256)',(token,self.amount),(self.amount,))
            sources.append(dict(pool_id=self.pool,source_asset=token,asset_policy_id=admission))
        contracts = ('pools','oracle','liquidity','strategy','fees','membership','migration','entry',
            'activation_assets','budget','balancing_router','portfolio_policy','lp_balance_math',
            'lp_position_executor','protocol_policy','rebalance_confirmation','contribution_pricing')
        pin = lambda role:dict(address=self.c[role],code_hash='0x'+keccak256(bytes.fromhex(self.codes[self.c[role]][2:])).hex())
        self.activation_config = dict(schema=1,routing_version=3,pricing_version=2,review_policy_version=2,
            lp_routing_version=2,portfolio_version=2,execution_quality_version=1,maintenance_policy_version=3,
            rebalance_confirmation_version=3,range_policy_version=1,
            range_policies=[dict(pool_id=self.pool,orientation=1,keeper=dict(enabled=False,narrow_trigger_bps=0,
                widen_trigger_bps=0,minimum_interval_seconds=0,configuration_hash=ZERO_HASH,review_hash=ZERO_HASH))],
            contracts={role:pin(role) for role in contracts},tokens=self.tokens,
            dependencies=[pin(role) for role in ('pool_manager','state_view','position_manager','permit2')],
            sources=sources,sequencer=dict(address=ZERO,policy_id=ZERO_HASH),call_pins=[],storage_pins=[],
            fee_policy=dict(estimate_includes_all_fees=True,review_hash='0x'+'f'*64,max_gas_price_wei=str(10**11)))
        self.request = dict(action='increase' if increase else 'activate',wallet=addr(30),
            token_id=str(self.inner.nft_id),pool_id=self.pool,source_asset=asset,
            amount_in=str(self.amount),slippage_bps=100)
        self.p = Projection(self.config,self,clock=lambda:4000)
        self.service = ActivationTransactions(self.p,self.activation_config)

    def put(self,target,signature,args=(),values=(0,)):
        self.responses[target,data(signature,*args)] = words(*values)

    def call(self,method,params=None):
        params=[] if params is None else params
        if any(x in method.lower() for x in ('send','sign','anvil')):
            raise AssertionError('Synthetic V10 producer cannot sign, submit or mutate chain state')
        if method in ('eth_call','eth_estimateGas','eth_getBalance','eth_getCode','debug_traceCall'):
            if params[1]!={'blockHash':self.inner.hash,'requireCanonical':True}:
                raise AssertionError('Every monetary read/simulation must use the exact canonical hash')
        if method=='debug_traceCall':
            self.trace_count += 1
            return self.trace(params[0])
        if method=='eth_call':
            tx=params[0]
            if 'from' in tx:
                if tx['to']==self.c['entry']:
                    self.trace(tx)  # Strict synthetic request validation only.
                    return '0x'
                if tx['to']!=addr(20) or tx['data']!=data('approve(address,uint256)',self.c['entry'],self.amount):
                    raise AssertionError('Only an exact contribution approval is simulated')
                return words(1)
            if (tx['to'],tx['data']) in self.responses:
                return self.responses[tx['to'],tx['data']]
            if tx['to']==addr(20):
                if tx['data']==data('balanceOf(address)',addr(30)):return words(1000*USD)
                if tx['data']==data('allowance(address,address)',addr(30),self.c['entry']):
                    return words(0 if self.approval else self.amount)
        if method=='eth_estimateGas':return hex(500000)
        if method=='eth_gasPrice':return hex(10**9)
        if method=='eth_getBalance':return hex(1000*USD)
        return self.inner.call(method,params)

    def trace(self,tx):
        """Construct exact reviewed phases using controlled, auditable arithmetic."""
        q=[int(w,16) for w in T.decode_words('0x'+tx['data'][10:])]
        identifier,pool,source,amount,minimum,deadline,increase,maximum,policy=q
        if (len(q)!=9 or tx['data'][:10]!=T.selector(T.EXECUTE_DIRECT_V3) or
                tx['from']!=addr(30) or tx['to']!=self.c['entry'] or
                identifier!=self.inner.nft_id or pool!=int(self.pool,16) or source!=int(self.source,16) or
                int(tx['value'],16)!=(self.amount if self.source==ZERO else 0) or
                maximum!=self.loss or amount!=self.amount or bool(increase)!=self.increase):
            raise AssertionError('Unexpected current7 direct review tuple')
        c=self.c;bucket=self.bucket;gross=self.amount;supply=1000*USD;old=1000*USD
        marginal=gross*99//100;net=marginal;issued=supply*net//old
        a0,a1=(amount,0) if self.source==ZERO else (0,amount)
        b0,b1=marginal//2,marginal-marginal//2
        limits=200 | self.loss<<16
        economic=(gross,supply,old,old,old+marginal,0,limits)
        def frame(caller,target,sig,args=(),out='0x',kind='CALL',value=0,calls=None,logs=None):
            return dict(type=kind,**{'from':caller,'to':target},input=data(sig,*args),output=out,
                value=hex(value),calls=[] if calls is None else calls,logs=[] if logs is None else logs)
        def nav(deployed,idle):
            nested=frame(c['budget'],c['contribution_pricing'],T.NAV_PRICING,(bucket,),words(deployed,idle))
            return frame(c['vault'],c['budget'],T.NAV_PRICING,(bucket,),nested['output'],calls=[nested])
        def compound():
            nested=frame(c['budget'],c['contribution_pricing'],'valueBucket(uint256,uint256,uint256)',(bucket,0,0),words(0),'STATICCALL')
            return frame(c['vault'],c['budget'],'valueBucket(uint256,uint256,uint256)',(bucket,0,0),words(0),'STATICCALL',calls=[nested])
        def context():
            nested=frame(c['budget'],c['liquidity'],'balanceContext(bytes32)',(self.pool,),words(123),'STATICCALL')
            return frame(c['vault'],c['budget'],'balanceContext(uint256)',(bucket,),words(123),'STATICCALL',calls=[nested])
        packed=a0|(a1<<128)
        validation=frame(c['vault'],c['budget'],T.VALIDATE_PRICING,(identifier,bucket,gross,packed,minimum,int(not increase)),
            words(ZERO,addr(20),limits),calls=[frame(c['budget'],c['contribution_pricing'],T.BEGIN_PRICING,
                (identifier,bucket,packed,gross,limits))])
        balanced=frame(c['vault'],c['liquidity'],T.BALANCE,(self.pool,self.main,a0,a1,deadline),words(b0,b1),value=a0)
        pos_reads=[frame(c['lp_position_executor'],c['position_manager'],'getPositionLiquidity(uint256)',
            (self.main,),words(n),'STATICCALL') for n in (500,1500)]
        execution=frame(c['liquidity'],c['lp_position_executor'],T.INCREASE,
            (self.pool,self.main,b0,b1,minimum,deadline),words(b0,b1),value=b0,calls=pos_reads)
        mint=frame(c['vault'],c['liquidity'],T.INCREASE,(self.pool,self.main,b0,b1,minimum,deadline),
            execution['output'],value=b0,calls=[execution])
        finish=frame(c['budget'],c['contribution_pricing'],T.FINISH_PRICING,(bucket,*economic),words(issued,net))
        finish['calls']=[frame(c['contribution_pricing'],c['budget'],'compositionEpoch(uint256)',(bucket,),words(0),'STATICCALL') for _ in range(2)]
        finish['logs']=[dict(address=c['contribution_pricing'],topics=[T.VERIFIED,words(identifier),words(bucket)],
            data=words(gross,gross,marginal,net,2**96,'0x'+'8'*64))]
        check=frame(c['vault'],c['budget'],T.CONFIGURABLE_RESULT,(bucket,*economic),words(issued,net),calls=[finish])
        signature='increase(uint256,uint256,uint256,uint128,uint256)' if increase else 'activate(uint256,bytes32,uint256,uint256,uint128,uint256)'
        args=(identifier,a0,a1,minimum,deadline) if increase else (identifier,self.pool,a0,a1,minimum,deadline)
        vault=frame(c['entry'],c['vault'],signature,args,value=a0,calls=[validation,nav(old,0),compound(),context(),balanced,
            context(),nav(old,0),mint,compound(),nav(old+marginal,0),check],
            logs=[dict(address=c['vault'],topics=[T.SHARES,words(identifier),words(bucket)],data=words(issued,net))])
        begin=frame(c['entry'],c['contribution_pricing'],T.BEGIN_ENTRY_REVIEWED_V2,
            (identifier,self.pool,self.source,amount,maximum,'0x'+f'{policy:064x}'),words(gross))
        begin['calls']=[frame(c['contribution_pricing'],c['oracle'],'priceBounds(address)',(token,),
            words(*(value[k] for k in ('lower','upper','fingerprint'))),'STATICCALL') for token,value in self.price_bounds.items()]
        return dict(type='CALL',**{'from':tx['from'],'to':tx['to']},input=tx['data'],output='0x',value=tx['value'],
            gasUsed=hex(500000),calls=[begin,vault,frame(c['entry'],c['contribution_pricing'],'endEntry()')],
            logs=[dict(address=c['entry'],topics=[T.SOURCE,words(tx['from']),words(identifier),self.pool],
                data=words(self.source,amount,gross,self.source,amount,increase))])
