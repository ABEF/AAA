// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZLiquidity, IZZZOracle, IZZZFees, IZZZStrategy} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";
import {IPairVault} from "./ZZZMigrationBudget.sol";
interface IHistoricalCompound { function historicalCompoundValue(uint256 id) external view returns (uint256); }
interface IMetadataCollection {
    function ownerOf(uint256 id) external view returns (address);
    function royaltyRewards() external view returns (address);
    function rarityOf(uint256 id) external view returns (uint8);
    function paletteOf(uint256 id) external view returns (uint8);
    function patternOf(uint256 id) external view returns (uint8);
    function traitsReady(uint256 id) external view returns (bool);
    function artworkBaseURI() external view returns (string memory);
}
interface IMetadataRoyaltyWeight { function weightOf(uint256 id) external view returns (uint256); }

struct NFTMetadataInput {
    uint256 id;
    uint8 rarity;
    uint8 palette;
    uint8 pattern;
    uint8 stage;
    bool traitsReady;
    bool valuationAvailable;
    uint256 valueUSD;
    // Actual activated ledger weight, not the fixed rarity trait. This does not
    // establish readiness of any individual royalty payment currency.
    uint8 royaltyWeight;
    string baseURI;
}

/// @notice Read-only renderer. It never changes custody or reward eligibility.
/// Valuation fails closed while custody is external/parked or dependencies are
/// unavailable; the NFT explicitly reports an unavailable marked LP value.
contract ZZZNFTMetadata {
    IZZZAccess public immutable access;
    error ValuationUnavailable();
    error InvalidArtwork();
    error InvalidConfiguration();
    constructor(address controller) { access = IZZZAccess(controller); }

    /// @notice Preserve the collection's immutable-storage URI syntax rules.
    function validateBaseURI(string memory uri) external pure {
        bytes memory value=bytes(uri);
        if(value.length==0)return;
        bool ipfs=value.length>=7 && value[0]=="i" && value[1]=="p" && value[2]=="f" &&
            value[3]=="s" && value[4]==":" && value[5]=="/" && value[6]=="/";
        bool arweave=value.length>=5 && value[0]=="a" && value[1]=="r" && value[2]==":" &&
            value[3]=="/" && value[4]=="/";
        if(!ipfs && !arweave)revert InvalidConfiguration();
    }

    /// @notice Fixed artwork lookup only. The NFT retains its draw state/order;
    /// this immutable read-only child holds the same finite prepared tables.
    function artworkItem(uint8 rarity, uint256 item)
        external pure returns (uint8 palette, uint8 pattern, uint8 color) {
        if (rarity > 2 || item >= (rarity == 0 ? 600 : rarity == 1 ? 300 : 100)) revert InvalidArtwork();
        (palette, pattern) = ZZZArtwork.item(rarity, item);
        color = ZZZArtwork.primaryColor(palette);
    }

    function currentValue(uint256 id) external view returns (uint256 valueUSD) {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        uint256 bucket = vault.nftBucket(id);
        uint256 shares = vault.sharesOf(id); uint256 supply = vault.bucketTotalShares(bucket);
        Position memory position = vault.group(bucket);
        if (bucket != 0 && shares != 0 && supply >= shares && position.status == PositionStatus.Exited) return 0;
        if (bucket == 0 || shares == 0 || supply < shares || position.status != PositionStatus.Active ||
            position.lpTokenId == 0) revert ValuationUnavailable();
        PoolConfig memory config = IZZZPools(access.module(Ids.POOLS)).accounting(position.poolId);
        // Mark actual concentrated-liquidity amounts only when their spot price
        // agrees with fresh oracle prices. Disabled operations do not invalidate
        // an otherwise honest mark; this view never changes rights or custody.
        IZZZStrategy(access.module(Ids.STRATEGY)).validateExitPrice(position.poolId);
        (uint256 a0, uint256 a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).portfolioAmounts(position.lpTokenId);
        IZZZFees fees = IZZZFees(access.module(Ids.FEES));
        a0 += position.idle0 + fees.compoundBalance(bucket, config.key.currency0);
        a1 += position.idle1 + fees.compoundBalance(bucket, config.key.currency1);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        uint256 nav = oracle.value(config.key.currency0, a0) + oracle.value(config.key.currency1, a1);
        nav += IHistoricalCompound(address(IPairVault(address(vault)).migrationBudget())).historicalCompoundValue(bucket);
        return Math.mulDiv(nav, shares, supply);
    }

    /// @notice Existing dormant NFTs need no prices. Failed marked valuation
    /// remains unavailable; it never becomes a fabricated zero-valued position.
    function markedValue(uint256 id) external view returns (bool available, uint256 valueUSD) {
        return _markedValue(id, _ownedCollection(id));
    }

    /// @notice One stage policy serves both the public evolution read and JSON.
    /// Exited LP keeps its distinct stage and all existing royalty eligibility.
    function evolutionOf(uint256 id) external view returns (bool available, uint8 stage) {
        IMetadataCollection nft = _ownedCollection(id);
        uint256 value;
        (available, value) = _markedValue(id, nft);
        stage = _evolutionStage(id, value, IMetadataRoyaltyWeight(nft.royaltyRewards()).weightOf(id));
    }

    /// @notice Read the canonical NFT's exact traits and rights, then render the
    /// unchanged JSON. No ownership, entitlement or metadata state is written.
    function tokenMetadata(uint256 id) external view returns (string memory) {
        IMetadataCollection nft = _ownedCollection(id);
        (bool available, uint256 value) = _markedValue(id, nft);
        uint8 weight = uint8(IMetadataRoyaltyWeight(nft.royaltyRewards()).weightOf(id));
        uint8 stage = _evolutionStage(id, value, weight);
        return render(NFTMetadataInput(id, nft.rarityOf(id), nft.paletteOf(id), nft.patternOf(id), stage,
            nft.traitsReady(id), available, value, weight, nft.artworkBaseURI()));
    }

    function _ownedCollection(uint256 id) private view returns (IMetadataCollection nft) {
        nft = IMetadataCollection(access.module(Ids.NFT));
        nft.ownerOf(id);
    }

    function _markedValue(uint256 id, IMetadataCollection nft) private view returns (bool, uint256) {
        if (IMetadataRoyaltyWeight(nft.royaltyRewards()).weightOf(id) == 0) return (true, 0);
        try this.currentValue(id) returns (uint256 value) { return (true, value); }
        catch { return (false, 0); }
    }

    function _evolutionStage(uint256 id, uint256 value, uint256 weight) private view returns (uint8) {
        if (weight == 0) return 0;
        if (IZZZVault(access.module(Ids.VAULT)).nftStatus(id) == PositionStatus.Exited) return 4;
        IZZZProtocolPolicy.MetadataPolicy memory policy = IZZZProtocolPolicy(access.protocolPolicy()).metadataPolicy();
        return value >= policy.singularityUSD ? 3 : value >= policy.enhancedUSD ? 2 : 1;
    }

    function render(NFTMetadataInput memory input) public pure returns (string memory) {
        string memory rarity = input.traitsReady ? _rarity(input.rarity) : "Unrevealed";
        string memory state = input.valuationAvailable ? _stage(input.stage) : "Valuation unavailable";
        string memory image;
        if (input.traitsReady) {
            // Activated art is labelled as fallback, never a fabricated Dormant
            // state, when current marked LP valuation cannot be established.
            image = string.concat(input.baseURI, _palette(input.palette, true), "-", _patternFile(input.pattern), "-",
                _rarityFile(input.rarity), "-", _stageFile(input.valuationAvailable ? input.stage : 1), ".svg");
        } else {
            image = string.concat("data:image/svg+xml;base64,", Base64.encode(bytes(
                '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="800"><rect width="640" height="800" fill="#030a1d"/><ellipse cx="320" cy="365" rx="150" ry="210" fill="#08142a" stroke="#46637a"/><text x="320" y="680" fill="#aac7d8" text-anchor="middle" font-size="20">Awaiting verifiable randomness</text></svg>')));
        }
        string memory description = input.stage == 4 ?
            "LP exited. Returned principal entitlement, unclaimed rewards and future royalty rights follow this NFT." :
            !input.traitsReady ? "Dormant NFT. Verifiable rarity, palette and circuit reveal pending." :
            input.valuationAvailable ? "Permanent LP fee rights follow this NFT. Rarity weights only NFT-sale royalties." :
            "Current LP valuation unavailable. Activated artwork is a fallback; royalty eligibility and fee rights remain.";
        bytes memory json = abi.encodePacked('{"name":"PoPL #', Strings.toString(input.id),
            '","description":"', description, '","image":"', Strings.escapeJSON(image),
            '","valuation_available":', input.valuationAvailable ? "true" : "false",
            ',"lp_exited":', input.stage == 4 ? "true" : "false",
            ',"royalty_activated":', input.royaltyWeight != 0 ? "true" : "false",
            ',"lp_value_usd_18":', input.valuationAvailable ? string.concat('"', Strings.toString(input.valueUSD), '"') : "null",
            ',"attributes":[{"trait_type":"Rarity","value":"', rarity,
            '"}', _visualAttributes(input), ',{"trait_type":"Evolution","value":"', state,
            '"},{"trait_type":"NFT-sale royalty weight","value":',
            input.traitsReady ? Strings.toString(uint256(input.rarity) + 1) : '"Unrevealed"', '}]}');
        return string.concat("data:application/json;base64,", Base64.encode(json));
    }

    function _rarity(uint8 value) private pure returns (string memory) {
        return value == 0 ? "Commun" : value == 1 ? "Rare" : "Legendary";
    }
    function _rarityFile(uint8 value) private pure returns (string memory) {
        return value == 0 ? "commun" : value == 1 ? "rare" : "legendary";
    }
    function _color(uint8 value) private pure returns (string memory) {
        string[8] memory labels = ["Cyan", "Blue", "Violet", "Emerald", "Amber", "Crimson", "Ivory", "Onyx"];
        return labels[value];
    }
    function _colorFile(uint8 value) private pure returns (string memory) {
        string[8] memory labels = ["cyan", "blue", "violet", "emerald", "amber", "crimson", "ivory", "onyx"];
        return labels[value];
    }
    function _palette(uint8 value, bool filename) private pure returns (string memory label) {
        uint8 colors = ZZZArtwork.mask(value);
        for (uint8 i; i < 8; ++i) {
            if ((colors & (uint8(1) << i)) != 0) {
                string memory part = filename ? _colorFile(i) : _color(i);
                label = bytes(label).length == 0 ? part : string.concat(label, filename ? "-" : " / ", part);
            }
        }
    }
    function _visualAttributes(NFTMetadataInput memory input) private pure returns (bytes memory attributes) {
        if (!input.traitsReady) return abi.encodePacked(
            ',{"trait_type":"Color style","value":"Unrevealed"}',
            ',{"trait_type":"Palette","value":"Unrevealed"}',
            ',{"trait_type":"Circuit pattern","value":"Unrevealed"}');
        string memory style = input.palette < 8 ? "Monochrome" : input.palette < 30 ? "Bicolor" : "Tricolor";
        attributes = abi.encodePacked(',{"trait_type":"Color style","value":"', style,
            '"},{"trait_type":"Palette","value":"', _palette(input.palette, false), '"}');
        uint8 colors = ZZZArtwork.mask(input.palette); uint256 number;
        for (uint8 i; i < 8; ++i) {
            if ((colors & (uint8(1) << i)) != 0) {
                attributes = abi.encodePacked(attributes, ',{"trait_type":"Color ', Strings.toString(++number),
                    '","value":"', _color(i), '"}');
            }
        }
        return abi.encodePacked(attributes, ',{"trait_type":"Circuit pattern","value":"', _pattern(input.pattern), '"}');
    }
    function _pattern(uint8 value) private pure returns (string memory) {
        string[4] memory labels = ["Flowing arcs", "Segmented panels", "Orbital rings", "Twin circuit routes"];
        return labels[value];
    }
    function _patternFile(uint8 value) private pure returns (string memory) {
        string[4] memory labels = ["arcs", "panels", "orbits", "ribs"];
        return labels[value];
    }
    function _stage(uint8 value) private pure returns (string memory) {
        if (value == 4) return "LP exited";
        string[4] memory labels = ["Dormant", "Activated", "Enhanced", "Singularity"];
        return labels[value];
    }
    function _stageFile(uint8 value) private pure returns (string memory) {
        if (value == 4) return "activated";
        string[4] memory labels = ["dormant", "activated", "enhanced", "singularity"];
        return labels[value];
    }
}
