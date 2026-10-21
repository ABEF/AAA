// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {IActivationV3Router} from "../../src/ZZZActivationEntry.sol";

// Disposable Anvil fixtures. Symbols describe UI scenarios, not public assets.
contract LocalInputToken is ERC20 {
    address public immutable operator = msg.sender;
    uint8 private immutable precision;
    constructor(string memory label, uint8 digits) ERC20(label, label) {
        require(block.chainid == 31337 && digits <= 18); precision = digits;
    }
    function decimals() public view override returns(uint8) { return precision; }
    function mint(address to, uint256 amount) external { require(msg.sender == operator); _mint(to, amount); }
}
contract LocalInputWETH is ERC20 {
    constructor() ERC20("Local test WETH", "WETH") { require(block.chainid == 31337); }
    function deposit() external payable { _mint(msg.sender, msg.value); }
    function withdraw(uint256 amount) external {
        _burn(msg.sender, amount); (bool ok,) = msg.sender.call{value: amount}(""); require(ok);
    }
}
contract LocalInputPool {
    address public immutable factory;
    address public immutable token0;
    address public immutable token1;
    uint24 public constant fee = 500;
    constructor(address a, address b) {
        require(block.chainid == 31337); factory = msg.sender;
        (token0,token1) = a < b ? (a,b) : (b,a);
    }
    // Local reserve-presence indicator for API admission, NOT Uniswap liquidity math.
    function liquidity() external view returns(uint128) {
        uint256 x=IERC20Metadata(token0).balanceOf(address(this));
        uint256 y=IERC20Metadata(token1).balanceOf(address(this));
        uint256 smallest=x<y?x:y;
        require(smallest<=type(uint128).max);return uint128(smallest);
    }
}
contract LocalInputFactory {
    address public immutable operator = msg.sender;
    mapping(bytes32 => address) private pools;
    constructor() { require(block.chainid == 31337); }
    function create(address a, address b) external returns(address pool) {
        require(msg.sender == operator && a != b);
        bytes32 key = keccak256(abi.encode(a < b ? a : b, a < b ? b : a));
        require(pools[key] == address(0)); pool = address(new LocalInputPool(a,b)); pools[key] = pool;
    }
    function getPool(address a, address b, uint24 fee) external view returns(address) {
        return fee == 500 ? pools[keccak256(abi.encode(a < b ? a : b, a < b ? b : a))] : address(0);
    }
}
contract LocalInputRouter is IActivationV3Router {
    address public immutable factory;
    constructor(address selected) { require(block.chainid == 31337); factory = selected; }
    function exactInputSingle(ExactInputSingleParams calldata p) external payable returns(uint256 out) {
        require(msg.value == 0 && p.sqrtPriceLimitX96 == 0 && p.recipient == msg.sender);
        require(LocalInputFactory(factory).getPool(p.tokenIn,p.tokenOut,p.fee) != address(0));
        IERC20Metadata input = IERC20Metadata(p.tokenIn); IERC20Metadata output = IERC20Metadata(p.tokenOut);
        // Both mock marks are $1. This does not qualify Uniswap or market pricing.
        out = p.amountIn * 10**output.decimals() / 10**input.decimals();
        require(out >= p.amountOutMinimum && input.transferFrom(msg.sender,address(this),p.amountIn));
        require(output.transfer(p.recipient,out));
    }
}
