// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

interface IFixturePhysicalAmounts {
    function amounts(uint256) external view returns(uint256,uint256);
}
interface IFixtureExecutionIdentity {
    function executionPortfolioFingerprint(uint256) external view returns(bytes32);
}

/// @notice TEST ONLY: explicit one-leg fixture capability. Real two-leg
/// association, owner checks and execution are tested on the actual Manager.
abstract contract SinglePositionFixture {
    uint256 public constant PORTFOLIO_VERSION = 2;
    function positionOperator() external view returns(address) { return address(this); }
    function secondaryId(uint256) external pure returns(uint256) { return 0; }
    function activeSecondaryCount() external pure returns(uint256) { return 0; }
    function portfolioAmounts(uint256 id) external view returns(uint256,uint256) {
        return IFixturePhysicalAmounts(address(this)).amounts(id);
    }
    function portfolioFingerprint(uint256 id) external view returns(bytes32) {
        return keccak256(abi.encode(address(this),id));
    }
    function executionPortfolioFingerprint(uint256 id) external view returns(bytes32) {
        if (id == 0) return keccak256(abi.encode(address(this),id));
        (uint256 a0,uint256 a1) = IFixturePhysicalAmounts(address(this)).amounts(id);
        return keccak256(abi.encode(address(this),id,a0,a1));
    }
}

/// @notice TEST ONLY: accounting fixtures explicitly disable the new optional
/// strategy. They do not qualify policy geometry or sampled trigger timing.
abstract contract NoHybridPolicyFixture {
    function portfolioPolicy() external view returns(address) { return address(this); }
    function enabled(bytes32) external pure returns(bool) { return false; }
    function revision() external pure returns(uint64) { return 0; }
}

library PortfolioFixture {
    function executionHash(address manager,uint256 id) internal view returns(bytes32) {
        return IFixtureExecutionIdentity(manager).executionPortfolioFingerprint(id);
    }
}
