# Verified publication - liquidity operations

Verified `2026-10-24T23:38:06.551675+00:00`. Both pushes used main; their remote heads were independently
read with `git ls-remote origin refs/heads/main` after successful pushes.

| Repository | Verified implementation/memory revision | Scope |
| --- | --- | --- |
| Contract | [`593a212`](https://github.com/ABEF/AAA/commit/593a2121f101b987e9a4ca1e6481a98698683c61) | Liquidity/idle/default/range/keeper code, strict API/inventory/events, generator repair, focused evidence and task/operator/memory records |
| Website | [`1e1a9ba`](https://github.com/ABEF/AAA-website/commit/1e1a9ba99909c88f7a10ab76cd25a10c0f7a5bdb) | AGENTS.md and PROJECT_CONTEXT.md only |

[Machine receipt](publication.json) pins all121files of the implementation commit.
This separate receipt and memory follow-up does not change that code revision.
[Verification](VERIFICATION.md), [review](REVIEW.md) and [final scope](FINAL_SCOPE.json)
retain the exact passing, failed-first, oversize, reuse and substitution boundaries.
68distinct scoped Solidity cases,297Python passes/one Unix-only skip,37normal object
gates and111selected functional/evidence input hashes are source-bound. The extra
unrelated research-reader diagnostic hash is explicitly excluded, not silently
published or called tested. Exact-revision CI is not declared green.

Contribution default2%, conversion1%, maintenance3%, gas separate. The original
shallow fixture now deploys$99.378 of$100 at an explicit stricter1%cap. Adaptive
range selection is default-disabled and requires reviewed ZZZ-price orientation,
thresholds/runtime/configuration/cooldown policy; real strategy economics are
unqualified. Source-chain custody handles external token/chain conversion;
integrated bridging and remote NFT/reward transport are deferred optional scope.

**Still open:** reviewed caller-bound Entry loss policy before public activation
signing, actual feeds/routes/authorities/VRF/OpenSea/native website/services,
maximal real venue gas and operating rehearsals, independent audit/remediation.
Vault runtime margin57bytes and Registry initcode margin31bytes require size-safe
future work. Production **NOT APPROVED**.

No website source/build/server, existing8902/Anvil/NFT/LP/balances/journals/dist
overlay, signer policy, service or paused-monitor change. Public DEPLOYMENT null;
signer Anvil-only. Older unrelated local drafts remain preserved and excluded.
