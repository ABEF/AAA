// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

interface ISource9DepthToken {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function transferFrom(address owner, address recipient, uint256 amount) external returns (bool);
}

interface ISource9DepthCore {
    struct PoolKey { address currency0; address currency1; uint24 fee; int24 tickSpacing; address hooks; }
    struct ModifyLiquidityParams { int24 tickLower; int24 tickUpper; int256 liquidityDelta; bytes32 salt; }
    function unlock(bytes calldata data) external returns (bytes memory);
    function modifyLiquidity(PoolKey calldata key, ModifyLiquidityParams calldata params, bytes calldata hookData)
        external returns (int256 callerDelta, int256 feesAccrued);
    function sync(address asset) external;
    function settle() external payable returns (uint256);
    function take(address asset, address recipient, uint256 amount) external;
}

interface ISource9DepthState {
    function poolManager() external view returns (address);
    function getSlot0(bytes32 pool) external view returns (uint160, int24, uint24, uint24);
}

/// @notice DISPOSABLE FORK FIXTURE ONLY. Add explicit synthetic external depth
/// after retaining the unseeded market failure. This neither qualifies actual
/// market liquidity nor changes PoPL, its positions, feeds or financial limits.
/// The helper owns one new core position and exposes no close/withdraw method.
contract Source9DepthSeeder {
    address public immutable operator = msg.sender;
    address private constant CORE = 0x8366a39CC670B4001A1121B8F6A443A643e40951;
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    address private constant STATE = 0xF3334192D15450CdD385c8B70e03f9A6bD9E673b;
    bytes32 public constant POOL = 0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b;
    int24 public constant LOWER = -887200;
    int24 public constant UPPER = 887200;
    uint256 public constant MAX_NATIVE_BUDGET = 100 ether;
    uint256 public constant MAX_ZZZ_BUDGET = 100_000_000 ether;
    bytes32 private constant SALT = keccak256("SOURCE9_DISPOSABLE_EXTERNAL_DEPTH_ONLY");
    bool public seeded;
    bool private entered;
    bytes32 private pending;

    event ExternalDepthSeeded(address indexed operator, uint128 liquidity, uint256 maximumNative,
        uint256 maximumZZZ, uint256 spentNative, uint256 spentZZZ,
        uint256 refundedNative, uint256 refundedZZZ, uint160 unchangedSqrtPriceX96, int24 unchangedTick);

    constructor() {
        _dependencies();
        require(ISource9DepthState(STATE).poolManager() == CORE, "fixed state/core binding");
    }

    receive() external payable {
        require(msg.sender == CORE && entered && pending != bytes32(0), "expected actual core credit");
    }

    function _dependencies() private view {
        require(block.chainid == 4663, "isolated selected-chain fork only");
        require(CORE.codehash == 0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626 &&
                ZZZ.codehash == 0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597 &&
                STATE.codehash == 0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6,
                "fixed real dependency runtimes");
    }

    function seed(uint128 liquidity, uint256 maximumZZZ)
        external payable returns (uint256 spentNative, uint256 spentZZZ) {
        require(msg.sender == operator && !entered && !seeded, "single operator seed only");
        require(liquidity != 0 && liquidity <= uint128(type(int128).max) &&
                msg.value != 0 && msg.value <= MAX_NATIVE_BUDGET &&
                maximumZZZ != 0 && maximumZZZ <= MAX_ZZZ_BUDGET, "bounded positive caller budgets");
        _dependencies();
        entered = true;
        (uint160 beforePrice, int24 beforeTick, uint24 beforeProtocol, uint24 beforeFee) =
            ISource9DepthState(STATE).getSlot0(POOL);
        require(beforePrice != 0 && beforeFee == 10020, "initialized fixed pool");
        bytes32 beforeState = keccak256(abi.encode(beforePrice,beforeTick,beforeProtocol,beforeFee));
        uint256 nativePrefund = address(this).balance - msg.value;
        uint256 tokenPrefund = ISource9DepthToken(ZZZ).balanceOf(address(this));
        require(ISource9DepthToken(ZZZ).transferFrom(operator,address(this),maximumZZZ) &&
                ISource9DepthToken(ZZZ).balanceOf(address(this)) == tokenPrefund + maximumZZZ,
                "exact caller token funding");
        bytes memory data = abi.encode(liquidity,msg.value,maximumZZZ);
        pending = keccak256(data);
        (spentNative,spentZZZ) = abi.decode(ISource9DepthCore(CORE).unlock(data),(uint256,uint256));
        pending = bytes32(0);
        require(spentNative <= msg.value && spentZZZ <= maximumZZZ, "caller budgets only");
        uint256 refundNative = msg.value - spentNative;
        uint256 refundZZZ = maximumZZZ - spentZZZ;
        require(address(this).balance == nativePrefund + refundNative &&
                ISource9DepthToken(ZZZ).balanceOf(address(this)) == tokenPrefund + refundZZZ,
                "prefunds cannot subsidize seed");
        seeded = true;
        if (refundZZZ != 0) require(ISource9DepthToken(ZZZ).transfer(operator,refundZZZ), "caller token refund");
        if (refundNative != 0) { (bool paid,) = payable(operator).call{value:refundNative}(""); require(paid, "caller native refund"); }
        require(address(this).balance == nativePrefund &&
                ISource9DepthToken(ZZZ).balanceOf(address(this)) == tokenPrefund, "all unused caller funds refunded");
        (uint160 afterPrice, int24 afterTick, uint24 afterProtocol, uint24 afterFee) =
            ISource9DepthState(STATE).getSlot0(POOL);
        require(keccak256(abi.encode(afterPrice,afterTick,afterProtocol,afterFee)) == beforeState,
                "seed cannot change captured pool price or fees");
        entered = false;
        emit ExternalDepthSeeded(operator,liquidity,msg.value,maximumZZZ,spentNative,spentZZZ,
            refundNative,refundZZZ,afterPrice,afterTick);
    }

    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == CORE && entered && pending != bytes32(0) && keccak256(data) == pending,
                "actual armed core only");
        (uint128 liquidity, uint256 nativeBudget, uint256 tokenBudget) = abi.decode(data,(uint128,uint256,uint256));
        ISource9DepthCore core = ISource9DepthCore(CORE);
        (int256 delta,int256 fees) = core.modifyLiquidity(
            ISource9DepthCore.PoolKey(address(0),ZZZ,10020,200,address(0)),
            ISource9DepthCore.ModifyLiquidityParams(LOWER,UPPER,int256(uint256(liquidity)),SALT), "");
        require(fees == 0, "new external position has no prior fees");
        int128 first = int128(delta >> 128);
        int128 second = int128(uint128(uint256(delta)));
        uint256 spentNative = _settle(core,address(0),first,nativeBudget);
        uint256 spentZZZ = _settle(core,ZZZ,second,tokenBudget);
        return abi.encode(spentNative,spentZZZ);
    }

    function _settle(ISource9DepthCore core, address asset, int128 delta, uint256 budget)
        private returns (uint256 spent) {
        if (delta == 0) return 0;
        if (delta > 0) {
            core.take(asset,address(this),uint256(int256(delta)));
            return 0;
        }
        spent = uint256(-int256(delta));
        require(spent <= budget, "actual debt exceeds caller budget");
        core.sync(asset);
        if (asset == address(0)) require(core.settle{value:spent}() == spent, "actual native debt settlement");
        else {
            require(ISource9DepthToken(ZZZ).transfer(CORE,spent), "actual token debt transfer");
            require(core.settle() == spent, "actual token debt settlement");
        }
    }
}
