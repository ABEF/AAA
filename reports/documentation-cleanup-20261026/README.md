# Documentation consolidation - 2026-10-26

The user requested consistent Markdown and removal of unnecessary old pages.
This is **documentation only**: no contract/backend/frontend implementation,
transaction, deployment, seal, chain state, service or monitor change.

## What changed

- Consolidated the active README, project instructions/context, feature reference,
  roadmap and work handoff. Removed accumulated superseded checkpoint prose;
  current rules and procedures take precedence over historical snapshots.
- Reconciled specialist guides against current source: accounting3/direct
  governance2/fee1/localV4, ETH/fixedZZZ inputs,2/1/3%default limits with10%ceilings,
  pricing2/3%agreement, exact Entry review, custody and current fee history.
- Corrected concrete stale examples: removed function aliases/selectors,
  scheduler instructions, single-feed pricing, converter/reporting versions,
  old native-state codes, obsolete creator/bridge procedures, and claims that
  paused monitoring or historical local ports are currently running.
- Kept direct-mint unsigned preparation distinct from unsupported OpenSea
  qualification; published native2/historical local profiles do not become
  current3 public wallet acceptance by relabeling configuration.
- Added the [documentation map](../../docs/README.md). Kept the sole65-task ledger
  and statuses; the feature reference and release record remain different duties.
- Preserved source-scoped reports byte-for-byte, apart from their navigation
  index. Historical research linked by old evidence is now a short explicit
  pointer to its exact pre-cleanup Git text, rather than a stale operating manual.

## Redundant files removed

| Removed page | Owning guide(s) retaining the current information |
| --- | --- |
| `docs/PRODUCT.md` | [README](../../README.md), [economics](../../docs/ECONOMICS.md), [metadata](../../docs/NFT_METADATA.md) |
| `docs/ACTIVATION_ASSETS.md` | [Entry/source policy](../../docs/ACTIVATION_ENTRY.md), [operator manual](../../docs/OPERATOR_MANUAL.md) |
| `docs/NATIVE_POOL_ADAPTER.md` | [Selected pool admission and settlement](../../docs/POOL_SELECTION.md), [native architecture](../../docs/NATIVE_ETH_ARCHITECTURE.md) |
| `docs/OPENSEA_MINT.md` | [Primary mint and VRF qualification](../../docs/MINT_INTEGRATION_QUALIFICATION.md) |
| `docs/REFERENCES.md` | [Development and exact dependency pins](../../docs/DEVELOPMENT.md), [source review](../full-audit-20261025/UPSTREAM.md) |

Their full text remains in [pre-cleanup Git](https://github.com/ABEF/AAA/tree/a5fad3e744da3d2ecbde01611c3f0b5371736784/docs).
No unique live procedure or audit evidence was discarded to reduce file count.

## Preservation and verification

All348tracked Markdown files were inventoried before consolidation. Full original
working copies and all14original dirty paths are backed up and hashed outside
Git under the documentation-cleanup evidence directory named in
[work handoff](../../docs/WORK_HANDOFF.md). Original unrelated code drafts remain
unchanged. The reviewed dirty Markdown is intentionally replaced; its unpublished
preimages remain available, and unrelated code is not included in the commit.

Validation checks current file links/section anchors, generated Todo and callable
reference, exact unchanged production/dependency/build/backend-test pins, and
historical report preservation. Results and actual changed-file counts are in
the final verification JSON alongside this document. No unchanged contract,
backend, browser, fork or service suite is rerun for prose changes. Existing
source-scoped evidence is reused without increasing test counts.

Website changes are repository memory only. Public DEPLOYMENT stays null,
signing Anvil-only, monitoring paused; existing Anvil/NFT/LP/balances/journals/dist
and public server stay untouched. Publication is verified separately.
**Production NOT APPROVED:** actual services, prices/routes/VRF/authorities,
OpenSea/current3website, target-gas/operations and independent audit remain open.
