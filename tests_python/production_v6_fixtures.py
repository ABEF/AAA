"""Synthetic Policy1/schema8 fixture; no deployed state or release evidence."""
import copy
from tests_python import production_v5_fixtures as H
from zzz_ops import production_v6 as P
from zzz_ops import production_observer as O
from zzz_ops.protocol_policy import DOMAINS,VRF_FIELDS
from zzz_ops.abi import keccak256

NOW,COMMIT,RUNTIME=H.NOW,H.COMMIT,H.RUNTIME

def refresh_bindings(cfg):
    chain=cfg['chains'][0]
    for row in chain['portfolio']['observed']['pools']:
        row['control_fingerprint']=P.portfolio_control_fingerprint(chain,row)
    for group,records in P.expected_bindings(chain).items():
        for role,values in records.items():
            chain[group][role]['observed_bindings']=copy.deepcopy(values)
            if group=='helpers':chain[group][role]['bindings']=copy.deepcopy(values)

def fixture(*,active=True,residual=True):
    cfg=H.fixture(active=active,residual=residual);cfg.update(P.VERSIONS,accounting_model='shared-pools-native-v6',canonical_schema=P.SCHEMA_NAME)
    chain=cfg['chains'][0];target=H.F.old.addr(10026)
    chain['helpers']['protocol_policy']=dict(address=target,runtime_hash=H.F.old.HASH,
        observed_runtime_hash=H.F.old.HASH,immutable=True,review_evidence=H.F.old.proof())
    data={'entry':(100*10**18,5*10**18,500,1),'maintenance':(500,1),'gas':(180000,500000,250000,1),
        'sale':(5*10**16,int(chain['constructor']['mint_proceeds_recipient'],16),0,1),
        'metadata':(1000*10**18,10000*10**18,1)}
    policy={}
    for domain,values in data.items():
        names=DOMAINS[domain][2]
        raw=f'{int(target,16):064x}'+''.join(f'{v:064x}' for v in values)
        row=dict(zip(names,values))
        if domain=='sale':
            row.update(recipient='0x'+f'{values[1]:040x}',pending_recipient=P.ZERO)
        policy[domain]=dict(version=1,domain=domain,policy=target,fingerprint='0x'+keccak256(bytes.fromhex(raw)).hex(),**row)
    vrf=chain['nft_inventory']['randomness']
    random=dict(coordinator=vrf['coordinator'],expected_code_hash=vrf['runtime_hash'],key_hash=vrf['keyHash'],
        subscription_id=int(vrf['subscriptionId']),request_confirmations=vrf['requestConfirmations'],
        callback_gas_limit=vrf['callbackGasLimit'],native_payment=vrf['nativePayment'],generation=0,configured=True,review_hash=H.F.old.HASH)
    random_raw=''.join(f'{int(random[n],16) if isinstance(random[n],str) and random[n].startswith("0x") else int(random[n]):064x}' for n in VRF_FIELDS)
    sale_raw=''.join(f'{v:064x}' for v in data['sale'])
    fingerprint='0x'+keccak256(bytes.fromhex(f'{int(target,16):064x}'+sale_raw+f'{1:064x}'+random_raw)).hex()
    policy['mint']=dict(version=1,policy=target,fingerprint=fingerprint,vrf_revision=1,
        sale_fingerprint=policy['sale']['fingerprint'],randomness=random)
    policy.update(configuration_hash=H.F.old.HASH,vrf_revision=1)
    policy['observed']=copy.deepcopy(policy)
    policy['review_evidence']=H.F.old.proof(chain_id=4663,block_number=100,block_hash=H.F.old.HASH,
        deployment=chain['modules']['access']['address'],kind='protocol_policy_qualification')
    chain['protocol_policy']=policy;cfg['evidence']['protocol_policy']=H.F.old.proof()
    chain['native_accounting']['version']=6
    chain['native_accounting']['canonical_schema']=P.SCHEMA_HASH
    chain['portfolio']['trigger_revision']=1;chain['portfolio']['observed']['trigger_revision']=1
    chain['portfolio']['observed']['version']=2
    for key in ('minimum_main_bps','maximum_residual_bps'):chain['portfolio']['observed'].pop(key)
    for rows in (chain['portfolio']['pools'],chain['portfolio']['observed']['pools']):
        for row in rows:row.update(control_revision=row['geometry_revision'],minimum_main_bps=6000,residual_gap_spacings=1)
    for bucket in chain['holder_exit']['observed']['buckets']:
        if bucket['portfolio']:bucket['portfolio']['version']=2
    chain['nft_inventory']['randomness'].pop('immutable_provider_configuration',None)
    chain['nft_inventory']['randomness']['provider_rotation_when_drained']=True
    cfg['nft_policy']['evolution_thresholds_usd18']=[0,0,1000*10**18,10000*10**18]
    chain['lp_execution']['observed']=P.execution_expected(chain)
    for role,profile in P.SERVICE_PROFILES.items():
        chain['services'][role]['profile']=profile;chain['services'][role]['evidence']['profile']=profile
    refresh_bindings(cfg)
    return cfg

class RPC(H.RPC):
    def __init__(self,cfg):
        super().__init__(cfg);self.expected=P.expected_bindings(self.chain)
    def call(self,method,params=None):
        if method=='eth_call':
            target,data=params[0]['to'],params[0]['data'];chain=self.chain
            if (target,data) in self.overrides:return super().call(method,params)
            def matches(signature,*args):return data==H.F.selector(signature)+''.join(O._word(a) for a in args)
            helper=chain['helpers']['protocol_policy']['address']
            if target==helper:
                policy=chain['protocol_policy']['observed']
                for domain,(getter,fingerprint,names,widths) in DOMAINS.items():
                    row=policy[domain]
                    if matches(getter):return H.F.encoded(*(row[name] for name in names))
                    if matches(fingerprint):return H.F.encoded(row['fingerprint'])
                if matches('configurationHash()'):return H.F.encoded(policy['configuration_hash'])
                if matches('vrfRevision()'):return H.F.encoded(policy['vrf_revision'])
                if matches('vrfPolicy()'):return H.F.encoded(*(int(policy['mint']['randomness'][n]) if type(policy['mint']['randomness'][n]) is bool else policy['mint']['randomness'][n] for n in VRF_FIELDS))
                if matches('mintFingerprint()'):return H.F.encoded(policy['mint']['fingerprint'])
            if target==chain['helpers']['portfolio_policy']['address']:
                if matches('triggerRevision()'):return H.F.encoded(chain['portfolio']['trigger_revision'])
                for row in chain['portfolio']['observed']['pools']:
                    for getter,key in (('controlRevision','control_revision'),('minimumMainBps','minimum_main_bps'),('residualGapSpacings','residual_gap_spacings')):
                        if matches(getter+'(bytes32)',row['pool_id']):return H.F.encoded(row[key])
                    if matches('maximumResidualBps(bytes32)',row['pool_id']):return H.F.encoded(10000-row['minimum_main_bps'])
        return super().call(method,params)
