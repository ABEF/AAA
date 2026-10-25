# Native royalty-custody producer boundary

`RoyaltyCustodyTest.testNativeCustodyDefersOnlyNewNativeEligibilityWithoutRetroactiveFees`
**passed once**, independently of the two native-regression cases. This existing
case was not included in the earlier 32-method selection.

The actual PoPL ledgers produce the deferred-native state expected by the API:

1. An existing activated NFT receives 1 ETH in royalties, which leaves through
   the explicitly governed native custody exit.
2. Another NFT activates its LP during custody. Its native royalty eligibility
   remains deferred; activation itself succeeds.
3. A further 0.5 ETH arrives while custody is outstanding. Exact return of the
   original 1 ETH restores backing without creating new royalty income.
4. After synchronization, the newcomer joins with zero retroactive entitlement;
   the incumbent NFT can claim exactly 1.5 ETH.

The run used a fresh isolated profile and unchanged hash-pinned AST driver,
took 112.563 seconds including compilation, and had no failures, skips, retries,
missing methods or unexpected methods. All 265 AST inputs and 75 unchanged
normal-build input bindings matched before and after execution. Exact bodies,
source hashes and raw artifact hashes are in [the receipt](native-custody-boundary-verification.json);
the [wrapper](run-native-custody-boundary.py) selects only this case.

This case exercises actual RoyaltyRewards/Membership/Vault/NFT accounting through
PooledVaultFixture's explicit MockAccess, token, oracle and fake LP venue seams.
It does not claim an additional installed-Uniswap-Core integration or live
provider qualification. No source/test, existing Anvil state, wallet journal,
public signer, service or website changed. The separate two native regressions
plus this producer case are three fresh methods in this review turn, with their
individual evidence scopes retained.
