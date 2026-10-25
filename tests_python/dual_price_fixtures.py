"""Synthetic dual-source inventory migration for current-profile test fixtures."""
import copy
from zzz_ops import price_policy as D


def upgrade_inventory(config, proof):
    config['review_policy_version'] = 1
    chain=config['chains'][0]
    for role,getter in (('activation_entry','REVIEW_POLICY_VERSION'),('contribution_pricing','ENTRY_REVIEW_VERSION')):
        for key in ('bindings','observed_bindings'):
            chain['helpers'][role].setdefault(key,{})[getter]=1
    if config.get('pricing_version') == 2:
        return config
    config['pricing_version'] = 2
    chain = config['chains'][0]; oracle = chain['modules']['oracle']['address']
    stamp = chain['observed_block']['timestamp']
    for ordinal, token in enumerate(chain['tokens']):
        feed = token.pop('feed'); sources=[]
        for index in range(2):
            source='0x'+f'{11000+ordinal*2+index:040x}'
            independence='0x'+f'{index+1:064x}'
            sources.append({'source':source,'runtime_hash':feed['runtime_hash'],
                'observed_runtime_hash':feed['observed_runtime_hash'],'denomination':'USD',
                'decimals':feed['decimals'],'round_id':feed['round_id'],'answer':feed['answer'],
                'started_at':feed['updated_at']-10,'updated_at':feed['updated_at'],
                'answered_in_round':feed['answered_in_round'],
                'review_evidence':proof(independent_price_source=True,depeg_and_manipulation_reviewed=True,
                    underlying_sources_reviewed=True,proxy_implementation_reviewed=True,
                    chain_id=chain['chain_id'],asset=token['address'],source=source,
                    runtime_hash=feed['runtime_hash'],independence_id=independence)})
        def source_policy(index):
            item=sources[index]
            return {'source':item['source'],'expectedCodeHash':item['runtime_hash'],
                'independenceId':item['review_evidence']['independence_id'],
                'maxAge':feed['maximum_age_seconds'],'feedDecimals':feed['decimals']}
        policy={'token':token['address'],'primary':source_policy(0),'secondary':source_policy(1),
            'maxDeviationBps':50,'assetDecimals':token['decimals'],'reviewHash':'0x'+'88'*32}
        token['price_policy']={'ordinal':ordinal,'policy':policy,'sources':sources,
            'observed_pricing_version':2,'observed_policy_count':len(chain['tokens'])}
        rebind_token(chain,token,proof)
    chain['services']['api']['profile']='accounting_v2_routing_v2_pricing_v2_review_v1'
    chain['services']['api']['evidence']['profile']='accounting_v2_routing_v2_pricing_v2_review_v1'
    chain['services']['pricing']['profile']='independent_dual_usd_v2'
    chain['services']['pricing']['evidence']['profile']='independent_dual_usd_v2'
    return config


def rebind_token(chain,token,proof):
    record=token['price_policy'];oracle=chain['modules']['oracle']['address']
    policy=record['policy'];policy['token']=token['address'];policy['assetDecimals']=token['decimals']
    identifier=D.policy_id(oracle,record['ordinal'],policy)
    record.update(policy_id=identifier,observed_policy_id=identifier,observed_ordinal_id=identifier,
        observed_policy=copy.deepcopy(policy))
    raw=[];prices=[]
    for role,item in zip(('primary','secondary'),record['sources']):
        item['review_evidence']['asset']=token['address']
        values=[item[key] for key in ('round_id','answer','started_at','updated_at','answered_in_round')]
        price,_=D.round_data(D.words(values),policy[role],chain['observed_block']['timestamp'])
        prices.append(price);raw.extend(values)
    record['observed_bounds']={'lower':min(prices),'upper':max(prices),'fingerprint':D.hash_words(
        [D.DOMAIN,chain['chain_id'],oracle,identifier,chain['sequencer'].get('active_policy_id',D.ZERO_HASH)]+raw)}
    record['review_evidence']=proof(kind='dual_source_pricing_review',chain_id=chain['chain_id'],
        asset=token['address'],oracle=oracle,policy_id=identifier,onchain_review_hash=policy['reviewHash'],
        sources_independent=True,common_mode_risk_reviewed=True,bounds_and_outage_reviewed=True)
