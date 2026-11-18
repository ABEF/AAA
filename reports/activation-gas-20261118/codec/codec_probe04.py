from pathlib import Path
import hashlib,json,os,re,subprocess,time
R=Path('C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
V=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
O=V/'activation-gas-20261118/codec04';O.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=(R/'src/ZZZOracle.sol').read_text(encoding='utf-8')
def function(name):
 start=source.index('    function '+name+'(');brace=source.index('{',start);end=brace+1;depth=1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]
structs=source[source.index('    struct ExecutionMarket'):source.index('    // Bounded ABI words')]
new='''    function _loadExecution() internal view returns(Execution memory c) {
        if(_executionLength()==0)return c;
        bytes32 base=EXECUTION_WORDS;
        // Only _saveExecution writes this canonical49-word typed encoding.
        // The compiler-allocated nested layout is checked by the codec regression.
        assembly ("memory-safe") {
            function words(dst,src,count,area) {
                for {let i:=0}lt(i,count){i:=add(i,1)} {
                    mstore(add(dst,mul(i,32)),tload(add(area,add(src,i))))
                }
            }
            words(c,0,7,base)
            words(mload(add(c,224)),7,4,base)
            words(mload(add(c,256)),11,2,base)
            words(mload(add(c,288)),13,4,base)
            mstore(add(c,320),tload(add(base,17)))
            let markets:=mload(add(c,352))
            for{let i:=0}lt(i,2){i:=add(i,1)}{
                let market:=mload(add(markets,mul(i,32)))
                let start:=add(18,mul(i,9))
                words(market,start,3,base)
                words(mload(add(market,96)),add(start,3),5,base)
                mstore(add(market,128),tload(add(base,add(start,8))))
            }
            words(add(c,384),36,4,base)
            let venue:=mload(add(c,512))
            words(venue,40,3,base)
            words(mload(add(venue,96)),43,5,base)
            mstore(add(venue,128),tload(add(base,48)))
        }
    }'''
(O/'CANDIDATE_FUNCTION.sol.txt').write_text(new,encoding='utf-8')
base='''// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
struct MarketState { uint160 sqrtPriceX96; int24 tick; uint24 protocolFee; uint24 lpFee; uint128 liquidity; }
abstract contract CodecBase {
'''+structs+'''
    error InvalidState();
    bytes32 private constant EXECUTION_LENGTH=keccak256("ZZZ_ORACLE_EXECUTION_LENGTH_V1");
    bytes32 private constant EXECUTION_WORDS=keccak256("ZZZ_ORACLE_EXECUTION_WORDS_V1");
    uint256 private constant EXECUTION_BYTES=49*32;
'''+function('_executionLength')+'\n'+function('_executionWord')+'\n'+function('_saveExecution')+'\n'+function('_clearExecution')+'''
    function _loadExecution() internal view virtual returns(Execution memory);
    function store(Execution calldata c) external {_saveExecution(c);}
    function clear() external {_clearExecution();}
    function testLength(uint256 n) external {bytes32 slot=EXECUTION_LENGTH;assembly{tstore(slot,n)}}
    function mutate() external {Execution memory c=_loadExecution();c.markets[0].origin.tick=type(int24).min;
        c.markets[1].origin.liquidity=type(uint128).max;c.pendingSwap=!c.pendingSwap;
        c.venue.expected.tick=type(int24).max;c.venue.omitLiquidity=!c.venue.omitLiquidity;_saveExecution(c);}
    function memorySentinels() external view returns(bytes32 h){bytes memory a=new bytes(129);for(uint256 i;i<a.length;++i)a[i]=bytes1(uint8(i));
        bytes32 beforeHash=keccak256(a);Execution memory c=_loadExecution();bytes memory b=new bytes(163);
        for(uint256 i;i<b.length;++i)b[i]=bytes1(uint8(i^99));require(keccak256(a)==beforeHash);
        h=keccak256(abi.encode(c));require(keccak256(b)!=0);}

    function readHash() external view returns(bytes32){return keccak256(abi.encode(_loadExecution()));}
}
contract OldCodec is CodecBase {
'''+function('_loadExecution').replace('private view','internal view override')+'''
}
contract NewCodec is CodecBase {
'''+new.replace('internal view returns','internal view override returns')+'''
}
contract CodecProbeTest {
    OldCodec old=new OldCodec();NewCodec fresh=new NewCodec();
    event CodecGas(uint256 oldGas,uint256 newGas);
    function _data(uint256 n)private pure returns(CodecBase.Execution memory c){
        c.owner=address(uint160(n|1));c.zzz=address(type(uint160).max);
        c.ethPolicy=keccak256(abi.encode(n));c.zzzPolicy=bytes32(n);c.sequencerPolicy=bytes32(~n);
        c.sourceRevision=uint64(n);c.gasPolicy=bytes32(n<<5);
        for(uint256 i;i<4;++i)c.roundHashes[i]=keccak256(abi.encode(n,i));
        for(uint256 i;i<2;++i)c.fingerprints[i]=keccak256(abi.encode(i,n));
        for(uint256 i;i<4;++i)c.bounds[i]=n^(1<<i);
        c.zzzDigits=uint8(n);
        for(uint256 i;i<2;++i){
            c.markets[i].core=address(uint160(n^i));c.markets[i].stateView=address(uint160(~(n^i)));
            c.markets[i].poolId=bytes32(n^i);c.markets[i].expected=bytes32(~(n^i));
            c.markets[i].origin=MarketState(uint160(n^i),i==0?type(int24).min:type(int24).max,uint24(n>>(3+i)),uint24(n>>(5+i)),uint128(n^i));
        }
        c.managerLoan=n&1!=0;c.swapped=n&2!=0;c.pendingSwap=n&4!=0;c.destination=bytes32(n<<8);
        c.venue.core=address(uint160(n>>2));c.venue.stateView=address(uint160(n>>4));c.venue.poolId=bytes32(n>>6);
        c.venue.expected=MarketState(uint160(~n),int24(int256(~n)),uint24(~n),uint24(n),uint128(~n));
        c.venue.omitLiquidity=n&8!=0;
    }
    function testNewCodecEmptyMatchesExistingZeroStruct()external view {require(old.readHash()==fresh.readHash());}
    function testNewCodecAllCanonicalBitsAndNestedRowsRoundTrip()external {
        for(uint256 i;i<24;++i){
            uint256 n=i==0?0:i==1?type(uint256).max:uint256(keccak256(abi.encode(i)));
            CodecBase.Execution memory c=_data(n);old.store(c);fresh.store(c);
            bytes32 expected=keccak256(abi.encode(c));require(old.readHash()==expected);require(fresh.readHash()==expected);
        }
    }
    function testNewCodecRejectsNonzeroWrongLengths()external {
        uint256[4] memory bad=[uint256(1),uint256(1567),uint256(1569),type(uint256).max];
        for(uint256 i;i<bad.length;++i){old.testLength(bad[i]);fresh.testLength(bad[i]);
            (bool a,bytes memory x)=address(old).staticcall(abi.encodeWithSelector(old.readHash.selector));
            (bool b,bytes memory y)=address(fresh).staticcall(abi.encodeWithSelector(fresh.readHash.selector));
            require(!a&&!b&&keccak256(x)==keccak256(y)&&x.length==4);}
    }
    function testNewCodecSaveClearMutateAndNewCapture()external {
        CodecBase.Execution memory c=_data(13);old.store(c);fresh.store(c);old.mutate();fresh.mutate();
        c.markets[0].origin.tick=type(int24).min;c.markets[1].origin.liquidity=type(uint128).max;
        c.pendingSwap=!c.pendingSwap;c.venue.expected.tick=type(int24).max;c.venue.omitLiquidity=!c.venue.omitLiquidity;
        require(old.readHash()==keccak256(abi.encode(c)));require(fresh.readHash()==old.readHash());
        old.clear();fresh.clear();CodecBase.Execution memory zero;require(old.readHash()==keccak256(abi.encode(zero)));
        require(fresh.readHash()==old.readHash());c=_data(0);old.store(c);fresh.store(c);require(fresh.readHash()==keccak256(abi.encode(c)));
    }
    function testNewCodecMemorySentinelsPreserved()external {
        CodecBase.Execution memory c=_data(type(uint256).max);old.store(c);fresh.store(c);
        require(old.memorySentinels()==keccak256(abi.encode(c)));require(fresh.memorySentinels()==old.memorySentinels());
    }
    function testNewCodecGasAtSameTypedRecord()external {
        CodecBase.Execution memory c=_data(type(uint256).max);old.store(c);fresh.store(c);
        uint256 a=gasleft();bytes32 original=old.readHash();a-=gasleft();
        uint256 b=gasleft();bytes32 candidate=fresh.readHash();b-=gasleft();
        require(original==candidate && b<a);emit CodecGas(a,b);
    }
}
'''
base=base.replace('private constant','internal constant').replace('private view','internal view').replace('private {','internal {').replace('private returns','internal returns')
(O/'test').mkdir();(O/'test/CodecProbe.t.sol').write_text(base,encoding='utf-8')
config='''[profile.default]
src = "src"
test = "test"
solc_version = "0.8.26"
evm_version = "cancun"
optimizer = true
optimizer_runs = 1
via_ir = true
optimizer_details = { yul = false }
gas_limit = 30000000
'''
(O/'foundry.toml').write_text(config,encoding='utf-8');(O/'src').mkdir()
forge=V/'foundry-v1.4.4/forge.exe';solc=V/'toolchain-0.8.26/solc.exe'
env={k:v for k,v in os.environ.items()if k.upper()in ['SYSTEMROOT','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT']};env['PATH']=str(solc.parent)+';C:/Windows/System32'
start=time.monotonic();before=sha(R/'src/ZZZOracle.sol')
with(O/'raw.json').open('xb')as out,(O/'stderr.log').open('xb')as err:
 p=subprocess.run([str(forge),'test','--root',str(O),'--offline','--use',str(solc),'--json','-vv','--match-test','testNewCodec(AllCanonical|GasAt|RejectsNonzero|SaveClear|MemorySentinels)'],env=env,stdout=out,stderr=err,timeout=150)
results=json.loads((O/'raw.json').read_bytes());rows=[]
for suite in results.values():
 for name,row in suite.get('test_results',{}).items():rows.append({'method':name,'status':row['status'],'logs':row.get('decoded_logs'), 'reason':row.get('reason')})
summary={'new_methods':rows,'seconds':time.monotonic()-start,'exit_code':p.returncode,'root_source_stable':before==sha(R/'src/ZZZOracle.sol'),'prototype_not_adopted':True,'root_config_untouched':True}
(O/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))
