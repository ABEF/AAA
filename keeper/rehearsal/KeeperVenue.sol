// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// Test-only operational fixture. No real liquidity, prices, royalties or Pons hook.
/// Exercises the keeper's actual ABI discovery, signed actions and process recovery.
contract KeeperVenue {
    address public admin;
    mapping(address => bool) public keepers;
    bool public paused;
    bool public requested;
    bool public rejectExecution;
    uint256 public harvests;
    uint256 public rebalances;
    uint256 public lastRebalance;

    constructor() { admin = msg.sender; }
    modifier onlyAdmin() { require(msg.sender == admin); _; }
    function authorize(address who, bool allowed) external onlyAdmin { keepers[who] = allowed; }
    function setPaused(bool value) external onlyAdmin { paused = value; }
    function requestRebalance() external onlyAdmin { requested = true; }
    function setReject(bool value) external onlyAdmin { rejectExecution = value; }
    function isSealed() external pure returns (bool) { return true; }
    function bucketCount() external pure returns (uint256) { return 1; }
    function bucketAt(uint256 ordinal) external pure returns (uint256) { require(ordinal == 0); return 1; }
    function bucketTotalShares(uint256 bucket) external pure returns (uint256) { require(bucket == 1); return 1000; }
    function config() public pure returns (uint256[14] memory c) {
        c[0] = 1; c[1] = 2; c[2] = 3000; c[3] = 60;
    }
    function poolId() public pure returns (bytes32) {
        uint256[14] memory c = config();
        return keccak256(abi.encode(c[0], c[1], c[2], c[3], c[4]));
    }
    function get(bytes32 pool) external pure returns (uint256[14] memory) { require(pool == poolId()); return config(); }
    function accounting(bytes32 pool) external pure returns (uint256[14] memory) { require(pool == poolId()); return config(); }
    function poolBucket(bytes32 pool) external pure returns (uint256) { require(pool == poolId()); return 1; }
    function group(uint256 bucket) external view returns (uint256[15] memory g) {
        require(bucket == 1);
        g[0] = uint256(poolId()); g[1] = 1; g[7] = 1; g[8] = block.chainid;
        g[9] = uint160(address(this)); g[10] = uint160(address(this));
        g[11] = uint160(address(this)); g[12] = uint160(address(this));
        g[13] = block.chainid; g[14] = uint160(address(this));
    }
    function rewardReceiver(uint256) external pure returns (address) { return address(0); }
    function needsRebalance(uint256) external view returns (bool) { return requested && block.timestamp >= lastRebalance + 600; }
    function collectFees(uint256 bucket, uint256 deadline) external {
        require(keepers[msg.sender] && !paused && !rejectExecution && bucket == 1 && block.timestamp <= deadline);
        ++harvests;
    }
    function rebalance(uint256 bucket, uint128 minimum, uint256 deadline) external {
        require(keepers[msg.sender] && !paused && !rejectExecution && requested && bucket == 1 && minimum > 0);
        require(block.timestamp <= deadline && block.timestamp >= lastRebalance + 600);
        ++rebalances; requested = false; lastRebalance = block.timestamp;
    }
}
