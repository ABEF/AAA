// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {SeaDropPoPLFixture} from "./SeaDropPoPLIntegration.t.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @dev Official pinned SeaDrop runtime + actual NFT/Vault/renderer/lifecycle
/// reader, controlled VRF and explicit MockAccess. No hosted OpenSea, public
/// signing, content availability or actual Access.seal qualification is proved.
contract SeaDropArtworkBoundary20261117Test is SeaDropPoPLFixture {
    function testSeaDropMintStillUsesCollectionRootForRevealedArtwork() public {
        // This fixture authority deliberately permits bindings. Production
        // binds its immutable lifecycle reader before sealing instead.
        access.bind(Ids.NFT_CANONICAL,address(new ZZZNFTCanonical(address(access),address(nft))));
        assertEq(_decode("data:application/json;base64,eyJrIjoidiJ9"),'{"k":"v"}');
        vm.warp(config.publicStart);
        _public(ALICE,1);
        uint256 id=_firstId();
        assertEq(nft.ownerOf(id),ALICE);assertEq(nft.originalMintRecipient(id),ALICE);
        assertEq(helper.totalMinted(),1);assertEq(vrf.sequence(),1);
        assertEq(FEE.balance,0.005 ether);assertEq(CREATOR.balance,0.045 ether);
        assertEq(address(vault).balance,0);assertEq(nft.artworkBaseURI(),"ipfs://TEST-ONLY/");
        string memory beforeURI=nft.tokenURI(id);
        string memory beforeJSON=_decode(beforeURI);
        assertFalse(vm.parseJsonBool(beforeJSON,".royalty_activated"));
        assertTrue(_starts(vm.parseJsonString(beforeJSON,".image"),"data:image/svg+xml;base64,"));
        vrf.fulfill(nft.requestOf(id),0,0);nft.finalizeTraits(id);
        string memory afterURI=nft.tokenURI(id);
        string memory afterJSON=_decode(afterURI);
        assertTrue(nft.traitsReady(id));assertTrue(keccak256(bytes(afterURI))!=keccak256(bytes(beforeURI)));
        string memory image=vm.parseJsonString(afterJSON,".image");
        assertTrue(_starts(image,"ipfs://TEST-ONLY/"));assertTrue(bytes(image).length>bytes("ipfs://TEST-ONLY/").length);
        assertFalse(vm.parseJsonBool(afterJSON,".royalty_activated"));
        assertEq(nft.royaltyRewards().weightOf(id),0);assertEq(vault.sharesOf(id),0);
        assertEq(nft.ownerOf(id),ALICE);assertEq(helper.totalMinted(),1);assertEq(vrf.sequence(),1);
    }

    function _starts(string memory value,string memory prefix) private pure returns(bool) {
        bytes memory a=bytes(value);bytes memory b=bytes(prefix);if(a.length<b.length)return false;
        for(uint256 i;i<b.length;++i)if(a[i]!=b[i])return false;return true;
    }
    // Same bounded decoding algorithm used by the maintained metadata tests,
    // with an independent known vector above and strict prefix/block checks.
    function _decode(string memory uri) private pure returns(string memory) {
        require(_starts(uri,"data:application/json;base64,"),"metadata prefix");
        bytes memory data=bytes(uri);uint256 prefix=29;require((data.length-prefix)%4==0,"base64 blocks");
        bytes memory decoded=new bytes((data.length-prefix)/4*3);uint256 count;
        for(uint256 i=prefix;i<data.length;i+=4) {
            uint256 word=(_digit(data[i])<<18)|(_digit(data[i+1])<<12)|(_digit(data[i+2])<<6)|_digit(data[i+3]);
            decoded[count++]=bytes1(uint8(word>>16));
            if(data[i+2]!="=")decoded[count++]=bytes1(uint8(word>>8));
            if(data[i+3]!="=")decoded[count++]=bytes1(uint8(word));
        }
        bytes memory result=new bytes(count);for(uint256 i;i<count;++i)result[i]=decoded[i];return string(result);
    }
    function _digit(bytes1 character) private pure returns(uint256) {
        uint8 value=uint8(character);if(value>=65&&value<=90)return value-65;
        if(value>=97&&value<=122)return value-71;if(value>=48&&value<=57)return value+4;
        if(value==43)return 62;if(value==47)return 63;require(value==61,"base64 digit");return 0;
    }
}
