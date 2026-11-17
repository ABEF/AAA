// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {MockAccess} from "./mocks/Mocks.sol";
import {ProtocolPolicyFixture} from "./helpers/ProtocolPolicyFixture.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZNFTMetadata} from "../src/ZZZNFTMetadata.sol";
import {ZZZModule} from "../src/base/ZZZModule.sol";

/// @dev Focused constructor/content guards, not release readiness. Historical
/// creation bytecode is tracked and hash-pinned solely to reproduce acceptance
/// of the invalid inputs. It is never an admitted production artifact.
contract SealCriticalInputs20261117Test is Test {
    MockAccess private control;
    ZZZMigrationBudget private budget;
    ZZZNFTMetadata private renderer;

    function setUp() public {
        control = new MockAccess();
        ProtocolPolicyFixture.bind(address(control));
        budget = new ZZZMigrationBudget(address(control));
        renderer = new ZZZNFTMetadata(address(control));
    }

    function _historical(string memory name, bytes32 expectedHash, bytes memory args)
        private returns (address deployed) {
        bytes memory code = vm.getCode(string.concat("test/fixtures/seal-critical-003c8d8/",name,".json"));
        assertEq(sha256(code),expectedHash,"historical creation bytes changed");
        bytes memory init = bytes.concat(code,args);
        assembly ("memory-safe") { deployed := create(0,add(init,32),mload(init)) }
        assertGt(deployed.code.length,0,"historical fixture must actually deploy");
    }

    function testForeignHomeChainHistoricalAcceptanceNowRejectedAtConstruction() public {
        uint256 foreign = block.chainid + 1;
        address old = _historical("ZZZVault",
            0x86e0099b554188f66e75ab9572ebc72e860028664e9b26e3523531c3f773b29f,
            abi.encode(address(control),foreign,address(budget)));
        assertEq(ZZZVault(payable(old)).canonicalChainId(),foreign);
        assertNotEq(ZZZVault(payable(old)).canonicalChainId(),block.chainid);
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        new ZZZVault(address(control),foreign,address(budget));
    }

    function testZeroHomeChainStillRejectedAndCurrentChainRemainsValid() public {
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        new ZZZVault(address(control),0,address(budget));
        ZZZVault valid = new ZZZVault(address(control),block.chainid,address(budget));
        assertEq(valid.canonicalChainId(),block.chainid);
        assertEq(address(valid.access()),address(control));
        assertEq(address(valid.migrationBudget()),address(budget));
    }

    function testSchemeOnlyHistoricalAcceptanceNowRejectedForBothSchemes() public {
        address old = _historical("ZZZNFTMetadata",
            0x4f6d31c72e99976d7f14fa61acd1f690ec1635ead23529f3134f32ad72d9c97b,
            abi.encode(address(control)));
        ZZZNFTMetadata(old).validateBaseURI("ipfs://");
        ZZZNFTMetadata(old).validateBaseURI("ar://");
        vm.expectRevert(ZZZNFTMetadata.InvalidConfiguration.selector);
        renderer.validateBaseURI("ipfs://");
        vm.expectRevert(ZZZNFTMetadata.InvalidConfiguration.selector);
        renderer.validateBaseURI("ar://");
        // Syntax acceptance is deliberately not CID or content qualification.
        renderer.validateBaseURI("");
        renderer.validateBaseURI("ipfs://TEST-ONLY/");
        renderer.validateBaseURI("ar://TEST-ONLY/");
    }

    function testActualNFTConstructorRejectsSchemeOnlyArtworkRoot() public {
        vm.expectRevert(ZZZNFTMetadata.InvalidConfiguration.selector);
        new ZZZNFT(address(control),"ipfs://",address(renderer));
        vm.expectRevert(ZZZNFTMetadata.InvalidConfiguration.selector);
        new ZZZNFT(address(control),"ar://",address(renderer));
    }

    function testEmptyNFTBootstrapRootCanRecoverWithoutConsumingOneTimeWrite() public {
        ZZZNFT nft = new ZZZNFT(address(control),"",address(renderer));
        assertEq(nft.artworkBaseURI(),"");
        vm.expectRevert(ZZZNFTMetadata.InvalidConfiguration.selector);
        nft.setBaseURI("ipfs://");
        assertEq(nft.artworkBaseURI(),"");
        nft.setBaseURI("ipfs://TEST-ONLY/");
        assertEq(nft.artworkBaseURI(),"ipfs://TEST-ONLY/");
        vm.expectRevert(ZZZModule.InvalidConfiguration.selector);
        nft.setBaseURI("ar://another-TEST-ONLY/");
        assertEq(nft.artworkBaseURI(),"ipfs://TEST-ONLY/");
    }
}
