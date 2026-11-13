# Focused 20M / 24M EVM qualification

The four new exact-dollar contribution cases fit the explicit **20,000,000**
profile with the full 20% estimate margin. Six explicit keeper maintenance
cases fit **24,000,000** with the full 25% margin. Each also executed at its
exact padded estimate, rather than relying on gas arithmetic alone.

These are controlled local execution results, not production approval or a
change to the existing 12M defaults. No production Solidity, safeguard, live
configuration, signer, service, website or existing Anvil state changed.

## Actual RPC results

All rows use the actual owner or authorized keeper EOA, an independently
restored pre-call state, a canonical pinned block and a 32M local block limit.
`Trace` is the actual `debug_traceCall` gas used; `Estimate` is the separate
`eth_estimateGas` result. Both the profile-cap call and exact padded-estimate
call succeeded for every row.

| Operation | Trace | Estimate | Padded estimate | Profile cap |
| --- | ---: | ---: | ---: | ---: |
| ETH activation, $100 | 14,094,485 | 14,748,028 | 17,697,634 | 20,000,000 |
| ETH growth, $5 | 12,894,696 | 13,616,039 | 16,339,247 | 20,000,000 |
| ZZZ activation, $100 | 14,304,627 | 15,082,371 | 18,098,846 | 20,000,000 |
| ZZZ growth, $5 | 13,117,736 | 13,929,079 | 16,714,895 | 20,000,000 |
| Main harvest | 672,362 | 728,312 | 910,390 | 24,000,000 |
| Compound existing main | 10,310,034 | 10,987,750 | 13,734,688 | 24,000,000 |
| Ordinary single replacement | 12,847,413 | 13,535,113 | 16,918,892 | 24,000,000 |
| Open main plus residual | 15,636,730 | 16,473,330 | 20,591,663 | 24,000,000 |
| Harvest main plus residual | 927,866 | 1,083,316 | 1,354,145 | 24,000,000 |
| Replace main plus residual | 15,848,089 | 16,836,989 | 21,046,237 | 24,000,000 |

Worst remaining profile margins are **1,901,154** for contributions and
**2,953,763** for the measured maintenance workload. These margins are not
predictions for every future deployment, cohort, currency count or market.

## What was newly checked

Five methods in [GasProfileQualification.t.sol](../../../test/GasProfileQualification.t.sol)
ran once each. Four contribution pre-states and six maintenance pre-states were
then checked through actual read-only RPC calls on ten separately owned local
nodes. The nodes used no default accounts, suppressed startup secrets and were
all stopped. No transaction was signed or submitted.

- Exact $100 activation and $5 growth through the production Entry graph for
  ETH and the fixed ZZZ. One smallest input unit below each minimum fails with
  the exact `InvalidAmount` error and preserves the captured atomic state.
- At least 97% marginal deployed LP, exact net-NAV share issuance, current-owner
  rights, cleared exact allowances, Vault custody and unchanged growth geometry
  and rebalance clock. Prior compound is explicitly zero for this launch NAV
  comparison; it is not silently omitted from the denominator.
- Real fee collection, existing-main compounding, ordinary single replacement,
  hybrid opening, two-leg harvesting and two-leg replacement. The hybrid case
  closes both prior LPs, clears the old residual association and retains only
  the new main plus one residual, with custody, shares and ownership checked.
- Existing timing, sampled confirmation, price, route, loss, callback, accounting
  and principal guards execute unchanged. Keeper permission is explicitly
  granted to the actual empty-code test keeper; the exporter is not substituted
  as caller.

The compiler reused the accepted normal production input byte-for-byte:
100 normal sources, including all 61 production Solidity files. Only the new
test host was compiled: 201 watched/supplied sources, 198 actually compiled.
No normal or static build and none of the parent's 35 existing methods were
rerun. Its sole change is the test field `exportSetupHash` becoming `internal`;
reversing that visibility edit reproduces the complete original parent bytes.

## State and evidence boundaries

The exporter authenticates the actual setup and pre-call delta with their
emitted Keccak hashes. Restoration merges storage by slot, including explicit
zero overrides, and verifies the actual production graph's runtime hashes at
the pinned RPC block. It materializes existing exact code only. The executing
test harness can be absent from Foundry's dump; its hash/length is recorded and
no production descendant calls the omitted harness. The event's `pre_state`
digest is retained metadata, not a recomputed hash of the restored whole VM.
An activation event's pre-write bucket is zero; the new bucket is resolved from
the actual Vault trace, never assumed to be zero.

Compact exact Forge method results with all logs, actual RPC records and fixture
hashes are retained below. Duplicate full Forge traces and labeled bytecode
dumps remain byte-identical in the external archive, with original hashes;
the compact public method files do not pretend to contain those full traces.
[GAS.json](GAS.json) distinguishes unit-call gas from RPC estimates and trace
gas. [TEST_SCOPE.json](TEST_SCOPE.json), [SOURCE_SNAPSHOT.json](SOURCE_SNAPSHOT.json)
and [EXECUTION.json](EXECUTION.json) record scope and reuse;
[ARTIFACTS.json](ARTIFACTS.json) hashes this public package.
[EXTERNAL.json](EXTERNAL.json) identifies the larger local setup/delta/genesis
archive without requiring it for the portable recorded-response check.

All ten captures used producer v1, which inherited its Python environment.
Environment names/values were not inspected or logged; this is not a claim of
credential-free inheritance. Its actual Anvil commands used `--accounts 0
--silent`, explicit local arguments and a read-only RPC allowlist. Future v2
adds a child-environment whitelist; successful cases were not rerun for hygiene.
[PRODUCER_STAGES.json](PRODUCER_STAGES.json) keeps those versions separate.

## What this does not qualify

The fixture uses controlled feeds (ETH is $1), synthetic funded venue depth,
test authority/admission/Permit2 seams and a direct-mint setup. Its pool minimum
is $1 while global activation/growth minima remain $100/$5; a stronger admitted
pool minimum can still reject growth. This does not approve real ETH or ZZZ
sources, actual selected-pool depth, routes, VRF, SeaDrop/mint2 onboarding,
production authorities, a complete deployment inventory or a live provider.

The four contribution captures are separately replayed by the backend evidence
through the production marginal-LP reader and gas helpers. The six maintenance
captures establish actual keeper-call execution; they are not full admission
of every manual governance C/D action. No extra historical header is fabricated
to satisfy a different manual helper's response contract.

Recorded gas price, funded balances and `reviewed_fee_wei` establish local
execution affordability only. The last field is calculated padded gas cost,
not an operator-approved production spending ceiling. Actual target-chain
posting fees, live gas-price ceilings, daily budgets, provider reliability,
four-bucket/large-cohort workloads and independent approval remain separate.

Run `python reports/gas-profiles-20261113/evm/verify.py` for offline artifact,
source and recorded-response reconciliation. It starts no node, compiler or
test suite and makes no network calls.
