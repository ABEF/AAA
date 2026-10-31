// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZArtwork} from "../src/libraries/ZZZArtwork.sol";

/// @notice Exhaust the unchanged finite tables, not regenerated art snapshots.
/// State/draw ordering remains covered by the collection's reveal tests.
contract ArtworkLookupTest is Test {
    ZZZNFTMetadata private renderer;
    function setUp() public { renderer = new ZZZNFTMetadata(address(0x1234)); }

    function _compare(uint8 rarity,uint256 count) private view {
        for(uint256 item;item<count;++item) {
            (uint8 expectedPalette,uint8 expectedPattern)=ZZZArtwork.item(rarity,item);
            uint8 expectedColor=ZZZArtwork.primaryColor(expectedPalette);
            (uint8 palette,uint8 pattern,uint8 color)=renderer.artworkItem(rarity,item);
            assertEq(palette,expectedPalette,"palette changed");
            assertEq(pattern,expectedPattern,"pattern changed");
            assertEq(color,expectedColor,"primary color changed");
        }
    }
    function testAll600CommunMappingsUnchanged() public view { _compare(0,600); }
    function testAll300RareMappingsUnchanged() public view { _compare(1,300); }
    function testAll100LegendaryMappingsUnchanged() public view { _compare(2,100); }
    function testInvalidLookupDomainRejects() public {
        vm.expectRevert(ZZZNFTMetadata.InvalidArtwork.selector);renderer.artworkItem(3,0);
        vm.expectRevert(ZZZNFTMetadata.InvalidArtwork.selector);renderer.artworkItem(0,600);
        vm.expectRevert(ZZZNFTMetadata.InvalidArtwork.selector);renderer.artworkItem(1,300);
        vm.expectRevert(ZZZNFTMetadata.InvalidArtwork.selector);renderer.artworkItem(2,100);
    }
}
