# Residual obsolete-code review

The review starts from `9213cae` and the current native ETH/fixed-ZZZ, LP-only,
source-chain custody architecture. Its objective is to remove unused executable
surface and misleading operating requirements, without deleting historical
records or changing economic rights. It is an internal review, not an independent
audit or approval to deploy.

## Removed and corrected

| Finding | Change and boundary |
| --- | --- |
| Registry WETH review records had no execution consumer after the native port. | Remove their tuple, three storage fields/getters, two governed setters, two private helpers, two events, unused WETH constant and four admin/wrapper interface declarations. Native wiring/runtime checks remain; actual converter wrapper policies are separate and unchanged. |
| The former creator-payment measurement tool was still an active module/CLI/test suite. | Retire `zzz_ops/revenue_share.py`, its dedicated tests and current run commands. Exact source/test/guide copies are archived. The hookless pool supplies actual LP fees; no creator agreement or measurement service is required. |
| The shipped keeper example silently selected legacy profiles and enabled creator synchronization. | Set explicit accounting2/fee-intake1, remove that job and use separate current-profile journal paths. The example remains dry-run with placeholders, no pins and no live review; it does not qualify or start a service. |
| An unused finality interface and import helper remained from broader handoff work. | Remove `IZZZCanonicalFinality` and `_canonicalBeginImport`; retain the sole test harness's equivalent state/cursor check. Production import uses its existing `_canonicalNext` checks. |
| NFT `_baseURI` override was unreachable because custom `tokenURI` directly supplies the stored artwork base to its renderer. | Remove only that override. URI validation, fixed artwork base, metadata availability/evolution and revealed traits remain. |
| Unused imported names and an orphaned removed-selector comment obscured current responsibilities. | Remove them. Compiler-pruned declarations are a maintainability improvement; no runtime saving is attributed to them. |
| Current docs/Todo still required creator inboxes, remote proofs or arbitrary new input assets. | Correct operating/security instructions to ETH/fixed ZZZ, actual funded local receipts, `recover(id,deadline)`, separately approved raw exit and the retained same-chain handoff. Deferred research is labelled historical, not a release prerequisite. |

The Registry runtime falls from **12,027 to 9,987 bytes**, saving **2,040 bytes**;
creation falls from 43,406 to 41,366 bytes under the same compiler settings. The
callable reference falls from 649 to **644 functions** across the same 31 concrete
contracts. Seven metadata-stripped runtime comparisons, including NFT, Vault and
both reward ledgers, remain identical; see [comparison](runtime-comparison.json).

This is a **fresh-deployment source change**. Registry `contributionPool` moves
from old slot5 to slot2 after removal of unused metadata slots. There is no
storage-compatible upgrade claim, bytecode patch or change to an existing Anvil
deployment. The pool/position ABI and canonical accounting schema are retained.

## Deliberately retained

| Looks old | Why it is still needed |
| --- | --- |
| Converter WETH configuration | Reviewed v3 LP/royalty conversions may receive and unwrap actual WETH. These checks guard real transfers and are unrelated to the removed Registry record. Native custody does not require WETH. |
| Historical fee profiles, event descriptors and pending journals | They preserve the meaning of older deployed fixtures, receipts and recovery evidence. Removing them would corrupt inspection/recovery rather than simplify the current runtime. |
| Position fields/status numbers and rejected bridge module IDs | They preserve stable decoding/import boundaries and explicitly reject retired capabilities. They are not an active bridge. |
| `nativeAsset` and `movePool` selectors | Historical routing clients still use the former; the latter is a documented alias with the same guarded authority. They are intentional compatibility, not abandoned implementations. |
| Two fixed ZZZ bindings | Source admission and custody snapshots actually consume them. A single canonical identity may simplify setup, but requires a deliberate versioned design that preserves raw-exit independence. Sealing currently requires a matching nonzero token. |
| Preparation notice for a not-yet-ready destination | This is cancellable planning/draining behavior, not a bridge. Freezing still requires a committed sealed same-chain importer. Narrowing that behavior is a separate product/lifecycle decision. |
| Same-chain whole-collection handoff and exact funded abort | They preserve ownership, traits, LP shares, unclaimed rewards and backing when replacing the collection. External principal exit alone does not provide this. |

## Evidence and remaining limits

See [verification](VERIFICATION.md), [ABI comparison](abi-comparison.json),
[Registry caller analysis](registry-wrapper-removal.json),
[service review](SERVICE_REVIEW.md) and [retirement manifests](retired-tools/).
Removed self-bookkeeping or creator-payment tests are archived, not counted as
current passes. Changes to acceptance wording preserve all existing task IDs and
statuses; external gates are not closed by deleting obsolete requirements.

The current constructor-size issue is **not fixed by this cleanup**: Access with
minimal nonempty role arrays still has only 29 bytes of initcode headroom. Actual
release arguments, current selected-pool fork qualification, real feeds/routes/VRF,
OpenSea primary mint, authorities, native operations and independent audit/remediation
remain open. Contracts currently enforce minimum $100 activation/$5 growth;
no stricter exact-$100 contract rule is introduced by this removal pass.

Governance and external custody remain trusted. No absence-of-vulnerabilities,
full fresh regression, green published CI or real-service qualification is claimed.
Website source/build/server, signer, existing local chain/NFT/LP/balances/journals
and paused monitoring are unchanged. No deployment or public transaction occurred.
