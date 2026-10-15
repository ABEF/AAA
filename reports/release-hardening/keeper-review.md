# Keeper metadata workflow: separate internal review

Completed 2026-10-15 by an agent separate from the keeper implementation author. **Not an external audit or production approval.** This review made no keeper-source edits and submitted no real transaction. Exact hashes, resolved findings and test identities are recorded in [keeper-review.json](keeper-review.json).

Frozen inputs were `keeper/monitor.py` SHA-256 `25fc60e9d9d0e4966b5c919b69532330b98c72ae34c7ef9dbed028ad37a4c125`, `keeper/config.example.json` `aa7986b2ca6c60214732b4851789f2a24da04e22eaa25b4197ccd19f6312f39e`, and metadata tests `1f07219db1be9d66d01b9135229f9b093ec472262cac97184e4db2ecc28c879f`.

## Findings resolved during review

| Finding | Before | Reviewed resolution |
| --- | --- | --- |
| Partial/wrapped scan starvation | The cursor skipped a full 50-token observation window after submitting only its smaller/nonwrapping prefix. Repeated prefix changes could indefinitely omit trailing NFTs. | Changed work now advances past the selected notification range; unchanged work advances past the full scan. Both maintain a durable cursor without claiming successful notification. |
| Trigger-state versus execution-state race | An observation at stage A could notify during stage B, then suppress a later return to A by storing the old trigger fingerprint. | Confirmation re-reads the bounded exact IDs, traits, availability and stage at the canonical receipt block, then checkpoints that execution snapshot. Invalid/aged triggers clear previous selected fingerprints to permit retry. |
| Simultaneous trigger/receipt reorg | The author found an early invalid-trigger return that could bypass final receipt anchoring. | Canonical receipt rechecking now precedes both successful checkpointing and invalid-trigger cache clearing. Malformed execution observations or changed receipt blocks retain pending state. |

The starvation regressions continually change ordinals 1/51 with 100 NFTs and scan50/batch10, and ordinal98 with cursor98 and the default 50-token batch. They demonstrate coverage of all 100 NFTs despite those changes. The state-race regression includes a prior baseline, a new trigger, a different receipt-block stage, and a return to the trigger stage without suppressing notification.

## Scope and verification

The reviewer inspected persistent chain/controller/NFT identity, fixed module/canonical-chain/runtime bindings, bounded canonical ABI observations, exact zero-value calldata intent, durable pre-signing pending state, existing nonce/transaction/receipt identity and budgets, reorg handling, feature-disable reconciliation, and priority between metadata and pool maintenance. Notification makes no LP principal, reward or royalty change; the scan is separate from pool-level rebalancing.

The separate reviewer then executed **10 targeted regressions: 10 passed, zero failures/errors/skips**, in 3.968 seconds. Inputs remained byte-identical before/after. This includes both starvation schedules, receipt-state and invalid-trigger cases, malformed receipt state, simultaneous/during-confirmation reorgs, tampered pending calldata, disabling/reconciling pending work and metadata/LP priority. See [execution log](keeper-review-tests.log) and the nested source-bound receipt in [keeper-review.json](keeper-review.json). The author's full focused run and the parent's complete Python suite are separate evidence; these ten tests are not added to their totals.

No further actionable issue was found within this scoped internal review. That does not establish exploit absence or close production gates.

## Operating limits

- Change detection fingerprints **stage, valuation availability and reveal readiness**, not every price movement within the same stage. Marketplace numeric metadata can remain cached between refreshes.
- ERC-4906 events request a refresh; external marketplace retrieval and display timing remain outside the protocol's control.
- Tests use mock RPC and signer results. Real RPC, encrypted-keystore signing, actual chain confirmations/finality, interruptions, recovery and monitoring still require staging.
- Rechecked block anchors do not prove absolute finality or protect against a dishonest RPC. Production provider/confirmation/outage policies remain review obligations.
- Metadata automation defaults disabled. Authorities and deployment configuration remain unselected. Actual VRF, immutable artwork publication, selected native-ETH/Pons custody and input routing, bridge backing, independent audit and deployment review remain open.
