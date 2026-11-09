// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {IZZZSeaDrop,INonFungibleSeaDropToken,PublicDrop,AllowListData} from "./interfaces/IZZZSeaDrop.sol";

interface ISeaDropMintCollection {
    function access() external view returns(address);
    function mintedCount() external view returns(uint256);
    function royaltyRewards() external view returns(address);
}
interface ISeaDropMintRoyaltyEnd {
    function mintEnd() external view returns(uint64);
    function mintEndRevision() external view returns(uint64);
}

/// @notice Fixed NFT-only mint bookkeeping and reviewed SeaDrop configuration.
/// Never receives proceeds, requests randomness, mints NFTs or executes calls.
/// SeaDrop's atomic mint-and-payment transaction owns payout rollback. This
/// helper's lock spans the NFT callback only, not subsequent fee/payee callbacks.
contract ZZZSeaDropMint is ZZZModule {
    uint256 public constant MINT_INTEGRATION_VERSION = 1;
    uint256 public constant MAX_SUPPLY = 1000;
    uint256 public constant MAX_BATCH_ENGINEERING = 10;
    uint256 public constant MAX_PAYERS_ENGINEERING = 16;
    uint8 public constant TEAM = 1;
    uint8 public constant ALLOWLIST = 2;
    uint8 public constant PUBLIC = 3;

    struct MintConfig {
        uint16 teamAllocation;
        uint16 allowlistAllocation;
        uint16 publicWalletLimit;
        uint16 feeBps;
        uint8 maxBatch;
        uint48 teamStart;
        uint48 teamEnd;
        uint48 allowlistStart;
        uint48 allowlistEnd;
        uint48 publicStart;
        uint48 publicEnd;
        bool releaseUnusedTeamToPublic;
        bytes32 merkleRoot;
        address feeRecipient;
        bytes32 allowedPayersHash;
    }

    address public immutable nft;
    address public immutable seaDrop;
    bytes32 public immutable seaDropCodeHash;
    MintConfig private settings;
    bool public configured;
    bool public minting;
    uint64 public revision;
    bytes32 public configurationReviewHash;
    uint128 public reviewedMintPrice;
    uint256 public totalMinted;
    mapping(uint8 => uint256) public phaseMinted;
    mapping(address => uint256) public lifetimeMinted;
    mapping(address => uint256) public allowlistMinted;
    mapping(uint256 => address) public originalMintRecipient;
    mapping(uint256 => uint8) public mintStage;
    bytes32 private pendingFingerprint;
    address public activeRecipient;

    event MintConfigurationReviewed(uint64 revision,bytes32 configurationHash,bytes32 reviewHash);
    event SeaDropConfigurationChanging(uint64 revision);
    event MintBatchRecorded(address indexed recipient,uint8 indexed phase,uint256 firstOrdinal,uint256 quantity);

    constructor(address controller,address collection,address seaDropImplementation,bytes32 expectedCodeHash)
        ZZZModule(controller) {
        if(collection.code.length==0 || ISeaDropMintCollection(collection).access()!=controller ||
            ISeaDropMintCollection(collection).mintedCount()!=0 || seaDropImplementation.code.length==0 ||
            expectedCodeHash==bytes32(0) || seaDropImplementation.codehash!=expectedCodeHash ||
            access.protocolPolicy().code.length==0) revert InvalidConfiguration();
        nft=collection;seaDrop=seaDropImplementation;seaDropCodeHash=expectedCodeHash;
    }

    modifier onlyNFT() { if(msg.sender!=nft)revert Unauthorized();_; }

    function mintConfig() external view returns(MintConfig memory) { return settings; }

    /// @notice Fixed helper verifies its own constructor-bound graph, avoiding
    /// duplicate encoders in the size-constrained NFT's one-time bind setter.
    function validateBinding() external view onlyNFT {
        address boundNFT=access.module(Ids.NFT);
        if(access.isSealed() || ISeaDropMintCollection(nft).mintedCount()!=0 || totalMinted!=0 || minting ||
            (boundNFT!=address(0) && boundNFT!=nft) || seaDrop.codehash!=seaDropCodeHash)
            revert InvalidConfiguration();
    }

    /// @notice Future configuration; historical per-phase counts never reset.
    /// No external drop is changed here: NFT-keyed typed setters synchronize it.
    function configure(MintConfig calldata next,uint128 expectedMintPrice,bytes32 reviewHash)
        external onlyGovernance operating principalOperating {
        if(minting || reviewHash==bytes32(0) || uint256(next.teamAllocation)+next.allowlistAllocation>MAX_SUPPLY ||
            next.teamAllocation<phaseMinted[TEAM] || next.allowlistAllocation<phaseMinted[ALLOWLIST] ||
            next.publicWalletLimit==0 || next.publicWalletLimit>MAX_SUPPLY || next.feeBps>10000 ||
            next.maxBatch==0 || next.maxBatch>MAX_BATCH_ENGINEERING || next.feeRecipient==address(0) ||
            (next.merkleRoot==bytes32(0) && (next.teamAllocation!=0 || next.allowlistAllocation!=0)) ||
            next.allowedPayersHash==bytes32(0) ||
            next.teamStart==0 || next.teamStart>next.teamEnd ||
            next.teamEnd>=next.allowlistStart || next.allowlistStart>next.allowlistEnd ||
            next.allowlistEnd>=next.publicStart || next.publicStart>next.publicEnd ||
            (!next.releaseUnusedTeamToPublic && totalMinted>MAX_SUPPLY-(next.teamAllocation-phaseMinted[TEAM])))
            revert InvalidConfiguration();
        uint128 price=IZZZProtocolPolicy(access.protocolPolicy()).salePolicy().mintPrice;
        if(price==0 || price!=expectedMintPrice || price>type(uint80).max)revert InvalidConfiguration();
        // An unchanged CURRENT root cannot silently acquire different leaf
        // meanings. This catches operator mistakes, not malicious initial roots
        // or reuse of older roots after intervening configurations. Those remain
        // explicit source-bound manifest/builder review obligations.
        if(configured && next.merkleRoot!=bytes32(0) && next.merkleRoot==settings.merkleRoot &&
            _leafTerms(next,price)!=_leafTerms(settings,reviewedMintPrice))revert InvalidConfiguration();
        settings=next;configured=true;configurationReviewHash=reviewHash;reviewedMintPrice=price;++revision;
        emit MintConfigurationReviewed(revision,configurationHash(),reviewHash);
    }

    /// @notice Prepare one of the fixed NFT-keyed configuration calls. The
    /// caller is authenticated by the fixed NFT forwarding its actual caller.
    /// No target, value or arbitrary selector is accepted or returned.
    function prepareUpdate(address caller,bytes calldata originalData)
        external onlyNFT operating principalOperating returns(bytes memory encoded) {
        if(!access.canConfigure(caller))revert Unauthorized();
        if(minting || originalData.length<4 || seaDrop.codehash!=seaDropCodeHash)revert InvalidState();
        bytes4 selector=bytes4(originalData[:4]);
        address implementation;
        if(selector==INonFungibleSeaDropToken.updatePublicDrop.selector) {
            PublicDrop memory value;
            (implementation,value)=abi.decode(originalData[4:],(address,PublicDrop));
            encoded=abi.encodeCall(IZZZSeaDrop.updatePublicDrop,(value));
        } else if(selector==INonFungibleSeaDropToken.updateAllowList.selector) {
            AllowListData memory value;
            (implementation,value)=abi.decode(originalData[4:],(address,AllowListData));
            encoded=abi.encodeCall(IZZZSeaDrop.updateAllowList,(value));
        } else if(selector==INonFungibleSeaDropToken.updateDropURI.selector) {
            string memory value;
            (implementation,value)=abi.decode(originalData[4:],(address,string));
            encoded=abi.encodeCall(IZZZSeaDrop.updateDropURI,(value));
        } else if(selector==INonFungibleSeaDropToken.updateCreatorPayoutAddress.selector) {
            address value;
            (implementation,value)=abi.decode(originalData[4:],(address,address));
            if(value!=IZZZProtocolPolicy(access.protocolPolicy()).salePolicy().recipient)revert InvalidConfiguration();
            encoded=abi.encodeCall(IZZZSeaDrop.updateCreatorPayoutAddress,(value));
        } else if(selector==INonFungibleSeaDropToken.updateAllowedFeeRecipient.selector) {
            address value;bool allowed;
            (implementation,value,allowed)=abi.decode(originalData[4:],(address,address,bool));
            encoded=abi.encodeCall(IZZZSeaDrop.updateAllowedFeeRecipient,(value,allowed));
        } else if(selector==INonFungibleSeaDropToken.updatePayer.selector) {
            address value;bool allowed;
            (implementation,value,allowed)=abi.decode(originalData[4:],(address,address,bool));
            encoded=abi.encodeCall(IZZZSeaDrop.updatePayer,(value,allowed));
        } else revert InvalidConfiguration();
        if(implementation!=seaDrop)revert InvalidConfiguration();
        ++revision;emit SeaDropConfigurationChanging(revision);
    }

    /// @notice Reserve the COMPLETE batch before VRF/receiver callbacks. These
    /// stats are issuance counts, never balances or present NFT owners.
    function beginMint(address caller,address recipient,uint256 quantity)
        external onlyNFT live operating principalOperating returns(uint256 firstOrdinal,bytes32 fingerprint,uint8 phase) {
        if(caller!=seaDrop || seaDrop.codehash!=seaDropCodeHash)revert Unauthorized();
        if(minting || !configured || recipient==address(0) || quantity==0 || quantity>settings.maxBatch ||
            totalMinted!=ISeaDropMintCollection(nft).mintedCount() || totalMinted+quantity>MAX_SUPPLY ||
            access.module(Ids.NFT)!=nft)revert InvalidState();
        phase=currentPhase();
        if(phase==0)revert NotReady();
        if(phase==TEAM) {
            if(phaseMinted[TEAM]+quantity>settings.teamAllocation)revert InvalidState();
        } else if(phase==ALLOWLIST) {
            if(phaseMinted[ALLOWLIST]+quantity>settings.allowlistAllocation || allowlistMinted[recipient]+quantity>1)
                revert InvalidState();
        } else {
            uint256 ceiling=MAX_SUPPLY;
            if(!settings.releaseUnusedTeamToPublic)ceiling-=settings.teamAllocation-phaseMinted[TEAM];
            if(totalMinted+quantity>ceiling || lifetimeMinted[recipient]+quantity>settings.publicWalletLimit)
                revert InvalidState();
        }
        fingerprint=_validatedFingerprint();
        firstOrdinal=totalMinted+1;
        totalMinted+=quantity;lifetimeMinted[recipient]+=quantity;phaseMinted[phase]+=quantity;
        if(phase==ALLOWLIST)allowlistMinted[recipient]+=quantity;
        for(uint256 ordinal=firstOrdinal;ordinal<firstOrdinal+quantity;++ordinal) {
            originalMintRecipient[ordinal]=recipient;mintStage[ordinal]=phase;
        }
        minting=true;pendingFingerprint=fingerprint;activeRecipient=recipient;
        emit MintBatchRecorded(recipient,phase,firstOrdinal,quantity);
    }

    function finishMint(bytes32 fingerprint) external onlyNFT live operating principalOperating {
        if(!minting || fingerprint==bytes32(0) || fingerprint!=pendingFingerprint ||
            fingerprint!=_validatedFingerprint() || totalMinted!=ISeaDropMintCollection(nft).mintedCount())
            revert InvalidState();
        minting=false;delete pendingFingerprint;delete activeRecipient;
    }

    /// @notice Fixed NFT validates the Vault's in-flight issuance review. This
    /// is a recipient proof only; it neither mints nor releases any funds.
    function validateMintReview(bytes32 fingerprint) external view onlyNFT returns(address) {
        if(!minting || fingerprint==bytes32(0) || fingerprint!=pendingFingerprint)revert InvalidState();
        return activeRecipient;
    }

    function activeFingerprint() external view returns(bytes32) { return pendingFingerprint; }

    /// @notice Canonical V10 restores original issuance, not current ownership.
    /// Only the fixed NFT importing its ordered records can reconstruct books.
    function restoreMint(uint256 ordinal,address recipient,uint8 phase) external onlyNFT {
        if(access.canonicalState()!=2 || minting || ordinal!=totalMinted+1 || ordinal>MAX_SUPPLY ||
            ordinal>ISeaDropMintCollection(nft).mintedCount() || recipient==address(0) || phase<TEAM || phase>PUBLIC ||
            (phase==ALLOWLIST && allowlistMinted[recipient]!=0))revert InvalidState();
        originalMintRecipient[ordinal]=recipient;mintStage[ordinal]=phase;
        ++totalMinted;++lifetimeMinted[recipient];++phaseMinted[phase];
        if(phase==ALLOWLIST)++allowlistMinted[recipient];
    }

    function assertCanonicalCount() external view {
        if(minting || totalMinted!=ISeaDropMintCollection(nft).mintedCount() ||
            (configured && (phaseMinted[TEAM]>settings.teamAllocation || phaseMinted[ALLOWLIST]>settings.allowlistAllocation)))
            revert InvalidState();
    }

    function mintStats(address recipient) external view returns(uint256,uint256,uint256) {
        return(lifetimeMinted[recipient],totalMinted,MAX_SUPPLY);
    }

    /// @notice Inclusive SeaDrop timestamps require strictly disjoint windows.
    function currentPhase() public view returns(uint8) {
        MintConfig memory c=settings;
        if(!configured)return 0;
        if(block.timestamp>=c.teamStart && block.timestamp<=c.teamEnd)return TEAM;
        if(block.timestamp>=c.allowlistStart && block.timestamp<=c.allowlistEnd)return ALLOWLIST;
        if(block.timestamp>=c.publicStart && block.timestamp<=c.publicEnd)return PUBLIC;
        return 0;
    }

    function configurationHash() public view returns(bytes32) {
        return keccak256(abi.encode(address(this),address(access),nft,seaDrop,seaDropCodeHash,
            settings,reviewedMintPrice,revision,configurationReviewHash));
    }

    /// @notice Semantic handoff comparison excludes local addresses/revisions.
    /// SeaDrop address/runtime are compared separately by the NFT codec.
    function configurationValuesHash() external view returns(bytes32) {
        return keccak256(abi.encode(configured,settings,reviewedMintPrice));
    }

    function expectedPublicDrop() public view returns(PublicDrop memory) {
        uint128 price=IZZZProtocolPolicy(access.protocolPolicy()).salePolicy().mintPrice;
        if(price==0 || price!=reviewedMintPrice || price>type(uint80).max)revert InvalidConfiguration();
        MintConfig memory c=settings;
        return PublicDrop(uint80(price),c.publicStart,c.publicEnd,c.publicWalletLimit,c.feeBps,true);
    }

    /// @dev The callback ABI has no price/stage/fee arguments. The immutable
    /// reviewed SeaDrop validates actual payments and Merkle leaves. Reviewed
    /// manifests must contain ONLY free-team and same-price allowlist leaves in
    /// their matching windows; inspecting public-drop getters cannot prove which
    /// upstream entry point was called or repair an incorrectly approved root.
    function _validatedFingerprint() private view returns(bytes32) {
        IZZZSeaDrop drop=IZZZSeaDrop(seaDrop);
        MintConfig memory c=settings;
        IZZZProtocolPolicy policy=IZZZProtocolPolicy(access.protocolPolicy());
        ISeaDropMintRoyaltyEnd royalties=ISeaDropMintRoyaltyEnd(ISeaDropMintCollection(nft).royaltyRewards());
        PublicDrop memory actual=drop.getPublicDrop(nft);
        address[] memory feeRecipients=drop.getAllowedFeeRecipients(nft);
        if(seaDrop.codehash!=seaDropCodeHash || keccak256(abi.encode(actual))!=keccak256(abi.encode(expectedPublicDrop())) ||
            drop.getCreatorPayoutAddress(nft)!=policy.salePolicy().recipient ||
            drop.getAllowListMerkleRoot(nft)!=c.merkleRoot || feeRecipients.length!=1 ||
            feeRecipients[0]!=c.feeRecipient || !drop.getFeeRecipientIsAllowed(nft,c.feeRecipient) ||
            _payersHash(drop.getPayers(nft))!=c.allowedPayersHash ||
            drop.getSigners(nft).length!=0 || drop.getTokenGatedAllowedTokens(nft).length!=0 ||
            royalties.mintEnd()!=c.publicEnd)revert InvalidConfiguration();
        return keccak256(abi.encode(keccak256("ZZZ_SEADROP_MINT_V1"),configurationHash(),
            policy.mintFingerprint(),address(royalties),royalties.mintEnd(),royalties.mintEndRevision()));
    }

    /// @dev Enumeration order is not authority. Canonicalize the bounded list
    /// so removing/re-adding the same reviewed payer cannot change semantics.
    function _payersHash(address[] memory payers) private pure returns(bytes32) {
        if(payers.length>MAX_PAYERS_ENGINEERING)revert InvalidConfiguration();
        for(uint256 i;i<payers.length;++i) {
            address value=payers[i];
            if(value==address(0))revert InvalidConfiguration();
            uint256 j=i;
            while(j!=0 && uint160(payers[j-1])>uint160(value)) {
                payers[j]=payers[j-1];--j;
            }
            if(j!=0 && payers[j-1]==value)revert InvalidConfiguration();
            payers[j]=value;
        }
        return keccak256(abi.encode(payers));
    }

    function _leafTerms(MintConfig memory c,uint128 price) private pure returns(bytes32) {
        bytes32 teamTerms;
        bytes32 allowlistTerms;
        if(c.teamAllocation!=0)teamTerms=keccak256(abi.encode(c.teamAllocation,c.teamStart,c.teamEnd));
        if(c.allowlistAllocation!=0)allowlistTerms=keccak256(abi.encode(price,c.feeBps,
            uint256(c.teamAllocation)+c.allowlistAllocation,c.allowlistStart,c.allowlistEnd));
        return keccak256(abi.encode(teamTerms,allowlistTerms));
    }
}
