// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Constructor-only read tool. eth_call returns this finite ABI data;
/// no deployed helper, arbitrary selector, external value or mutable call exists.
contract WalletReadBatch {
    uint256 private constant PLAIN_GAS = 50_000;
    uint256 private constant LP_GAS = 250_000;
    uint256 private constant ROYALTY_GAS = 1_000_000;
    bytes32 private constant MAGIC = keccak256("POPL_WALLET_STATIC_READ_BATCH_V1");

    constructor(address[4] memory modules, uint256[] memory ids,
                address[2] memory lpAssets, address[] memory royaltyAssets) payable {
        require(msg.value == 0 && ids.length > 0 && ids.length <= 4 &&
            lpAssets[0] == address(0) && lpAssets[1] != address(0) && royaltyAssets.length <= 4);
        for (uint256 i; i < 4; ++i) {
            require(modules[i] != address(0));
            for (uint256 j; j < i; ++j) require(modules[i] != modules[j]);
        }
        for (uint256 i; i < ids.length; ++i) require(ids[i] != 0 && (i == 0 || ids[i] > ids[i-1]));
        for (uint256 i; i < royaltyAssets.length; ++i)
            require(i == 0 || royaltyAssets[i] > royaltyAssets[i-1]);

        uint256 rows = ids.length*(11+royaltyAssets.length);
        bytes memory out = new bytes(128+rows*96);
        bytes32 fingerprint = keccak256(abi.encode(modules,ids,lpAssets,royaltyAssets));
        bytes32 magic = MAGIC;
        uint256 chain = block.chainid;
        assembly ("memory-safe") {
            mstore(add(out,32),magic)
            mstore(add(out,64),chain)
            mstore(add(out,96),fingerprint)
            mstore(add(out,128),rows)
        }
        uint256 cursor = 128;
        for (uint256 i; i < ids.length; ++i) {
            uint256 id = ids[i];
            (cursor,,) = read(out,cursor,modules[0],abi.encodeWithSignature("ownerOf(uint256)",id),32,PLAIN_GAS);
            uint256 ordinalStatus; uint256 ordinal;
            (cursor,ordinalStatus,ordinal) = read(out,cursor,modules[0],abi.encodeWithSignature("mintOrdinalOf(uint256)",id),32,PLAIN_GAS);
            // The fixed row remains present even if the preceding ordinal read
            // failed. Python seeds no guessed tokenAtOrdinal query in that case.
            if (ordinalStatus == 1)
                (cursor,,) = read(out,cursor,modules[0],abi.encodeWithSignature("tokenAtOrdinal(uint256)",ordinal),32,PLAIN_GAS);
            else cursor += 96;
            (cursor,,) = read(out,cursor,modules[1],abi.encodeWithSignature("sharesOf(uint256)",id),32,PLAIN_GAS);
            (cursor,,) = read(out,cursor,modules[1],abi.encodeWithSignature("nftBucket(uint256)",id),32,PLAIN_GAS);
            (cursor,,) = read(out,cursor,modules[2],abi.encodeWithSignature("weightOf(uint256)",id),32,PLAIN_GAS);
            (cursor,,) = read(out,cursor,modules[3],abi.encodeWithSignature("rewardBucket(uint256)",id),32,PLAIN_GAS);
            for (uint256 a; a < 2; ++a)
                (cursor,,) = read(out,cursor,modules[3],abi.encodeWithSignature("claimableComponents(uint256,address)",id,lpAssets[a]),64,LP_GAS);
            for (uint256 a; a < 2; ++a)
                (cursor,,) = read(out,cursor,modules[3],abi.encodeWithSignature("claimable(uint256,address)",id,lpAssets[a]),32,LP_GAS);
            for (uint256 a; a < royaltyAssets.length; ++a)
                (cursor,,) = read(out,cursor,modules[2],abi.encodeWithSignature("claimable(uint256,address)",id,royaltyAssets[a]),32,ROYALTY_GAS);
        }
        require(cursor == out.length && out.length <= 24_576);
        assembly ("memory-safe") { return(add(out,32),mload(out)) }
    }

    /// @dev Copy at most two words. A malicious oversized return never expands
    /// output or memory. Status0 is revert;2 is a successful wrong ABI length.
    function read(bytes memory out, uint256 cursor, address target, bytes memory data,
                  uint256 size, uint256 gasCap)
        private view returns (uint256 next, uint256 status, uint256 first)
    {
        assembly ("memory-safe") {
            let output := add(add(out,32),cursor)
            let ok := staticcall(gasCap,target,add(data,32),mload(data),0,0)
            let length := returndatasize()
            status := 0
            if ok {
                status := 2
                if eq(length,size) {
                    status := 1
                    returndatacopy(add(output,32),0,size)
                    first := mload(add(output,32))
                }
            }
            mstore(output,status)
            next := add(cursor,96)
        }
    }
}
