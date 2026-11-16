# Verification — real-market refresh, 16 November 2026

This verifies a bounded captured observation and its offline interpretation.
It does not verify a deployed PoPL transaction or approve a dependency.

## Exact scopes

| Stage | Actual work | Result and boundary |
| --- | --- | --- |
| Initial new collector checks | Four mocked transport methods | Three pass; pacing method exposes Windows coarse monotonic-clock resolution. Original source and failure retained. |
| Clock correction | High-resolution clock; affected method only | Intermediate fixture timing-margin error retained; corrected affected method passes. Three unchanged methods are not rerun. No production tool changes. |
| Primary capture | 33 serialized public reads; six quotes; 64.382494s | 28 results, five application RPC errors, canonical hash closure, no HTTP refusal/retry. Frozen collector SHA256 `f0cd1487229df7807765bca1997dfc8b013b8407709c9107cdd9ea9e432241e5`. |
| Recent discovery | Three public reads; 4.347493s | Exact pair/core `113296580..115708674`, no Initialize events; before/after anchor matches. |
| Inventory gap closure | Three public reads; 4.369041s | Exact pair/core `110324512..113296579`, no Initialize events; before/after retained November13 header matches. |
| Offline analysis | Exact integer/rational calculations; no network | 95 known PoolKeys, packed states, directional fees, nominal-size quote inputs, output/error interpretation, source ages/spread and unapproved candidate configuration. |
| Independent review | Separately calculated against original wire bytes and historical provenance | Fresh answers/math and contiguous requested discovery ranges agree. Provider completeness, global market coverage and finality remain unproven. |
| Offline verifier hardening | Four new adversarial methods, demonstrated against initial and corrected checker sources | Truncated quotes, detached quote error, spoofed embedded API3 observation and spoofed anchor fail closed at the corrected source. Exact six directions, keys, feed/implementation observations and wire/summary relationships are bound. No protocol code changes. |

These 39 requests are **not** 39 passed tests. There are 34 successful JSON-RPC
results and five retained application-level reverts. Six quotes overlap the
33-request primary phase. Discovery phases each add only one filtered log query
and two header reads. Earlier 696 quote calls, the November13 provider checks and
previous local/EVM suites retain their own source scopes and are not added here.

There are eight unique new report-helper checks: four transport and four
verifier methods, with the separate source stages above. The valid final bundle
is also checked by the corrected verifier; that is an artifact check, not another
feature or an unchanged suite rerun.

The newly written offline evidence checker was independently challenged before
publication. Its initial positive pass did not prove rejection of truncated or
detached quote summaries. The original checker is retained; current admission
must bind the complete six-quote set, PoolKeys, results, source observations and
anchor to original wire records. New focused rejection checks and their exact
source stages are retained separately in the evidence bundle. A package hash is
an integrity reference, not proof of authentic provider answers or market truth.

## Reproduce without network or compilation

From this repository's root, using Python 3.11 or later:

```text
python -I -B reports/real-market-refresh-20261116/verify.py
```

The checker reads the bounded [evidence.zip](evidence.zip), requires the pinned
repository Keccak helper and verifies recorded request/response hashes and
semantic relationships. It sends no RPC request, compiles no contract and runs
no old test suite. It does not extract or execute archived collector code. Raw
responses, collector/analyzer source, transport stages, previous provenance and
independent calculations remain in the archive. Use the accompanying
[evidence manifest](EVIDENCE_MANIFEST.json) and [producer stages](PRODUCER_STAGE.json)
for exact bytes/source hashes. [RESULTS.json](RESULTS.json) is a readable export;
the archive is the replay input. Null admission fields are intentional.

The frozen archive has 90 members (89 manifest-hashed files), 289,771 bytes and
SHA256 `ec687b4d1e3bc6cde830dba06620a9a6871ee5628c9f7337bac38ea025867d1e`.
The current verifier SHA256 is
`c4d3ae7aba1a0bed3f250b9f87b6366d6cbfa8cd75fffb7f4555691630477233`.
The [final valid-bundle check](VERIFICATION.json) passes. A separate
[independent package review](INDEPENDENT_PACKAGE_REVIEW.json) checks the frozen
archive, all 39 original responses and standalone snapshots without another
verifier run. It is a sidecar pinning that archive, not an extra archived member.

## Preservation and publication

Owning docs and the sole Todo are updated; task IDs/statuses are preserved.
The current operator procedure separates source discovery, publication ownership,
admission review and actual operating adoption. No callable contract, parameter,
permission or behavior changes, so ABI/function tables need no regeneration.

Prepublication checks compare all 61 production Solidity files, eight prior
deployment preparation/rehearsal files and four unrelated dirty files against
the task-start hashes. They verify generated Todo consistency, changed document
targets/anchors, JSON/Python syntax and exact owned publication scope. No old
compiler, static analysis, EVM, browser, full RPC qualification or unchanged
test suite is rerun.

Existing Anvil8902, NFTs/LP/balances, journals, dist overlays, shared Anvil-only
signer, both public null configurations, websites/services and user-paused
heartbeat remain untouched. No public transaction, deployment, sealing, new
provider adoption or final release sign-off is authorized by this evidence.
