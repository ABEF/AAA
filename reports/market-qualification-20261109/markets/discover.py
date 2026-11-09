import json,pathlib,sys
from capture import ROOT,rpc,save
REPO=pathlib.Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(REPO))
from zzz_ops.abi import keccak256
Z='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
W='0x0bd7d308f8e1639fab988df18a8011f41eacad73'
C='0x8366a39cc670b4001a1121b8f6a443a643e40951'
F='0x1f7d7550b1b028f7571e69a784071f0205fd2efa'
S='0xf3334192d15450cdd385c8b70e03f9a6bd9e673b'
A=json.loads((ROOT/'anchor.json').read_text(encoding='utf-8'))
PIN={'blockHash':A['hash'],'requireCanonical':True}
def h(s): return '0x'+keccak256(s.encode()).hex()
def word(x): return int(x,16).to_bytes(32,'big').hex() if isinstance(x,str) else x.to_bytes(32,'big').hex()
def data(sig,*args): return h(sig)[:10]+''.join(word(x) for x in args)
def call(addr,sig,*args): return ('eth_call',[{'to':addr,'data':data(sig,*args)},PIN])
def put(name,obj):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')

if __name__=='__main__':
    commits=save('official-registry-commits','https://api.github.com/repos/Uniswap/contracts/commits?path=deployments/4663.md&per_page=1')
    if isinstance(commits,list):
        commit=commits[0]['sha']
        save('official-registry-pinned','https://raw.githubusercontent.com/Uniswap/contracts/'+commit+'/deployments/4663.md')
        put('registry-pin.json',{'repository':'https://github.com/Uniswap/contracts','commit':commit,'path':'deployments/4663.md'})
    for label,url in [('v4-quoter','https://raw.githubusercontent.com/Uniswap/v4-periphery/main/src/interfaces/IV4Quoter.sol'),('v3-quoter','https://raw.githubusercontent.com/Uniswap/v3-periphery/main/contracts/interfaces/IQuoterV2.sol')]:save('official-'+label,url)
    logs=rpc('v4-initialize-all-01',('eth_getLogs',[{'address':C,'fromBlock':'0x0','toBlock':A['number'],'topics':[h('Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)'),None,'0x'+word(0),'0x'+word(Z)]}]))
    fees=rpc('v3-fees-all-01',('eth_getLogs',[{'address':F,'fromBlock':'0x0','toBlock':A['number'],'topics':[h('FeeAmountEnabled(uint24,int24)')]}]))
    batch=[]
    for fee in [100,250,500,1000,3000,10000]:batch.extend([call(F,'feeAmountTickSpacing(uint24)',fee),call(F,'getPool(address,address,uint24)',Z,W,fee)])
    res=rpc('v3-known-fees-01',batch)
    put('v3-known-fees-decoded.json',[{'fee':f,'spacing_response':res[i*2],'pool_response':res[i*2+1]} for i,f in enumerate([100,250,500,1000,3000,10000])])
    addrs={'ZZZ':Z,'WETH':W,'V4PoolManager':C,'V4StateView':S,'V4PositionManager':'0x58daec3116aae6d93017baaea7749052e8a04fa7','V4Quoter':'0x8dc178efb8111bb0973dd9d722ebeff267c98f94','V3Factory':F,'V3SwapRouter02':'0xcaf681a66d020601342297493863e78c959e5cb2','V3QuoterV2':'0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'}
    codes=rpc('bindings-code-01',[('eth_getCode',[addr,PIN]) for addr in addrs.values()])
    put('bindings-runtime-hashes.json',[{'name':k,'address':v,'runtime_bytes':len(bytes.fromhex(r['result'][2:])),'runtime_keccak256':'0x'+keccak256(bytes.fromhex(r['result'][2:])).hex()} for (k,v),r in zip(addrs.items(),codes)])
    bindings=rpc('bindings-call-01',[call(S,'poolManager()'),call(addrs['V4PositionManager'],'poolManager()'),call(addrs['V4Quoter'],'poolManager()'),call(addrs['V3SwapRouter02'],'factory()'),call(addrs['V3SwapRouter02'],'WETH9()'),call(Z,'decimals()'),call(Z,'totalSupply()')])
    print(json.dumps({'v4_log_result':logs,'v3_fee_events':fees,'v3_known_pools':res},indent=2))
