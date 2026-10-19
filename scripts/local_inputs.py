"""Named disposable inputs for the local browser lab, never public routes."""
from zzz_ops.abi import keccak256

UNIT = 10**18
ZERO = '0x'+'00'*20
EMPTY = '0x'+'00'*32

def deploy_inputs(lab):
    zzz = lab.deploy('LocalInputToken', 'constructor(string,uint8)', ('ZZZ',18),local=True)
    weth = lab.deploy('LocalInputWETH',local=True)
    usdc = lab.deploy('LocalInputToken', 'constructor(string,uint8)', ('USDC',6),local=True)
    usdg = lab.deploy('LocalInputToken', 'constructor(string,uint8)', ('USDG',6),local=True)
    lab.tokens = sorted([zzz,weth])
    lab.input_assets = [dict(symbol=s,address=a,decimals=d,route_id=EMPTY,enabled=True)
                        for s,a,d in [('ZZZ',zzz,18),('USDG',usdg,6),('USDC',usdc,6),('ETH',ZERO,18)]]
    lab.weth = weth
    # Reserve-backed WETH only; deposit test ETH then transfer, never mint a fake wrapper balance.
    lab.call(weth,'deposit()',value=4_000_000*UNIT)

def configure_inputs(lab):
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
        values=[token,zzz,router,factory,pool,500,*[lab.pin(x)['code_hash'] for x in (router,factory,pool,token,zzz)],review]
        signature='(address,address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32,bytes32)'
        tuple_value='('+','.join(map(str,values))+')'
        a['route_id']='0x'+keccak256(bytes.fromhex(lab.encode('policy('+signature+')',tuple_value,constructor=True)[2:])).hex()
        lab.call('entry','addRoute('+signature+')',tuple_value)

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
    amount=value*10**a['decimals'];route=a['route_id']
    minimum=value*UNIT*99//100 if route!=EMPTY else 0
    return {'from':owner,'to':lab.contracts['entry'],'value':'0x0',
            'data':lab.encode('execute((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool))',
                f'({identifier},{lab.pool},{source},{amount},{route},{minimum},1,{lab.clock()+120},{str(increase).lower()})')}
