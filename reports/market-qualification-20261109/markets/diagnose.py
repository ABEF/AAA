from discover import *
from quotes import v4call
from zzz_ops.tick_math import sqrt_price_at_tick
import hashlib
if __name__=='__main__':
    sources=[]
    expected={x['name']:x['runtime_keccak256'] for x in json.loads((ROOT/'bindings-runtime-hashes.json').read_text(encoding='utf-8'))}
    for label,name in [('core','V4PoolManager'),('quoter','V4Quoter'),('wrapper','WETH'),('zzz','ZZZ')]:
        obj=json.loads((ROOT/('explorer-'+label+'-02-response.raw')).read_text(encoding='utf-8'))
        folder=ROOT/'verified-sources'/label;folder.mkdir(parents=True,exist_ok=False)
        items=[{'file_path':obj['file_path'],'source_code':obj['source_code']}]+obj.get('additional_sources',[])
        for item in items:
            pp=pathlib.PurePosixPath(item['file_path'])
            if pp.is_absolute() or '..' in pp.parts:raise ValueError('unsafe original path')
            target=folder.joinpath(*pp.parts);target.parent.mkdir(parents=True,exist_ok=True)
            raw=item['source_code'].encode('utf-8')
            with target.open('xb') as f:f.write(raw)
            sources.append({'path':str(target.relative_to(ROOT)).replace('\\','/'),'original_file_path':item['file_path'],'sha256':hashlib.sha256(raw).hexdigest()})
        bytecode=obj.get('deployed_bytecode','')
        bytecode=bytecode[2:] if bytecode.startswith('0x') else bytecode
        actual='0x'+keccak256(bytes.fromhex(bytecode)).hex() if bytecode else None
        print(json.dumps({'label':label,'verified':obj.get('is_verified'),'name':obj.get('name'),'compiler':obj.get('compiler_version'),'explorer_runtime_hash':actual,'pinned_runtime_hash':expected[name],'runtime_matches':actual==expected[name]}))
        if actual!=expected[name]:raise ValueError('verified-source runtime differs')
    put('verified-source-manifest.json',sources)
    chosen=next(x for x in json.loads((ROOT/'v4-hookless-state.json').read_text(encoding='utf-8')) if x['poolId'].startswith('0x501122'))
    poolid=chosen['poolId'];tick=chosen['slot0']['tick'];upper=((tick//200)+1)*200
    calls=[call(S,'getTickInfo(bytes32,int24)',poolid,upper),call(S,'getTickInfo(bytes32,int24)',poolid,upper+200),call(S,'getTickBitmap(bytes32,int16)',poolid,tick//200//256),call(C,'protocolFeeController()'),call(C,'owner()')]
    for amount in [1,10**6,10**12,10**15]:calls.append(v4call(chosen['key'],False,amount))
    r=rpc('selected-reverse-diagnosis-01',calls)
    put('selected-reverse-diagnosis.json',{'anchor':A['hash'],'upper_tick':upper,'upper_sqrt':sqrt_price_at_tick(upper),'stored_sqrt':chosen['slot0']['sqrtPriceX96'],'exact_upper_boundary':sqrt_price_at_tick(upper)==chosen['slot0']['sqrtPriceX96'],'NotEnoughLiquidity_selector':h('NotEnoughLiquidity(bytes32)')[:10],'UnexpectedRevertBytes_selector':h('UnexpectedRevertBytes(bytes)')[:10],'responses':r})
    impl='0xc6b81b429797e0f555440b70cd99e032d7ae947e';admin='0xa3acd31afb851b4eb9dad00f5204c01d924267df'
    dep=rpc('wrapper-control-02',[('eth_getCode',[impl,PIN]),('eth_getCode',[admin,PIN]),call(admin,'owner()')])
    put('wrapper-control-decoded.json',{'implementation':impl,'implementation_runtime_keccak256':'0x'+keccak256(bytes.fromhex(dep[0]['result'][2:])).hex(),'admin':admin,'admin_runtime_keccak256':'0x'+keccak256(bytes.fromhex(dep[1]['result'][2:])).hex(),'admin_owner':dep[2]})
    print(json.dumps({'selected_exact_upper':sqrt_price_at_tick(upper)==chosen['slot0']['sqrtPriceX96'],'tick_responses':r[:3],'tiny_quotes':r[5:],'wrapper_owner':dep[2]},indent=2))
