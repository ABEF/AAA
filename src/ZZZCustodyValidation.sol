// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IZZZAccess,IZZZVault,IZZZPools} from "./interfaces/IZZZ.sol";
import {Ids,Position,PositionStatus,PoolConfig} from "./libraries/ZZZTypes.sol";
interface ILocalParkingState {
    function parkingNonce(uint256) external view returns(uint64);
    function custodyEpoch(uint256) external view returns(uint64);
}
/// @notice Read-only local parking checks. There is no external custody request,
/// recipient, destination binding, recovery deposit or conversion-exit helper.
contract ZZZCustodyValidation {
    address public immutable migration;
    IZZZAccess public immutable access;
    struct Parking {
        uint256 bucketId;bytes32 poolId;uint256 lpTokenId;uint256 totalShares;uint256 depositUSD;
        uint64 custodyEpoch;uint64 nonce;address token0;address token1;
        uint128 minimum0;uint128 minimum1;uint256 deadline;bytes32 reviewHash;
    }
    error Unauthorized();error InvalidState();
    constructor(address controller){migration=msg.sender;access=IZZZAccess(controller);}
    function validateParking(bytes calldata encoded) external view {
        if(msg.sender!=migration) revert Unauthorized();
        Parking memory r=abi.decode(encoded,(Parking));
        IZZZVault v=IZZZVault(access.module(Ids.VAULT));Position memory p=v.group(r.bucketId);
        PoolConfig memory c=IZZZPools(access.module(Ids.POOLS)).accounting(r.poolId);
        ILocalParkingState state=ILocalParkingState(migration);
        if(!access.isSealed() || !access.paused() || access.lpExitStarted() || r.reviewHash==bytes32(0) ||
            (r.minimum0==0 && r.minimum1==0) || r.lpTokenId==0 || r.nonce!=state.parkingNonce(r.bucketId) ||
            r.custodyEpoch!=state.custodyEpoch(r.bucketId) || p.status!=PositionStatus.Active || p.poolId!=r.poolId ||
            p.lpTokenId!=r.lpTokenId || p.depositUSD!=r.depositUSD ||
            r.totalShares==0 || v.bucketTotalShares(r.bucketId)!=r.totalShares ||
            c.key.currency0!=r.token0 || c.key.currency1!=r.token1) revert InvalidState();
    }
}
