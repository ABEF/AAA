// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";
import {Ids,PositionStatus} from "./libraries/ZZZTypes.sol";
import {CanonicalNFTHeader, CanonicalNFTRecord, IZZZNFTCanonicalState} from "./interfaces/IZZZNFTCanonical.sol";
import {IZZZAccess,IZZZVault} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
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
interface INFTLifecycleSuccessor {
    function canonicalSuccessor() external view returns(address controller,address replacementNFT);
}
interface INFTLifecyclePrincipal {
    function exitPhase() external view returns(uint8);
    function principalOf(uint256 id) external view returns(uint256 ethAmount,uint256 zzzAmount,bool allocated,bool paid);
}

/// @notice Seal-bound NFT state codec. It has no custody or independent economic
/// authority; typed writes are usable only by the fixed handoff while importing.
contract ZZZNFTCanonical is ZZZModule {
    struct Lifecycle {
        uint256 flags;
        uint256 ethAmount;
        uint256 zzzAmount;
        address successorController;
        address successorNFT;
    }
    IZZZNFTCanonicalState public immutable nft;
    uint256 private cursor;
    constructor(address controller, address collection) ZZZModule(controller) {
        if (collection.code.length == 0 || IZZZNFTCanonicalState(collection).access() != controller) revert InvalidConfiguration();
        nft = IZZZNFTCanonicalState(collection);
    }
    /// @notice Price-free schema2 lifecycle lens for this immutable collection.
    /// This reads existing books only; it neither authorizes work nor changes
    /// canonical records, custody, accounting or the handoff state machine.
    /// Flags: version0..7, canonical8..15, exit16..23, position24..31;
    /// preparing32, exit-started33, shares34, allocated35, paid36.
    function metadataLifecycleState(uint256 id) external view returns(
        uint256 flags,uint256 ethAmount,uint256 zzzAmount,address successorController,address successorNFT) {
        return _metadataLifecycleState(id);
    }
    /// @notice Same single price-free read, with schema2 machine fields and a
    /// human lifecycle label. Block/time identify this read, not price freshness.
    function metadataLifecycleContext(uint256 id) external view returns(bytes memory context,string memory label,
        uint256 flags,uint256 ethAmount,uint256 zzzAmount) {
        Lifecycle memory value;
        (value.flags,value.ethAmount,value.zzzAmount,value.successorController,value.successorNFT)=_metadataLifecycleState(id);
        return (_context(value),_lifecycleLabel(value),value.flags,value.ethAmount,value.zzzAmount);
    }
    function _metadataLifecycleState(uint256 id) private view returns(
        uint256 flags,uint256 ethAmount,uint256 zzzAmount,address successorController,address successorNFT) {
        if(access.module(Ids.NFT)!=address(nft))revert InvalidConfiguration();
        nft.ownerOf(id);
        uint8 canonical=access.canonicalState();
        if(canonical>4)revert InvalidConfiguration();
        IZZZVault vault=IZZZVault(access.module(Ids.VAULT));
        flags=2 | (uint256(canonical)<<8) | (uint256(vault.nftStatus(id))<<24);
        if(access.preparationActive())flags|=1<<32;
        bool hasShares=vault.sharesOf(id)!=0;
        if(hasShares)flags|=1<<34;
        if(access.lpExitStarted()) {
            flags|=1<<33;
            INFTLifecyclePrincipal settlement=INFTLifecyclePrincipal(access.module(Ids.MIGRATION));
            uint8 phase=settlement.exitPhase();bool allocated;bool paid;
            (ethAmount,zzzAmount,allocated,paid)=settlement.principalOf(id);
            if(canonical!=0 || phase==0 || phase>3 || (allocated && phase==1) ||
                (!allocated && (ethAmount!=0 || zzzAmount!=0)) ||
                (!hasShares && (ethAmount!=0 || zzzAmount!=0)) ||
                (paid && (!allocated || phase!=3 || (ethAmount==0 && zzzAmount==0))))revert InvalidConfiguration();
            flags|=uint256(phase)<<16;
            if(allocated)flags|=1<<35;
            if(paid)flags|=1<<36;
        }
        if(canonical==3) {
            (successorController,successorNFT)=INFTLifecycleSuccessor(address(nft)).canonicalSuccessor();
            if(successorController==address(0) || successorNFT==address(0))revert InvalidConfiguration();
        }
    }
    function _canonical(Lifecycle memory value) private pure returns(uint8){return uint8(value.flags>>8);}
    function _phase(Lifecycle memory value) private pure returns(uint8){return uint8(value.flags>>16);}
    function _position(Lifecycle memory value) private pure returns(PositionStatus){return PositionStatus(uint8(value.flags>>24));}
    function _flag(Lifecycle memory value,uint8 bit) private pure returns(bool){return (value.flags&(uint256(1)<<bit))!=0;}
    function _context(Lifecycle memory value) private view returns(bytes memory) {
        bytes memory json="";
        json=_field(json,"metadata_schema","2");
        json=_field(json,"metadata_snapshot_block",Strings.toString(block.number));
        json=_field(json,"metadata_snapshot_timestamp",Strings.toString(block.timestamp));
        json=_field(json,"canonical_state",Strings.toString(_canonical(value)));
        json=_field(json,"replacement_preparing",_flag(value,32)?"true":"false");
        json=_field(json,"successor_controller",_addressOrNull(value.successorController));
        json=_field(json,"successor_nft",_addressOrNull(value.successorNFT));
        json=_field(json,"collection_lp_exit_started",_flag(value,33)?"true":"false");
        json=_field(json,"collection_exit_phase",Strings.toString(_phase(value)));
        json=_field(json,"activation_closed",(_flag(value,33) || _canonical(value)==3 || _canonical(value)==4)?"true":"false");
        json=_field(json,"principal_return_status",_quoted(_principalStatus(value)));
        json=_field(json,"principal_allocated",_flag(value,35)?"true":"false");
        return _field(json,"principal_paid",_flag(value,36)?"true":"false");
    }
    function _field(bytes memory json,string memory key,string memory value) private pure returns(bytes memory) {
        return _append(_append(_append(_append(json,bytes(',"')),bytes(key)),bytes('":')),bytes(value));
    }
    function _append(bytes memory left,bytes memory right) private pure returns(bytes memory){return bytes.concat(left,right);}
    function _quoted(string memory value) private pure returns(string memory){return string(_append(_append(bytes('"'),bytes(value)),bytes('"')));}
    function _addressOrNull(address value) private pure returns(string memory){return value==address(0)?"null":_quoted(Strings.toHexString(value));}
    function _principalStatus(Lifecycle memory value) private pure returns(string memory) {
        if(_canonical(value)!=0)return "unavailable_on_this_deployment";
        if(!_flag(value,34))return "not_applicable";
        if(!_flag(value,33))return "not_started";
        if(!_flag(value,35))return "awaiting_allocation";
        if(_flag(value,36))return "paid";
        if(value.ethAmount==0 && value.zzzAmount==0)return "zero_entitlement";
        return _phase(value)==3?"payable":"allocated_pending_readiness";
    }
    function _lifecycleLabel(Lifecycle memory value) private pure returns(string memory) {
        if(_canonical(value)==1)return "Replacement frozen";
        if(_canonical(value)==2)return "Replacement importing";
        if(_canonical(value)==3)return "Replaced";
        if(_canonical(value)==4)return "Cancelled import";
        if(_flag(value,32))return "Replacement preparing";
        if(_flag(value,33) && !_flag(value,34))return "Activation closed";
        if(_position(value)==PositionStatus.Exited)return "LP exited";
        if(_flag(value,33))return "LP exit in progress";
        if(_position(value)==PositionStatus.Parked)return "LP parked";
        return _flag(value,34)?"Operating":"Awaiting activation";
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
