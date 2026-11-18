# Constant-cost exact royalties and bounded activation reads

Fresh source candidate,18November2026. Main only. Production remains undeployed and NOT APPROVED.

## Outcome

Royalty receipt allocation now updates constant-size complete rounds/cursor state rather than a holder tree. Each currency retains at most1,000 immutable enrollment boundaries; scalar claims find the birth cohort within10 binary-search steps. Original-currency exact-unit rights, rarity1/2/3, current-owner claims, one-hour opening, earlier-cohort recovery, flattened canonical import/export and funded abort remain. This append-only royalty design does not replace the separate mutable LP engine.

Activation balance reads have a separately governed50,000gas default,10,000–1,000,000 engineering bounds and a fixed32-byte copy. A token cannot force unbounded return copying. Funding is proved for the complete frame or independently for the read plus120k. Only the fixed child's authenticated4-byte read-unavailable signal permits partial-frame deferral; other failed partial frames revert the activation. The complete-sync maximum stays1M. Ordinary sync/claims/canonical reads retain their existing paths. No required pre-sync worker, payout currency conversion or extra holder transaction is added.

**The full20M profile with20% headroom is still unqualified at maximum tested state.** All13 actual cold20M calls and financial/entitlement checks pass, but only5 fit the required padded budget;8 activations are correctly refused. Comparable original-source cases save824,023–1,782,018 estimated gas. The worst final case needs23,190,542 including padding. Limits/defaults are unchanged; these refusals are not relabelled bad-token faults or accepted profiles.

## Additional fixes and identities

- Replace duplicate royalty `accounted` storage with the checked identity `liabilities + orphaned + openingPool`; keep monetary/backing/overflow checks.
- Correct a demonstrated import blockage: an unused replacement's synchronized ETH/ERC20 opening prefunds were counted twice. Import now clears that opening classification and counts actual prefunds once as orphaned, independently of earned source liabilities. A C07 failure and C08 regression pass preserve the evidence.
- Reuse only adjacent immutable-child/STATIC placement proofs; retain full public/callback and final mint proofs. Entry validates admission, then uses its already authenticated captured USD quote before funds move. Economic floors, oracle checks, exact balances and callback boundaries remain.
- Fresh `ROYALTY_ALLOCATION_VERSION()==2`, explicit factory payload5 and exact runtimes/source pins are required. Settlement4/recovery2/reporting5/schema17/canonicalV10 flat wire semantics remain. Private books/layout change; never reinterpret old raw storage or relabel payload3/4, old runtime reviews or journals.

See [final source review](FINAL_SOURCE_CHANGE_REVIEW.md), [accounting proof](ROUND_ACCOUNTING_REVIEW.md), [final storage comparison](FINAL_STORAGE_COMPATIBILITY.json), [placement proof review](PLACEMENT_PROOF_REUSE_REVIEW.md), [prefund regression](synced-prefund/REVIEW.md) and [consumer review](CONSUMER_REVIEW.md). Initial proposal/phase1 and C07 evidence keep their original source scope.

## Verification and reuse

| Evidence | Actual scope |
|---|---|
| Eight current arithmetic prototype methods | Independent per-ticket oracle; prefix/phase/cursor transitions, cohort lookup at1,000, MAX lifetime wraps and imported accrued. Test-only arithmetic seam, not complete Entry gas. |
| C07 actual ledger14 methods | Nine new (six ledger, three funding) plus five affected prior Q03 controls. Exact claims/transfers/recovery/import; malformed/reverting/oversized/under-backed reads; starved-caller rollback and high configured cap. [Results](ledger-c07/RESULT.json). These ordinary paths retain an explicit final-source reuse boundary. |
| Final C08 prefund regression | One distinct new method: actual C07 failure then C08 pass; ETH/ERC20 prefunds, current-owner/imported rights, future receipts, complete eligible drainage and checked-MAX atomic retry. [Stages](synced-prefund/INDEX.json). |
| Final C08 affected abort control | One affected earlier method passes against final source, restoring source rights and future claims. [Result](funded-abort-c08/RESULT.json). Not added twice to the14-method prior stage. |
| Three Policy methods | Bounds/permissions/revisions; unchanged four-word gas tuple/fingerprint and post-seal-context behavior. [Review](POLICY_REVIEW.md). |
| Five new actual-v4 placement methods, C07 | Full public/callback proof, immutable-child placement, source-round/owner mutation rollback/retry, admission/minimum and phase/authority rejection. Exact ordinary-path reuse to C08; no manual emergency suite rerun. [Results](placement/RESULT.json). |
| Twelve distinct consumer methods | Initial11new/1adapted; strengthened historical-loader method and artifact-dependent follow-ups separately source-scoped. C08 four affected checks pass; eight controls reuse prior unchanged evidence. No count summation across executions. [Review](CONSUMER_REVIEW.md). |
| Final normal compile/admission | Exact100closed sources, unchanged compiler/settings/build inputs,48 runtime/initcode gates and strict importer pass. Royalty24,572/4bytes headroom; Manager24,459/117; Oracle24,573/3; Vault24,544/32; Access fullinit48,590/562. [Admission](build/final/ADMISSION_RESULT.json). |
| Final1,000-NFT full Entry method | One changed method,13 exported scenarios;999 real incumbent entries,16 admitted ERC20s plus ETH, mixed rarity, exact payouts/future rights/drainage. [Full-flow review](FINAL_FULL_FLOW_REVIEW.md). |
| Final13 cold RPC scenarios | Exact runtime/policy binding, financial trace reconciliation, actual20M calls, slow-read costs, fault deferral and growth isolation.5/13 meet full20% headroom;8refused. [Strict results](full-flow-final/full04/local-rpc/SUMMARY.json). |

No unchanged contract/browser suite was rerun. Updated old cooling helpers replace guessed private tree slots with recorded slots/account cooling; their two directly affected historical-source gas checks retain their own scope. Frozen V4 tree tests remain historical and unrun. Test/harness/compiler/infrastructure failures, interrupted/preflight stages and the failed initial gas design are retained rather than counted as passes. Component gas is never added into a claimed whole-operation estimate.

## Cold20M results

The padded amount is the fresh estimate plus the full20%, rounded upward. A successful actual20M call alone is insufficient. Padded simulations are accepted only when they fit the reviewed cap.

| Controlled scenario | Cold estimate | With20% |20M review |
|---|---:|---:|---|
| 999-opening-eth | 18,035,007 | 21,642,009 | Refused |
| 999-opening-zzz-allfault | 16,089,655 | 19,307,586 | Pass |
| 999-opening-zzz | 18,679,435 | 22,415,322 | Refused |
| 999-opening-zzz-allslow | 19,325,451 | 23,190,542 | Refused |
| 999-opening-eth-allslow | 18,681,023 | 22,417,228 | Refused |
| 999-rotated-zzz | 17,582,618 | 21,099,142 | Refused |
| 999-rotated-eth-onefault | 16,837,543 | 20,205,052 | Refused |
| 999-rotated-eth-allfault | 15,331,306 | 18,397,568 | Pass |
| 999-rotated-zzz-allfault | 15,975,734 | 19,170,881 | Pass |
| 999-rotated-zzz-allslow | 18,228,634 | 21,874,361 | Refused |
| 999-rotated-eth | 16,938,190 | 20,325,828 | Refused |
| 1000-grow-eth | 11,645,827 | 13,974,993 | Pass |
| 1000-grow-zzz-allfault | 12,291,980 | 14,750,376 | Pass |

## Remaining work and preservation

Q03 remains open: reduce the remaining complete Entry/accounting cost safely, then requalify only affected cold workloads. Do not lower headroom, misclassify healthy expensive reads, raise defaults or require an extra holder transaction to hide the blocker. A pre-sync may be an optional separately paid operation but cannot guarantee future state at inclusion.

This finite fixture has a fixed final entrant order, mixed600/300/100 mint quotas, two holder accounts, one physical main LP, controlled prices/VRF/depth and16ERC20 currencies. It is not all activation orders, two-leg/max64-currency/max-graph coverage, actual market/provider/fees, independent audit or release acceptance. Permanently malicious/frozen currencies can still prevent their own transfers and canonical completion; bounded activation reads cannot repair token semantics.

The12M default, reviewed20M contribution/full20%, maintenance24M, all economic/source/callback controls and NFT rights stay. No public transaction, deployment/seal, website/service rollout, existing chain/DB/journal/dist/signer/public-null change or heartbeat restart occurred. Only newly owned loopback verifier nodes were used and stopped. Four unrelated dirty files remain byte-identical and unstaged. Actual independent feeds/routes, provider/fees, VRF/OpenSea/authorities, selected deployment/operating adoption and independent approval remain open.
