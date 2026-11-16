# Reviewed earnings checkpoints

This optional backend profile serves collection, NFT and wallet-chunk earnings
from an immutable reviewed checkpoint plus raw recent events. It changes no
contracts, funds, reward rights, signer or running service. Default configuration
still uses full replay. Checkpoint1 supports explicit historical accounting6/
custody5/fee-intake1. Explicit checkpoint2 supports fresh accounting7/LP-allocation1/
custody5/fee-intake1 with original-currency royalty4. Schemas1/2 retain their
original-deployment-only scope. New **checkpoint3** supports complete configured
accounting7/custody5/royalty4 same-chain lineages; it never reinterprets1/2 bytes.
Public deployments remain blocked.

The builder chooses the format from the authenticated deployment/lineage
profile, never from a caller's desired label. Accounting7 rejects checkpoint1 before restoring
state; accounting6 likewise rejects checkpoint2. There is no cross-accounting artifact conversion, edited source-hash adoption,
pruning or live rollout. The separate explicit offline importer below can use a
compatible exact2/shorter3 prefix to build a new standard3 artifact. Changes to
pinned semantic sources require independently reviewed rebuild/re-pin, including
previously built format1 files; adding this separate importer changes none.

Accounting7 backend mint profile1/default authenticates canonicalV9; explicit2
authenticates mint2/canonicalV10 and its additional mint contract pins. Original
deployments use checkpoint2; a configured exact-accounting lineage uses3 under
each peer's exact source/deployment identity.
This is not V9-to-V10 artifact adoption: changed source, contract pins or deployment
requires reviewed rebuild/re-pin. The checkpoint is an earnings seed, not a backup
or restoration codec for SeaDrop phase quotas and original-mint recipient books.

## What is authenticated

The operator pins the artifact's SHA-256 through the reviewed API configuration.
The reader verifies that exact file, semantic source hashes, deployment/helper/
asset identities and canonical cutoff. It still reconciles current indexes,
membership, shares, cohorts and NFT entitlement/claims. A checksum authenticates
bytes relative to that configuration; it does not prove honest ingestion or
every historical payment. Never approve a candidate just because its own hash
matches. Preserve independent raw-provider/history-audit evidence and raw SQLite.

The file contains public contract identities and exact token accounting, not
RPC URLs, private configuration paths, keys, USD estimates or nonce journals.
The API loads immutable bytes; each request restores separate maps. No HTTP
request builds, approves, edits or rotates checkpoints.
An existing reader retains its already validated bytes; it never hot-reloads a
changed path. New readers/restarts validate the file again. Stop/restart is the
deliberate configuration cutover, not editing or deleting the file in place.

## Exact retained accounting

The checkpoint carries ownership, cumulative claims/conversions, minted order,
shares/supplies, equal membership, rarity weights, royalty eligibility prefixes,
fee dust, LP reward indexes and complete earnings. Royalty4 on that explicit6 profile also retains
whole-unit allocation books, zero-based internal ticket offsets and raw currency
cursors, with explicit one-based source adapters. Reporting may scale whole
royalty earnings internally, but this creates no royalty fractional liability.
Checkpoint1's historical scaled LP totals preserve their carried fractions.
Checkpoint2 additionally stores the exact ETH/fixed-ZZZ pair, immutable mint
ordinals, all individual and collective tree weights, raw pending units,
high/low allocation phase, outstanding units, direct credits and orphaned units.
It validates shares/membership against the tree geometry, every assigned whole
unit against outstanding backing, and whole-unit earnings. It never settles or
flattens the saved phase. Each restored request owns independent tree/maps.
The builder checks every minted NFT's owner, ordinal, shares, royalty tickets,
exact LP components and claimed/converted/earned reconciliation at the operating
checkpoint cursor. With schema3, paid amounts include every completed local
epoch exactly once; retired sources retain aggregate book reconciliation but
are not queried through royalty pending/claimable views after backing moved. Those checks do not prove complete logs
or independently reveal internal phase in an operating contract; phase remains
derived from the complete reviewed event history. Claims,
conversions, contributions, compounding principal and imports are not new income.
The80/10/5/5 split and quarantine rules do not change. ETH/ZZZ remain the only
principal inputs; separate royalty currencies retain their own admission.

A served checkpoint must be **at least86400 chain-timestamp seconds older than
the requested snapshot**. This is inclusive: its timestamp may equal the day's
exclusive lower boundary. The entire actual24-hour window is then replayed from
raw suffix logs. No daily buckets, interpolated history or guessed timing replace
events. Current USD prices are applied at the final confirmed request block.

## Checkpoint3 across replacement contracts

An **epoch** here is one canonical NFT/reward deployment, not a pool or rebalance.
Schema3 binds the complete ordered graph (up to eight predecessors), each peer's
mint/execution profile, exact code/emitters/assets, history identity and retirement
transaction. The existing one-million combined configured event bound,32MiB
artifact limit and tagged-codec/work limits remain; no request budget is raised.

The artifact has one cumulative exact accounting state at an operating full-block
cursor in any epoch, plus separate local ownership/payout/conversion histories for
completed earlier epochs. It never sums cumulative earnings models. Raw LP trees,
pending units/high-low phase/direct credits and royalty tickets/cursors remain.
One restore at the cursor is followed by raw events, including all later authentic
handoffs. Import/backing/claim/conversion is not new income.

Choose `--block` by **canonical activation windows**, not by successor deployment
date: replacement contracts can be predeployed. A full block containing a handoff
belongs to the final operating destination at that block end; a frozen/preparing
cursor rejects. A suitable block may be in the original or a middle deployment.
The builder authenticates the full graph at the confirmed current head, then
replays only as far as that historical operating cursor. It validates all NFTs
there and all completed epoch books. Retired royalty pending/claimable views may
revert after their backing was forwarded; lifetime paid totals instead reconcile
against the operating cursor's actual remaining rights.

For a recent replacement, choose an earlier-epoch cursor at least86,400seconds
before the oldest snapshot to serve. The raw suffix then spans the whole rolling
day across the handoff. A cursor after the recent handoff can still be built, but
serving rejects until it ages; no stored day total or silent fallback fills the gap.

Use the same unsigned, read-only command after reviewing the complete input:

```sh
python scripts/build-earnings-checkpoint.py --config /secure/reviewed-lineage-api.json --block ELIGIBLE_BLOCK_NUMBER --output /archive/new-lineage-checkpoint.json
```

Replace the block/path placeholders. `--max-seconds/--max-calls/--max-posts` remain
explicit offline budgets; no gas, transaction or signing input exists. The builder
may use the reviewed descriptor **superset** for a historical cursor before a later
royalty-currency admission. It validates only currencies actually admitted then;
an unknown admitted currency, bad metadata or wrong ETH/fixed-ZZZ pair still fails.
Ordinary API reads and transaction preparation keep exact descriptor equality.

Independently compare full replay with the candidate for collection/NFT/wallet
results, transfers, prior payouts/conversions, dormant/new activations, exact units
and complete24-hour suffix. Review/re-pin through the existing `path`/`sha256`
object, then separately authorize the normal stop/restart procedure. This is a
reporting artifact digest, not an on-chain `reviewHash`. Public output fields,
current-price USD semantics and NFT ownership/economic rights are unchanged.

Each read still authenticates every peer, both handoff directions, receipts,
commitments, runtime/creation/retirement/cursor anchors and raw suffix. Completed
prefixes use reviewed local history seeds, not unauthenticated totals; raw/WAL and
prefix duplicate-transaction checks remain. Immutable per-section bytes restore
fresh maps per request; history-only reads do not decode the entire LP tree state.

Same-graph advancement may move from an earlier to a later epoch cursor; keep the
old approved artifact in the input and choose a later block. `previous_sha256`
records provenance only. A **new subsequent handoff changes the graph** and needs
a reviewed new candidate. Use a complete raw rebuild, or the explicit offline
prefix-import procedure below for a compatible original2/shorter3 artifact.
Existing raw/event/work bounds remain; this is not unlimited lifetime history.
The financial-history task remains in progress.

## Import a reviewed prefix into an extended graph

This **offline backend tool** accepts a separately approved original checkpoint2
or strictly shorter-graph checkpoint3. It is not an HTTP operation, contract
import or same-graph advancement. It produces a NEW standard checkpoint3 plus a
producer-review file; it never edits or installs the prefix. Use the ordinary
builder above for same-graph advancement.

1. Preserve the approved input bytes, approval record, exact digest, old configuration
   and consistent raw/WAL backups. Review the complete target lineage, profiles,
   exact runtimes/assets/history anchors and appended retirement transactions.
   The target configuration must contain **no `earnings_history.checkpoint` key**,
   even a null one; the input prefix is supplied separately to prevent ambiguity.
2. Check the input still matches the installed semantic source hashes. The existing
   strict format2/3 readers validate it unchanged. Format1, incompatible sources,
   reordered/foreign/full graphs, changed identities and invalid cursors reject.
   A then-current prefix tail may acquire only its authenticated retirement edge;
   it is not permission to rotate code or reinterpret old accounting. Existing
   reviewed royalty-descriptor extension rules remain, and every target epoch
   must prove the exact same native ETH/fixed-ZZZ principal pair.
3. Choose a confirmed operating full-block `--block` at or after the imported cursor.
   To serve a complete day, choose it at least86,400 chain seconds before the oldest
   intended request snapshot. A historical cursor before a recent handoff is valid.
   The tool authenticates all appended handoffs even if the candidate ends earlier.
4. Use two **new distinct paths** in existing directories:

```sh
python scripts/import-earnings-checkpoint.py --config /secure/extended-lineage-api.json --prefix /archive/approved-prefix.json --prefix-sha256 REVIEWED_64_LOWERCASE_HEX_DIGEST --block ELIGIBLE_BLOCK_NUMBER --output /archive/extended-candidate.json --review-output /archive/extended-import-review.json
```

Replace every placeholder. The digest is the approved SHA-256 of the exact prefix
bytes, without `0x`; it is **not** `reviewHash`, `custodyHash` or an on-chain input.
No key, gas budget, wallet, contract call or signing input is needed. Offline
`--max-seconds/--max-calls/--max-posts` keep the existing60/4096/8192 defaults and
3600/65536/65536 maxima; nested work cannot reset an outer budget. API limits,
32MiB artifact/codec bounds, graph and event limits remain unchanged. The review
sidecar has a separate1MiB ceiling; it does not increase the checkpoint limit.
5. Review both artifacts. The standard3 candidate binds unchanged consumer semantic
   sources and `previous_sha256` to the input. The separate sidecar pins the NEW
   importer/CLI, input/output digests and semantic sources, target graph/config hash,
   cursor, canonical snapshot, appended handoff commitments and earliest serving
   timestamp. All approval/install/submission flags remain false. Exact trees,
   pending/high-low phase/direct credits, royalty cohorts and completed local payout
   books are restored through the existing reader/builder, never totals-only copying.
6. Independently compare collection/NFT/current-holdings earnings with reviewed raw
   evidence, including claims/conversions/transfers and the **entire raw24-hour suffix**.
   Approve/re-pin the candidate's standard path/SHA only through the existing explicit
   adoption procedure. The sidecar is provenance, not a consensus/completeness proof
   or self-approval. Actual archive, provider and maximum-state operation still need
   qualification. Publishing this tool changes no service or configuration.

Publication creates the review first and candidate second, each flushed and
exclusively linked without overwriting existing files. The pair is **not jointly
atomic**. Interruption, collision or a reporting error can leave one or both
unapproved outputs. Inspect and preserve both paths; use fresh names for another
attempt. No input, partial output, raw database or old approved artifact is deleted.
The tool does not prune history, auto-rotate, edit source pins or raise request limits.

## Configure, build and review

All commands run from the repository root. They are read-only RPC/database work
plus creation of a new local candidate file; no wallet or governance key is used.
The examples below are templates: replace the paths and BLOCK_NUMBER first.

1. Review the exact schema2 API configuration and all seven emitters from NFT
   creation in every configured epoch. For checkpoint3 include the entire ordered
   predecessor list, exact peer profiles/runtime/history pins and retirement hashes. Use the actual archive RPC, raw database and pinned deployment.
   The initial config has no checkpoint key. Keep a WAL-consistent backup and
   retain previous raw/log/provider audit evidence. Do not reset the indexer.
2. Choose a confirmed historical BLOCK_NUMBER at a full block boundary. Its
   timestamp must precede the complete rolling day for the snapshots to be served.
   The builder verifies actual creation/runtime/module/ledger state at the cutoff,
   every minted NFT's owner/ordinal/shares/weight/claims and final canonicality/depth.
3. Prepare an exclusive candidate in an existing private directory:

```bash
python scripts/build-earnings-checkpoint.py --config /secure/api.json --block BLOCK_NUMBER --output /archive/earnings-BLOCK_NUMBER.json
```

Default offline limits are60seconds/4096logical RPC calls/8192HTTP posts. For a
reviewed larger build, explicit `--max-seconds`, `--max-calls`, `--max-posts` may
increase offline limits only, up to3600seconds and65536each. They never increase
HTTP request limits or an already stricter outer budget. Real provider latency,
archive behavior and maximal1000-NFT/asset workload remain qualification.

The output prints only a candidate digest and a nonapproval notice. Publication
uses a flushed temporary file and atomic exclusive hard-link creation; an
existing path is never replaced. Unsupported filesystems fail, without an unsafe
overwrite fallback. Preserve failed-attempt diagnostics and use a new output name.

4. Independently review source/identity/cutoff/raw completeness and reconciliation.
   Compare representative NFT, collection and current-holdings results with full
   replay while that is practical, including dormant NFTs, historical fractions
   or fresh whole-unit balances,
   prior claims/conversions, deferred royalties and transfers. Do not infer
   qualification from the candidate or a local fixture. Record approval through
   the existing review process, outside the public request path.
5. Add this optional object to the existing `earnings_history` configuration:

```json
"checkpoint": {
  "path": "/archive/earnings-BLOCK_NUMBER.json",
  "sha256": "REVIEWED_64_LOWERCASE_HEX_CHARACTERS_WITHOUT_0x"
}
```

These are placeholders. Hash/identity/source/shape mismatches fail closed. Adding
a checkpoint digest changes only reviewed backend configuration: it is not
reviewHash, custodyHash, portfolioHash or any on-chain function argument. Adding
a newly admitted royalty descriptor is supported only when every old descriptor
retains its meaning and the suffix proves actual admission. This does not admit
a new principal token. Changing old descriptor meaning requires reviewed rebuild.

6. Through a separately authorized rollout, stop/reconcile the API, preserve its
   original configuration, mount the approved artifact read-only, install exact
   reviewed source/config, restart and verify the three earnings endpoints. The
   response's epoch history records checkpoint block/hash/digest and actual suffix
   log count. Configuration identity changes, so clients must not combine chunks
   across a cutover. Existing source publication performs none of these actions.

## Advance, stop and recover

To advance, run the same builder with the previously approved checkpoint still
pinned in its input config and a later confirmed cutoff. It replays only the
bounded suffix, checks all NFTs again and writes a new exclusive candidate.
Review/re-pin/restart explicitly; the printed digest never approves itself.
`previous_sha256` records provenance, not a cryptographic completeness proof.
Keep the previous artifacts/configuration and raw archive.

| Incident | Required action |
| --- | --- |
| Wrong/missing/partial/hash-changed artifact | The profile rejects it; no zero/automatic fallback. Restore the approved bytes or deliberately remove the optional key and restart. Full replay can still exceed existing bounds. |
| Checkpoint less than24hours old, or requested block before it | Choose a suitable older reviewed checkpoint. Do not shorten the24-hour window or relabel its timestamp. |
| Reorg across checkpoint / changed indexed anchor | Stop using that artifact, retain its evidence, reconcile/backfill raw history and rebuild/review/re-pin. It is not repaired by restarting or changing a stored hash. |
| Suffix exceeds event/deadline/RPC limits | Advance through reviewed bounded stages. Never truncate events or raise public request caps to hide missing architecture. |
| Build interrupted or RPC/currency unavailable | No candidate is approved; the previous file/config stays intact. Restore dependencies and retry with a new output name. No claim/keeper nonce recovery is changed. |
| Source/profile upgrade invalidates semantic hashes | Rebuild through bounded raw stages with the new reviewed source and exact historical configs/archive state; then advance. A future compatible checkpoint migration needs its own reviewed codec/evidence. Never edit source hashes to relabel old state. |
| Canonical replacement or predecessors | Use explicit checkpoint3 for accounting7 lineages. An appended matching graph needs a new reviewed candidate: rebuild raw or import an approved compatible exact2/shorter3 prefix offline. Reordered/replaced graphs still reject; never edit identities/source hashes. Formats1/2 cannot be installed directly for lineage. |

Builder/readers preserve ordinary transaction provenance, including cross-prefix
transaction duplication through the existing SQLite primary-key index. Raw prefix
logs/creation header remain retained; no pruning/archive deletion is implemented.
For current accounting7 use the [offline recovery tool](HISTORY_RECOVERY.md) to snapshot/verify/restore all raw databases and exact checkpoint bytes. Never copy only a live main file without its committed WAL data. Historical6-only formats remain separately reviewed.

## Scope and remaining work

Checkpoints accelerate **earnings endpoints only**, including collection, NFT
and current-holdings wallet chunks. Other ownership, claim-history and preparation
paths keep their existing full-history behavior. Schema3 supports the configured
lineage; creation/retirement/cursor archive RPC and raw databases remain required.
The [offline recovery tool](HISTORY_RECOVERY.md) now implements current-profile snapshot backup, integrity verification and separate restore. It is not unattended rotation, archive pruning, automatic graph extension or
operating approval. Measure realistic long-history latency/memory/storage and safe rotation/
restore before hosting. The [financial-history task](../TODO.md#task-financial-history)
remains in progress. [Original evidence](../reports/earnings-checkpoints-20261104/REVIEW.md);
[lineage implementation](../reports/lineage-checkpoints-20261116/REVIEW.md);
[current offline import evidence](../reports/checkpoint-prefix-import-20261116/REVIEW.md).

## Controlled collection-scale evidence

The [1,000-NFT rehearsal](../reports/history-scale-rehearsal-20261116/REVIEW.md)
passes exact checkpoint2-to-3 prefix import, backup/verification/new-file restore,
independent whole-unit accounting and complete per-copy wallet coverage. It spans
three controlled deployments, 900 active/100 dormant NFTs, 7,757 raw logs and
346,800 chain seconds, including receipts before/at/after the day's exclusive
lower boundary. Nonzero high/low LP allocation phase is retained.

The original default 4,096-read refusal is retained; positive offline build/import
uses explicit existing 65,536-call settings under the unchanged 60-second deadline.
HTTP defaults, 16-NFT chunks, 32MiB checkpoint, codec/event/graph/currency bounds
and recovery defaults remain unchanged. The rehearsal uses synthetic chain,
getter and lifecycle observations; local timing excludes real-provider posts,
network latency and complete admission cost. It does not qualify maximum lifetime
history, all currencies/buckets/epochs, Unix/off-host restore or deployment.
See the [operator procedure](OPERATOR_MANUAL.md#collection-scale-history-rehearsal).
