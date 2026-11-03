// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ZZZActivationAssets} from "./ZZZActivationAssets.sol";
import {IZZZNFT, IZZZPools, IZZZOracle} from "./interfaces/IZZZ.sol";
import {Ids, PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {ZZZContributionPricing} from "./ZZZContributionPricing.sol";
import {IZZZProtocolPolicy} from "./interfaces/IZZZProtocolPolicy.sol";

interface IActivationVault {
    function activate(uint256, bytes32, uint256, uint256, uint128, uint256) external payable;
    function increase(uint256, uint256, uint256, uint128, uint256) external payable;
}
/// @notice Atomic owner-funded ETH/ZZZ contribution into the permanent LP Vault.
/// The Registry creates this immutable child. No arbitrary executor, recipient,
/// user-supplied USD value, NFT custody, permit or token rescue path exists.
contract ZZZActivationEntry is ZZZModule, ReentrancyGuard {
    /// @notice Direct pair-input ABI. Historical routed requests are incompatible.
    uint256 public constant ENTRY_ROUTING_VERSION = 3;
    /// @notice Signed contribution policy: no legacy unbounded entry fallback.
    uint256 public constant REVIEW_POLICY_VERSION = 2;
    address public immutable registry;
    ZZZActivationAssets public immutable activationAssets;

    struct Request {
        uint256 nftId;
        bytes32 poolId;
        address sourceAsset; // Zero is native ETH, distinct from every ERC20.
        uint256 amountIn;
        uint128 minimumLiquidity;
        uint256 deadline;
        bool increase;
    }
    struct Context {
        address owner;
        uint256 nftId;
        bytes32 callHash;
        bytes32 poolId;
        uint256 amount0;
        uint256 amount1;
        uint256 grossUSD;
    }
    Context private context;
    event SourceContributed(address indexed owner, uint256 indexed nftId, bytes32 indexed poolId,
        address sourceAsset, uint256 sourceAmount, uint256 grossUSD, address output, uint256 outputAmount, bool increase);

    constructor(address controller, address poolRegistry, address assets) ZZZModule(controller) {
        if (poolRegistry == address(0) || msg.sender != poolRegistry || assets.code.length == 0 ||
            ZZZActivationAssets(assets).registry() != poolRegistry ||
            address(ZZZActivationAssets(assets).access()) != controller) revert InvalidConfiguration();
        registry = poolRegistry;
        activationAssets = ZZZActivationAssets(assets);
    }
    function _owner(uint256 id) private view returns (address) {
        return IZZZNFT(access.module(Ids.NFT)).ownerOf(id);
    }
    function _vault() private view returns (address vault) {
        vault = access.module(Ids.VAULT);
        if (!access.isSealed() || access.module(Ids.POOLS) != registry || vault.code.length == 0) revert InvalidConfiguration();
    }

    /// @notice Only the canonical Vault may authorize this exact active call.
    /// ERC721 token/operator approval is never contribution authority.
    function validateOwner(uint256 id, bytes32 vaultCallHash) external view {
        Context memory c = context;
        if (msg.sender != _vault() || c.owner == address(0) || c.nftId != id ||
            c.callHash != vaultCallHash || _owner(id) != c.owner) revert Unauthorized();
    }
    /// @notice Only Registry valuation may replace pair-input value with the
    /// original, proven source value. An active mismatch MUST NOT fall back.
    function sourceValue(bytes32 poolId, uint256 amount0, uint256 amount1) external view returns (uint256) {
        if (msg.sender != registry) revert Unauthorized();
        Context memory c = context;
        if (c.owner == address(0)) return 0;
        if (c.poolId != poolId || c.amount0 != amount0 || c.amount1 != amount1 ||
            _owner(c.nftId) != c.owner) revert InvalidState();
        return c.grossUSD;
    }

    function _pricing() private view returns(ZZZContributionPricing) {
        return ZZZContributionPricing(IZZZOracle(access.module(Ids.ORACLE)).contributionPricing());
    }
    /// @notice The fixed pricing companion may adopt only this exact live Vault context.
    function pricingContext(uint256 id,bytes32 pool,uint256 packed,uint256 gross) external view returns(bool) {
        if (msg.sender != address(_pricing())) revert Unauthorized();
        Context memory c = context;
        return c.owner != address(0) && c.nftId == id && c.poolId == pool && c.grossUSD == gross &&
            c.amount0 <= type(uint128).max && c.amount1 <= type(uint128).max &&
            packed == (c.amount0 | (c.amount1 << 128)) && _owner(id) == c.owner;
    }

    /// @notice The signed maximum covers Vault balancing and placement loss; gas is separate.
    /// A tighter execution-time policy is allowed, but never a wider one than reviewed.
    function executeReviewed(Request calldata request, uint16 maximumLossBps,bytes32 expectedContributionPolicy)
        external payable live operating principalOperating nonReentrant {
        _deadline(request.deadline);
        IZZZProtocolPolicy policySource=IZZZProtocolPolicy(access.protocolPolicy());
        if(expectedContributionPolicy==bytes32(0) || policySource.entryFingerprint()!=expectedContributionPolicy)
            revert InvalidState();
        IZZZProtocolPolicy.EntryPolicy memory entryTerms=policySource.entryPolicy();
        address vault = _vault();
        if (request.amountIn == 0 || request.minimumLiquidity == 0 || _owner(request.nftId) != msg.sender) revert Unauthorized();
        PoolConfig memory pool = IZZZPools(registry).accounting(request.poolId);
        if (!pool.depositsEnabled || !pool.operationsEnabled ||
            pool.key.currency0 == pool.key.currency1) revert InvalidConfiguration();
        address source = request.sourceAsset;
        if (!activationAssets.isContributionAsset(source)) revert InvalidConfiguration();
        if (source != pool.key.currency0 && source != pool.key.currency1) revert InvalidConfiguration();
        if (msg.value != (source == address(0) ? request.amountIn : 0)) revert InvalidAmount();
        uint256 nativeBaseline = address(this).balance - msg.value;
        uint256 sourceBaseline = ExactAsset.balance(source,address(this)) - (source == address(0) ? msg.value : 0);
        // Freeze source + LP-pair prices BEFORE token pulls or approvals can
        // call external code. Both bounds come from two sources.
        uint256 grossUSD = activationAssets.value(source, request.amountIn);
        if (grossUSD == 0 || grossUSD < (request.increase?entryTerms.minGrowthUSD:entryTerms.minActivationUSD))
            revert InvalidAmount();
        if (_pricing().beginEntryReviewed(request.nftId,request.poolId,source,request.amountIn,maximumLossBps,
            expectedContributionPolicy) != grossUSD) revert InvalidState();
        if (source != address(0)) ExactToken.pull(source, msg.sender, request.amountIn);
        if (_owner(request.nftId) != msg.sender) revert Unauthorized();
        uint256 amount0 = source == pool.key.currency0 ? request.amountIn : 0;
        uint256 amount1 = source == pool.key.currency1 ? request.amountIn : 0;
        bytes memory payload = request.increase
            ? abi.encodeCall(IActivationVault.increase, (request.nftId, amount0, amount1, request.minimumLiquidity, request.deadline))
            : abi.encodeCall(IActivationVault.activate, (request.nftId, request.poolId, amount0, amount1, request.minimumLiquidity, request.deadline));
        // Token approval can call arbitrary token code. Context must remain
        // inactive until the immediate Vault call, whose own guard then protects
        // contribution valuation against unrelated callback-driven joins.
        ExactAsset.approve(source,vault, request.amountIn);
        if (_owner(request.nftId) != msg.sender) revert Unauthorized();
        context = Context(msg.sender, request.nftId, keccak256(payload), request.poolId, amount0, amount1, grossUSD);
        (bool success, bytes memory result) = vault.call{value: source == address(0) ? request.amountIn : 0}(payload);
        if (!success) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
        delete context;
        ExactAsset.approve(source,vault, 0);
        if (_owner(request.nftId) != msg.sender || ExactAsset.balance(source,address(this)) != sourceBaseline || address(this).balance != nativeBaseline) revert InvalidState();
        _pricing().endEntry();
        if(policySource.entryFingerprint()!=expectedContributionPolicy)revert InvalidState();
        emit SourceContributed(msg.sender, request.nftId, request.poolId, request.sourceAsset,
            request.amountIn, grossUSD, source, request.amountIn, request.increase);
    }
}
