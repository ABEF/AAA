// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
// TEST ONLY. Every mock here intentionally omits production authentication.
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ids,PoolKey,PoolConfig,Position,Route,BridgeMessage} from "../../src/libraries/ZZZTypes.sol";
import {IZZZAccess,IZZZTransportReceiver,IZZZOracle} from "../../src/interfaces/IZZZ.sol";
import {ZZZRoyaltyFactory} from "../../src/ZZZRoyaltyFactory.sol";
interface IMockCallerAccess { function access() external view returns (address); }
contract MockAccess {
    mapping(bytes32=>address) public module;
    mapping(address=>bool) public keepers;
    bool public isSealed; bool public paused; bool public preparationActive;
    uint8 public canonicalState;
    bool public canonicalSettling;
    address public immutable royaltyFactory;
    address public governor;
    constructor(){governor=msg.sender;royaltyFactory=address(new ZZZRoyaltyFactory());}
    function canonicalHandoff() external view returns(address){return module[Ids.CANONICAL];}
    function moduleAuthorized(bytes32 id,address caller) external view returns(bool){
        return isSealed && canonicalState==0 && caller==module[id];
    }
    function keeperAuthorized(address caller) external view returns(bool){
        return isSealed && canonicalState==0 && keepers[caller];
    }
    function canConfigure(address a) external view returns(bool){return !preparationActive && a==governor;}
    function setPreparation(bool active) external {preparationActive=active;}
    function setCanonicalState(uint8 state) external {canonicalState=state;}
    function bind(bytes32 id,address a) external {module[id]=a;}
    function seal() external {isSealed=true;}
    function setPaused(bool a) external {paused=a;}
    function setKeeper(address a,bool b) external {keepers[a]=b;}
}
contract MockToken is ERC20 {
    uint8 private immutable digits;
    constructor(uint8 d) ERC20("Mock","MOCK"){digits=d;}
    function decimals() public view override returns(uint8){return digits;}
    function mint(address a,uint256 n) external {_mint(a,n);}
    function burn(uint256 n) external {_burn(msg.sender,n);}
}
contract TaxToken is MockToken {
    constructor() MockToken(18){}
    function _update(address a,address b,uint256 n) internal override {
        if(a!=address(0)&&b!=address(0)&&n>=10){super._update(a,address(0),n/10);n-=n/10;}
        super._update(a,b,n);
    }
}
contract ExtraTaxToken is MockToken {
    constructor() MockToken(18){}
    function _update(address a,address b,uint256 n) internal override {
        if(a!=address(0)&&b!=address(0)&&n>=10)super._update(a,address(0),n/10);
        super._update(a,b,n);
    }
}
contract MockFeed {
    uint8 public immutable decimals; uint80 public round=1;int256 public answer;uint256 public started;
    uint256 public updated;uint80 public answeredRound=1;
    constructor(uint8 d,int256 a){decimals=d;set(a,block.timestamp,block.timestamp);}
    function set(int256 a,uint256 s,uint256 u) public {answer=a;started=s;updated=u;}
    function rounds(uint80 r,uint80 ar) external {round=r;answeredRound=ar;}
    function latestRoundData() external view returns(uint80,int256,uint256,uint256,uint80){return(round,answer,started,updated,answeredRound);}
}
contract MockPools {
    address public activationEntry;
    mapping(bytes32=>PoolConfig) private configs;
    function set(bytes32 id,PoolConfig memory c) external {configs[id]=c;}
    function get(bytes32 id) external view returns(PoolConfig memory){return configs[id];}
    function accounting(bytes32 id) external view returns(PoolConfig memory){return configs[id];}
    function contributionValue(bytes32 id,uint256 amount0,uint256 amount1) external view returns(uint256){
        IZZZAccess controller=IZZZAccess(IMockCallerAccess(msg.sender).access());
        IZZZOracle oracle=IZZZOracle(controller.module(Ids.ORACLE));PoolConfig memory c=configs[id];
        return oracle.value(c.key.currency0,amount0)+oracle.value(c.key.currency1,amount1);
    }
}
contract MockVaultRecord {
    Position private p;
    function set(Position memory v) external {p=v;}
    function position(uint256) external view returns(Position memory){return p;}
}
contract MockRoutes {
    mapping(bytes32=>Route) private routes;mapping(bytes32=>bool) private exists;
    function set(bytes32 id,Route memory r) external {routes[id]=r;exists[id]=true;}
    function get(bytes32 id) external view returns(Route memory,bool){require(exists[id]);return(routes[id],true);}
}
contract MockMessageReceiver {
    using SafeERC20 for IERC20;
    address public token;uint256 public received;bool public fail;
    function configure(address t,bool f) external {token=t;fail=f;}
    function receiveMessage(uint256,address,BridgeMessage calldata m) external {
        require(!fail,"receiver failed");
        if(m.amount0>0)IERC20(token).safeTransferFrom(msg.sender,address(this),m.amount0);
        received++;
    }
}
contract MockTransport {
    using SafeERC20 for IERC20;
    uint256 private nonce;
    function send(uint256,address,address[] calldata ts,uint256[] calldata amounts,bytes calldata) external payable returns(bytes32){
        for(uint256 i;i<ts.length;i++)IERC20(ts[i]).safeTransferFrom(msg.sender,address(this),amounts[i]);
        return bytes32(++nonce);
    }
    function deliver(address adapter,uint256 source,address sender,bytes memory message,address token,uint256 amount) external {
        if(token!=address(0))IERC20(token).forceApprove(adapter,amount);
        IZZZTransportReceiver(adapter).onMessage(source,sender,message);
        if(token!=address(0))IERC20(token).forceApprove(adapter,0);
    }
}
contract BoundDummy {
    IZZZAccess public immutable access;
    bool public randomnessConfigured = true;
    constructor(address a){access=IZZZAccess(a);}
    function transport() external view returns(address){return access.module(Ids.TRANSPORT);}
    function canonicalChainId() external view returns(uint256){return block.chainid;}
    function setRandomnessConfigured(bool ready) external {randomnessConfigured=ready;}
}
// TEST ONLY: custody unit tests explicitly bypass transport readiness. Router
// readiness/authentication is tested with real modules in separate suites.
contract MockReadyRouter { function canSend(bytes32) external pure returns(bool){return true;} }
