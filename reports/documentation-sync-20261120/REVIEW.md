# Current documentation and memory reconciliation

20 November 2026. Contract baseline `b9baa01ceb2ca8520cfe058b74bc736bb7355c40`;
website baseline `2183e1ac676e4eb7d7ccac6dc0ce597c419aef0c`. Main only.
**Documentation publication; production remains undeployed and NOT APPROVED.**

## Corrections

- Removed the operator manual's stale requirement to use `0x501122…afe1b` for
  initial production. Final selection is operator-deferred; the old pool and
  `SELECTED_NATIVE_POOL` are existing integration/reference identities. The
  actual chosen supported pool still needs fresh qualification before adoption.
- Scoped the recorded1.002% LP/approximately1.101% combined fee to that dated
  target. It is not the fee of a production pool that has not been selected.
- Updated current market/preflight/service/price/route links to the117-response
  20November capture. Earlier tiny favorable quotes and API3/price observations
  retain their dates and original meaning; no old result becomes current proof.
- Added an explicit [v3 scope correction](../market-route-qualification-20261120/ERRATA.md).
  Principal routing and the spot reader are native-v4-only. The Solidity earned
  converter already supports reviewed v3-to-wrapper-to-ETH execution, but the
  current zero-wrapper construction and accounting7 `v4_native` worker cannot
  use it through configuration alone. Wrapper identity is fixed at construction.
- Synchronized the website README/AGENTS/PROJECT_CONTEXT with backend first-
  successful-prefix planning, finite market evidence and deferred selection.
  Backend26-pin proof is not website33-pin/source10 adoption or browser/HTTP
  acceptance. Website client limits and public signing boundaries stay unchanged.

## Evidence and unresolved work

This is a source/document consistency review, not a new dynamic audit, gas
qualification, market probe, browser suite or re-run of unchanged tests. The
current task statuses, exact source graph, all financial/resource bounds and
original evidence remain. The sole Todo and release record retain ownership.

Still open: operator's final pool, independent feeds/publication and usable
routes/depth, production RPC/complete fees, expanded full-normal workloads,
the prior slow-ZZZ estimate reduction, actual OpenSea/VRF/authorities/content,
matching consumer/host/recovery adoption and independent audit/release approval.

Original changed documents were archived outside Git before editing. The four
unrelated tracked edits and original reports remain byte-identical. The website
update changes three Markdown files only; no build/dist, signer, deployment
configuration, served popldemo/poplint, existing Anvil, journal/checkpoint, service
or paused-heartbeat changes are authorized or performed.
