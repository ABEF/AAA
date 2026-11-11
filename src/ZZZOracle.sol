// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {IPriceFeed} from "./interfaces/IZZZ.sol";
import {ZZZContributionPricing} from "./ZZZContributionPricing.sol";
import {ZZZPriceMath} from "./libraries/ZZZPriceMath.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {MarketState,IZZZExecutionSpotSource} from "./interfaces/IZZZExecutionOracle.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";

interface IExecutionFixedZZZ { function fixedZZZ() external view returns(address); }
interface IExecutionManagerIdentity {
    function poolManager() external view returns(address);
    function stateView() external view returns(address);
    function executionStrategy() external view returns(address);
}

/// @notice Two-source USD consensus. Source independence is a reviewed governance
/// assertion, not something two addresses or two matching answers can prove.
contract ZZZOracle is ZZZModule {
    ZZZContributionPricing public immutable contributionPricing;
    uint256 public constant PRICING_VERSION = 2;
    uint256 public constant EXECUTION_PRICE_VERSION = 1;
    uint16 public constant MAX_DEVIATION_BPS = 500;
    bytes32 public constant FINGERPRINT_DOMAIN = keccak256("ZZZ_DUAL_USD_V2");
    struct SourcePolicy {
        address source;
        bytes32 expectedCodeHash;
        bytes32 independenceId;
        uint32 maxAge;
        uint8 feedDecimals;
    }
    struct DualPolicy {
        address token;
        SourcePolicy primary;
        SourcePolicy secondary;
        uint16 maxDeviationBps;
        uint8 assetDecimals;
        bytes32 reviewHash;
    }
    struct Round {
        uint80 round;
        int256 answer;
        uint256 startedAt;
        uint256 updatedAt;
        uint80 answeredInRound;
    }
    mapping(bytes32 => DualPolicy) private policies;
    mapping(address => bytes32) public activePolicy;
    bytes32[] private history;
    struct ExecutionSourcePolicy { bool enabled; bytes32 codeHash; bytes32 reviewHash; }
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
    // Bounded ABI words in a domain-separated transient area. No ordinary
    // Oracle read consults this area; every successful owner-end clears it all.
    bytes32 private constant EXECUTION_LENGTH=keccak256("ZZZ_ORACLE_EXECUTION_LENGTH_V1");
    bytes32 private constant EXECUTION_WORDS=keccak256("ZZZ_ORACLE_EXECUTION_WORDS_V1");
    // V1's entirely static abi.encode(Execution) is exactly 49 ABI words.
    // These are ABI offsets, never Solidity's internal memory layout. Only
    // _saveExecution writes them, from the compiler's canonical typed encoder.
    uint256 private constant EXECUTION_BYTES=49*32;
    uint256 private constant QUOTE_FINGERPRINT_WORD=11;
    uint256 private constant QUOTE_BOUNDS_WORD=13;
    uint256 private constant QUOTE_DIGITS_WORD=17;
    uint256 private constant QUOTE_PENDING_WORD=38;
    struct SequencerPolicy { address source; bytes32 expectedCodeHash; bytes32 reviewHash; bool bootstrapAdmission; }
    // The getter ABI is unchanged. Only governed, reviewed nonzero replacements
    // are possible; configuration never removes an existing uptime safeguard.
    address public sequencerFeed;
    mapping(bytes32 => SequencerPolicy) public sequencerPolicies;
    bytes32 public activeSequencerPolicy;
    bytes32[] private sequencerHistory;
    mapping(address=>ExecutionSourcePolicy) public executionSourcePolicies;
    uint64 public executionSourceRevision;
    uint256 public constant SEQUENCER_GRACE = 1 hours;
    event DualPolicyRecorded(bytes32 indexed id, address indexed token, address indexed primary,
        address secondary, bytes32 primaryIndependenceId, bytes32 secondaryIndependenceId,
        uint16 maxDeviationBps, bytes32 reviewHash);
    event DualPolicyActivated(address indexed token, bytes32 indexed previousPolicy, bytes32 indexed activePolicy);
    event SequencerPolicyRecorded(bytes32 indexed id, address indexed source, bytes32 expectedCodeHash,
        bytes32 reviewHash, bool bootstrapAdmission);
    event SequencerPolicyActivated(bytes32 indexed previousPolicy, bytes32 indexed activePolicy);
    event ExecutionSourceConfigured(address indexed source,bool enabled,bytes32 expectedCodeHash,bytes32 reviewHash,uint64 revision);
    error InvalidPrice(address token);
    constructor(address controller, address sequencer) ZZZModule(controller) {
        contributionPricing = new ZZZContributionPricing(controller,address(this));
        if (sequencer != address(0)) {
            bytes32 codeHash = sequencer.codehash;
            _sequencerData(sequencer, codeHash);
            // A deployment admission reference is provenance, not an independent
            // review. Production qualification must separately review this pin.
            bytes32 admissionReference = keccak256(abi.encode("ZZZ_SEQUENCER_BOOTSTRAP_V1", sequencer, codeHash));
            _recordSequencer(SequencerPolicy(sequencer, codeHash, admissionReference, true));
        }
    }
    function sequencerPolicyCount() external view returns (uint256) { return sequencerHistory.length; }
    function sequencerPolicyAt(uint256 ordinal) external view returns (bytes32) { return sequencerHistory[ordinal]; }
    /// @notice Replace a failed/deprecated uptime dependency through the existing
    /// governance authority after sealing. Never query the old dependency here.
    /// A down or recovering new feed remains unusable for price reads until up
    /// and beyond the mandatory grace period; review does not waive that guard.
    function setSequencerFeed(address source, bytes32 expectedCodeHash, bytes32 reviewHash)
        external onlyGovernance returns (bytes32 id) {
        if (source == address(0) || reviewHash == bytes32(0)) revert InvalidConfiguration();
        _sequencerData(source, expectedCodeHash);
        return _recordSequencer(SequencerPolicy(source, expectedCodeHash, reviewHash, false));
    }
    function _recordSequencer(SequencerPolicy memory entry) private returns (bytes32 id) {
        bytes32 previous = activeSequencerPolicy;
        id = keccak256(abi.encode(address(this), sequencerHistory.length, entry));
        sequencerPolicies[id] = entry;
        sequencerHistory.push(id);
        activeSequencerPolicy = id;
        sequencerFeed = entry.source;
        emit SequencerPolicyRecorded(id, entry.source, entry.expectedCodeHash, entry.reviewHash,
            entry.bootstrapAdmission);
        emit SequencerPolicyActivated(previous, id);
    }
    function _sequencerData(address source, bytes32 expectedCodeHash) private view
        returns (int256 answer, uint256 startedAt) {
        if (source.code.length == 0 || expectedCodeHash == bytes32(0) || source.codehash != expectedCodeHash ||
            _decimals(source, source) != 0) revert InvalidConfiguration();
        uint256 round; uint256 answeredRound; uint256 updated;
        (round, answer, startedAt, updated, answeredRound) = abi.decode(
            _boundedRead(source, IPriceFeed.latestRoundData.selector, 160, source),
            (uint256, int256, uint256, uint256, uint256));
        if (round == 0 || round > type(uint80).max || answeredRound > type(uint80).max ||
            answeredRound < round || (answer != 0 && answer != 1) || startedAt == 0 ||
            startedAt > block.timestamp || updated < startedAt || updated > block.timestamp) revert InvalidPrice(source);
        // Uptime feeds report status transitions, not periodic price rounds. A
        // healthy unchanged status must not expire based on updatedAt age.
    }
    function policyCount() external view returns (uint256) { return history.length; }
    function policyAt(uint256 ordinal) external view returns (bytes32) { return history[ordinal]; }
    function policy(bytes32 id) external view returns (DualPolicy memory) { return policies[id]; }
    /// @notice Append and activate a reviewed, two-source policy. No stale-price,
    /// single-source, target-pool or presumed stable-peg fallback is available.
    /// Zero spread permits exact agreement only; 500bps is a hard safety ceiling,
    /// not a production recommendation. A particular asset needs reviewed bounds.
    function setDualFeed(address token, SourcePolicy calldata primary, SourcePolicy calldata secondary,
        uint16 maxDeviationBps, bytes32 reviewHash) external onlyGovernance returns (bytes32 id) {
        if (reviewHash == bytes32(0) || maxDeviationBps > MAX_DEVIATION_BPS ||
            primary.source == secondary.source || primary.independenceId == bytes32(0) ||
            primary.independenceId == secondary.independenceId || secondary.independenceId == bytes32(0)) {
            revert InvalidConfiguration();
        }
        uint8 assetDecimals = token == address(0) ? 18 : _decimals(token, token);
        if (assetDecimals > 18) revert InvalidConfiguration();
        DualPolicy memory next = DualPolicy(token, primary, secondary, maxDeviationBps, assetDecimals, reviewHash);
        // Reject an invalid current observation at admission too. Static source
        // calls cannot mutate the policy or its authority during these checks.
        // _round also validates each source policy: do not repeat those calls.
        _readBounds(next);
        bytes32 previous = activePolicy[token];
        id = keccak256(abi.encode(address(this), history.length, next));
        policies[id] = next;
        history.push(id);
        activePolicy[token] = id;
        emit DualPolicyRecorded(id, token, primary.source, secondary.source, primary.independenceId,
            secondary.independenceId, maxDeviationBps, reviewHash);
        emit DualPolicyActivated(token, previous, id);
    }
    function _boundedRead(address source, bytes4 selector, uint256 expectedLength, address token)
        private view returns (bytes memory result) {
        bool success;uint256 returned;
        uint256 gasLimit=IZZZProtocolPolicy(access.protocolPolicy()).sourceCallGas();
        // Copy only the exact bounded result, never arbitrary return/revert data.
        assembly("memory-safe"){
            let input:=mload(0x40)
            mstore(input,selector)
            success:=staticcall(gasLimit,source,input,4,0,0)
            returned:=returndatasize()
        }
        if(!success || returned!=expectedLength)revert InvalidPrice(token);
        result=new bytes(expectedLength);
        assembly("memory-safe"){returndatacopy(add(result,32),0,expectedLength)}
    }
    function _decimals(address source, address token) private view returns (uint8 digits) {
        if (source.code.length == 0) revert InvalidConfiguration();
        uint256 decoded = abi.decode(_boundedRead(source, IPriceFeed.decimals.selector, 32, token), (uint256));
        if (decoded > 18) revert InvalidConfiguration();
        digits = uint8(decoded);
    }
    function _validateSource(SourcePolicy memory source, address token) private view {
        if (source.source.code.length == 0 || source.expectedCodeHash == bytes32(0) ||
            source.source.codehash != source.expectedCodeHash || source.maxAge == 0 || source.maxAge > 1 days ||
            source.feedDecimals > 18 || _decimals(source.source, token) != source.feedDecimals) {
            revert InvalidConfiguration();
        }
    }
    function _round(SourcePolicy memory source, address token) private view returns (Round memory r, uint256 usd) {
        _validateSource(source, token);
        bytes memory encoded = _boundedRead(source.source, IPriceFeed.latestRoundData.selector, 160, token);
        return _decodeRound(encoded,0,source,token);
    }
    /// @dev The exact same wide-word validation serves ordinary feed responses
    /// and the final five words of a registered reader's bounded proof. No
    /// separately fetched/latest round can diverge from that proof's ETH read.
    function _decodeRound(bytes memory encoded,uint256 offset,SourcePolicy memory source,address token)
        private view returns(Round memory r,uint256 usd) {
        if(offset>encoded.length || encoded.length-offset!=160)revert InvalidPrice(token);
        // Decode wide words first so noncanonical narrow integers produce the
        // same bounded domain error as other malformed source responses.
        uint256 round;int256 answer;uint256 started;uint256 updated;uint256 answered;
        assembly("memory-safe"){
            let data:=add(add(encoded,32),offset)
            round:=mload(data)
            answer:=mload(add(data,32))
            started:=mload(add(data,64))
            updated:=mload(add(data,96))
            answered:=mload(add(data,128))
        }
        if (round == 0 || round > type(uint80).max || answered > type(uint80).max || answered < round ||
            answer <= 0 || started == 0 || started > updated || updated == 0 || updated > block.timestamp ||
            block.timestamp - updated > source.maxAge) revert InvalidPrice(token);
        uint256 scale = 10 ** (18 - source.feedDecimals);
        if (uint256(answer) > 1e36 / scale) revert InvalidPrice(token);
        usd = uint256(answer) * scale;
        r = Round(uint80(round), answer, started, updated, uint80(answered));
    }
    function _readBounds(DualPolicy memory p)
        private view returns (uint256 lower, uint256 upper, Round memory first, Round memory second) {
        uint256 a;
        uint256 b;
        (first, a) = _round(p.primary, p.token);
        (second, b) = _round(p.secondary, p.token);
        (lower,upper)=_agreedBounds(a,b,p.maxDeviationBps,p.token);
    }
    function _agreedBounds(uint256 a,uint256 b,uint16 maximumDeviation,address token)
        private pure returns(uint256 lower,uint256 upper) {
        lower=Math.min(a,b);upper=Math.max(a,b);
        // The denominator is the lower price. Rounding cannot admit a spread
        // one raw unit above the configured tolerance.
        if(upper-lower>Math.mulDiv(lower,maximumDeviation,10000))revert InvalidPrice(token);
    }
    function _sequencerCheck() private view {
        if (sequencerFeed == address(0)) return;
        SequencerPolicy memory entry = sequencerPolicies[activeSequencerPolicy];
        (int256 answer, uint256 startedAt) = _sequencerData(sequencerFeed, entry.expectedCodeHash);
        if (answer != 0 || block.timestamp - startedAt <= SEQUENCER_GRACE) revert InvalidPrice(sequencerFeed);
    }
    function priceBounds(address token) public view returns (uint256 lower, uint256 upper, bytes32 fingerprint) {
        _sequencerCheck();
        bytes32 id = activePolicy[token];
        if (id == bytes32(0)) revert InvalidPrice(token);
        DualPolicy memory p = policies[id];
        if (token != address(0) && _decimals(token, token) != p.assetDecimals) revert InvalidConfiguration();
        Round memory first;
        Round memory second;
        (lower, upper, first, second) = _readBounds(p);
        fingerprint = keccak256(abi.encode(FINGERPRINT_DOMAIN, block.chainid, address(this), id,
            activeSequencerPolicy, first, second));
    }
    /// @notice Lower bound for minimum-contribution and ordinary display values.
    function price(address token) public view returns (uint256 normalizedUSD) {
        (normalizedUSD,,) = priceBounds(token);
    }
    function tokenDecimals(address token) public view returns (uint8) {
        bytes32 id = activePolicy[token];
        if (id == bytes32(0)) revert InvalidPrice(token);
        return policies[id].assetDecimals;
    }
    function value(address token, uint256 amount) public view returns (uint256) {
        return Math.mulDiv(amount, price(token), 10 ** tokenDecimals(token));
    }
    function quote(address input, address output, uint256 amount) external view returns (uint256) {
        (, uint256 upper,) = priceBounds(input);
        if (input == output) return amount;
        (uint256 lower,,) = priceBounds(output);
        uint256 sourceUSD = Math.mulDiv(amount, upper, 10 ** tokenDecimals(input));
        return Math.mulDiv(sourceUSD, 10 ** tokenDecimals(output), lower);
    }
    function referenceX96(address token0, address token1) external view returns (uint160) {
        return ZZZPriceMath.referenceX96(price(token0),price(token1),
            tokenDecimals(token0),tokenDecimals(token1),token0);
    }

    /// @notice Opt in only an already admitted fixed-ZZZ composite source.
    /// Disabling does not query a broken dependency. Every edit invalidates an
    /// in-flight context, including disabling and restoring identical settings.
    function setExecutionSource(address source,bool enabled,bytes32 expectedCodeHash,bytes32 reviewHash)
        external onlyGovernance {
        if(source==address(0) || reviewHash==bytes32(0))revert InvalidConfiguration();
        if(enabled) {
            address zzz=_fixedZZZ();DualPolicy memory p=policies[activePolicy[zzz]];
            if(expectedCodeHash==bytes32(0) || source.codehash!=expectedCodeHash ||
                !((p.primary.source==source && p.primary.expectedCodeHash==expectedCodeHash) ||
                  (p.secondary.source==source && p.secondary.expectedCodeHash==expectedCodeHash)))revert InvalidConfiguration();
            _readBounds(p);
            if(abi.decode(_boundedRead(source,IZZZExecutionSpotSource.EXECUTION_SOURCE_VERSION.selector,32,zzz),(uint256))!=1 ||
                abi.decode(_boundedRead(source,IZZZExecutionSpotSource.executionAsset.selector,32,zzz),(address))!=zzz)
                revert InvalidConfiguration();
            _sourceMarket(source,zzz);
        }
        executionSourcePolicies[source]=ExecutionSourcePolicy(enabled,expectedCodeHash,reviewHash);
        ++executionSourceRevision;
        emit ExecutionSourceConfigured(source,enabled,expectedCodeHash,reviewHash,executionSourceRevision);
    }
    function _fixedZZZ() private view returns(address zzz) {
        return IExecutionFixedZZZ(IExecutionManagerIdentity(access.module(Ids.LIQUIDITY)).executionStrategy()).fixedZZZ();
    }
    function _executionLength() private view returns(uint256 length) {
        bytes32 slot=EXECUTION_LENGTH;
        assembly("memory-safe"){length:=tload(slot)}
        if(length!=0 && length!=EXECUTION_BYTES)revert InvalidState();
    }
    function executionActive() external view returns(bool){return _executionLength()!=0;}
    function _loadExecution() private view returns(Execution memory c) {
        uint256 length=_executionLength();if(length==0)return c;
        bytes memory encoded=new bytes(length);bytes32 base=EXECUTION_WORDS;
        assembly("memory-safe"){
            for{let i:=0}lt(i,length){i:=add(i,32)}{
                mstore(add(add(encoded,32),i),tload(add(base,div(i,32))))
            }
        }
        c=abi.decode(encoded,(Execution));
    }
    function _executionWord(uint256 index) private view returns(uint256 word) {
        bytes32 base=EXECUTION_WORDS;
        assembly("memory-safe"){word:=tload(add(base,index))}
    }
    /// @dev Quote getters need just the seven control words, original vector,
    /// decimals and pending flag. Full mutable-boundary proof still decodes all
    /// 49 words. No cached value grants authority or replaces a live public read.
    function _loadQuote() private view returns(Execution memory c) {
        if(_executionLength()==0)return c;
        c.owner=address(uint160(_executionWord(0)));c.zzz=address(uint160(_executionWord(1)));
        c.ethPolicy=bytes32(_executionWord(2));c.zzzPolicy=bytes32(_executionWord(3));
        c.sequencerPolicy=bytes32(_executionWord(4));c.sourceRevision=uint64(_executionWord(5));
        c.gasPolicy=bytes32(_executionWord(6));
        for(uint256 i;i<2;++i)c.fingerprints[i]=bytes32(_executionWord(QUOTE_FINGERPRINT_WORD+i));
        for(uint256 i;i<4;++i)c.bounds[i]=_executionWord(QUOTE_BOUNDS_WORD+i);
        c.zzzDigits=uint8(_executionWord(QUOTE_DIGITS_WORD));
        c.pendingSwap=_executionWord(QUOTE_PENDING_WORD)!=0;
    }
    function _saveExecution(Execution memory c) private {
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
    function _clearExecution() private {
        uint256 length=_executionLength();bytes32 base=EXECUTION_WORDS;bytes32 slot=EXECUTION_LENGTH;
        assembly("memory-safe"){
            for{let i:=0}lt(i,length){i:=add(i,32)}{tstore(add(base,div(i,32)),0)}
            tstore(slot,0)
        }
    }
    function _executionCaller(bool pricing) private view {
        if(access.module(Ids.ORACLE)!=address(this) ||
            msg.sender!=(pricing?address(contributionPricing):access.module(Ids.LIQUIDITY)))revert Unauthorized();
    }
    function _executionControls(Execution memory c) private view {
        if(c.owner==address(0) || !access.isSealed() || access.canonicalState()!=0 || access.preparationActive() ||
            access.module(Ids.ORACLE)!=address(this) || activePolicy[address(0)]!=c.ethPolicy ||
            activePolicy[c.zzz]!=c.zzzPolicy || activeSequencerPolicy!=c.sequencerPolicy ||
            executionSourceRevision!=c.sourceRevision ||
            IZZZProtocolPolicy(access.protocolPolicy()).gasFingerprint()!=c.gasPolicy)revert InvalidState();
    }
    function _captureExecution(address zzz,address owner) private view returns(Execution memory c) {
        if(_executionLength()!=0 || zzz!=_fixedZZZ())revert InvalidState();
        c.owner=owner;c.zzz=zzz;c.ethPolicy=activePolicy[address(0)];c.zzzPolicy=activePolicy[zzz];
        c.sequencerPolicy=activeSequencerPolicy;c.sourceRevision=executionSourceRevision;
        c.gasPolicy=IZZZProtocolPolicy(access.protocolPolicy()).gasFingerprint();
        _executionControls(c);_sequencerCheck();
        if(c.ethPolicy==bytes32(0) || c.zzzPolicy==bytes32(0))revert InvalidState();
        DualPolicy memory eth=policies[c.ethPolicy];DualPolicy memory token=policies[c.zzzPolicy];
        if(eth.assetDecimals!=18 || _decimals(zzz,zzz)!=token.assetDecimals)revert InvalidConfiguration();
        c.zzzDigits=token.assetDecimals;
        Round memory a;Round memory b;Round memory d;Round memory e;
        (c.bounds[0],c.bounds[1],a,b)=_readBounds(eth);
        (c.bounds[2],c.bounds[3],d,e)=_readBounds(token);
        c.roundHashes=[_roundHash(a),_roundHash(b),_roundHash(d),_roundHash(e)];
        c.fingerprints[0]=keccak256(abi.encode(FINGERPRINT_DOMAIN,block.chainid,address(this),c.ethPolicy,c.sequencerPolicy,a,b));
        c.fingerprints[1]=keccak256(abi.encode(FINGERPRINT_DOMAIN,block.chainid,address(this),c.zzzPolicy,c.sequencerPolicy,d,e));
        c.markets[0]=_captureMarket(token.primary,c.roundHashes[2],zzz);
        c.markets[1]=_captureMarket(token.secondary,c.roundHashes[3],zzz);
        if(c.markets[0].poolId!=bytes32(0) && c.markets[0].core==c.markets[1].core &&
            c.markets[0].poolId==c.markets[1].poolId)revert InvalidConfiguration();
    }
    function _sourceMarket(address source,address token) private view
        returns(address core,address stateView,bytes32 poolId,MarketState memory state) {
        (core,stateView,poolId,state)=abi.decode(_boundedRead(source,
            IZZZExecutionSpotSource.executionMarket.selector,256,token),(address,address,bytes32,MarketState));
        if(core.code.length==0 || stateView.code.length==0 || poolId==bytes32(0))revert InvalidConfiguration();
    }
    function _captureMarket(SourcePolicy memory source,bytes32 roundHash,address zzz)
        private view returns(ExecutionMarket memory m) {
        ExecutionSourcePolicy memory policy_=executionSourcePolicies[source.source];
        if(!policy_.enabled)return m;
        if(policy_.codeHash!=source.expectedCodeHash || source.feedDecimals!=18 ||
            abi.decode(_boundedRead(source.source,IZZZExecutionSpotSource.EXECUTION_SOURCE_VERSION.selector,32,zzz),(uint256))!=1 ||
            abi.decode(_boundedRead(source.source,IZZZExecutionSpotSource.executionAsset.selector,32,zzz),(address))!=zzz)
            revert InvalidConfiguration();
        (m.core,m.stateView,m.poolId,m.origin)=_sourceMarket(source.source,zzz);
        m.expected=_marketHash(m.origin);
        bytes memory proof=_marketProof(source.source,m,roundHash,zzz);
        (Round memory current,)=_decodeRound(proof,160,source,zzz);
        if(_roundHash(current)!=roundHash)revert InvalidState();
    }
    function _boundedExecutionRead(address source,bytes memory input,uint256 expected,address token)
        private view returns(bytes memory result) {
        bool ok;uint256 returned;uint256 limit=IZZZProtocolPolicy(access.protocolPolicy()).sourceCallGas();
        assembly("memory-safe"){
            ok:=staticcall(limit,source,add(input,32),mload(input),0,0)
            returned:=returndatasize()
        }
        if(!ok || returned!=expected)revert InvalidPrice(token);
        result=new bytes(expected);
        assembly("memory-safe"){returndatacopy(add(result,32),0,expected)}
    }
    function _roundHash(Round memory round) private pure returns(bytes32){return keccak256(abi.encode(round));}
    function _marketHash(MarketState memory state) private pure returns(bytes32){return keccak256(abi.encode(state));}
    function _spotHash(MarketState memory state) private pure returns(bytes32){
        return keccak256(abi.encode(state.sqrtPriceX96,state.tick,state.protocolFee,state.lpFee));
    }
    function _executionRound(SourcePolicy memory source,bytes32 original,ExecutionMarket memory market,address token)
        private view returns(uint256 usd) {
        if(market.poolId==bytes32(0)) {
            Round memory current;(current,usd)=_round(source,token);
            if(original!=_roundHash(current))revert InvalidState();
            return usd;
        }
        _validateSource(source,token);
        bytes memory proof=_marketProof(source.source,market,original,token);
        (,usd)=_decodeRound(proof,160,source,token);
    }
    function _marketProof(address source,ExecutionMarket memory market,bytes32 original,address token)
        private view returns(bytes memory proof) {
        proof=_boundedExecutionRead(source,abi.encodeWithSelector(IZZZExecutionSpotSource.executionProof.selector,market.origin),320,token);
        (address core,address stateView,bytes32 poolId,bytes32 observed,bytes32 roundHash)=abi.decode(
            proof,(address,address,bytes32,bytes32,bytes32));
        if(core!=market.core || stateView!=market.stateView || poolId!=market.poolId ||
            observed!=market.expected || roundHash!=original)revert InvalidState();
    }
    function _validateExecution(Execution memory c) private view {
        _executionControls(c);if(c.pendingSwap)revert InvalidState();_sequencerCheck();
        DualPolicy memory eth=policies[c.ethPolicy];DualPolicy memory zzz=policies[c.zzzPolicy];
        if(_decimals(c.zzz,c.zzz)!=c.zzzDigits)revert InvalidConfiguration();
        // Current freshness AND agreement still apply. Their changed values do
        // not replace the starting financial vector returned by executionBounds.
        (,,Round memory a,Round memory b)=_readBounds(eth);
        if(_roundHash(a)!=c.roundHashes[0] || _roundHash(b)!=c.roundHashes[1])revert InvalidState();
        uint256 first=_executionRound(zzz.primary,c.roundHashes[2],c.markets[0],c.zzz);
        uint256 second=_executionRound(zzz.secondary,c.roundHashes[3],c.markets[1],c.zzz);
        _agreedBounds(first,second,zzz.maxDeviationBps,c.zzz);
        if(c.venue.poolId!=bytes32(0)) {
            MarketState memory actual=_readMarket(c.venue.stateView,c.venue.poolId);
            if(c.venue.omitLiquidity?_spotHash(actual)!=_spotHash(c.venue.expected):
                _marketHash(actual)!=_marketHash(c.venue.expected))revert InvalidState();
        }
    }
    /// @notice Full market/source proof at an execution boundary. Explicit
    /// captured-value getters perform only controls/pending checks so a chain
    /// of read-only calculations does not repeatedly fetch the same sources.
    /// Callers must validate before and after each mutable external boundary.
    function validateExecution() external view {
        Execution memory c=_loadExecution();if(c.owner!=address(0))_validateExecution(c);
    }
    /// @notice Whole-entry/maintenance scope, begun before external movement.
    function beginExecution(address zzz) external {
        _executionCaller(true);_saveExecution(_captureExecution(zzz,msg.sender));
    }
    function endExecution() external {
        _executionCaller(true);Execution memory c=_loadExecution();
        if(c.owner!=msg.sender || c.managerLoan)revert InvalidState();
        _validateExecution(c);_clearExecution();
    }
    /// @notice A zero destination denotes standalone swapping, never LP mint.
    /// Borrowing is accepted only from Manager's explicit Vault branch.
    function beginManagerExecution(address zzz,bytes32 destination,bool borrowVault) external returns(bool owned) {
        _executionCaller(false);Execution memory c=_loadExecution();
        if(c.owner==address(0)){c=_captureExecution(zzz,msg.sender);owned=true;}
        else {
            if(!borrowVault || c.owner!=address(contributionPricing) || c.managerLoan || c.zzz!=zzz)revert InvalidState();
            _validateExecution(c);
        }
        if(destination!=bytes32(0)) {
            if(c.destination!=bytes32(0) && c.destination!=destination)revert InvalidState();
            address core=IExecutionManagerIdentity(msg.sender).poolManager();
            for(uint256 i;i<2;++i)if(c.markets[i].poolId==destination && c.markets[i].core==core)revert InvalidConfiguration();
            c.destination=destination;
        }
        c.managerLoan=true;_saveExecution(c);
    }
    function endManagerExecution(bool owned) external {
        _executionCaller(false);Execution memory c=_loadExecution();
        if(!c.managerLoan || (owned?c.owner!=msg.sender:c.owner!=address(contributionPricing)))revert InvalidState();
        _validateExecution(c);
        if(owned){_clearExecution();return;}
        c.managerLoan=false;
        // Full selected-venue state is proven through the entire balancing
        // call, including settlement/refunds. A later legitimate LP write may
        // change L in the NON-reference destination only; price/tick/fees stay
        // exact. Reference and external venue liquidity is never relaxed.
        if(c.venue.poolId!=bytes32(0) && c.venue.poolId==c.destination)c.venue.omitLiquidity=true;
        _saveExecution(c);
    }
    function executionBounds(address token) public view returns(uint256 lower,uint256 upper,bytes32 fingerprint) {
        Execution memory c=_loadQuote();if(c.owner==address(0))return priceBounds(token);
        _executionControls(c);if(c.pendingSwap)revert InvalidState();
        uint256 i;if(token==address(0))i=0;else if(token==c.zzz)i=2;else revert InvalidPrice(token);
        lower=c.bounds[i];upper=c.bounds[i+1];
        fingerprint=c.fingerprints[i/2];
    }
    function executionReferenceX96(address token0,address token1) external view returns(uint160) {
        Execution memory c=_loadQuote();
        if(c.owner==address(0))return ZZZPriceMath.referenceX96(price(token0),price(token1),
            tokenDecimals(token0),tokenDecimals(token1),token0);
        _executionControls(c);if(c.pendingSwap)revert InvalidState();
        if((token0!=address(0) && token0!=c.zzz) || (token1!=address(0) && token1!=c.zzz))revert InvalidConfiguration();
        return ZZZPriceMath.referenceX96(c.bounds[token0==address(0)?0:2],c.bounds[token1==address(0)?0:2],
            token0==address(0)?18:c.zzzDigits,token1==address(0)?18:c.zzzDigits,token0);
    }
    function _readMarket(address stateView,bytes32 poolId) private view returns(MarketState memory state) {
        bytes memory slot=_boundedExecutionRead(stateView,abi.encodeWithSignature("getSlot0(bytes32)",poolId),128,address(0));
        (state.sqrtPriceX96,state.tick,state.protocolFee,state.lpFee)=abi.decode(slot,(uint160,int24,uint24,uint24));
        state.liquidity=abi.decode(_boundedExecutionRead(stateView,
            abi.encodeWithSignature("getLiquidity(bytes32)",poolId),32,address(0)),(uint128));
    }
    /// @notice Arm exactly the quote-selected, actual-core swap. No keeper can
    /// supply an override or adopt an arbitrary newly observed reference state.
    function beforeSwap(address core,address stateView,bytes32 poolId,MarketState calldata expectedAfter) external {
        _executionCaller(false);Execution memory c=_loadExecution();
        if(!c.managerLoan || c.swapped || poolId==bytes32(0) ||
            IExecutionManagerIdentity(msg.sender).poolManager()!=core || IExecutionManagerIdentity(msg.sender).stateView()!=stateView)
            revert InvalidState();
        _validateExecution(c);
        MarketState memory before_=_readMarket(stateView,poolId);
        if(expectedAfter.sqrtPriceX96<TickMath.MIN_SQRT_PRICE || expectedAfter.sqrtPriceX96>=TickMath.MAX_SQRT_PRICE ||
            expectedAfter.tick<TickMath.MIN_TICK || expectedAfter.tick>=TickMath.MAX_TICK ||
            expectedAfter.protocolFee!=before_.protocolFee || expectedAfter.lpFee!=before_.lpFee)revert InvalidState();
        for(uint256 i;i<2;++i)if(c.markets[i].poolId==poolId && c.markets[i].core==core &&
            c.markets[i].stateView!=stateView)revert InvalidState();
        c.venue=ExecutionVenue(core,stateView,poolId,expectedAfter,false);
        c.swapped=true;c.pendingSwap=true;_saveExecution(c);
    }
    /// @notice Called immediately after core.swap, BEFORE input settlement,
    /// output delivery or token callbacks. Later boundaries prove it unchanged.
    function afterSwap() external {
        _executionCaller(false);Execution memory c=_loadExecution();
        if(!c.managerLoan || !c.pendingSwap || !c.swapped)revert InvalidState();
        _executionControls(c);
        MarketState memory actual=_readMarket(c.venue.stateView,c.venue.poolId);
        if(_marketHash(actual)!=_marketHash(c.venue.expected))revert InvalidState();
        for(uint256 i;i<2;++i)if(c.markets[i].poolId==c.venue.poolId && c.markets[i].core==c.venue.core) {
            if(c.markets[i].stateView!=c.venue.stateView)revert InvalidState();
            c.markets[i].expected=_marketHash(actual);
        }
        c.pendingSwap=false;_validateExecution(c);_saveExecution(c);
    }
}
