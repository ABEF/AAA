# LP holder ETH settlement: scoped verification

2026-10-20. Internal development review; release **NOT APPROVED**.

The user approved a maximum 1% LP reward conversion loss, with network gas
separate. [The implementation and operator procedure](../../docs/LP_ETH_SETTLEMENT.md)
describe the exact accounting boundary. The fixed 80/10/5/5 allocation runs first;
only earned individual/collective whole units are converted, never LP principal,
compound/buyback reserves, orphaned funds or source fractions. Output remains
attached to the same NFT and its current owner.

## Results

| Scope | Evidence and limits |
| --- | --- |
| Solidity | **142 distinct passing affected cases** across scoped runs, including 1,000 fuzz samples, 32-NFT maximum batch, 99%/98.99% boundary, exact unwrap, source fallback, rejecting ETH owner, callback rollback, original rewards/fees, claims, capacity/gas and complete same-chain handoff. [Coverage](solidity-coverage.json) identifies the latest passing receipt per case; this is not a newly executed full regression. |
| Compiler objects | **32 normal size gates**, **41 exact production-source bindings**, Solidity 0.8.26/Cancun/via-IR/optimizer-1/Yul-disabled. [Build review](build-review.json) records runtime/initcode and constructor limitations. Vault still has only 19 runtime bytes spare. Standalone Windows `forge build` produced artifacts but then returned a cache-directory error; passing `forge test` runs and exact artifact/source checks establish the scoped compilation, not a successful standalone build command. |
| Backend | Initial 99-case run exposed a new-test import error and obsolete native-LP rejection assertion. After correction, 66 cases exposed the missing native `ownerIndex` read allowance; it was fixed. The [12-case focused rerun](lp-eth-python-attempt3.log) passes. [Dependent run](lp-eth-dependent-python.log): 273 cases, 271 passes and two Unix-only skips on Windows. [API run](lp-eth-api-regression.log): 91 cases exposed old asset-limit/native expectations and an existing draft expiry-message expectation; [three corrected cases](lp-eth-api-fixture-corrections.log) pass. [Final scheduling/lineage run](lp-eth-scheduling-lineage.log): 99 cases, 98 passes and one Unix-only skip, including two new cases. Runs overlap; counts are not summed as unique coverage. |
| Local chain and website API | [33 assertions pass](local-journey-summary.json): exact approval, activation/no past fees, top-up, confirmed LP, transfer, invalidated old-owner draft, native LP-plus-royalty claims, repeated-operation recovery and mint. Both prepared claim operations use native ETH only. [Full receipt](local-journey.json) retains disposable local transaction hashes and confirmed projections. Reserve-backed local WETH, deterministic swaps and $1 mock prices do not qualify Robinhood. Existing user Anvil state was not reset. |
| Website | The 38-case affected run exposed a pending-card financial-read regression and an already-stale assertion for the removed Previously claimed frame. The first was fixed and passed in the [37/38 rerun](lp-eth-site-tests-fixed.log); the stale assertion was corrected to enforce the user's earlier removal. Final focused UI receipt is retained separately. Source currencies remain visible as awaiting conversion and are never relabeled ETH. Catalogue validation and the 5,590-file build pass; artwork is unchanged. |

[Source bindings](source-bindings.json) cover the final changed production code
and focused tests. Final line-ending normalization did not change test bodies;
the binding file explicitly hashes LF-normalized text. Production compiler
metadata is checked against exact source bytes separately.

## Findings corrected during development

- Adding native settlement to the Rewards inventory exposed two real integration
  assumptions: Vault/Fees canonical helpers attempted an ERC20 balance read at
  address zero. Both now skip the Rewards-only native slot. All 34 original
  handoff cases and 22 claim-router cases pass afterward. A new full-system case
  converts 3 ETH of LP rewards, transfers the NFT, freezes/imports/funds/commits,
  then proves only the new owner can claim it on the replacement.
- Native LP history needed an explicit zero-address allowance for the confirmed
  `ownerIndex` read. Native rewards have no index accrual; import rejects nonzero
  native indices/fractions. ETH credits reconcile against original earned source
  units, conversions and actual claims; they are not new income.
- Conversion scheduling now grants LP conversion, royalty conversion and
  maintenance alternating priority. Buybacks execute before fallback conversion
  on the maintenance turn; a busy conversion stream cannot consume that slot.
  Existing pending-transaction recovery takes precedence over all three.
- One pending UI path read the financial payload before its identity was ready;
  the conversion notice now respects the existing pending guard.

Initial fixture failures are retained: the first fuzz mock lacked enough native
backing for its synthetic large inputs; its reserve was enlarged. The new
handoff test initially consumed a one-call `vm.prank` on an intervening getter;
the getter was moved before the prank. Neither required weakening production
guards. The corrected full-system case passes. The first fresh local launcher
rejected stale compiler artifacts, then started after the matching build.

## Internal security review and remaining gates

Reviewed exact ledger/converter binding, immediate-governance dependency trust,
exact approvals and resets, typed routing, fresh oracle floor and deadlines,
input/output deltas, callbacks, current-owner claims, source fallback ordering,
rounding conservation, no redistribution to new members, native donations,
prefunds/backing/abort, claim/event separation, predecessor cutoffs and bounded
keeper nonce/pending state. No arbitrary payout recipient or principal access
was introduced. This is not an independent audit or assurance of no vulnerabilities.

Actual WETH/proxy policy, source swap routes/liquidity, independent feeds,
operator pins, economical batch sizes, full 1,000-NFT settlement latency,
Linux hosting/long-run recovery, target-chain gas and independent audit remain
open. Oracle error or harmful governance-approved dependencies can still cause
loss. A successful batch can use the approved 1% allowance; gas is additional.
Source assets remain claimable as an explicit fallback; a broken token may also
block that fallback. Native ETH rejection by a contract holder preserves its
claim but requires a compatible owner/receiver arrangement. Converter/wrapper
binding is irreversible after sealing. Same-chain schema compatibility must be
reviewed before replacement; different-pair and cross-chain handoff remain open.

No public contract deployment/transaction or paused-monitor restart occurred.
Git and the website deployment receipt establish publication separately.
