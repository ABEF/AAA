// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZOracle} from "../../src/ZZZOracle.sol";
import {IPriceFeed} from "../../src/interfaces/IZZZ.sol";

/// @dev TEST ONLY correlated mirror for historical fixtures whose subject is
/// not data-provider independence. Distinct declared IDs are mock metadata,
/// never evidence of independent production sources. DualOracleSecurity uses
/// separately controlled feeds instead of this mirror.
contract CorrelatedFixtureFeed {
    IPriceFeed private immutable original;
    constructor(address source) { original = IPriceFeed(source); }
    function decimals() external view returns(uint8) { return original.decimals(); }
    function latestRoundData() external view returns(uint80,int256,uint256,uint256,uint80) {
        return original.latestRoundData();
    }
}
library DualOracleFixture {
    function setTestFeed(ZZZOracle oracle,address token,address primary,uint32 age) internal {
        address secondary = address(new CorrelatedFixtureFeed(primary));
        uint8 decimals = IPriceFeed(primary).decimals();
        oracle.setDualFeed(token,
            ZZZOracle.SourcePolicy(primary,primary.codehash,keccak256(abi.encode("TEST_PRIMARY",primary)),age,decimals),
            ZZZOracle.SourcePolicy(secondary,secondary.codehash,keccak256(abi.encode("TEST_CORRELATED_MIRROR",secondary)),age,decimals),
            0,keccak256("TEST_ONLY_NOT_INDEPENDENT_MARKET_QUALIFICATION"));
    }
}
