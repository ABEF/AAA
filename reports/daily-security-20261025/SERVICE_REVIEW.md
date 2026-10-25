# October25 service consistency review

Internal source review of the Paris-day changes beginning2026-10-24T22:00Z,
including current keeper state/recovery, indexer ingestion, inventory/profile
boundaries, RPC observations and relevant operator instructions. Source review is
not exhaustive vulnerability absence, qualified provider operation or an external
audit. No existing chain, service, database, wallet or monitor was operated.

## P2 fixed: malformed log identity could poison retained history

`indexer/monitor.py` previously checked the confirmed block/emitter but only
lowercased the transaction hash and parsed log quantities with `int`. It could
persist short/zero transaction hashes, noncanonical or negative log indexes,
oversized unknown events, duplicate block/log positions under different transaction
hashes, or one transaction reported in different blocks. The history consumer
would later reject these rows, making earnings/history unavailable after the
cursor had already advanced. This is a data-integrity/availability defect; no
on-chain claim or custody bypass was established.

The indexer now validates complete nonzero32-byte hashes, canonical SQLite-bounded
quantities, exact nonremoved status, configured emitter, at most four fixed topics,
byte-aligned data and complete raw logs within the consumer's131,072-character
bound. Known malformed event layouts fail with sanitized `invalid_log`; conflicting
identities use `duplicate_log`. Anonymous/unknown wellformed logs retain their full
raw representation. Each incoming transaction has one recorded block; an indexed
LIMIT-1 lookup checks retained transaction history before any insertion. A short
IMMEDIATE transaction rechecks the cursor and publishes the complete block/log
batch atomically. No schema change, deletion, automatic reset or rescan is added.

Before-fix negative controls reproduce the rejected/poisoned cases with stored
prefix blocks and a saved cursor. Final cases verify the prefix, cursor and owner
projection remain unchanged on failure. Existing genuine bounded-reorg recovery,
resumption and block ingestion assertions remain active.

## P3 clarified: keeper recovery profile documentation

The recovery introduction now states that new LP-only deployments require the
separate `fee_intake_version: 1`, actual Fees address, exact runtime pin and current
version getter. Native accounting2 alone is insufficient. Existing profile0
journals retain original pending transaction identity; no version edit or copied
current example constitutes an upgrade. This changes documentation only; keeper
runtime behavior and installed services are unchanged.

## Reviewed boundaries retained

- Pending keeper intents retain signing-time gas/cap/L1 review, exact sender,
  nonce/target/calldata/value/chain binding and canonical receipt checkpoints.
  Ambiguous submissions remain pending; no automatic resend is introduced.
- New keeper work requires current profile/runtime checks, canonical operating
  state and original limits. Receipt recovery precedes new scheduling. Current
  fee1 rejects removed creator-sync jobs; historical pending profiles stay separate.
- Current OpenSea primary mint remains hardblocked in release qualification:
  self-declared manifest evidence cannot supply a missing recipient/payment path.
  Actual VRF, feeds/routes, providers, authorities and operating approval remain open.
- The read-only observer does not sign or approve release. Runtime/parent pins,
  approved inventory and actual observations remain separate. Historical data is
  not relabelled as current provider qualification.
- Lineage predecessor configuration inherits the current fee profile. Cross-codec
  old-fee0/nativeV2 to current fee1/LP-onlyV3 imports are already rejected by
  `CanonicalHandoff.prepareImport` schema equality. This review does not widen
  that unsupported migration or alter authenticated same-schema lineage checks.

## Evidence

[Before-fix record](indexer-log-poison-before.json) retains the original failures
and exact source bindings. The eight new methods include negative subcases; their
multiple failure/error diagnostics are not extra distinct tests or passes.
[Final execution](indexer-log-poison-after.json): **35/35 methods pass once**,
comprising eight new provenance methods and27 existing affected Indexer methods.
Isolated SQLite/mock-chain only; no real RPC, database migration, service rehearsal
or public action. Unchanged broader keeper/frontend/contract suites were not rerun.

Payload validation cannot prove a provider returned every real log. Independent
history comparison, actual RPC/archive qualification and final operational review
remain release gates. Existing already-poisoned historical databases are preserved
for operator review; this patch does not silently rewrite them.
