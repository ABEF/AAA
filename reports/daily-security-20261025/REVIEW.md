# October25 changes: security, necessity and consistency review

The day scope is Europe/Paris2026-10-25, starting2026-10-24T22:00Z, including the
clock change. Git establishes the first day commit as `14ee92e`; its parent is
`3551868d3413f650e07523229b959d3ea7d0f4a8`. The reviewed published endpoint is
`1e00b49`, followed by the fixes recorded here. Older unrelated dirty drafts are
outside this audit's implementation/publication scope.

Three source reviews traced financial execution, governance/custody and services.
The root review cross-checked the combined changes, callers, actual evidence,
current operator procedures and the one-ZZZ product decision. This is an internal,
bounded review, not an independent audit or proof that all possible bugs are gone.

## Confirmed findings and changes

| Severity | Finding | Resolution and retained boundary |
| --- | --- | --- |
| P2 setup/liveness | Source and normal-exit ZZZ could match each other while differing from Registry's hardcoded native-pool ZZZ. | Native admission now requires the already configured source ZZZ to equal the existing native token constant before venue checks. One-time source identity cannot later be rebound. Generic ERC20 admission remains separate; successful real native admission still needs actual dependencies. |
| Product/security policy | Buyback still had an old governance token-retargeting function, inconsistent with the user's explicit one-ZZZ/exit-and-redeploy decision. | User explicitly chose a fixed target. Buyback `zzz` is immutable and `setZZZ`/its event are removed. One-time Migration configuration requires the bound Buyback and source identity to match before recording its exit pin. Existing seal matching then proves all three match without adding Access initcode. This is one token used by multiple modules, not multiple ZZZ tokens. |
| P2 availability | Global incumbent dust settlement queried live venue accounting for every historical bucket, even with no dust. A broken old native venue could block healthy new entry elsewhere. | Enumerate already admitted stored currencies with Registry `get`. Nonzero dust still needs exact funded settlement and solvent backing; current-pool execution still validates actual accounting/LP/prices. No old reward is skipped or given to a newcomer. |
| P2 data integrity/availability | Indexer could commit malformed transaction/log identities or duplicate block/log positions, then advance the cursor; history consumers rejected the stored rows. | Validate hashes, quantities, emitter, topics/data/raw bounds and transaction/block uniqueness before writes. Recheck cursor under a short atomic transaction. Preserve valid unknown events; no schema migration, silent repair, deletion or resubmission. See [service review](SERVICE_REVIEW.md). |
| P3 maintainability/documentation | An unused `IMigrationContribution` declaration, an orphaned retired-initializer comment, stale burn-target instructions and duplicate operator paragraphs remained. | Remove unused declaration, label the live reviewed initializer correctly and reconcile current setup/operator/function notes. Older evidence retains its original source scope. |

No confirmed new unprivileged withdrawal, arbitrary-call authority, reward-theft,
double-claim or share-dilution exploit was established in the inspected paths.
That statement describes this review's findings, not a guarantee of exploit absence.

## Combined reasoning checked

- Contribution admission remains ETH/fixed ZZZ, with minimum$100 activation and
  $5 growth, exact original input, frozen dual-price/policy basis, caller loss
  maximum and actual marginal deployed-LP/backing checks. The source3% agreement
  band does not promise a contribution can satisfy the tighter default2% floor.
- Fee receipts remain actual local collections, allocated80/10/5/5 with carried
  raw dust, incumbent settlement, separate compound/buyback backing and equal
  activated membership. Top-ups/transfers do not create membership or old income.
- Independent royalties retain actual-receipt funding, fixed rarity weights,
  optional-currency outage cohorts, same-NFT conversion credits and current-owner
  claims. Metadata state does not authorize funds or change fixed traits.
- Maintenance remains bounded two-pass execution and optional reviewed25/50width
  selection. Per-operation3% is not a cumulative-loss cap or an impermanent-loss
  guarantee; the user explicitly retained per-operation policy only.
- Caller-bound source-policy factory creation, exact module bindings, terminal
  canonical states, LP-only V3 row lengths, authentic exports, exact backing and
  fully funded same-chain abort/retirement remain. Source-chain external custody
  is trusted and is not cross-chain NFT/ledger transport.
- Normal exit remains all-ZZZ under captured minima/floor. Raw exit is explicitly
  approved no-swap actual-asset delivery, with no invented USD guarantee or
  automatic fallback. It gains no buyback/source validation dependency from the
  new bootstrap consistency check.
- Keeper saved-intent gas/nonce/receipt recovery and old profiles are preserved.
  Indexer reads are not custody authority; missing/provider-poisoned history is
  unavailable, never synthesized as zero earnings or permission to claim.
- Optional Pyth is a bounded source adapter, not an independent ZZZ feed or
  update service. Runtime/source/review hashes cannot establish provider honesty,
  common-mode independence, correct proxy administration or real market depth.

## Necessity decisions

The [31-contract purpose/caller inventory](NECESSITY.md) explains retained code.
Real converter wrappers, stable Position/status ABI, historical event/profile
readers, saved-transaction recovery and same-chain handoff are necessary to their
current obligations. Removing them just because names look old would break
safety/compatibility. Preparation notices do not grant a remote successor power.
Public/API/user/operator entrypoints need not have an internal Solidity caller.

The earlier obsolete Registry wrapper records, creator inboxes/measurement and
bridge/finality declarations were removed in their own source-bound checkpoints.
This audit found and removed one additional unused interface. No universal
minimality, optimal gas or exhaustive no-dead-code proof is claimed.

## Fresh-deployment and remaining release gates

Buyback's token is now immutable, changing its fresh-deployment storage layout.
Together with the earlier Registry cleanup, this is **not an in-place upgrade**.
Do not patch the existing Anvil deployment or reinterpret its journals.

Access construction remains49,123bytes with minimal nonempty role arrays:29bytes
of headroom. One extra32-byte role entry exceeds the limit by3bytes. Actual release
arguments are not qualified; a multisig's owners belong inside that multisig,
not automatically in proposer/executor arrays. No size/optimizer/EVM waiver was used.

Actual source/route/VRF/RPC qualification, authorities, OpenSea primary mint,
native wallet/services, maximal venue gas/strategy economics, operating rehearsals
and independent audit/remediation remain open. Current code minima are not an
exact-$100-only contract restriction. Historical-to-current cross-codec imports
remain unsupported; this audit does not widen lineage or canonical schema support.

Production remains NOT APPROVED. No deployment, public transaction, signing-policy
change, service restart, server update, existing database repair or paused-monitor
change occurred. See [verification](VERIFICATION.md) and the separate publication
receipt for what was actually tested, reused, committed and pushed.
