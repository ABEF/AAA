from discover import *
if __name__=='__main__':
    for label,addr in [('core',C),('quoter',QV if False else '0x8dc178efb8111bb0973dd9d722ebeff267c98f94'),('wrapper',W),('zzz',Z)]:
        obj=save('explorer-'+label+'-01','https://robinhoodchain.blockscout.com/api/v2/smart-contracts/'+addr)
        if isinstance(obj,dict) and isinstance(obj.get('source_code'),str):
            with (ROOT/('verified-'+label+'.sol')).open('x',encoding='utf-8',newline='\n') as f:f.write(obj['source_code'])
            print(json.dumps({'contract':label,'name':obj.get('name'),'errors':[x for x in obj.get('abi',[]) if x.get('type')=='error']}))
    slots=['0x'+format(int.from_bytes(keccak256(s.encode()),'big')-1,'064x') for s in ['eip1967.proxy.implementation','eip1967.proxy.admin']]
    results=rpc('wrapper-proxy-01',[('eth_getStorageAt',[W,s,PIN]) for s in slots]+[call(W,'decimals()'),call(W,'name()'),call(W,'symbol()')])
    put('wrapper-proxy-slots.json',{'slots':slots,'responses':results})
    print(json.dumps(results,indent=2))
