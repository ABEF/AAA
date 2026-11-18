// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
struct MarketState { uint160 sqrtPriceX96; int24 tick; uint24 protocolFee; uint24 lpFee; uint128 liquidity; }
abstract contract CodecBase {
    struct ExecutionMarket {
        address core; address stateView; bytes32 poolId;
        MarketState origin; bytes32 expected;
    }
    struct ExecutionVenue {
        address core; address stateView; bytes32 poolId; MarketState expected;
        bool omitLiquidity;
    }
    struct Execution {
        address owner; address zzz; bytes32 ethPolicy; bytes32 zzzPolicy;
        bytes32 sequencerPolicy; uint64 sourceRevision; bytes32 gasPolicy;
        bytes32[4] roundHashes; bytes32[2] fingerprints;
        uint256[4] bounds; uint8 zzzDigits;
        ExecutionMarket[2] markets;
        bool managerLoan; bool swapped; bool pendingSwap; bytes32 destination;
        ExecutionVenue venue;
    }

    error InvalidState();
    bytes32 internal constant EXECUTION_LENGTH=keccak256("ZZZ_ORACLE_EXECUTION_LENGTH_V1");
    bytes32 internal constant EXECUTION_WORDS=keccak256("ZZZ_ORACLE_EXECUTION_WORDS_V1");
    uint256 internal constant EXECUTION_BYTES=49*32;
    function _executionLength() internal view returns(uint256 length) {
        bytes32 slot=EXECUTION_LENGTH;
        assembly("memory-safe"){length:=tload(slot)}
        if(length!=0 && length!=EXECUTION_BYTES)revert InvalidState();
    }
    function _executionWord(uint256 index) internal view returns(uint256 word) {
        bytes32 base=EXECUTION_WORDS;
        assembly("memory-safe"){word:=tload(add(base,index))}
    }
    function _saveExecution(Execution memory c) internal {
        bytes memory encoded=abi.encode(c);uint256 length=encoded.length;
        if(length!=EXECUTION_BYTES)revert InvalidState();
        uint256 previous=_executionLength();bytes32 base=EXECUTION_WORDS;bytes32 slot=EXECUTION_LENGTH;
        assembly("memory-safe"){
            for{let i:=0}lt(i,length){i:=add(i,32)}{
                tstore(add(base,div(i,32)),mload(add(add(encoded,32),i)))
            }
            for{let i:=length}lt(i,previous){i:=add(i,32)}{tstore(add(base,div(i,32)),0)}
            tstore(slot,length)
        }
    }
    function _loadExecution() internal view virtual returns(Execution memory);
    function store(Execution calldata c) external {_saveExecution(c);}
    function readHash() external view returns(bytes32){return keccak256(abi.encode(_loadExecution()));}
}
contract OldCodec is CodecBase {
    function _loadExecution() internal view override returns(Execution memory c) {
        uint256 length=_executionLength();if(length==0)return c;
        bytes memory encoded=new bytes(length);bytes32 base=EXECUTION_WORDS;
        assembly("memory-safe"){
            for{let i:=0}lt(i,length){i:=add(i,32)}{
                mstore(add(add(encoded,32),i),tload(add(base,div(i,32))))
            }
        }
        c=abi.decode(encoded,(Execution));
    }
}
contract NewCodec is CodecBase {
    function _loadExecution() internal view override returns(Execution memory c) {
        if(_executionLength()==0)return c;
        c.owner=address(uint160(_executionWord(0)));c.zzz=address(uint160(_executionWord(1)));
        c.ethPolicy=bytes32(_executionWord(2));c.zzzPolicy=bytes32(_executionWord(3));
        c.sequencerPolicy=bytes32(_executionWord(4));c.sourceRevision=uint64(_executionWord(5));
        c.gasPolicy=bytes32(_executionWord(6));
        for(uint256 i;i<4;++i)c.roundHashes[i]=bytes32(_executionWord(7+i));
        for(uint256 i;i<2;++i)c.fingerprints[i]=bytes32(_executionWord(11+i));
        for(uint256 i;i<4;++i)c.bounds[i]=_executionWord(13+i);
        c.zzzDigits=uint8(_executionWord(17));
        for(uint256 i;i<2;++i){
            uint256 start=18+9*i;
            c.markets[i].core=address(uint160(_executionWord(start)));
            c.markets[i].stateView=address(uint160(_executionWord(start+1)));
            c.markets[i].poolId=bytes32(_executionWord(start+2));
            c.markets[i].origin=MarketState(uint160(_executionWord(start+3)),int24(int256(_executionWord(start+4))),
                uint24(_executionWord(start+5)),uint24(_executionWord(start+6)),uint128(_executionWord(start+7)));
            c.markets[i].expected=bytes32(_executionWord(start+8));
        }
        c.managerLoan=_executionWord(36)!=0;c.swapped=_executionWord(37)!=0;c.pendingSwap=_executionWord(38)!=0;
        c.destination=bytes32(_executionWord(39));
        c.venue.core=address(uint160(_executionWord(40)));c.venue.stateView=address(uint160(_executionWord(41)));
        c.venue.poolId=bytes32(_executionWord(42));
        c.venue.expected=MarketState(uint160(_executionWord(43)),int24(int256(_executionWord(44))),
            uint24(_executionWord(45)),uint24(_executionWord(46)),uint128(_executionWord(47)));
        c.venue.omitLiquidity=_executionWord(48)!=0;
    }
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
            c.markets[i].origin=MarketState(uint160(n),int24(int256(n)),uint24(n>>3),uint24(n>>5),uint128(n));
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
    function testNewCodecGasAtSameTypedRecord()external {
        CodecBase.Execution memory c=_data(type(uint256).max);old.store(c);fresh.store(c);
        uint256 a=gasleft();bytes32 original=old.readHash();a-=gasleft();
        uint256 b=gasleft();bytes32 candidate=fresh.readHash();b-=gasleft();
        require(original==candidate);emit CodecGas(a,b);
    }
}
