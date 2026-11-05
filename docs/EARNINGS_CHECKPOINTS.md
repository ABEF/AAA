# Reviewed earnings checkpoints

This optional backend profile serves collection, NFT and wallet-chunk earnings
from an immutable reviewed checkpoint plus raw recent events. It changes no
contracts, funds, reward rights, signer or running service. Default configuration
still uses full replay. Fresh source supports explicit accounting6/custody5/
fee-intake1 only, without predecessor lineage. Public deployments remain blocked.

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
fee dust, LP reward indexes and complete earnings. Fresh royalty4 also retains
whole-unit allocation books, zero-based internal ticket offsets and raw currency
cursors, with explicit one-based source adapters. Reporting may scale whole
royalty earnings internally, but this creates no royalty fractional liability.
LP/historical scaled totals preserve their carried fractions. Claims,
conversions, contributions, compounding principal and imports are not new income.
The80/10/5/5 split and quarantine rules do not change. ETH/ZZZ remain the only
principal inputs; separate royalty currencies retain their own admission.

A served checkpoint must be **at least86400 chain-timestamp seconds older than
the requested snapshot**. This is inclusive: its timestamp may equal the day's
exclusive lower boundary. The entire actual24-hour window is then replayed from
raw suffix logs. No daily buckets, interpolated history or guessed timing replace
events. Current USD prices are applied at the final confirmed request block.

## Configure, build and review

All commands run from the repository root. They are read-only RPC/database work
plus creation of a new local candidate file; no wallet or governance key is used.
The examples below are templates: replace the paths and BLOCK_NUMBER first.

1. Review the exact schema2 API configuration and all seven emitters from NFT
   creation. Use the actual archive RPC, raw database and pinned deployment.
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
   replay while that is practical, including dormant NFTs, fractional balances,
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
| Canonical replacement or predecessors | This checkpoint profile rejects lineage. Preserve the existing explicit full-lineage reader. General lineage checkpoints require a separately reviewed extension. |

Builder/readers preserve ordinary transaction provenance, including cross-prefix
transaction duplication through the existing SQLite primary-key index. Raw prefix
logs/creation header remain retained; no pruning/archive deletion is implemented.
Restore from a consistent SQLite backup, not a copied live main file without WAL.

## Scope and remaining work

This first milestone accelerates **earnings endpoints only**. Other ownership,
claim-history and preparation paths keep their existing full-history behavior.
It still needs creation-block archive RPC reads. It is not an unattended mutable
read model, general lineage checkpoint, archive-retention solution or operating
approval. Measure realistic long-history latency/memory/storage and safe rotation/
restore before hosting. The [financial-history task](../TODO.md#task-financial-history)
remains in progress. [Source evidence](../reports/earnings-checkpoints-20261104/REVIEW.md).
