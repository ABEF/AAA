# Operating-control publication receipt - 2026-10-24

| Repository | Published scope | Verified main commit |
| --- | --- | --- |
| ABEF/AAA | Bounded future-request VRF tuning, buyback operating ceiling, compatible event catalog, inventory checks, scoped evidence and operator/Todo updates | [143734c](https://github.com/ABEF/AAA/commit/143734c632eea5ae3a91cb43e490f457bd600261) |
| ABEF/AAA-website | Both repository memories only | [34f53d6](https://github.com/ABEF/AAA-website/commit/34f53d639f8a41250a322b6febe55a7407e80cff) |

Both commits were pushed normally to main and verified with remote hashes before
this receipt. The receipt and final contract-memory prefix are a separate
documentation-only follow-up. No branch, PR or force push was created.

[Scoped verification](VERIFICATION.md) records nine distinct new VRF cases, six
affected existing VRF/reveal cases and 35 distinct buyback cases across the
recorded runs. Two initial VRF test expectations were repaired and only the
affected cases rerun; no production guard was changed to repair them. The
strengthened buyback fuzz used 1,000 runs. Twenty-six inventory and five final
event cases pass. All 34 production size gates pass; 32 source objects are
unchanged from the native checkpoint, 78 compiler bindings match, and 104
Solidity inputs typecheck. The 111-file candidate snapshot and evidence hashes
match published bytes. No full fresh regression or real-service approval is claimed.

The [internal review](REVIEW.md) covers immediate governance, ordinary pause,
preparation/canonical locks, reentry, pending-request continuity, per-trade bounds,
reserve preservation, snapshot accuracy and historical event decoding. The
operator manual explains exact calls, USD18 units, stop/reopen, pending operations,
keeper configuration/backoff and successor-local policies. Central Todo, feature
reference, roadmap and both repository memories are aligned.

Actual provider limits/funding/recovery, typed v4 conversions, native website
profile, reviewed production inventory, routes/feeds/services, target-chain
rehearsals and independent audit remain open. Future VRF tuning cannot repair a
past request. Buyback zero stops future buys and direct ZZZ burns without moving
the reserve; resize/remove fixed keeper tasks to avoid intentional failures.
The 1%/3% execution limits and separate gas remain unchanged.

No private key access, public transaction/deployment, website source/build/server,
existing 8902/Anvil/NFT/LP/balances/journals/dist overlay, service or paused-monitor
change. Shared signing stays Anvil-only and public DEPLOYMENT null. Older
unrelated local drafts are preserved and excluded. Production remains NOT APPROVED.
