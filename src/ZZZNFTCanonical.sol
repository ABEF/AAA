// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {CanonicalNFTHeader, CanonicalNFTRecord, IZZZNFTCanonicalState} from "./interfaces/IZZZNFTCanonical.sol";
import {IZZZAccess} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
interface INFTPolicyHandoff {
    function incomingSource() external view returns(address);
    function destinationController() external view returns(address);
}
interface INFTMintPolicy {
    function nft() external view returns(address);
    function access() external view returns(address);
    function MINT_INTEGRATION_VERSION() external view returns(uint256);
    function configurationValuesHash() external view returns(bytes32);
    function configurationHash() external view returns(bytes32);
    function seaDrop() external view returns(address);
    function seaDropCodeHash() external view returns(bytes32);
    function originalMintRecipient(uint256) external view returns(address);
    function assertCanonicalCount() external view;
}

/// @notice Seal-bound NFT state codec. It has no custody or independent economic
/// authority; typed writes are usable only by the fixed handoff while importing.
contract ZZZNFTCanonical is ZZZModule {
    IZZZNFTCanonicalState public immutable nft;
    uint256 private cursor;
    constructor(address controller, address collection) ZZZModule(controller) {
        if (collection.code.length == 0 || IZZZNFTCanonicalState(collection).access() != controller) revert InvalidConfiguration();
        nft = IZZZNFTCanonicalState(collection);
    }
    function canonicalCapture() external onlyHandoff {
        _sameMetadataPolicy();
        _mintCount();
        uint256 count = nft.mintedCount();
        if (nft.nextToFinalize() != count + 1 || nft.remainingToReveal() != 1000 - count ||
            uint256(nft.rarityRemaining(0)) + nft.rarityRemaining(1) + nft.rarityRemaining(2) != nft.remainingToReveal()) revert InvalidState();
    }
    function canonicalSettle() external onlyHandoff {}
    function canonicalCount() public view returns (uint256) { return 1001 + nft.mintedCount(); }
    function canonicalExport(uint256 row) external view returns (bytes memory) {
        if ((access.canonicalState() != 1 && access.canonicalState() != 3) || row >= canonicalCount()) revert InvalidState();
        if (row == 0) {
            uint16[3] memory quotas = [nft.rarityRemaining(0), nft.rarityRemaining(1), nft.rarityRemaining(2)];
            return abi.encode(CanonicalNFTHeader(nft.mintedCount(),nft.nextToFinalize(),nft.remainingToReveal(),
                quotas,nft.randomnessEpoch(),nft.artworkBaseURI()));
        }
        uint256 count = nft.mintedCount();
        if (row <= count) {
            uint256 id = nft.tokenAtOrdinal(row);
            (uint256 actualId,uint256 rarityWord,uint256 colorWord,bool requested,bool fulfilled) = nft.canonicalRandomness(id);
            address originalRecipient=nft.originalMintRecipient(id);
            uint8 mintStage=nft.mintStageOf(id);
            _recordMintPolicy(row,originalRecipient,mintStage);
            if (!nft.traitsReady(id) || !requested || !fulfilled || actualId != id) revert InvalidState();
            return abi.encode(CanonicalNFTRecord(id,nft.ownerOf(id),nft.rarityOf(id),nft.colorOf(id),nft.paletteOf(id),
                nft.patternOf(id),nft.requestOf(id),nft.requestEpochOf(id),rarityWord,colorWord,originalRecipient,mintStage));
        }
        (uint8 rarity, uint256 item) = _inventoryRow(row - count - 1);
        return abi.encode(rarity,item,nft.canonicalArtwork(rarity,item));
    }
    function canonicalImport(uint256 row, bytes calldata record) external onlyHandoff {
        if (access.canonicalState() != 2 || row != cursor++) revert InvalidState();
        if (row == 0) {
            _sameMetadataPolicy();
            if (nft.mintedCount() != 0) revert InvalidState();
            CanonicalNFTHeader memory header = abi.decode(record,(CanonicalNFTHeader));
            if (header.count > 1000 || header.next != header.count + 1 || header.remaining != 1000 - header.count ||
                uint256(header.quotas[0]) + header.quotas[1] + header.quotas[2] != header.remaining ||
                header.quotas[0] > 600 || header.quotas[1] > 300 || header.quotas[2] > 100 ||
                keccak256(bytes(header.base)) != keccak256(bytes(nft.artworkBaseURI()))) revert InvalidState();
            nft.canonicalWriteHeader(header.count,header.next,header.remaining,header.quotas,header.epoch + 1);
            return;
        }
        if (row >= canonicalCount()) revert InvalidState();
        uint256 count = nft.mintedCount();
        if (row <= count) {
            CanonicalNFTRecord memory value = abi.decode(record,(CanonicalNFTRecord));
            if (value.owner == address(0) || value.rarity > 2 || value.palette >= 58 || value.pattern >= 4 ||
                value.color != ZZZArtwork.primaryColor(value.palette) || value.requestId == 0 ||
                value.requestEpoch >= nft.randomnessEpoch()) revert InvalidState();
            if(value.originalRecipient==address(0) || (nft.seaDropMint()==address(0) ? value.mintStage!=0 :
                value.mintStage<1 || value.mintStage>3))revert InvalidState();
            nft.canonicalWriteRecord(row,value); return;
        }
        (uint8 rarity,uint256 item,uint16 value) = abi.decode(record,(uint8,uint256,uint16));
        (uint8 expectedRarity,uint256 expectedItem) = _inventoryRow(row - count - 1);
        uint256 limit = rarity == 0 ? 600 : rarity == 1 ? 300 : 100;
        if (rarity != expectedRarity || item != expectedItem || value > limit) revert InvalidState();
        nft.canonicalWriteArtwork(rarity,item,value);
    }
    function _inventoryRow(uint256 row) private pure returns (uint8 rarity, uint256 item) {
        if (row < 600) return (0,row);
        if (row < 900) return (1,row - 600);
        return (2,row - 900);
    }
    function canonicalAssetCount() external pure returns (uint256) { return 0; }
    /// @notice Typed read-only extension of the V10 deployment commitment.
    /// Moving this encoding out of the size-constrained coordinator preserves
    /// every policy field and additionally pins its storage-bound mint helper.
    function deploymentConfigurationCommitment() external view returns(bytes32) {
        address policy=access.protocolPolicy();
        bytes32 policyCommitment=keccak256(abi.encode(policy,policy.codehash,
            IZZZProtocolPolicy(policy).PROTOCOL_POLICY_VERSION(),IZZZProtocolPolicy(policy).configurationHash()));
        address helper=nft.seaDropMint();
        bytes32 mintCommitment;
        if(helper!=address(0)) {
            INFTMintPolicy mintPolicy=INFTMintPolicy(helper);
            if(helper.code.length==0 || mintPolicy.nft()!=address(nft) || mintPolicy.access()!=address(access) ||
                mintPolicy.MINT_INTEGRATION_VERSION()!=1)revert InvalidConfiguration();
            mintCommitment=keccak256(abi.encode(helper,helper.codehash,mintPolicy.configurationHash(),
                mintPolicy.seaDrop(),mintPolicy.seaDropCodeHash()));
        }
        return keccak256(abi.encode(policyCommitment,helper,mintCommitment));
    }
    function canonicalValidate() external view {
        uint8 state=access.canonicalState();
        if (state == 2 && cursor != canonicalCount()) revert InvalidState();
        if(state==1 || state==2) { _sameMetadataPolicy(); _mintCount(); }
    }
    function canonicalActivate() external onlyHandoff {
        if (access.canonicalState() != 2) revert InvalidState();
        _sameMetadataPolicy();
        _mintCount();
    }
    /// @dev Keep the existing NFT record wire only when visual semantics match.
    /// Future provider policy is separately reviewed at the successor; every old
    /// draw is already final. Compare threshold values, never local revision or
    /// helper addresses, which necessarily differ between deployments.
    function _sameMetadataPolicy() private view {
        uint8 state=access.canonicalState();
        INFTPolicyHandoff handoff=INFTPolicyHandoff(access.canonicalHandoff());
        address peer=state==2 ? handoff.incomingSource() : handoff.destinationController();
        if((state!=1 && state!=2) || peer==address(0)) revert InvalidState();
        IZZZProtocolPolicy.MetadataPolicy memory local=
            IZZZProtocolPolicy(access.protocolPolicy()).metadataPolicy();
        IZZZProtocolPolicy.MetadataPolicy memory other=
            IZZZProtocolPolicy(IZZZAccess(peer).protocolPolicy()).metadataPolicy();
        if(local.enhancedUSD!=other.enhancedUSD || local.singularityUSD!=other.singularityUSD) revert InvalidConfiguration();
        _sameMintPolicy(peer);
    }
    /// @dev Preserve the original buyer's lifetime/stage books. Current owners
    /// may differ after transfers and are never used to reconstruct mint limits.
    function _recordMintPolicy(uint256 ordinal,address recipient,uint8 stage) private view {
        address helper=nft.seaDropMint();
        if(recipient==address(0))revert InvalidState();
        if(helper==address(0)) {
            if(stage!=0)revert InvalidState();
        } else if(stage<1 || stage>3 || INFTMintPolicy(helper).originalMintRecipient(ordinal)!=recipient)
            revert InvalidState();
    }
    function _mintCount() private view {
        address helper=nft.seaDropMint();
        if(helper!=address(0))INFTMintPolicy(helper).assertCanonicalCount();
    }
    function _sameMintPolicy(address peer) private view {
        address otherNFT=IZZZAccess(peer).module(Ids.NFT);
        address localHelper=nft.seaDropMint();
        address otherHelper=IZZZNFTCanonicalState(otherNFT).seaDropMint();
        if(localHelper==address(0) || otherHelper==address(0)) {
            if(localHelper!=otherHelper)revert InvalidConfiguration();
            return;
        }
        INFTMintPolicy local=INFTMintPolicy(localHelper);
        INFTMintPolicy other=INFTMintPolicy(otherHelper);
        if(local.nft()!=address(nft) || other.nft()!=otherNFT || local.access()!=address(access) || other.access()!=peer ||
            local.MINT_INTEGRATION_VERSION()!=1 || other.MINT_INTEGRATION_VERSION()!=1 ||
            local.configurationValuesHash()!=other.configurationValuesHash() || local.seaDrop()!=other.seaDrop() ||
            local.seaDropCodeHash()!=other.seaDropCodeHash())revert InvalidConfiguration();
    }
}
