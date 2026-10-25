from pathlib import Path
import json,subprocess,time,hashlib,difflib
R=Path.cwd();E=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9');B=E/'vault-headroom-20261025'
sources={p.relative_to(R).as_posix():{'content':p.read_bytes().decode('utf-8-sig')} for p in (R/'src').rglob('*.sol')};base=sources['src/ZZZVault.sol']['content']
def unwind(s):
 assert s.count('_unwind(id, deadline, true)')==2
 return s.replace('function _unwind(uint256 id, uint256 deadline, bool migrating)','function _unwind(uint256 id, uint256 deadline)').replace('if (migrating) _migrationCheckpoint(id, 1);','_migrationCheckpoint(id, 1);').replace('_unwind(id, deadline, true)','_unwind(id, deadline)')
def swap(s):
 a='''            address manager = _moduleLiquidity();
            ExactAsset.approve(input, manager, amountIn);
            uint256 amountOut = IZZZLiquidity(manager).swap{value: input == address(0) ? amountIn : 0}(p.poolId, zeroForOne, amountIn, minimumOut, deadline);
            ExactAsset.approve(input, manager, 0);'''
 b='''            uint256 amountOut = _swap(id, zeroForOne, input, amountIn, minimumOut, deadline);'''
 c='''            address manager = _moduleLiquidity();
            ExactAsset.approve(plan.input,manager,plan.amount);
            uint256 out = IZZZLiquidity(manager).swap{value: plan.input == address(0) ? plan.amount : 0}(
                p.poolId,plan.direction,plan.amount,plan.minimum,deadline);
            ExactAsset.approve(plan.input,manager,0);'''
 d='''            uint256 out = _swap(id,plan.direction,plan.input,plan.amount,plan.minimum,deadline);'''
 helper='''    function _swap(uint256 id,bool direction,address input,uint256 amount,uint256 minimum,uint256 deadline)
        private returns(uint256 output) {
        address manager = _moduleLiquidity();
        ExactAsset.approve(input,manager,amount);
        output = IZZZLiquidity(manager).swap{value:input == address(0) ? amount : 0}(
            positions[id].poolId,direction,amount,minimum,deadline);
        ExactAsset.approve(input,manager,0);
    }
'''
 assert a in s and c in s
 return s.replace(a,b).replace(c,d).replace('    function _balanceUsing(',helper+'    function _balanceUsing(')
def venue(s):
 start=s.index('    function _harvestVenue(');end=s.index('    function collectFees(',start)
 shared='''    function _venueDelta(uint256 id,uint256 deadline,bool closing)
        private returns(address token0,address token1,uint256 amount0,uint256 amount1) {
        Position storage p = positions[id];
        (token0,token1) = _tokens(id);
        uint256 before0 = _tokenBalance(token0);
        uint256 before1 = _tokenBalance(token1);
        uint256 received = nativeReceived;
        IZZZLiquidity manager = IZZZLiquidity(_moduleLiquidity());
        if (closing) manager.close(p.poolId,p.lpTokenId,deadline);
        else manager.collect(p.poolId,p.lpTokenId,deadline);
        amount0 = _tokenBalance(token0)-before0;
        amount1 = _tokenBalance(token1)-before1;
        if (token0 == address(0) && amount0 != nativeReceived-received) revert InvalidState();
    }
    function _harvestVenue(uint256 id, uint256 deadline) private {
        (address token0,address token1,uint256 fee0,uint256 fee1) = _venueDelta(id,deadline,false);
        _allocate(id,token0,fee0);
        _allocate(id,token1,fee1);
        emit FeesCollected(id,fee0,fee1);
    }
'''
 s=s[:start]+shared+s[end:];start=s.index('    function _close(');end=s.index('    function _balanceUsing(',start)
 replacement='''    function _close(uint256 id, uint256 deadline) private {
        Position storage p = positions[id];
        (,,uint256 closed0,uint256 closed1) = _venueDelta(id,deadline,true);
        p.lpTokenId = 0;
        _idle(id,p.idle0+closed0,p.idle1+closed1);
    }
'''
 return s[:start]+replacement+s[end:]
def finish(s):
 a='''        _redeploy(id, minimumLiquidity, deadline);
        _migrationCheckpoint(id, 2);
        emit Rebalanced(id, oldId, p.lpTokenId, p.centerX96);'''
 assert s.count(a)==2
 helper='''    function _finishRebalance(uint256 id,uint256 oldId,uint128 minimumLiquidity,uint256 deadline) private {
        _redeploy(id,minimumLiquidity,deadline);
        _migrationCheckpoint(id,2);
        Position storage p = positions[id];
        emit Rebalanced(id,oldId,p.lpTokenId,p.centerX96);
    }
'''
 return s.replace(a,'        _finishRebalance(id,oldId,minimumLiquidity,deadline);').replace('    function rebalance(',helper+'    function rebalance(')
def cache_put(s):
 start=s.index('    function _put(');end=s.index('    /// @notice Paid issuance',start)
 body=s[start:end];assert 'migrationBudget.' in body
 body=body.replace('        Position storage p = positions[id];','        ZZZMigrationBudget budget = migrationBudget;\n        Position storage p = positions[id];',1).replace('migrationBudget.','budget.')
 return s[:start]+body+s[end:]
def cache_join(s):
 start=s.index('    function _join(');end=s.index('    function _allocate(',start)
 body=s[start:end];assert 'migrationBudget.' in body
 body=body.replace('        Position storage p = positions[bucket];','        ZZZMigrationBudget budget = migrationBudget;\n        Position storage p = positions[bucket];',1).replace('migrationBudget.','budget.')
 return s[:start]+body+s[end:]
variants={'baseline':base,'cache_put':cache_put(base),'cache_join':cache_join(base),'cache_both':cache_join(cache_put(base)),'unwind_swap_cache':cache_join(cache_put(swap(unwind(base))))}
selection={}
for name,s in variants.items():
 contract='Vault_'+name;path='variants/'+contract+'.sol';s=s.replace('contract ZZZVault is','contract '+contract+' is').replace('"./','"../src/');sources[path]={'content':s};selection[path]={contract:['abi','storageLayout','evm.bytecode.object','evm.deployedBytecode.object']}
 (B/(name+'.sol')).write_text(s,encoding='utf-8',newline='\n')
settings={'evmVersion':'cancun','viaIR':True,'optimizer':{'enabled':True,'runs':1,'details':{'yul':False}},'remappings':['@openzeppelin/contracts/=node_modules/@openzeppelin/contracts/','@uniswap/v4-core/=node_modules/@uniswap/v4-core/','@uniswap/v4-periphery/=node_modules/@uniswap/v4-periphery/','forge-std/=lib/forge-std/src/','solmate/=node_modules/@uniswap/v4-core/lib/solmate/'],'outputSelection':selection}
t=time.monotonic();p=subprocess.run([str(E/'toolchain-0.8.26/solc.exe'),'--standard-json','--base-path',str(R)],input=json.dumps({'language':'Solidity','sources':sources,'settings':settings}).encode(),cwd=R,capture_output=True,timeout=1500)
raw=p.stdout[p.stdout.find(b'{'):];(B/'cache-compile.json').write_bytes(raw);x=json.loads(raw);errors=[a for a in x.get('errors',[]) if a['severity']=='error']
def layout(v):
 types=v['storageLayout']['types']
 def ty(key):
  a=types[key];return {k:(ty(z) if k in ('key','value','base') else [dict(label=m['label'],slot=m['slot'],offset=m['offset'],type=ty(m['type'])) for m in z] if k=='members' else z) for k,z in a.items() if k not in ('astId','contract')}
 return [dict(label=a['label'],slot=a['slot'],offset=a['offset'],type=ty(a['type'])) for a in v['storageLayout']['storage']]
results=[];baseline=None
for name in variants:
 path='variants/Vault_'+name+'.sol';v=x.get('contracts',{}).get(path,{}).get('Vault_'+name)
 if v is None:continue
 runtime=len(v['evm']['deployedBytecode']['object'])//2;creation=len(v['evm']['bytecode']['object'])//2
 if baseline is None:baseline=v
 results.append({'variant':name,'runtime':runtime,'runtime_margin':24576-runtime,'creation_with_96_args':creation+96,'creation_margin':49152-creation-96,'abi_equal':v['abi']==baseline['abi'],'storage_equal':layout(v)==layout(baseline),'runtime_saved':len(baseline['evm']['deployedBytecode']['object'])//2-runtime})
report={'elapsed_seconds':time.monotonic()-t,'errors':errors,'results':results,'settings':settings,'source_sha256':{k:hashlib.sha256(v['content'].encode()).hexdigest() for k,v in sources.items()},'scope':'External in-memory compiler experiments only. No repository production source edited, no deployment/execution or relaxed limits. Same ABI and normalized storage layout comparison, not semantic proof.'}
(B/'cache-summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in report.items() if k not in ('settings','source_sha256')},indent=2));assert not errors
