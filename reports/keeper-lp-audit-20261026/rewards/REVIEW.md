# Reward, conversion and keeper metadata review

Reviewed 26 October 2026 against initial main `9fe9997`. This scope covers
`keeper/royalties.py`, shared range/Position/static-ABI helpers, FeeController,
Rewards, Membership, LP/royalty converters, RoyaltyRewards, V4RouteExecutor and
Buyback. Exact read-source hashes are in [source bindings](source-bindings.json).
Parent reviews own Vault/venue/strategy/custody and common keeper signing/state.
This is an internal source review, not an independent audit or production approval.

## Confirmed defect and minimal fix

The conversion worker read the converter's `enabled()` and v3/v4
`routeEnabled(bytes32)` as unsigned integers and treated **every value except 1**
as a legitimate disabled control. A correctly sized but noncanonical Boolean 2
or uint256 maximum therefore returned ordinary no-work, without the existing
`*_conversion_deferred` outcome or increased blocked-action count. A corrupt
core observation could masquerade as healthy governance shutdown.

This is an operational integrity/observability defect. It did not bypass a
swap minimum, authorize signing or alter holder accounting. It could hide why
conversion stopped and leave the operator with an unjustified healthy cycle.

The worker now accepts only 0/1 in those specifically Boolean getter slots.
Zero retains its intentional off behavior; one retains the original exact batch,
output floor, gas ceiling and submission path. Other values raise the existing
`RpcError`, so common conversion handling records a deferred/blocked action and
the existing cycle health logic can report degraded. No new policy, event,
configuration/journal field, route, source asset or signing path is introduced.

`isAsset()` already rejected any value other than 1. Numeric caps, counters and
route-kind getters retain their separate numeric validation. This patch does not
reinterpret every uint getter as a Boolean or change the generic ABI codec.

## Focused evidence

The [new regression module](../../../tests_python/test_keeper_conversion_integrity.py)
composes actual Keeper and RoyaltyAutomation with injected byte-level RPC and
temporary state files. It covers both LP and royalty ledgers under historical
`v3_wrapper`, governed `v3_wrapper_configurable`, and `v4_native` profiles.
The governed fixture configurations explicitly select accounting 3/fee-intake 1;
their synthetic markets/providers are not Robinhood qualification.

| Capture | Actual result |
| --- | --- |
| [Before](before.json), [log](before.log) | 5 methods;18 assertion failures across 2 methods (6 malformed-enable cases and 12 malformed-route cases), 0 errors. Three positive control methods pass. |
| [After](after.json), [log](after.log) |The same 5 methods pass, with unchanged source inputs during the capture. |
| [Original implementation](royalties-before.py.txt) |Exact source preimage preserved; no failing evidence overwritten. |

Controls establish that legitimate 0 stays off, legitimate 1 retains the exact
IDs/calldata minimum/deadline and maximum-cost argument, and actual claimable
transport failure retains the separate existing deferred path. No method signs,
broadcasts, opens a network listener, calls a live RPC or changes an existing
database/journal/Anvil service. Earlier unchanged suites were not repeated here;
the parent final affected sweep owns any broader combined verification.

Final owned hashes:

- `keeper/royalties.py`: `7354c3187d8aad49bbfef7debe4fed7c9cecd4e484178470580559756175ccb9`
- `tests_python/test_keeper_conversion_integrity.py`: `f8786830e8581e1da779ba2523e1f066fb9ce6082d81bc84b2146b7ff5cc7223`

## Financial source trace and retained safeguards

| Boundary | Source observation and conclusion |
| --- | --- |
| Local fee intake | FeeController requires the bound Vault, active bucket/pair and exact declared native/ERC20 receipt. Twenty raw units allocate 16 individual / 2 collective / 1 compound / 1 buyback. Sub-20 receipts carry; incumbent dust settlement is individual-only. Reserve/claim backing is not split twice. |
| Share and collective weights | Rewards uses independent owner-share indexes and equal eligible-NFT collective indexes. Membership checkpoints before its one eligibility share exists; a top-up does not create another membership. The separate Vault review confirms owner checkpoints precede share writes. |
| Fractions and liabilities | Per-NFT fractions carry through checkpoints/claims; global index-division residue stays reserved. The recorded liability is not an exact sum of immediately payable whole units and is not a sweepable profit. No new dust redistribution was added. |
| Ownership and callbacks | Current owner authorization and id-bound ledgers preserve unclaimed rights across transfers. The ledger mutex covers funding/index changes and claims/conversion. FeeController stays locked across approval→credit→approval reset; ExactToken checks both transfer endpoints. A payout callback may transfer the NFT before its claim event without double-paying its ledger balance. |
| LP conversion | Only checkpointed whole units of the selected NFTs' individual/collective balances are debited. Exact source decrease and native increase are verified. Cumulative output rounding conserves every output wei across the same IDs and both LP components. Source fractions remain in their original currency; native credits do not enter indexes again. |
| Royalty conversion | Actual pending receipts sync before selecting balances; older eligible cohorts retain earlier receipts before waiting activations join. Rarity weights affect royalties only. Source and ETH liabilities/accounted balances change by the actual debit/credit, with cumulative per-NFT rounding and no new income event. Native custody blocks creating unbacked native conversions. |
| Converter execution | Current shared converter enforces enabled/lifecycle/keeper authority, exact source funding, a current Oracle floor and stronger caller minimum, temporary exact approvals and native settlement. An unused wrapper cannot block an explicit native-v4 route. V3 wrapper policies retain their separate reviewed runtime/implementation boundary. |
| Typed v4 helper | Immutable parent, static hookless ordered key, source/output/manager/view runtime pins, initialized pool and exact signed deltas. Exact funding, callback identity/hash, output and final parent balance changes reject prefund subsidy or leftover balances. This is source evidence, not a new live-Core rehearsal. |
| Buyback | Immutable ZZZ target, upper-marked operating spend bound, actual fee-reserve release, pair/swap guard and exact total-supply/balance burn checks. A reserve allocation alone is not proof the burn executed; actual ZZZ burn semantics remain unqualified. |
| Keeper batches and pricing | A conversion scan selects at most 32 ordinals, resolves actual token IDs, sorts/deduplicates them, reads claimable at one confirmed hash, validates bindings/profile/route/runtime and computes the same ceiling-rounded output floor. Common submission re-simulates before a bounded signing decision. A scan cursor is not a claim ledger or a guarantee of immediate conversion. |
| Range and Position helpers | Explicit versioned Position lengths/statuses reject removed-field assumptions. Accounting3 local identity relies on authenticated caller chain/Vault/module checks, rather than invented remote fields. Reviewed range metadata binds orientation/configuration, permitted 25/50 widths, policy cooldown and target; no arbitrary keeper-selected algorithm is added. |

No concrete Solidity fund/accounting defect was established in these reviewed
paths, so none was edited and no unchanged Solidity suite was rerun for this
Python-only correction. This is not a claim that all attacks are impossible.

## Remaining limitations and release gates

- Qualify actual independent ETH/ZZZ sources, sequencer/update policies, native
  market depths and conversion routes. At the current default 1% conversion cap,
  the selected pool's recorded effective fee alone is too high; a cheaper
  reviewed route is still required. Matching source code cannot create it.
- Current governance can set the existing bounded operating caps. A keeper's
  captured stronger raw minimum stays stronger; this fix does not widen any cap.
  The user selected per-operation limits only, not a cumulative loss guarantee.
- Price moves, competing holder claims, governance changes and MEV after final
  simulation can make a transaction revert or make maintenance uneconomic.
  Gas budgets, deadlines, nonce/receipt recovery and alerts remain necessary;
  ordinary simulation does not eliminate that interval.
- Token issuer upgrades, tax/rebase/pause behavior and a broken historical token
  can block exact transfers or funded dust settlement. Source-level exact balance
  checks cannot establish benign future token behavior. Do not skip funded dust
  or substitute another holder's assets to restore liveness.
- External royalty currencies need deliberate admission, verified runtime/units
  and a qualified route. Unknown currencies at a retired receiver have no rescue.
  Current native custody needs authenticated full return and normal sync; moving
  LP alone does not move NFT ownership/reward ledgers to another chain.
- Batch/scan/request bounds do not prove target-chain maximum-state gas,
  throughput, current-profile extension acceptance, monitoring reliability or
  off-host restore. Provider, operating and realistic economic rehearsals remain.
- Supported VRF, OpenSea primary mint, production authorities, artwork hosting,
  whole-release qualification and independent audit/remediation remain open.
