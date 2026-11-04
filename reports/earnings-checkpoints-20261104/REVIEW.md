# Reviewed earnings checkpoints: implemented first milestone

November5,2026; baseline main096fd2be4db514d5fd8930c672522ed1fc6c3ff0.
**Production NOT APPROVED.** [Plan and two design critiques](PLAN.md),
[operator/configuration guide](../../docs/EARNINGS_CHECKPOINTS.md),
[OpenSea investigation](OPENSEA_RESEARCH.md), [verification](VERIFICATION.md).

## What improved

Collection, NFT and wallet-chunk earnings can opt into an immutable externally
pinned checkpoint and replay only a bounded raw suffix. Previously every request
replayed from creation. The changed code proves an actual availability improvement:
the same3-event limit admits a correct checkpoint suffix and rejects the longer
full replay; lowering that suffix bound to2still rejects rather than truncating.

The checkpoint includes scaled NFT earnings, fee dust, share/index denominators,
membership/cohorts, owners, claims and conversions. It is not a cache of rounded
totals. A complete rolling24hours remains raw-replayed: a served checkpoint must
be at least86400chain-time seconds old. At the exact boundary it is valid; newer
checkpoints reject. Today-price valuation stays at the current confirmed block.

The offline builder validates the actual pinned source/deployment/ledger state
and all minted NFT rights at a complete cutoff. It can advance an old approved
checkpoint, under separate explicit offline budgets. New artifact creation is
atomic/exclusive; no existing artifact/configuration is automatically replaced.
The HTTP request budgets, public paths, financial weights and fixed input assets
are unchanged. No checkpoint was built from an actual deployment or installed.

## Security/operating design choices

| Boundary | Implemented behavior / limitation |
| --- | --- |
| Trust | Exact artifact SHA-256 must come from reviewed configuration, alongside semantic source and deployment bindings. A hash does not prove honest or complete history; raw/provider evidence and independent approval remain. |
| Entitlements | Whole totals derive from complete carried fractions. Credits pair with exact fee allocations; newcomer dust/cohorts stay isolated. Live indexes/shares/membership and selected NFT claims/conversions still reconcile. |
| Snapshot/reorg | Creation and checkpoint anchors, complete suffix ancestry/chronology, canonical RPC/depth and a read-only SQLite transaction remain. Cross-prefix transaction repetition uses the existing PK index, not a lifetime scan. An anchor reorg requires reviewed rebuild/re-pin. |
| Concurrency | Immutable loaded bytes and per-request reconstructed maps prevent one replay changing another. Current-holdings ownership remains pinned; concurrent WAL ingestion cannot change a read transaction's snapshot. |
| Failure | Missing/corrupt/wrong-source/too-young/unsupported state fails closed. No zero, implicit full replay, new authority or deletion of pending records is supplied. |
| Compatibility | Opt-in checkpoint1 requires explicit accounting6/custody5/fee-intake1, no predecessors. Old config/profile behavior remains explicit. All public wallet signing remains Anvil-only; no site/manifest/runtime relabel. |
| Future changes | Old descriptor meaning stays fixed; a new actual royalty admission can extend descriptors with matching suffix evidence. Source changes require bounded rebuilt stages or a separately reviewed future codec, not editing a hash. |

No source Solidity/ABI/storage/economic or permission change. Original reports,
four protected dirty files, services/sites, Anvil/NFTs/LP/balances, nonce/spend
journals and paused heartbeat are preserved.

## Actually verified and deliberately still open

The broader affected147Python methods passed at their recorded source stage.
After stricter checkpoint validation, the final24new checkpoint methods passed
again. These are overlapping stages, not171distinct checks. They exercise actual
fresh Projection/Earnings/History, real disposable SQLite/WAL and synthetic pinned
RPC transcripts—not live target dependencies or new EVM execution.

Checks include full-replay equivalence and independent expected amounts; exact
fractions crossing in the rolling day;80/10/5/5dust; deferred royalty recovery;
new royalty admission/prefund exclusion; transfer/claim nonincome;1000account
tracking; bounded suffix; restart/concurrent reads/WAL ingestion; source/digest/
identity/schema errors; reorg/gap/duplicate transaction; publication failure and
offline budget isolation. Initial fixture/setup failures remain retained.

This is not the whole lifetime-history task completed. General lineage
checkpoints, other full-history consumers, unattended rotation, raw archival/
retention, source-codec migration tooling, maximal deployment/asset workload and
real archive/provider/host/storage qualification remain. Current frozen-release
independent audit remains open. No unchanged Solidity/compiler/analyzer suite
was repeated; exact previous source-bound contract evidence is reused.

OpenSea investigation separately confirms required recipient/statistics/payment
and callback design work. Exact Robinhood primary-drop product/deployment and
actual fees remain unqualified; no guessed minter authority or template NFT was
introduced to make that task look complete.
