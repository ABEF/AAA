# Maximum-state LP conversion and claim qualification

20 November 2026. Baseline main: `f1713c1b0b3005f6367943ceb88219cae7b786aa`.
Trusted normal source: `activation-final-six-20261118`, Factory6/allocation2.
**Production is undeployed and NOT APPROVED.** One backend efficiency fix is
described below. Solidity, financial guards, gas defaults, authorities, journals,
existing chains, websites and running services remain unchanged.

## What this work checks

Reuse the authenticated maximum-workload export containing 1,000 activated NFTs,
64 ERC20 royalty currencies plus ETH and a funded main/residual. Do not repeat
the unchanged producer, 999 Entry activations, normal compilation/size checks or
old test suites. The new [plan](PLAN.md) targets separate same-NFT LP settlement,
current-owner claims, partial batches, fault isolation and resource admission.

LP fees are recorded as earned ETH and the fixed fixture ZZZ. Conversion spends
only selected whole ZZZ entitlements and credits measured ETH to the same NFTs'
individual/collective components. Royalties remain in their original currencies.
Neither operation creates income or spends principal/compound/buyback backing.

## Confirmed backend improvement

The32-entry mixed unsigned planner exceeded its existing25-second request bound.
An offline replay of its exact captured RPC data, without network latency, spent
18.094seconds overall:568 `_code` verifications cost16.372seconds. Cached runtime
bytes were repeatedly Keccak-hashed for each trial and final preparation.

`frontend_api/claim_planner.py` now reuses only successful exact runtime proofs
within one request, for the same admitted target, expected hash and canonical
EIP1898 block. The normal verifier runs on every miss. Failures are never cached;
512 is still the metadata ceiling. Deadline/global-error checks remain active on
hits. No proof survives into another plan. Owners, balances, lifecycle, heads,
simulation, estimates, fees and final freshness/canonicality remain checked.
`service.py`, transaction preparation, checkpoints and gas policy are unchanged.

Nine new focused methods pass, including actual hash rejection, changed
target/pin/block/read shape, transport/deadline faults, bounded caching, request
isolation and owner changes during final preparation. No unchanged test method
or contract/browser suite was rerun. Source publication changes no running API.

Exact captured-RPC replay falls from18.094seconds to6.031seconds with the same
903 RPC reads. Actual hashing/verifications fall from568 to71. This is a finite
offline CPU comparison, not a provider or end-user latency guarantee. The
[before/after records](planner-performance/MANIFEST.json) preserve both source
scopes. The original nine-test invocation was observed once; its receipt honestly
states that an independent raw stdout file was not captured.

The [new function inventory](FUNCTION_INVENTORY.json) retains all1,021 ABI rows,
1,056 implemented Solidity definitions and original61/39/4 normal build pins;
only `claim_planner.py` changes among179 production Python files. There are now
1,977 named Python definitions, one more private helper. The old inventory and
report remain untouched; the normal verifier selects this new exact inventory.

## Cold gas measurements

Each row is a new separately simulated/estimated EVM transaction on a controlled
snapshot. Views before it do not warm a later transaction. Admission uses the
estimate plus full padding, never receipt gas in place of the estimate.

| New selected operation | Cold estimate | Full padding | Outcome |
| --- | ---: | ---: | --- |
| Convert 1 NFT | 2,020,746 | 2,525,933 | Fits24M/full25% |
| Convert 8 NFTs | 7,142,747 | 8,928,434 | Fits24M/full25% |
| Convert 16 NFTs | 12,290,506 | 15,363,133 | Fits24M/full25% |
| Convert 32 NFTs | 19,966,538 | 24,958,173 | Refused;24M ceiling unchanged |
| Claim 1 unsettled LP-ETH entry | 1,040,946 | 1,249,136 | Fits12M/full20% |
| Claim 8 unsettled LP-ETH entries | 6,130,061 | 7,356,074 | Fits12M/full20% |
| Claim 16 unsettled LP-ETH entries | 11,380,799 | 13,656,959 | Refused;12M ceiling unchanged |
| Claim 32 unsettled LP-ETH entries |12M simulation refuses|Not admitted|Opaque execution refusal retained |
| Claim 8 converted-direct LP-ETH entries | 1,233,014 | 1,479,617 | Fits12M/full20% |
| Claim 8 pending-royalty entries | 1,042,625 | 1,251,150 | Fits12M/full20% |

These are state-specific measurements, not universal safe batch sizes. Thirty-two
is the contract selection ceiling. Smaller freshly prepared batches retain every
remaining entitlement; do not raise gas caps or clip padding to approve a row.
Claims use an explicit report-only policy2 configuration at the unchanged12M
ceiling to demonstrate full20%. Legacy policy1 defaults/semantics are unchanged.

## Actual continuation and independent reconciliation

| Evidence stage | Actual result |
| --- | --- |
| [Main matrix03](campaign03/SUMMARY.json) |39 operation records:28 mined,11 refusals. Accounting/transfer/fault checks pass; the original unsigned planner times out. That failure remains in the original record. |
| [Targeted completion04](campaign04/SUMMARY.json) |10 mined operations, no failures; only the missing prefix/suffix and optimized planner continuation run. The completed matrix is not rerun. |
| Independent captured-wire check |17 financial assertions,2 ownership observations and5 full financial rollback snapshots in03;4 financial assertions plus conversion/planner continuation in04. These are offline checks of the same EVM evidence, not additional test transactions. |
| New focused Python methods |9 passes at the changed planner source, separate from the controlled EVM cases. No unchanged method/suite rerun. |

The [published matrix verification](PUBLISHED_ACCOUNTING_VERIFICATION.json) keeps
the original planner failure visible. The [published completion verification](PUBLISHED_COMPLETION_VERIFICATION.json)
closes that exact gap at the changed planner source, without relabeling03.
Four [new offline rejection controls](EVIDENCE_CONTROL_CHECKS.json) reject reduced
padding, altered recipient balances, an LP/royalty ledger mismatch and a forged
capture-root mapping. They execute no EVM and modify no captured evidence.

Every state capture reconciles all1,000 NFTs' whole individual/collective LP
rights to liabilities and backing. Vault shares/group, both physical LP IDs,
ticks/liquidity/custody, all65 royalty books and classified fees remain checked.
Selected conversion reconstructs each integer component using measured output
and independently captured1% quote/caller floor. No unselected NFT, principal,
compound, buyback, orphan or forced external converter/executor prefund pays for it.

Transfers before conversion and before claim carry unpaid rights to the new
owner; former-owner claims refuse. Explicit raw-ZZZ recovery consumes those
rights before conversion, without a second payout. A selected royalty currency
with a deliberately failing **balance read** reverts the mixed claim atomically;
the fresh healthy subset succeeds, and repaired original-currency rights pay
once. This does not qualify every possible transfer-tax/rebase/blacklist/callback
or untransferable-token failure mode.

Following the32-conversion padding refusal, a new16-prefix plus16-suffix series
drains exactly those32 source entitlements. The first costs15,363,133 padded;
the freshly priced suffix11,219,193. Both retain24M/full25%. A split operation
need not have the same output or rounding as a hypothetical single swap. The
captured continuation's unfortunately named
`not_equal_to_hypothetical_single_swap` field means **no single-swap equivalence
was asserted**; no hypothetical swap was executed or numerical inequality proved.

After the planner fix, the actual32-entry mixed selection publishes24 entries
after six bounded trials plus a fresh final preparation:9,780,043 estimated,
11,736,052 padded. Confirmation precedes a fresh remaining8-entry plan:
3,748,706 estimated,4,498,448 padded. Both stay12M/full20%; the respective request
counts are903 and319 within1024. Replanning all original32 returns zero balances,
no next transaction and no simulation trials. No entry disappears or pays twice.

The first903-read result is **under the documented admission seam**. It is not
proof that adding the entire normal deployment admission will fit the remaining
request allowance. Full endpoint/profile admission still needs its own current
graph rehearsal; do not raise bounds or silently skip those checks to adopt this.

## Original attempts and reproducibility

All four owned nodes stop. Early [attempt01](campaign01/SUMMARY.json) stops before
the financial matrix because a new report-harness read omitted `from`, invoking
a mock's deliberate zero-caller fault. [Attempt02](campaign02/SUMMARY.json) stops
before that matrix because its test-prefund sender lacks13wei. The corrected
fixture uses an explicitly funded disposable actor, no balance override. Neither
attempt is a contract failure, financial pass or rerun of the completed matrix.

Published campaign manifests preserve original bytes, source snapshots,
simulations, estimates, transaction envelopes/hashes/receipts, headers, raw RPC,
states and assertion links. Reproducible36MB genesis copies stay in the external
archive; their hashes remain in each fixture record, and the original source
population/export is separately retained. The checker rebases absolute original
capture paths only through each explicit publication manifest and validates hashes.
No key or credential is required or published.

## Fixture and qualification limits

The reused population was minted through mint2 and funded through actual Entry
calls against actual local Uniswap code. It retains its original mocked
Access/Registry/feeds/VRF/Permit2, two holding addresses, controlled prices and
synthetic external depth. It is not evidence for 1,000 distinct signers or real
token transfer behavior. The prior producer's all65-currency payout proof remains
source-scoped; the new campaign does not repeat its entire drain.

The export did not bind a converter. A new owned-chain **test-only MockAccess
bootstrap** installs the unchanged normal-build native-v4 converter and restores
the mock seal. Exact creation/runtime/child evidence is retained. Real Access has
no unseal function. This does not qualify sealed-deployment converter rotation.
Small explicit external converter/executor prefunds and two original-currency
receipts are fixture funding, not newly invented holder LP rewards.

The unchanged planner uses real EVM balances, owners, asset metadata, simulations,
estimates, fee/funding and canonical snapshot checks. Its **complete production
deployment/profile/lifecycle admission is explicitly replaced by a fixture seam**;
the mock graph cannot establish that proof. Local fee declarations do not qualify
Robinhood complete fees. No endpoint, wallet or running configuration is adopted.

Current-market independent sources, a real1%-eligible LP conversion route,
complete provider fees, full production API/profile admission and matching
consumer/operating acceptance remain open. The separate maximum-state slow-ZZZ
opening contribution still exceeds32M/full20%; this work does not fix it.
Independent security/release approval remains required.
