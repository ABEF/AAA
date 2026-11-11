# Higher-budget qualification remains separate

The final controlled cold Entry fixture measures15,317,541gas for native ETH
and15,644,361gas for ZZZ. Full20% headroom requires18,381,050 and18,773,234.
Default12M therefore rejects; original failures are retained. The existing
optional activation policy2 can be exercised in an isolated higher-budget
simulation without enabling or raising any production/default configuration.
Neither a32M local diagnostic nor these measurements establishes a universal
maximum or actual target-chain cost. Routing depth/count, input size, callbacks,
state and token behavior matter.

Subsequent true-owner local RPC estimates require17.18M–18.93M with full20%
headroom. All four exact calls succeed at those reviewed limits, as well as the
separate32M simulation cap. [Case evidence](backend/rpc-cases.json) distinguishes
trace gas, estimate, reviewed envelope and default rejection. These are still
local synthetic-market diagnostics without Robinhood data-fee qualification.

Before selecting a production budget, qualify BOTH block and transaction limits,
actual RPC simulation/estimation limits, full20% headroom, complete network-fee
semantics and matching consumers. The existing policy2 mechanically checks the
confirmed block limit; it does not discover every chain-specific transaction
ceiling. Configuration review must establish those additional limits rather than
assuming the block header is sufficient. A source guard is not weakened when a
budget is rejected.

An insufficient whole-operation budget can appear as a bounded dependency's
price/read failure rather than an outer out-of-gas message. Preserve the exact
trace and reject the review; do not assume that such an error proves a faulty
feed or respond by widening price/loss limits. The controlled same-call higher-
budget comparison diagnoses this fixture only, not every provider failure.

Robinhood's [official fee guide](https://docs.robinhood.com/chain/gas-and-fees/)
describes execution plus Ethereum data fees in its estimates. A local Anvil
estimate cannot qualify that total. Offchain's [current gas-info interface](https://github.com/OffchainLabs/nitro-precompile-interfaces/blob/main/ArbGasInfo.sol)
distinguishes accounting/block parameters and the version-dependent transaction
limit getter. Verify the actual chain/version and supported method; do not infer
a current transaction cap from an old interface or interpret the third accounting
word as a transaction limit.

A bounded anonymous read was attempted against the [documented mainnet RPC](https://docs.robinhood.com/chain/connecting/)
on11November2026 at04:27:51UTC. Its first `eth_chainId` request returned HTTP403.
No valid chain/header/gas/precompile response was obtained, so no target limit or
fee result is claimed. The restriction's cause is unqualified; it is not evidence
of chain downtime. No credentials, signing, public transaction or service change
was used. [Exact observation](gas/read-only-chain-gas.json).

The recommended next step is to qualify the existing higher-budget policy with
a reviewed provider and exact release/operation graph. Retain the12M default,
financial limits, user fee ceiling and explicit failure until then. A change to
an installed budget or public signing is not authorized by this source report.
