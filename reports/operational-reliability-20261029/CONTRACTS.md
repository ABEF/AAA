# Contract operational reliability: second source pass

2026-10-29; read-only. No new independently reproducible contract defect was
confirmed in the paths below. No Solidity or test file was changed, and no
compiler, EVM test, network, service or signing action was run. This is additional
source reasoning over the existing exact build closure, not a fresh whole-suite
claim or global security approval.

## Cases challenged and dispositions

| Case | Source path and adversarial question | Disposition |
| --- | --- | --- |
| OR-C01 | `Access:77–120,195–211`; `ZZZModule` authorization/lifecycle modifiers. Can governance rotation, guardian pause or unpause restore a retired/importing deployment or terminal principal rights? | No witness. Governance is a two-step transfer; keeper rights stay separate. Module/keeper authorization requires sealed canonical state0. Ordinary unpause does not change canonical state or `lpExitStarted`; principal operations check the terminal lock before and after callbacks. A governance rotation deliberately does not revoke other role grants automatically. |
| OR-C02 | `NFT:139–192`; `Vault:198–208`; `OperatorControls:112–158`. Can a receiver/counterparty cause duplicate mint/request, mint-only pause cancel old reveal, or late settings replace old randomness? | No witness. NFT mint is nonreentrant, binds request/ordinal before receiver callback, rejects duplicate/zero request IDs and rechecks mintPaused after the receiver. Fulfillment is coordinator-only, stores original two words once, and reveal proceeds in ordinal order without reroll. Future request settings do not replace pending requests. Existing tests were read, not rerun. |
| OR-C03 | `Vault.mintDormant`'s later proceeds callback versus NFT's earlier receiver check. Could a governance proceeds recipient pause/mint-pause after NFT creation yet let the outer mint finish? | **Rejected as a confirmed defect.** Source chooses a receiver-time mintPaused check; documentation promises stopping new mint work, not universal rollback for every later administrative callback. A legitimate later governance call is not itself an exploit. Preparation is rechecked by Vault's outer operating modifier. Terminal exit must cross the nonreentrant Vault barrier and cannot start inside mint. No source change/test was added merely to impose broader pause-completion semantics. |
| OR-C04 | `Vault:257–320`; `Entry:157–184,204–276`; `ContributionPricing:139–178,209–275`. Can owner changes, price/cap callbacks, reserve release or incumbent repricing subsidize an entrant? | No new witness. Entry validates owner again through final approval reset/endEntry; source price/cap basis starts before pull/conversion and persists through final checks. Only the explicit entrant budget is balanced/deployed. Incumbent LP is repriced before put; old idle and released compound stay in incumbent NAV. Shares are based on net added NAV; marginal deployed LP is a separate acceptance floor. Direct Vault owner-to-NFT gifts during an authorized operator transfer do not establish unauthorized spending by an outsider. |
| OR-C05 | `Fees:68–120`; `Membership:37–74`; `Rewards:67–148`; contribution fee checkpoints. Can repeated sub20 receipts create a new reserve, entrant entitlement or sweep? | No new witness. Whole20-unit amounts allocate80/10/5/5; carried remainder is settled to incumbent individual shares before membership changes. Repeated sub20 settlements are not cumulatively bounded; this is the existing asset/dust economic qualification, not a fixed-ratio proof for every raw receipt. Classified compound/buyback and reward fractions remain distinct; no new generic withdrawal is inferred. |
| OR-C06 | `Rewards:151–228`; `RoyaltyRewards:127–163,187–265,298–346`; `ClaimRouter:48–78`; `RewardConverter:157–226`. Can conversion redistribute rights to the wrong owners, duplicate a claim, or turn a failed optional royalty read into zero backing? | No new witness. Conversion batches are sorted/unique, at most32, consume selected funded liabilities and conserve output with cumulative rounding into the same NFT records. Claims check actual current owner; router repeats owner checks after earlier callbacks and is atomic. Optional activation reads can defer only that currency's cohort; later synchronization assigns unseen receipts to the old cohort before enrolling waiters. Unreadable actual backing may still block custody qualification. |
| OR-C07 | `Vault:528–584`; `Migration:314–329`; `CustodyValidation:21–32`. Can parking/move/resume redirect principal externally or replace token identity? | No witness. Parking retains principal in Vault under a paused custody manifest with raw close minima; resume/move require the same ordered pair and guarded deployment. Shares persist. A failed destination config, token/core runtime or normal financial check is not permission to skip it. Pool operations can be disabled without preventing the separate governed close path's structural dependency checks. |
| OR-C08 | `Migration:166–308`; `Vault:489–525`. Can terminal close omit compound, pay old owners, duplicate payment, or let a rejecting/expensive owner block others? | No new witness. Irreversible start snapshots bounded buckets/share denominators before closing; actual principal plus released compound is apportioned by cumulative shares. Allocation/payment batches are capped32. Payment uses current owner, self-call isolation and backed retry/owner fallback. `paid` is set before transfers and rollback isolates a rejected payment. LP rewards, royalties and buyback reserves are not principal. No USD swap guarantee is invented for raw exit. |
| OR-C09 | `CanonicalHandoff:181–469`; `VaultCanonical:106–269`; `FeesCanonical:41–140`; base canonical ledger. Can partial import/funding, prefunds, callbacks or abort open both deployments? | No new witness. Freeze requires parked/None custody; captures and ordered settlement precede export/import. Import compares exact source rows/roots; backing is paired by domain/index/asset/amount, with exact transfer deltas and separate prefunds. Commit's source retirement and destination activation are atomic. Abort cancels the importer and requires every transferred row returned before reopening the source. Failed token/backing reads remain a blocking recovery dependency, not guessed zero. |
| OR-C10 | `NFTCanonical:16–77`; `NFT:317–347`; `Rewards/RoyaltyRewards` canonical codecs. Can successor request IDs collide with imported randomness, dropped approvals give old operators rights, or deferred royalty cohorts replay? | No new witness. Imported records retain their old epochs, then the successor uses epoch+1 for future requests. Ownership is imported without copying old operator approvals. Deferred-join paid baselines are flattened into portable per-NFT rows; royalty cutoff settlement enrolls waiters once. Retired late receipts are forwarded only to the immediate canonical successor, so multi-hop forwarding/recovery remains explicit. |
| OR-C11 | Fixed1,000NFT scope,4buckets,33LP/17royalty assets; `Handoff.MAX_ROWS=8`, `Migration.MAX_BATCH=32`, converter/claim batches32. Can a public caller supply an unbounded array or force whole-supply payout/reveal in one transaction? | No such witness. Public export/import/allocation/claim/conversion work is bounded; NFT reveal is one ordered record. Capture/settlement has fixed asset/bucket loops, and terminal startup checks every bounded bucket. This does not establish actual maximum gas/provider availability: source limits and historical mock fixtures remain separate from actual qualification. Pool aliases are governance-append-only and not bounded to four; four bounds physical buckets, not the number of aliases/admitted routes. |

## Management constraint for operator review

`Vault.reservePool(pool,bucket)` (`Vault:107–118`, `Budget:296–300`) accepts an
admitted pool and any nonzero unconflicted bucket, permanently records the
alias, and may consume a permanent bucket slot. Initial activation, while that
bucket is None, requires the reserved bucket to equal the canonical
`bucketIdentity(pool)` (`Vault:222–226`). A governance reservation to an arbitrary
new bucket can therefore make that pool's first activation unavailable; aliases
cannot simply be reassigned. A deliberate move instead aliases the destination
to an already active/parked canonical bucket.

This is an authorized irreversible setup error within the explicitly permanent
reservation policy, not an unprivileged contract exploit or grounds for adding
a release/unreserve mechanism. For a fresh operating origin, operator code
should distinguish first-activation canonical reservation from a deliberate
existing-bucket move and review identity/permanent capacity before drafting.

**Successor exception:** a moved source bucket originally created for pool A but
currently using pool B exports alias B→originalBucketA. The successor must
import that exact alias, not derive a new bucket from B. Its local None state
before import does not justify a universal canonical(B) rule. In fact the current
import header requires destination sequence0, bucketCount0 and aliases.length0
(`VaultCanonical:165–167`): executing a local reservePool before import would
make it nonempty and reject import. Planned/source-inherited alias validation
for an inert successor and executing a fresh local reservation are different
operations. Backend/preflight applicability is being checked independently;
this source observation alone is not a claim that a production gate falsely
passes either case.

## Why no additional test was run

The challenged mint-proceeds callback lacks a proven violated completion
invariant; executing a mock merely to show authorized ordering would not resolve
that policy question. Existing canonical/holder/claim fixtures already contain
focused cases for freeze and partial funding, abort/recapture, all1,000ordinals,
four buckets, rejecting/gas-consuming recipients, duplicate batches, callback
transfers and prefund isolation. Their method names/bodies were consulted as
existing evidence, not counted as newly executed passes. No new source change
or unresolved concrete witness justified rerunning them here.

Actual dependency authority/upgrades, liquidity/economics, gas/host limits,
VRF/provider availability and independent review stay open. A blocker requiring
a bad trusted implementation, intentionally waived emergency finances or a
deliberately irreversible governance configuration is not relabelled a newly
discovered unprivileged exploit.
