// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZAccess,IZZZVault,IZZZPools,IZZZLiquidity,IZZZOracle,IZZZStrategy,IPositionManagerMinimal} from "./interfaces/IZZZ.sol";
import {EmergencyRebalance} from "./interfaces/IZZZEmergency.sol";
import {Ids,Position,PositionStatus,PoolConfig,PoolKey} from "./libraries/ZZZTypes.sol";
interface ILocalParkingState {
    function parkingNonce(uint256) external view returns(uint64);
    function custodyEpoch(uint256) external view returns(uint64);
}
interface ICustodyRegistryRevision { function configurationRevision() external view returns(uint64); }
interface ICustodyExecutionFingerprint { function executionPortfolioFingerprint(uint256) external view returns(bytes32); }
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
    error Unauthorized();error InvalidState();
    constructor(address controller){migration=msg.sender;access=IZZZAccess(controller);}
    /// @notice Exact reviewed physical/accounting identity, including the
    /// immutable main/residual association. Only the fixed parent forwards it.
    function emergencyCustodyHash(uint256 bucket) external view returns(bytes32) {
        if (msg.sender != migration) revert Unauthorized();
        IZZZVault vault = IZZZVault(access.module(Ids.VAULT));
        Position memory p = vault.group(bucket);
        return keccak256(abi.encode(block.chainid,address(vault),bucket,p,vault.bucketTotalShares(bucket),
            ICustodyExecutionFingerprint(access.module(Ids.LIQUIDITY)).executionPortfolioFingerprint(p.lpTokenId)));
    }
    /// @notice Read-only computation moved out of the custody-bearing parent.
    /// The parent still authenticates its Budget and active emergency context.
    function emergencyFingerprint(EmergencyRebalance calldata request) external view returns(bytes32 result) {
        if (msg.sender != migration) revert Unauthorized();
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
    function validateParking(bytes calldata encoded) external view {
        if(msg.sender!=migration) revert Unauthorized();
        Parking memory r=abi.decode(encoded,(Parking));
        IZZZVault v=IZZZVault(access.module(Ids.VAULT));Position memory p=v.group(r.bucketId);
        PoolConfig memory c=IZZZPools(access.module(Ids.POOLS)).accounting(r.poolId);
        ILocalParkingState state=ILocalParkingState(migration);
        if(!access.isSealed() || !access.paused() || access.lpExitStarted() || r.reviewHash==bytes32(0) ||
            (r.minimum0==0 && r.minimum1==0) || r.lpTokenId==0 || r.nonce!=state.parkingNonce(r.bucketId) ||
            r.custodyEpoch!=state.custodyEpoch(r.bucketId) || p.status!=PositionStatus.Active || p.poolId!=r.poolId ||
            p.lpTokenId!=r.lpTokenId || p.depositUSD!=r.depositUSD || r.portfolioHash==bytes32(0) ||
            ICustodyExecutionFingerprint(access.module(Ids.LIQUIDITY)).executionPortfolioFingerprint(r.lpTokenId)!=r.portfolioHash ||
            r.totalShares==0 || v.bucketTotalShares(r.bucketId)!=r.totalShares ||
            c.key.currency0!=r.token0 || c.key.currency1!=r.token1) revert InvalidState();
    }
}
