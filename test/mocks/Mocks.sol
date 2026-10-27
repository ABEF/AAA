// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
// TEST ONLY. Every mock here intentionally omits production authentication.
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ids,PoolKey,PoolConfig,Position} from "../../src/libraries/ZZZTypes.sol";
import {IZZZAccess,IZZZOracle} from "../../src/interfaces/IZZZ.sol";
import {ZZZRoyaltyFactory} from "../../src/ZZZRoyaltyFactory.sol";
import {ZZZActivationAssetsFactory} from "../../src/ZZZActivationAssetsFactory.sol";
interface IMockCallerAccess { function access() external view returns (address); }
interface IMockSealRegistry { function activationAssets() external view returns(address); }
interface IMockSealIdentity { function zzz() external view returns(address); }
contract MockAccess {
    mapping(bytes32=>address) public module;
    mapping(address=>bool) public keepers;
    bool public isSealed; bool public paused; bool public preparationActive; bool public lpExitStarted;
    uint8 public canonicalState;
    bool public canonicalSettling;
    address public immutable royaltyFactory;
    address public immutable activationAssetsFactory;
    address public governor;
    constructor(){governor=msg.sender;royaltyFactory=address(new ZZZRoyaltyFactory());activationAssetsFactory=address(new ZZZActivationAssetsFactory());}
    function governance() external view returns(address){return governor;}
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
    // TEST ONLY: assemble replacement mock dependencies during an explicit
    // bootstrap phase. Real AccessController has no unseal function.
    function beginBootstrap() external {isSealed=false;}
    function setPaused(bool a) external {paused=a;}
    function startLPExit() external {
        require(msg.sender==module[Ids.VAULT] && isSealed && paused && !lpExitStarted && !preparationActive && canonicalState==0);
        lpExitStarted=true;
    }
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
    address public activationAssets;
    function setActivationAssets(address helper) external {activationAssets=helper;}
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
contract BoundDummy {
    IZZZAccess public immutable access;
    bool public randomnessConfigured = true;
    address public zzz;
    constructor(address a){access=IZZZAccess(a);zzz=address(this);}
    // TEST ONLY: seal identity stubs. This dummy has no financial behavior.
    function FEE_INTAKE_VERSION() external pure returns(uint256){return 1;}
    function activationAssets() external view returns(address){return address(this);}
    function setTestZZZIdentity(address token) external {zzz=token;}
    function currentZZZ() external view returns(address) {
        return IMockSealIdentity(IMockSealRegistry(access.module(Ids.POOLS)).activationAssets()).zzz();
    }
    function canonicalChainId() external view returns(uint256){return block.chainid;}
    function setRandomnessConfigured(bool ready) external {randomnessConfigured=ready;}
}
// TEST ONLY: custody unit tests explicitly bypass transport readiness. Router
// readiness/authentication is tested with real modules in separate suites.
