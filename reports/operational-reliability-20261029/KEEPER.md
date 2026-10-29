# Keeper operational reliability follow-up

Baseline: main `c2b82b09b5349f389fc58be5c3658a830c394c42`,2026-10-29.
This is a bounded implementation follow-up after the whole normal-operation
design review. It does not select early confirmation, a new compound policy,
harvest coalescing, new wallets/roles or any economic/operating configuration.
No installed service, signer, operating journal, Anvil, website, network provider,
deployment or public transaction was accessed or changed.

## Reproduced repairs

1. **Management JSON could contradict itself while reporting healthy.** Keeper
   runtime/config parsing already used strict shared JSON, but `keeper.ops`
   independently used ordinary `json.loads` for health, configuration and backup
   verification. A health file containing `blocked_actions:1` followed by
   `blocked_actions:0` passed. An unused NaN/Infinity/overflow number also passed.
   A snapshot with two conflicting `pending` values could pass its checksum
   because JSON silently selected the final value. CLI duplicate configuration
   reached its requested check. Required ops inputs now use shared `read_json`;
   duplicate/escaped-equivalent keys and nonfinite values fail before evaluation.
   Missing inputs still raise `FileNotFoundError`, valid results are unchanged,
   and files are neither repaired nor rewritten. This detects malformed input,
   not malicious replacement of otherwise well-formed local files.
   Independent review also found valid non-object JSON reaching object-only
   checks: arrays/null/numbers/bools/strings produced inconsistent AttributeError/
   TypeError diagnostics. CLI already caught those exceptions; it was not an
   uncaught CLI crash. The required-input helper now explicitly requires an
   object and raises a fixed `ValueError` before dispatch or schema access.
2. **A new head could precede its known confirmed checkpoint in time.**
   `_validate_checkpoint` checked height/depth and the exact old header but
   discarded the latest head timestamp. A higher-number head with timestamp below
   that confirmed anchor passed and could refresh health success. It now fails
   closed before subsequent work. Equal timestamps remain allowed; no extra RPC
   or journal field was introduced.
3. **A successor nonce receipt could move saved receipt history backwards.**
   `poll_pending` validated receipt/transaction identity, fee bounds and repeated
   canonical headers but did not compare the new nonce's inclusion height/time
   with the previous nonce's saved anchor. An internally contradictory transcript
   could be charged and advance nonce while replacing the anchor with an earlier
   block/time. New checks reject either retreat before any paid-state save. A
   legitimate successor in the same block with the same hash/timestamp remains
   valid. Existing inspection behavior without an old checkpoint is preserved;
   used live signers still require their original checkpoint under the existing
   rule. These detect contradictory provider evidence, not prove provider
   authenticity or that a real chain reorg occurred.

Changed files: `keeper/monitor.py`, `keeper/ops.py`, new
`tests_python/test_keeper_operational_integrity.py`, and the new module entry in
`scripts/run-keeper-tests.py`. Root owns the separate broad Python-runner/profile
work. No financial threshold, timer, route, lifecycle permission, callback,
compound/confirmation rule or journal schema changed.

## Source/body scope and non-findings

Reread the current normal-operation design and relevant bodies for checkpoint,
pending/fee recovery, metadata candidate/receipt save, submit guards, strict
journal parsing, ops health/preflight/snapshot commands, principal delivery and
existing fairness/clock/override regression fixtures. The earlier complete
operational body ledger remains separate source-scoped context; this follow-up
does not call itself a new whole-project audit.

Kept intentional boundaries: malformed metadata receipt snapshots preserve
pending/cost truth; an unrelated share/route observation failure does not invent
a market reset; canonical pending work remains first; no same-key manual nonce
or spend state is adopted automatically; compound/reference/idle triggers and
standalone harvest clocks remain exactly as described in the design report.
No additional confirmed queue-policy defect was established in this slice.

## Verification and evidence

`negative-before.log`:13 new selected methods produced12 failing
assertions/subcases across9 distinct methods. Four positive controls already
passed. This is not12 independent tests. It reproduces false management success,
false checkpoint-clock health success and backwards receipt recovery without
using a real signer or RPC.

`focused-final.json/log`:62 distinct methods pass (13 new,49 existing), no
failures, errors or skips and no source drift during execution. The selection
is explicit/deduplicated. It includes signed-fee policy, canonical/reorg/finality,
ops input/missing-file/backup exclusivity, original pending/nonce/spend recovery,
metadata snapshot/save/reorg behavior, checkpoint/confirmation incidents and
dedicated runner inventory. Methods and exact source/test pins are in the JSON;
they are not added to older overlapping runs.

After the independent object-shape follow-up, `shape-negative-before.log`
records15 failing subcases across three additional methods. `shape-final.json`
records23 affected read-only ops methods passing against final source, including
the20 overlapping ops methods and three new shape cases. The union at that stage was
**65 distinct methods:16 new and49 existing**, not62+23. At that stage, monitor/receipt code and
shared strict parser had not changed after the62-method campaign; affected ops
methods were rerun after the shape gate. Both receipts retain their own exact
source pins and scope, rather than representing a new65-method single run.

The standalone `new-after.log` repeats the13-method subset and is retained but
not added. An initial `apply_patch` failed a source-context string before any
edit; the corrected source patch was then applied. No gate/test assertion was
weakened to get a pass. Original production bytes are archived in
`monitor-before.py` and `ops-before.py`. `summary.json` records final identities,
pins and negative-control counts. `git diff --check` passed for owned changes.

Evidence is Windows/Python3.12.14 offline fixture execution. It does not qualify
Unix ownership/locking/systemd, actual receipt finality/provider behavior, source
rollout, gas economics, backups/alerts, or production operation. Source/health
hashes are not runtime attestation. The original four dirty files and all
operating state remain preserved.


## Final independent review: same-height receipt identity

The final combined-source review found a remaining receipt identity gap after
the entry checkpoint read. If RPC failover/reorg changed the canonical block at
the saved height, a successor receipt could match its own repeated inclusion
reads yet replace the prior saved block hash. An inconsistent timestamp at that
same height could also replace the saved timestamp. Monotonic height/time alone
did not reject either transcript. `poll_pending` now requires exact saved hash
and timestamp when a successor shares the saved checkpoint height. Legitimate
same-block successors remain valid; higher-height equal timestamps remain
permitted. No additional RPC, state field, journal rewrite or timing/economic
policy was introduced.

The two new negative controls allow the initial saved checkpoint validation to
succeed, then change only the later same-height inclusion header hash or time.
`same-height-before.json/log` records two failing methods out of three, with the
matching hash/time positive already passing. `same-height-final.json/log` records
all three passing; these cases verify unchanged in-memory and durable paid truth
on rejection and exact cost/nonce progression for the valid positive. The
pre-guard source is preserved as `monitor-before-same-height.py`.

`same-height-focused-final.json/log` is the final-source campaign: **67 distinct
methods pass,18 new and49 existing**, no failures/errors/skips or source drift.
Selected and executed identities match exactly. It reruns the affected prior
fee/recovery/checkpoint/metadata/management/inventory scopes after this shared
monitor guard. Earlier62/23 results and the three-case probe remain historical
evidence and are not added to67. `summary-before-same-height.json` preserves the
earlier65-method union; current `summary.json` pins the final67-method campaign
and current owned source hashes. No further test expansion was performed.

The final read-only tooling/doc review found no additional confirmed source
regression or sensitive logging issue in the reviewed full Python selector,
normal-profile validator, verification wrapper, keeper management commands or
recovery guidance. The exact Forge-version check now rejects prefix/devsuffix
controls; allowlisted metadata and fixed diagnostics retain the stated secret
handling boundary. This is bounded source review, not operating qualification.
