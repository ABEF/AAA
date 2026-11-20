# Supplied-pool Entry and NFT integration

20 November 2026. **Four current Entry contributions passed** on a new isolated
fork at block119107223/hash
`0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335`.
The supplied ETH/ZZZ pool remains the test target; final launch selection is
deferred. This is finite integration evidence, not production approval.

## New scope

The new fixture constructs the normal F6 graph using the unchanged, source-pinned
constructor runner:25top-level CREATE transactions,19bindings and39instances.
Those44transactions are necessary setup for this composed Entry test, not44new
constructor test cases or a rerun of the earlier constructor acceptance suite.
All100normal source pins and trusted build-file digests are checked against the
`activation-final-six-20261118` artifacts. No production compiler or contract
source changed.

Unlike the earlier typed-custody physical-LP partition, this run uses real normal
Access, Registry, Entry, Vault, NFT, Membership, Rewards, Fees and Manager modules
against the actual inherited core, PositionManager, StateView, Permit2 and ZZZ.
The production bounded balancing catalog has one configured test venue: the
supplied pool. The real Entry calls exercise that production placement/routing
path and actual Uniswap mint/increase, rather than substituting an external
test-trader swap for the production path.

There are two NFTs, both owned by the same disposable local account. The sequence
is ETH activation, ZZZ activation, ETH growth and ZZZ growth. The two activations
each supply about110USD at the fixed fixture marks; growth supplies about20USD.
Those values exercise the governed100USD/5USD minima without changing them.

## Results and independent saved-evidence checks

| Operation | Estimated gas | Full20% envelope | Actual gas |
| --- | ---: | ---: | ---: |
| ETH activation |10,587,724|12,705,269|10,255,624|
| ZZZ activation |10,975,926|13,171,112|10,335,526|
| ETH growth |9,418,190|11,301,828|9,007,090|
| ZZZ growth |9,883,458|11,860,150|9,288,458|

Every contribution passes the existing32M ceiling with complete20% padding.
These are finite two-NFT, one-main, native-royalty-only observations; they do not
replace the maximum-state gas evidence or close its remaining cold shortfall.
Transaction gas is not a complete Robinhood fee quotation.

The [saved-evidence verifier](verify_entry.py) and
[verification result](VERIFICATION.json) confirm:

- The exact reviewed/submitted/included contribution envelopes and receipts.
- Manager balancing receives only the entrant's source ETH or ZZZ. Its returned
  amounts exactly match the subsequent main mint/increase budgets; actual spend
  stays inside those budgets. Existing idle or compound cannot supplement those
  captured placement budgets.
- Every contribution retains the caller's3% maximum. Lower-input and upper-input
  event values match independent floor/ceil valuation; the stronger upper-input
  marginal-deployed and net-NAV floors hold. Equal feed answers can still differ
  by one raw USD unit after floor/ceil rounding.
- All three NAV marks reconcile to actual Manager principal amounts and Vault
  idle, independently valued at the fixed fixture feed marks. The incumbent
  denominator includes repriced principal, earlier idle and freshly released
  compound. Issued shares equal net added NAV initially, then the floored
  proportional issuance; exact stored totals equal both NFT shares and the
  Rewards allocation-tree weight.
- The second activation and both growths retain the same main LP ID, ticks,
  centre and rebalance clock. Physical main liquidity increases; no residual is
  created. The unaffected NFT's shares remain unchanged.
- Both activated NFTs acquire Membership and royalty enrollment once, and
  newly activated NFTs receive no previously accrued LP reward. Owner and
  Vault custody checks, zero Entry balances and reviewed ERC20 approval resets
  pass after every contribution.

The independent review additionally verifies1,916 immutable request hashes,
all91 transaction/receipt identities and gas envelopes, and the four trace/event
replays. Three positive `FeesAllocated` events occur during the contributions.
This report does not claim a complete fee-ledger or royalty payout qualification.

## Explicit fixture seams and limits

The original selected pool has zero active liquidity at the recorded public
anchor. Three test-only `Source9DepthSeeder` instances supply synthetic external
core liquidity, outside PoPL principal and share accounting. Each helper proves
unchanged pool price/fees, bounded exact funding and unused refunds. This is not
evidence that independent market depth is available publicly.

ETH and ZZZ balances are substituted only on the owned local chain. Two fixed
feeds per asset deliberately use correlated answers; the four addresses do not
qualify independent price sources. Their answers are not refreshed to spot to
make a trade pass. The archived exact SeaDrop runtime and guard default are
locally materialized, and controlled VRF callbacks finalize the two NFT draws.
This does not qualify OpenSea onboarding, a live custom Merkle mint path,
randomness cryptography, funding or service reliability. The illustrative
constructor artwork URI is not immutable-content availability evidence.

The new local Access is sealed once solely to exercise normal Entry/module
authorization in this disposable fixture. [The captured proof](LOCAL_SEAL.json)
records its fresh address, PID, port and successful receipt. No existing or
public Access is called, deployed or sealed. The fixture uses one main physical
LP only, two NFTs owned by one account and native ETH as the sole admitted
royalty currency. Optional hybrid,1,000-NFT/64-currency states, multiple wallet
concurrency, real independent prices/depth, provider capacity, complete fees,
marketplace operation and production approval remain separate.

## Execution and preservation

One bounded attempt completes in307.719seconds. There are47setup/scenario
receipts, including the four contributions, in addition to44constructor/binding
receipts:91successful local transactions. The relay makes148public read-only
HTTP posts, all returning200, with108cache hits and no retries. Two non-admitted
startup requests are rejected locally; their method details are not captured,
so this is not a claim of zero rejections. No allowlist is expanded to pass them.
The authenticated145-entry prior cache is imported; new entries are retained.

The process is bounded by a1,020-second Windows kill-on-close job and uses a new
loopback listener with per-mutation PID checks. Owned PID10920/port54717 stops,
with no pending transaction. Its final state export is an isolated test artifact,
not a protocol checkpoint or permission to restore another node. Existing
Anvil8902, NFTs/LP/balances, journals, live services/sites, signer restrictions,
production authorities and the user-paused heartbeat stay unchanged.

No unchanged tests or contract/browser suites are rerun. Independent checks use
the saved wire/traces, not another EVM execution. Source publication does not
authorize any live rollout. [Archive and exact member hashes](EVIDENCE_MANIFEST.json)
preserve the attempt, imported tools, supervisor and verifier source bytes.
