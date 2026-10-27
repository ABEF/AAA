// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Test} from "forge-std/Test.sol";
import {PooledVaultFixture} from "./VaultAccounting.t.sol";
import {Position} from "../src/libraries/ZZZTypes.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";

contract EmptyPooledPlan {
    function activePlan(uint256) external pure returns(bytes32) {return bytes32(0);}
}

/// @dev Stateful conservation with real custody/reward modules and a FAKE venue.
contract PooledAccountingHandler is PooledVaultFixture {
    uint256[] public ids;
    mapping(uint256 => address) public owners;
    uint256[2] private deposited;
    uint256[2] private collected;
    uint256[2] private paid;
    uint256[2] private donations;
    uint256 public expectedContribution;
    constructor() {
        setUp();
        // A constructor has no deployed runtime; use a deployed plan fixture.
        ac.bind(Ids.MIGRATION,address(new EmptyPooledPlan()));
        mint(false); activate(0,1000,1000); mint(true);
    }
    function mint(bool second) public {
        if(ac.paused() || ids.length>=8) return;
        address owner=second ? bob : alice;vm.deal(owner,10 ether);
        uint256 id=_mint(owner);ids.push(id);owners[id]=owner;
        assertEq(vault.sharesOf(id),0);assertFalse(membership.eligible(id));
    }
    function activate(uint256 seed,uint256 x,uint256 y) public {
        uint256 id=ids[seed%ids.length];
        if(ac.paused() || vault.nftBucket(id)!=0) return;
        _entry(id,bound(x,500,1000),bound(y,500,1000),true);
        assertEq(rewards.claimable(id,address(t0)),0,"retroactive reward");
        assertEq(rewards.claimable(id,address(t1)),0,"retroactive reward");
    }
    function _entry(uint256 id,uint256 x,uint256 y,bool first) private {
        uint256 bucket=vault.poolBucket(poolId);uint256 supply=vault.bucketTotalShares(bucket);
        Position memory p=vault.group(bucket);
        uint256 nav=venue.a0(p.lpTokenId)+venue.a1(p.lpTokenId)+p.idle0+p.idle1;
        nav+=fees.compoundBalance(bucket,address(t0))+fees.compoundBalance(bucket,address(t1));
        uint256 beforeShares=vault.sharesOf(id);
        uint256 old0=rewards.claimable(id,address(t0));uint256 old1=rewards.claimable(id,address(t1));
        vm.prank(owners[id]);
        if(first)vault.activate(id,poolId,x,y,1,block.timestamp+100);
        else vault.increase(id,x,y,1,block.timestamp+100);
        bucket=vault.nftBucket(id);
        uint256 expected=supply==0 ? (x+y)*1e18 : supply*(x+y)/nav;
        assertEq(vault.sharesOf(id)-beforeShares,expected,"independent share price");
        assertGe(rewards.claimable(id,address(t0)),old0,"lost history");
        assertGe(rewards.claimable(id,address(t1)),old1,"lost history");
        deposited[0]+=x;deposited[1]+=y;expectedContribution+=(x+y)*1e18;
    }
    function topUp(uint256 seed,uint256 x,uint256 y) external {
        uint256 id=ids[seed%ids.length];if(ac.paused() || vault.nftBucket(id)==0)return;
        _entry(id,bound(x,1,100),bound(y,1,100),false);
    }
    function harvest(uint256 x,uint256 y) public {
        if(ac.paused())return;x=bound(x,0,1000);y=bound(y,0,1000);
        venue.setFees(x,y);vault.collectFees(vault.poolBucket(poolId),block.timestamp+100);
        collected[0]+=x;collected[1]+=y;
    }
    function claim(uint256 seed,bool second) public {
        uint256 id=ids[seed%ids.length];uint256 token=second?1:0;
        uint256 expected=rewards.claimable(id,token==0?address(t0):address(t1));
        vm.prank(owners[id]);uint256 amount=rewards.claim(id,token==0?address(t0):address(t1));
        assertEq(amount,expected);paid[token]+=amount;
    }
    function transfer(uint256 seed) external {
        uint256 id=ids[seed%ids.length];address old=owners[id];address next=old==alice?bob:alice;
        uint256 shares=vault.sharesOf(id);uint256 entitlement=rewards.claimable(id,address(t0));
        vm.prank(old);nft.transferFrom(old,next,id);owners[id]=next;
        assertEq(vault.sharesOf(id),shares);assertEq(rewards.claimable(id,address(t0)),entitlement);
    }
    function paused(bool state) external {ac.setPaused(state);}
    function donate(uint256 amount,bool second) external {
        amount=bound(amount,1,1000);uint256 token=second?1:0;
        if(second)t1.mint(address(vault),amount);else t0.mint(address(vault),amount);donations[token]+=amount;
    }
    function rebalance() external {
        if(ac.paused())return;uint256 bucket=vault.poolBucket(poolId);uint256 shares=vault.bucketTotalShares(bucket);
        vault.rebalance(bucket,1,block.timestamp+100);assertEq(vault.bucketTotalShares(bucket),shares);
    }
    function compound() external {
        if(ac.paused())return;uint256 bucket=vault.poolBucket(poolId);
        if(fees.compoundBalance(bucket,address(t0))+fees.compoundBalance(bucket,address(t1))==0)return;
        policy.setNeed(false);
        compounder.compound(bucket,1,block.timestamp+100);
        policy.setNeed(true);
    }
    function assertConservation() external view {
        uint256 bucket=vault.poolBucket(poolId);Position memory p=vault.group(bucket);
        uint256 shares;uint256 contribution;uint256 active;uint256[2] memory claims;
        for(uint256 i;i<ids.length;i++) {
            uint256 id=ids[i];assertEq(nft.ownerOf(id),owners[id]);
            shares+=vault.sharesOf(id);contribution+=vault.contributionUSD(id);
            assertEq(membership.eligible(id),vault.nftBucket(id)!=0);
            if(membership.eligible(id))active++;
            if(vault.nftBucket(id)==0)assertEq(vault.sharesOf(id),0);
            claims[0]+=rewards.claimable(id,address(t0));claims[1]+=rewards.claimable(id,address(t1));
        }
        assertEq(shares,vault.bucketTotalShares(bucket));assertEq(contribution,p.depositUSD);
        assertEq(membership.totalEligible(),active);assertEq(contribution,expectedContribution);
        assertEq(vault.bucketCount(),1);assertEq(venue.ownerOf(p.lpTokenId),address(vault));
        assertEq(vault.totalIdle(address(t0)),p.idle0);assertEq(vault.totalIdle(address(t1)),p.idle1);
        assertEq(t0.balanceOf(address(vault)),p.idle0+donations[0]);assertEq(t1.balanceOf(address(vault)),p.idle1+donations[1]);
        for(uint256 i;i<2;i++) {
            address token=i==0?address(t0):address(t1);
            uint256 principal=(i==0?venue.a0(p.lpTokenId)+p.idle0:venue.a1(p.lpTokenId)+p.idle1);
            uint256 liabilities=rewards.liabilities(token);assertLe(claims[i],liabilities,"unfunded claim");
            uint256 balance=i==0?t0.balanceOf(address(rewards)):t1.balanceOf(address(rewards));
            assertEq(balance,liabilities+rewards.orphaned(token));
            uint256 feeBalance=i==0?t0.balanceOf(address(fees)):t1.balanceOf(address(fees));
            assertEq(feeBalance,fees.accounted(token));
            assertEq(feeBalance,fees.dust(bucket,token)+fees.compoundBalance(bucket,token)+fees.buybackBalance(token));
            assertEq(principal+feeBalance+balance+paid[i],deposited[i]+collected[i],"lost or created token");
        }
        assertEq(treasury.balance,ids.length*0.05 ether);assertEq(address(vault).balance,0);
    }
}
contract ProductionAccountingInvariantTest is Test {
    PooledAccountingHandler private handler;
    function setUp() public {
        handler=new PooledAccountingHandler();bytes4[] memory selectors=new bytes4[](10);
        selectors[0]=handler.mint.selector;selectors[1]=handler.activate.selector;
        selectors[2]=handler.topUp.selector;selectors[3]=handler.harvest.selector;
        selectors[4]=handler.claim.selector;selectors[5]=handler.transfer.selector;
        selectors[6]=handler.paused.selector;selectors[7]=handler.donate.selector;
        selectors[8]=handler.rebalance.selector;selectors[9]=handler.compound.selector;
        targetContract(address(handler));targetSelector(FuzzSelector(address(handler),selectors));
    }
    function invariant_pooledCustodyAndClaimsConserved() public view {handler.assertConservation();}
    function testMembershipHistoryAndPausedClaims() public {
        handler.harvest(109,217);handler.activate(1,700,800);handler.topUp(0,30,40);
        handler.harvest(211,307);handler.rebalance();handler.paused(true);
        handler.transfer(0);handler.claim(0,false);handler.claim(1,true);handler.assertConservation();
    }
}
