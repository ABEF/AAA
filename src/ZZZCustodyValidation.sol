// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZAccess,IZZZVault,IZZZPools,IZZZLiquidity,IZZZOracle,IZZZStrategy,IZZZRewards,IPositionManagerMinimal,IStateViewMinimal} from "./interfaces/IZZZ.sol";
import {EmergencyRebalance} from "./interfaces/IZZZEmergency.sol";
import {Ids,Position,PositionStatus,PoolConfig,PoolKey} from "./libraries/ZZZTypes.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
interface ILocalParkingState {
    function parkingNonce(uint256) external view returns(uint64);
    function custodyEpoch(uint256) external view returns(uint64);
    function currentZZZ() external view returns(address);
}
interface IExitTokenRegistry { function activationAssets() external view returns(address); }
interface IExitTokenIdentity { function zzz() external view returns(address); }
interface ICustodyRegistryRevision { function configurationRevision() external view returns(uint64); }
interface ICustodyExecutionFingerprint {
    function executionPortfolioFingerprint(uint256) external view returns(bytes32);
    function activeSecondaryCount() external view returns(uint256);
    function stateView() external view returns(address);
}
interface IResidualPolicyControl { function controlFingerprint(bytes32) external view returns(bytes32); }
/// @notice Read-only local parking checks. There is no external custody request,
/// recipient, destination binding, recovery deposit or conversion-exit helper.
contract ZZZCustodyValidation {
    address public immutable migration;
    IZZZAccess public immutable access;
    struct Parking {
        uint256 bucketId;bytes32 poolId;uint256 lpTokenId;uint256 totalShares;uint256 depositUSD;
        uint64 custodyEpoch;uint64 nonce;address token0;address token1;
        uint128 minimum0;uint128 minimum1;uint256 deadline;bytes32 reviewHash;bytes32 portfolioHash;
    }
    struct Consolidation { bytes32 mainHash; uint128 liquidity; uint256 secondary; uint256 count; }
    struct ResidualClose { bytes32 mainHash; uint256 idle0; uint256 idle1; uint256 secondary; }
    error Unauthorized();error InvalidState();error InvalidConfiguration();error Slippage();
    constructor(address controller){migration=msg.sender;access=IZZZAccess(controller);}
    /// @notice Bootstrap identity checks only. Governance and the one-time
    /// storage writes remain in Migration; every dependency read is public.
    function validateZZZ(address token,bytes32 codeHash,bytes32 reviewHash) external view {
        if(msg.sender!=migration) revert Unauthorized();
        if(access.isSealed() || ILocalParkingState(migration).currentZZZ()!=address(0) ||
            token.code.length==0 || token.codehash!=codeHash || reviewHash==bytes32(0) ||
            !IZZZRewards(access.module(Ids.REWARDS)).isAsset(token)) revert InvalidConfiguration();
        address buyback=access.module(Ids.BUYBACK);
        address source=IExitTokenRegistry(access.module(Ids.POOLS)).activationAssets();
        if(buyback.code.length==0 || IExitTokenIdentity(buyback).zzz()!=token ||
            IExitTokenIdentity(source).zzz()!=token) revert InvalidConfiguration();
    }
    /// @notice Exact reviewed physical/accounting identity, including the
    /// immutable main/residual association. Only the fixed parent forwards it.
    function emergencyCustodyHash(uint256 bucket) external view returns(bytes32) {
        if (msg.sender != migration) revert Unauthorized();
        return _emergencyCustodyHash(bucket);
    }
    function _emergencyCustodyHash(uint256 bucket) private view returns(bytes32) {
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(bucket);
        return keccak256(abi.encode(block.chainid,address(vault),bucket,p,vault.bucketTotalShares(bucket),
            ICustodyExecutionFingerprint(access.module(Ids.LIQUIDITY)).executionPortfolioFingerprint(p.lpTokenId)));
    }
    /// @notice Replay-resistant review identity; a raw close, park or earlier
    /// reinvestment consumes the same local nonce/epoch even if assets return.
    function consolidationCustodyHash(uint256 bucket) external view returns(bytes32) {
        if(msg.sender!=migration) revert Unauthorized();
        return _consolidationCustodyHash(bucket);
    }
    function _consolidationCustodyHash(uint256 bucket) private view returns(bytes32) {
        ILocalParkingState state=ILocalParkingState(migration);
        return keccak256(abi.encode("ZZZ_RESIDUAL_REINVEST_V1",_emergencyCustodyHash(bucket),
            state.parkingNonce(bucket),state.custodyEpoch(bucket),_control(bucket)));
    }
    function _control(uint256 bucket) private view returns(bytes32) {
        bytes32 pool=IZZZVault(access.module(Ids.VAULT)).group(bucket).poolId;
        return IResidualPolicyControl(IZZZStrategy(access.module(Ids.STRATEGY)).portfolioPolicy()).controlFingerprint(pool);
    }
    /// @notice Existing emergency validation stays identical; moving it to the
    /// immutable read-only child leaves room for the typed custody coordinator.
    function validateEmergency(EmergencyRebalance calldata r) external view {
        if(msg.sender!=migration) revert Unauthorized();
        _request(r);
        if(r.custodyHash!=_emergencyCustodyHash(r.bucket)) revert InvalidConfiguration();
    }
    function _request(EmergencyRebalance calldata r) private view {
        if(!access.isSealed() || !access.paused() || r.checks>31 || r.bucket==0 ||
            r.amountIn>uint128(type(int128).max) || r.minimumOut>uint128(type(int128).max) ||
            r.minimumLiquidity==0 || r.lower<TickMath.MIN_TICK || r.upper>TickMath.MAX_TICK ||
            r.lower>=r.upper || r.reviewHash==bytes32(0) ||
            (r.amountIn==0 ? r.swapPool!=bytes32(0) || r.minimumOut!=0 :
                r.swapPool==bytes32(0) || r.minimumOut==0)) revert InvalidConfiguration();
    }
    function captureConsolidation(EmergencyRebalance calldata r,bool forced) external view returns(Consolidation memory s) {
        if(msg.sender!=migration) revert Unauthorized();
        _request(r);
        if(r.custodyHash!=_consolidationCustodyHash(r.bucket) || (!forced &&
            (r.checks!=14 || r.swapPool!=bytes32(0) || r.zeroForOne || r.amountIn!=0 || r.minimumOut!=0)))
            revert InvalidConfiguration();
        s=_consolidation(r.bucket,!forced);
        IZZZVault vault=IZZZVault(access.module(Ids.VAULT));
        Position memory p=vault.group(r.bucket);
        (int24 lower,int24 upper)=IZZZLiquidity(access.module(Ids.LIQUIDITY)).ticks(p.lpTokenId);
        if(r.lower!=lower || r.upper!=upper || (s.secondary==0 && p.idle0==0 && p.idle1==0)) revert InvalidState();
    }
    function verifyConsolidation(EmergencyRebalance calldata r,bool forced,Consolidation calldata beforeState) external view {
        if(msg.sender!=migration) revert Unauthorized();
        Consolidation memory afterState=_consolidation(r.bucket,!forced);
        if(afterState.mainHash!=beforeState.mainHash || afterState.secondary!=0 ||
            uint256(afterState.liquidity)<uint256(beforeState.liquidity)+r.minimumLiquidity ||
            afterState.count+(beforeState.secondary==0?0:1)!=beforeState.count) revert InvalidState();
    }
    /// @dev Excludes ONLY intended changes (idle, main liquidity, residual).
    /// Main ownership/full metadata and all economic/control identities remain.
    function _consolidation(uint256 bucket,bool active) private view returns(Consolidation memory s) {
        IZZZVault vault=IZZZVault(access.module(Ids.VAULT));
        Position memory p=vault.group(bucket);
        IZZZLiquidity manager=IZZZLiquidity(access.module(Ids.LIQUIDITY));
        IPositionManagerMinimal posm=IPositionManagerMinimal(manager.positionManager());
        (PoolKey memory key,uint256 info)=posm.getPoolAndPositionInfo(p.lpTokenId);
        int24 lower=int24(uint24(info>>8));int24 upper=int24(uint24(info>>32));
        s.liquidity=posm.getPositionLiquidity(p.lpTokenId);
        uint256 shares=vault.bucketTotalShares(bucket);
        if(!access.isSealed() || !access.paused() || access.lpExitStarted() || p.status!=PositionStatus.Active ||
            p.lpTokenId==0 || shares==0 || s.liquidity==0 || posm.ownerOf(p.lpTokenId)!=address(vault) ||
            keccak256(abi.encode(key))!=p.poolId || lower<TickMath.MIN_TICK || upper>TickMath.MAX_TICK || lower>=upper)
            revert InvalidState();
        if(active) {
            (,int24 tick,,)=IStateViewMinimal(ICustodyExecutionFingerprint(address(manager)).stateView()).getSlot0(p.poolId);
            if(tick<lower || tick>=upper) revert InvalidState();
        }
        s.secondary=manager.secondaryId(p.lpTokenId);
        s.count=ICustodyExecutionFingerprint(address(manager)).activeSecondaryCount();
        ILocalParkingState state=ILocalParkingState(migration);
        s.mainHash=keccak256(abi.encode(p.poolId,p.lpTokenId,p.depositUSD,p.centerX96,p.lastRebalance,p.status,
            shares,posm.ownerOf(p.lpTokenId),key,info,access.governance(),state.parkingNonce(bucket),state.custodyEpoch(bucket),
            ICustodyRegistryRevision(access.module(Ids.POOLS)).configurationRevision(),_control(bucket)));
    }
    /// @notice Read-only computation moved out of the custody-bearing parent.
    /// The parent still authenticates its Budget and active emergency context.
    function emergencyFingerprint(EmergencyRebalance calldata request) external view returns(bytes32 result) {
        if (msg.sender != migration) revert Unauthorized();
        return _emergencyFingerprint(request);
    }
    /// @dev Domain separation prevents an explicit full-replacement manifest
    /// from being reused as a same-main operation; policy is mandatory even at0.
    function consolidationEmergencyFingerprint(EmergencyRebalance calldata request) external view returns(bytes32) {
        if(msg.sender!=migration) revert Unauthorized();
        return keccak256(abi.encode("ZZZ_RESIDUAL_REINVEST_V1",_emergencyFingerprint(request),_control(request.bucket)));
    }
    function _emergencyFingerprint(EmergencyRebalance calldata request) private view returns(bytes32 result) {
        result = keccak256(abi.encode(request,access.governance(),
            ICustodyRegistryRevision(access.module(Ids.POOLS)).configurationRevision()));
        if ((request.checks & 6) != 0) {
            PoolConfig memory c = IZZZPools(access.module(Ids.POOLS)).accounting(
                IZZZVault(access.module(Ids.VAULT)).group(request.bucket).poolId);
            IZZZOracle oracle = IZZZOracle(access.module(Ids.ORACLE));
            (,,bytes32 a) = oracle.priceBounds(c.key.currency0); (,,bytes32 b) = oracle.priceBounds(c.key.currency1);
            result = keccak256(abi.encode(result,a,b,IZZZStrategy(access.module(Ids.STRATEGY)).executionQualityRevision()));
        }
    }
    /// @notice Residual-only closure must preserve the complete main position,
    /// its NFT custody/liquidity and all bucket fields except attributed idle.
    /// Policy/Registry changes during callbacks also invalidate the review.
    /// Neither USD prices nor desired residual mode are changed or required.
    function residualMainFingerprint(uint256 bucket) external view returns(bytes32) {
        if(msg.sender != migration) revert Unauthorized();
        return _residualMainFingerprint(bucket);
    }
    function _residualMainFingerprint(uint256 bucket) private view returns(bytes32) {
        IZZZVault vault=IZZZVault(access.module(Ids.VAULT));
        Position memory p=vault.group(bucket);
        IZZZLiquidity manager=IZZZLiquidity(access.module(Ids.LIQUIDITY));
        IPositionManagerMinimal posm=IPositionManagerMinimal(manager.positionManager());
        (PoolKey memory key,uint256 info)=posm.getPoolAndPositionInfo(p.lpTokenId);
        return keccak256(abi.encode(p.poolId,p.lpTokenId,p.depositUSD,p.centerX96,p.lastRebalance,p.status,
            vault.bucketTotalShares(bucket),posm.ownerOf(p.lpTokenId),key,info,posm.getPositionLiquidity(p.lpTokenId),
            ICustodyRegistryRevision(access.module(Ids.POOLS)).configurationRevision(),
            IResidualPolicyControl(IZZZStrategy(access.module(Ids.STRATEGY)).portfolioPolicy()).controlFingerprint(p.poolId)));
    }
    /// @notice Paused governance may accept both raw receipt floors as zero;
    /// custody, actual receipt accounting and every supplied positive floor remain binding.
    function validateParking(bytes calldata encoded) external view {
        if(msg.sender!=migration) revert Unauthorized();
        Parking memory r=abi.decode(encoded,(Parking));
        _validateParking(r);
    }
    function _validateParking(Parking memory r) private view {
        IZZZVault v=IZZZVault(access.module(Ids.VAULT));Position memory p=v.group(r.bucketId);
        PoolConfig memory c=IZZZPools(access.module(Ids.POOLS)).accounting(r.poolId);
        ILocalParkingState state=ILocalParkingState(migration);
        if(!access.isSealed() || !access.paused() || access.lpExitStarted() || r.reviewHash==bytes32(0) ||
            r.lpTokenId==0 || r.nonce!=state.parkingNonce(r.bucketId) ||
            r.custodyEpoch!=state.custodyEpoch(r.bucketId) || p.status!=PositionStatus.Active || p.poolId!=r.poolId ||
            p.lpTokenId!=r.lpTokenId || p.depositUSD!=r.depositUSD || r.portfolioHash==bytes32(0) ||
            ICustodyExecutionFingerprint(access.module(Ids.LIQUIDITY)).executionPortfolioFingerprint(r.lpTokenId)!=r.portfolioHash ||
            r.totalShares==0 || v.bucketTotalShares(r.bucketId)!=r.totalShares ||
            c.key.currency0!=r.token0 || c.key.currency1!=r.token1) revert InvalidState();
    }
    /// @notice Raw-close extraction retains original error and nonce/epoch
    /// checks. This immutable child never writes custody or calls an executor.
    function captureResidualClose(bytes calldata encoded) external view returns(ResidualClose memory s) {
        if(msg.sender!=migration) revert Unauthorized();
        Parking memory r=abi.decode(encoded,(Parking)); _validateParking(r);
        s.secondary=IZZZLiquidity(access.module(Ids.LIQUIDITY)).secondaryId(r.lpTokenId);
        if(s.secondary==0) revert InvalidState();
        Position memory p=IZZZVault(access.module(Ids.VAULT)).group(r.bucketId);
        s.mainHash=_residualMainFingerprint(r.bucketId); s.idle0=p.idle0; s.idle1=p.idle1;
    }
    function verifyResidualClose(bytes calldata encoded,ResidualClose calldata beforeState)
        external view returns(uint256 amount0,uint256 amount1) {
        if(msg.sender!=migration) revert Unauthorized();
        Parking memory r=abi.decode(encoded,(Parking));
        Position memory p=IZZZVault(access.module(Ids.VAULT)).group(r.bucketId);
        amount0=p.idle0-beforeState.idle0; amount1=p.idle1-beforeState.idle1;
        ILocalParkingState state=ILocalParkingState(migration);
        if(!access.isSealed() || !access.paused() || _residualMainFingerprint(r.bucketId)!=beforeState.mainHash ||
            state.parkingNonce(r.bucketId)!=r.nonce+1 || state.custodyEpoch(r.bucketId)!=r.custodyEpoch ||
            IZZZLiquidity(access.module(Ids.LIQUIDITY)).secondaryId(r.lpTokenId)!=0 ||
            amount0<r.minimum0 || amount1<r.minimum1) revert Slippage();
    }
}
