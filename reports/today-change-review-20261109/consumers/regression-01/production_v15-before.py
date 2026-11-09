"""Schema17: explicit SeaDrop mint2/helper1/V10 source; no release approval.

The prior schema16 gate remains historical and keeps its direct-mint blocker.
Mint manifests and observations cannot authenticate OpenSea onboarding, evidence,
market providers, operating acceptance or the reviewed Merkle leaf contents.
"""
from zzz_ops import production_v14 as H,production_v6 as BASE
from zzz_ops.opensea_drop import CONFIG_FIELDS,address_list_hash

V,ZERO_HASH=H.V,H.ZERO_HASH
MODULES,HELPERS=H.MODULES,H.HELPERS+('seadrop_mint',)
SCHEMA_NAME='ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_SEADROP_V10'
SCHEMA_HASH='0x'+V.keccak256(SCHEMA_NAME.encode()).hex()
VERSIONS=dict(H.VERSIONS,schema_version=17,mint_integration_version=2)
TOP_FIELDS=H.TOP_FIELDS
CHAIN_FIELDS=H.CHAIN_FIELDS|{'primary_mint'}
MAX_TOKEN_RECORDS=H.MAX_TOKEN_RECORDS
SERVICE_PROFILES=dict(H.SERVICE_PROFILES,
    api=H.SERVICE_PROFILES['api'].replace('holder_exit_v9','holder_exit_v10')+'_mint2',
    keeper=H.SERVICE_PROFILES['keeper']+'_canonical_v10_mint2',
    opensea='seadrop_sequential_v1')
ROYALTY_CREATION_CODE_HASH=H.ROYALTY_CREATION_CODE_HASH
raw_royalty_assets,precheck_chain,validate_tokens=H.raw_royalty_assets,H.precheck_chain,H.validate_tokens
PROFILE='seadrop_sequential_v1'
CONFIG_TYPES=('uint16','uint16','uint16','uint16','uint8','uint48','uint48','uint48','uint48','uint48','uint48',
    'bool','bytes32','address','bytes32')
FIELDS={'implementation_profile','mint_config','expected_mint_price_wei','configuration_hash',
    'configuration_values_hash','configuration_review_hash','revision','sea_drop','sea_drop_runtime_hash',
    'allowed_payers','observed','review_evidence','onboarding_evidence','fee_qualification_evidence',
    'operating_evidence','manifest_review_evidence'}


def expected_bindings(chain):
    result=H.expected_bindings(chain)
    primary=V._obj(chain.get('primary_mint'))
    helper=V._obj(V._obj(chain.get('helpers')).get('seadrop_mint')).get('address')
    result['modules']['canonical']['SCHEMA']=SCHEMA_HASH
    result['modules']['nft']['seaDropMint']=helper
    result['helpers']['seadrop_mint']=dict(access=chain['modules']['access']['address'],
        nft=chain['modules']['nft']['address'],seaDrop=primary.get('sea_drop'),
        seaDropCodeHash=primary.get('sea_drop_runtime_hash'),MINT_INTEGRATION_VERSION=1)
    return result


def _config(g,raw,path):
    c=g.obj(raw,path);g.keys(c,CONFIG_FIELDS,path)
    bounds={'teamAllocation':1000,'allowlistAllocation':1000,'publicWalletLimit':1000,'feeBps':10000,
        'maxBatch':10,**{key:2**48-1 for key in CONFIG_FIELDS if key.endswith(('Start','End'))}}
    for key,maximum in bounds.items():
        g.check(type(c.get(key)) is int,path+'.'+key,'mint.config.type','Use exact bounded integer observations.','services')
        g.num(c.get(key),path+'.'+key,1 if key in ('publicWalletLimit','maxBatch') or key.endswith(('Start','End')) else 0,maximum)
    if all(type(c.get(k)) is int for k in bounds):
        g.check(c['teamAllocation']+c['allowlistAllocation']<=1000 and
            0<c['teamStart']<=c['teamEnd']<c['allowlistStart']<=c['allowlistEnd']<c['publicStart']<=c['publicEnd'],
            path,'mint.config.windows','Keep inclusive stages disjoint and allocations within1000.','services')
    g.check(type(c.get('releaseUnusedTeamToPublic')) is bool,path,'mint.team.rollover','Review unused-team reservation explicitly.','services')
    g.hex(c.get('feeRecipient'),path+'.feeRecipient',20)
    g.hex(c.get('allowedPayersHash'),path+'.allowedPayersHash')
    g.hex(c.get('merkleRoot'),path+'.merkleRoot',zero=c.get('teamAllocation')==c.get('allowlistAllocation')==0)
    return c


def _randomness(g,chain,path):
    # Carry the original-request recovery requirements into the NEW mint profile.
    vrf=V._obj(V._obj(chain.get('nft_inventory')).get('randomness'));p=path+'.nft_inventory.randomness'
    g.check(vrf.get('request_profile')==V.VRF_REQUEST_PROFILE and vrf.get('request_selector')==V.VRF_REQUEST_SELECTOR and
        type(vrf.get('num_words')) is int and vrf['num_words']==2,p,'randomness.request_profile','Qualify the original two-word request.','randomness')
    recovery=V._obj(vrf.get('recovery_policy'))
    g.check(all(recovery.get(k)==v for k,v in dict(unserved_request='original_request_remains_valid',
        refund_or_expiry='cannot_invalidate_original_fulfillment',failed_callback='same_request_same_result',reroll='none').items()),
        p,'randomness.recovery_policy','Original requests cannot be cancelled or rerolled.','randomness')
    staged=V._obj(vrf.get('integration_evidence'))
    original=g.num(staged.get('fulfilled_request_id'),p+'.fulfilled_request_id',1)
    recovered=g.num(staged.get('recovery_request_id'),p+'.recovery_request_id',1)
    original_hash=g.hex(staged.get('original_result_sha256'),p+'.original_result_sha256',prefix=False)
    recovered_hash=g.hex(staged.get('recovered_result_sha256'),p+'.recovered_result_sha256',prefix=False)
    g.check(original is not None and recovered==original and original_hash is not None and recovered_hash==original_hash and
        staged.get('request_selector')==V.VRF_REQUEST_SELECTOR and type(staged.get('callback_words_count')) is int and staged['callback_words_count']==2,
        p,'randomness.original_result_recovery','Verify the same original request and result.','randomness')
    for key in ('invalid_proof_rejection_sha256','unauthenticated_callback_rejection_sha256'):
        g.hex(staged.get(key),p+'.'+key,prefix=False)
    funding=V._obj(vrf.get('funding'))
    g.check(funding.get('source')=='external_subscription_reserve',p,'randomness.funding','Fund randomness outside LP and rewards.','randomness')
    g.hex(funding.get('owner'),p+'.funding.owner',20)


def configuration_hashes(chain,section):
    """Independently encode the helper's exact static ABI commitments."""
    config=section['mint_config'];price=V._numeric(section['expected_mint_price_wei'])
    fields=[(config[k],typ) for k,typ in zip(CONFIG_FIELDS,CONFIG_TYPES)]
    semantic=V.identity([(True,'bool')]+fields+[(price,'uint128')])
    full=V.identity([(chain['helpers']['seadrop_mint']['address'],'address'),(chain['modules']['access']['address'],'address'),
        (chain['modules']['nft']['address'],'address'),(section['sea_drop'],'address'),(section['sea_drop_runtime_hash'],'bytes32')]+
        fields+[(price,'uint128'),(section['revision'],'uint64'),(section['configuration_review_hash'],'bytes32')])
    return full,semantic


def mint_integration(g,chain,path):
    section=g.obj(chain.get('primary_mint'),path+'.primary_mint');p=path+'.primary_mint'
    g.keys(section,FIELDS,p)
    g.check(section.get('implementation_profile')==PROFILE,p,'mint.implementation_profile','Use the exact reviewed SeaDrop sequential profile.','services')
    c=_config(g,section.get('mint_config'),p+'.mint_config')
    price=g.num(section.get('expected_mint_price_wei'),p+'.expected_mint_price_wei',1,2**80-1)
    policy_price=V._numeric(V._obj(V._obj(chain.get('protocol_policy')).get('sale')).get('mint_price_wei'))
    g.check(price is not None and price==policy_price,p,'mint.price','Bind explicit configure price to current governed price.','services')
    sd=g.hex(section.get('sea_drop'),p+'.sea_drop',20);runtime=g.hex(section.get('sea_drop_runtime_hash'),p+'.sea_drop_runtime_hash')
    for key in ('configuration_hash','configuration_values_hash','configuration_review_hash'):g.hex(section.get(key),p+'.'+key)
    g.check(type(section.get('revision')) is int,p+'.revision','mint.revision.type','Read the monotonic configuration revision.','services')
    g.num(section.get('revision'),p+'.revision',1,2**64-1)
    try:hashes=configuration_hashes(chain,section)
    except (ValueError,KeyError,TypeError,OverflowError):hashes=None
    g.check(hashes is not None and hashes==(section.get('configuration_hash'),section.get('configuration_values_hash')),
        p,'mint.configuration_hash','Recompute exact helper configuration commitments.','bindings')
    payers=g.items(section.get('allowed_payers'),p+'.allowed_payers',16,0)
    try: payer_hash=address_list_hash(payers)
    except (TypeError,ValueError):payer_hash=None
    g.check(payer_hash is not None and payer_hash==c.get('allowedPayersHash'),p,'mint.payers','Bind the exact sorted approved payer set.','services')
    o=g.obj(section.get('observed'),p+'.observed')
    wanted=dict(helper=chain['helpers']['seadrop_mint']['address'],helper_version=1,sea_drop=sd,sea_drop_code_hash=runtime,
        runtime_hash=runtime,config=c,configured=True,minting=False,revision=section.get('revision'),
        configuration_hash=section.get('configuration_hash'),configuration_values_hash=section.get('configuration_values_hash'),
        configuration_review_hash=section.get('configuration_review_hash'),reviewed_mint_price=price)
    g.keys(o,set(wanted)|{'total_minted','nft_minted_count','vault_sequence','phase_minted','current_phase','ordinals','wallets',
        'public_drop','creator_payout','allowlist_root','allowed_fee_recipients','allowed_payers','signer_count','token_gate_count',
        'mint_end','mint_end_revision'},p+'.observed')
    g.check(all(V._equal(o.get(k),v) for k,v in wanted.items()),p+'.observed','mint.bindings','Compare all source-owned helper configuration observations.','bindings')
    count=g.num(o.get('total_minted'),p+'.observed.total_minted',0,1000)
    g.check(all(type(o.get(k)) is int for k in ('total_minted','nft_minted_count','vault_sequence')) and
        count==o.get('nft_minted_count')==o.get('vault_sequence'),p,'mint.supply','Reconcile helper, NFT and Vault issuance counts.','bindings')
    rows=g.items(o.get('ordinals'),p+'.observed.ordinals',1000,0);wallets=g.items(o.get('wallets'),p+'.observed.wallets',1000,0)
    totals={};allows={};phases=[0,0,0];identifiers=set()
    for index,row in enumerate(rows):
        r=g.obj(row,p+'.observed.ordinals');recipient=r.get('recipient');phase=r.get('stage')
        g.hex(recipient,p+'.observed.ordinals.recipient',20)
        valid=type(phase) is int and 1<=phase<=3
        g.keys(r,{'ordinal','reverse_ordinal','id','recipient','stage','nft_original_recipient','nft_stage'},p+'.observed.ordinals')
        g.check(type(r.get('ordinal')) is int and r['ordinal']==index+1 and type(r.get('id')) is int and r['id']>0 and valid and
            r.get('nft_original_recipient')==recipient and type(r.get('nft_stage')) is int and r['nft_stage']==phase,
            p,'mint.ordinal','Preserve original recipients and stage after transfers/import.','bindings')
        lineage=V._obj(chain.get('canonical_handoff'))
        try:expected_id=int(V.identity([(lineage['origin_chain_id'],'uint256'),(lineage['origin_vault'],'address'),(index+1,'uint256')]),16)
        except (ValueError,KeyError,TypeError,OverflowError):expected_id=None
        identifier=r.get('id');unique=type(identifier) is int and identifier not in identifiers
        g.check(unique and expected_id is not None and identifier==expected_id and type(r.get('reverse_ordinal')) is int and r['reverse_ordinal']==index+1,
            p,'mint.ordinal.identity','Verify unique canonical hashed IDs and reverse ordinals.','bindings')
        if type(identifier) is int:identifiers.add(identifier)
        if valid:phases[phase-1]+=1
        if isinstance(recipient,str):
            totals[recipient]=totals.get(recipient,0)+1
            if phase==2:allows[recipient]=allows.get(recipient,0)+1
    actual_wallets={r.get('address'):(r.get('lifetime'),r.get('allowlist')) for r in wallets if isinstance(r,dict)}
    for row in wallets:
        r=g.obj(row,p+'.observed.wallets');g.keys(r,{'address','lifetime','allowlist'},p+'.observed.wallets')
        g.check(all(type(r.get(k)) is int and 0<=r[k]<=1000 for k in ('lifetime','allowlist')),
            p,'mint.wallet.type','Use exact whole lifetime counts.','bindings')
    g.check(count==len(rows) and len(wallets)==len(totals) and len(actual_wallets)==len(wallets) and
        actual_wallets=={a:(n,allows.get(a,0)) for a,n in totals.items()} and all(n<=1 for n in allows.values()) and
        isinstance(o.get('phase_minted'),list) and all(type(n) is int for n in o['phase_minted']) and
        o['phase_minted']==phases,p,'mint.lifetime','Rebuild complete lifetime wallet and phase counts.','bindings')
    g.check(type(o.get('current_phase')) is int and 0<=o['current_phase']<=3 and
        type(o.get('mint_end_revision')) is int and 0<=o['mint_end_revision']<2**64,
        p,'mint.observation.type','Read exact phase and sale-end revision.','bindings')
    g.check(type(c.get('teamAllocation')) is int and type(c.get('allowlistAllocation')) is int and
        phases[0]<=c['teamAllocation'] and phases[1]<=c['allowlistAllocation'],p,'mint.phase_caps','Historical phase counts cannot exceed configured quotas.','bindings')
    if c.get('releaseUnusedTeamToPublic') is False and count is not None and type(c.get('teamAllocation')) is int:
        g.check(count<=1000-c['teamAllocation']+phases[0],p,'mint.team.reservation','Unused team supply remains reserved.','bindings')
    g.check(o.get('allowlist_root')==c.get('merkleRoot') and o.get('allowed_fee_recipients')==[c.get('feeRecipient')] and
        o.get('allowed_payers')==payers and o.get('signer_count')==o.get('token_gate_count')==0,p,'mint.drop_controls','Reject unreviewed payers, fees and mint families.','bindings')
    public=dict(mintPrice=price,startTime=c.get('publicStart'),endTime=c.get('publicEnd'),
        maxTotalMintableByWallet=c.get('publicWalletLimit'),feeBps=c.get('feeBps'),restrictFeeRecipients=True)
    g.check(V._equal(o.get('public_drop'),public) and o.get('creator_payout')==V._obj(V._obj(chain.get('protocol_policy')).get('sale')).get('recipient') and
        o.get('mint_end')==c.get('publicEnd'),p,'mint.drop_state','Bind actual payment settings and official sale end.','bindings')
    for field,kind in (('review_evidence','seadrop_mint_implementation_review'),('manifest_review_evidence','seadrop_leaf_manifest_review'),
            ('onboarding_evidence','opensea_primary_drop_acceptance'),('fee_qualification_evidence','opensea_primary_fee_qualification'),
            ('operating_evidence','seadrop_wallet_operating_qualification')):
        proof=V._bound_proof(g,section.get(field),p+'.'+field,chain,kind=kind,exact_block=field=='operating_evidence')
        if field=='onboarding_evidence':g.check(proof.get('primary_drop_accepted') is True,p,'mint.onboarding','Qualify actual OpenSea primary-drop onboarding.','services')
        if field=='manifest_review_evidence':
            g.check(proof.get('review_hash')==section.get('configuration_review_hash') and proof.get('allowlist_root')==c.get('merkleRoot') and
                V._numeric(proof.get('mint_price_wei'))==price and proof.get('mint_config_sha256')==V.configuration_hash(c),
                p,'mint.manifest_scope','Review the exact root, price and configuration.','services')
        if field=='fee_qualification_evidence':
            g.check(type(proof.get('fee_bps')) is int and proof['fee_bps']==c.get('feeBps') and proof.get('fee_recipient')==c.get('feeRecipient'),
                p,'mint.fee_scope','Qualify the actual buyer-inclusive platform fee.','services')
    integration=V._obj(V._obj(V._obj(chain.get('services')).get('opensea')).get('integration'))
    g.check(integration.get('requested_product')=='opensea_seadrop_v1' and integration.get('implementation_profile')==PROFILE,
        p,'mint.product','Do not substitute generic marketplace chain support.','services')
    _randomness(g,chain,path)


def validate(config,*,expected_commit=None,now=None):
    return BASE._validate(config,expected_commit=expected_commit,now=now,versions=VERSIONS,helpers=HELPERS,
        binding_factory=expected_bindings,service_profiles=SERVICE_PROFILES,route_validator=H.LEGACY.validate_routes,
        royalty_conversion=False,token_validator=validate_tokens,canonical_schema_name=SCHEMA_NAME,canonical_schema_hash=SCHEMA_HASH,
        royalty_max_assets=65,royalty_mint_revision=True,chain_fields=CHAIN_FIELDS,chain_validator=H.factory_code,
        top_fields=TOP_FIELDS,mint_validator=mint_integration,mint_implementation=PROFILE)
