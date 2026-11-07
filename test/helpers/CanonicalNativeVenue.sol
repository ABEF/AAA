// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {SinglePositionFixture} from "./PortfolioFixture.sol";
import {IZZZAccess} from "../../src/interfaces/IZZZ.sol";
import {MockToken} from "../mocks/Mocks.sol";

/// @dev Deterministic settlement fixture only. All custody, NFT, fee/reward,
/// royalty, lifecycle and canonical transfer contracts in the test are real.
contract CanonicalNativeVenue is ERC721 , SinglePositionFixture {
    IZZZAccess public immutable access;
    MockToken private immutable token;
    uint256 private next = 1;
    uint256 private fee0;
    uint256 private fee1;
    mapping(uint256 => uint256) private a0;
    mapping(uint256 => uint256) private a1;
    constructor(address controller, address asset) ERC721("Native handoff fixture", "NHF") {
        access = IZZZAccess(controller); token = MockToken(asset);
    }
    receive() external payable {}
    function positionManager() external view returns (address) { return address(this); }
    function balanceContext(bytes32) external pure returns(bytes32){return bytes32(0);}
    function balance(bytes32,uint256,uint256 x,uint256 y,uint256) external payable returns(uint256,uint256) {
        require(msg.value==x);
        if(x!=0){(bool ok,)=msg.sender.call{value:x}("");require(ok);}
        return(x,y); // Canonical backing fixture; it intentionally has no swap model.
    }
    function spot(bytes32) external pure returns (uint160) { return uint160(1 << 96); }
    function setFees(uint256 x, uint256 y) external { fee0 = x; fee1 = y; }
    function mint(bytes32, int24, int24, uint256 x, uint256 y, uint128, uint256)
        external payable returns (uint256 id, uint256 spent0, uint256 spent1) {
        id = next++; _mint(msg.sender, id); _fund(id, x, y); return (id, x, y);
    }
    function increase(bytes32, uint256 id, uint256 x, uint256 y, uint128, uint256)
        external payable returns (uint256, uint256) { _fund(id, x, y); return (x, y); }
    function _fund(uint256 id, uint256 x, uint256 y) private {
        require(msg.value == x); require(token.transferFrom(msg.sender, address(this), y)); a0[id] += x; a1[id] += y;
    }
    function amounts(uint256 id) external view returns (uint256, uint256) { return (a0[id], a1[id]); }
    function collect(bytes32, uint256, uint256) external {
        uint256 x = fee0; uint256 y = fee1; fee0 = 0; fee1 = 0;
        if (x != 0) { (bool ok,) = msg.sender.call{value: x}(""); require(ok); }
        token.mint(msg.sender, y);
    }
    function close(bytes32, uint256 id, uint256) external {
        uint256 x = a0[id]; uint256 y = a1[id]; delete a0[id]; delete a1[id]; _burn(id);
        (bool ok,) = msg.sender.call{value: x}(""); require(ok); require(token.transfer(msg.sender, y));
    }
}
