"""Inspect only the three newly discovered pools; no v3 adoption or signing."""
from pathlib import Path
import argparse,hashlib,json,time
import transport_base as b


def main():
    a=argparse.ArgumentParser();a.add_argument('discovery',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
    raw=args.discovery.read_bytes();prior=json.loads(raw)
    assert prior['canonical_final_recheck'] is True and not prior.get('stopped')
    args.output.mkdir(parents=True,exist_ok=False);b.OUT=args.output;c=b.Capture()
    h=prior['anchor'];c.block=dict(blockHash=h['hash'],requireCanonical=True)
    result=dict(schema=1,phase='v3-state',anchor=h,prior_capture_sha256=hashlib.sha256(raw).hexdigest(),pools=[],production_approved=False,configuration_adopted=False,public_transactions=0,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        assert c.rpc('eth_getBlockByNumber',[hex(h['number']),False],'anchor-before')==h['header']
        for lead in prior['factory_leads']:
            if lead['kind']!='v3' or isinstance(lead['result'],dict):continue
            value=b.vals(lead['result'],1)[0]
            if not value:continue
            assert value<1<<160
            address='0x'+f'{value:040x}'
            row=dict(address=address,reported_fee=lead['fee'],factory_lead=lead['factory'],qualified=False)
            result['pools'].append(row)
            code=c.rpc('eth_getCode',[address,c.block],address+'.runtime')
            row['runtime']=dict(bytes=(len(code)-2)//2,keccak256='0x'+b.keccak256(bytes.fromhex(code[2:])).hex())
            for signature in ('factory()','token0()','token1()','fee()','tickSpacing()','liquidity()','slot0()'):
                row[signature]=c.call(address,signature,label=address+'.'+signature)
            token0=b.vals(row['token0()'],1)[0];token1=b.vals(row['token1()'],1)[0]
            assert {token0,token1}=={int(b.ZZZ,16),int('0x0bd7d308f8e1639fab988df18a8011f41eacad73',16)}
            assert b.vals(row['factory()'],1)[0]==int(lead['factory'],16) and b.vals(row['fee()'],1)[0]==lead['fee']
            row['balances']={}
            for token in (token0,token1):
                target='0x'+f'{token:040x}'
                row['balances'][target]=c.call(target,'balanceOf(address)',(address,),label=address+'.balance.'+target)
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
