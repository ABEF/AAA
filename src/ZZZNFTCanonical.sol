// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";
import {CanonicalNFTHeader, CanonicalNFTRecord, IZZZNFTCanonicalState} from "./interfaces/IZZZNFTCanonical.sol";

/// @notice Seal-bound NFT state codec. It has no custody or independent economic
/// authority; typed writes are usable only by the fixed handoff while importing.
contract ZZZNFTCanonical is ZZZModule {
    IZZZNFTCanonicalState public immutable nft;
    uint256 private cursor;
    constructor(address controller, address collection) ZZZModule(controller) {
        if (collection.code.length == 0 || IZZZNFTCanonicalState(collection).access() != controller) revert InvalidConfiguration();
        nft = IZZZNFTCanonicalState(collection);
    }
    function canonicalCapture() external onlyHandoff {
        uint256 count = nft.mintedCount();
        if (nft.nextToFinalize() != count + 1 || nft.remainingToReveal() != 1000 - count ||
            uint256(nft.rarityRemaining(0)) + nft.rarityRemaining(1) + nft.rarityRemaining(2) != nft.remainingToReveal()) revert InvalidState();
    }
    function canonicalSettle() external onlyHandoff {}
    function canonicalCount() public view returns (uint256) { return 1001 + nft.mintedCount(); }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if ((access.canonicalState() != 1 && access.canonicalState() != 3) || row >= canonicalCount()) revert InvalidState();
        if (row == 0) {
            uint16[3] memory quotas = [nft.rarityRemaining(0), nft.rarityRemaining(1), nft.rarityRemaining(2)];
            return abi.encode(CanonicalNFTHeader(nft.mintedCount(),nft.nextToFinalize(),nft.remainingToReveal(),
                quotas,nft.randomnessEpoch(),nft.artworkBaseURI()));
        }
        uint256 count = nft.mintedCount();
        if (row <= count) {
            uint256 id = nft.tokenAtOrdinal(row);
            (uint256 actualId,uint256 rarityWord,uint256 colorWord,bool requested,bool fulfilled) = nft.canonicalRandomness(id);
            if (!nft.traitsReady(id) || !requested || !fulfilled || actualId != id) revert InvalidState();
            return abi.encode(CanonicalNFTRecord(id,nft.ownerOf(id),nft.rarityOf(id),nft.colorOf(id),nft.paletteOf(id),
                nft.patternOf(id),nft.requestOf(id),nft.requestEpochOf(id),rarityWord,colorWord));
        }
        (uint8 rarity, uint256 item) = _inventoryRow(row - count - 1);
        return abi.encode(rarity,item,nft.canonicalArtwork(rarity,item));
    }
    function canonicalImport(uint256 row, bytes calldata record) external onlyHandoff {
        if (access.canonicalState() != 2 || row != cursor++) revert InvalidState();
        if (row == 0) {
            if (nft.mintedCount() != 0) revert InvalidState();
            CanonicalNFTHeader memory header = abi.decode(record,(CanonicalNFTHeader));
            if (header.count > 1000 || header.next != header.count + 1 || header.remaining != 1000 - header.count ||
                uint256(header.quotas[0]) + header.quotas[1] + header.quotas[2] != header.remaining ||
                header.quotas[0] > 600 || header.quotas[1] > 300 || header.quotas[2] > 100 ||
                keccak256(bytes(header.base)) != keccak256(bytes(nft.artworkBaseURI()))) revert InvalidState();
            nft.canonicalWriteHeader(header.count,header.next,header.remaining,header.quotas,header.epoch + 1);
            return;
        }
        if (row >= canonicalCount()) revert InvalidState();
        uint256 count = nft.mintedCount();
        if (row <= count) {
            CanonicalNFTRecord memory value = abi.decode(record,(CanonicalNFTRecord));
            if (value.owner == address(0) || value.rarity > 2 || value.palette >= 58 || value.pattern >= 4 ||
                value.color != ZZZArtwork.primaryColor(value.palette) || value.requestId == 0 ||
                value.requestEpoch >= nft.randomnessEpoch()) revert InvalidState();
            nft.canonicalWriteRecord(row,value); return;
        }
        (uint8 rarity,uint256 item,uint16 value) = abi.decode(record,(uint8,uint256,uint16));
        (uint8 expectedRarity,uint256 expectedItem) = _inventoryRow(row - count - 1);
        uint256 limit = rarity == 0 ? 600 : rarity == 1 ? 300 : 100;
        if (rarity != expectedRarity || item != expectedItem || value > limit) revert InvalidState();
        nft.canonicalWriteArtwork(rarity,item,value);
    }
    function _inventoryRow(uint256 row) private pure returns (uint8 rarity, uint256 item) {
        if (row < 600) return (0,row);
        if (row < 900) return (1,row - 600);
        return (2,row - 900);
    }
    function canonicalAssetCount() external pure returns (uint256) { return 0; }
    function canonicalBacking(uint256) external pure returns (address,uint256) { revert InvalidState(); }
    function canonicalRelease(uint256,address) external pure { revert InvalidState(); }
    function canonicalAccept(uint256,address) external payable { revert InvalidState(); }
    function canonicalRestore(uint256,address) external payable { revert InvalidState(); }
    function canonicalValidate() external view {
        if (access.canonicalState() == 2 && cursor != canonicalCount()) revert InvalidState();
    }
    function canonicalActivate() external onlyHandoff {
        if (access.canonicalState() != 2) revert InvalidState();
    }
}
