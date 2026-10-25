# Qualify RPC capabilities before deploying PoPL

The existing `keeper.probe` has two explicit read-only profiles. Neither approves
a provider, deployment, signer or release. It can run before PoPL contracts exist.
The [production observer](PRODUCTION_PREFLIGHT.md) remains the separate check for
the actual deployed PoPL bindings and inventory.

| Profile | Observations |
| --- | --- |
| `keeper_v1` (existing default) | Fresh heads, common confirmed block, canonical-hash call/code/storage reads, explicit missing-block rejection, gas-price observation, safe/finalized tags and bounded ordinary receipts. |
| `activation_api_v1` | All of the above, plus the independently reviewed genesis and probe-token runtime, and an actual `callTracer`/`withLog` event witness at the same canonical block hash. |

## Prepare public identity and private endpoint configuration

Use one to eight reviewed URLs in a private JSON file containing `chain_id` and
`rpc_urls`. External endpoints require HTTPS; HTTP is allowed only on loopback.
Keep credentials outside Git and reports. Do not place wallet keys in this file.
The CLI rejects duplicate JSON keys, nonfinite numbers, files over 64 KiB,
ambiguous arguments and an output path equal to the input configuration.

For the preparation profile, independently establish:

- The expected genesis hash of the intended network, not a value copied from
  the endpoint under test merely to obtain a pass.
- An already deployed, reviewed ERC20 probe address and its exact runtime
  Keccak-256 hash. Choose a token that implements ordinary `approve` and emits
  the standard `Approval` event. A proxy runtime alone does not review its
  implementation, administrators, token safety or future upgrades.
- A bounded getter on that token for the existing canonical-state read probe.
  `0x18160ddd` is `totalSupply()`; do not assume every target implements it.

Robinhood mainnet is chain 4663 and its testnet is 46630. The
[official connection guide](https://docs.robinhood.com/chain/connecting/) recommends
archive access for historical reads and warns that public endpoints are
rate-limited and unsuitable as a production-service plan.

## Run the opt-in read-only probe

Replace the uppercase values below with reviewed public identifiers:

```sh
python3 -m keeper.probe --config PRIVATE_RPC_CONFIG.json --profile activation_api_v1 --address REVIEWED_ERC20_ADDRESS --calldata 0x18160ddd --genesis-hash REVIEWED_GENESIS_HASH --runtime-hash REVIEWED_RUNTIME_HASH --output var/rpc-preparation-observation.json
```

Optional `--confirmations` and `--receipt-blocks` retain the existing defaults of
12 and bounds of 1-1000 and 1-32. The tool never discovers a key, submits a
transaction, signs, starts a service or modifies a journal. Running the command
does make read RPC requests and may consume the provider's API quota.

The extra witness simulates `approve(probeAddress, 0)` with zero ETH from a fixed
public probe address, using `eth_call` and `debug_traceCall`. Both simulations
discard state. No allowance is actually created or revoked. No state override,
user balance, user approval or PoPL runtime is needed. The reviewed token runtime
must match before tracing proceeds.

The trace must describe the exact caller, target, calldata, zero value, successful
return and bounded gas, and contain exactly the expected `Approval(0)` log with
the correct emitter/topics/data. A standard proxy may emit it in a child frame.
Accepting `withLog: true` on a getter that emits nothing is insufficient evidence
that the provider supplies the logs required by activation preparation. See
[Geth's tracer specification](https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers).

## Interpret failures and retain evidence

A failed required check keeps `compatibility_checks_passed` false. A missing
reference header on one endpoint is recorded without hiding subsequent endpoint
results. Outputs contain endpoint indices, public probe identities, fixed
diagnostics and sanitized remote error codes/reasons; they omit endpoint URLs,
credentials and raw provider error messages. Redirects are refused even on the
same host. Each endpoint permits at most 100 logical RPC calls, refuses new
calls or late results beyond its 90-second deadline, and uses bounded transport
timeouts. This is not a hard wall-clock process watchdog: an in-flight transport
can take longer to return before its result is rejected. Receipt sampling remains
limited to three ordinary receipts.

The unknown-hash test passes only after an explicit recognized unavailable-block
JSON-RPC error. A timeout, rate limit, unsupported parameter or ambiguous error
is a failed/unavailable observation. Unknown provider wording requires review;
do not relabel an outage as successful rejection. This follows the
[EIP-1898 missing-block requirement](https://eips.ethereum.org/EIPS/eip-1898).

The CLI returns zero only when all scoped endpoint checks pass. Preserve the
report, exact probe-source hash, reviewed pins, chosen confirmation policy and
observation time. Configuration/argument rejection does not replace an older
report. A completed failed capability observation is intentionally saved with
its result false. Publication uses an atomic replacement; if a filesystem error
is reported during publication, inspect the artifact rather than assuming that
the old or new version is durable. Do not present older evidence as fresh.

Even a pass is not independent provider approval, consensus/finality proof,
uptime, full archive/log completeness, fee-accounting qualification or a
successful PoPL financial operation. A malicious provider can fabricate
self-consistent replies. Rehearse actual current-version activation/growth,
claims, gas, outages and recovery against the reviewed deployment, and obtain
independent operational approval before real funds. Track those remaining gates
in the [central Todo](../TODO.md#task-host-services).
