# Verification and evidence boundaries

Baseline `11e74883787e32e816b5c01b1213189400fe01fe`,13November2026.
**New external evidence and offline integrity only. No production/test code,
unchanged suite, EVM financial operation, fork or compiler run.**

| Evidence | New execution | Boundary |
| --- | --- | --- |
| Independent identity |9 Ethereum HTTP attempts:7 JSON-RPC replies including a null receipt,2 initial403 denials | Official rollup/deployment source; assertion/event hashes independently recomputed. No receipt-trie or local consensus proof. |
| Existing full RPC profile |48 Robinhood HTTP posts,24 logical reads,13 passing checks | Unchanged helper with configured1.5-second monotonic transport pacing. Intentional unknown-hash error is successful negative evidence. Stock CLI parsing/cadence not rerun. |
| Capacity/history |19 further bounded Robinhood reads,3 successful diagnostic groups | Tiny50k code-only override/nonpersistence, one retained event and one exact historical state/runtime; no full20M/24M workload or plan guarantee. |
| Markets |58 attempts:53 results,4 explicit RPC errors,1 retained429 | Original partial phase retained; separate7-read closure rechecks same canonical anchor. Four new200k quote diagnostics; no old696-quote campaign rerun. |

These are separate anchors and phases. The full profile, capacity and delayed
market closure were serialized after the original market429, with slower spacing
and cooldowns. No immediate retry, refusal bypass or new public transaction was
used. Document GETs have their own record and are not added to RPC totals.

## Independent review and offline checks

- Exact event layout/topic, zero parent/before-state, six-word after-state hash,
  assertion commitment, initialized chain/WASM and canonical L1 header were
  reconciled by a second reviewer before using the expected genesis.
- All three new evidence verifiers pass offline. RPC pins11public/93external
  artifacts; capacity pins11public/35external, with its verifier checking28
  original response/document/producer files; markets verifies70public input
  files and57exact response bodies. Manifest counts have distinct meanings and
  are not added as test totals. See their own manifests and reports.
- Peer review found no material overclaim. Wording distinguishes configured
  monotonic pacing from observed UTC gaps, and activeL from TVL or usable depth.
- Root's first external RPC verification pointed to the parent evidence folder
  and failed on missing `derive_identity.py`. It was corrected to its `rpc`
  subfolder and passed. No observation, network request or evidence byte changed.
- Generated Todo, function reference and operator table checks pass:
  40contracts/956functions/40constructors/13receive hooks, with zero explanation,
  input or output annotation gaps;1009operator examples. This establishes
  documentation coverage, not function execution or submission approval.

## Preservation and publication

The [completion receipt](COMPLETION.json) records final mechanical source,
archive, introduced-link, task and exact publication checks. All61production
Solidity files and100normal compiler-input sources match their accepted bytes.
The existing strict567record review,48normal gates, controlled20M/24M traces and
earlier14keeper methods retain their exact original scope; none was rerun.

Current backend/helper pins, all12website import inputs, website revision,
shared Anvil-only signer and both public null configurations remain unchanged.
All20original current docs were archived before consolidation. Four protected
tracked dirty files remain byte-identical and excluded from publication.
Existing reports are immutable except their navigation index. Main only;
source/docs publication is not deployment/provider/configuration adoption.

Actual qualified feeds/routes, current launch-state full fees, numerical
provider capacity/plan/SLA/lifetime archive, authorities, OpenSea/VRF and
operating/independent approval remain open. No default or safeguard changed;
no service/site, existing Anvil/journal or user-paused heartbeat change occurred.
