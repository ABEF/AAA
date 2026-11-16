# Metadata lifecycle2: presentation, notifications and recovery

Reviewed 16 November 2026 against baseline `dd242634b7dc4d3ead6d66f8a42c857da587cf15`.
This implements the agreed gaps in the [80-case matrix](../../docs/METADATA_LIFECYCLE.md).
The matrix is a scenario inventory, not80new tests or a guarantee covering every
possible failure. Exact executed evidence is in [verification](VERIFICATION.md).

## What changed

| Gap | Implemented source behavior |
| --- | --- |
| LP closure notification lag | O(1) whole-collection ERC-4906 events at exit start, each bucket close and final Ready. No unbounded NFT loop or wait for successful payout. |
| Unpaid versus paid principal | Metadata2 distinguishes awaiting allocation, allocated/not ready, payable, paid and exact zero. Successful isolated payout emits its NFT event; failed payout rolls back that event. |
| Dormant NFT after permanent exit | It remains Dormant with royalty activation false. Collection lifecycle separately reports permanent activation closure. It never acquires another NFT's principal or royalty rights. |
| Whole-collection replacement | Explicit preparing/frozen/importing/replaced/cancelled states, verified successor addresses and committed transition notifications. Temporary preparation is not permanent shutdown. |
| Unavailable valuation | Contract and integration source use a labelled Activated fallback for confirmed activated NFTs. Pending contributions retain their own confirmed image, or no image until confirmation if no earlier snapshot exists. |
| Lifecycle-only watcher changes | Optional `metadata_refresh.lifecycle_version:2` adds a price-free lifecycle fingerprint with exact renderer/runtime binding and a separate durable identity. Omission/0 keeps historical behavior. |

**LP exited remains separate from Dormant.** Exited activated NFTs keep Activated
art with a terminal label, transfers, old unclaimed rewards and future royalty
rights. There is no fifth image, new artwork, economic deactivation, royalty
weight reset or principal reopening.

## Architecture and safety boundary

Five production Solidity sources change: Access controller, Migration, NFT,
NFTMetadata and the existing NFTCanonical companion. The companion gains only
read-only lifecycle state/context methods. Its fixed parent/controller checks,
canonical writer/export/import record formats and storage remain. No production helper,
custody address, financial authority, executor, accounting profile or constructor input is
added. Accounting7, canonicalV10/schema17 and20callable helpers plus2inert data
children retain their existing meaning; these labels alone do not authenticate
new runtimes.

The existing NFT `policyMetadataChanged()` selector becomes a fixed-module
event-only hook for Policy, controller and Migration. It reads no price and
moves no funds. Governance EOAs use the existing permissionless individual/range
refresh functions rather than calling this internal hook. Financial callbacks,
allocation, paid flags and current-owner payouts keep their original ordering
and atomic rollback.

The lifecycle lens validates NFT/controller bindings, existing ownership,
canonical/exit ranges, coherent allocated/paid state and retired successor
identity. Historical assigned ETH/ZZZ remain assigned after payment; they are
**not unpaid balances**. Metadata deliberately avoids duplicating raw principal
amounts. Existing Migration/API reads remain authoritative for actual remaining
principal and receipts.

## Refresh and freshness

New JSON context identifies its read block/time, canonical state, replacement
preparation, permanent activation closure, collection exit phase and principal
allocation/payment status. Read block/time do not attest feed freshness or
marketplace cache age. Numeric NAV remains a current read snapshot; neither
watcher profile emits paid transactions for every numeric price movement.

The optional version2 watcher authenticates accounting7, renderer address/runtime,
NFT renderer binding and `METADATA_LIFECYCLE_VERSION()==2`. It compares the opaque
lifecycle fingerprint alongside existing reveal/tier/availability observations
and advances a checkpoint only after confirmed notification. The fingerprint
excludes numeric NAV, owner and snapshot time. It is not `reviewHash`, consent,
payment authority or uninterrupted market history.

Old journal identities are not silently adopted, downgraded or rewritten.
Pending recovery keeps its original identity/configuration. A new version needs
explicit review and rollout; publishing this source enables no running worker.
See [operations](../../docs/OPERATIONS.md) and the
[operator procedure](../../docs/OPERATOR_MANUAL.md#metadata-lifecycle-and-marketplace-recovery).

## Verification and engineering findings

The changed source has a fresh closed normal compiler/size record and full
source-bound internal static review. Historical exact source/finding reuse is
separate from individual current-context review. New lifecycle/notification and
differential-renderer checks, focused keeper cases and browser rendering checks
verify changed compositions; unchanged suites are not rerun. Compiler/harness
failures, earlier source stages and corrected attempts are retained rather than
presented as passes. See [verification](VERIFICATION.md),
[normal gates](build/normal-size-evidence.json),
[static review](static-review.json) and [evidence manifest](EVIDENCE_MANIFEST.json).

The normal build initially caught a stack issue and excessive renderer size.
Shared serialization and the existing read-only NFT companion resolve them
without changing compiler settings, size gates, authority or financial guards.
Other focused checks caught strict keeper identity typing and a pending-artwork
fallback interaction. Those corrections preserve legacy checkpoints and the
requirement that artwork follows confirmed LP execution.

## What remains open

- Actual supported-chain OpenSea onboarding, tokenURI read gas, content/root
  retention, queued retrieval, cache/media outcome and measured latency.
- Matching-host watcher operation, budgets/backlog, outages/restarts/reorgs and
  explicitly approved integration/runtime/configuration rollout.
- Real independent feeds/routes/VRF, authorities, market/deployment/gas/complete
  fees and remaining operating rehearsals, plus independent audit/remediation.

ERC-4906 is a notification, not marketplace acknowledgement or an immediate
display guarantee. The original [OpenSea update guidance](https://docs.opensea.io/docs/updating-metadata)
and [ERC-4906](https://eips.ethereum.org/EIPS/eip-4906) support the notification
mechanism; actual collection/media acceptance still requires observation.

No public transaction, deployment, seal, service/site rollout, signer change,
existing Anvil call/reset, journal rewrite or heartbeat restart occurs. Source
publication is not production approval. All financial guards and NFT rights
remain; old reports/artifacts retain their original source scopes.
