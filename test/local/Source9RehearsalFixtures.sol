// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

/// @dev DISPOSABLE FORK ONLY. These prices are operator-controlled correlated
/// observations; two addresses do not establish independent production sources.
contract Source9RehearsalFeed {
    address public immutable operator = msg.sender;
    uint8 public constant decimals = 18;
    uint80 public round = 1;
    int256 public answer;
    uint256 public startedAt;
    uint256 public updatedAt;
    uint80 public answeredInRound = 1;

    constructor(int256 initialAnswer) {
        require(block.chainid == 4663, "isolated selected-chain fork only");
        answer = initialAnswer;
        startedAt = updatedAt = block.timestamp;
    }

    function set(int256 nextAnswer, uint256 nextStartedAt, uint256 nextUpdatedAt) external {
        require(msg.sender == operator, "fixture operator");
        answer = nextAnswer;
        startedAt = nextStartedAt;
        updatedAt = nextUpdatedAt;
        answeredInRound = ++round;
    }

    function setRound(uint80 nextRound, uint80 nextAnsweredInRound) external {
        require(msg.sender == operator, "fixture operator");
        round = nextRound;
        answeredInRound = nextAnsweredInRound;
    }

    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        return (round, answer, startedAt, updatedAt, answeredInRound);
    }
}

interface ISource9RehearsalConsumer {
    function rawFulfillRandomWords(uint256 requestId, uint256[] calldata words) external;
}

/// @dev DISPOSABLE FORK ONLY. Implements the official tuple shape, with no VRF
/// proof verification, subscription backing or public-network qualification.
contract Source9RehearsalVRF {
    struct RandomWordsRequest {
        bytes32 keyHash;
        uint256 subId;
        uint16 requestConfirmations;
        uint32 callbackGasLimit;
        uint32 numWords;
        bytes extraArgs;
    }
    address public immutable operator = msg.sender;
    uint256 public sequence;
    mapping(uint256 => address) public consumer;
    bool public failRequests;

    constructor() { require(block.chainid == 4663, "isolated selected-chain fork only"); }

    function setFailRequests(bool fail) external {
        require(msg.sender == operator, "fixture operator");
        failRequests = fail;
    }

    function requestRandomWords(RandomWordsRequest calldata request) external returns (uint256 requestId) {
        require(!failRequests && msg.sender.code.length != 0 && request.numWords == 2, "fixture request");
        requestId = ++sequence;
        consumer[requestId] = msg.sender;
    }

    function fulfill(uint256 requestId, uint256 word0, uint256 word1) external {
        require(msg.sender == operator && consumer[requestId] != address(0), "fixture operator");
        uint256[] memory words = new uint256[](2);
        words[0] = word0;
        words[1] = word1;
        ISource9RehearsalConsumer(consumer[requestId]).rawFulfillRandomWords(requestId, words);
    }
}

interface ISource9RehearsalToken {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

interface ISource9RehearsalCore {
    struct PoolKey { address currency0; address currency1; uint24 fee; int24 tickSpacing; address hooks; }
    struct SwapParams { bool zeroForOne; int256 amountSpecified; uint160 sqrtPriceLimitX96; }
    function unlock(bytes calldata data) external returns (bytes memory);
    function swap(PoolKey calldata key, SwapParams calldata params, bytes calldata data) external returns (int256);
    function sync(address asset) external;
    function settle() external payable returns (uint256);
    function take(address asset, address recipient, uint256 amount) external;
}

/// @dev DISPOSABLE FORK ONLY. A fixed-pool trader for controlled market cases.
/// Only its deployer supplies input; output returns to that same caller. No
/// PoPL permission, LP principal, arbitrary recipient or token sweep exists.
contract Source9RehearsalTrader {
    address public immutable operator = msg.sender;
    address private constant CORE = 0x8366a39CC670B4001A1121B8F6A443A643e40951;
    address private constant ZZZ = 0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    bool private armed;
    event ActualRehearsalSwap(bool nativeInput, uint256 input, uint256 output);

    constructor() { require(block.chainid == 4663, "isolated selected-chain fork only"); }
    receive() external payable { require(msg.sender == CORE && armed, "expected actual core payout"); }

    function execute(bool nativeInput, uint256 amount, uint256 minimumOutput, uint160 priceLimit)
        external payable returns (uint256 output) {
        require(msg.sender == operator && !armed && amount > 0 && amount <= uint256(type(int256).max), "fixture operator");
        require(msg.value == (nativeInput ? amount : 0), "exact caller funds");
        uint256 nativeBefore = address(this).balance - msg.value;
        uint256 tokenBefore = ISource9RehearsalToken(ZZZ).balanceOf(address(this));
        if (!nativeInput) require(ISource9RehearsalToken(ZZZ).transferFrom(msg.sender, address(this), amount), "exact token input");
        armed = true;
        output = abi.decode(ISource9RehearsalCore(CORE).unlock(abi.encode(nativeInput, amount, minimumOutput, priceLimit)), (uint256));
        armed = false;
        if (nativeInput) require(ISource9RehearsalToken(ZZZ).transfer(operator, output), "caller token payout");
        else { (bool paid,) = payable(operator).call{value: output}(""); require(paid, "caller native payout"); }
        require(address(this).balance == nativeBefore && ISource9RehearsalToken(ZZZ).balanceOf(address(this)) == tokenBefore,
                "prefunds cannot subsidize trade");
        emit ActualRehearsalSwap(nativeInput, amount, output);
    }

    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == CORE && armed, "actual armed core only");
        (bool nativeInput, uint256 amount, uint256 minimumOutput, uint160 limit) = abi.decode(data, (bool,uint256,uint256,uint160));
        ISource9RehearsalCore core = ISource9RehearsalCore(CORE);
        int256 packed = core.swap(ISource9RehearsalCore.PoolKey(address(0),ZZZ,10020,200,address(0)),
            ISource9RehearsalCore.SwapParams(nativeInput,-int256(amount),limit), "");
        int128 first = int128(packed >> 128);
        int128 second = int128(uint128(uint256(packed)));
        int128 debt = nativeInput ? first : second;
        int128 credit = nativeInput ? second : first;
        require(debt < 0 && uint256(-int256(debt)) == amount && credit > 0, "full exact input required");
        uint256 output = uint256(int256(credit));
        require(output >= minimumOutput, "caller output floor");
        core.sync(nativeInput ? address(0) : ZZZ);
        if (nativeInput) require(core.settle{value: amount}() == amount, "actual native settlement");
        else {
            require(ISource9RehearsalToken(ZZZ).transfer(CORE, amount), "actual token settlement");
            require(core.settle() == amount, "exact actual token debt");
        }
        core.take(nativeInput ? ZZZ : address(0), address(this), output);
        return abi.encode(output);
    }
}
