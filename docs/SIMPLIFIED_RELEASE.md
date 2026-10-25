# Simplified release boundary

The current candidate accepts **native ETH or the explicitly reviewed ZZZ token**
for activation and growing attached LP. No stablecoin or WETH user input is
admitted. The ZZZ identity is bound once before sealing. An issuer token migration uses
custody exit and a fresh deployment; ordinary asset admission cannot enable a
third contribution currency. This is separate from pool accounting and marketplace royalty currencies.

## Kept, removed and why

| Component | Current purpose |
| --- | --- |
| Vault, Liquidity and Strategy | Shared LP custody, actual placement, harvesting, approved range management and guarded maintenance. |
| Fees and Rewards | Allocate physically received local LP fees at 80/10/5/5, preserving each NFT's earned rights and equal collective membership. |
| NFT royalty receiver and ledger | Account for royalties actually received, including admitted non-ETH marketplace settlement currencies and their guarded ETH conversion. This feature remains. |
| Migration | Same-chain pool movement, parked custody, explicitly approved normal/raw exit to the chosen external custodian, exact funded return and local redeployment. |
| Canonical handoff | Same-chain replacement of NFT ownership, shares, reward ledgers and exact backing, with one active deployment and funded abort. |
| Creator-payment inboxes | Removed. The selected hookless pool supplies actual LP fees directly; there is no creator-payment agreement or inbox service to operate. |
| Integrated bridge and remote fee accounting | Removed. The custodian may perform an external token migration or bridge outside PoPL. This does not migrate canonical NFT ownership or create verified remote LP value. |
| Legacy always-reverting functions | Removed from the callable ABI; old selectors reject rather than expose a misleading operation. |

Keeping separate ledgers and bounded companions serves custody and bytecode
limits. Combining them solely to reduce the contract count would not simplify
economic verification. Historical readers and old event decoders remain because
removing old income or transaction history would corrupt recovery and reporting.

## Residual cleanup

The [follow-up review](../reports/obsolete-code-20261025/REVIEW.md) removes unused
Registry wrapper-review records, creator-payment measurement tooling and orphaned
internal declarations. Converter-specific wrapping checks remain active. New
Registry storage is for a fresh deployment only; existing Anvil code/journals
retain their original layouts. Current source/fee/custody/schema identities and
economic rights are otherwise unchanged.

## Operator changes

1. Configure the reviewed ZZZ identity in `PoolRegistry.activationAssets()` with
   `configureZZZ(token, codeHash, reviewHash)` once before sealing, using actual
   token/runtime and dual-price evidence. Rebinding is rejected.
   Native ETH uses its explicit native identity. Disable/re-enable these two
   inputs through their append-only source policies. Bind `Migration.configureZZZ`
   to that same identity before sealing; seal rejects unset/mismatched bindings.
   Changing the token identity
   requires custody exit and a fresh deployment.
2. Keep contribution, conversion and maintenance defaults at **2%, 1% and 3%**,
   respectively; governance maxima remain 10%, with gas separate. A smaller
   caller maximum still applies. No silent loss-cap widening or sweep is added.
3. Use `Migration.moveFunds` for a supported same-chain, same-ordered-pair pool
   move. Review and select the contribution pool separately. ETH and WETH remain
   distinct assets; a different pair requires the trusted custody workflow.
4. For custody exit, pause, review parking, capture the stable source snapshot,
   approve the exact local request and execute `exit`. Ordinary exit converts to
   reviewed ZZZ under its budget; explicit raw exit performs no swap and uses raw
   minima. Failure never automatically downgrades normal exit to raw exit.
5. Use `recover(id, deadline)` to return **all actually sent assets**, or the
   reviewed local completion path to deploy funded assets. An externally bridged
   balance is outside PoPL custody and is not reported as redeemable remote LP.
   There is no built-in finality verifier, remote completion or bridge operator.
6. Do not schedule creator-inbox synchronization. LP harvesting, compounding,
   buyback and royalty conversion remain separate bounded keeper jobs.

A fresh deployment does not automatically move existing NFTs or erase earned
rewards. Preserve ownership, shares and both ledgers through the reviewed funded
same-chain handoff when replacing an existing collection; resolve outstanding
custody first. External exit alone is not collection migration or a reset.

## Explicit compatibility boundary

Current profiles require `fee_intake_version: 1`, `Fees.FEE_INTAKE_VERSION() == 1`,
`Migration.CUSTODY_VERSION() == 2`, and canonical schema
`ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V3`. There are 15 current inventory helpers, including the fixed noncustodial source-policy factory;
the deleted reward-receiver factory is not a zero-address placeholder.

The fee header is two words and each fee bucket row four words. Old inbox/remote
rows cannot be imported under this schema. Old local deployments, journals and
source-bound evidence retain their original profile. Absence/zero fee profile
means historical inspection, never current release qualification. No running
deployment is upgraded or reset by these source changes.

Read the [operator manual](OPERATOR_MANUAL.md), [callable reference](CONTRACT_FUNCTIONS.md)
and [audit scope](../reports/simplification-20261025/REVIEW.md). Public signing,
real dependencies, OpenSea qualification, operating rehearsals and independent
release approval remain open. This candidate is not approved for real funds.
