// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IPriceFeed} from "./interfaces/IZZZ.sol";
import {ZZZContributionPricing} from "./ZZZContributionPricing.sol";

/// @notice Two-source USD consensus. Source independence is a reviewed governance
/// assertion, not something two addresses or two matching answers can prove.
contract ZZZOracle is ZZZModule {
    ZZZContributionPricing public immutable contributionPricing;
    uint256 public constant PRICING_VERSION = 2;
    uint16 public constant MAX_DEVIATION_BPS = 500;
    uint256 public constant SOURCE_CALL_GAS = 500_000;
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
    // Historical ABI only: primary metadata cannot establish V2 readiness.
    // Current consumers must inspect PRICING_VERSION and the complete dual policy.
    struct Feed { address source; uint32 maxAge; uint8 feedDecimals; uint8 assetDecimals; }
    mapping(address => Feed) public feeds;
    struct SequencerPolicy { address source; bytes32 expectedCodeHash; bytes32 reviewHash; bool bootstrapAdmission; }
    // The getter ABI is unchanged. Only governed, reviewed nonzero replacements
    // are possible; configuration never removes an existing uptime safeguard.
    address public sequencerFeed;
    mapping(bytes32 => SequencerPolicy) public sequencerPolicies;
    bytes32 public activeSequencerPolicy;
    bytes32[] private sequencerHistory;
    uint256 public constant SEQUENCER_GRACE = 1 hours;
    event FeedConfigured(address indexed token, address indexed source, uint32 maxAge);
    event DualPolicyRecorded(bytes32 indexed id, address indexed token, address indexed primary,
        address secondary, bytes32 primaryIndependenceId, bytes32 secondaryIndependenceId,
        uint16 maxDeviationBps, bytes32 reviewHash);
    event DualPolicyActivated(address indexed token, bytes32 indexed previousPolicy, bytes32 indexed activePolicy);
    event SequencerPolicyRecorded(bytes32 indexed id, address indexed source, bytes32 expectedCodeHash,
        bytes32 reviewHash, bool bootstrapAdmission);
    event SequencerPolicyActivated(bytes32 indexed previousPolicy, bytes32 indexed activePolicy);
    error InvalidPrice(address token);
    error SingleSourceUnsupported();
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
            IPriceFeed(source).decimals() != 0) revert InvalidConfiguration();
        uint80 round; uint80 answeredRound; uint256 updated;
        (round, answer, startedAt, updated, answeredRound) = IPriceFeed(source).latestRoundData();
        if (round == 0 || answeredRound < round || (answer != 0 && answer != 1) || startedAt == 0 ||
            startedAt > block.timestamp || updated < startedAt || updated > block.timestamp) revert InvalidPrice(source);
        // Uptime feeds report status transitions, not periodic price rounds. A
        // healthy unchanged status must not expire based on updatedAt age.
    }
    /// @notice A single-source policy is deliberately unavailable, including
    /// bootstrap. Retaining this ABI must not silently retain its old semantics.
    function setFeed(address, address, uint32) external pure {
        revert SingleSourceUnsupported();
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
        _validateSource(primary, token);
        _validateSource(secondary, token);
        // Reject an invalid current observation at admission too. Static source
        // calls cannot mutate the policy or its authority during these checks.
        _readBounds(next);
        bytes32 previous = activePolicy[token];
        id = keccak256(abi.encode(address(this), history.length, next));
        policies[id] = next;
        history.push(id);
        activePolicy[token] = id;
        feeds[token] = Feed(primary.source, primary.maxAge, primary.feedDecimals, assetDecimals);
        emit FeedConfigured(token, primary.source, primary.maxAge);
        emit DualPolicyRecorded(id, token, primary.source, secondary.source, primary.independenceId,
            secondary.independenceId, maxDeviationBps, reviewHash);
        emit DualPolicyActivated(token, previous, id);
    }
    function _boundedRead(address source, bytes4 selector, uint256 expectedLength, address token)
        private view returns (bytes memory result) {
        bool success;
        uint256 returned;
        uint256 gasLimit = SOURCE_CALL_GAS;
        // Copy only the exact bounded ABI result. A source cannot make the
        // caller allocate arbitrary returndata or disclose its revert payload.
        assembly ("memory-safe") {
            let input := mload(0x40)
            mstore(input, selector)
            success := staticcall(gasLimit, source, input, 4, 0, 0)
            returned := returndatasize()
        }
        if (!success || returned != expectedLength) revert InvalidPrice(token);
        result = new bytes(expectedLength);
        assembly ("memory-safe") { returndatacopy(add(result, 32), 0, expectedLength) }
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
        // Decode wide words first so noncanonical narrow integers produce the
        // same bounded domain error as other malformed source responses.
        (uint256 round, int256 answer, uint256 started, uint256 updated, uint256 answered) =
            abi.decode(encoded, (uint256, int256, uint256, uint256, uint256));
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
        lower = Math.min(a, b);
        upper = Math.max(a, b);
        // The denominator is the lower price. Rounding cannot admit a spread
        // one raw unit above the configured tolerance.
        if (upper - lower > Math.mulDiv(lower, p.maxDeviationBps, 10000)) revert InvalidPrice(p.token);
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
        (uint256 lower,,) = priceBounds(output);
        if (input == output) return amount;
        uint256 sourceUSD = Math.mulDiv(amount, upper, 10 ** tokenDecimals(input));
        return Math.mulDiv(sourceUSD, 10 ** tokenDecimals(output), lower);
    }
    function referenceX96(address token0, address token1) external view returns (uint160) {
        uint256 ratioX128 = Math.mulDiv(price(token0), uint256(1) << 128, price(token1));
        uint8 d0 = tokenDecimals(token0);
        uint8 d1 = tokenDecimals(token1);
        if (d1 >= d0) ratioX128 = Math.mulDiv(ratioX128, 10 ** (d1 - d0), 1);
        else ratioX128 /= 10 ** (d0 - d1);
        uint256 root = Math.sqrt(ratioX128);
        if (root == 0 || root > type(uint128).max) revert InvalidPrice(token0);
        return uint160(root << 32);
    }
}
