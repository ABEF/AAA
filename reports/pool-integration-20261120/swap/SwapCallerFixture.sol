// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
interface IFixtureManagerSwap {
    function swap(bytes32,bool,uint256,uint256,uint256) external payable returns(uint256);
}
interface IFixtureERC20 { function approve(address,uint256) external returns(bool); }
/// @dev Report-only caller. MockAccess explicitly binds this caller as BUYBACK;
/// it does not instantiate buyback reserve/claim/NFT or Vault accounting.
contract SwapCallerFixture {
    address public immutable operator=msg.sender;
    address public immutable manager;
    address constant ZZZ=0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    constructor(address target){manager=target;}
    receive() external payable {}
    function swap(bytes32 pool,bool direction,uint256 amount,uint256 floor,uint256 deadline)
        external payable returns(uint256 output) {
        require(msg.sender==operator,"report operator");
        require(msg.value==(direction?amount:0),"report native input");
        if(!direction)require(IFixtureERC20(ZZZ).approve(manager,amount),"report approval");
        output=IFixtureManagerSwap(manager).swap{value:msg.value}(pool,direction,amount,floor,deadline);
        if(!direction)require(IFixtureERC20(ZZZ).approve(manager,0),"report reset");
    }
}
