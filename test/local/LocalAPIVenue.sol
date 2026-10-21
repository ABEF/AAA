// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {LocalOnly} from "./LocalDemoVenue.sol";

/// @dev Test-only observation surfaces for the REAL API validation and call tracer.
/// This remains a deterministic 1:1 custody fixture, NOT Uniswap or Pons math.
contract LocalAPIDependency is LocalOnly {}
interface ILocalAPIVenue {
    function amounts(uint256 id) external view returns(uint256,uint256);
    function ownerOf(uint256 id) external view returns(address);
}
contract LocalAPIPositionManager is LocalOnly {
    address public immutable venue;
    address public immutable poolManager;
    address public immutable permit2;
    mapping(uint256 => address) public getApproved;
    constructor(address v,address p,address a) {venue=v;poolManager=p;permit2=a;}
    function getPositionLiquidity(uint256 id) external view returns(uint128) {
        (uint256 x,uint256 y)=ILocalAPIVenue(venue).amounts(id);
        require(x+y<=type(uint128).max);return uint128(x+y);
    }
    function ownerOf(uint256 id) external view returns(address) {return ILocalAPIVenue(venue).ownerOf(id);}
    function approve(address to,uint256 id) external {
        require(msg.sender==ILocalAPIVenue(venue).ownerOf(id) && to==venue);
        getApproved[id]=to;
    }
}
contract LocalAPIStateView is LocalOnly {
    address public immutable poolManager;
    constructor(address p) {poolManager=p;}
    function getSlot0(bytes32) external pure returns(uint160,int24,uint24,uint24) {
        return(uint160(1<<96),0,0,3000);
    }
}
/// @dev Owns real local ERC20 balances; governance/Entry/Vault/ledgers are unchanged.
contract LocalAPIVenue is ERC721, LocalOnly {
    LocalAPIPositionManager public immutable positionManager;
    address public immutable poolManager;
    address public immutable permit2;
    address public immutable stateView;
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
        poolManager=address(new LocalAPIDependency());
        permit2=address(new LocalAPIDependency());
        positionManager=new LocalAPIPositionManager(address(this),poolManager,permit2);
        stateView=address(new LocalAPIStateView(poolManager));
    }
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
        _fund(id,x,y);require(positionManager.getPositionLiquidity(id)>=min);return(id,x,y);
    }
    function increase(bytes32,uint256 id,uint256 x,uint256 y,uint128 min,uint256 deadline)
        external returns(uint256,uint256) {
        require(ownerOf(id)==msg.sender && block.timestamp<=deadline && min>0 && min<=x+y);
        uint128 beforeLP=positionManager.getPositionLiquidity(id);
        _fund(id,x,y);require(positionManager.getPositionLiquidity(id)-beforeLP>=min);return(x,y);
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
