// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZNFTMetadata,NFTMetadataInput} from "../src/ZZZNFTMetadata.sol";
import {ZZZArtwork} from "../src/libraries/ZZZArtwork.sol";
import {HistoricalMetadata20261115} from "./helpers/HistoricalMetadata20261115.sol";

interface IHistoricalMetadataRender {
    function render(NFTMetadataInput memory input)external pure returns(string memory);
}

/// @notice NEW differential properties against accepted compiled baseline bytes,
/// not reruns of the historical metadata test suite. Both calls are pure previews:
/// no financial graph, price service, wallet, public deployment or source adoption.
contract MetadataRendererCompatibilityTest is Test {
    IHistoricalMetadataRender private original;
    ZZZNFTMetadata private candidate;
    function setUp()public{
        original=IHistoricalMetadataRender(HistoricalMetadata20261115.deploy(address(this)));
        candidate=new ZZZNFTMetadata(address(this));
    }
    function _digit(bytes1 character)private pure returns(uint256){
        uint8 value=uint8(character);
        if(value>=65 && value<=90)return value-65;
        if(value>=97 && value<=122)return value-71;
        if(value>=48 && value<=57)return value+4;
        if(value==43)return 62;if(value==47)return 63;return 0;
    }
    function _json(string memory uri)private pure returns(string memory){
        bytes memory data=bytes(uri);uint256 prefix=29;
        bytes memory decoded=new bytes((data.length-prefix)/4*3);uint256 count;
        for(uint256 i=prefix;i<data.length;i+=4){
            uint256 word=(_digit(data[i])<<18)|(_digit(data[i+1])<<12)|(_digit(data[i+2])<<6)|_digit(data[i+3]);
            decoded[count++]=bytes1(uint8(word>>16));
            if(data[i+2]!="=")decoded[count++]=bytes1(uint8(word>>8));
            if(data[i+3]!="=")decoded[count++]=bytes1(uint8(word));
        }
        bytes memory result=new bytes(count);for(uint256 i;i<count;++i)result[i]=decoded[i];
        return string(result);
    }
    function _input(uint8 palette,uint8 rarity,uint8 pattern,uint8 stage,bool available,bool ready)
        private pure returns(NFTMetadataInput memory value){
        value=NFTMetadataInput(type(uint256).max-uint256(palette)*100-uint256(rarity)*10-pattern,
            rarity,palette,pattern,stage,ready,available,
            stage==0 || stage==4?0:uint256(stage)*1000e18,stage==0?0:rarity+1,"ipfs://reviewed-preview/");
    }
    function _compare(NFTMetadataInput memory input)private view{
        string memory beforeJSON=_json(original.render(input));
        string memory afterJSON=_json(candidate.render(input));
        assertEq(vm.parseJsonString(afterJSON,".name"),vm.parseJsonString(beforeJSON,".name"));
        assertEq(vm.parseJsonString(afterJSON,".image"),vm.parseJsonString(beforeJSON,".image"));
        assertEq(vm.parseJsonBool(afterJSON,".valuation_available"),vm.parseJsonBool(beforeJSON,".valuation_available"));
        assertEq(vm.parseJsonBool(afterJSON,".lp_exited"),vm.parseJsonBool(beforeJSON,".lp_exited"));
        assertEq(vm.parseJsonBool(afterJSON,".royalty_activated"),vm.parseJsonBool(beforeJSON,".royalty_activated"));
        assertTrue(vm.keyExistsJson(beforeJSON,".lp_value_usd_18"));assertTrue(vm.keyExistsJson(afterJSON,".lp_value_usd_18"));
        assertEq(vm.parseJson(afterJSON,".lp_value_usd_18"),vm.parseJson(beforeJSON,".lp_value_usd_18"));
        uint256 colors;
        if(input.traitsReady){
            uint8 mask=ZZZArtwork.mask(input.palette);
            for(uint256 i;i<8;++i)if((mask & uint8(1<<i))!=0)++colors;
        }
        uint256 count=input.traitsReady?6+colors:6;
        for(uint256 i;i<count;++i){
            string memory path=string.concat(".attributes[",vm.toString(i),"]");
            assertTrue(vm.keyExistsJson(beforeJSON,path));assertTrue(vm.keyExistsJson(afterJSON,path));
            string memory key=string.concat(path,".trait_type");
            string memory trait=vm.parseJsonString(beforeJSON,key);
            assertEq(vm.parseJsonString(afterJSON,key),trait);
            key=string.concat(path,".value");
            if(input.traitsReady && keccak256(bytes(trait))==keccak256("NFT-sale royalty weight"))
                assertEq(vm.parseJsonUint(afterJSON,key),vm.parseJsonUint(beforeJSON,key));
            else assertEq(vm.parseJsonString(afterJSON,key),vm.parseJsonString(beforeJSON,key));
        }
        string memory pastEnd=string.concat(".attributes[",vm.toString(count),"]");
        assertFalse(vm.keyExistsJson(beforeJSON,pastEnd));assertFalse(vm.keyExistsJson(afterJSON,pastEnd));
        // Description is intentionally corrected; canonical-only schema/context
        // is tested through actual tokenURI in the lifecycle composition suite.
    }
    function testMetadataRenderCompatibilityVisualInventoryAndEscapedPreviewURI()public{
        uint8[3] memory palettes=[uint8(0),uint8(8),uint8(30)];uint256 cases;
        for(uint256 style;style<3;++style)for(uint8 rarity;rarity<3;++rarity)for(uint8 pattern;pattern<4;++pattern){
            uint8 stage=uint8((uint256(rarity)+pattern)%5);
            _compare(_input(palettes[style],rarity,pattern,stage,true,true));
            _compare(_input(palettes[style],rarity,pattern,uint8((stage+2)%5),true,true));cases+=2;
        }
        NFTMetadataInput memory escaped=_input(30,2,3,4,true,true);
        // Caller preview only; this string is not an admitted immutable root.
        escaped.baseURI="ipfs://preview/quote\"backslash\\newline\n/";
        _compare(escaped);++cases;assertEq(cases,73);
        emit log_named_uint("new_visual_differential_cases",cases);
    }
    function testMetadataRenderCompatibilityUnavailableAndUnrevealedPreview()public{
        uint8[3] memory palettes=[uint8(0),uint8(8),uint8(30)];uint256 cases;
        for(uint256 style;style<3;++style)for(uint8 rarity;rarity<3;++rarity)for(uint8 pattern;pattern<4;++pattern){
            _compare(_input(palettes[style],rarity,pattern,uint8(1+pattern%3),false,true));++cases;
        }
        NFTMetadataInput memory pending=_input(0,0,0,0,true,false);pending.royaltyWeight=0;
        _compare(pending);++cases;assertEq(cases,37);
        emit log_named_uint("new_unavailable_unrevealed_differential_cases",cases);
    }
}
