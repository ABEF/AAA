// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids} from "./libraries/ZZZTypes.sol";
import {IZZZVault, IZZZAccess} from "./interfaces/IZZZ.sol";
import {ZZZRoyaltyRewards} from "./ZZZRoyaltyRewards.sol";
import {ZZZClaimRouter} from "./ZZZClaimRouter.sol";
import {ZZZNFTMetadata, NFTMetadataInput} from "./ZZZNFTMetadata.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";
import {ZZZRoyaltyFactory} from "./ZZZRoyaltyFactory.sol";
import {IZZZCanonicalAccess} from "./interfaces/IZZZCanonical.sol";
import {CanonicalNFTRecord} from "./interfaces/IZZZNFTCanonical.sol";
interface IZZZNFTSuccessor {
    function destinationController() external view returns (address);
}

/// @dev Minimal official VRF v2.5 subscription ABI. A matching selector does not
/// prove a coordinator verifies VRF proofs; actual network support, coordinator,
/// subscription and key require independent production review.
interface IZZZVRFCoordinator {
    struct RandomWordsRequest {
        bytes32 keyHash;
        uint256 subId;
        uint16 requestConfirmations;
        uint32 callbackGasLimit;
        uint32 numWords;
        bytes extraArgs;
    }
    function requestRandomWords(RandomWordsRequest calldata request) external returns (uint256 requestId);
}

/// @notice Canonical ownership and immutable revealed traits. NFT-sale royalties
/// have their own funded ledger; rarity never changes LP or collective rewards.
contract ZZZNFT is ERC721, ZZZModule, ReentrancyGuard {
    string private metadataBase;
    bool private metadataConfigured;
    ZZZRoyaltyRewards public immutable royaltyRewards;
    ZZZClaimRouter public immutable claimRouter;
    ZZZNFTMetadata public immutable metadataRenderer;
    address public randomnessCoordinator;
    bytes32 public keyHash;
    uint256 public subscriptionId;
    uint16 public requestConfirmations;
    uint32 public callbackGasLimit;
    bool public nativePayment;
    bool public randomnessConfigured;
    uint256 public constant MAX_SUPPLY = 1000;
    uint256 public constant MAX_METADATA_REFRESH_BATCH = 50;
    uint256 public mintedCount;
    uint256 public nextToFinalize = 1;
    uint256 public remainingToReveal = MAX_SUPPLY;
    uint16[3] public rarityRemaining = [600, 300, 100];
    mapping(uint256 => uint256) public mintOrdinalOf;
    mapping(uint256 => uint256) public tokenAtOrdinal;
    mapping(uint256 => uint256) public requestOf;
    mapping(uint256 => bool) public traitsReady;
    mapping(uint256 => uint8) public rarityOf;
    mapping(uint256 => uint8) public colorOf;
    mapping(uint256 => uint8) public paletteOf;
    mapping(uint256 => uint8) public patternOf;
    // Sparse Fisher-Yates indices, encoded plus one so zero denotes identity.
    // Each rarity owns a finite, immutable artwork inventory independent of the
    // rarity draw. Neither owners nor governance can choose or reroll artwork.
    mapping(uint8 => mapping(uint256 => uint16)) private artworkDraw;
    struct RandomnessResult {
        uint256 nftId;
        uint256 rarityWord;
        uint256 colorWord;
        bool requested;
        bool fulfilled;
    }
    mapping(bytes32 => RandomnessResult) private randomness;
    mapping(uint256 => uint256) public requestEpochOf;
    uint256 public randomnessEpoch;
    event MetadataBaseChanged(string newBase);
    event RandomnessConfigured(address indexed coordinator, bytes32 keyHash, uint256 subscriptionId,
        uint16 confirmations, uint32 callbackGasLimit, bool nativePayment);
    event RandomnessRequested(uint256 indexed nftId, uint256 indexed requestId, uint256 indexed ordinal);
    event RandomnessReceived(uint256 indexed requestId);
    event TraitsFinalized(uint256 indexed nftId, uint8 rarity, uint8 color);
    event ArtworkFinalized(uint256 indexed nftId, uint8 palette, uint8 pattern);
    event MetadataUpdate(uint256 tokenId);
    event BatchMetadataUpdate(uint256 fromTokenId, uint256 toTokenId);

    constructor(address controller, string memory baseURI)
        ERC721("ZZZ Permanent Liquidity Rights", "ZZZLP") ZZZModule(controller) {
        _validateBaseURI(baseURI);
        metadataBase = baseURI;
        metadataConfigured = bytes(baseURI).length != 0;
        royaltyRewards = ZZZRoyaltyFactory(access.royaltyFactory()).create();
        if (royaltyRewards.canonicalController() != controller || royaltyRewards.nft() != address(this)) revert InvalidConfiguration();
        claimRouter = new ZZZClaimRouter(controller, address(this), address(royaltyRewards));
        metadataRenderer = new ZZZNFTMetadata(controller);
    }

    /// @notice Configure once before sealing. No coordinator replacement,
    /// cancellation, retry, owner-selected traits or administrator reroll exists.
    function configureRandomness(address coordinator, bytes32 gasLane, uint256 subId, uint16 confirmations,
        uint32 gasLimit, bool payNative) external onlyGovernance {
        if (access.isSealed() || randomnessConfigured || coordinator.code.length == 0 ||
            gasLane == bytes32(0) || subId == 0 || confirmations < 3 || confirmations > 200 ||
            gasLimit < 200000 || gasLimit > 10000000) revert InvalidConfiguration();
        randomnessCoordinator = coordinator; keyHash = gasLane; subscriptionId = subId;
        requestConfirmations = confirmations; callbackGasLimit = gasLimit; nativePayment = payNative;
        randomnessConfigured = true;
        emit RandomnessConfigured(coordinator, gasLane, subId, confirmations, gasLimit, payNative);
    }

    function mint(address to, uint256 id) external onlyModule(Ids.VAULT) operating nonReentrant {
        if (!randomnessConfigured) revert NotReady();
        if (mintedCount == MAX_SUPPLY) revert InvalidState();
        address recipient = IZZZVault(msg.sender).mintProceedsRecipient();
        if (recipient == address(royaltyRewards) || recipient == address(this)) revert InvalidConfiguration();
        uint256 ordinal = ++mintedCount;
        mintOrdinalOf[id] = ordinal; tokenAtOrdinal[ordinal] = id;
        // Bind before the ERC721 receiver callback. Official fulfillment is
        // asynchronous; a synchronous coordinator callback is rejected.
        uint256 requestId = IZZZVRFCoordinator(randomnessCoordinator).requestRandomWords(
            IZZZVRFCoordinator.RandomWordsRequest(keyHash, subscriptionId, requestConfirmations,
                callbackGasLimit, 2, abi.encodeWithSelector(bytes4(keccak256("VRF ExtraArgsV1")), nativePayment)));
        bytes32 requestKey = _requestKey(randomnessEpoch, requestId);
        if (requestId == 0 || randomness[requestKey].requested) revert InvalidState();
        randomness[requestKey].nftId = id; randomness[requestKey].requested = true;
        requestEpochOf[id] = randomnessEpoch;
        requestOf[id] = requestId;
        _safeMint(to, id);
        emit RandomnessRequested(id, requestId, ordinal);
    }

    /// @dev Bounded callback stores only authenticated words. Metadata work can
    /// neither consume its gas nor turn a fulfilled request into another draw.
    function rawFulfillRandomWords(uint256 requestId, uint256[] calldata words) external {
        if (msg.sender != randomnessCoordinator) revert Unauthorized();
        RandomnessResult storage result = randomness[_requestKey(randomnessEpoch, requestId)];
        if (!result.requested || result.fulfilled || words.length != 2) revert InvalidState();
        result.fulfilled = true; result.rarityWord = words[0]; result.colorWord = words[1];
        emit RandomnessReceived(requestId);
    }

    /// @notice Draw without replacement, strictly in mint order: exactly 600
    /// Commun, 300 Rare and 100 Legendary when all 1,000 NFTs are revealed.
    /// Missing earlier fulfillment blocks later reveals; no fallback or reroll.
    function finalizeTraits(uint256 id) external nonReentrant canonicalAccounting {
        _requireOwned(id);
        RandomnessResult storage result = randomness[_requestKey(requestEpochOf[id], requestOf[id])];
        if (!result.fulfilled || traitsReady[id] || mintOrdinalOf[id] != nextToFinalize || result.nftId != id) {
            revert NotReady();
        }
        uint256 rarityRoll = result.rarityWord % remainingToReveal;
        uint8 rarity = rarityRoll < rarityRemaining[0] ? 0 :
            rarityRoll < uint256(rarityRemaining[0]) + rarityRemaining[1] ? 1 : 2;
        (uint8 palette, uint8 pattern) = _drawArtwork(rarity, result.colorWord, rarityRemaining[rarity]);
        --rarityRemaining[rarity]; --remainingToReveal; ++nextToFinalize;
        rarityOf[id] = rarity; paletteOf[id] = palette; patternOf[id] = pattern;
        colorOf[id] = ZZZArtwork.primaryColor(palette);
        traitsReady[id] = true;
        emit TraitsFinalized(id, rarity, colorOf[id]);
        emit ArtworkFinalized(id, palette, pattern);
        emit MetadataUpdate(id);
    }

    function _drawArtwork(uint8 rarity, uint256 word, uint256 remaining) private returns (uint8, uint8) {
        uint256 draw = word % remaining;
        uint16 stored = artworkDraw[rarity][draw];
        uint256 entry = stored == 0 ? draw : uint256(stored) - 1;
        uint256 last = remaining - 1;
        if (draw != last) {
            uint16 replacement = artworkDraw[rarity][last];
            artworkDraw[rarity][draw] = replacement == 0 ? uint16(last + 1) : replacement;
        }
        delete artworkDraw[rarity][last];
        return ZZZArtwork.item(rarity, entry);
    }

    /// @notice Called after the Vault commits successful share issuance.
    /// Eligibility persists through market decreases and migration states.
    function notifyContribution(uint256 id) external onlyModule(Ids.VAULT) operating {
        _requireOwned(id);
        if (!traitsReady[id] || IZZZVault(msg.sender).sharesOf(id) == 0) revert NotReady();
        if (royaltyRewards.weightOf(id) == 0) royaltyRewards.activate(id, uint256(rarityOf[id]) + 1);
        emit MetadataUpdate(id);
    }

    function addRoyaltyAsset(address token) external onlyGovernance { royaltyRewards.addAsset(token); }

    /// @notice Fixed 5% marketplace request, wholly payable to the holder pool.
    /// ERC2981 cannot enforce marketplace payment.
    function royaltyInfo(uint256, uint256 salePrice) external view returns (address receiver, uint256 royaltyAmount) {
        return (address(royaltyRewards), Math.mulDiv(salePrice, 500, 10000));
    }

    function supportsInterface(bytes4 interfaceId) public view override returns (bool) {
        return interfaceId == 0x2a55205a || interfaceId == 0x49064906 || super.supportsInterface(interfaceId);
    }

    /// @notice Current home-chain marked principal, idle and compound NAV share.
    /// Remote/in-flight custody or stale dependencies reports unavailable.
    function currentLPValue(uint256 id) public view returns (bool available, uint256 valueUSD) {
        _requireOwned(id);
        if (royaltyRewards.weightOf(id) == 0) return (true, 0);
        try metadataRenderer.currentValue(id) returns (uint256 value) { return (true, value); }
        catch { return (false, 0); }
    }

    function evolution(uint256 id) public view returns (bool available, uint8 stage) {
        _requireOwned(id);
        if (royaltyRewards.weightOf(id) == 0) return (true, 0);
        uint256 value;
        (available, value) = currentLPValue(id);
        if (!available) return (false, 1);
        return (true, value >= 10000e18 ? 3 : value >= 1000e18 ? 2 : 1);
    }

    function tokenURI(uint256 id) public view override returns (string memory) {
        _requireOwned(id);
        (bool available, uint256 value) = currentLPValue(id);
        uint8 weight = uint8(royaltyRewards.weightOf(id));
        uint8 stage = weight == 0 ? 0 : value >= 10000e18 ? 3 : value >= 1000e18 ? 2 : 1;
        return metadataRenderer.render(NFTMetadataInput(id, rarityOf[id], paletteOf[id], patternOf[id], stage, traitsReady[id],
            available, value, weight, metadataBase));
    }

    /// @notice Permissionless indexer notification after market moves.
    function refreshMetadata(uint256 id) external { _requireOwned(id); emit MetadataUpdate(id); }

    /// @notice Notify a bounded inclusive range of mint ordinals without reading valuations.
    /// Ordinals are not token IDs: each notification uses the actual minted ID.
    function refreshMetadataRange(uint256 firstOrdinal, uint256 lastOrdinal) external {
        if (firstOrdinal == 0 || firstOrdinal > lastOrdinal || lastOrdinal > mintedCount ||
            lastOrdinal - firstOrdinal >= MAX_METADATA_REFRESH_BATCH) revert InvalidAmount();
        for (uint256 ordinal = firstOrdinal; ordinal <= lastOrdinal; ++ordinal) {
            uint256 id = tokenAtOrdinal[ordinal];
            _requireOwned(id);
            emit MetadataUpdate(id);
        }
    }

    function artworkBaseURI() external view returns (string memory) { return metadataBase; }

    /// @notice Only an initially empty base can be populated, once before seal.
    function setBaseURI(string calldata baseURI) external onlyGovernance {
        if (access.isSealed() || metadataConfigured || bytes(baseURI).length == 0) revert InvalidConfiguration();
        _validateBaseURI(baseURI);
        metadataConfigured = true; metadataBase = baseURI;
        emit MetadataBaseChanged(baseURI);
        emit BatchMetadataUpdate(0, type(uint256).max);
    }
    function _validateBaseURI(string memory baseURI) private pure {
        bytes memory value = bytes(baseURI);
        if (value.length == 0) return; // Unconfigured draft; production admission requires a reviewed CID.
        bool ipfs = value.length >= 7 && value[0] == "i" && value[1] == "p" && value[2] == "f" &&
            value[3] == "s" && value[4] == ":" && value[5] == "/" && value[6] == "/";
        bool arweave = value.length >= 5 && value[0] == "a" && value[1] == "r" &&
            value[2] == ":" && value[3] == "/" && value[4] == "/";
        if (!ipfs && !arweave) revert InvalidConfiguration();
    }
    function _baseURI() internal view override returns (string memory) { return metadataBase; }
    function _requestKey(uint256 epoch, uint256 requestId) private pure returns (bytes32) {
        return keccak256(abi.encode(epoch, requestId));
    }
    function transferFrom(address from, address to, uint256 tokenId) public override canonicalAccounting {
        super.transferFrom(from, to, tokenId);
    }
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory data)
        public override canonicalAccounting {
        super.safeTransferFrom(from, to, tokenId, data);
    }
    /// @dev Imports deliberately mint inert ownership without receiver callbacks;
    /// ordinary transfers/mints cannot execute while either deployment is frozen.
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        uint8 state = IZZZCanonicalAccess(address(access)).canonicalState();
        if (state != 0 && !(state == 2 && canonicalImporting && msg.sender == canonicalModule())) revert InvalidState();
        return super._update(to, tokenId, auth);
    }

    bool private canonicalImporting;
    function canonicalModule() public view returns (address) { return access.module(Ids.NFT_CANONICAL); }
    modifier onlyCanonicalWriter() {
        if (msg.sender != canonicalModule() || !access.isSealed() || access.canonicalState() != 2) revert Unauthorized();
        _;
    }
    function canonicalRandomness(uint256 id) external view returns (uint256,uint256,uint256,bool,bool) {
        RandomnessResult storage result = randomness[_requestKey(requestEpochOf[id], requestOf[id])];
        return (result.nftId,result.rarityWord,result.colorWord,result.requested,result.fulfilled);
    }
    function canonicalArtwork(uint8 rarity, uint256 item) external view returns (uint16) { return artworkDraw[rarity][item]; }
    function canonicalWriteHeader(uint256 count, uint256 next, uint256 remaining, uint16[3] calldata quotas, uint256 epoch)
        external onlyCanonicalWriter {
        mintedCount = count; nextToFinalize = next; remainingToReveal = remaining;
        rarityRemaining = quotas; randomnessEpoch = epoch;
    }
    function canonicalWriteRecord(uint256 row, CanonicalNFTRecord calldata value) external onlyCanonicalWriter {
        bytes32 key = _requestKey(value.requestEpoch, value.requestId);
        if (randomness[key].requested) revert InvalidState();
        randomness[key] = RandomnessResult(value.id, value.rarityWord, value.colorWord, true, true);
        requestOf[value.id] = value.requestId; requestEpochOf[value.id] = value.requestEpoch;
        mintOrdinalOf[value.id] = row; tokenAtOrdinal[row] = value.id;
        rarityOf[value.id] = value.rarity; colorOf[value.id] = value.color;
        paletteOf[value.id] = value.palette; patternOf[value.id] = value.pattern; traitsReady[value.id] = true;
        canonicalImporting = true; _mint(value.owner, value.id); canonicalImporting = false;
    }
    function canonicalWriteArtwork(uint8 rarity, uint256 item, uint16 value) external onlyCanonicalWriter {
        artworkDraw[rarity][item] = value;
    }
    function canonicalSuccessor() external view returns (address controller, address replacementNFT) {
        if (access.canonicalState() != 3) return (address(0), address(0));
        controller = IZZZNFTSuccessor(access.canonicalHandoff()).destinationController();
        replacementNFT = IZZZAccess(controller).module(Ids.NFT);
    }
    function canonicalRetire() external onlyHandoff {
        if (access.canonicalState() != 3) revert InvalidState();
        emit BatchMetadataUpdate(0, type(uint256).max);
    }
    // No burn or principal-redemption entrypoint. Standard ERC721 safe transfers.
}
