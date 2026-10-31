// SPDX-License-Identifier: MIT
pragma solidity 0.8.26;
import {ZZZLPBalancer} from "../src/ZZZLPBalancer.sol";
import {ZZZMigrationBudget} from "../src/ZZZMigrationBudget.sol";
import {ZZZPortfolioPolicy} from "../src/ZZZPortfolioPolicy.sol";
import {ZZZRebalanceConfirmation} from "../src/ZZZRebalanceConfirmation.sol";
import {Script} from "forge-std/Script.sol";
import {Ids} from "../src/libraries/ZZZTypes.sol";
import {ZZZAccessController} from "../src/ZZZAccessController.sol";
import {ZZZProtocolPolicy} from "../src/ZZZProtocolPolicy.sol";
import {ZZZVault} from "../src/ZZZVault.sol";
import {ZZZNFT} from "../src/ZZZNFT.sol";
import {ZZZLiquidityManager} from "../src/ZZZLiquidityManager.sol";
import {ZZZRewards} from "../src/ZZZRewards.sol";
import {ZZZMembership} from "../src/ZZZMembership.sol";
import {ZZZFeeController} from "../src/ZZZFeeController.sol";
import {ZZZStrategy} from "../src/ZZZStrategy.sol";
import {ZZZCompounder} from "../src/ZZZCompounder.sol";
import {ZZZBuyback} from "../src/ZZZBuyback.sol";
import {ZZZMigration} from "../src/ZZZMigration.sol";
import {ZZZOracle} from "../src/ZZZOracle.sol";
import {ZZZPoolRegistry} from "../src/ZZZPoolRegistry.sol";
import {ZZZCanonicalHandoff} from "../src/ZZZCanonicalHandoff.sol";
import {ZZZNFTCanonical} from "../src/ZZZNFTCanonical.sol";
import {ZZZVaultCanonical} from "../src/ZZZVaultCanonical.sol";
import {ZZZFeesCanonical} from "../src/ZZZFeesCanonical.sol";
/// @notice LOCAL DEVELOPMENT ONLY. This script cannot deploy on public-chain IDs.
/// Requires reviewed local Uniswap dependencies; no integrated bridge exists.
contract DeployCore is Script {
    function run() external {
        require(block.chainid == 31337 || block.chainid == 31338, "local chains only");
        require(vm.envBool("ALLOW_UNAUDITED_LOCAL_DEPLOYMENT"), "explicit local consent required");
        uint256 home=vm.envUint("CANONICAL_CHAIN_ID");
        vm.startBroadcast();
        ZZZAccessController a=new ZZZAccessController(vm.envAddress("GOVERNANCE_MULTISIG"),
            vm.envAddress("KEEPER_ADDRESS"),vm.envAddress("GUARDIAN_ADDRESS"));
        address controller=address(a);
        ZZZProtocolPolicy policy=new ZZZProtocolPolicy(controller,vm.envAddress("MINT_PROCEEDS_RECIPIENT"));
        a.bindProtocolPolicy(address(policy));
        a.bind(Ids.VAULT,address(new ZZZVault(controller,home,address(new ZZZMigrationBudget(controller)))));
        ZZZNFT nft=new ZZZNFT(controller,vm.envString("NFT_BASE_URI"));
        a.bind(Ids.NFT,address(nft));
        // Optional LOCAL reviewed coordinator configuration. Without it minting
        // remains disabled. No public-network coordinator is assumed here.
        address coordinator=vm.envOr("NFT_VRF_COORDINATOR",address(0));
        if(coordinator!=address(0))policy.configureRandomness(coordinator,coordinator.codehash,vm.envBytes32("NFT_VRF_KEY_HASH"),
            vm.envUint("NFT_VRF_SUBSCRIPTION_ID"),uint16(vm.envUint("NFT_VRF_CONFIRMATIONS")),
            uint32(vm.envUint("NFT_VRF_CALLBACK_GAS")),vm.envBool("NFT_VRF_NATIVE_PAYMENT"),vm.envBytes32("NFT_VRF_REVIEW_HASH"));
        a.bind(Ids.LIQUIDITY,address(new ZZZLiquidityManager(controller,
            vm.envAddress("V4_POSITION_MANAGER"),vm.envAddress("V4_STATE_VIEW"),
            vm.envAddress("V4_POOL_MANAGER"),vm.envAddress("PERMIT2"), address(new ZZZLPBalancer(controller, vm.envAddress("V4_POOL_MANAGER"), vm.envAddress("V4_STATE_VIEW"))))));
        a.bind(Ids.REWARDS,address(new ZZZRewards(controller)));
        a.bind(Ids.MEMBERSHIP,address(new ZZZMembership(controller)));
        a.bind(Ids.FEES,address(new ZZZFeeController(controller)));
        a.bind(Ids.STRATEGY,address(new ZZZStrategy(controller, address(new ZZZPortfolioPolicy(controller)), address(new ZZZRebalanceConfirmation(controller)))));
        a.bind(Ids.COMPOUNDER,address(new ZZZCompounder(controller)));
        a.bind(Ids.BUYBACK,address(new ZZZBuyback(controller,vm.envAddress("ZZZ_TOKEN"),vm.envUint("MAX_BUYBACK_USD18"))));
        a.bind(Ids.MIGRATION,address(new ZZZMigration(controller)));
        a.bind(Ids.ORACLE,address(new ZZZOracle(controller,vm.envAddress("SEQUENCER_FEED"))));
        a.bind(Ids.POOLS,address(new ZZZPoolRegistry(controller)));
        a.bind(Ids.CANONICAL,address(new ZZZCanonicalHandoff(controller)));
        a.bind(Ids.NFT_CANONICAL,address(new ZZZNFTCanonical(controller,address(nft))));
        a.bind(Ids.VAULT_CANONICAL,address(new ZZZVaultCanonical(controller,a.module(Ids.VAULT),home)));
        a.bind(Ids.FEES_CANONICAL,address(new ZZZFeesCanonical(controller,a.module(Ids.FEES))));
        vm.stopBroadcast();
        vm.createDir("deployments",true);
        vm.serializeAddress("local-deployment","controller",controller);
        string memory encoded=vm.serializeUint("local-deployment","chainId",block.chainid);
        vm.writeJson(encoded,string.concat("deployments/",vm.toString(block.chainid),".json"));
        // Deliberately NOT sealed. Configure feeds/assets/pools/routes, validate both
        // local dependencies and all bindings, then consciously seal. Never broadcast mainnet.
    }
}
