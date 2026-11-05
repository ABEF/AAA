# Verification and source boundaries

Internal, source-scoped verification; **production NOT APPROVED**. This is not
a full regression, public CI result, real-wallet campaign or independent audit.
Use [review](REVIEW.md), [evidence](evidence.json) and the exact input hashes.

## Final evidence

| Evidence | Result | Limits |
| --- | --- | --- |
| Normal closed compiler |43/43gates;52production plus31dependency sources unchanged; Solidity0.8.26/Cancun, viaIR, runs1, Yulfalse | Normal runtime and initcode bounds; exact dynamic constructor arguments and target gas still require qualification. |
| Final selected contract stage |25/25methods, unchanged source/tests |5mint,7ledger canonical,2actual-wire,2cooled gas,3factory,3claim/reentry,3integrated handoff/abort. Integrated principal venue is synthetic, not current-pool fork qualification. |
| Final cancelled-recovery stage |6/6methods, unchanged source/tests | Completed funded abort, current governance, callback rollback, old unallocated separation, two retired hops, later aborted successor snapshot and helper-call rejection. Earlier six-case stages are not additive. |
| Allocator |12methods;256fuzz runs with64step sequences, all3,000engineering tickets, repeated MAXuint drain, iterative/recursive representation comparison | Exact unchanged internal helper source reused. This alone does not prove the ledger's cohort/GCD/permission logic. Earlier26GCD/factory/allocation methods retain their own source scope; not relabeled as a fresh whole-contract pass. |
| Backend |223/223methods,0failures/errors/skips, unchanged inputs |17affected modules; actual source fixture has34logs,6getter snapshots and12V8rows. Includes replay/checkpoint/lineage, one-based wire adapters, zero canonical telemetry, mint reviews and opening readiness. Supersedes earlier synthetic168acceptance; overlapping stages are not added. |
| Profile/observer/event/CLI cohort |55distinct selected methods accepted across53original successes and2corrected CLI reruns | Two old expectations still said current schema8; corrected to13 while preserving false readiness. New8-profile checks are already included in55. Historical observer bounds remain33; fresh bound97 is not admission/gas approval. |
| Reference/static checker |93/93methods | Parser/coverage/default drift controls; no new contract execution. |
| Function/operator generation |36contracts,814functions,36constructors,12receivers;862examples;0input/output/explanation gaps | Templates only, no transaction readiness or simulation. Todo generated/check passes. |
| Website |210/210selected source-helper cases | Opening status, locked/native totals, original currencies and dormant deadline preference. Signer/config/dist untouched. Complete fresh native6 consumer and browser/marketplace acceptance remain open. |
| Keeper changes |8focused methods pass | Explicit settlement4 supported, older2/3 preserved, no royalty swaps, LP conversion separate, pending state/nonfinite clocks protected. No operating service or cadence qualification. |
| Static analyzer |487actual detector records, successful analyzer completion, unchanged83sources; strict gate passes |137current contexts individually reviewed(31false positives/106accepted risks);350unique normalized exact referenced-source reuses. Detector severities are not confirmed exploits or independent approval. |

The analyzer's detector-present process exit was4294967295, not an empty clean
report. Its JSON explicitly reports success with no analyzer error. Strict review
covers all487fingerprints and current source/toolchain hashes. The CI/checker
default points to this [full record](static-review.json), retaining older479pins.
The source-context review and execution receipt are included as separate artifacts.

## Current-test maintenance supplement

The later user question expanded the test-consumer review. Production source,
normal43/static487 and actual source-wire records remain unchanged:

-6distinct Python methods pass at their final stages; historical schema8 fixtures
 stay explicit and current templates exercise the actual schema13validator.
-24distinct Solidity methods pass, including all7real-authority preparation
 cases, metadata/full1ETH payouts, terminal royalties,1000NFTV8 import, maximum
 domains/prefunds, dormant activation after handoff and closed-sale inventory.
 The5Combined gas methods were rerun with actual ProtocolPolicy cooled; these
 supersede the earlier5and are not another5distinct methods.
-4additional portfolio/dynamic-accounting EVM scenarios pass after real opening,
 synchronization and nonzero-rights checks.
-6collection/stateful contexts accepted:5exact unchanged financial/model contexts
 plus the corrected benchmark. The invariant runs32sequences/4096calls with zero
 unexpected reverts and funded final drains. Full1000NFTpayouts, explicit zero
 cohort and idle-limit rejection/refund preservation are checked.

The mixed-claim benchmark retains12M absolute limits; its old O(1) index-based
comparison was inappropriate for exact tree accounting. Measured2→1000cases
both claim a weight1NFT, but ticket prefixes differ3→1500; the1NFTcase hasweight2.
Mixed5-entry costs959445→1467033gas; selected32-entry shape5193487gas. The+100k
comparison remains for LP paths: activation3082367→3062296, LPclaim182996→183137,
rebalance2353042→2353325 and compound2161355→2161638. These are scoped local
synthetic benchmarks, not complete target maximum-state qualification.

Combined cold cases measure healthy activation6635250, indexedactivation7716244,
growth4259039 and indexedgrowth5686743gas.16full-budget faults reject12M atomically
at10921854gas; a separately labeled24M LOCAL call succeeds at21913087gas.
Neither that probe nor smaller healthy cohorts qualifies1000NFT×16/64currencies
or changes a running API/provider limit. Healthy pending work may be synchronized
currency-by-currency before re-simulation; pathological assets still need review.

See [maintenance map](TEST_MAINTENANCE.md) and supplement JSON artifacts. Retain
original pre-fix failures, compilation/interruption/empty selections, stale
authority initialization and benchmark/model corrections. No source safeguard,
12M ceiling or financial invariant was relaxed to make tests green. Only the
misleading relative royalty-cost assertion was removed; true LP-path bounds stay.


## Local gas and deployment sizes

Recorded-slot-cooled local fixture measurements:

| Measurement | Gas |
| --- | ---: |
| Rotated cold full royalty synchronization |747,393 |
| Activation including healthy worst optional synchronization |904,342 |
| Actual Access/controller inner CREATE/construction |21,756,812 |
| Actual NFT inner CREATE/construction |13,962,340 |

These are NOT complete wallet deployment receipts, Robinhood fees or actual
target provider acceptance. Constructor values omit transaction intrinsic and
calldata overhead; maximum population/currency/canonical paths still need review.
Fresh optional-sync forwarding ceiling is1m; it is not a fixed charge. A32-entry
claim-count bound is not a universal gas guarantee.

Normal runtime margins: Royalty52, Migration39, Budget237, Balancer360,
Handoff448, VaultCanonical511, Vault635bytes. Factory runtime1182bytes; its
fixed stored ledger creation payload is25,522bytes with source-bound hash
`0x4a520b4af1c8ded6fe2539ec7f3ec4f6d9a1c7fbdd710a53ccffd3412bfce831`.
Use the exact reviewed compiler/source bytes and payload; never adopt a measured
runtime/hash automatically or treat another optimizer/profile as this build.

## Retained negative and intermediate evidence

- Eight old-source royalty3 reproductions confirm stranded raw units and receipt
  segmentation behavior. The initial exact candidate's integral fairness failure
  prompted GCD normalization; it was not dismissed as a test error.
- Old fractional-carry expectations were adapted only after the authorized
  rounding policy changed. Wrong cursor/expectRevert fixtures and the accidental
  zero-method regex selection remain recorded; empty selection is not a pass.
- Source changes during several otherwise green contract stages were marked
  drifted/intermediate. Final25and6successes are separately pinned.
- Normal builds that exceeded factory, royalty or coordinator size are retained.
  They prompted fixed-code storage, bitmap/send deduplication and the read-only
  companion split. No size gate was relaxed.
- A real-source fixture caught the zero-based wire mismatch and zero eligible
  canonical telemetry bug that synthetic tests missed. Stale fixture provenance
  failed rather than being relabeled; regenerated exact-source bytes are committed.
- Profile validation exposed missing revision-parameter propagation; corrected.
  Expansion tests first lacked a required buyback fixture value; the financial
  guard stayed intact. A transient indentation error was corrected before final
  profile/affected checks. CLI8→13expectations were fixed without weakening guards.
- Website's initial failures and timestamp fixtures remain external. The final
  source-helper cohort passes; no live browser/server or public signing follows.

All raw/failed stages stay under the external local evidence root documented in
[evidence](evidence.json). Selected durable summaries/logs are included here.
After the backend run, event-schema CRLF was restored with exact normalized-byte
and JSON equality; the223test pins retain their original tested bytes. Current
documentation newline conventions were likewise restored without semantic
changes, then the generated function/operator/Todo checks passed again.
Historical reports remain byte-preserved; their counts/source scopes are not
added to current tests. The four protected dirty files and all other website
tracked boundaries are checked against the initial snapshot.

## Reuse and release limits

Unchanged indexer anchor/startup/WAL, keeper deadline/reset scheduling, and
manual safeguard source contexts reuse their original exact evidence. This
does not rerun their93/100/etc historical suites. LP split/share/math source is
unchanged by the royalty correction; it is not newly qualified for every market.

No deployment, current-pool fork/real funds, source8 service/site configuration,
Anvil reset, journal/nonce adoption, public signer extension or heartbeat restart.
Actual OpenSea integration/payment/currency timing, routes/dual feeds/VRF,
authorities, target maximum-state gas/economics, storage/restore/history workloads
and independent audit/remediation remain open under the [sole Todo](../../TODO.md).
