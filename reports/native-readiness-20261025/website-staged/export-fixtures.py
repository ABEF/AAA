"""Export actual current Python API DTOs; all venue/feed/RPC data synthetic."""
import copy, hashlib, json, sys
from pathlib import Path

ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(ROOT))
from tests_python.test_dual_price_integration import DualActivationRPC,install,bounds
from tests_python.test_frontend_api import configuration,addr,words
from tests_python.test_native_backend_boundary import native_data
from frontend_api.service import Projection,ZERO
from frontend_api.activation import ActivationTransactions
from frontend_api.transactions import Transactions
from tests_python.test_frontend_transactions import transaction_config
from zzz_ops.abi import calldata,keccak256
from zzz_ops import price_policy as D

OUT=Path(__file__).parent
fixtures={}
for name,options in [('activate_eth',{}),('increase_eth',{'increase':True}),
                     ('activate_usdg',{'routed':True}),('approve_usdg',{'routed':True}),
                     ('claim_eth_both',{'increase':True})]:
    rpc=install(DualActivationRPC(loss=200,**options))
    # Match the approved 3% disagreement policy without inventing live sources.
    for token in rpc.config['tokens']:
        record=token['price_policy'];record['policy']['maxDeviationBps']=300
        record['policy_id']=D.policy_id(rpc.pins['oracle'],record['ordinal'],record['policy'])
        rpc.responses[rpc.pins['oracle'],native_data('activePolicy(address)',token['address'])]=words(record['policy_id'])
        rpc.put(rpc.pins['oracle'],'policyAt(uint256)',(record['ordinal'],),(record['policy_id'],))
        rpc.put(rpc.pins['oracle'],'policy(bytes32)',(record['policy_id'],),D.flat(record['policy']))
        value=bounds(record,rpc.pins['oracle'])
        rpc.responses[rpc.pins['oracle'],native_data('priceBounds(address)',token['address'])]=words(value['lower'],value['upper'],value['fingerprint'])
    cfg=configuration();cfg['accounting_version']=2
    # Projection and activation use one coherent, explicitly local asset inventory.
    cfg['assets']=[dict(address=ZERO,symbol='ETH',decimals=18,code_hash=None)]+[
        dict(address=addr(n),symbol='ZZZ' if n==20 else 'USDC',decimals=18,code_hash=rpc.digest(addr(n)))
        for n in (20,21)]
    # Native-V2 LP ledger reserves address(0) at index zero. The two ERC20s
    # remain explicit synthetic historical settlement currencies, not live fees.
    rpc.put(addr(4),'assetCount()',values=(3,))
    for index,asset in enumerate([ZERO,addr(20),addr(21)]):
        rpc.put(addr(4),'assets(uint256)',(index,),(asset,))
    rpc.put(addr(4),'claimable(uint256,address)',(rpc.nft_id,ZERO),(0,))
    if name=='claim_eth_both':
        rpc.put(addr(4),'claimable(uint256,address)',(rpc.nft_id,ZERO),(3*10**16,))
    # The preparation fixture tests read fewer NFT views than a full read DTO.
    # Make dormant membership and historical balances consistently empty.
    if not options.get('increase'):
        for signature,values in [('nftBucket(uint256)',(0,)),('sharesOf(uint256)',(0,)),
                                  ('currentLPValue(uint256)',(1,0))]:
            rpc.put(addr(3) if signature!='currentLPValue(uint256)' else addr(2),signature,(rpc.nft_id,),values)
        rpc.put(addr(5),'weightOf(uint256)',(rpc.nft_id,),(0,))
        for role,assets in [(4,[addr(20),addr(21)]),(5,[ZERO,addr(21)])]:
            for asset in assets:rpc.put(addr(role),'claimable(uint256,address)',(rpc.nft_id,asset),(0,))
    # Read API still lists historical currencies; all are exactly admitted.
    for token in cfg['assets']:
        if token['address']!=ZERO:
            rpc.put(token['address'],'decimals()',values=(token['decimals'],))
    if name.startswith('approve'):rpc.allowance=0
    p=Projection(cfg,rpc,clock=lambda:1000)
    protocol=p.protocol()
    nft=p.nft(str(rpc.nft_id))
    if name=='claim_eth_both':
        original_call=rpc.call
        def claim_call(method,params):
            if method=='eth_call' and params[0].get('to')==addr(6) and 'from' in params[0]:
                rpc.calls.append((method,copy.deepcopy(params)))
                return words(32,2,3*10**16,33333333333333333333)
            return original_call(method,params)
        rpc.call=claim_call
        draft=Transactions(p,transaction_config(p)).prepare(dict(action='claim',wallet=addr(30),
            claims=[dict(token_id=str(rpc.nft_id),asset=ZERO,royalty=royalty) for royalty in (False,True)]))
    else:draft=ActivationTransactions(p,rpc.config).prepare(rpc.request)
    source=next(t for t in rpc.config['tokens'] if t['address']==rpc.source)
    fixtures[name]=dict(protocol=protocol,nft=nft,draft=draft,projection_identity=p.identity,source_asset=rpc.source,
        pins=rpc.pins,codes=rpc.codes,route=rpc.route,source_decimals=source['decimals'],
        source_price_policy=source['price_policy'],asset_policy=rpc.config['sources'][0]['asset_policy_id'],
        route_kind=rpc.config['sources'][0]['route_kind'],
        rpc_responses=[dict(target=t,data=d,result=v) for (t,d),v in rpc.responses.items()])
target=OUT/'deployment-native-api.json'
target.write_text(json.dumps(fixtures,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'file':str(target),'fixtures':list(fixtures),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'scope':'Real Python API serialization with synthetic pinned dependencies; no live provider or wallet.'}))
