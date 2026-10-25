// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Fixed module boundary for a frozen, complete canonical-state handoff.
/// Rows are source-derived, ordered and include explicit zero accounting rows.
interface IZZZCanonicalModule {
    function canonicalCapture() external;
    function canonicalSettle() external;
    function canonicalCount() external view returns (uint256);
    function canonicalExport(uint256 row) external view returns (bytes memory);
    function canonicalImport(uint256 row, bytes calldata record) external;
    function canonicalAssetCount() external view returns (uint256);
    function canonicalBacking(uint256 index) external view returns (address asset, uint256 amount);
    function canonicalRelease(uint256 index, address destination) external;
    function canonicalRestore(uint256 index, address source) external payable;
    function canonicalAccept(uint256 index, address source) external payable;
    function canonicalValidate() external view;
    function canonicalActivate() external;
}

interface IZZZCanonicalAccess {
    function canonicalHandoff() external view returns (address);
    // 0: operating, 1: frozen source, 2: importing, 3: retired, 4: cancelled destination.
    function canonicalState() external view returns (uint8);
    function canonicalSettling() external view returns (bool);
}

