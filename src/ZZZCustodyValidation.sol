// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZAccess,IZZZVault,IZZZPools,IZZZRewards,IZZZOracle} from "./interfaces/IZZZ.sol";
import {Ids,Position,PositionStatus,PoolConfig} from "./libraries/ZZZTypes.sol";
interface ICustodyParkingState {
    function currentZZZ() external view returns(address);
    function zzzCodeHash() external view returns(bytes32);
    function sourceSnapshot(uint256) external view returns(bytes32);
    function activePlan(uint256) external view returns(bytes32);
    function parkingNonce(uint256) external view returns(uint64);
    function custodyEpoch(uint256) external view returns(uint64);
}
/// @notice Immutable read-only validation companion, not a custody/execution path.
contract ZZZCustodyValidation {
    address public immutable migration;
    IZZZAccess public immutable access;
    struct Parking {
        uint256 bucketId;bytes32 poolId;uint256 lpTokenId;uint256 totalShares;uint256 depositUSD;
        uint64 custodyEpoch;uint64 nonce;address token0;address token1;
        uint128 minimum0;uint128 minimum1;uint256 deadline;bytes32 reviewHash;
    }
    error Unauthorized();error InvalidState();error InvalidConfiguration();
    struct Request {
        uint256 bucket; bytes32 sourceSnapshot; address recipient; bytes32 recipientCodeHash;
        address destinationCustody; bytes32 destinationPool;
        address output0; address output1; uint256 minimum0; uint256 minimum1;
        bool rawExit; uint256 exitMinimum0; uint256 exitMinimum1;
        uint256 minimumZZZ; uint256 deadline; bytes32 reviewHash;
    }
    constructor(address controller){migration=msg.sender;access=IZZZAccess(controller);}
    function validateRequest(bytes calldata encoded) external view {
        if(msg.sender!=migration || access.module(Ids.MIGRATION)!=migration) revert Unauthorized();
        Request memory r=abi.decode(encoded,(Request));ICustodyParkingState state=ICustodyParkingState(migration);
        IZZZVault v=IZZZVault(access.module(Ids.VAULT));Position memory p=v.group(r.bucket);
        address token=state.currentZZZ();
        bool custodyOnly=r.destinationPool==bytes32(0) && r.destinationCustody==r.recipient;
        if(!access.isSealed() || r.bucket==0 || state.activePlan(r.bucket)!=bytes32(0) ||
            (p.status!=PositionStatus.Active && p.status!=PositionStatus.Parked) ||
            v.bucketTotalShares(r.bucket)==0 || r.sourceSnapshot!=state.sourceSnapshot(r.bucket) || (!r.rawExit && (token==address(0) ||
            token.codehash!=state.zzzCodeHash())) || r.recipient==address(0) || r.recipient==migration || r.recipient==address(this) ||
            r.recipient==address(v) || r.recipient.codehash!=r.recipientCodeHash ||
            r.destinationCustody==address(0) || (!custodyOnly && r.destinationPool==bytes32(0)) || r.output1==address(0) || r.output0==r.output1 || (!custodyOnly && r.minimum0==0 && r.minimum1==0) ||
            (r.rawExit ? (r.exitMinimum0==0 && r.exitMinimum1==0) : r.minimumZZZ==0) || r.reviewHash==bytes32(0)) revert InvalidConfiguration();
    }
    function validateDestination(bytes calldata encoded) external view returns(uint256,uint256,uint256,uint256) {
        if(msg.sender!=migration || access.module(Ids.MIGRATION)!=migration) revert Unauthorized();
        Request memory r=abi.decode(encoded,(Request));
        IZZZVault v=IZZZVault(access.module(Ids.VAULT));
        PoolConfig memory target=IZZZPools(access.module(Ids.POOLS)).accounting(r.destinationPool);
        IZZZRewards rewards=IZZZRewards(access.module(Ids.REWARDS));
        if(r.destinationCustody!=address(v) || v.poolBucket(r.destinationPool)!=r.bucket || !target.operationsEnabled ||
            target.key.currency0!=r.output0 || target.key.currency1!=r.output1 ||
            !rewards.isAsset(r.output0) || !rewards.isAsset(r.output1)) revert InvalidConfiguration();
        if(r.rawExit) return(0,0,0,0);
        IZZZOracle oracle=IZZZOracle(access.module(Ids.ORACLE));
        return(oracle.price(r.output0),oracle.price(r.output1),10**oracle.tokenDecimals(r.output0),10**oracle.tokenDecimals(r.output1));
    }
    function validateParking(bytes calldata encoded) external view {
        if(msg.sender!=migration) revert Unauthorized();
        Parking memory r=abi.decode(encoded,(Parking));
        IZZZVault v=IZZZVault(access.module(Ids.VAULT));Position memory p=v.group(r.bucketId);
        PoolConfig memory c=IZZZPools(access.module(Ids.POOLS)).accounting(r.poolId);
        ICustodyParkingState state=ICustodyParkingState(migration);
        if(!access.isSealed() || !access.paused() || r.reviewHash==bytes32(0) || (r.minimum0==0 && r.minimum1==0) ||
            r.lpTokenId==0 || state.activePlan(r.bucketId)!=bytes32(0) || r.nonce!=state.parkingNonce(r.bucketId) ||
            r.custodyEpoch!=state.custodyEpoch(r.bucketId) || p.status!=PositionStatus.Active || p.poolId!=r.poolId ||
            p.lpTokenId!=r.lpTokenId || p.depositUSD!=r.depositUSD ||
            r.totalShares==0 || v.bucketTotalShares(r.bucketId)!=r.totalShares ||
            c.key.currency0!=r.token0 || c.key.currency1!=r.token1) revert InvalidState();
    }
}
