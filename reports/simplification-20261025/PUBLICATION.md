# Source publication receipt - 2026-10-25

**GitHub publication only. No deployment was requested or performed.**

| Repository | Commit on main | Verified remote |
| --- | --- | --- |
| Contract | `82ba6edf4a2ca510480c49d6b8d0771a37bc791e` | Exact origin/main match |
| Website, memory only | `ce1f31ef54efe079b3378cabda7064a4bed15b59` | Exact origin/main match |

The remote heads were checked at `2026-10-25T03:58:44.476782+00:00`.
This receipt is a separate documentation commit and does not deploy those sources.

Normal custody exit uses the fixed deployment ZZZ. Sealing checks that contribution
and normal-exit identities match; explicit raw exit sends ETH/ZZZ without swaps.
Creator-payment inboxes and integrated cross-chain paths are removed. Same-chain
pool moves, external custody exit/recovery, royalty accounting and complete
collection handoff remain. See [review](REVIEW.md), [verification](VERIFICATION.md)
and [staged source scope](FINAL_SCOPE.json).

Evidence covers 89 distinct selected Solidity behaviors across two source scopes,
not a fresh full final-source regression. Normal bytecode limits pass; minimum
nonempty Access role-array initcode has only 29 bytes of margin, so actual release
constructor arguments remain an explicit qualification gate. Todo and the
source-bound function reference were checked after the final operator wording fix.

Website source/build/server, existing8902/Anvil/NFT/LP/balances/journals, the
Anvil-only signer, null public DEPLOYMENT and paused monitoring are unchanged.
No public contract deployment, signing, transaction or service action occurred.
Older unrelated drafts remain local. Production is NOT APPROVED: current real-pool
fork qualification, feeds/routes/VRF, authorities, OpenSea, operating rehearsals
and independent audit/remediation remain open.
