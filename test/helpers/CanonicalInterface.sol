// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

interface ICanonicalHandoffTest {
    function prepareImport(address sourceController) external;
    function deploymentCommitment() external view returns (bytes32);
    function freeze() external;
    function settle(uint8 slot) external;
    function settlementCursor() external view returns (uint8);
    function phase() external view returns (uint8);
    function moduleAt(uint8 slot) external view returns (address);
    function recordCount(uint256 slot) external view returns (uint256);
    function assetCount(uint256 slot) external view returns (uint256);
    function exportRows(uint8 slot, uint256 count) external;
    function importRows(uint8 slot, bytes[] calldata records) external;
    function completeImport() external;
    function fund(uint8 slot, uint256 index) external;
    function commit() external;
    function abort() external;
    function returnFunds(uint8 slot, uint256 index) external;
    function finishAbort() external;
    function stateRoot() external view returns (bytes32);
    function funded(uint8 slot, uint256 index) external view returns (bool);
}
