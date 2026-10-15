// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZLiquidity, IZZZOracle, IZZZFees} from "./interfaces/IZZZ.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";

struct NFTMetadataInput {
    uint256 id;
    uint8 rarity;
    uint8 palette;
    uint8 pattern;
    uint8 stage;
    bool traitsReady;
    bool valuationAvailable;
    uint256 valueUSD;
    uint8 royaltyWeight;
    string baseURI;
}

/// @notice Read-only renderer. It never changes custody or reward eligibility.
/// Valuation fails closed while custody is remote/in-flight or dependencies are
/// unavailable; the NFT explicitly reports an unavailable marked LP value.
contract ZZZNFTMetadata {
    IZZZAccess public immutable access;
    error ValuationUnavailable();
    constructor(address controller) { access = IZZZAccess(controller); }

    function currentValue(uint256 id) external view returns (uint256 valueUSD) {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        uint256 bucket = vault.nftBucket(id);
        uint256 shares = vault.sharesOf(id); uint256 supply = vault.bucketTotalShares(bucket);
        Position memory position = vault.group(bucket);
        if (bucket == 0 || shares == 0 || supply < shares || position.status != PositionStatus.Active ||
            position.homeChain != block.chainid || position.homeVault != address(vault) ||
            position.locationChain != block.chainid || position.locationVault != address(vault) ||
            position.lpTokenId == 0) revert ValuationUnavailable();
        PoolConfig memory config = IZZZPools(access.module(Ids.POOLS)).accounting(position.poolId);
        (uint256 a0, uint256 a1) = IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(position.lpTokenId);
        IZZZFees fees = IZZZFees(access.module(Ids.FEES));
        a0 += position.idle0 + fees.compoundBalance(bucket, config.key.currency0);
        a1 += position.idle1 + fees.compoundBalance(bucket, config.key.currency1);
        IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
        uint256 nav = oracle.value(config.key.currency0, a0) + oracle.value(config.key.currency1, a1);
        return Math.mulDiv(nav, shares, supply);
    }

    function render(NFTMetadataInput calldata input) external pure returns (string memory) {
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
        string memory description = !input.traitsReady ? "Dormant NFT. Verifiable rarity, palette and circuit reveal pending." :
            input.valuationAvailable ? "Permanent LP fee rights follow this NFT. Rarity weights only NFT-sale royalties." :
            "Current LP valuation unavailable. Activated artwork is a fallback; royalty eligibility and fee rights remain.";
        bytes memory json = abi.encodePacked('{"name":"PoPL #', Strings.toString(input.id),
            '","description":"', description, '","image":"', Strings.escapeJSON(image),
            '","valuation_available":', input.valuationAvailable ? "true" : "false",
            ',"lp_value_usd_18":', input.valuationAvailable ? string.concat('"', Strings.toString(input.valueUSD), '"') : "null",
            ',"attributes":[{"trait_type":"Rarity","value":"', rarity,
            '"}', _visualAttributes(input), ',{"trait_type":"Evolution","value":"', state,
            '"},{"trait_type":"NFT-sale royalty weight","value":', Strings.toString(input.royaltyWeight), '}]}');
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
    function _visualAttributes(NFTMetadataInput calldata input) private pure returns (bytes memory attributes) {
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
        string[4] memory labels = ["Flowing arcs", "Segmented panels", "Orbital rings", "Vertical ribs"];
        return labels[value];
    }
    function _patternFile(uint8 value) private pure returns (string memory) {
        string[4] memory labels = ["arcs", "panels", "orbits", "ribs"];
        return labels[value];
    }
    function _stage(uint8 value) private pure returns (string memory) {
        string[4] memory labels = ["Dormant", "Activated", "Enhanced", "Singularity"];
        return labels[value];
    }
    function _stageFile(uint8 value) private pure returns (string memory) {
        string[4] memory labels = ["dormant", "activated", "enhanced", "singularity"];
        return labels[value];
    }
}
