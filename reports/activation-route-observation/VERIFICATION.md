# Read-only activation-route observation - 2026-10-18

**Conversion observations only; not activation qualification or release approval.**
Production source, services and the website are unchanged. No key was read,
signature produced, contract deployed or public transaction submitted.

The initial two attempts retained in the $1 rehearsal evidence failed on an HTTP
error. A paced feed-only probe subsequently read both expected feed runtimes,
decimals and rounds successfully. The original HTTP failure's cause remains
undetermined; this does not establish reliable provider operation.

At Robinhood block **92,079,017**, hash
`0x2dbc27f76a61f811732d62a93f817064eb4c828ad99245b3f0dc1d1f69306ef3`,
the next probe verified the recorded USDG/WETH identities, router/quoter/factory
runtime and bindings, pool mappings/currencies/fees, active liquidity and funded
quote output. Calls used the same canonical block hash. The final canonicality
and 300-second observation freshness checks passed at an age of 193 seconds.
This historical observation is not a currently executable wallet quote.

The observed feed values were USDG **$0.99997977** and ETH **$2,345.50519761**.
Input **1.000021 USDG** rounded up to at least $1 of gross source value.

| V3 fee tier | Oracle-marked WETH output | Conversion shortfall, approximately |
| --- | ---: | ---: |
| 0.01% | $0.996100 | 0.3901% |
| 0.05% | $0.996013 | 0.3988% |
| 0.30% | $0.995948 | 0.4052% |
| 1.00% | $0.988115 | 1.1886% |

The last route already exceeds the full 1% budget. The other quotes leave only
part of that budget for subsequent conversion, LP deployment and undeployed input.
These shortfalls include the difference between venue output and the observed
oracle mark; they are not pure fee or isolated slippage measurements. No slippage
tolerance or complete operation gas estimate has been deducted. Quoter internal
gas is not the wallet transaction gas, and the $1 result does not qualify $100 inputs.

## Evidence and limits

- [Conversion observations](conversion-observation.json) record raw quantities,
  block identity, checked runtime hashes, source hashes and the complete result.
- [Feed diagnosis](feed-diagnosis.json) records the preceding separately pinned
  feed-only read. Its values are not substituted for the conversion snapshot.
- [Artifact manifest](artifacts.json) binds the external probe scripts and records.

The probes use the existing local unpublished conversion-reader draft; its exact
hash is recorded, and this documentation publication does not publish that draft.
Raw scripts remain in the external `dollar-rehearsal-20261018` evidence directory.
The provider was Pinax; one successful paced observation is not redundancy, uptime
or production RPC qualification. Feed implementation/authority, heartbeat/sequencer
policy and independent ZZZ valuation still need review. A proxy runtime match alone
does not approve an oracle. Existing feed-round checks do not choose production policy.

No complete Entry/Vault/Pons LP execution was performed in this observation. The
existing local tests and earlier fork tests were not repeated or relabelled.
Follow the [integration campaign](../../docs/INTEGRATION_CAMPAIGN.md) and
[central activation task](../../TODO.md#task-activation-assets) for the remaining scope.
