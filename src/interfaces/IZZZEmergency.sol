// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice A manual, paused governance operation. Mask bits RETAIN checks:
/// 1=raw ordinary trigger/cooldown (not sampled confirmation); 2=independent price agreement;
/// 4=USD loss/venue-quality/idle limits; 8=pool operations-enabled flags.
/// 16=recorded sampled confirmation (can expire while paused).
/// Zero explicitly bypasses these economic/timing checks, never custody,
/// native ETH/fixed ZZZ identity, exact accounting or terminal lifecycle locks.
struct EmergencyRebalance {
    uint256 bucket;
    bytes32 custodyHash;
    uint8 checks;
    int24 lower;
    int24 upper;
    bytes32 swapPool;
    bool zeroForOne;
    uint128 amountIn;
    uint128 minimumOut;
    uint128 minimumLiquidity;
    uint256 deadline;
    bytes32 reviewHash;
}

interface IZZZEmergencyBudget {
    function emergencyActive() external view returns(bool);
    function emergencyBucket() external view returns(uint256);
    function emergencyChecks() external view returns(uint8);
    function emergencyFingerprint() external view returns(bytes32);
    function validateEmergency(uint256 bucket) external view;
}
interface IZZZEmergencyController {
    function emergencyRequest() external view returns(EmergencyRebalance memory);
}
interface IZZZEmergencyVault {
    function migrationBudget() external view returns(address);
    function emergencyRebalance(uint256 bucket,uint128 minimumLiquidity,uint256 deadline) external;
}
interface IZZZEmergencyLiquidity {
    function beginEmergency() external;
    function endEmergency() external;
}
