"""Export actual Python API response shapes against existing byte-level fixtures.
No chain connection, signer, funds or unchanged test suite is used.
"""
import sys,json,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests_python.test_frontend_activation import ActivationRPC, ActivationPreparationTests, USD
from tests_python.test_frontend_transactions import TransactionRPC, transaction_config
from tests_python.test_frontend_api import configuration,addr
from frontend_api.service import Projection, ZERO
from frontend_api.activation import ActivationTransactions
from frontend_api.transactions import Transactions
from zzz_ops.abi import keccak256

def setup(rpc):
    cfg=configuration()
    for asset in cfg['assets']:
        if asset['address']!=ZERO:
            asset['code_hash']='0x'+keccak256(bytes.fromhex(rpc.codes[asset['address']][2:])).hex()
            if isinstance(rpc,ActivationRPC):asset['decimals']=18
    rpc.put(addr(2),'mintedCount()',values=(1,))
    rpc.put(addr(2),'nextToFinalize()',values=(2,))
    rpc.put(addr(2),'remainingToReveal()',values=(999,))
    for i,v in enumerate((600,299,100)):rpc.put(addr(2),'rarityRemaining(uint256)',(i,),(v,))
    rpc.put(addr(2),'randomnessConfigured()',values=(1,))
    rpc.put(addr(2),'randomnessCoordinator()',values=(addr(90),))
    rpc.put(addr(2),'mintOrdinalOf(uint256)',(rpc.nft_id,),(1,))
    rpc.put(addr(2),'tokenAtOrdinal(uint256)',(1,),(rpc.nft_id,))
    p=Projection(cfg,rpc,clock=lambda:1000)
    return p

out={}
for name,options in [('activate_zzz',{}),('activate_eth',{'native':True}),('activate_usdc',{'conversion':True,'source_decimals':6}),('activate_usdg',{'conversion':True}),('increase_zzz',{'increase':True}),('increase_usdc_5',{'increase':True,'conversion':True,'source_decimals':6}),('increase_eth_5',{'increase':True,'native':True}),('approve_zzz',{}),('approve_usdc',{'conversion':True,'source_decimals':6})]:
    rpc=ActivationPreparationTests().small_contribution(value=5*USD,**options) if name.endswith('_5') else ActivationRPC(**options)
    if name.startswith('approve'):rpc.allowance=0
    p=setup(rpc)
    active=options.get('increase',False)
    if not active:
        rpc.put(addr(3),'nftBucket(uint256)',(rpc.nft_id,),(0,))
        rpc.put(addr(3),'sharesOf(uint256)',(rpc.nft_id,),(0,))
        rpc.put(addr(5),'weightOf(uint256)',(rpc.nft_id,),(0,))
        rpc.put(addr(2),'currentLPValue(uint256)',(rpc.nft_id,),(1,0))
    service=ActivationTransactions(p,rpc.config)
    rpc.request['slippage_bps']=100
    draft=service.prepare(rpc.request)
    out[name]={'protocol':p.protocol(),'nft':p.nft(str(rpc.nft_id)), 'readiness':p.mint_readiness(), 'draft':draft,'request':rpc.request,
        'codes':rpc.codes,'pins':rpc.pins,'source_decimals':rpc.source_decimals,'route':rpc.config['sources'][0]['route_id'],'projection_identity':p.identity}

rpc=TransactionRPC();p=setup(rpc);service=Transactions(p,transaction_config(p))
for name,request in [('mint',{'action':'mint','wallet':addr(30)}),('claim',{'action':'claim','wallet':addr(30),'claims':[{'token_id':str(rpc.nft_id),'asset':ZERO,'royalty':True}]})]:
    out[name]={'protocol':p.protocol(),'nft':p.nft(str(rpc.nft_id)),'readiness':p.mint_readiness(),'draft':service.prepare(request),'request':request,'codes':rpc.codes,'projection_identity':p.identity}
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',required=True,type=Path)
target=parser.parse_args().output.resolve()
if target.suffix!='.json':raise ValueError('Fixture output must be a JSON file')
target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'cases':list(out),'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
