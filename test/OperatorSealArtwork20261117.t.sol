// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

/// @dev Sealing checks these typed bindings. Other economics are deliberately
/// absent: this regression isolates the actual controller/NFT/bootstrap trap,
/// not real pool, VRF, market, full graph or release qualification.
contract OperatorSealBindingFixture {
    address public immutable access;
    address public immutable nft;
    address public immutable vault;
    address public immutable fees;
    address public immutable activationAssets;
    address public immutable zzz;
    address public immutable currentZZZ;
    constructor(address controller,address collection,address custody,address feeLedger,address identity) {
        access=controller;nft=collection;vault=custody;fees=feeLedger;
        activationAssets=address(this);zzz=identity;currentZZZ=identity;
    }
    function canonicalChainId() external view returns(uint256) {return block.chainid;}
}

contract OperatorSealArtwork20261117Test is Test {
    bytes32 constant REVIEW=keccak256("isolated seal artwork root readiness");

    function _graph(string memory root) private returns(ZZZAccessController access,ZZZNFT nft) {
        access=new ZZZAccessController(address(this),address(0xB0B),address(0xCA701));
        ZZZProtocolPolicy policy=new ZZZProtocolPolicy(address(access),address(0xFEE));
        access.bindProtocolPolicy(address(policy));
        nft=new ZZZNFT(address(access),root,address(new ZZZNFTMetadata(address(access))));
        access.bind(Ids.NFT,address(nft));
        address custody=address(new OperatorSealBindingFixture(address(access),address(nft),address(0),address(0),address(0x222)));
        address fees=address(new OperatorSealBindingFixture(address(access),address(nft),custody,address(0),address(0x222)));
        access.bind(Ids.VAULT,custody);access.bind(Ids.FEES,fees);
        bytes32[13] memory others=[Ids.LIQUIDITY,Ids.REWARDS,Ids.MEMBERSHIP,Ids.STRATEGY,
            Ids.COMPOUNDER,Ids.BUYBACK,Ids.MIGRATION,Ids.ORACLE,Ids.POOLS,
            Ids.CANONICAL,Ids.NFT_CANONICAL,Ids.VAULT_CANONICAL,Ids.FEES_CANONICAL];
        for(uint256 i;i<others.length;++i)
            access.bind(others[i],address(new OperatorSealBindingFixture(address(access),address(nft),custody,fees,address(0x222))));
        address coordinator=address(new OperatorSealBindingFixture(address(access),address(nft),custody,fees,address(0x222)));
        policy.configureRandomness(coordinator,coordinator.codehash,bytes32(uint256(1)),1,3,500000,false,REVIEW);
    }

    function testUnconfiguredArtworkRootBlocksSealThenBootstrapCanCompleteSetup() public {
        (ZZZAccessController access,ZZZNFT nft)=_graph("");
        assertEq(nft.artworkBaseURI(),"");assertEq(access.bootstrap(),address(this));
        vm.expectRevert(ZZZAccessController.InvalidConfiguration.selector);
        access.seal();
        assertFalse(access.isSealed());assertEq(access.bootstrap(),address(this));
        nft.setBaseURI("ipfs://reviewed-complete-catalog/");
        access.seal();
        assertTrue(access.isSealed());assertEq(access.bootstrap(),address(0));
        assertEq(nft.artworkBaseURI(),"ipfs://reviewed-complete-catalog/");
        vm.expectRevert();nft.setBaseURI("ipfs://replacement/");
    }

    function testConstructorConfiguredArtworkRootStillSealsWithoutMutation() public {
        (ZZZAccessController access,ZZZNFT nft)=_graph("ar://reviewed-complete-catalog/");
        assertFalse(access.isSealed());
        access.seal();
        assertTrue(access.isSealed());assertEq(access.bootstrap(),address(0));
        assertEq(nft.artworkBaseURI(),"ar://reviewed-complete-catalog/");
        assertEq(nft.mintedCount(),0);
    }

    function testNonbootstrapCannotPopulateEmptyRootOrSeal() public {
        (ZZZAccessController access,ZZZNFT nft)=_graph("");
        vm.startPrank(address(0xB0B));
        vm.expectRevert();nft.setBaseURI("ipfs://unreviewed/");
        vm.expectRevert();access.seal();
        vm.stopPrank();
        assertEq(nft.artworkBaseURI(),"");assertFalse(access.isSealed());
        assertEq(access.bootstrap(),address(this));
    }
}
