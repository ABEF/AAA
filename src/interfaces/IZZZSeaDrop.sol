// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @dev ABI-equivalent local types for the verified SeaDrop V1 deployment.
/// These declarations do not substitute for runtime/product qualification.
struct PublicDrop {
    uint80 mintPrice;
    uint48 startTime;
    uint48 endTime;
    uint16 maxTotalMintableByWallet;
    uint16 feeBps;
    bool restrictFeeRecipients;
}
struct MintParams {
    uint256 mintPrice;
    uint256 maxTotalMintableByWallet;
    uint256 startTime;
    uint256 endTime;
    uint256 dropStageIndex;
    uint256 maxTokenSupplyForStage;
    uint256 feeBps;
    bool restrictFeeRecipients;
}
struct AllowListData { bytes32 merkleRoot; string[] publicKeyURIs; string allowListURI; }
struct TokenGatedMintParams { address allowedNftToken; uint256[] allowedNftTokenIds; }
struct TokenGatedDropStage {
    uint80 mintPrice;
    uint16 maxTotalMintableByWallet;
    uint48 startTime;
    uint48 endTime;
    uint8 dropStageIndex;
    uint32 maxTokenSupplyForStage;
    uint16 feeBps;
    bool restrictFeeRecipients;
}
struct SignedMintValidationParams {
    uint80 minMintPrice;
    uint24 maxMaxTotalMintableByWallet;
    uint40 minStartTime;
    uint40 maxEndTime;
    uint40 maxMaxTokenSupplyForStage;
    uint16 minFeeBps;
    uint16 maxFeeBps;
}

interface IZZZSeaDrop {
    function mintPublic(address nftContract,address feeRecipient,address minterIfNotPayer,uint256 quantity)
        external payable;
    function mintAllowList(address nftContract,address feeRecipient,address minterIfNotPayer,uint256 quantity,
        MintParams calldata mintParams,bytes32[] calldata proof) external payable;
    function mintSigned(address nftContract,address feeRecipient,address minterIfNotPayer,uint256 quantity,
        MintParams calldata mintParams,uint256 salt,bytes calldata signature) external payable;
    function mintAllowedTokenHolder(address nftContract,address feeRecipient,address minterIfNotPayer,
        TokenGatedMintParams calldata mintParams) external payable;
    function getPublicDrop(address nftContract) external view returns(PublicDrop memory);
    function getCreatorPayoutAddress(address nftContract) external view returns(address);
    function getAllowListMerkleRoot(address nftContract) external view returns(bytes32);
    function getAllowedFeeRecipients(address nftContract) external view returns(address[] memory);
    function getFeeRecipientIsAllowed(address nftContract,address feeRecipient) external view returns(bool);
    function getSigners(address nftContract) external view returns(address[] memory);
    function getTokenGatedAllowedTokens(address nftContract) external view returns(address[] memory);
    function getPayerIsAllowed(address nftContract,address payer) external view returns(bool);
    function getPayers(address nftContract) external view returns(address[] memory);
    function updatePublicDrop(PublicDrop calldata publicDrop) external;
    function updateAllowList(AllowListData calldata allowListData) external;
    function updateTokenGatedDrop(address allowedNftToken,TokenGatedDropStage calldata dropStage) external;
    function updateDropURI(string calldata dropURI) external;
    function updateCreatorPayoutAddress(address payoutAddress) external;
    function updateAllowedFeeRecipient(address feeRecipient,bool allowed) external;
    function updateSignedMintValidationParams(address signer,SignedMintValidationParams calldata params) external;
    function updatePayer(address payer,bool allowed) external;
}

interface IZZZSeaDropTokenMetadata {
    function contractURI() external view returns(string memory);
    function setContractURI(string calldata newContractURI) external;
    function baseURI() external view returns(string memory);
    function setBaseURI(string calldata newBaseURI) external;
    function maxSupply() external view returns(uint256);
    function setMaxSupply(uint256 newMaxSupply) external;
    function provenanceHash() external view returns(bytes32);
    function setProvenanceHash(bytes32 newProvenanceHash) external;
}

/// @dev Exactly the eleven directly declared V1 selectors. Inherited metadata
/// selectors are intentionally a separate interface, as in upstream Solidity.
interface INonFungibleSeaDropToken is IZZZSeaDropTokenMetadata {
    event AllowedSeaDropUpdated(address[] allowedSeaDrop);
    function updateAllowedSeaDrop(address[] calldata allowedSeaDrop) external;
    function mintSeaDrop(address minter,uint256 quantity) external payable;
    function getMintStats(address minter) external view returns(uint256,uint256,uint256);
    function updatePublicDrop(address seaDropImpl,PublicDrop calldata publicDrop) external;
    function updateAllowList(address seaDropImpl,AllowListData calldata allowListData) external;
    function updateTokenGatedDrop(address seaDropImpl,address allowedNftToken,TokenGatedDropStage calldata dropStage) external;
    function updateDropURI(address seaDropImpl,string calldata dropURI) external;
    function updateCreatorPayoutAddress(address seaDropImpl,address payoutAddress) external;
    function updateAllowedFeeRecipient(address seaDropImpl,address feeRecipient,bool allowed) external;
    function updateSignedMintValidationParams(address seaDropImpl,address signer,
        SignedMintValidationParams calldata params) external;
    function updatePayer(address seaDropImpl,address payer,bool allowed) external;
}
