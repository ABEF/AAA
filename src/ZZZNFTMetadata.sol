// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {Ids, Position, PositionStatus, PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZAccess, IZZZVault, IZZZPools, IZZZLiquidity, IZZZOracle, IZZZFees, IZZZStrategy} from "./interfaces/IZZZ.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";
import {ZZZArtwork} from "./libraries/ZZZArtwork.sol";
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
interface IMetadataLifecycleLens {
    function access() external view returns (address);
    function nft() external view returns (address);
    function metadataLifecycleState(uint256 id) external view returns(uint256 flags,uint256 ethAmount,uint256 zzzAmount,address successorController,address successorNFT);
    function metadataLifecycleContext(uint256 id) external view returns(bytes memory context,string memory label,uint256 flags,uint256 ethAmount,uint256 zzzAmount);
}

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
/// Valuation fails closed while principal is parked or dependencies are
/// unavailable; the NFT explicitly reports an unavailable marked LP value.
contract ZZZNFTMetadata {
    IZZZAccess public immutable access;
    uint256 public constant METADATA_LIFECYCLE_VERSION = 2;
    struct Lifecycle {
        uint256 flags;
        uint256 ethAmount;
        uint256 zzzAmount;
        address successorController;
        address successorNFT;
    }
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

    /// @notice Canonical schema2: exact traits, lifecycle and settlement reads.
    /// Snapshot block/time describe this call, never source publication freshness.
    /// Bound lifecycle dependency failure reverts rather than fabricating rights.
    function tokenMetadata(uint256 id) external view returns (string memory) {
        IMetadataCollection nft = _ownedCollection(id);
        (bool available, uint256 value) = _markedValue(id, nft);
        uint8 weight = uint8(IMetadataRoyaltyWeight(nft.royaltyRewards()).weightOf(id));
        uint8 stage = _evolutionStage(id, value, weight);
        NFTMetadataInput memory input=NFTMetadataInput(id,nft.rarityOf(id),nft.paletteOf(id),nft.patternOf(id),stage,
            nft.traitsReady(id),available,value,weight,nft.artworkBaseURI());
        return _renderCanonical(input,nft);
    }
    function _renderCanonical(NFTMetadataInput memory input,IMetadataCollection nft) private view returns(string memory) {
        (bytes memory context,string memory label,uint256 flags,uint256 ethAmount,uint256 zzzAmount)=
            _checkedLens(nft).metadataLifecycleContext(input.id);
        _checkFlags(flags);
        Lifecycle memory lifecycle=Lifecycle(flags,ethAmount,zzzAmount,address(0),address(0));
        return _render(input,context,_description(input,lifecycle),label);
    }

    /// @notice Price-free watcher key. Excludes NAV and snapshot block/time so
    /// repeated unchanged observations do not cause per-block notification writes.
    function metadataLifecycleFingerprint(uint256 id) external view returns (bytes32) {
        Lifecycle memory lifecycle=_lifecycle(id,_ownedCollection(id));
        return keccak256(abi.encode(lifecycle.flags,lifecycle.ethAmount,lifecycle.zzzAmount,
            lifecycle.successorController,lifecycle.successorNFT));
    }

    function _lifecycle(uint256 id,IMetadataCollection nft) private view returns (Lifecycle memory value) {
        (value.flags,value.ethAmount,value.zzzAmount,value.successorController,value.successorNFT)=_checkedLens(nft).metadataLifecycleState(id);
        _checkFlags(value.flags);
    }
    function _checkedLens(IMetadataCollection nft) private view returns(IMetadataLifecycleLens lens) {
        lens=IMetadataLifecycleLens(access.module(Ids.NFT_CANONICAL));
        if(lens.access()!=address(access) || lens.nft()!=address(nft))revert InvalidConfiguration();
    }
    function _checkFlags(uint256 flags) private pure {
        if(uint8(flags)!=METADATA_LIFECYCLE_VERSION || flags>>37!=0)revert InvalidConfiguration();
    }
    function _canonical(Lifecycle memory value) private pure returns(uint8){return uint8(value.flags>>8);}
    function _phase(Lifecycle memory value) private pure returns(uint8){return uint8(value.flags>>16);}
    function _flag(Lifecycle memory value,uint8 bit) private pure returns(bool){return (value.flags&(uint256(1)<<bit))!=0;}

    /// @dev Keys are fixed and values are already serialized/escaped internally.
    /// One shared encoder avoids duplicating large packed-ABI code per field set.
    function _field(bytes memory json,string memory key,string memory value) private pure returns (bytes memory) {
        return _append(_append(_append(_append(json,bytes(',"')),bytes(key)),bytes('":')),bytes(value));
    }
    function _append(bytes memory left,bytes memory right) private pure returns (bytes memory) {return bytes.concat(left,right);}
    function _quoted(string memory value) private pure returns (string memory) {
        return string(_append(_append(bytes('"'),bytes(value)),bytes('"')));
    }

    function _description(NFTMetadataInput memory input,Lifecycle memory value) private pure returns (string memory) {
        if(_canonical(value)==1)return "Replacement frozen. Financial actions are locked until recovery or completion.";
        if(_canonical(value)==2)return "Inert replacement import. These records cannot authorize financial actions.";
        if(_canonical(value)==3)return "Retired deployment. Rights use the verified successor; this retired NFT cannot exercise them.";
        if(_canonical(value)==4)return "Cancelled import. This deployment is permanently inert with no exercisable claims.";
        if(_flag(value,32))return "Replacement preparing. New mint/LP work is stopped; ownership and earned claims retain their separate rules.";
        if(_flag(value,33) && !_flag(value,34))return input.traitsReady?
            "LP permanently closed. This NFT was never activated: no principal return or royalty eligibility.":
            "LP permanently closed. Never activated: no principal return or royalty eligibility. Artwork reveal remains pending.";
        if(input.stage==4) {
            if(!_flag(value,35))return _exitDescription("Principal allocation pending.");
            if(_flag(value,36))return _exitDescription("Principal has already been paid; no principal remains payable.");
            if(value.ethAmount==0 && value.zzzAmount==0)return _exitDescription("Exact-unit allocation assigns no principal.");
            if(_phase(value)!=3)return _exitDescription("Principal allocated; distribution not ready.");
            return _exitDescription("Unpaid ETH/ZZZ principal follows current ownership until paid.");
        }
        if(_flag(value,33))return "Collective exit started. This NFT's bucket has not closed; principal not returned. Rewards and royalties remain.";
        return _previewDescription(input);
    }
    function _exitDescription(string memory reason) private pure returns (string memory) {
        return string(_append(_append(bytes("LP exited. "),bytes(reason)),bytes(" Unclaimed rewards and future royalties follow this NFT.")));
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

    /// @notice Stateless preview. Canonical tokenMetadata supplies lifecycle,
    /// settlement and snapshot context; caller-supplied preview inputs do not.
    function render(NFTMetadataInput memory input) public pure returns (string memory) {
        return _render(input,"",_previewDescription(input),"");
    }
    function _previewDescription(NFTMetadataInput memory input) private pure returns (string memory) {
        return input.stage == 4 ?
            "LP exited. Any remaining unpaid principal, unclaimed rewards and future royalty rights follow this NFT." :
            !input.traitsReady ? "Dormant NFT. Verifiable rarity, palette and circuit reveal pending." :
            input.royaltyWeight == 0 ? "Dormant NFT. Activation is required before LP fee and NFT-sale royalty eligibility." :
            input.valuationAvailable ? "Permanent LP fee rights follow this NFT. Rarity weights only NFT-sale royalties." :
            "Current LP valuation unavailable. Activated artwork is a fallback; royalty eligibility and fee rights remain.";
    }
    function _render(NFTMetadataInput memory input,bytes memory context,string memory description,string memory lifecycle)
        private pure returns (string memory) {
        string memory image;
        if (input.traitsReady) {
            // Activated art is labelled as fallback, never a fabricated Dormant
            // state, when current marked LP valuation cannot be established.
            bytes memory path=_append(bytes(input.baseURI),bytes(_palette(input.palette,true)));
            path=_append(_append(path,bytes("-")),bytes(_patternFile(input.pattern)));
            path=_append(_append(path,bytes("-")),bytes(_rarityFile(input.rarity)));
            path=_append(_append(path,bytes("-")),bytes(_stageFile(input.valuationAvailable?input.stage:1)));
            image=string(_append(path,bytes(".svg")));
        } else {
            image = string.concat("data:image/svg+xml;base64,", Base64.encode(bytes(
                '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="800"><rect width="640" height="800" fill="#030a1d"/><ellipse cx="320" cy="365" rx="150" ry="210" fill="#08142a" stroke="#46637a"/><text x="320" y="680" fill="#aac7d8" text-anchor="middle" font-size="20">Awaiting verifiable randomness</text></svg>')));
        }
        bytes memory header=_append(_append(bytes('{"name":"PoPL #'),bytes(Strings.toString(input.id))),bytes('"'));
        header=_field(header,"description",_quoted(description));
        header=_field(header,"image",_quoted(Strings.escapeJSON(image)));
        bytes memory json=_append(_append(_append(header,_valueContext(input)),context),_attributes(input,lifecycle));
        return string.concat("data:application/json;base64,",Base64.encode(json));
    }
    function _valueContext(NFTMetadataInput memory input) private pure returns (bytes memory) {
        bytes memory json=_field("","valuation_available",input.valuationAvailable?"true":"false");
        json=_field(json,"lp_exited",input.stage==4?"true":"false");
        json=_field(json,"royalty_activated",input.royaltyWeight!=0?"true":"false");
        return _field(json,"lp_value_usd_18",input.valuationAvailable?_quoted(Strings.toString(input.valueUSD)):"null");
    }
    function _attributes(NFTMetadataInput memory input,string memory lifecycle) private pure returns (bytes memory) {
        bytes memory traits=_append(bytes(',"attributes":[{"trait_type":"Rarity","value":'),
            bytes(_quoted(input.traitsReady?_rarity(input.rarity):"Unrevealed")));
        traits=_append(_append(traits,bytes("}")),_visualAttributes(input));
        traits=_append(traits,_attribute("Evolution",input.valuationAvailable?_stage(input.stage):"Valuation unavailable"));
        if(bytes(lifecycle).length!=0)traits=_append(traits,_attribute("Lifecycle",lifecycle));
        traits=_append(traits,bytes(',{"trait_type":"NFT-sale royalty weight","value":'));
        traits=_append(traits,bytes(input.traitsReady?Strings.toString(uint256(input.rarity)+1):'"Unrevealed"'));
        return _append(traits,bytes("}]}"));
    }
    function _attribute(string memory name,string memory value) private pure returns (bytes memory) {
        return _append(_append(_append(_append(bytes(',{"trait_type":"'),bytes(name)),
            bytes('","value":"')),bytes(value)),bytes('"}'));
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
        attributes=_append(_attribute("Color style",style),_attribute("Palette",_palette(input.palette,false)));
        uint8 colors = ZZZArtwork.mask(input.palette); uint256 number;
        for (uint8 i; i < 8; ++i) {
            if ((colors & (uint8(1) << i)) != 0) {
                attributes=_append(attributes,_attribute(string.concat("Color ",Strings.toString(++number)),_color(i)));
            }
        }
        return _append(attributes,_attribute("Circuit pattern",_pattern(input.pattern)));
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
