// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {IZZZProtocolPolicy as P} from "./interfaces/IZZZProtocolPolicy.sol";

interface IPolicyNFT {
    function mintedCount() external view returns(uint256);
    function nextToFinalize() external view returns(uint256);
    function royaltyRewards() external view returns(address);
    function policyMetadataChanged() external;
}

/// @notice Fixed-controller, noncustodial future operating policy. Separately
/// deployed before consumers; no arbitrary execution, approval, asset transfer,
/// principal recipient, share writer or relaxation of fixed loss ceilings.
contract ZZZProtocolPolicy is ZZZModule,ReentrancyGuard {
    uint256 public constant PROTOCOL_POLICY_VERSION=1;
    uint16 public constant MAX_IDLE_BPS=4000;
    uint32 public constant MIN_CALL_GAS=100000;
    uint32 public constant MAX_CALL_GAS=1000000;
    P.EntryPolicy private entry;
    P.MaintenancePolicy private maintenance;
    P.GasPolicy private gasLimits;
    P.SalePolicy private sale;
    P.MetadataPolicy private metadata;
    P.VrfPolicy private randomness;
    uint64 public vrfRevision;
    uint64 public configurationRevision;
    bytes32 public configurationHash;
    event EntryPolicyConfigured(uint128 activationUSD,uint128 growthUSD,uint16 maxIdleBps,uint64 revision,bytes32 reviewHash);
    event MaintenancePolicyConfigured(uint16 maxIdleBps,uint64 revision,bytes32 reviewHash);
    event GasPolicyConfigured(uint32 payoutGas,uint32 sourceCallGas,uint32 royaltySyncGas,uint64 revision,bytes32 reviewHash);
    event MintPriceConfigured(uint128 previous,uint128 current,uint64 revision,bytes32 reviewHash);
    event MintRecipientProposed(address indexed current,address indexed pending,uint64 revision,bytes32 reviewHash);
    event MintRecipientAccepted(address indexed previous,address indexed current,uint64 revision);
    event EvolutionThresholdsConfigured(uint128 enhancedUSD,uint128 singularityUSD,uint64 revision,bytes32 reviewHash);
    event RandomnessConfigured(address indexed coordinator,uint64 generation,uint64 revision,bytes32 reviewHash);
    event RandomnessSettingsConfigured(uint16 confirmations,uint32 callbackGasLimit,uint64 revision,bytes32 reviewHash);

    constructor(address controller,address initialMintRecipient) ZZZModule(controller) {
        if(initialMintRecipient==address(0) || initialMintRecipient==controller || initialMintRecipient==address(this))
            revert InvalidConfiguration();
        entry=P.EntryPolicy(100e18,5e18,500,1);
        maintenance=P.MaintenancePolicy(500,1);
        gasLimits=P.GasPolicy(180000,500000,250000,1);
        sale=P.SalePolicy(uint128(0.05 ether),initialMintRecipient,address(0),1);
        metadata=P.MetadataPolicy(1000e18,10000e18,1);
        configurationHash=keccak256(abi.encode("ZZZ_PROTOCOL_POLICY_V1",block.chainid,address(this),controller,
            entry,maintenance,gasLimits,sale,metadata));
    }
    function entryPolicy() external view returns(P.EntryPolicy memory){return entry;}
    function maintenancePolicy() external view returns(P.MaintenancePolicy memory){return maintenance;}
    function gasPolicy() external view returns(P.GasPolicy memory){return gasLimits;}
    /// @notice One-word consumer reads avoid decoding the full operational
    /// tuple in tight custody modules; the complete tuple remains reviewable.
    function payoutGas() external view returns(uint32){return gasLimits.payoutGas;}
    function sourceCallGas() external view returns(uint32){return gasLimits.sourceCallGas;}
    function royaltySyncGas() external view returns(uint32){return gasLimits.royaltySyncGas;}
    function salePolicy() external view returns(P.SalePolicy memory){return sale;}
    function metadataPolicy() external view returns(P.MetadataPolicy memory){return metadata;}
    function vrfPolicy() external view returns(P.VrfPolicy memory){return randomness;}
    function entryFingerprint() external view returns(bytes32){return keccak256(abi.encode(address(this),entry));}
    function maintenanceFingerprint() external view returns(bytes32){return keccak256(abi.encode(address(this),maintenance));}
    function gasFingerprint() external view returns(bytes32){return keccak256(abi.encode(address(this),gasLimits));}
    function saleFingerprint() external view returns(bytes32){return keccak256(abi.encode(address(this),sale));}
    /// @notice A reviewed mint binds both future proceeds and the exact draw
    /// provider/settings generation. Cosmetic/read/payout policies are separate.
    function mintFingerprint() external view returns(bytes32){return keccak256(abi.encode(address(this),sale,vrfRevision,randomness));}
    function metadataFingerprint() external view returns(bytes32){return keccak256(abi.encode(address(this),metadata));}
    function _record(bytes32 domain,bytes32 value) private {
        ++configurationRevision;
        configurationHash=keccak256(abi.encode(configurationHash,domain,configurationRevision,value));
    }
    function _review(bytes32 review) private pure {if(review==bytes32(0))revert InvalidConfiguration();}

    /// @notice Changes only future contribution policy. Individual incoming
    /// budgets and actual marginal deployed-LP loss floors remain independent.
    function setEntryPolicy(uint128 activationUSD,uint128 growthUSD,uint16 maxIdleBps,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        _review(reviewHash);
        if(activationUSD<1e18 || growthUSD<1e18 || growthUSD>activationUSD || maxIdleBps>MAX_IDLE_BPS)
            revert InvalidConfiguration();
        entry=P.EntryPolicy(activationUSD,growthUSD,maxIdleBps,entry.revision+1);
        _record("ENTRY",keccak256(abi.encode(entry,reviewHash)));
        emit EntryPolicyConfigured(activationUSD,growthUSD,maxIdleBps,entry.revision,reviewHash);
    }
    function setMaintenancePolicy(uint16 maxIdleBps,bytes32 reviewHash) external onlyGovernance operating nonReentrant {
        _review(reviewHash);if(maxIdleBps>MAX_IDLE_BPS)revert InvalidConfiguration();
        maintenance=P.MaintenancePolicy(maxIdleBps,maintenance.revision+1);
        _record("MAINTENANCE",keccak256(abi.encode(maintenance,reviewHash)));
        emit MaintenancePolicyConfigured(maxIdleBps,maintenance.revision,reviewHash);
    }
    /// @notice Explicit engineering limits, not qualification of full batches
    /// or future providers. These revisions never alter LP sample geometry.
    function setGasPolicy(uint32 payoutGas,uint32 sourceCallGas,uint32 royaltySyncGas,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        _review(reviewHash);
        if(payoutGas<MIN_CALL_GAS || payoutGas>MAX_CALL_GAS || sourceCallGas<MIN_CALL_GAS ||
            sourceCallGas>MAX_CALL_GAS || royaltySyncGas<MIN_CALL_GAS || royaltySyncGas>MAX_CALL_GAS)
            revert InvalidConfiguration();
        gasLimits=P.GasPolicy(payoutGas,sourceCallGas,royaltySyncGas,gasLimits.revision+1);
        _record("GAS",keccak256(abi.encode(gasLimits,reviewHash)));
        emit GasPolicyConfigured(payoutGas,sourceCallGas,royaltySyncGas,gasLimits.revision,reviewHash);
    }
    function setMintPrice(uint128 price,bytes32 reviewHash) external onlyGovernance operating nonReentrant {
        _review(reviewHash);if(price==0)revert InvalidConfiguration();uint128 previous=sale.mintPrice;
        sale.mintPrice=price;++sale.revision;_record("MINT_PRICE",keccak256(abi.encode(sale,reviewHash)));
        emit MintPriceConfigured(previous,price,sale.revision,reviewHash);
    }
    /// @notice Only future primary-sale proceeds change. Zero cancels the
    /// proposal; accepting the new address requires that address itself.
    function proposeMintRecipient(address candidate,bytes32 reviewHash) external onlyGovernance operating nonReentrant {
        _review(reviewHash);
        if(candidate!=address(0)){
            _validRecipient(candidate);if(candidate==sale.recipient)revert InvalidConfiguration();
        }
        sale.pendingRecipient=candidate;++sale.revision;
        _record("MINT_RECIPIENT_PROPOSE",keccak256(abi.encode(sale,reviewHash)));
        emit MintRecipientProposed(sale.recipient,candidate,sale.revision,reviewHash);
    }
    function acceptMintRecipient() external operating nonReentrant {
        if(msg.sender==address(0) || msg.sender!=sale.pendingRecipient || access.preparationActive() ||
            (access.isSealed() && access.canonicalState()!=0))revert Unauthorized();
        _validRecipient(msg.sender);address previous=sale.recipient;
        sale.recipient=msg.sender;sale.pendingRecipient=address(0);++sale.revision;
        _record("MINT_RECIPIENT_ACCEPT",keccak256(abi.encode(sale)));
        emit MintRecipientAccepted(previous,sale.recipient,sale.revision);
    }
    function validateMintRecipient() external view {_validRecipient(sale.recipient);}
    function _validRecipient(address candidate) private view {
        address collection=access.module(Ids.NFT);
        if(candidate==address(0) || candidate==address(this) || candidate==address(access) ||
            candidate==access.module(Ids.VAULT) || candidate==collection || candidate==access.module(Ids.FEES) ||
            candidate==access.module(Ids.REWARDS) || candidate==access.module(Ids.MIGRATION))revert InvalidConfiguration();
        if(collection!=address(0) && candidate==IPolicyNFT(collection).royaltyRewards())revert InvalidConfiguration();
    }
    /// @notice Cosmetic tiers only; never touches rarity or economic shares.
    function setEvolutionThresholds(uint128 enhancedUSD,uint128 singularityUSD,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        _review(reviewHash);
        if(enhancedUSD==0 || singularityUSD<=enhancedUSD)revert InvalidConfiguration();
        metadata=P.MetadataPolicy(enhancedUSD,singularityUSD,metadata.revision+1);
        _record("METADATA",keccak256(abi.encode(metadata,reviewHash)));
        address collection=access.module(Ids.NFT);
        if(collection!=address(0))IPolicyNFT(collection).policyMetadataChanged();
        emit EvolutionThresholdsConfigured(enhancedUSD,singularityUSD,metadata.revision,reviewHash);
    }
    function _vrf(address coordinator,bytes32 expectedCodeHash,bytes32 keyHash,uint256 subscriptionId,
        uint16 confirmations,uint32 callbackGas,bool nativePayment,bytes32 reviewHash,uint64 generation)
        private view returns(P.VrfPolicy memory result) {
        _review(reviewHash);
        if(coordinator.code.length==0 || expectedCodeHash==bytes32(0) || coordinator.codehash!=expectedCodeHash ||
            keyHash==bytes32(0) || subscriptionId==0 || confirmations<3 || confirmations>200 ||
            callbackGas<200000 || callbackGas>10000000)revert InvalidConfiguration();
        result=P.VrfPolicy(coordinator,expectedCodeHash,keyHash,subscriptionId,confirmations,callbackGas,nativePayment,
            generation,true,reviewHash);
    }
    function configureRandomness(address coordinator,bytes32 expectedCodeHash,bytes32 keyHash,uint256 subscriptionId,
        uint16 confirmations,uint32 callbackGas,bool nativePayment,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        if(access.isSealed() || randomness.configured || randomness.generation!=0)revert InvalidConfiguration();
        randomness=_vrf(coordinator,expectedCodeHash,keyHash,subscriptionId,confirmations,callbackGas,nativePayment,reviewHash,0);
        ++vrfRevision;_record("VRF",keccak256(abi.encode(randomness,vrfRevision)));
        emit RandomnessConfigured(coordinator,0,vrfRevision,reviewHash);
    }
    /// @notice Future mints only, after every old draw is finalized. There is
    /// no provider retargeting, reroll or administrator-selected pending result.
    function rotateRandomness(address coordinator,bytes32 expectedCodeHash,bytes32 keyHash,uint256 subscriptionId,
        uint16 confirmations,uint32 callbackGas,bool nativePayment,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        if(!access.isSealed() || access.lpExitStarted() || !randomness.configured)revert InvalidState();
        IPolicyNFT collection=IPolicyNFT(access.module(Ids.NFT));
        if(collection.nextToFinalize()!=collection.mintedCount()+1)revert InvalidState();
        randomness=_vrf(coordinator,expectedCodeHash,keyHash,subscriptionId,confirmations,callbackGas,nativePayment,reviewHash,
            randomness.generation+1);
        ++vrfRevision;_record("VRF",keccak256(abi.encode(randomness,vrfRevision)));
        emit RandomnessConfigured(coordinator,randomness.generation,vrfRevision,reviewHash);
    }
    function setRandomnessRequestSettings(uint16 confirmations,uint32 callbackGas,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        _review(reviewHash);if(!randomness.configured || confirmations<3 || confirmations>200 ||
            callbackGas<200000 || callbackGas>10000000)revert InvalidConfiguration();
        randomness.requestConfirmations=confirmations;randomness.callbackGasLimit=callbackGas;randomness.reviewHash=reviewHash;
        ++vrfRevision;_record("VRF_SETTINGS",keccak256(abi.encode(randomness,vrfRevision)));
        emit RandomnessSettingsConfigured(confirmations,callbackGas,vrfRevision,reviewHash);
    }
}
