# Execution-price backend evidence

The current source implements explicit `execution_price_version: 1` with LP routing3. Omitted/0 remains the historical routing2 family. Holdings and claims do not gain a live Oracle availability dependency. Financial preparation authenticates six pinned components plus the existing Math child, an inactive context and the source-kind revision. Public dual-source price observations remain live.

- `python-consumers.json`: 323 distinct affected Python methods pass, with no failures/errors/skips and stable source hashes. This deduplicates earlier staged runs; do not add their overlapping counts.
- `actual-trace-replay.json`: four additional methods replay four actual owner-origin RPC traces through the production contribution decoder. These are offline replays of the same four local EVM workflows, not four additional EVM executions.
- `rpc-cases.json`: individual inputs, source/runtime provenance, physical LP/share measurements, original default rejection and separate diagnostic gas/fee evidence. The four compressed fixtures live under `tests_python/fixtures/reference-execution1-actual-*.json.gz`.
- `reviewed-envelope-calls.json`: the same four exact calls also succeed when simulation gas is reduced from32M to the derived reviewed network limit17.18M–18.93M; caller, destination, value, calldata, canonical source state and empty output are unchanged. These are separate bounded read-only calls, not additional workflow or Python method counts.
- `source-manifest.json`: exact modified source/test/fixture hashes and adoption boundaries.
- `export-merge-format.json`: independent actual EVM proof that setup baseline plus per-slot delta preserves explicit zero writes and untouched values.

All four exact operations reject at the unchanged 12M default. Separate local policy2 diagnostics use a 32M simulation cap, a confirmed 64M engineering block limit, full20% estimate headroom and explicit gas-price/network-fee bounds. This does not approve a production budget, enable policy2 or change a caller/default/running configuration.

The producer authenticates a setup-end baseline file with its emitted raw Keccak, merges account fields and storage slots with the final delta (including zero), and verifies the materialized runtimes. Foundry omits its running harness; no Entry descendant calls it. No balances or storage values are invented. Raw large allocations, complete RPC logs, original failed exports and compiler stages remain external.

These are actual local core/StateView/PosM and production Entry/Vault/Pricing/Oracle/Manager/Rewards/Fees calls with explicit MockAccess, registry/admission, Permit2, ETH publication, VRF and funded-market seams. The initial contribution is1000USD; growth uses100input tokens. This is not the browser's exact100USD activation-selection test, current Mint2/OpenSea onboarding, an admitted production inventory/API service, real market/source independence or hosting/wallet/operating qualification.

All owned temporary nodes were stopped. There were no signed or broadcast transactions, public/configuration/service/site changes, or changes to Anvil8902, journals, signer restrictions or the paused heartbeat. Optional source-pinned checkpoint adoption still requires reviewed rebuild/re-pin; preserve old artifacts and raw/WAL data. Source hashes are not running-code attestation.
