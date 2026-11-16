# Offline checkpoint prefix import — 16 November 2026

Implemented the explicitly authorized offline importer. It extends a reviewed
original exact-accounting checkpoint2 or strictly shorter checkpoint3 graph into
a NEW standard checkpoint3 candidate, without replaying the already reviewed
earnings prefix. The full raw 24-hour window, exact accounting and existing
safeguards/limits remain. **No artifact, service or deployment is approved.**

Baseline: `3c180f2f5a0fe3743b87184250dd2d0f96d09881` on main. The earlier
[checkpoint3 report](../lineage-checkpoints-20261116/REVIEW.md) retains its exact
source/evidence scope. Its then-open prefix-import capability is addressed here;
actual lifetime archival and operation remain open.

| Item | Result |
| --- | --- |
| Missing extended-graph producer | New [module](../../frontend_api/earnings_checkpoint_import.py) and [CLI](../../scripts/import-earnings-checkpoint.py) prepare an explicit input-digest-bound candidate and separate review. Same-graph advancement stays with the old builder. |
| Compatibility risk from editing source-pinned readers | All **14 semantic source files** remain byte-identical. Existing strict format2/3 admission and the existing standard3 builder/consumer perform validation. No source override or historical-state relabeling. |
| Exact account/epoch continuity | Restore the original raw state once, retain completed local payout/conversion books separately and replay subsequent authenticated raw handoffs/events. All appended epochs must retain native ETH/the fixed ZZZ, even when output cursor precedes them. |
| Review-file binding gap found during implementation | Publication now binds exact sidecar shape, false readiness flags, semantic/producer pins, target graph/count/anchors, full-day deadline and appended handoff identities/order to candidate bytes. New adversarial publication checks cover this. |
| Long-term deployment adoption | Still separate: operator approves input provenance and new output, then explicitly authorizes the matching API configuration/restart. No automatic adoption, pruning, signing or journal mutation. |

## Validation and boundaries

The importer requires a strictly shorter ordered matching graph. It reads the
prefix through the unchanged strict decoder under a nonmutating old-graph view,
then authenticates the full target graph, both directions of each handoff and
actual canonical receipt/commitment/anchor identities. The old graph's current
tail can acquire its reviewed retirement edge; this does not permit different
code, token meanings or arbitrary historical peers. Existing rules allow later
reviewed royalty descriptors on that then-current tail; earlier retired identities
remain exact. Actual later admission and unchanged existing meanings are checked.

The imported cursor must be inside its authenticated operating epoch, before
retirement, at/after deployment, with the correct original namespace/predecessor
and no active preparation. Output cannot move backward. The ordinary builder
checks every NFT and exact account state at the output operating cursor, preserves
raw LP pending/high/low/direct books and royalty tickets, and creates ordinary3
bytes. The standard consumer then validates the output before preparation returns.
Retired live-royalty backing views are not substituted for completed local books.

Input SHA, producer/semantic sources and graph are checked again before return.
The new producer hashes live in a **separate review**, so adding this tool does
not invalidate compatible approved checkpoint2/3 consumer pins. Incompatible old
sources still reject; editing stored hashes is never an adoption method.

The existing 86,400-chain-second age gate and complete raw rolling-day suffix
are unchanged. A candidate may use a historical operating cursor before a recent
handoff. Its earliest serving timestamp is explicit; producing a too-recent
candidate does not make it usable early. Claims/conversions/imports remain
distinct from income, and current-owner/collection/current-holdings reporting
retains the existing public format and current-price semantics.

One shared offline work budget covers construction, prefix load, proofs, replay,
strict output admission and publication. Defaults remain60 seconds/4096 logical
calls/8192 posts; existing offline maxima and any stronger outer budget remain.
API budgets, up-to-eight-predecessor graph, combined event limit, tagged-codec
and32MiB checkpoint bounds stay. The new review is separately bounded to1MiB.
These are bounded work checks, not proof that every filesystem/provider call
can be interrupted instantly or that actual maximum state is qualified.

Publication is exclusive and flushed for each file, review first then candidate;
**the pair is not jointly atomic**. A failure can leave one or both unapproved
files. Errors instruct the operator to inspect/preserve both paths and retry
with fresh names. Existing input/output paths are never overwritten or deleted.
Both successful digests remain unapproved. No credential or RPC configuration
contents are included in the public sidecar.

## Verification

**46 distinct new methods pass across recorded source stages:**20 import methods
and26 CLI/publication methods. The initial fixture/harness failures and correction
stages are retained, not counted as additional successes. No unchanged test
method, Solidity/compiler/static suite, browser suite or public RPC probe was run.
The existing real SQLite/replay/codec/readers are exercised with synthetic
lifecycle/getter/provider truths; this is not a deployed V10 or live-host rehearsal.

Coverage includes original2 and shorter3 imports, nonzero raw allocation phases,
full-replay equality for collection/NFT/wallet, whole-unit conservation, full24h
through recent handoffs, claims/conversions/transfers, late currency admission,
wrong profiles/runtime/graph/cursors, corrupt receipt/root/reorg/archive evidence,
shared limits, immutable inputs and exclusive/partial output behavior. CLI cases
also verify required inputs, exact budget flow, ambiguity rejection and sanitized
errors. See [verification](VERIFICATION.md) and the [evidence inventory](EVIDENCE.json).

The publication-only hardening was applied after the first19 import methods.
Their critical importer/class/function bodies are cryptographically/AST-bound
as unchanged; they were not rerun. The later-descriptor method and all26
CLI/publication methods use the final producer source. Independent internal
source reviews found no additional concrete accounting/cursor defect; they are
not an independent release audit.

Hash checks preserve all61 Solidity sources,14 semantic source files,6191 old
report files and the four unrelated dirty files. Websites, shared signer/public
null configurations, Anvil state, journals, services and user-paused heartbeat
were not acted on. Source publication is not environment adoption.

## Operator impact and remaining work

Use the [exact command and recovery procedure](../../docs/EARNINGS_CHECKPOINTS.md#import-a-reviewed-prefix-into-an-extended-graph)
and the [single operator manual](../../docs/OPERATOR_MANUAL.md#prepare-and-rotate-an-earnings-checkpoint).
The reviewed prefix digest is a local artifact SHA-256, **not an on-chain
`reviewHash`, `custodyHash` or `portfolioHash`**. No operator wallet call is needed.

The [financial-history task](../../TODO.md#task-financial-history) stays In progress.
Actual archive completeness/canonicality, provider latency/capacity, expanded
currency/1000-NFT maximum-state operation, long-lived storage/restore, other
full-history consumers and authorized service adoption remain unqualified.
Source-semantic upgrades still require reviewed rebuild/compatible migration
work; this importer accepts no arbitrary prior-source codec. A digest plus
matching RPC reconciliation is not consensus or historical log-completeness proof.
Production dependencies and independent audit/remediation remain release gates.
