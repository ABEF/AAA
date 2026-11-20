// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;

interface IFixtureToken {
    function approve(address,uint256) external returns(bool);
}
interface IFixtureManager {
    function positionOperator() external view returns(address);
    function mint(bytes32,int24,int24,uint256,uint256,uint128,uint256) external payable returns(uint256,uint256,uint256);
    function increase(bytes32,uint256,uint256,uint256,uint128,uint256) external payable returns(uint256,uint256);
    function collect(bytes32,uint256,uint256) external;
    function close(bytes32,uint256,uint256) external;
}
interface IFixturePositions { function approve(address,uint256) external; }

/// @dev Test-only, no pending ordinary replacement. Not a production budget.
contract PoolFixtureBudget {
    function maintenanceBucket() external pure returns(uint256) { return 0; }
}
/// @dev Test-only admission book, not real NFT fee/reward accounting.
contract PoolFixtureAssets {
    function isAsset(address) external pure returns(bool) { return true; }
}
/// @dev Test-only typed custody caller. This does not instantiate PoPL Vault
/// shares, NFT ownership, fee allocation or Entry contribution accounting.
contract PoolCustodyFixture {
    address public immutable operator=msg.sender;
    address public immutable migrationBudget;
    address public immutable manager;
    address private constant ZZZ=0x7dbf38976f6D3b9c529e7D9484A71898B409eE6a;
    address private constant POSM=0x58daec3116aae6D93017bAAea7749052E8a04fA7;
    constructor(address managed,address budget) { manager=managed;migrationBudget=budget; }
    modifier onlyOperator() { require(msg.sender==operator,"test operator");_; }
    receive() external payable {}
    function onERC721Received(address,address,uint256,bytes calldata) external pure returns(bytes4) {
        return 0x150b7a02;
    }
    function mint(bytes32 pool,int24 lower,int24 upper,uint256 a0,uint256 a1,uint128 minL,uint256 deadline)
        external payable onlyOperator returns(uint256 id,uint256 spent0,uint256 spent1) {
        require(msg.value==a0,"exact test native input");
        address child=IFixtureManager(manager).positionOperator();
        require(IFixtureToken(ZZZ).approve(child,a1),"test approval");
        (id,spent0,spent1)=IFixtureManager(manager).mint{value:a0}(pool,lower,upper,a0,a1,minL,deadline);
        require(IFixtureToken(ZZZ).approve(child,0),"test reset");
        IFixturePositions(POSM).approve(child,id);
    }
    function increase(bytes32 pool,uint256 id,uint256 a0,uint256 a1,uint128 minL,uint256 deadline)
        external payable onlyOperator returns(uint256 spent0,uint256 spent1) {
        require(msg.value==a0,"exact test native input");
        address child=IFixtureManager(manager).positionOperator();
        require(IFixtureToken(ZZZ).approve(child,a1),"test approval");
        (spent0,spent1)=IFixtureManager(manager).increase{value:a0}(pool,id,a0,a1,minL,deadline);
        require(IFixtureToken(ZZZ).approve(child,0),"test reset");
    }
    function collect(bytes32 pool,uint256 id,uint256 deadline) external onlyOperator {
        IFixtureManager(manager).collect(pool,id,deadline);
    }
    function close(bytes32 pool,uint256 id,uint256 deadline) external onlyOperator {
        IFixtureManager(manager).close(pool,id,deadline);
    }
}
