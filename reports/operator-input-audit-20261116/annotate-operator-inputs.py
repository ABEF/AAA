"""Reviewed documentation producer, never a live input/transaction producer."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT/'docs/function-reference-notes.json'
notes = json.loads(path.read_text(encoding='utf-8'))
contracts = notes['contracts']


def annotate(contract, signature, index, fields):
    note = contracts[contract]['functions'][signature]['inputs']
    old = note[str(index)]
    explanation = old['explanation'] if isinstance(old, dict) else old
    note[str(index)] = {'explanation': explanation, 'fields': fields}


review = 'Nonzero bytes32 provenance commitment to reviewed evidence; not authority, a live state hash or proof that execution is safe.'
pin = 'Exact Keccak-256 runtime code hash from the reviewed deployment, rechecked on admission/use; a proxy code hash alone does not freeze its upstream implementation.'
key = {
    'currency0': 'Actual ordered token0 address; native ETH is address(0), not WETH. Read the initialized PoolKey and recompute its pool ID.',
    'currency1': 'Actual ordered token1 address; principal admission requires the one fixed ZZZ token. Read the initialized PoolKey.',
    'fee': 'Static LP fee in millionths (10020 = 1.002%), not basis points; directional protocol fees are separate and may change.',
    'tickSpacing': 'Positive int24 tick spacing of the initialized pool; lower/upper ticks must align. Principal admission permits 1..32767.',
    'hooks': 'Hook address from the exact PoolKey; supported principal and v4 conversion venues require address(0).',
}
source = {
    'source': 'Reviewed deployed AggregatorV3-compatible source address, not an API URL or token address; independent upstream admission is an external obligation.',
    'expectedCodeHash': pin,
    'independenceId': 'Nonzero bytes32 independently reviewed source identity, distinct from the other source; contract inequality cannot prove economic independence.',
    'maxAge': 'Maximum original source age in seconds, 1..86400; compare actual round updatedAt at execution. Not a new timestamp assigned by a wrapper.',
    'feedDecimals': 'Exact source decimals() result, 0..18, retained and checked against the admitted source; not token decimals or USD18.',
}
parking = {
    'bucketId': 'Shared bucket ID from Vault.nftBucket(NFT_ID) or Vault.poolBucket(POOL_ID), then Vault.group(bucketId); not the collection NFT ID or LP NFT ID.',
    'poolId': 'Current Vault.group(bucketId).poolId, the bytes32 Keccak PoolKey hash. External swaps change spot, not this identity.',
    'lpTokenId': 'Current Vault.group(bucketId).lpTokenId; physical main position ID, not the bucket or collection NFT ID.',
    'totalShares': 'Exact Vault.bucketTotalShares(bucketId) integer; contributions before inclusion invalidate this physical custody snapshot.',
    'depositUSD': 'Current Position.depositUSD bookkeeping integer in USD18, not current LP value; copy the exact group field.',
    'custodyEpoch': 'Current Migration.custodyEpoch(bucketId), uint64; reread after custody-changing operations.',
    'nonce': 'Current Migration.parkingNonce(bucketId), uint64; do not reuse a consumed or invalidated request.',
    'token0': 'Actual pool currency0 from PoolRegistry.accounting(poolId).key: address(0) for native ETH.',
    'token1': 'Actual pool currency1 from PoolRegistry.accounting(poolId).key: fixed ZZZ, not a currency ticker.',
    'minimum0': 'Caller-reviewed minimum raw native ETH wei received from the scope of this close; uint128, zero is an explicit raw-close choice.',
    'minimum1': 'Caller-reviewed minimum raw fixed-ZZZ units received from the scope of this close; uint128, use admitted ZZZ decimals, zero is explicit.',
    'deadline': 'Original inclusive Unix-seconds expiry; execution requires now <= deadline <= now+600. Never extend it while reusing the same review.',
    'reviewHash': review,
    'portfolioHash': 'LiquidityManager.executionPortfolioFingerprint(lpTokenId), including both physical legs and their liquidity. Capture after pause; a new contribution can invalidate it, while an ordinary outside swap does not change fixed position ticks/L.',
}
emergency = {
    'bucket': parking['bucketId'],
    'custodyHash': 'Current Migration.emergencyCustodyHash(bucket) for full replacement; use consolidationCustodyHash(bucket) for residual-only reinvestment. Capture the exact operation-specific hash after pause.',
    'checks': 'Retained-check mask uint8 0..31: 1 raw trigger/cooldown, 2 independent price bounds, 4 USD/loss/quality/idle, 8 operation flags, 16 sampled confirmation. Bits retain checks; they do not grant authority.',
    'lower': 'Signed int24 lower physical tick, aligned to pool spacing and below upper. For same-main consolidation copy Manager.ticks(mainPositionId).lower exactly; it does not follow the current tick.',
    'upper': 'Signed int24 upper physical tick, aligned to pool spacing and above lower. For same-main consolidation copy Manager.ticks(mainPositionId).upper exactly; a swap changes current price, not this boundary.',
    'swapPool': 'Exact admitted native ETH/ZZZ venue PoolKey hash, bytes32; zero for no swap. Guarded consolidation requires zero and lets reviewed routing choose at execution.',
    'zeroForOne': 'True sells currency0/native ETH for currency1/ZZZ; false sells ZZZ for ETH. Guarded consolidation supplies false because explicit swap fields must be empty.',
    'amountIn': 'Exact raw input uint128 of the selected direction; must fit supported signed deltas. Zero means no explicit swap; never a USD amount or percentage.',
    'minimumOut': 'Caller minimum raw output uint128 of the opposite currency, positive when explicitly swapping and zero for no swap; preserve original review floors.',
    'minimumLiquidity': 'Positive raw physical main liquidity L floor: added delta for same-main consolidation, new main L for full replacement. Not USD, token quantity or sum of both ranges.',
    'deadline': parking['deadline'],
    'reviewHash': review,
}
annotate('ZZZAccessController', 'startPreparation((uint256,address,bytes32,bytes32))', 0, {
    'destinationChain': 'Exact current block.chainid uint256. Current canonical transport is same-chain only; this field does not implement bridging.',
    'successorController': 'Reviewed distinct destination controller address. A usable importer is sealed/inert and bound to this source; this notice alone does not approve or freeze it.',
    'deploymentCommitment': 'Exact destination CanonicalHandoff.deploymentCommitment() bytes32 from a reviewed matching deployment; not its address or a generic source hash.',
    'reviewHash': review,
})
annotate('ZZZLPRewardConverter', 'addRoute((address,address,address,address,uint24,bytes32,bytes32,bytes32,bytes32,bytes32))', 0, {
    'source': 'Actual nonzero LP reward token address admitted by the bound ledger; fresh Rewards admits fixed ZZZ. Raw token units use source decimals.',
    'router': 'Reviewed deployed v3 router, whose supported exactInputSingle ABI and factory relationship must match the pinned dependencies.',
    'factory': 'Reviewed deployed v3 factory, independently validated against router/pool wiring.',
    'pool': 'Actual v3 source/wrapper pool contract address, not a v4 pool ID. The immutable wrapper must be nonzero for this compatibility route.',
    'fee': 'Actual v3 pool fee in millionths, not basis points; source/wrapper/fee identity must match the factory pool.',
    'sourceCodeHash': pin, 'routerCodeHash': pin, 'factoryCodeHash': pin,
    'poolCodeHash': pin, 'reviewHash': review,
})
annotate('ZZZLPRewardConverter', 'addV4Route((address,address,(address,address,uint24,int24,address),address,address,bytes32,bytes32,bytes32,bytes32,bytes32))', 0, {
    'source': 'Actual nonzero LP reward token, fresh fixed ZZZ; not an arbitrary royalty payment currency.',
    'output': 'Must be address(0), native ETH paid back to the same bound LP reward ledger.',
    'key': {'explanation': 'Exact initialized hookless source/native-ETH v4 PoolKey, in currency-address order.', 'fields': key},
    'poolManager': 'Reviewed actual v4 PoolManager address; native balance settlement happens through this fixed core, not a pool contract.',
    'stateView': 'Reviewed StateView for the same PoolManager; verify parent/core wiring, runtime and initialized key.',
    'sourceCodeHash': pin,
    'outputCodeHash': 'Native ETH uses the executor NATIVE_ASSET_CODE_HASH constant, not extcodehash(address(0)); read the exact constant from the reviewed child.',
    'poolManagerCodeHash': pin, 'stateViewCodeHash': pin, 'reviewHash': review,
})
annotate('ZZZLPRewardConverter', 'configureWrapper((bytes32,address,address,address,bytes32,bytes32,bytes32))', 0, {
    'codeHash': 'Reviewed exact immutable wrapper runtime code hash. A zero immutable wrapper disables this optional v3 compatibility path.',
    'admin': 'Reviewed proxy administrator address, or address(0) for explicitly reviewed nonproxy wrapper; zero requires every related proxy field/hash zero.',
    'implementation': 'Exact reviewed proxy implementation address reported by the selected admin; zero only in the nonproxy policy.',
    'adminOwner': 'Exact owner() of the reviewed proxy admin; zero only in the nonproxy policy. Code hashes alone do not prove upstream immutability.',
    'adminCodeHash': 'Exact reviewed admin runtime hash, or zero for the nonproxy policy.',
    'implementationCodeHash': 'Exact reviewed implementation runtime hash, or zero for the nonproxy policy.',
    'reviewHash': review,
})
for signature in (
    'closeResidual((uint256,bytes32,uint256,uint256,uint256,uint64,uint64,address,address,uint128,uint128,uint256,bytes32,bytes32))',
    'park((uint256,bytes32,uint256,uint256,uint256,uint64,uint64,address,address,uint128,uint128,uint256,bytes32,bytes32))',
):
    fields = dict(parking)
    scope = 'residual principal only; main remains unchanged' if signature.startswith('closeResidual') else 'combined main+residual principal close; attributed idle/compound remain separately accounted'
    fields['minimum0'] += ' Scope: ' + scope + '.'
    fields['minimum1'] += ' Scope: ' + scope + '.'
    annotate('ZZZMigration', signature, 0, fields)
for signature in (
    'consolidateResidual((uint256,bytes32,uint8,int24,int24,bytes32,bool,uint128,uint128,uint128,uint256,bytes32),bool)',
    'emergencyRebalance((uint256,bytes32,uint8,int24,int24,bytes32,bool,uint128,uint128,uint128,uint256,bytes32))',
):
    fields = dict(emergency)
    fields['custodyHash'] = ('Exact current Migration.consolidationCustodyHash(bucket), including nonce/epoch/policy controls; not emergencyCustodyHash.'
                             if signature.startswith('consolidateResidual') else
                             'Exact current Migration.emergencyCustodyHash(bucket), including chain, position, shares, nonce/epoch and current controls; not consolidationCustodyHash.')
    annotate('ZZZMigration', signature, 0, fields)
annotate('ZZZNFT', 'updateAllowList(address,(bytes32,string[],string))', 1, {
    'merkleRoot': 'Exact independently reviewed SeaDrop free-team/paid-allowlist root; must match helper settings and all intended leaf prices, stages, caps and windows.',
    'publicKeyURIs': 'Ordered string[] of reviewed public-key/document URIs. These are published strings, not signing secrets, token addresses or automatic proof validation.',
    'allowListURI': 'Reviewed public allowlist manifest URI. URI text alone does not authenticate the on-chain root or each Merkle leaf.',
})
annotate('ZZZNFT', 'updatePublicDrop(address,(uint80,uint48,uint48,uint16,uint16,bool))', 1, {
    'mintPrice': 'Gross native ETH price in wei, uint80, from SeaDropMint.expectedPublicDrop(); not net creator proceeds or USD.',
    'startTime': 'Inclusive Unix seconds, uint48, matching configured publicStart; never browser milliseconds.',
    'endTime': 'Inclusive Unix seconds, uint48, matching publicEnd and NFT/RoyaltyRewards mintEnd; the separate royalty opening is end+3600.',
    'maxTotalMintableByWallet': 'Lifetime original-recipient mint count limit, uint16; not current wallet balance or per-transaction quantity.',
    'feeBps': 'Paid platform fee in basis points, 0..10000, included in gross price. Must match reviewed helper settings.',
    'restrictFeeRecipients': 'Must be true for the reviewed single allowed platform fee recipient; not a user-selectable payout override.',
})
for index in (1, 2):
    annotate('ZZZOracle', 'setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)', index, source)
annotate('ZZZPoolRegistry', 'configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))', 0, {
    'key': {'explanation': 'Exact initialized native ETH/fixed-ZZZ static hookless PoolKey; recompute poolId as Keccak(abi.encode(key)).', 'fields': key},
    'depositsEnabled': 'True selects this as the sole contribution pool; another currently enabled destination must first be disabled. False also required for post-exit Ready reserve-only admission.',
    'operationsEnabled': 'True enables ordinary maintenance/deployment for this admitted venue. False does not erase custody, claims or existing LP.',
    'rangeBps': 'Human-price width in basis points, 100..9999; Strategy.setRangeOrientation separately selects raw/inverse price. Desired width changes existing geometry only at replacement.',
    'triggerBps': 'Historical movement field, 100..rangeBps-1. Current portfolio threshold policy does not authorize ordinary replacement from this field alone.',
    'maxSpotDeviationBps': 'Allowed spot/reference deviation in basis points, 1..500 and below rangeBps. This is distinct from source agreement and loss budgets.',
    'maxSlippageBps': 'Per-venue gross swap floor in basis points, 1..1000; key.fee must be strictly below value*100 fee-pips. Aggregate/caller/additional-loss protections remain separate.',
    'minRebalanceInterval': 'Hard ordinary rebalance cooldown in seconds, 600..604800; selected policy43200 (12h), separate from compound and harvest intervals.',
    'minDepositUSD': 'Positive USD18 pool minimum (1 USD=10**18), checked alongside the stronger current action minimum; not raw ZZZ or current pool TVL.',
    'maxPositionUSD': 'Maximum cumulative gross contribution per NFT in USD18, at least minDepositUSD; not total bucket capacity or current mark-to-market value.',
})
annotate('ZZZSeaDropMint', 'configure((uint16,uint16,uint16,uint16,uint8,uint48,uint48,uint48,uint48,uint48,uint48,bool,bytes32,address,bytes32),uint128,bytes32)', 0, {
    'teamAllocation': 'Reserved free-team NFT count, uint16, initially20; cannot fall below already issued team count; team+allowlist<=1000.',
    'allowlistAllocation': 'Paid allowlist NFT count, uint16, initially500; cannot fall below issued allowlist count. Unused allowance rolls into public.',
    'publicWalletLimit': 'Lifetime original-recipient count ceiling, 1..1000; transfers do not restore mint quota.',
    'feeBps': 'Reviewed paid platform share in basis points, 0..10000, included in gross governed mint price.',
    'maxBatch': 'Maximum NFTs in one mint callback, 1..10; engineering ceiling is not actual VRF/payment/gas qualification.',
    'teamStart': 'Positive inclusive Unix seconds uint48; at or before teamEnd.',
    'teamEnd': 'Inclusive Unix seconds uint48; strictly below allowlistStart.',
    'allowlistStart': 'Inclusive Unix seconds uint48; strictly after teamEnd and at or before allowlistEnd.',
    'allowlistEnd': 'Inclusive Unix seconds uint48; strictly below publicStart.',
    'publicStart': 'Inclusive Unix seconds uint48; strictly after allowlistEnd and at or before publicEnd.',
    'publicEnd': 'Inclusive final Unix seconds uint48; match NFT.setMintEnd and public-drop end. The separate royalty opening is end+3600.',
    'releaseUnusedTeamToPublic': 'False initially preserves unminted free-team slots; true releases unused team capacity. Issued history never resets.',
    'merkleRoot': 'Independently reviewed shared free-team/paid-allowlist root with correct phase leaves; zero allowed only when both reserved allocations are zero.',
    'feeRecipient': 'Exact reviewed nonzero platform recipient; match the one allowed upstream recipient, not creator proceeds or royalty receiver.',
    'allowedPayersHash': 'Keccak-256 of abi.encode(address[]) of sorted unique reviewed nonzero payer addresses, maximum16; use the encoded empty array for no payers, not bytes32(0).',
})
converter = contracts['ZZZLPRewardConverter']['functions']
converter['setConversionLossBps(uint16)']['inputs']['0'] = 'Future conversion-loss limit in basis points, 0..1000 (100=1%,1000=10%); gas separate and stronger caller minimums remain binding.'
converter['setEnabled(bool)']['inputs']['0'] = 'True enables future conversion attempts; false stops them without reading external dependencies. Neither changes NFT rights or funded claims.'
converter['setRouteEnabled(bytes32,bool)']['inputs']['1'] = 'True revalidates and enables this admitted route; false disables it without querying failing dependencies. Not an ETH amount.'
path.write_text(json.dumps(notes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
print('Reviewed all operator tuple components and corrected three converter control inputs.')
