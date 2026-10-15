// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {IZZZAccess, IZZZNFT} from "./interfaces/IZZZ.sol";
import {Ids} from "./libraries/ZZZTypes.sol";

interface IZZZClaimLedger {
    function claimFor(uint256 id, address asset, address owner) external returns (uint256);
}

/// @notice Atomic, owner-authenticated batching of funded LP and royalty claims.
/// Ledgers pay the current owner directly. This helper never holds funds or
/// approvals, and accepts neither an arbitrary target nor a payout recipient.
contract ZZZClaimRouter is ReentrancyGuard {
    uint256 public constant MAX_CLAIMS = 32;
    IZZZAccess public immutable access;
    address public immutable nft;
    address public immutable royalties;

    struct Claim {
        uint256 nftId;
        address asset;
        bool royalty;
    }

    error InvalidConfiguration();
    error InvalidBatch();
    error DuplicateClaim();
    error Unauthorized();
    event BatchClaimed(address indexed owner, uint256 operations);

    /// @dev Created only by its NFT, while that NFT is under construction.
    /// The LP ledger is resolved through the canonical sealed access registry.
    constructor(address controller, address nftController, address royaltyLedger) {
        if (controller.code.length == 0 || msg.sender != nftController || royaltyLedger.code.length == 0) {
            revert InvalidConfiguration();
        }
        access = IZZZAccess(controller);
        nft = nftController;
        royalties = royaltyLedger;
    }

    /// @notice At most 32 selected (NFT, asset, ledger) operations per transaction.
    /// Results retain input order and raw asset units; unlike dollar values,
    /// amounts for different assets must never be summed. Any failure rolls back
    /// the complete batch. Chunk larger portfolios, and omit failing assets.
    function claimBatch(Claim[] calldata claims) external nonReentrant returns (uint256[] memory amounts) {
        uint256 length = claims.length;
        if (length == 0 || length > MAX_CLAIMS) revert InvalidBatch();
        if (!access.isSealed() || access.module(Ids.NFT) != nft) revert InvalidConfiguration();
        // Reject malformed/unauthorized batches before any payout callback.
        for (uint256 i; i < length; ++i) {
            Claim calldata entry = claims[i];
            if (IZZZNFT(nft).ownerOf(entry.nftId) != msg.sender) revert Unauthorized();
            for (uint256 j; j < i; ++j) {
                Claim calldata earlier = claims[j];
                if (entry.nftId == earlier.nftId && entry.asset == earlier.asset && entry.royalty == earlier.royalty) {
                    revert DuplicateClaim();
                }
            }
        }
        amounts = new uint256[](length);
        for (uint256 i; i < length; ++i) {
            Claim calldata entry = claims[i];
            // A preceding native/token callback may have transferred this NFT.
            // Each ledger independently repeats the same current-owner check.
            if (IZZZNFT(nft).ownerOf(entry.nftId) != msg.sender) revert Unauthorized();
            address target = entry.royalty ? royalties : access.module(Ids.REWARDS);
            if (target.code.length == 0) revert InvalidConfiguration();
            amounts[i] = IZZZClaimLedger(target).claimFor(entry.nftId, entry.asset, msg.sender);
        }
        emit BatchClaimed(msg.sender, length);
    }
}
