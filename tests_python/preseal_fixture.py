"""Explicit synthetic planner inputs; no real dependency/authority admission."""
import copy
import hashlib
import json
from pathlib import Path

from zzz_ops import deployment_plan as D, opensea_drop as O
from zzz_ops.abi import keccak256


def addr(n): return '0x'+format(n,'040x')
def code(n): return '0x'+format(n,'064x')
ZZZ_CODE='0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597'
CORE_CODE='0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626'
STATE_CODE='0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6'


def pool_key(fee='10020',spacing='200'):
    return dict(currency0=D.ZERO,currency1=D.NATIVE['zzz'],fee=fee,tickSpacing=spacing,hooks=D.ZERO)


def pool_id(key):
    values=[int(key[k],16) if k in ('currency0','currency1','hooks') else int(key[k])
            for k in ('currency0','currency1','fee','tickSpacing','hooks')]
    return '0x'+keccak256(b''.join((v % (1<<256)).to_bytes(32,'big') for v in values)).hex()


def pool_config(key,deposits):
    return dict(key=copy.deepcopy(key),depositsEnabled=deposits,operationsEnabled=True,
        rangeBps='5000',triggerBps='100',maxSpotDeviationBps='300',maxSlippageBps='200',
        minRebalanceInterval='43200',minDepositUSD=str(100*10**18),maxPositionUSD=str(10**24))


def constructor():
    value=D.template()
    value['planned_addresses']={role:addr(1000+n) for n,(role,_,_) in enumerate(D.TOP)}
    value['inputs'].update(governance=addr(1),keeper=addr(2),guardian=addr(3),mint_recipient=addr(4),
        sequencer=D.ZERO,**D.NATIVE,seadrop=D.SEADROP,seadrop_codehash=D.SEADROP_HASH,
        base_uri='ipfs://preseal-synthetic-content/',buyback_maximum_trade_usd=str(100*10**18))
    value['qualification_evidence']={name:format(99,'064x') for name in D.QUALIFICATIONS}
    return value


def proof_artifact(folder,construct):
    request=dict(schema=1,chain_id='4663',nft_contract=construct['planned_addresses']['nft'],
        seadrop=D.SEADROP,seadrop_runtime_keccak256=D.SEADROP_HASH,
        creator_payout_address=construct['inputs']['mint_recipient'],mint_price_wei='50000000000000000',
        fee_bps='500',fee_recipient=addr(8),public_wallet_limit='2',max_batch='4',
        team=[dict(address=addr(30),quantity='20')],allowlist=[addr(31),addr(32)],
        team_allocation='20',allowlist_allocation='500',allowed_payers=[addr(33)],
        team_window=dict(start='100',end='199'),allowlist_window=dict(start='200',end='299'),
        public_window=dict(start='300',end='399'),release_unused_team_to_public=False,
        review_notes_sha256=format(77,'064x'),source_sha256=O.source_identity())
    artifact=O.prepare(request)
    raw=O.render(artifact);path=Path(folder)/'proofs.json';path.write_bytes(raw)
    return artifact,dict(artifact_path=str(path),artifact_sha256=hashlib.sha256(raw).hexdigest())


def complete(folder):
    from zzz_ops import preseal_plan as P
    value=P.example();value['constructor_input']=constructor();value['bootstrap']=addr(9)
    value['child_addresses']={role:addr(2000+n) for n,(role,*_) in enumerate(D.INTERNAL)}
    def source(number):
        return dict(source=addr(number),expectedCodeHash=code(number),independenceId=code(number+100),
                    maxAge='3600',feedDecimals='8')
    value['settings']['dual_usd']={name:dict(primary=source(n),secondary=source(n+1),
        maxDeviationBps='300',reviewHash=code(n+200)) for name,n in (('eth',3000),('zzz',4000))}
    value['settings']['dual_usd']['zzz']['primary']['feedDecimals']='18'
    value['settings']['fixed_zzz']=dict(expectedCodeHash=ZZZ_CODE,reviewHash=code(12))
    value['settings']['lp_asset']=dict(add_fixed_zzz=True)
    value['settings']['migration_zzz']=dict(codeHash=ZZZ_CODE,reviewHash=code(13))
    value['settings']['execution_sources']=dict(sources=[dict(source=addr(4000),expectedCodeHash=code(4000),reviewHash=code(14))])
    main=pool_key();venue=pool_key('3000','60')
    value['settings']['native_pools']=dict(pools=[dict(config=pool_config(main,True),orientation='1'),
                                                dict(config=pool_config(venue,False),orientation='1')])
    route=dict(source=D.NATIVE['zzz'],output=D.ZERO,key=copy.deepcopy(venue),
        poolManager=D.NATIVE['pool_manager'],stateView=D.NATIVE['state_view'],
        sourceCodeHash=ZZZ_CODE,outputCodeHash='0x'+keccak256(b'ZZZ_NATIVE_ETH_V1').hex(),
        poolManagerCodeHash=CORE_CODE,stateViewCodeHash=STATE_CODE,reviewHash=code(17))
    value['settings']['routes']=dict(execution_pool_ids=[pool_id(venue)],execution_review_hash=code(18),
        conversion_routes=[route],conversion_enabled=True)
    value['settings']['confirmation']=dict(secondsRequired='600',maximumGap='300',reviewed=code(19),
        requireReferenceExit=True,referenceReview=code(20))
    value['settings']['randomness']=dict(coordinator=addr(5000),expectedCodeHash=code(21),keyHash=code(22),
        subscriptionId='1',confirmations='3',callbackGas='500000',nativePayment=True,reviewHash=code(23))
    artifact,terms=proof_artifact(folder,value['constructor_input']);value['settings']['seadrop_terms']=terms
    value['settings']['seadrop_upstream']=dict(publicKeyURIs=['ipfs://synthetic-public-proof/'],
        allowListURI='ipfs://synthetic-allowlist/',dropURI='ipfs://synthetic-drop/',
        existingFeeRecipients=[],existingPayers=[],existingSigners=[],existingTokenGated=[])
    value['settings']['mint_end']=dict(end=artifact['mint_config']['publicEnd'])
    return value
