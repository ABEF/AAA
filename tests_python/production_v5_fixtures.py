"""Synthetic fresh capability graph and physical portfolio; never release evidence."""
import copy
from zzz_ops import production_v5 as P
from zzz_ops import production_observer as O
from tests_python import production_v4_fixtures as F

NOW,COMMIT,RUNTIME=F.NOW,F.COMMIT,F.RUNTIME


def refresh_bindings(cfg):
    chain=cfg['chains'][0]
    if isinstance(chain.get('portfolio',{}).get('observed'),dict):
        for row in chain['portfolio']['observed']['pools']:
            row['control_fingerprint']=P.portfolio_control_fingerprint(chain,row)
    for group,records in P.expected_bindings(chain).items():
        for role,values in records.items():
            chain[group][role]['observed_bindings']=copy.deepcopy(values)
            if group=='helpers':chain[group][role]['bindings']=copy.deepcopy(values)


def fixture(*,active=False,residual=False):
    cfg=F.active(F.fixture()) if active else F.fixture()
    cfg.update(P.VERSIONS,canonical_schema=P.SCHEMA_NAME,
        accounting_model='shared-pools-native-v5',custody_architecture='collective-holder-return-v4')
    chain=cfg['chains'][0];pid=chain['pools'][0]['pool_id']
    for i,role in enumerate(('portfolio_policy','lp_balance_math','lp_position_executor')):
        chain['helpers'][role]=dict(address=F.old.addr(10023+i),runtime_hash=F.old.HASH,
            observed_runtime_hash=F.old.HASH,immutable=True,review_evidence=F.old.proof())
    chain['native_accounting']['version']=5
    cfg['evidence']['portfolio']=F.old.proof()
    chain['portfolio']=dict(threshold_bps=8500,policy_revision=1,trigger_review_hash=P.ZERO_HASH,
        source_check_interval_seconds=240,pools=[dict(pool_id=pid,enabled=residual,geometry_revision=int(residual),
            residual_side_bps=5000,mode_review_hash=F.old.HASH if residual else P.ZERO_HASH,residual_review_hash=P.ZERO_HASH)],
        review_evidence=F.old.proof(chain_id=4663,block_number=100,block_hash=F.old.HASH,
            deployment=chain['modules']['access']['address'],kind='bounded_portfolio_qualification'))
    chain['portfolio']['observed']=dict(version=1,threshold_bps=8500,policy_revision=1,trigger_review_hash=P.ZERO_HASH,
        minimum_main_bps=6000,maximum_residual_bps=4000,default_residual_side_bps=5000,
        active_secondary_count=int(residual and active),pools=[dict(chain['portfolio']['pools'][0],control_fingerprint=F.old.HASH)],buckets=[])
    for bucket in chain['holder_exit']['observed']['buckets']:
        group=bucket['position'];legs=[]
        if group[7]==1:
            pool=chain['pools'][0];price=O._uint(pool['slot0']['sqrt_price_x96'])
            main=dict(id=group[1],owner=bucket['lp_owner'],liquidity=bucket['lp_liquidity'],ticks=bucket['lp_ticks'],
                pool_key=bucket['lp_pool_key'],position_info=bucket['lp_position_info'])
            main['amounts']=P.physical_amounts(price,main['ticks'],main['liquidity']);legs.append(main)
            if residual:
                ticks=[-3000,0];physical=F.physical_position(pool,ticks)
                leg=dict(id=100,owner=bucket['lp_owner'],liquidity=50000,ticks=ticks,
                    pool_key=physical['lp_pool_key'],position_info=physical['lp_position_info'])
                leg['amounts']=P.physical_amounts(price,ticks,leg['liquidity']);legs.append(leg)
            stable,execution=P.portfolio_fingerprints(chain,pid,legs)
            bucket['portfolio']=dict(version=1,secondary_id=100 if residual else 0,fingerprint=stable,
                execution_fingerprint=execution,amounts=[sum(l['amounts'][n] for l in legs) for n in range(2)],legs=legs)
        else:bucket['portfolio']=None
        chain['portfolio']['observed']['buckets'].append(dict(id=bucket['id'],main_id=group[1],
            secondary_id=100 if residual and group[7]==1 else 0,applied_revision=int(residual) if group[7]==1 else None,
            configuration_pending=False))
    c=chain['rebalance_confirmation'];c['duration']=600;c['observed']['duration']=600
    for row,bucket in zip(c['observed']['buckets'],chain['holder_exit']['observed']['buckets']):
        group=bucket['position'];price=O._uint(chain['pools'][0]['slot0']['sqrt_price_x96'])
        side=P.threshold_side(group[5],bucket['lp_ticks'],price,8500)
        row.update(condition_side=side,condition_identity=F.old.HASH if side else P.ZERO_HASH,
            manual=False,stored_identity=F.old.HASH,first_seen=NOW-600,last_seen=NOW-1,stored_side=side or 2,
            ready=bool(side),raw_needed=bool(side),range_pending=False,physical_side=side,reference_side=side,reference_x96=price)
    chain['lp_execution']['observed']=P.execution_expected(chain)
    for role,profile in P.SERVICE_PROFILES.items():
        chain['services'][role]['profile']=profile;chain['services'][role]['evidence']['profile']=profile
    refresh_bindings(cfg)
    return cfg


class RPC(F.RPC):
    def __init__(self,cfg):
        super().__init__(cfg);self.expected=P.expected_bindings(self.chain)

    def call(self,method,params=None):
        c=self.chain;m=c['modules'];h=c['helpers'];p=c['portfolio']['observed']
        if method=='eth_call':
            target,data=params[0]['to'],params[0]['data']
            if (target,data) in self.overrides:return super().call(method,params)
            result=None
            def matches(signature,*args):return data==F.selector(signature)+''.join(O._word(a) for a in args)
            if target==h['portfolio_policy']['address']:
                globals={'PORTFOLIO_VERSION()':p['version'],'thresholdBps()':p['threshold_bps'],'revision()':p['policy_revision'],
                    'triggerReviewHash()':p['trigger_review_hash'],'minimumMainBps()':6000,'maximumResidualBps()':4000,'DEFAULT_RESIDUAL_SIDE_BPS()':5000}
                for sig,value in globals.items():
                    if matches(sig):result=F.encoded(value)
                for pool in p['pools']:
                    for getter,key in (('enabled','enabled'),('geometryRevision','geometry_revision'),('residualSideBps','residual_side_bps'),
                            ('modeReviewHash','mode_review_hash'),('residualReviewHash','residual_review_hash'),('controlFingerprint','control_fingerprint')):
                        if matches(getter+'(bytes32)',pool['pool_id']):result=F.encoded(int(pool[key]) if type(pool[key]) is bool else pool[key])
                for row in p['buckets']:
                    if matches('appliedRevision(uint256)',row['main_id']):result=F.encoded(row['applied_revision'])
                    if matches('configurationPending(uint256)',row['id']):result=F.encoded(int(row['configuration_pending']))
            if target==m['liquidity']['address']:
                if matches('activeSecondaryCount()'):result=F.encoded(p['active_secondary_count'])
                for bucket in c['holder_exit']['observed']['buckets']:
                    portfolio=bucket['portfolio'];main=bucket['position'][1]
                    if portfolio:
                        for getter,key in (('secondaryId','secondary_id'),('portfolioFingerprint','fingerprint'),('executionPortfolioFingerprint','execution_fingerprint')):
                            if matches(getter+'(uint256)',main):result=F.encoded(portfolio[key])
                        if matches('portfolioAmounts(uint256)',main):result=F.encoded(*portfolio['amounts'])
                        for leg in portfolio['legs']:
                            if matches('amounts(uint256)',leg['id']):result=F.encoded(*leg['amounts'])
                            if matches('ticks(uint256)',leg['id']):result=F.encoded(*(t%2**256 for t in leg['ticks']))
            if target==c['dependencies']['position_manager']['address']:
                for bucket in c['holder_exit']['observed']['buckets']:
                    for leg in (bucket['portfolio'] or {}).get('legs',[]):
                        if matches('ownerOf(uint256)',leg['id']):result=F.encoded(leg['owner'])
                        if matches('getPositionLiquidity(uint256)',leg['id']):result=F.encoded(leg['liquidity'])
                        if matches('getPoolAndPositionInfo(uint256)',leg['id']):result='0x'+''.join(leg['pool_key'])+leg['position_info']
            if target==m['oracle']['address']:
                for row in c['rebalance_confirmation']['observed']['buckets']:
                    if row['reference_x96'] is not None:
                        pool=c['pools'][0]
                        if matches('referenceX96(address,address)',pool['currency0'],pool['currency1']):result=F.encoded(row['reference_x96'])
            if result is not None:self.calls.append((method,params));return result
        return super().call(method,params)
