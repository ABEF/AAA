"""Historical legacy disposable inputs; never current V2 qualification or public routes."""
from zzz_ops.abi import keccak256
from scripts.local_fixture_profile import require_legacy_fixture_artifacts

UNIT = 10**18
ZERO = '0x'+'00'*20
EMPTY = '0x'+'00'*32

def deploy_inputs(lab):
    zzz = lab.deploy('LocalInputToken', 'constructor(string,uint8)', ('ZZZ',18),local=True)
    weth = lab.deploy('LocalInputWETH',local=True)
    usdc = lab.deploy('LocalInputToken', 'constructor(string,uint8)', ('USDC',6),local=True)
    usdg = lab.deploy('LocalInputToken', 'constructor(string,uint8)', ('USDG',6),local=True)
    lab.tokens = [weth,zzz] if getattr(lab,'native_input',False) else sorted([zzz,weth])
    lab.input_assets = [dict(symbol=s,address=a,decimals=d,route_id=EMPTY,enabled=True)
                        for s,a,d in [('ZZZ',zzz,18),('USDG',usdg,6),('USDC',usdc,6),('ETH',ZERO,18)]]
    lab.weth = weth
    # Reserve-backed WETH only; deposit test ETH then transfer, never mint a fake wrapper balance.
    lab.call(weth,'deposit()',value=4_000_000*UNIT)

def configure_inputs(lab):
    require_legacy_fixture_artifacts(lab.args.artifacts)
    assets = lab.addr('pools','activationAssets()')
    factory = lab.deploy('LocalInputFactory',local=True)
    router = lab.deploy('LocalInputRouter','constructor(address)',(factory,),local=True)
    zzz = next(a['address'] for a in lab.input_assets if a['symbol']=='ZZZ')
    lab.call(zzz,'mint(address,uint256)',router,1_000_000*UNIT)
    for a in lab.input_assets:
        if a['symbol'] in ('ETH','ZZZ'):continue
        token=a['address'];lab.call('oracle','setFeed(address,address,uint32)',token,lab.feed,3600)
        for owner in lab.accounts:lab.call(token,'mint(address,uint256)',owner,100_000*10**a['decimals'])
        review='0x'+keccak256(('LOCAL ONLY '+a['symbol']).encode()).hex()
        lab.call(assets,'setAsset(address,bool,bytes32,bytes32)',token,True,lab.pin(token)['code_hash'],review)
        lab.call(factory,'create(address,address)',token,zzz)
        pool=lab.addr(factory,'getPool(address,address,uint24)',token,zzz,500)
        if getattr(lab.args,'venue_fixture',None)=='LocalAPIVenue':
            # Explicit reserve presence for the API fixture, no real V3 pool claim.
            lab.call(token,'transfer(address,uint256)',pool,1000*10**a['decimals'])
            lab.call(zzz,'transfer(address,uint256)',pool,1000*UNIT)
        values=[token,zzz,router,factory,pool,500,*[lab.pin(x)['code_hash'] for x in (router,factory,pool,token,zzz)],review]
        signature='(address,address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32,bytes32)'
        tuple_value='('+','.join(map(str,values))+')'
        a['route_id']='0x'+keccak256(bytes.fromhex(lab.encode('policy('+signature+')',tuple_value,constructor=True)[2:])).hex()
        lab.call('entry','addRoute('+signature+')',tuple_value)

    # Dedicated LP conversion instance, using only reserve-backed local WETH and
    # the deterministic $1 test venue. This is not a reviewed public swap route.
    converter=lab.deploy('ZZZLPRewardConverter','constructor(address,address,address)',
                        (lab.contracts['access'],lab.contracts['rewards'],lab.weth))
    lab.contracts['lp_converter']=converter
    lab.call('rewards','bindConverter(address)',converter)
    review='0x'+keccak256(b'LOCAL LP SETTLEMENT ONLY').hex()
    wrapper=f'({lab.pin(lab.weth)["code_hash"]},{ZERO},{ZERO},{ZERO},{EMPTY},{EMPTY},{review})'
    lab.call(converter,'configureWrapper((bytes32,address,address,address,bytes32,bytes32,bytes32))',wrapper)
    lab.call(converter,'setEnabled(bool)',True)
    lab.call(factory,'create(address,address)',zzz,lab.weth)
    pool=lab.addr(factory,'getPool(address,address,uint24)',zzz,lab.weth,500)
    lab.call(lab.weth,'transfer(address,uint256)',router,100_000*UNIT)
    values=[zzz,router,factory,pool,500,*[lab.pin(x)['code_hash'] for x in (zzz,router,factory,pool)],review]
    signature='(address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32)'
    policy='('+','.join(map(str,values))+')'
    lab.lp_route='0x'+keccak256(bytes.fromhex(lab.encode('policy('+signature+')',policy,constructor=True)[2:])).hex()
    lab.call(converter,'addRoute('+signature+')',policy)

def settle_lp(lab, identifiers):
    if not getattr(lab,'lp_route',None): return
    ids=sorted(map(int,identifiers))
    for token in lab.tokens:
        total=sum(lab.uint('rewards','claimable(uint256,address)',i,token) for i in ids)
        if not total: continue
        route=EMPTY if token==lab.weth else lab.lp_route
        lab.call('rewards','convertBatch(address,uint256[],bytes32,uint256,uint256)',token,
                 '['+','.join(map(str,ids))+']',route,max(1,total*99//100),lab.clock()+120)

def input_for(lab, symbol=None):
    inventory=getattr(lab,'input_assets',None)
    if not inventory:
        if symbol not in (None,'TEST-1'):raise ValueError('This older local deployment has no route for that asset')
        return dict(symbol='TEST-1',address=lab.tokens[0],decimals=18,route_id=EMPTY,enabled=True)
    if symbol is None:symbol='ZZZ'
    match=next((a for a in inventory if a['symbol']==symbol),None)
    if not match or not match['enabled']:raise ValueError('Unsupported or disabled local input')
    return match

def input_tx(lab, owner, identifier, value, increase, asset=None):
    a=input_for(lab,asset);source=lab.weth if a['symbol']=='ETH' else a['address']
    native=a['symbol']=='ETH' and getattr(lab,'native_input',False)
    if native:source=ZERO
    amount=value*10**a['decimals'];route=a['route_id']
    minimum=value*UNIT*99//100 if route!=EMPTY else 0
    return {'from':owner,'to':lab.contracts['entry'],'value':hex(amount) if native else '0x0',
            'data':lab.encode('execute((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool))',
                f'({identifier},{lab.pool},{source},{amount},{route},{minimum},1,{lab.clock()+120},{str(increase).lower()})')}
