"""NEW production Manager swap partition on a restored owned local fork."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,zipfile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import driver_base as B
from driver_base import *
PRIOR=V/'pool-lifecycle-20261120/run/attempt4'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    for name in ('run_swap.py','driver_base.py','warm_cache.py','supervise.py','SwapCallerFixture.sol'):(OUT/('source-'+name)).write_bytes((HERE/name).read_bytes())
    source=HERE/'SwapCallerFixture.sol'
    request={'language':'Solidity','sources':{'SwapCallerFixture.sol':{'content':source.read_text()}},'settings':{'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},'viaIR':True,'evmVersion':'cancun','outputSelection':{'*':{'*':['abi','evm.bytecode.object','evm.deployedBytecode.object']}}}}
    save('fixture-input.json',request)
    p=subprocess.run([str(SOLC),'--standard-json'],input=json.dumps(request).encode(),capture_output=True,timeout=60,env=toolenv(),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert p.returncode==0,p.stderr.decode();compiled=json.loads(p.stdout);assert not [e for e in compiled.get('errors',[])if e['severity']=='error']
    (OUT/'fixture-output.json').write_bytes(p.stdout)
    obj=compiled['contracts']['SwapCallerFixture.sol']['SwapCallerFixture']
    artifacts=Artifacts();artifacts.check_sources()
    archive=ROOT/'reports/pool-lifecycle-20261120/run/evidence.zip'
    assert sha(archive.read_bytes())=='ef4a40fe3e06d5502441c9808395dc10451e6f055ca6225dbc8e3e89cc511e0f'
    snapshot=(PRIOR/'owned-state.dump').read_bytes();capture=json.loads((PRIOR/'owned-state-capture.json').read_bytes())
    assert sha(snapshot)==capture['sha256']=='a4942af6bceff142b5c4b3e132dfbf024f051e082a639a11172a76265c0431de' and capture['no_pending']
    with zipfile.ZipFile(archive)as z:
        for filename in ('owned-state.dump','owned-state-capture.json','receipts.json'):
            assert z.read('attempt4/'+filename)==(PRIOR/filename).read_bytes(),filename
    receipts=json.loads((PRIOR/'receipts.json').read_bytes())
    deployed={r['label'][7:]:addr(r['receipt']['contractAddress'])for r in receipts if r['label'].startswith('deploy:') and r['receipt']['contractAddress']}
    control=deployed['MockAccess'];manager=deployed['ZZZLiquidityManager'];vault=deployed['PoolCustodyFixture'];balancer=deployed['ZZZLPBalancer'];strategy=deployed['ZZZStrategy']
    save('INPUT_PROVENANCE.json',{'prior_archive_sha256':sha(archive.read_bytes()),'snapshot_sha256':sha(snapshot),'snapshot_capture_sha256':sha((PRIOR/'owned-state-capture.json').read_bytes()),'prior_receipts_sha256':sha((PRIOR/'receipts.json').read_bytes()),'production_profile':artifacts.profile,'source_sha256':artifacts.source_pins,'source_contract_changed':False,'fixture_sha256':sha(source.read_bytes()),'fixture_compile_only':True,'addresses':deployed})
    try:
      with cached_fork_provider(PUBLIC_ENDPOINT,BLOCK,HASH,OUT/'relay',requests_per_second=.5)as relay:
       with Node(relay.url)as n:
        assert n.call('anvil_loadState',['0x'+snapshot.hex()]) is True
        for name,address in [('ZZZVault',vault),('ZZZLiquidityManager',manager),('ZZZStrategy',strategy)]:assert addr(n.read(control,'module(bytes32)',module(name)))==address
        restored=n.call('eth_getBlockByNumber',['latest',False]);save('RESTORED_HEAD.json',{'restored':restored,'expected':capture['block']})
        for key in ('number','hash','stateRoot','timestamp'):assert restored[key]==capture['block'][key],('restored header',key,restored[key],capture['block'][key])
        pending_before=n.call('eth_getBlockByNumber',['pending',False]);restored_time=int(restored['timestamp'],16)
        assert n.pending is None
        n.call('evm_setNextBlockTimestamp',[restored_time+1]);n.call('evm_mine',[])
        latest=n.call('eth_getBlockByNumber',['latest',False]);pending_after=n.call('eth_getBlockByNumber',['pending',False])
        assert int(latest['timestamp'],16)>=restored_time+1 and int(pending_after['timestamp'],16)>=int(latest['timestamp'],16)
        save('RESTORED_CLOCK.json',{'pending_before':pending_before,'owned_next_timestamp':restored_time+1,'latest_after':latest,'pending_after':pending_after,'new_owned_node_only':True})
        before_roles={name:addr(n.read(control,'module(bytes32)',module(name)))for name in ('ZZZVault','ZZZLiquidityManager','ZZZStrategy','ZZZOracle','ZZZPoolRegistry','ZZZRewards','ZZZBuyback')}
        assert int(n.read(STATE,'getLiquidity(bytes32)',POOL),16)==0
        n.call('anvil_impersonateAccount',[OWNER])
        caller=n.send('deploy:typed_swap_caller',None,'0x'+obj['evm']['bytecode']['object']+word(manager).hex())
        n.send('bind:test_buyback_only',control,abi('bind(bytes32,address)',module('ZZZBuyback'),caller))
        after_roles={name:addr(n.read(control,'module(bytes32)',module(name)))for name in before_roles}
        assert all(after_roles[name]==(caller if name=='ZZZBuyback'else before_roles[name])for name in before_roles)
        save('MOCK_BINDING.json',{'before':before_roles,'after':after_roles,'only_buyback_changed':True,'production_access_behavior':False})
        deadlines=[]
        def deadline():
            assert n.pending is None;n.call('evm_mine',[])
            head=n.call('eth_getBlockByNumber',['latest',False]);now=int(head['timestamp'],16);deadlines.append({'head':head['hash'],'timestamp':now,'deadline':now+300});return now+300
        # Previous setup/closure is REUSED; re-open solely as synthetic swap depth.
        ticks=words(n.read(strategy,'target(bytes32)',POOL));lower=ticks[0]-(1<<256)if ticks[0]>>255 else ticks[0];upper=ticks[1]-(1<<256)if ticks[1]>>255 else ticks[1]
        sqrt=words(n.read(STATE,'getSlot0(bytes32)',POOL))[0];a0=10**17;a1=a0*sqrt**2//(1<<192)*2
        id=int(n.read(POSM,'nextTokenId()'),16)
        n.send('setup:synthetic_depth_reopen',vault,abi('mint(bytes32,int24,int24,uint256,uint256,uint128,uint256)',POOL,lower,upper,a0,a1,1,deadline()),a0)
        L=int(n.read(POSM,'getPositionLiquidity(uint256)',id),16);assert L>0 and addr(n.read(POSM,'ownerOf(uint256)',id))==vault
        review='0x'+keccak256(b'ISOLATED SWAP PARTITION EXPLICIT MOCK CONTROL CORRELATED USD').hex()
        child=addr(n.read(manager,'positionOperator()'))
        def balances():
            return {'native':int(n.call('eth_getBalance',[caller,'latest']),16),'ZZZ':int(n.read(ZZZ,'balanceOf(address)',caller),16),'slot0':words(n.read(STATE,'getSlot0(bytes32)',POOL)),'pool_L':int(n.read(STATE,'getLiquidity(bytes32)',POOL),16),'manager_native':int(n.call('eth_getBalance',[manager,'latest']),16),'manager_ZZZ':int(n.read(ZZZ,'balanceOf(address)',manager),16),'allowance':int(n.read(ZZZ,'allowance(address,address)',caller,manager),16),'child_native':int(n.call('eth_getBalance',[child,'latest']),16),'child_ZZZ':int(n.read(ZZZ,'balanceOf(address)',child),16)}
        states=[];rows=[]
        def swap(label,direction,amount,minimum):
            d=deadline();before=balances();data=abi('swap(bytes32,bool,uint256,uint256,uint256)',POOL,direction,amount,minimum,d)
            simulated=n.call('eth_call',[{'from':OWNER,'to':caller,'data':data,'value':hex(amount if direction else 0),'gas':hex(24_000_000)},'latest'])
            expected=int(simulated,16);assert expected>=minimum>0
            n.send(label,caller,data,amount if direction else 0)
            after=balances();assert after['pool_L']==before['pool_L']
            assert after['native']==before['native']+(expected if not direction else 0)
            assert after['ZZZ']==before['ZZZ']+(expected if direction else -amount)
            for key in ('manager_native','manager_ZZZ','allowance','child_native','child_ZZZ'):assert after[key]==before[key]==0
            states.append({'label':label,'before':before,'after':after});rows.append({'label':label,'direction_native_to_ZZZ':direction,'input_raw':str(amount),'caller_minimum_raw':str(minimum),'simulated_output_raw':str(expected),'actual_output_delta':str(after['ZZZ']-before['ZZZ']if direction else after['native']-before['native'])})
            return expected
        received=swap('new:production_manager_native_to_ZZZ',True,10**12,1)
        # From actual earned forward output only, no artificial caller token funding.
        swap('new:production_manager_ZZZ_to_native',False,received//2,1)
        before=balances();data=abi('swap(bytes32,bool,uint256,uint256,uint256)',POOL,True,10**12,(1<<128)-1,deadline())
        rejected=n.call('eth_call',[{'from':OWNER,'to':caller,'data':data,'value':hex(10**12),'gas':hex(24_000_000)},'latest'],allow_error=True)
        assert rejected.get('error',{}).get('data')=='0x'+keccak256(b'Slippage()')[:4].hex(),rejected
        assert balances()==before
        save('CALLER_FLOOR_ROLLBACK.json',{'simulation_error':rejected,'before':before,'after':balances(),'exact_unchanged':True,'transaction_sent':False})
        n.send('cleanup:close_synthetic_depth',vault,abi('close(bytes32,uint256,uint256)',POOL,id,deadline()))
        assert int(n.read(STATE,'getLiquidity(bytes32)',POOL),16)==0
        for target in(manager,child):
            assert int(n.call('eth_getBalance',[target,'latest']),16)==0 and int(n.read(ZZZ,'balanceOf(address)',target),16)==0
            assert int(n.read(ZZZ,'allowance(address,address)',target,PERMIT2),16)==0
            assert words(n.read(PERMIT2,'allowance(address,address,address)',target,ZZZ,POSM))[0]==0
        artifacts.check_sources();save('receipts.json',n.receipts);save('deadlines.json',deadlines);save('SWAPS.json',rows);save('STATES.json',states)
        save('RESULT.json',{'successful':True,'both_production_manager_swap_directions':True,'router_actual_core_quote_and_guards':True,'actual_core_output':True,'caller_floor_rollback':True,'slot_and_liquidity_rollback':True,'manager_child_balances_allowances_zero':True,'MockAccess_BUYBACK_only_rebinding':True,'synthetic_L':str(L),'entry_NFT_accounting_tested':False,'independent_prices_qualified':False,'target_market_depth_qualified':False,'target_gas_fees_qualified':False,'production_approved':False})
      return 0
    except BaseException as exc:
      save('FAILED.json',{'class':type(exc).__name__,'reason':str(exc),'production_approved':False});raise
if __name__=='__main__':raise SystemExit(main())
