// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ZZZModule} from "./base/ZZZModule.sol";
import {Ids,PoolKey,PoolConfig} from "./libraries/ZZZTypes.sol";
import {ExactToken} from "./libraries/ExactToken.sol";
import {ZZZLPBalancer} from "./ZZZLPBalancer.sol";
import {IZZZStrategy,IPositionManagerMinimal,IStateViewMinimal,IPoolManagerMinimal,IPermit2Minimal} from "./interfaces/IZZZ.sol";
interface IPositionExecutionParent {
    function executionConfig(bytes32,bool) external view returns(PoolConfig memory);
    function executionSpot(bytes32) external view returns(uint160);
    function executionOrdinaryReplacement() external view returns(bool);
    function executionHybridReplacement(bytes32) external view returns(bool);
    function balanceContext(bytes32) external view returns(bytes32);
}
interface IPositionPortfolioPolicy {
    function enabled(bytes32) external view returns(bool);
    function residualRange(bytes32,uint160,int24,int24,bool) external view returns(int24,int24);
}
/// @notice Immutable typed v4 LP executor. Vault owns both physical NFTs. Only
/// the fixed current Manager may call the four typed operations. No arbitrary
/// action, recipient, upgrade, sweep, generic executor or governance withdrawal.
contract ZZZLPPositionExecutor is ZZZModule,ReentrancyGuard {
    using SafeERC20 for IERC20;
    uint256 public constant LP_POSITION_EXECUTOR_VERSION=1;
    uint256 public constant RESIDUAL_EXIT_VERSION=1;
    address public immutable liquidityManager;
    IPositionManagerMinimal private immutable posm;
    IStateViewMinimal public immutable stateView;
    IPoolManagerMinimal public immutable poolManager;
    IPermit2Minimal public immutable permit2;
    ZZZLPBalancer public immutable balancingRouter;
    address private nativeSender;
    uint256 private nativeReceived;
    mapping(uint256=>uint256) public secondaryId;
    mapping(uint256=>uint256) private primaryOfSecondary;
    uint256 public activeSecondaryCount;
    event PortfolioCreated(uint256 indexed mainId,uint256 indexed secondaryId,bytes32 indexed poolId);
    struct AuxiliaryMint {uint256 id;int24 lower;int24 upper;uint128 liquidity;uint256 debt0;uint256 debt1;}
    uint8 private constant INCREASE=0x00;uint8 private constant DECREASE=0x01;
    uint8 private constant MINT=0x02;uint8 private constant BURN=0x03;
    uint8 private constant SETTLE_PAIR=0x0d;uint8 private constant TAKE_PAIR=0x11;
    constructor(address controller,address positionManager_,address stateView_,address poolManager_,address permit2_,address balancer_)
        ZZZModule(controller) {
        liquidityManager=msg.sender;posm=IPositionManagerMinimal(positionManager_);
        stateView=IStateViewMinimal(stateView_);poolManager=IPoolManagerMinimal(poolManager_);
        permit2=IPermit2Minimal(permit2_);balancingRouter=ZZZLPBalancer(balancer_);
    }
    modifier onlyManager() {
        if(msg.sender!=liquidityManager || access.module(Ids.LIQUIDITY)!=liquidityManager || !access.isSealed())revert Unauthorized();_;
    }
    receive()external payable {
        if(msg.sender!=nativeSender || nativeSender==address(0))revert Unauthorized();nativeReceived+=msg.value;
    }
    function positionManager()external view returns(address){return address(posm);}
    function _config(bytes32 poolId,bool ops)private view returns(PoolConfig memory){return IPositionExecutionParent(liquidityManager).executionConfig(poolId,ops);}
    function _policySpot(bytes32 poolId)private view returns(uint160){return IPositionExecutionParent(liquidityManager).executionSpot(poolId);}
    function _balanceContext(bytes32 poolId)private view returns(bytes32){return IPositionExecutionParent(liquidityManager).balanceContext(poolId);}
    function _hybridReplacement(bytes32 poolId)private view returns(bool){return IPositionExecutionParent(liquidityManager).executionHybridReplacement(poolId);}
    function _sendNative(address recipient, uint256 amount) private {
        if (amount == 0) return;
        uint256 beforeNative = address(this).balance;
        (bool ok,) = recipient.call{value: amount}("");
        if (!ok || address(this).balance + amount != beforeNative) revert InvalidState();
    }

    function _finishNativeCredit(uint256 beforeNative, address recipient) private {
        nativeSender = address(0);
        uint256 amount = nativeReceived;
        nativeReceived = 0;
        if (address(this).balance != beforeNative + amount) revert InvalidState();
        _sendNative(recipient, amount);
    }

    function _checkPosition(bytes32 poolId, uint256 id) private view returns (int24 lower, int24 upper) {
        if (posm.ownerOf(id) != access.module(Ids.VAULT)) revert InvalidState();
        (PoolKey memory key, uint256 info) = posm.getPoolAndPositionInfo(id);
        if (keccak256(abi.encode(key)) != poolId) revert InvalidState();
        lower = int24(uint24(info >> 8));
        upper = int24(uint24(info >> 32));
    }

    function _main(uint256 id) private view {
        if(id==0 || primaryOfSecondary[id]!=0)revert InvalidState();
    }

    function _portfolioPolicy() private view returns(IPositionPortfolioPolicy) {
        return IPositionPortfolioPolicy(IZZZStrategy(access.module(Ids.STRATEGY)).portfolioPolicy());
    }

    function portfolioFingerprint(uint256 mainId) external view returns(bytes32) {
        if(mainId==0)return keccak256(abi.encode(address(this),uint256(0)));
        _main(mainId);
        (PoolKey memory key,uint256 info)=posm.getPoolAndPositionInfo(mainId);
        bytes32 poolId=keccak256(abi.encode(key));
        _checkPosition(poolId,mainId);
        uint256 aux=secondaryId[mainId];uint256 auxInfo;
        if(aux!=0) {
            _checkPosition(poolId,aux);
            (,auxInfo)=posm.getPoolAndPositionInfo(aux);
            if(primaryOfSecondary[aux]!=mainId || aux==mainId)revert InvalidState();
        }
        return keccak256(abi.encode(address(this),address(posm),access.module(Ids.VAULT),poolId,mainId,info,aux,auxInfo));
    }

    function portfolioAmounts(uint256 mainId) external view returns(uint256 amount0,uint256 amount1) {
        _main(mainId);
        (PoolKey memory key,)=posm.getPoolAndPositionInfo(mainId);
        _checkPosition(keccak256(abi.encode(key)),mainId);
        (amount0,amount1)=amounts(mainId);
        uint256 aux=secondaryId[mainId];
        if(aux!=0) {
            _checkPosition(keccak256(abi.encode(key)),aux);
            if(primaryOfSecondary[aux]!=mainId)revert InvalidState();
            (uint256 a0,uint256 a1)=amounts(aux);amount0+=a0;amount1+=a1;
        }
    }

    function _approve(address token, uint256 amount, uint256 deadline) private {
        if (amount > type(uint128).max) revert InvalidAmount();
        IERC20(token).forceApprove(address(permit2), amount);
        permit2.approve(token, address(posm), uint160(amount), uint48(deadline));
    }

    function _reset(address token) private {
        permit2.approve(token, address(posm), 0, 0);
        IERC20(token).forceApprove(address(permit2), 0);
    }

    function _activeMainMark(bytes32 poolId,uint160 current,int24 lower,int24 upper) private view {
        (uint160 mark,int24 tick,,)=stateView.getSlot0(poolId);
        if(mark!=current || tick<lower || tick>=upper)revert Slippage();
    }

    function _mintOrIncrease(bytes32 poolId, uint256 id, int24 lower, int24 upper, uint256 amount0,
        uint256 amount1, uint128 minimumLiquidity, uint256 deadline)
        private returns (uint256 tokenId, uint256 spent0, uint256 spent1) {
        _deadline(deadline);
        if (amount0 > type(uint128).max || amount1 > type(uint128).max) revert InvalidAmount();
        PoolConfig memory c = _config(poolId, true);
        bytes32 policyContext=_balanceContext(poolId);
        uint160 current = _policySpot(poolId);
        if (lower % c.key.tickSpacing != 0 || upper % c.key.tickSpacing != 0 || lower >= upper) revert InvalidConfiguration();
        uint128 previousLiquidity = id == 0 ? 0 : posm.getPositionLiquidity(id);
        (uint128 liquidity,uint256 nativeValue) = balancingRouter.deploymentAmounts(current,lower,upper,amount0,amount1);
        if (liquidity == 0 || liquidity < minimumLiquidity) revert Slippage();
        AuxiliaryMint memory aux;
        uint256 mainDebt1;
        bool replacement=id==0 && IPositionExecutionParent(liquidityManager).executionOrdinaryReplacement();
        bool hybrid=replacement && _hybridReplacement(poolId);
        if(replacement) {
            // Every normal replacement promises active placement. A value
            // retention floor alone also accepts fully one-sided inactive LP.
            // Inverse-price rounding can leave a narrow reference-centred band
            // outside an otherwise permitted spot deviation. Check physical
            // tick semantics, including the downward exact-boundary case.
            _activeMainMark(poolId,current,lower,upper);
        }
        if(hybrid) {
            (,mainDebt1)=balancingRouter.balanceMath().deploymentDebts(current,lower,upper,liquidity);
            uint256 totalValue=amount0+Math.mulDiv(Math.mulDiv(amount1,2**96,current),2**96,current);
            aux=_auxiliaryPlan(poolId,current,lower,upper,amount0-nativeValue,amount1-mainDebt1,totalValue);
        }
        address t1 = c.key.currency1;
        if (msg.value != amount0) revert InvalidAmount();
        uint256 before0 = address(this).balance - msg.value;
        uint256 before1 = IERC20(t1).balanceOf(address(this));
        ExactToken.pull(t1,access.module(Ids.VAULT),amount1);
        uint256 beforeNative = address(this).balance;
        if (beforeNative != before0 + msg.value) revert InvalidState();
        // No SWEEP: pay exactly rounded-up principal debt. Prior PosM donations
        // cannot fund this operation and any unconsumed value makes it revert.
        if (nativeValue+aux.debt0 > amount0 || mainDebt1+aux.debt1>amount1) revert Slippage();
        uint256 beforePosmNative = address(posm).balance;
        _approve(t1, amount1, deadline);
        bytes[] memory parameters = new bytes[](aux.liquidity==0?2:3);
        tokenId = id;
        if (id == 0) {
            tokenId = posm.nextTokenId();
            parameters[0] = abi.encode(c.key, lower, upper, uint256(liquidity), uint128(aux.liquidity==0?amount0:nativeValue), uint128(aux.liquidity==0?amount1:mainDebt1),
                access.module(Ids.VAULT), bytes(""));
        } else {
            parameters[0] = abi.encode(id, uint256(liquidity), uint128(amount0), uint128(amount1), bytes(""));
        }
        bytes memory actions=abi.encodePacked(id==0?MINT:INCREASE,SETTLE_PAIR);
        if(aux.liquidity!=0) {
            aux.id=tokenId+1;
            parameters[1]=abi.encode(c.key,aux.lower,aux.upper,uint256(aux.liquidity),uint128(aux.debt0),uint128(aux.debt1),
                access.module(Ids.VAULT),bytes(""));
            actions=abi.encodePacked(MINT,MINT,SETTLE_PAIR);
        }
        parameters[parameters.length-1] = abi.encode(c.key.currency0, c.key.currency1);
        nativeValue+=aux.debt0;
        posm.modifyLiquidities{value: nativeValue}(abi.encode(actions,parameters),deadline);
        if (address(posm).balance != beforePosmNative || address(this).balance + nativeValue != beforeNative) revert InvalidState();
        _reset(t1);
        uint256 unused0 = address(this).balance - before0;
        uint256 unused1 = IERC20(t1).balanceOf(address(this)) - before1;
        if (unused0 > amount0 || unused1 > amount1) revert InvalidState();
        spent0 = amount0 - unused0;
        spent1 = amount1 - unused1;
        _sendNative(access.module(Ids.VAULT),unused0);
        ExactToken.push(t1,access.module(Ids.VAULT),unused1);
        // A static hookless mint/increase does not move the pool price. Token
        // approvals, pulls, settlement and refunds can nevertheless call external
        // code. Check the final mark and physical LP only after ALL those calls,
        // so incumbent repricing or a late LP mutation cannot masquerade as new LP.
        if (_policySpot(poolId) != current) revert Slippage();
        (int24 actualLower, int24 actualUpper) = _checkPosition(poolId, tokenId);
        if (actualLower != lower || actualUpper != upper ||
            uint256(posm.getPositionLiquidity(tokenId)) != uint256(previousLiquidity) + liquidity) revert InvalidState();
        // Identical sqrt alone does not fix the stored tick at an exact
        // downward boundary; callbacks must not leave a once-active main out.
        if(replacement)_activeMainMark(poolId,current,actualLower,actualUpper);
        if(aux.liquidity!=0) {
            (int24 al,int24 au)=_checkPosition(poolId,aux.id);
            if(al!=aux.lower || au!=aux.upper || posm.getPositionLiquidity(aux.id)!=aux.liquidity ||
                secondaryId[tokenId]!=0 || primaryOfSecondary[aux.id]!=0 || activeSecondaryCount>=4)revert InvalidState();
            secondaryId[tokenId]=aux.id;primaryOfSecondary[aux.id]=tokenId;++activeSecondaryCount;
        }
        if(_balanceContext(poolId)!=policyContext)revert InvalidState();
        if(id==0) {
            emit PortfolioCreated(tokenId,aux.id,poolId);
        }
    }

    function _auxiliaryPlan(bytes32 poolId,uint160 current,int24 lower,int24 upper,uint256 a0,uint256 a1,uint256 totalValue)
        private view returns(AuxiliaryMint memory aux) {
        uint256 zzzAsETH=Math.mulDiv(Math.mulDiv(a1,2**96,current),2**96,current);
        // Do not create another NFT just for <=0.1% rounding leftovers.
        // These assets stay attributed idle under the separate 5% ceiling.
        if(a0+zzzAsETH<=totalValue/1000)return aux;
        bool excess0=a0>zzzAsETH;
        uint256 available=excess0?a0:a1;
        if(available==0)return aux;
        (aux.lower,aux.upper)=_portfolioPolicy().residualRange(poolId,current,lower,upper,excess0);
        (aux.liquidity,)=balancingRouter.deploymentAmounts(current,aux.lower,aux.upper,excess0?a0:0,excess0?0:a1);
        if(aux.liquidity==0)return aux;
        (aux.debt0,aux.debt1)=balancingRouter.balanceMath().deploymentDebts(current,aux.lower,aux.upper,aux.liquidity);
        if(aux.debt0>a0 || aux.debt1>a1 || (excess0?aux.debt1!=0:aux.debt0!=0))revert InvalidState();
    }

    function mint(bytes32 poolId, int24 lower, int24 upper, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline)
        external payable onlyManager nonReentrant returns (uint256 tokenId, uint256 spent0, uint256 spent1) {
        return _mintOrIncrease(poolId, 0, lower, upper, amount0, amount1, minimumLiquidity, deadline);
    }

    function increase(bytes32 poolId, uint256 id, uint256 amount0, uint256 amount1,
        uint128 minimumLiquidity, uint256 deadline)
        external payable onlyManager nonReentrant returns (uint256 spent0, uint256 spent1) {
        _main(id);
        (int24 lower, int24 upper) = _checkPosition(poolId, id);
        (, spent0, spent1) = _mintOrIncrease(poolId, id, lower, upper, amount0, amount1, minimumLiquidity, deadline);
    }

    function collect(bytes32 poolId, uint256 id, uint256 deadline) external onlyManager nonReentrant {
        _deadline(deadline);
        _main(id);
        PoolConfig memory c = _config(poolId, false);
        _collectOne(poolId,c.key,id,deadline);
        uint256 aux=secondaryId[id];
        if(aux!=0)_collectOne(poolId,c.key,aux,deadline);
    }

    function _collectOne(bytes32 poolId,PoolKey memory key,uint256 id,uint256 deadline) private {
        _checkPosition(poolId,id);
        bytes[] memory parameters = new bytes[](2);
        parameters[0] = abi.encode(id, uint256(0), uint128(0), uint128(0), bytes(""));
        _settleTakePair(key,DECREASE,parameters,deadline);
    }

    function _settleTakePair(PoolKey memory key, uint8 action, bytes[] memory parameters, uint256 deadline) private {
        uint256 beforeNative = address(this).balance;
        nativeSender = address(poolManager); nativeReceived = 0;
        parameters[1] = abi.encode(key.currency0, key.currency1, address(this));
        uint256 beforeToken1 = IERC20(key.currency1).balanceOf(address(this));
        posm.modifyLiquidities(abi.encode(abi.encodePacked(action, TAKE_PAIR), parameters), deadline);
        _finishNativeCredit(beforeNative, access.module(Ids.VAULT));
        ExactToken.push(key.currency1, access.module(Ids.VAULT), IERC20(key.currency1).balanceOf(address(this)) - beforeToken1);
    }

    function close(bytes32 poolId, uint256 id, uint256 deadline) external onlyManager nonReentrant {
        _deadline(deadline);
        _main(id);
        PoolConfig memory c = _config(poolId, false);
        uint256 aux=secondaryId[id];
        _closeOne(poolId,c,id,deadline);
        if(aux!=0) {
            _closeOne(poolId,c,aux,deadline);
            delete secondaryId[id];delete primaryOfSecondary[aux];--activeSecondaryCount;
        }
    }

    function _closeOne(bytes32 poolId,PoolConfig memory c,uint256 id,uint256 deadline) private {
        _checkPosition(poolId, id);
        (uint256 expected0, uint256 expected1) = amounts(id);
        uint256 min0 = Math.mulDiv(expected0, 10000 - c.maxSlippageBps, 10000);
        uint256 min1 = Math.mulDiv(expected1, 10000 - c.maxSlippageBps, 10000);
        if (min0 > type(uint128).max || min1 > type(uint128).max) revert InvalidAmount();
        bytes[] memory parameters = new bytes[](2);
        parameters[0] = abi.encode(id, uint128(min0), uint128(min1), bytes(""));
        _settleTakePair(c.key, BURN, parameters, deadline);
    }

    /// @notice Paused residual-only removal; fees must already have been
    /// harvested by Vault. Keep association until the actual burn succeeds.
    function closeSecondary(bytes32 poolId,uint256 main,uint256 deadline) external onlyManager nonReentrant {
        _deadline(deadline);
        if(!access.paused())revert InvalidState();
        _main(main);
        _checkPosition(poolId,main);
        uint256 aux=secondaryId[main];
        if(aux==0 || primaryOfSecondary[aux]!=main)revert InvalidState();
        _closeOne(poolId,_config(poolId,false),aux,deadline);
        delete secondaryId[main];delete primaryOfSecondary[aux];--activeSecondaryCount;
        if(!access.paused())revert InvalidState();
    }

    function ticks(uint256 id) external view returns (int24 lower, int24 upper) {
        (, uint256 info) = posm.getPoolAndPositionInfo(id);
        return (int24(uint24(info >> 8)), int24(uint24(info >> 32)));
    }

    function amounts(uint256 id) public view returns (uint256 amount0, uint256 amount1) {
        return balancingRouter.principalAmounts(id);
    }
}
