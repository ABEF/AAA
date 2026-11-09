# Source-scoped verification

Contract repository baseline: `ff4b502bf19772a01b9eb35c22ff5db1c55efacd` on main.
No production Solidity, ABI, storage, authority, runtime or operating setting was
changed. The existing source9 fork campaign and historical reports retain their
original scopes; no public transaction or new operating rehearsal ran here.

| Scope | What was checked |
| --- | --- |
| New custody adapters | 15methods: raw closure, exact14-word ParkingRequest, both zero floors, both physical legs, preparation drain, same/different same-pair resume, price outage and consent drift. |
| New terminal adapters | 13methods: terminal phase/pause matrix, bounded bucket/ordinal inventories, backing, current-owner/shared-wallet/zero/paid rights, exact dynamic ID arrays and no USD dependency. |
| Complete preparer | 13methods: seven exact action pipelines, source-bound provenance, canonical/final simulation, fixed gas and fees, gas-sensitive partial payouts, stale controls/owner/cursor, expiry/reorgs, bounded work, unsupported envelopes, exclusive output and error sanitation. |
| Existing B/C/D | 29methods after the behavior-preserving shared-policy extraction. These are existing affected checks, not29new features or another contract audit. |
| Independent ABI review | Seven actions match the pinned offline Cast encoder and actual source-bound callable catalogue, including a32-ID dynamic array. This is encoding verification, not execution. |

The final focused run had70unique test IDs, no failures/errors/skips. A later
one-line CLI correction changed `output_may_exist` for an already-existing file;
that affected method was rechecked successfully. Its overlap is not an additional
unique test. Earlier test-fixture setup/import-discovery failures are retained
outside the repository; no production guard was weakened to correct them.

The seven collected example artifacts are explicitly **synthetic test reviews**,
with fabricated deployment/RPC fixtures and `ready_for_submission=false`.
Their original test-stage source pins are retained; they must never be copied
into a live operator review or relabelled as current deployment evidence.

Local evidence:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/operator-management-20261109`.
Independent review:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/management-independent-20261109`.
Published records preserve exact source pins and separate the diagnostic-only
final delta from the unchanged preparation/adapter contexts.

Actual provider canonical-hash/fee support, governance wallet execution/envelopes,
target gas and recipient behavior, operating recovery and independent production
approval remain open. The normal/static/callable contract evidence may be reused
only at its unchanged source hashes; documentation checks do not turn it into a
new Solidity or deployment verification run.
