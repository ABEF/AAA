// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @notice Read-only policy surface shared by the fresh deployment's fixed
/// consumers. None of these values changes ownership or moves backing.
interface IZZZProtocolPolicy {
    struct EntryPolicy { uint128 minActivationUSD; uint128 minGrowthUSD; uint16 maxIdleBps; uint64 revision; }
    struct MaintenancePolicy { uint16 maxIdleBps; uint64 revision; }
    struct GasPolicy { uint32 payoutGas; uint32 sourceCallGas; uint32 royaltySyncGas; uint64 revision; }
    struct SalePolicy { uint128 mintPrice; address recipient; address pendingRecipient; uint64 revision; }
    struct MetadataPolicy { uint128 enhancedUSD; uint128 singularityUSD; uint64 revision; }
    struct VrfPolicy {
        address coordinator; bytes32 expectedCodeHash; bytes32 keyHash; uint256 subscriptionId;
        uint16 requestConfirmations; uint32 callbackGasLimit; bool nativePayment;
        uint64 generation; bool configured; bytes32 reviewHash;
    }
    function access() external view returns(address);
    function PROTOCOL_POLICY_VERSION() external view returns(uint256);
    function entryPolicy() external view returns(EntryPolicy memory);
    function maintenancePolicy() external view returns(MaintenancePolicy memory);
    function gasPolicy() external view returns(GasPolicy memory);
    function payoutGas() external view returns(uint32);
    function sourceCallGas() external view returns(uint32);
    function royaltySyncGas() external view returns(uint32);
    function salePolicy() external view returns(SalePolicy memory);
    function metadataPolicy() external view returns(MetadataPolicy memory);
    function vrfPolicy() external view returns(VrfPolicy memory);
    function vrfRevision() external view returns(uint64);
    function entryFingerprint() external view returns(bytes32);
    function maintenanceFingerprint() external view returns(bytes32);
    function gasFingerprint() external view returns(bytes32);
    function saleFingerprint() external view returns(bytes32);
    function mintFingerprint() external view returns(bytes32);
    function metadataFingerprint() external view returns(bytes32);
    function configurationHash() external view returns(bytes32);
    function validateMintRecipient() external view;
}
