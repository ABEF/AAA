// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
struct CanonicalNFTHeader {
    uint256 count; uint256 next; uint256 remaining; uint16[3] quotas; uint256 epoch; string base;
}
struct CanonicalNFTRecord {
    uint256 id; address owner; uint8 rarity; uint8 color; uint8 palette; uint8 pattern;
    uint256 requestId; uint256 requestEpoch; uint256 rarityWord; uint256 colorWord;
}
interface IZZZNFTCanonicalState {
    function access() external view returns (address);
    function mintedCount() external view returns (uint256);
    function nextToFinalize() external view returns (uint256);
    function remainingToReveal() external view returns (uint256);
    function rarityRemaining(uint256) external view returns (uint16);
    function randomnessEpoch() external view returns (uint256);
    function artworkBaseURI() external view returns (string memory);
    function tokenAtOrdinal(uint256) external view returns (uint256);
    function ownerOf(uint256) external view returns (address);
    function traitsReady(uint256) external view returns (bool);
    function rarityOf(uint256) external view returns (uint8);
    function colorOf(uint256) external view returns (uint8);
    function paletteOf(uint256) external view returns (uint8);
    function patternOf(uint256) external view returns (uint8);
    function requestOf(uint256) external view returns (uint256);
    function requestEpochOf(uint256) external view returns (uint256);
    function canonicalRandomness(uint256) external view returns (uint256,uint256,uint256,bool,bool);
    function canonicalArtwork(uint8,uint256) external view returns (uint16);
    function canonicalWriteHeader(uint256,uint256,uint256,uint16[3] calldata,uint256) external;
    function canonicalWriteRecord(uint256,CanonicalNFTRecord calldata) external;
    function canonicalWriteArtwork(uint8,uint256,uint16) external;
}
