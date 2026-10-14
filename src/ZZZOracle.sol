// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {IPriceFeed} from "./interfaces/IZZZ.sol";

/// @notice USD feed adapter, not a promise that every token has a safe price feed.
contract ZZZOracle is ZZZModule {
    struct Feed { address source; uint32 maxAge; uint8 feedDecimals; uint8 assetDecimals; }
    mapping(address => Feed) public feeds;
    address public immutable sequencerFeed;
    uint256 public constant SEQUENCER_GRACE = 1 hours;
    event FeedConfigured(address indexed token, address indexed source, uint32 maxAge);
    error InvalidPrice(address token);
    constructor(address controller, address sequencer) ZZZModule(controller) {
        if (sequencer != address(0) && sequencer.code.length == 0) revert InvalidConfiguration();
        sequencerFeed = sequencer;
    }
    function setFeed(address token, address feed, uint32 maxAge) external onlyGovernance {
        if (token.code.length == 0 || feed.code.length == 0 || maxAge == 0 || maxAge > 1 days) revert InvalidConfiguration();
        uint8 fd = IPriceFeed(feed).decimals();
        uint8 td = IERC20Metadata(token).decimals();
        if (fd > 18 || td > 18) revert InvalidConfiguration();
        feeds[token] = Feed(feed, maxAge, fd, td);
        emit FeedConfigured(token, feed, maxAge);
    }
    function _sequencerCheck() private view {
        if (sequencerFeed == address(0)) return;
        (, int256 answer, uint256 startedAt,,) = IPriceFeed(sequencerFeed).latestRoundData();
        if (answer != 0 || startedAt == 0 || startedAt > block.timestamp ||
            block.timestamp - startedAt <= SEQUENCER_GRACE) revert InvalidPrice(sequencerFeed);
    }
    function price(address token) public view returns (uint256 normalizedUSD) {
        _sequencerCheck();
        Feed memory f = feeds[token];
        if (f.source == address(0)) revert InvalidPrice(token);
        (uint80 round, int256 answer,, uint256 updated, uint80 answeredRound) = IPriceFeed(f.source).latestRoundData();
        if (answer <= 0 || round == 0 || answeredRound < round || updated == 0 ||
            updated > block.timestamp || block.timestamp - updated > f.maxAge) revert InvalidPrice(token);
        normalizedUSD = uint256(answer) * 10 ** (18 - f.feedDecimals);
        if (normalizedUSD == 0 || normalizedUSD > 1e36) revert InvalidPrice(token);
    }
    function tokenDecimals(address token) public view returns (uint8) {
        if (feeds[token].source == address(0)) revert InvalidPrice(token);
        return feeds[token].assetDecimals;
    }
    function value(address token, uint256 amount) public view returns (uint256) {
        return Math.mulDiv(amount, price(token), 10 ** tokenDecimals(token));
    }
    function quote(address input, address output, uint256 amount) external view returns (uint256) {
        return Math.mulDiv(value(input, amount), 10 ** tokenDecimals(output), price(output));
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
