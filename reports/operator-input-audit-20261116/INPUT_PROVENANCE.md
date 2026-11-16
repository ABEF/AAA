# Input provenance, authority and moving-state review

The [complete inventory](inventory.json) records every exact ABI row and recursively expanded input/output. The 92 operator/nominated targets have 333 input records including containers, 317 leaves and 137 nested records; every operator input has an explicit explanation. This is source/input reconciliation, not 92 fresh successful EVM operations.

| Input kind | Authoritative producer | What can invalidate it | Safe next action |
| --- | --- | --- | --- |
| Collection NFT ID | `NFT.tokenAtOrdinal(ordinal)` or authenticated confirmed holdings | Transfer changes caller/beneficiary, not the full ID | Reread owner; preserve uint256 precision |
| Bucket | `Vault.nftBucket(NFT_ID)`, `poolBucket(POOL_ID)` and `group(bucket)` | Movement changes pool mapping; terminal/canonical lifecycle changes allowed actions | Recheck group and lifecycle |
| Physical main/residual ID | `Vault.group(bucket).lpTokenId`, `Manager.secondaryId(main)` | Rebalance/replace/close/move, including another authorized operation | Reprepare from current identity |
| Existing boundaries | `Manager.ticks(main)` and authenticated position information | Protocol replacement changes IDs/geometry; ordinary swaps do not move these boundaries | Keep exact main geometry for same-main consolidation; use separate replacement if unsuitable |
| Current spot and active status | Same confirmed anchor's core/StateView | Swaps, liquidity operations and ordering before inclusion; not a reservation | Contract rechecks; retain price/floor guards |
| Stable geometry fingerprint | `Manager.portfolioFingerprint(main)` | IDs/key/bounds/ownership/dependency identity changes; liquidity increases are intentionally excluded. Governed policy controls are committed separately where required | Do not invalidate observations merely from top-up L |
| Physical portfolio fingerprint | `Manager.executionPortfolioFingerprint(main)` | Contributions change main L; close/replacement changes IDs/ticks/L | Capture after pause for parking/residual close |
| Full replacement custody hash | `Migration.emergencyCustodyHash(bucket)` | Encoded Position/share/physical execution changes; does not itself include consolidation nonce/epoch/policy controls | Use the fresh operation-specific hash; validate other controls separately |
| Residual reinvestment custody hash | `Migration.consolidationCustodyHash(bucket)` | Included nonce/epoch/portfolio/control changes; different domain from replacement | Never substitute emergencyCustodyHash |
| Parking fields | `Vault.group`, `bucketTotalShares`, `Migration.custodyEpoch`, `parkingNonce`, accounting PoolKey | Activation/growth changes shares/deposit/L; custody operations consume/change epoch/nonce | Read a coherent snapshot after pause, preserve the original request |
| Review hash | Digest of independently reviewed exact manifest | Manifest/source/terms change; bytes32 nonzero alone proves no review or authority | Review and regenerate, never use a guessed hash |
| Source/runtime pins | Exact deployed code, provider round/decimals and control review | Code/implementation/administrator/source publication changes | Requalify; distinct names/addresses do not prove independence |
| Pool key/ID | Reviewed initialized ordered PoolKey; Keccak of ABI encoding | Key itself is stable; directional protocol fees and market state can change | Keep identity distinct from mutable price/fee evidence |
| Minima and explicit swap fields | Caller-reviewed exact operation simulation/manifest | Price/depth changes before inclusion can make floors infeasible | Safe rejection/reprepare; never lower automatically |
| Timing | Original Unix-seconds deadline and actual on-chain clock | Inclusion delay, cooldown/reset/state transition | Reprepare a new review; do not silently extend an old review |
| Royalty recovery quantity | `RoyaltyRewards.orphaned(asset)` plus synchronization at execution | New receipts/sync/opening/cohort change | Explicit reviewed allocation; existing earned backing excluded |
| Sale helper/upstream terms | Current Policy/SeaDropMint and SeaDrop getter checks | Price/payee/end/root/payer/fee-recipient updates | Synchronize the complete reviewed set before mint; intermediate blocking is intentional |
| Canonical progress cursor | Current source/import coordinator getters | Permissionless valid progress can advance cursors | Reread; source-authenticated records still prevent altered rights |

## Source-specific conclusions

- Access `canConfigure` separates bootstrap before seal from governance after seal. Governance rotation does not implicitly rotate keeper/guardian. Actual source allows guardians to pause but never unpause. Global pause does not stop external Uniswap trading.
- `ZZZModule` rechecks governance, operating and terminal boundaries where declared. Direct governance is not automatically keeper authorization. Module-only and callback-only endpoints remain separate from wallet targets.
- `FeeController.flushDust` is restricted to sealed Vault/Membership; `Vault.collectFees` is public. Permissionless collection changes timing of realization but does not grant recipient or allocation control.
- `Migration.consolidateResidual` already completes residual mode OFF atomically after verified same-main reinvestment. `closeResidual` only closes to attributed idle and does not disable future mode or automatically reinvest.
- SeaDrop's NFT callback does not carry price/stage/payment proofs. Exact reviewed upstream runtime and complete Merkle-leaf/payment manifest remain a trust/qualification boundary. Reusing the current root with changed leaf terms is rejected; reuse of older roots is still a reviewed manifest responsibility.
- Sale price/payee/end configuration updates can intentionally block mint until the helper and upstream exact terms agree. This is a coordination requirement, not permission to skip fingerprint validation.
- Canonical export/import/fund progress can be permissionless without letting arbitrary callers change recorded bytes, backing receivers or governance commit/abort authority. A previously read cursor can be stale from valid public progress; protective rejection should be followed by a fresh read.
- Royalty admission after opening quarantines prior unsupported receipts as reviewed unallocated value. Explicit recovery uses current active weights; existing earned/deferred rights remain separate. Capacity/gas and conventional exact-transfer token admission remain release obligations.
- Ordinary swaps before inclusion affect executable ratio/output, not fixed bounds. Other transactions do not interleave an atomic close/swap/mint; callbacks and reentrancy are different boundaries and remain guarded.

## Corrections and evidence

The reference producer now accepts strict nested tuple notes in ABI order, while retaining legacy string notes. Three LP converter `value` inputs now state actual basis-point/boolean semantics. Expanded operator examples retain distinct operation-specific semantics even when two operations share a Solidity struct type.

Six distinct new tests pass; exact current function-reference checking passes without compiling, RPC or contract execution. [Verification record](inventory-verification.json) retains the one-off digest-helper decoding correction and finite scope. Full behavior and guard/economic conclusions remain in the main report and contract-family review.
