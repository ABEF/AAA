"""New v3-market diagnostics only; these are not admitted PoPL executors."""
from pathlib import Path
from fractions import Fraction
import argparse,hashlib,json,time
import transport_base as b

QUOTER='0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'
FACTORY='0x1f7d7550b1b028f7571e69a784071f0205fd2efa'
WETH='0x0bd7d308f8e1639fab988df18a8011f41eacad73'


def main():
    a=argparse.ArgumentParser();a.add_argument('state',type=Path);a.add_argument('native_state',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
    raw=args.state.read_bytes();prior=json.loads(raw);native_raw=args.native_state.read_bytes();native=json.loads(native_raw)
    assert prior['canonical_final_recheck'] is True and not prior.get('stopped') and prior['anchor']==native['anchor']
    args.output.mkdir(parents=True,exist_ok=False);b.OUT=args.output;c=b.Capture();h=prior['anchor'];c.block=dict(blockHash=h['hash'],requireCanonical=True)
    result=dict(schema=1,phase='v3-quotes',anchor=h,prior_capture_sha256=hashlib.sha256(raw).hexdigest(),native_capture_sha256=hashlib.sha256(native_raw).hexdigest(),quotes=[],production_approved=False,configuration_adopted=False,public_transactions=0,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        assert c.rpc('eth_getBlockByNumber',[hex(h['number']),False],'anchor-before')==h['header']
        code=c.rpc('eth_getCode',[QUOTER,c.block],'v3quoter.unqualified-runtime')
        result['quoter']=dict(address=QUOTER,bytes=(len(code)-2)//2,keccak256='0x'+b.keccak256(bytes.fromhex(code[2:])).hex(),independently_compiled_runtime_verified=False)
        result['quoter']['factory']=c.call(QUOTER,'factory()',label='v3quoter.factory')
        result['quoter']['WETH9']=c.call(QUOTER,'WETH9()',label='v3quoter.WETH9')
        assert b.vals(result['quoter']['factory'],1)[0]==int(FACTORY,16) and b.vals(result['quoter']['WETH9'],1)[0]==int(WETH,16)
        result['weth_decimals']=c.call(WETH,'decimals()',label='WETH.decimals')
        assert b.vals(result['weth_decimals'],1)[0]==18
        round_=b.vals(native['feeds']['chainlink_primary']['round'],5);dec=b.vals(native['feeds']['chainlink_primary']['decimals'],1)[0];eth=Fraction(round_[1],10**dec)
        for pool in prior['pools']:
            fee=pool['reported_fee']
            cases=[(WETH,b.ZZZ,int(Fraction(n*10**18,1)/eth),n) for n in (5,50)]+[(b.ZZZ,WETH,n*10**18,None) for n in (1,100,1000)]
            for token_in,token_out,amount,nominal in cases:
                args_=(token_in,token_out,amount,fee,0)
                data='0x'+(b.keccak256(b'quoteExactInputSingle((address,address,uint256,uint24,uint160))')[:4]+b''.join(b.word(v) for v in args_)).hex()
                value=c.call(QUOTER,'',data=data,label=pool['address']+'.'+token_in+'.'+str(amount),gas=500000)
                result['quotes'].append(dict(pool=pool['address'],fee_pips=fee,token_in=token_in,token_out=token_out,input_raw=str(amount),nominal_USD_from_single_ETH_round_only=nominal,result=value,gas_ceiling=500000,sqrt_price_limit_x96=0,complete_input_consumption_proved=False,complete_operation_qualified=False))
    except Exception as exc:
        result['stopped']=dict(exception_type=type(exc).__name__,reason=str(exc) if isinstance(exc,(AssertionError,ValueError,b.Stop)) else 'Transport failure; no retry',provider_stopped=c.stopped)
    finally:
        if not c.stopped:
            try:
                header=c.rpc('eth_getBlockByNumber',[hex(h['number']),False],'anchor-after',closure=True)
                result['canonical_final_recheck']=header==h['header'];result['final_header']=header
            except Exception as exc:result['closure_failure']=type(exc).__name__
        result['request_count']=len(c.rows);result['elapsed_seconds']=None if c.start is None else time.perf_counter()-c.start
        b.save('CAPTURE.json',result)
        print(json.dumps({k:result.get(k) for k in ['phase','request_count','elapsed_seconds','canonical_final_recheck','stopped']}))


if __name__=='__main__':main()
