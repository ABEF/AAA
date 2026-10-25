// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZCustodyValidation} from "./ZZZCustodyValidation.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {ExactAsset} from "./libraries/ExactAsset.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {Ids,Position,PositionStatus,PoolConfig} from "./libraries/ZZZTypes.sol";
import {IZZZVault,IZZZPools,IZZZOracle,IZZZLiquidity,IZZZRewards} from "./interfaces/IZZZ.sol";
interface ICustodyVault is IZZZVault {
    function migrationBudget() external view returns(address);
    function consolidateHandoff(uint256,address,uint256,uint256) external;
    function acceptHandoff(uint256,bytes32,uint256,uint256,uint128,uint256) external payable;
}
interface IMaintenanceLossPolicy { function maintenanceLossBps() external view returns(uint16); }
interface ICustodySourceRegistry { function activationAssets() external view returns(address); }
interface ICustodySourceIdentity { function zzz() external view returns(address); }
/// @notice Governed custody handoff; recipient custody/liveness are explicitly trusted.
/// Source-chain custody only; any bridge or issuer exchange happens outside PoPL.
/// No arbitrary call, delegatecall, sweep, timeout release or remote-completion proof.
contract ZZZMigration is ZZZModule, ReentrancyGuard {
    using SafeERC20 for IERC20;
    uint8 public constant CUSTODY_VERSION=2;
    enum Status { None, Approved, Sent, Completed, Recovered, Cancelled }
    struct ParkingRequest {
        uint256 bucketId; bytes32 poolId; uint256 lpTokenId; uint256 totalShares; uint256 depositUSD;
        uint64 custodyEpoch; uint64 nonce; address token0; address token1;
        uint128 minimum0; uint128 minimum1; uint256 deadline; bytes32 reviewHash;
    }
    struct Request {
        uint256 bucket; bytes32 sourceSnapshot; address recipient; bytes32 recipientCodeHash;
        address destinationCustody; bytes32 destinationPool;
        address output0; address output1; uint256 minimum0; uint256 minimum1;
        bool rawExit; uint256 exitMinimum0; uint256 exitMinimum1;
        uint256 minimumZZZ; uint256 deadline; bytes32 reviewHash;
    }
    struct Plan {
        Request request; bytes32 sourcePool; PositionStatus sourceStatus; Status status; uint256 shares;
        address zzz; address token0; address token1; uint256 sentZZZ;
        uint256 startingUSD;
        uint256 minimumRetainedUSD;
        uint256 sent0; uint256 sent1;
        uint256 outputPrice0; uint256 outputPrice1; uint256 outputScale0; uint256 outputScale1; uint256 departureBlock;
    }
    address public currentZZZ;
    bytes32 public zzzCodeHash;
    uint256 public sequence;
    uint256 public outstandingCount;
    mapping(bytes32=>Plan) private plans;
    mapping(uint256=>bytes32) public activePlan;
    mapping(uint256=>uint64) public custodyEpoch;
    mapping(uint256=>uint64) public parkingNonce;
    event ZZZConfigured(address indexed token,bytes32 codeHash,bytes32 reviewHash);
    event DestinationBound(bytes32 indexed id,bytes32 previousRequest,bytes32 newRequest,bytes32 destinationPool);
    event CustodyApproved(bytes32 indexed id,uint256 indexed bucket,address indexed recipient,address destinationCustody);
    event CustodySent(bytes32 indexed id,uint256 indexed bucket,address indexed recipient,uint256 zzzAmount);
    event CustodyCompleted(bytes32 indexed id,uint256 indexed bucket,uint256 lpTokenId);
    event CustodyAssetsSent(bytes32 indexed id,address token0,uint256 amount0,address token1,uint256 amount1,bool rawExit);
    event CustodyRecovered(bytes32 indexed id,uint256 indexed bucket,uint256 zzzAmount);
    event CustodyCancelled(bytes32 indexed id);
    event ParkingExecuted(bytes32 indexed requestHash,uint256 indexed bucketId,uint64 nonce,uint256 principal0,uint256 principal1);
    event ParkingInvalidated(uint256 indexed bucketId,uint64 nextNonce);
    ZZZCustodyValidation public immutable validation;
    constructor(address controller) ZZZModule(controller) {validation=new ZZZCustodyValidation(controller);}
    receive() external payable {
        if (msg.sender != access.module(Ids.VAULT)) revert Unauthorized();
    }
    function _balance(address asset) private view returns (uint256) { return ExactAsset.balance(asset,address(this)); }
    function _vault() private view returns(ICustodyVault) { return ICustodyVault(access.module(Ids.VAULT)); }
    function _pools() private view returns(IZZZPools) { return IZZZPools(access.module(Ids.POOLS)); }
    function request(bytes32 id) external view returns(Request memory) { return plans[id].request; }
    function state(bytes32 id) external view returns(Status,uint256,uint256,uint256,uint256) {
        Plan storage q=plans[id]; return(q.status,q.sent0,q.sent1,q.startingUSD,q.departureBlock);
    }
    function minimumRetainedUSD(bytes32 id) external view returns(uint256) { return plans[id].minimumRetainedUSD; }
    /// Bind the deployment's fixed ZZZ target once during bootstrap, before seal.
    /// Token-contract exchanges use external custody and a fresh reviewed deployment.
    function configureZZZ(address token,bytes32 codeHash,bytes32 reviewHash) external onlyGovernance nonReentrant {
        if(access.isSealed() || currentZZZ!=address(0) || outstandingCount!=0 || token.code.length==0 || token.codehash!=codeHash || reviewHash==bytes32(0) ||
            !IZZZRewards(access.module(Ids.REWARDS)).isAsset(token)) revert InvalidConfiguration();
        if(token!=ICustodySourceIdentity(ICustodySourceRegistry(address(_pools())).activationAssets()).zzz()) revert InvalidConfiguration();
        IZZZOracle(access.module(Ids.ORACLE)).price(token); currentZZZ=token; zzzCodeHash=codeHash;
        emit ZZZConfigured(token,codeHash,reviewHash);
    }
    function sourceSnapshot(uint256 bucket) public view returns(bytes32) {
        ICustodyVault v=_vault(); Position memory p=v.group(bucket); (uint256 a0,uint256 a1)=_amounts(p);
        return keccak256(abi.encode(block.chainid,address(this),address(v),bucket,p,v.bucketTotalShares(bucket),
            custodyEpoch[bucket],currentZZZ,zzzCodeHash,a0,a1));
    }
    function approve(Request calldata r) external onlyGovernance operating nonReentrant returns(bytes32 id) {
        _deadline(r.deadline); ICustodyVault v=_vault(); Position memory p=v.group(r.bucket);
        bool custodyOnly=r.destinationPool==bytes32(0) && r.destinationCustody==r.recipient;
        validation.validateRequest(abi.encode(r));
        PoolConfig memory source=_pools().accounting(p.poolId);
        if(!r.rawExit && source.key.currency0!=currentZZZ && source.key.currency1!=currentZZZ) revert InvalidConfiguration();
        id=keccak256(abi.encode("ZZZ_CUSTODY_V2",block.chainid,address(access),address(this),++sequence,r));
        Plan storage q=plans[id]; q.request=r; q.sourcePool=p.poolId; q.sourceStatus=p.status; q.status=Status.Approved;
        q.shares=v.bucketTotalShares(r.bucket); q.zzz=currentZZZ;
        q.token0=source.key.currency0; q.token1=source.key.currency1;
        IZZZOracle oracle=IZZZOracle(access.module(Ids.ORACLE)); (uint256 a0,uint256 a1)=_amounts(p);
        if(!r.rawExit) {
            q.startingUSD=oracle.value(q.token0,a0+p.idle0)+oracle.value(q.token1,a1+p.idle1);
            q.minimumRetainedUSD=_currentFloor(q.startingUSD);
            if(q.startingUSD==0 || oracle.value(currentZZZ,r.minimumZZZ)<q.minimumRetainedUSD) revert Slippage();
        }
        if(custodyOnly) {
            if(r.output0!=q.token0 || r.output1!=q.token1) revert InvalidConfiguration();
        } else {
            _bindDestination(q,r);
        }
        activePlan[r.bucket]=id; ++outstandingCount;
        emit CustodyApproved(id,r.bucket,r.recipient,r.destinationCustody);
    }
    /// @notice One-time local return destination for an already sent holding plan.
    /// Preserve source snapshot, actual departure, mode and original loss budget.
    function bindLocalDestination(bytes32 id,bytes32 pool,uint256 minimum0,uint256 minimum1,bytes32 reviewHash)
        external onlyGovernance operating nonReentrant {
        Plan storage q=plans[id];Request memory r=q.request;
        if(q.status!=Status.Sent || r.destinationPool!=bytes32(0) ||
            reviewHash==bytes32(0) || pool==bytes32(0) || (minimum0==0 && minimum1==0)) revert InvalidState();
        bytes32 previous=keccak256(abi.encode(r));PoolConfig memory target=_pools().accounting(pool);
        r.destinationPool=pool;r.destinationCustody=address(_vault());r.output0=target.key.currency0;r.output1=target.key.currency1;
        r.minimum0=minimum0;r.minimum1=minimum1;r.reviewHash=reviewHash;
        _bindDestination(q,r);q.request=r;
        emit DestinationBound(id,previous,keccak256(abi.encode(r)),pool);
    }
    function _bindDestination(Plan storage q,Request memory r) private {
        (q.outputPrice0,q.outputPrice1,q.outputScale0,q.outputScale1)=validation.validateDestination(abi.encode(r));
    }
    /// Migration Exit: close, convert ALL attributed principal to ZZZ, then send.
    /// Pause required; any close/swap/transfer failure rolls back this complete exit.
    function exit(bytes32 id) external onlyGovernance operating nonReentrant {
        Plan storage q=plans[id]; Request memory r=q.request; _deadline(r.deadline);
        if(q.status!=Status.Approved || !access.paused() || r.sourceSnapshot!=sourceSnapshot(r.bucket) ||
            r.recipient.codehash!=r.recipientCodeHash || (!r.rawExit && q.zzz.codehash!=zzzCodeHash)) revert InvalidState();
        ICustodyVault v=_vault();
        uint256 b0=_balance(q.token0); uint256 b1=_balance(q.token1);
        q.status=Status.Sent; q.departureBlock=block.number; ++custodyEpoch[r.bucket];
        if(q.sourceStatus==PositionStatus.Active) v.park(r.bucket,r.deadline);
        if(!r.rawExit) v.consolidateHandoff(r.bucket,q.zzz,r.minimumZZZ,r.deadline);
        (uint256 a0,uint256 a1)=v.releaseForMigration(r.bucket,id,r.deadline);
        if(r.rawExit) {
            if(a0<r.exitMinimum0 || a1<r.exitMinimum1) revert Slippage();
        } else if((q.zzz==q.token0?a1:a0)!=0 || (q.zzz==q.token0?a0:a1)<r.minimumZZZ) revert Slippage();
        if(_balance(q.token0)!=b0+a0 || _balance(q.token1)!=b1+a1) revert InvalidState();
        q.sent0=a0; q.sent1=a1; q.sentZZZ=q.zzz==address(0)?0:(q.zzz==q.token0?a0:(q.zzz==q.token1?a1:0));
        ExactAsset.push(q.token0,r.recipient,a0); ExactAsset.push(q.token1,r.recipient,a1);
        if(_balance(q.token0)!=b0 || _balance(q.token1)!=b1 ||
            v.bucketTotalShares(r.bucket)!=q.shares) revert InvalidState();
        emit CustodySent(id,r.bucket,r.recipient,q.sentZZZ);
        emit CustodyAssetsSent(id,q.token0,a0,q.token1,a1,r.rawExit);
    }
    function cancel(bytes32 id) external onlyDrainGovernance nonReentrant {
        Plan storage q=plans[id]; if(q.status!=Status.Approved) revert InvalidState();
        q.status=Status.Cancelled; _close(q,id); emit CustodyCancelled(id);
    }
    /// Actual funding + LP mint + original fixed-price approved budget in one transaction.
    function completeLocal(bytes32 id,uint256 a0,uint256 a1,uint128 minimumLiquidity,uint256 deadline)
        external payable live operating nonReentrant {
        _deadline(deadline); Plan storage q=plans[id]; Request memory r=q.request;
        if(q.status!=Status.Sent || r.destinationPool==bytes32(0) || a0<r.minimum0 ||
            a1<r.minimum1 || minimumLiquidity==0) revert InvalidState();
        PoolConfig memory target=_pools().accounting(r.destinationPool);
        if(target.key.currency0!=r.output0 || target.key.currency1!=r.output1) revert InvalidConfiguration();
        _receive(q,r.destinationPool,r.output0,r.output1,a0,a1,minimumLiquidity,deadline);
        Position memory p=_vault().group(r.bucket); (uint256 x,uint256 y)=_amounts(p);
        if(r.rawExit) {
            // Raw emergency approvals carry explicit destination token minima,
            // not a fabricated USD loss guarantee when pricing/markets fail.
            if(x+p.idle0<r.minimum0 || y+p.idle1<r.minimum1) revert Slippage();
        } else {
            uint256 retained=Math.mulDiv(x+p.idle0,q.outputPrice0,q.outputScale0)+Math.mulDiv(y+p.idle1,q.outputPrice1,q.outputScale1);
            if(retained<q.minimumRetainedUSD) revert Slippage();
        }
        if(p.status!=PositionStatus.Active || _vault().bucketTotalShares(r.bucket)!=q.shares) revert InvalidState();
        q.status=Status.Completed; _close(q,id); emit CustodyCompleted(id,r.bucket,p.lpTokenId);
    }
    /// Return every actually-sent source currency; no proof or invented remote balance.
    /// Anyone may fully fund recovery, including while ordinary operations are paused.
    function recover(bytes32 id,uint256 deadline) external payable operating nonReentrant {
        _deadline(deadline); Plan storage q=plans[id];
        if(q.status!=Status.Sent) revert InvalidState();
        uint256 a0=q.sent0; uint256 a1=q.sent1;
        _receive(q,q.sourcePool,q.token0,q.token1,a0,a1,0,deadline);
        if(_vault().bucketTotalShares(q.request.bucket)!=q.shares) revert InvalidState();
        q.status=Status.Recovered; _close(q,id); emit CustodyRecovered(id,q.request.bucket,q.sentZZZ);
    }
    function _receive(Plan storage q,bytes32 pool,address t0,address t1,uint256 a0,uint256 a1,uint128 minimum,uint256 deadline) private {
        ICustodyVault v=_vault(); if(v.group(q.request.bucket).status!=PositionStatus.Outbound ||
            v.bucketTotalShares(q.request.bucket)!=q.shares) revert InvalidState();
        uint256 nativeAmount=t0==address(0)?a0:(t1==address(0)?a1:0);
        if (msg.value!=nativeAmount || t0==t1) revert InvalidAmount();
        // This is the funding ingress. Existing ETH cannot cover missing value;
        // only this operation's declared native budget is forwarded to Vault.
        uint256 b0=_balance(t0)-(t0==address(0)?msg.value:0);
        uint256 b1=_balance(t1)-(t1==address(0)?msg.value:0);
        if (t0!=address(0)) { ExactToken.pull(t0,msg.sender,a0); IERC20(t0).forceApprove(address(v),a0); }
        if (t1!=address(0)) { ExactToken.pull(t1,msg.sender,a1); IERC20(t1).forceApprove(address(v),a1); }
        v.acceptHandoff{value:nativeAmount}(q.request.bucket,pool,a0,a1,minimum,deadline);
        if (t0!=address(0)) IERC20(t0).forceApprove(address(v),0);
        if (t1!=address(0)) IERC20(t1).forceApprove(address(v),0);
        if(_balance(t0)!=b0 || _balance(t1)!=b1) revert InvalidState();
    }
    function _close(Plan storage q,bytes32 id) private {
        if(activePlan[q.request.bucket]!=id) revert InvalidState(); delete activePlan[q.request.bucket]; --outstandingCount;
    }
    function _currentFloor(uint256 value) private view returns(uint256) {
        uint16 limit=IMaintenanceLossPolicy(_vault().migrationBudget()).maintenanceLossBps();
        if(limit>1000) revert InvalidConfiguration();
        return value-Math.mulDiv(value,limit,10000);
    }
    function _amounts(Position memory p) private view returns(uint256,uint256) {
        if(p.lpTokenId==0) return(0,0); return IZZZLiquidity(access.module(Ids.LIQUIDITY)).amounts(p.lpTokenId);
    }
    /// @notice Atomic pool-to-pool move. Never transfers principal to an external custodian.
    /// Only identical actual currencies are accepted; native ETH and WETH are distinct.
    /// One captured governed loss budget, unchanged NFT shares, actual destination LP.
    function moveFunds(uint256 id,bytes32 pool,uint128 minimum,uint256 deadline) public onlyGovernance live nonReentrant {
        if(activePlan[id]!=bytes32(0)) revert InvalidState(); _vault().movePool(id,pool,minimum,deadline);
    }
    // Retain the existing selector with exactly the same authority and safeguards.
    function movePool(uint256 id,bytes32 pool,uint128 minimum,uint256 deadline) external {
        moveFunds(id,pool,minimum,deadline);
    }
    function resume(uint256 id,bytes32 pool,uint128 minimum,uint256 deadline) external onlyGovernance live nonReentrant {
        if(activePlan[id]!=bytes32(0)) revert InvalidState(); _vault().resume(id,pool,minimum,deadline);
    }
    function park(ParkingRequest calldata r) external onlyDrainGovernance nonReentrant {
        _deadline(r.deadline); ICustodyVault v=_vault(); Position memory p=v.group(r.bucketId);
        validation.validateParking(abi.encode(r));
        ++parkingNonce[r.bucketId]; v.park(r.bucketId,r.deadline); Position memory afterPosition=v.group(r.bucketId);
        uint256 a0=afterPosition.idle0-p.idle0; uint256 a1=afterPosition.idle1-p.idle1;
        if(afterPosition.status!=PositionStatus.Parked || afterPosition.lpTokenId!=0 || a0<r.minimum0 || a1<r.minimum1) revert Slippage();
        emit ParkingExecuted(keccak256(abi.encode(block.chainid,address(this),address(v),r)),r.bucketId,r.nonce,a0,a1);
    }
    function invalidateParking(uint256 id) external onlyDrainGovernance {++parkingNonce[id];emit ParkingInvalidated(id,parkingNonce[id]);}
}
