// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZPower} from "../src/ZZZPower.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {Ids,Position,PositionStatus,PoolConfig} from "../src/libraries/ZZZTypes.sol";
import {MockAccess,MockToken,MockPools,MockVaultRecord} from "./mocks/Mocks.sol";
contract RewardsAndFeesTest is Test,IERC721Receiver {
    MockAccess ac;MockToken token;MockToken token1;MockPools pools;MockVaultRecord vault;
    ZZZNFT nft;ZZZPower power;ZZZRewards rewards;ZZZFeeController fees;
    address alice=address(0xA11CE);address bob=address(0xB0B);
    function setUp() public {
        ac=new MockAccess();token=new MockToken(18);token1=new MockToken(18);
        nft=new ZZZNFT(address(ac),"ipfs://");power=new ZZZPower(address(ac));rewards=new ZZZRewards(address(ac));
        fees=new ZZZFeeController(address(ac));pools=new MockPools();vault=new MockVaultRecord();
        ac.bind(Ids.VAULT,address(this));ac.bind(Ids.NFT,address(nft));ac.bind(Ids.POWER,address(power));
        ac.bind(Ids.REWARDS,address(rewards));ac.bind(Ids.FEES,address(fees));ac.bind(Ids.POOLS,address(pools));
        ac.bind(Ids.BUYBACK,address(this));rewards.addAsset(address(token));ac.seal();
        nft.mint(alice,1);nft.mint(bob,2);power.add(1,100);
    }
    function credit(uint256 personal,uint256 shared) private {
        token.mint(address(fees),personal+shared);
        vm.startPrank(address(fees));token.approve(address(rewards),personal+shared);
        rewards.credit(1,address(token),personal,shared);vm.stopPrank();
    }
    function testNewPowerCannotClaimPublishedPastReward() public {
        credit(50,30);power.add(2,100);
        assertEq(rewards.claimable(1,address(token)),80);assertEq(rewards.claimable(2,address(token)),0);
        credit(0,40);assertEq(rewards.claimable(1,address(token)),100);assertEq(rewards.claimable(2,address(token)),20);
    }
    function testIncreasePowerCheckpointsEarlierAllocation() public {
        power.add(2,100);credit(0,40);power.add(1,200);
        assertEq(rewards.claimable(1,address(token)),20);credit(0,40);
        assertEq(rewards.claimable(1,address(token)),50);assertEq(rewards.claimable(2,address(token)),30);
    }
    function testNFTTransferCarriesUnclaimedRewards() public {
        credit(50,30);vm.prank(alice);nft.transferFrom(alice,bob,1);
        vm.prank(alice);vm.expectRevert();rewards.claim(1,address(token));
        vm.prank(bob);assertEq(rewards.claim(1,address(token)),80);assertEq(token.balanceOf(bob),80);
    }
    function testClaimWorksWhilePaused() public {
        credit(50,30);ac.setPaused(true);vm.prank(alice);rewards.claim(1,address(token));assertEq(token.balanceOf(alice),80);
    }
    function testClaimsCannotRepeat() public {
        credit(50,30);vm.startPrank(alice);rewards.claim(1,address(token));
        assertEq(rewards.claim(1,address(token)),0);vm.stopPrank();assertEq(token.balanceOf(alice),80);
    }
    function testUnauthorizedCredit() public {vm.expectRevert();rewards.credit(1,address(token),1,1);}
    function testUnauthorizedPowerChange() public {vm.prank(alice);vm.expectRevert();power.add(1,100);}
    function testFractionalClaimsRemainFunded() public {
        power.add(2,200);for(uint256 i;i<30;i++){credit(0,1);vm.prank(alice);rewards.claim(1,address(token));}
        vm.prank(bob);rewards.claim(2,address(token));
        assertLe(token.balanceOf(alice)+token.balanceOf(bob),30);
        assertGe(token.balanceOf(address(rewards)),rewards.liabilities(address(token)));
    }
    function testNFTSupportsStandardERC721() public {assertTrue(nft.supportsInterface(0x80ac58cd));}
    function testUnsafeReceiverRejected() public {
        vm.prank(alice);vm.expectRevert();nft.safeTransferFrom(alice,address(token),1);assertEq(nft.ownerOf(1),alice);
    }
    function feeSetup() private {
        PoolConfig memory c;c.key.currency0=address(token);c.key.currency1=address(token1);pools.set(bytes32(uint256(1)),c);
        Position memory p;p.poolId=bytes32(uint256(1));p.homeChain=block.chainid;p.homeVault=address(vault);p.status=PositionStatus.Active;
        vault.set(p);ac.bind(Ids.VAULT,address(vault));token.mint(address(vault),1000000);
        vm.prank(address(vault));token.approve(address(fees),type(uint256).max);
    }
    function testFeeSplitIsExactAndBacked() public {
        feeSetup();vm.prank(address(vault));fees.allocate(1,address(token),1000);
        assertEq(rewards.claimable(1,address(token)),800);assertEq(fees.compoundBalance(1,address(token)),100);
        assertEq(fees.buybackBalance(address(token)),100);assertEq(token.balanceOf(address(fees)),200);
        assertEq(fees.accounted(address(token)),200);
    }
    function testTinyFeesCannotManipulateSplit() public {
        feeSetup();for(uint256 i;i<10;i++){vm.prank(address(vault));fees.allocate(1,address(token),1);}
        assertEq(rewards.claimable(1,address(token)),8);assertEq(fees.compoundBalance(1,address(token)),1);
        assertEq(fees.buybackBalance(address(token)),1);assertEq(fees.dust(1,address(token)),0);
    }
    function testDustOnMigrationGoesToCanonicalNFT() public {
        feeSetup();vm.prank(address(vault));fees.allocate(1,address(token),9);
        Position memory p=vault.position(1);p.status=PositionStatus.Outbound;vault.set(p);
        vm.prank(address(vault));fees.flushDust(1,address(token));
        assertEq(rewards.claimable(1,address(token)),9);assertEq(fees.accounted(address(token)),0);
    }
    function testUnauthorizedReserveRelease() public {
        feeSetup();vm.prank(address(vault));fees.allocate(1,address(token),100);
        vm.prank(alice);vm.expectRevert();fees.releaseCompound(1,address(token));
        vm.prank(alice);vm.expectRevert();fees.releaseBuyback(address(token),10);
    }
    function testFuzzFeeConservation(uint96 amount) public {
        vm.assume(amount>0);feeSetup();token.mint(address(vault),amount);
        vm.prank(address(vault));fees.allocate(1,address(token),amount);
        uint256 units=uint256(amount)/10;
        assertEq(rewards.claimable(1,address(token)),units*8);
        assertEq(fees.compoundBalance(1,address(token))+fees.buybackBalance(address(token))+fees.dust(1,address(token)),uint256(amount)-units*8);
        assertEq(fees.accounted(address(token)),token.balanceOf(address(fees)));
    }
    function onERC721Received(address,address,uint256,bytes calldata) external pure override returns(bytes4){return IERC721Receiver.onERC721Received.selector;}
}
