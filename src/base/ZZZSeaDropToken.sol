// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZModule} from "./ZZZModule.sol";
import {ZZZSeaDropMint} from "../ZZZSeaDropMint.sol";
import {Ids} from "../libraries/ZZZTypes.sol";
import {IZZZSeaDrop,PublicDrop,AllowListData,TokenGatedDropStage,SignedMintValidationParams}
    from "../interfaces/IZZZSeaDrop.sol";

interface ISeaDropTokenState {
    function mintedCount() external view returns(uint256);
    function artworkBaseURI() external view returns(string memory);
}

/// @notice Typed configuration for one pre-seal-bound SeaDrop integration.
/// No arbitrary target, calldata, new minter, proceeds custody or delegatecall.
abstract contract ZZZSeaDropToken is ZZZModule {
    ZZZSeaDropMint public seaDropMint;
    event SeaDropMintBound(address indexed helper);
    event AllowedSeaDropUpdated(address[] allowedSeaDrop);

    constructor(address controller) ZZZModule(controller) {}

    /// @notice Bind a separately deployed collection-specific helper once.
    /// Zero-helper direct minting remains an explicit test configuration only.
    function setSeaDropMint(address helper) external onlyGovernance {
        if(address(seaDropMint)!=address(0))revert InvalidConfiguration();
        ZZZSeaDropMint candidate=ZZZSeaDropMint(helper);
        candidate.validateBinding();
        seaDropMint=candidate;
        emit SeaDropMintBound(helper);
    }

    function getMintStats(address minter) external view returns(uint256,uint256,uint256) {
        return seaDropMint.mintStats(minter);
    }

    /// @dev Resolve the NFT-only Vault recording branch during its exact batch.
    function seaDropMintRecipient(bytes32 review) external view returns(address) {
        if(msg.sender!=access.module(Ids.VAULT_CANONICAL))revert Unauthorized();
        return seaDropMint.validateMintReview(review);
    }

    function _updateDrop() private {
        bytes memory data=seaDropMint.prepareUpdate(msg.sender,msg.data);
        if(data.length!=0) {
            (bool ok,)=seaDropMint.seaDrop().call(data);
            if(!ok)revert InvalidConfiguration();
        }
        if(!access.canConfigure(msg.sender))revert Unauthorized();
    }
    /// @notice Acknowledge only the SAME immutable singleton; never rotate it.
    function updateAllowedSeaDrop(address[] calldata) external pure {
        revert InvalidConfiguration();
    }
    function updatePublicDrop(address,PublicDrop calldata) external {
        _updateDrop();
    }
    function updateAllowList(address,AllowListData calldata) external {
        _updateDrop();
    }
    function updateDropURI(address,string calldata) external {
        _updateDrop();
    }
    function updateCreatorPayoutAddress(address,address) external {
        _updateDrop();
    }
    function updateAllowedFeeRecipient(address,address,bool) external {
        _updateDrop();
    }
    function updatePayer(address,address,bool) external {
        _updateDrop();
    }
    /// @notice Unsupported mint families cannot be enabled through V1 setters.
    function updateTokenGatedDrop(address,address,TokenGatedDropStage calldata) external pure {
        revert InvalidConfiguration();
    }
    function updateSignedMintValidationParams(address,address,SignedMintValidationParams calldata) external pure {
        revert InvalidConfiguration();
    }
    function maxSupply() external pure returns(uint256) { return 1000; }
    function setMaxSupply(uint256) external pure { revert InvalidConfiguration(); }
    function baseURI() external view returns(string memory) {
        return ISeaDropTokenState(address(this)).artworkBaseURI();
    }
}
