// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @dev Local browser rehearsal ONLY. No public deployment or market qualification.
abstract contract LocalOnly {
    address public immutable operator = msg.sender;
    constructor() { require(block.chainid == 31337, "local chain only"); }
    modifier admin() { require(msg.sender == operator, "local operator only"); _; }
}
contract LocalToken is ERC20, LocalOnly {
    constructor(string memory label) ERC20(label, label) {}
    function mint(address to, uint256 value) external admin { _mint(to, value); }
}
contract LocalFeed is LocalOnly {
    uint8 public constant decimals = 8;
    int256 public answer = 1e8;
    function set(int256 value) external admin { require(value > 0); answer = value; }
    function latestRoundData() external view returns(uint80,int256,uint256,uint256,uint80) {
        // Deliberately always fresh for a local fixture. NOT a production feed.
        return (1,answer,block.timestamp,block.timestamp,1);
    }
}
/// @dev Custody/math boundary substitute, not Uniswap. All deposited and funded
/// token balances are real local ERC20 transfers. Production Vault, Strategy,
/// Entry, budgets, shares and reward ledgers run unmodified above this boundary.
contract LocalDemoVenue is ERC721, LocalOnly {
    address public immutable access;
    ERC20 public immutable token0;
    ERC20 public immutable token1;
    uint256 public next = 1;
    uint256 public fee0;
    uint256 public fee1;
    mapping(uint256 => uint256) public a0;
    mapping(uint256 => uint256) public a1;
    mapping(uint256 => int24) private lower;
    mapping(uint256 => int24) private upper;
    constructor(address controller,address first,address second) ERC721("Local LP","LOCAL-LP") {
        access=controller; token0=ERC20(first);token1=ERC20(second);
    }
    function positionManager() external view returns(address) { return address(this); }
    function spot(bytes32) external pure returns(uint160) { return uint160(1<<96); }
    function ticks(uint256 id) external view returns(int24,int24) { return(lower[id],upper[id]); }
    function amounts(uint256 id) external view returns(uint256,uint256) { return(a0[id],a1[id]); }
    function fundFees(uint256 x,uint256 y) external admin {
        require(token0.transferFrom(msg.sender,address(this),x));
        require(token1.transferFrom(msg.sender,address(this),y));fee0+=x;fee1+=y;
    }
    function swap(bytes32,bool zeroForOne,uint256 amount,uint256 minimum,uint256 deadline) external returns(uint256) {
        require(block.timestamp<=deadline && minimum<=amount);
        ERC20 source=zeroForOne?token0:token1; ERC20 dest=zeroForOne?token1:token0;
        require(source.transferFrom(msg.sender,address(this),amount));
        require(dest.transfer(msg.sender,amount));return amount;
    }
    function mint(bytes32,int24 lo,int24 hi,uint256 x,uint256 y,uint128 min,uint256 deadline)
        external returns(uint256 id,uint256,uint256) {
        require(block.timestamp<=deadline && min>0 && min<=x+y && lo<hi);
        id=next++;_mint(msg.sender,id);lower[id]=lo;upper[id]=hi;
        _fund(id,x,y);return(id,x,y);
    }
    function increase(bytes32,uint256 id,uint256 x,uint256 y,uint128 min,uint256 deadline)
        external returns(uint256,uint256) {
        require(ownerOf(id)==msg.sender && block.timestamp<=deadline && min>0 && min<=x+y);
        _fund(id,x,y);return(x,y);
    }
    function _fund(uint256 id,uint256 x,uint256 y) private {
        require(token0.transferFrom(msg.sender,address(this),x));
        require(token1.transferFrom(msg.sender,address(this),y));a0[id]+=x;a1[id]+=y;
    }
    function collect(bytes32,uint256 id,uint256 deadline) external {
        require(ownerOf(id)==msg.sender && block.timestamp<=deadline);
        uint256 x=fee0;uint256 y=fee1;fee0=0;fee1=0;
        require(token0.transfer(msg.sender,x));require(token1.transfer(msg.sender,y));
    }
    function close(bytes32,uint256 id,uint256 deadline) external {
        require(ownerOf(id)==msg.sender && block.timestamp<=deadline);
        uint256 x=a0[id];uint256 y=a1[id];delete a0[id];delete a1[id];_burn(id);
        require(token0.transfer(msg.sender,x));require(token1.transfer(msg.sender,y));
    }
}
