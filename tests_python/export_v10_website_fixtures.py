"""Export actual V10 backend handlers using explicitly synthetic offline RPC.

This creates consumer compatibility evidence, not EVM execution, qualified
markets/prices, OpenSea onboarding, signing, deployment or operating acceptance.
The source9 exporter and original actual-EVM artifacts remain untouched.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from frontend_api.service import Projection, ZERO
from frontend_api.transactions import Transactions, CLAIM_SIGNATURE, TransactionInputError
from frontend_api.earnings_checkpoint_build import publish_candidate
from tests_python.test_earnings_checkpoint_v2 import Checkpoint2APITests
from tests_python.test_frontend_api import addr, words
from tests_python.test_frontend_transactions import transaction_config
from tests_python.test_native_backend_boundary import native_data
from tests_python.v10_website_fixture import Current7Activation, bind_mint2, data, V10
from zzz_ops.abi import calldata, decode_words, keccak256

PROFILE=dict(website_schema=5,source_profile=10,mint_integration_version=2,
    accounting_version=7,lp_allocation_version=1,custody_version=5,
    protocol_policy_version=1,governance_version=2,fee_intake_version=1,
    portfolio_version=2,maintenance_policy_version=3,rebalance_confirmation_version=3,
    idle_compounding_version=4,lp_routing_version=2,execution_quality_version=1,
    emergency_version=2,pricing_version=2,routing_version=3,review_policy_version=2,
    royalty_settlement_version=4,royalty_reporting_schema=5,
    canonical_domain='ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10')
SCOPE=('Actual current Python API DTO/preparation/claim/history handlers with new '
    'explicitly synthetic RPC, prices, traces, fee estimates and authority identities. '
    'Not EVM execution, real market/provider/VRF/OpenSea/wallet qualification, signing, '
    'deployment, service rollout or a running configuration.')


class RecordedRPC:
    def __init__(self,inner):self.inner=inner;self.rows=[]
    def __getattr__(self,name):return getattr(self.inner,name)
    def call(self,method,params=None):
        params=[] if params is None else params
        if any(x in method.lower() for x in ('send','sign','anvil')):
            raise AssertionError('Read/unsigned-only exporter')
        value=self.inner.call(method,params)
        self.rows.append(dict(method=method,params=copy.deepcopy(params),result=copy.deepcopy(value)))
        return value


def source_hashes():
    """Pin static imports and actually loaded local dynamic-import modules."""
    # This established fixture loader executes its CLI module without adding it
    # to sys.modules. Pin that explicit dynamic dependency as well.
    pending=[Path(__file__).resolve(),ROOT/'tests_python/test_v10_website_fixtures.py',
        ROOT/'scripts/observe-production-config.py']
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            target=Path(filename).resolve()
            if target.is_relative_to(ROOT) and target.suffix=='.py' and target.is_file():
                pending.append(target)
    selected=set()
    while pending:
        path=pending.pop()
        if path in selected or not path.is_file():continue
        selected.add(path)
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        for item in ast.walk(tree):
            names=[]
            if isinstance(item,ast.Import):names=[n.name for n in item.names]
            elif isinstance(item,ast.ImportFrom):
                module=item.module or ''
                if item.level:
                    parent=path.parent
                    for _ in range(item.level-1):parent=parent.parent
                    module='.'.join((*parent.relative_to(ROOT).parts,module))
                names=[module]+[module+'.'+n.name for n in item.names]
            for name in names:
                target=ROOT.joinpath(*name.split('.')).with_suffix('.py')
                if target.is_file():pending.append(target)
                package=ROOT.joinpath(*name.split('.'),'__init__.py')
                if package.is_file():pending.append(package)
    return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(selected)}


def browser_proof(contracts,codes,block):
    """Extra synthetic immutable proofs; never insert browser-only config keys."""
    c=dict(contracts);c.update(nft_canonical=addr(22000),metadata_renderer=addr(22001))
    extra_codes={}
    for role in ('nft_canonical','metadata_renderer'):
        code='0x600a'+f'{int(c[role],16):04x}'
        extra_codes[c[role]]=code
    replies=[]
    for role,signature,args,value in (
            ('nft','metadataRenderer()',(),c['metadata_renderer']),
            ('metadata_renderer','access()',(),c['access']),
            ('nft','canonicalModule()',(),c['nft_canonical']),
            ('nft_canonical','nft()',(),c['nft']),('nft_canonical','access()',(),c['access']),
            ('access','module(bytes32)',('0x'+keccak256(b'ZZZNFTCanonical').hex(),),c['nft_canonical']),
            ('handoff','moduleAt(uint8)',(0,),c['nft_canonical'])):
        replies.append(dict(method='eth_call',params=[dict(to=c[role],data=data(signature,*args)),copy.deepcopy(block)],result=words(value)))
    for target,code in extra_codes.items():
        replies.append(dict(method='eth_getCode',params=[target,copy.deepcopy(block)],result=code))
    return dict(scope='Browser-only synthetic identity replies, separate from strict backend read configuration.',
        pins={r:c[r] for r in ('nft_canonical','metadata_renderer')},codes=extra_codes,rpc_responses=replies)


def envelope(f,recorder,outputs,api_calls,**extra):
    c={role:item['address'] for role,item in f.config['contracts'].items()}
    c.update(getattr(f,'c',{}))
    codes=getattr(f,'codes',getattr(f,'inner',None).codes)
    return dict(read_configuration=f.config,profile=PROFILE,pins=c,codes=codes,
        projection_identity=outputs.get('protocol',{}).get('provenance',{}).get('configuration_sha256'),
        outputs=outputs,api_calls=api_calls,rpc_responses=recorder.rows,
        browser_proof=browser_proof(c,codes,{'blockHash':f.inner.hash,'requireCanonical':True}),**extra)


def get_call(path,key,handler):return dict(method='GET',path=path,handler=handler,response_key=key)


def detail_case(name):
    owner=unittest.TestCase()
    try:
        f=Current7Activation(owner,increase=name!='dormant',residual=name in ('active_residual','price_unavailable'))
        identifier=f.inner.nft_id
        if name=='price_unavailable':
            f.f.old.f.base.outage()
            f.put(f.c['nft'],'currentLPValue(uint256)',(identifier,),(0,0))
        if name=='dormant':
            for role,method,value in (('vault','nftBucket(uint256)',0),('vault','sharesOf(uint256)',0),
                    ('royalties','weightOf(uint256)',0),('royalties','activationOrdinal(uint256)',0),('royalties','ticketStart(uint256)',0)):
                f.put(f.c[role],method,(identifier,),(value,))
            for role,assets in (('rewards',(ZERO,addr(20))),('royalties',(ZERO,addr(21)))):
                for asset in assets:
                    f.put(f.c[role],'claimable(uint256,address)',(identifier,asset),(0,))
                    if role=='royalties':f.put(f.c[role],'eligibleFor(uint256,address)',(identifier,asset),(0,))
        if name.startswith('principal_'):
            paid=name=='principal_paid';phase=2 if name=='principal_allocated' else 3
            f.put(f.c['access'],'lpExitStarted()',values=(1,))
            f.put(f.c['principal_exit'],'exitPhase()',values=(phase,))
            f.put(f.c['vault'],'nftStatus(uint256)',(identifier,),(5,))
            f.q.position[1]=f.q.position[2]=f.q.position[3]=0;f.q.position[7]=5
            f.put(f.c['nft'],'currentLPValue(uint256)',(identifier,),(1,0))
            f.put(f.c['principal_exit'],'principalOf(uint256)',(identifier,),(123,456,1,int(paid)))
            f.put(f.c['principal_exit'],'claimablePrincipal(uint256)',(identifier,),(0,0) if paid else (123,456))
        recorder=RecordedRPC(f);p=Projection(f.config,recorder,clock=lambda:4000)
        outputs=dict(protocol=p.protocol(),nft=p.nft(str(identifier)))
        result=envelope(f,recorder,outputs,[get_call('/v1/protocol','protocol','Projection.protocol'),
            get_call('/v1/nfts/'+str(identifier),'nft','Projection.nft')])
        result['projection_identity']=p.identity
        return result
    finally:owner.doCleanups()


class ClaimRPC:
    def __init__(self,f):self.f=f
    def __getattr__(self,name):return getattr(self.f,name)
    def call(self,method,params=None):
        params=[] if params is None else params;f=self.f
        block={'blockHash':f.inner.hash,'requireCanonical':True}
        if method=='eth_getBlockByHash':
            if params!=[f.inner.hash,False]:raise AssertionError('Noncanonical fee-policy header')
            return dict(number=hex(f.inner.head-f.p.confirmations+1),hash=f.inner.hash,timestamp=hex(4000),gasLimit=hex(40_000_000))
        if method=='eth_getBlockByNumber':
            header=f.call(method,params)
            return {**header,'gasLimit':hex(40_000_000)}
        if method=='eth_call' and 'from' in params[0]:
            tx=params[0]
            if params[1]!=block or tx['to']!=f.c['claim_router'] or tx['data'][:10]!=T_SELECTOR_CLAIM:
                raise AssertionError('Only exact canonical claim simulation is allowed')
            raw=decode_words('0x'+tx['data'][10:]);count=int(raw[1],16)
            if int(raw[0],16)!=32 or not 1<=count<=32 or len(raw)!=2+3*count:raise AssertionError('Invalid claim ABI')
            result=[]
            for offset in range(2,len(raw),3):
                identifier,asset_word,royalty=map(lambda w:int(w,16),raw[offset:offset+3])
                if royalty not in (0,1):raise AssertionError('Invalid royalty flag')
                if int(f.call('eth_call',[dict(to=f.c['nft'],data=data('ownerOf(uint256)',identifier)),block]),16)!=int(tx['from'],16):
                    raise AssertionError('Claim owner differs')
                role='royalties' if royalty else 'rewards';asset=addr(asset_word)
                result.append(int(f.call('eth_call',[dict(to=f.c[role],data=data('claimable(uint256,address)',identifier,asset)),block]),16))
            return words(32,count,*result)
        return f.call(method,params)


T_SELECTOR_CLAIM='0x'+keccak256(CLAIM_SIGNATURE.encode()).hex()[:8]


def claim_case(policy):
    owner=unittest.TestCase()
    try:
        f=Current7Activation(owner,increase=True);recorder=RecordedRPC(ClaimRPC(f))
        p=Projection(f.config,recorder,clock=lambda:4000);cfg=transaction_config(p)
        if policy==2:cfg.update(schema=2);cfg['fee_policy']['max_gas_limit']='40000000'
        service=Transactions(p,cfg)
        request=dict(action='claim',wallet=addr(30),claims=[
            dict(token_id=str(f.inner.nft_id),asset=ZERO,royalty=False),
            dict(token_id=str(f.inner.nft_id),asset=ZERO,royalty=True),
            dict(token_id=str(f.inner.nft_id),asset=addr(21),royalty=True)])
        outputs=dict(protocol=p.protocol(),nft=p.nft(str(f.inner.nft_id)),draft=service.prepare(request),plan=service.plan_claims(request))
        result=envelope(f,recorder,outputs,[dict(method='POST',path='/v1/transactions/prepare',handler='Transactions.prepare',request=request,response_key='draft'),
            dict(method='POST',path='/v1/claims/plan',handler='Transactions.plan_claims',request=request,response_key='plan')],
            transaction_configuration=cfg,request=request)
        result['projection_identity']=p.identity
        return result
    finally:owner.doCleanups()


def activation_case(*,increase,asset,approval=False,residual=False):
    owner=unittest.TestCase()
    try:
        f=Current7Activation(owner,increase=increase,asset=asset,approval=approval,residual=residual)
        recorder=RecordedRPC(f);p=Projection(f.config,recorder,clock=lambda:4000)
        from frontend_api.activation import ActivationTransactions
        result=ActivationTransactions(p,f.activation_config).prepare(f.request)
        protocol=p.protocol();nft=p.nft(str(f.inner.nft_id))
        transaction={k:v for k,v in result['transaction'].items() if k!='chainId'}
        simulation=recorder.call('eth_call',[{**transaction,'gas':hex(12_000_000)},
            {'blockHash':f.inner.hash,'requireCanonical':True}])
        item=envelope(f,recorder,dict(draft=result,protocol=protocol,nft=nft,independent_simulation=simulation),[
            dict(method='POST',path='/v1/activation/prepare',handler='ActivationTransactions.prepare',request=f.request,response_key='draft'),
            get_call('/v1/protocol','protocol','Projection.protocol'),
            get_call('/v1/nfts/'+str(f.inner.nft_id),'nft','Projection.nft')],
            activation_configuration=f.activation_config,request=f.request,
            trace_scope='New synthetic current7 two-phase trace; no historical EVM witness is retagged.',
            expected_unchanged_geometry=dict(main_lp_token_id=str(f.main),lower_tick=f.q.lower,upper_tick=f.q.upper,
                last_rebalance_at=f.q.position[6],residual_lp_token_id=str(f.q.secondary) if f.q.secondary else None))
        item['projection_identity']=p.identity
        return item
    finally:owner.doCleanups()


def mint_case():
    owner=unittest.TestCase()
    try:
        f=Current7Activation(owner,increase=True);recorder=RecordedRPC(f)
        p=Projection(f.config,recorder,clock=lambda:4000);cfg=transaction_config(p)
        request=dict(action='mint',wallet=addr(30));before=len(recorder.rows)
        try:Transactions(p,cfg).prepare(request)
        except TransactionInputError as exc:failure=dict(type=type(exc).__name__,message=str(exc))
        else:raise AssertionError('V10 direct mint unexpectedly prepared')
        if len(recorder.rows)!=before:raise AssertionError('Use OpenSea must precede RPC and simulation')
        item=envelope(f,recorder,dict(error=failure),[dict(method='POST',path='/v1/transactions/prepare',
            handler='Transactions.prepare',request=request,error_key='error')],transaction_configuration=cfg,request=request)
        item['projection_identity']=p.identity
        return item
    finally:owner.doCleanups()


def earnings_case():
    f=Checkpoint2APITests('runTest')
    try:
        f.setUp()
        c={role:item['address'] for role,item in f.config['contracts'].items()};c.update(f.c)
        bind_mint2(f.inner,f.config,c,f.put)
        f.c=c
        recorder=RecordedRPC(f.rpc);f.rpc=recorder
        candidate=f.candidate();f.install(candidate);f.suffix()
        q=f.inner.responses.physical
        q.overrides[c['vault'],'poolBucket(bytes32)']=[f'{5:064x}']
        for role,method in (('vault','group(uint256)'),('strategy','rangeUpdatePending(uint256)'),('portfolio_policy','configurationPending(uint256)')):
            f.inner.responses.selected[c[role],calldata(method,5)]=(c[role],method,(5,))
        model=f.model()
        for identifier in f.ids:
            weight=model.weights.get(identifier,0)
            for role,method,value in (('nft','traitsReady(uint256)',1),('nft','rarityOf(uint256)',weight-1 if weight else 0),
                    ('nft','paletteOf(uint256)',24),('nft','patternOf(uint256)',2),
                    ('royalties','activationOrdinal(uint256)',model.activation_order.index(identifier)+1 if weight else 0),
                    ('vault','nftStatus(uint256)',1 if weight else 3),('vault','contributionUSD(uint256)',100*10**18 if weight else 0)):
                f.put(c[role],method,(identifier,),(value,))
            f.put(c['nft'],'currentLPValue(uint256)',(identifier,),(1,1432*10**18 if weight else 0))
            f.put(c['principal_exit'],'principalOf(uint256)',(identifier,),(0,0,0,0))
            for asset in f.royalties:f.put(c['royalties'],'eligibleFor(uint256,address)',(identifier,asset),(int(bool(weight)),))
        for asset in f.royalties:f.put(c['royalties'],'effectiveEligibleCount(address)',(asset,),(len(model.cohorts[asset]),))
        f.put(c['royalties'],'mintEndRevision()',values=(1,))
        p=f.projection();wallet=addr(32)
        outputs=dict(protocol=p.protocol(),nfts={str(i):p.nft(str(i)) for i in f.ids},inventory=p.wallet(wallet),
            earnings=p.earnings(),wallet_summary=p.wallet_summary(wallet,99),collection=p.collection(99),
            nft_earnings={str(i):p.earnings(str(i)) for i in f.ids},wallet_earnings=p.wallet_earnings(wallet,99),
            full_raw_earnings=f.projection(f.full_config()).earnings())
        for key in ('all_time','last_24h','window','event_count'):
            if outputs['earnings'][key]!=outputs['full_raw_earnings'][key]:raise AssertionError('New V10 checkpoint and raw replay differ')
        calls=[get_call('/v1/protocol','protocol','Projection.protocol'),get_call('/v1/wallets/'+wallet+'/nfts','inventory','Projection.wallet'),
            get_call('/v1/earnings','earnings','Projection.earnings'),get_call('/v1/wallets/'+wallet+'/summary/99/0','wallet_summary','Projection.wallet_summary'),
            get_call('/v1/collection/99/0','collection','Projection.collection'),get_call('/v1/wallets/'+wallet+'/earnings/99/0','wallet_earnings','Projection.wallet_earnings')]
        for identifier in f.ids:
            calls.extend([get_call('/v1/nfts/'+str(identifier),'nfts.'+str(identifier),'Projection.nft'),
                get_call('/v1/nfts/'+str(identifier)+'/earnings','nft_earnings.'+str(identifier),'Projection.earnings')])
        return dict(read_configuration=f.config,profile=PROFILE,pins=c,codes=f.inner.codes,projection_identity=p.identity,
            outputs=outputs,api_calls=calls,rpc_responses=recorder.rows,raw_logs=f.rows,
            checkpoint_candidate=json.loads(candidate),checkpoint_sha256=hashlib.sha256(candidate).hexdigest(),
            browser_proof=browser_proof(c,f.inner.codes,{'blockHash':f.inner.hash,'requireCanonical':True}),
            note='New V10-identity-bound checkpoint2 built by actual SQLite/history/replay handlers. All events/identities/prices are synthetic. No USD price config: unavailable remains unavailable. Temporary paths are inert evidence, not operating configuration.')
    finally:f.doCleanups()


def produce():
    cases={name:detail_case(name) for name in ('active_single','active_residual','price_unavailable','dormant',
        'principal_allocated','principal_ready','principal_paid')}
    for policy in (1,2):cases['claim_policy'+str(policy)]=claim_case(policy)
    cases['checkpoint2_earnings']=earnings_case()
    for increase in (False,True):
        for asset,symbol in ((ZERO,'eth'),(addr(20),'zzz')):
            name=('growth_' if increase else 'activation_')+symbol
            cases[name]=activation_case(increase=increase,asset=asset,residual=increase)
            if symbol=='zzz':cases[name+'_approval']=activation_case(increase=increase,asset=asset,approval=True,residual=increase)
    cases['mint_use_opensea']=mint_case()
    return dict(schema=1,kind='v10_website_synthetic_api_fixtures',scope=SCOPE,profile=PROFILE,
        source_sha256=source_hashes(),data_sha256={'indexer/event_schema.json':hashlib.sha256((ROOT/'indexer/event_schema.json').read_bytes()).hexdigest()},
        contract_source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT/'src').rglob('*.sol'))},cases=cases,
        unsupported=['No actual V10 deployment, market depth, independent price sources, VRF or marketplace is qualified.',
            'No signer, wallet submission, chain transaction, installed consumer or public site is exercised.',
            'The raw synthetic trace tests decoder/handler compatibility, not actual EVM contract execution.'])


def publish(target,result):
    target=Path(target).resolve()
    if target.suffix!='.json':raise ValueError('Fixture output must be JSON')
    raw=(json.dumps(result,indent=2,allow_nan=False)+'\n').encode()
    target.parent.mkdir(parents=True,exist_ok=True)
    return publish_candidate(target,raw)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    target=parser.parse_args().output;result=produce();digest=publish(target,result)
    print(json.dumps(dict(path=str(target.resolve()),cases=list(result['cases']),sha256=digest)))


if __name__=='__main__':main()
