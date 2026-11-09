// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {Test} from "forge-std/Test.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {IERC721Receiver} from "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
import {VerifiedSeaDropV1} from "./fixtures/VerifiedSeaDropV1.sol";

// TEST ONLY: these tuples are taken from the verified deployed V1 ABI, not the
// current upstream main branch. The fixture below models ERC721 mint callbacks;
// it does not model PoPL accounting, authority, VRF proof verification or custody.
struct RuntimePublicDrop {
    uint80 mintPrice;
    uint48 startTime;
    uint48 endTime;
    uint16 maxTotalMintableByWallet;
    uint16 feeBps;
    bool restrictFeeRecipients;
}
struct RuntimeAllowListData {bytes32 merkleRoot;string[] publicKeyURIs;string allowListURI;}
struct RuntimeTokenGatedDropStage {
    uint80 mintPrice;uint16 maxTotalMintableByWallet;uint48 startTime;uint48 endTime;
    uint8 dropStageIndex;uint32 maxTokenSupplyForStage;uint16 feeBps;bool restrictFeeRecipients;
}
struct RuntimeSignedMintValidationParams {
    uint80 minMintPrice;uint24 maxMaxTotalMintableByWallet;uint40 minStartTime;
    uint40 maxEndTime;uint40 maxMaxTokenSupplyForStage;uint16 minFeeBps;uint16 maxFeeBps;
}

interface IVerifiedSeaDropRuntime {
    function mintPublic(address nft,address feeRecipient,address minterIfNotPayer,uint256 quantity) external payable;
    function getPublicDrop(address nft) external view returns(RuntimePublicDrop memory);
    function getCreatorPayoutAddress(address nft) external view returns(address);
    function updatePublicDrop(RuntimePublicDrop calldata drop) external;
    function updateCreatorPayoutAddress(address recipient) external;
    function updateAllowedFeeRecipient(address recipient,bool allowed) external;
    function updatePayer(address payer,bool allowed) external;
    function updateAllowList(RuntimeAllowListData calldata data) external;
    function updateTokenGatedDrop(address token,RuntimeTokenGatedDropStage calldata data) external;
    function updateDropURI(string calldata uri) external;
    function updateSignedMintValidationParams(address signer,RuntimeSignedMintValidationParams calldata data) external;
}

contract SeaDropConformingNFTFixture is ERC721 {
    IVerifiedSeaDropRuntime public immutable seaDrop;
    address public owner;
    uint256 public mintedCount;
    uint256 public syntheticDraws;
    mapping(address => uint256) public mintedBy;

    constructor(address implementation) ERC721("SeaDrop integration fixture","TEST") {
        seaDrop=IVerifiedSeaDropRuntime(implementation);owner=msg.sender;
    }
    modifier onlyOwner(){require(msg.sender==owner,"fixture owner");_;}
    function transferOwner(address next) external onlyOwner {owner=next;}
    function configure(RuntimePublicDrop calldata drop) external onlyOwner {seaDrop.updatePublicDrop(drop);}
    function creator(address recipient) external onlyOwner {seaDrop.updateCreatorPayoutAddress(recipient);}
    function fee(address recipient,bool allowed) external onlyOwner {seaDrop.updateAllowedFeeRecipient(recipient,allowed);}
    function payer(address recipient,bool allowed) external onlyOwner {seaDrop.updatePayer(recipient,allowed);}
    // The complete eleven-selector V1 interface is present. Fixtures constrain
    // the implementation address explicitly; no arbitrary external call exists.
    function updateAllowedSeaDrop(address[] calldata allowed) external onlyOwner {
        require(allowed.length==1&&allowed[0]==address(seaDrop),"fixed fixture implementation");
    }
    function _implementation(address implementation) private view {require(implementation==address(seaDrop),"fixed fixture implementation");}
    function updatePublicDrop(address implementation,RuntimePublicDrop calldata drop) external onlyOwner {
        _implementation(implementation);seaDrop.updatePublicDrop(drop);
    }
    function updateAllowList(address implementation,RuntimeAllowListData calldata data) external onlyOwner {
        _implementation(implementation);seaDrop.updateAllowList(data);
    }
    function updateTokenGatedDrop(address implementation,address token,RuntimeTokenGatedDropStage calldata data) external onlyOwner {
        _implementation(implementation);seaDrop.updateTokenGatedDrop(token,data);
    }
    function updateDropURI(address implementation,string calldata uri) external onlyOwner {
        _implementation(implementation);seaDrop.updateDropURI(uri);
    }
    function updateCreatorPayoutAddress(address implementation,address recipient) external onlyOwner {
        _implementation(implementation);seaDrop.updateCreatorPayoutAddress(recipient);
    }
    function updateAllowedFeeRecipient(address implementation,address recipient,bool allowed) external onlyOwner {
        _implementation(implementation);seaDrop.updateAllowedFeeRecipient(recipient,allowed);
    }
    function updateSignedMintValidationParams(address implementation,address signer,RuntimeSignedMintValidationParams calldata data) external onlyOwner {
        _implementation(implementation);seaDrop.updateSignedMintValidationParams(signer,data);
    }
    function updatePayer(address implementation,address recipient,bool allowed) external onlyOwner {
        _implementation(implementation);seaDrop.updatePayer(recipient,allowed);
    }
    function supportsInterface(bytes4 id) public view override returns(bool) {
        return id==0x1890fe8e || super.supportsInterface(id);
    }
    function getMintStats(address recipient) external view returns(uint256,uint256,uint256) {
        return(mintedBy[recipient],mintedCount,1000);
    }
    function mintSeaDrop(address recipient,uint256 quantity) external {
        require(msg.sender==address(seaDrop),"fixture SeaDrop");
        uint256 first=mintedCount+1;
        require(mintedCount+quantity<=1000,"fixture supply");
        mintedCount+=quantity;mintedBy[recipient]+=quantity;syntheticDraws+=quantity;
        for(uint256 i;i<quantity;++i)_safeMint(recipient,first+i);
    }
}

contract SeaDropRejectsETHFixture {
    receive() external payable {revert("reject payment");}
}

contract SeaDropReceiverFixture is IERC721Receiver {
    IVerifiedSeaDropRuntime public immutable seaDrop;
    SeaDropConformingNFTFixture public immutable nft;
    address public feeRecipient;
    bool public rejectNFT;
    bool public attemptReentry;
    bool public reentrySucceeded;
    bool public observedBatchStats;
    constructor(address implementation,SeaDropConformingNFTFixture collection,address fee) {
        seaDrop=IVerifiedSeaDropRuntime(implementation);nft=collection;feeRecipient=fee;
    }
    function behavior(bool reject,bool reenter) external {rejectNFT=reject;attemptReentry=reenter;}
    function mint(uint256 quantity,uint256 payment) external {
        seaDrop.mintPublic{value:payment}(address(nft),feeRecipient,address(0),quantity);
    }
    function onERC721Received(address,address,uint256,bytes calldata) external returns(bytes4) {
        require(msg.sender==address(nft),"wrong NFT");
        (uint256 wallet,uint256 total,)=nft.getMintStats(address(this));
        observedBatchStats=wallet==total && wallet>0;
        if(attemptReentry){
            (reentrySucceeded,)=address(seaDrop).call{value:0.05 ether}(
                abi.encodeCall(seaDrop.mintPublic,(address(nft),feeRecipient,address(0),uint256(1))));
        }
        require(!rejectNFT,"reject NFT");
        return IERC721Receiver.onERC721Received.selector;
    }
    receive() external payable {}
}

/// @dev TEST ONLY authorized configuration changes in a payment callback. The
/// verified implementation captures current payment terms before this callback.
contract SeaDropPayeeMutationFixture {
    SeaDropConformingNFTFixture public immutable nft;
    bool public mutate;
    RuntimePublicDrop private futureDrop;
    address public nextPayee;
    constructor(SeaDropConformingNFTFixture collection){nft=collection;}
    function configure(RuntimePublicDrop calldata drop) external {nft.configure(drop);}
    function creator(address payee) external {nft.creator(payee);}
    function fee(address recipient,bool allowed) external {nft.fee(recipient,allowed);}
    function arm(RuntimePublicDrop calldata drop,address futurePayee) external {
        futureDrop=drop;nextPayee=futurePayee;mutate=true;
    }
    receive() external payable {
        if(mutate){mutate=false;nft.configure(futureDrop);nft.creator(nextPayee);}
    }
}

/// @notice Executes the exact deployed SeaDrop V1 runtime with a deliberately
/// isolated conforming token fixture. This is stronger than a replacement mint
/// mock, but does not assert OpenSea custom onboarding or complete PoPL behavior.
contract SeaDropActualRuntimeTest is Test {
    IVerifiedSeaDropRuntime private seaDrop;
    SeaDropConformingNFTFixture private nft;
    address private constant ALICE=address(0xA11CE);
    address private constant BOB=address(0xB0B);
    address private constant CREATOR=address(0xCAFE);
    address private constant FEE=address(0xFEE);
    uint256 private constant PRICE=0.05 ether;

    function setUp() public {
        vm.chainId(4663);vm.warp(1_000_000);
        seaDrop=IVerifiedSeaDropRuntime(VerifiedSeaDropV1.install(vm));
        nft=new SeaDropConformingNFTFixture(address(seaDrop));
        nft.configure(_drop());nft.creator(CREATOR);nft.fee(FEE,true);
        vm.deal(ALICE,100 ether);
    }
    function _drop() private view returns(RuntimePublicDrop memory) {
        return RuntimePublicDrop(uint80(PRICE),uint48(block.timestamp),uint48(block.timestamp+1 days),20,1000,true);
    }
    function _mint(address recipient,uint256 quantity,uint256 value) private {
        vm.prank(recipient);seaDrop.mintPublic{value:value}(address(nft),FEE,address(0),quantity);
    }
    function _assertUnminted() private view {
        assertEq(nft.mintedCount(),0);assertEq(nft.mintedBy(ALICE),0);assertEq(nft.syntheticDraws(),0);
        assertEq(ALICE.balance,100 ether);assertEq(FEE.balance,0);assertEq(CREATOR.balance,0);
        assertEq(uint256(vm.load(address(seaDrop),bytes32(0))),1);
    }

    function testExactDeployedRuntimeAndConstructorGuardAreInstalled() public view {
        assertEq(address(seaDrop).code.length,21081);
        assertEq(address(seaDrop).codehash,0x53e4b9339cf624803c9a7d0195576cca5b917920813508d86b3eb93dcbabeb5c);
        assertEq(uint256(vm.load(address(seaDrop),bytes32(0))),1);
    }
    function testPaidBatchPreservesExactGrossNetAndLifetimeStats() public {
        _mint(ALICE,3,3*PRICE);
        assertEq(nft.mintedCount(),3);assertEq(nft.syntheticDraws(),3);assertEq(nft.mintedBy(ALICE),3);
        assertEq(nft.ownerOf(1),ALICE);assertEq(nft.ownerOf(3),ALICE);
        assertEq(ALICE.balance,100 ether-3*PRICE);assertEq(FEE.balance,0.015 ether);assertEq(CREATOR.balance,0.135 ether);
        assertEq(address(seaDrop).balance,0);
        vm.prank(ALICE);nft.transferFrom(ALICE,BOB,1);
        (uint256 lifetime,uint256 total,uint256 maximum)=nft.getMintStats(ALICE);
        assertEq(lifetime,3);assertEq(total,3);assertEq(maximum,1000);
    }
    function testUnderpaymentOverpaymentAndZeroQuantityRevertWithoutIssuance() public {
        vm.expectRevert(abi.encodeWithSignature("IncorrectPayment(uint256,uint256)",PRICE-1,PRICE));_mint(ALICE,1,PRICE-1);
        vm.expectRevert(abi.encodeWithSignature("IncorrectPayment(uint256,uint256)",PRICE+1,PRICE));_mint(ALICE,1,PRICE+1);
        vm.expectRevert(bytes4(keccak256("MintQuantityCannotBeZero()")));_mint(ALICE,0,0);
        _assertUnminted();
    }
    function testPublicStageStartsAndEndsInclusively() public {
        RuntimePublicDrop memory drop=_drop();drop.startTime+=100;drop.endTime=drop.startTime+100;nft.configure(drop);
        vm.expectRevert(abi.encodeWithSignature("NotActive(uint256,uint256,uint256)",block.timestamp,drop.startTime,drop.endTime));
        _mint(ALICE,1,PRICE);
        vm.warp(drop.startTime);_mint(ALICE,1,PRICE);
        vm.warp(drop.endTime);_mint(ALICE,1,PRICE);
        vm.warp(uint256(drop.endTime)+1);
        vm.expectRevert(abi.encodeWithSignature("NotActive(uint256,uint256,uint256)",block.timestamp,drop.startTime,drop.endTime));
        _mint(ALICE,1,PRICE);
        assertEq(nft.mintedCount(),2);
    }
    function testWalletQuotaRemainsConsumedAfterTransfer() public {
        RuntimePublicDrop memory drop=_drop();drop.maxTotalMintableByWallet=1;nft.configure(drop);
        _mint(ALICE,1,PRICE);vm.prank(ALICE);nft.transferFrom(ALICE,BOB,1);
        vm.expectRevert(abi.encodeWithSignature("MintQuantityExceedsMaxMintedPerWallet(uint256,uint256)",2,1));_mint(ALICE,1,PRICE);
        assertEq(nft.mintedCount(),1);assertEq(nft.ownerOf(1),BOB);
    }
    function testUnapprovedAndZeroFeeRecipientsAreRejectedEvenForFreeMints() public {
        vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("FeeRecipientNotAllowed()")));
        seaDrop.mintPublic{value:PRICE}(address(nft),BOB,address(0),1);
        RuntimePublicDrop memory drop=_drop();drop.mintPrice=0;nft.configure(drop);
        vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("FeeRecipientCannotBeZeroAddress()")));
        seaDrop.mintPublic(address(nft),address(0),address(0),1);
        _assertUnminted();
    }
    function testNonpayerRecipientNeedsExplicitPayerAdmissionAndStatsFollowRecipient() public {
        vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("PayerNotAllowed()")));
        seaDrop.mintPublic{value:PRICE}(address(nft),FEE,BOB,1);
        nft.payer(ALICE,true);vm.prank(ALICE);seaDrop.mintPublic{value:PRICE}(address(nft),FEE,BOB,1);
        assertEq(nft.ownerOf(1),BOB);assertEq(nft.mintedBy(BOB),1);assertEq(nft.mintedBy(ALICE),0);
        nft.payer(ALICE,false);vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("PayerNotAllowed()")));
        seaDrop.mintPublic{value:PRICE}(address(nft),FEE,BOB,1);
    }
    function testFreeMintSkipsCreatorPayoutAndRequiresNoFinalSettlementCallback() public {
        SeaDropConformingNFTFixture freeNFT=new SeaDropConformingNFTFixture(address(seaDrop));
        RuntimePublicDrop memory drop=_drop();drop.mintPrice=0;freeNFT.configure(drop);freeNFT.fee(FEE,true);
        vm.prank(ALICE);seaDrop.mintPublic(address(freeNFT),FEE,address(0),2);
        assertEq(freeNFT.mintedCount(),2);assertEq(freeNFT.syntheticDraws(),2);
        assertEq(seaDrop.getCreatorPayoutAddress(address(freeNFT)),address(0));
        assertEq(FEE.balance,0);assertEq(ALICE.balance,100 ether);
    }
    function testMissingCreatorPayoutRollsBackEntireBatchAndSyntheticDraws() public {
        SeaDropConformingNFTFixture other=new SeaDropConformingNFTFixture(address(seaDrop));
        other.configure(_drop());other.fee(FEE,true);
        vm.prank(ALICE);vm.expectRevert(bytes4(keccak256("CreatorPayoutAddressCannotBeZeroAddress()")));
        seaDrop.mintPublic{value:2*PRICE}(address(other),FEE,address(0),2);
        assertEq(other.mintedCount(),0);assertEq(other.syntheticDraws(),0);assertEq(other.mintedBy(ALICE),0);
        _assertUnminted();
    }
    function testRejectingFeeRecipientRollsBackNFTBatchDrawsValueAndGuard() public {
        SeaDropRejectsETHFixture bad=new SeaDropRejectsETHFixture();nft.fee(address(bad),true);
        vm.prank(ALICE);vm.expectRevert();seaDrop.mintPublic{value:2*PRICE}(address(nft),address(bad),address(0),2);
        assertEq(address(bad).balance,0);_assertUnminted();
    }
    function testRejectingCreatorRollsBackAlreadyTransferredFeeAndAllMintState() public {
        SeaDropRejectsETHFixture bad=new SeaDropRejectsETHFixture();nft.creator(address(bad));
        vm.expectRevert();_mint(ALICE,2,2*PRICE);
        assertEq(address(bad).balance,0);_assertUnminted();
    }
    function testRejectingNFTReceiverRollsBackBatchAndDraws() public {
        SeaDropReceiverFixture receiver=new SeaDropReceiverFixture(address(seaDrop),nft,FEE);
        receiver.behavior(true,false);vm.deal(address(receiver),PRICE);
        vm.expectRevert();receiver.mint(1,PRICE);
        assertEq(address(receiver).balance,PRICE);assertEq(nft.mintedBy(address(receiver)),0);_assertUnminted();
    }
    function testAllBatchStatsPrecedeCallbacksAndRealSeaDropBlocksNestedMint() public {
        SeaDropReceiverFixture receiver=new SeaDropReceiverFixture(address(seaDrop),nft,FEE);
        receiver.behavior(false,true);vm.deal(address(receiver),4*PRICE);
        receiver.mint(2,2*PRICE);
        assertTrue(receiver.observedBatchStats());assertFalse(receiver.reentrySucceeded());
        assertEq(nft.mintedBy(address(receiver)),2);assertEq(nft.mintedCount(),2);assertEq(nft.syntheticDraws(),2);
        assertEq(address(receiver).balance,2*PRICE);
    }
    function testAuthorizedFeeCallbackChangesOnlyFuturePriceAndPayee() public {
        SeaDropPayeeMutationFixture actor=new SeaDropPayeeMutationFixture(nft);
        nft.fee(address(actor),true);nft.transferOwner(address(actor));
        RuntimePublicDrop memory future=_drop();future.mintPrice=uint80(PRICE*2);future.feeBps=2000;
        actor.arm(future,BOB);
        vm.prank(ALICE);seaDrop.mintPublic{value:PRICE}(address(nft),address(actor),address(0),1);
        assertEq(nft.mintedCount(),1);assertEq(address(actor).balance,0.005 ether);
        assertEq(CREATOR.balance,0.045 ether);assertEq(BOB.balance,0);
        assertEq(seaDrop.getPublicDrop(address(nft)).mintPrice,PRICE*2);
        assertEq(seaDrop.getCreatorPayoutAddress(address(nft)),BOB);
    }
    function testCreatorAndFeeConfigurationRejectInvalidValues() public {
        vm.expectRevert(bytes4(keccak256("CreatorPayoutAddressCannotBeZeroAddress()")));nft.creator(address(0));
        RuntimePublicDrop memory drop=_drop();drop.feeBps=10001;
        vm.expectRevert(abi.encodeWithSignature("InvalidFeeBps(uint256)",10001));nft.configure(drop);
        vm.expectRevert(bytes4(keccak256("DuplicateFeeRecipient()")));nft.fee(FEE,true);
        vm.expectRevert(bytes4(keccak256("FeeRecipientNotPresent()")));nft.fee(BOB,false);
    }
}
