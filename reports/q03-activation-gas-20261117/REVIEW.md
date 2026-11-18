# Q03 — Activation gas optimisation near collection capacity

Completed 18 November 2026; campaign started 17 November. Baseline main:
`23be8c9b01211b0732b2bcb64c227f0e05151e0a`. Current trusted build:
`q03-allocation-20261117`. Internal review; **production NOT APPROVED**.

## Result and remaining limit

Meaningful source improvements are implemented, with no budget increase or change
to NFT entitlements. Four demanding unsynchronised activation states still fail
the strict20M policy. Q03 therefore remains open for unrestricted maximum-state
and selected production-currency/provider qualification.

The existing optional operator synchronisation workflow was separately checked
after999 actual activations: a fresh healthy activation fits at19,484,950 gas
including full20% padding; with one deliberately unreadable currency it fits at
19,877,529. ETH and ZZZ growth fit too. These are conditional controlled-state
results, not a guarantee against receipts arriving between synchronisation and
transaction inclusion. No extra required holder transaction or worker was added.

## Implemented changes

1. **Same exact units, fewer royalty writes.** Large remainders use complementary
   range credits: allocate the upper quotient to the eligible prefix and subtract
   one from its small excluded interval. Rarity1/2/3, GCD normalization, rotating
   cursor, cutoff cohort, deferred currency rights and current-owner claims remain.
   Internal coefficients wrap modulo2^256; token balances and economic liabilities
   do not. Private `_distribute` reserves the checked same-currency global liability
   for all four credit paths. Each ticket take is bounded by remaining liability;
   checked aggregate claims, backing debits and exact transfers remain.
   [Mathematical/caller review](global/GLOBAL_BOUND_REVIEW.md).
2. **Reuse only genuinely adjacent price proofs.** Manager and Pricing omit full
   duplicate source validations when only static reads intervene after an
   authenticated begin or before the retained final proof. A zero-token pull makes
   no external token call. Nonzero transfer callbacks, actual swap proofs,
   public context reads, source/control revisions and final checks remain guarded.
   No global cache, keeper-selected price, new bypass or financial relaxation.
   [Boundary review](VALIDATION_REUSE_REVIEW.md).
3. **Explicit immutable payload identity.** Fresh schema17 opts into
   `factory_payload_version:4`; code-storage FORMAT2, canonicalV10, royalty4 and
   reporting5 remain. Exact payload4 creation is25,549 bytes, hash
   `0xb72393fbf136d2d75526d655fcb8c51c77de65b18d68a6084072b6dc436d88b5`.
   Omission/3 retains historical payload3. Mixed/unknown/Boolean selections refuse.
   One selected identity drives preflight bindings and observations. Old examples,
   runtimes and journals are not relabelled. [Consumer review](PAYLOAD4_CONSUMER_REVIEW.md).
4. **Current preparation and operator reference.** The unsigned planners use the
   exact current normal build; old builds stay explicitly registered. All40
   concrete contract ABIs,964 callable entries and1,017 reviewed example rows are
   unchanged; only the function reference's source snapshot changed. No calldata,
   permission or economic input was silently altered.
   [Reference review](OPERATOR_REFERENCE_REVIEW.json).

Four Solidity files change: RoyaltyRewards, its internal allocator, Manager and
ContributionPricing. No new contract/helper, storage slot, recipient, authority,
public ABI or canonical wire field is added. Mapping-only storage and flat
canonical rights remain identical. No hot upgrade or raw historical-book import
is claimed. Fixed80/10/5/5 LP allocation is independent and unchanged.

## Cold complete-flow measurements

These are newly owned account-free loopback Anvil calls. Full20% uses the actual
estimate, rounded upward, then the exact padded call must succeed. Trace execution
gas is a different quantity and is never substituted for that review. A successful
32M diagnostic is still a failed20M profile. Gas price and target fees are not
qualified by these local nodes.

| Controlled state | Old cold trace | Current cold trace | Estimate | Full20% |20M policy |
| --- | ---: | ---: | ---: | ---: | --- |
|999 active; initial opening allocation, ETH entry |21,470,885|20,048,633|Refused|—|Fail |
|999 active; rotated receipts, ZZZ entry |27,998,079|20,641,239|Refused|—|Fail |
|999 active; rotated receipts, one faulty currency, ETH |28,039,075|20,652,507|Refused|—|Fail |
|999 active; rotated receipts, ETH entry |27,769,561|19,995,412|Refused|—|Fail |
|1,000 active; ETH growth |12,985,190|11,800,050|12,469,850|14,963,820|Pass |
|999 active; previously synchronised, ETH entry |Not rerun|14,912,980|16,237,458|19,484,950|Pass |
|1,000 active; previously synchronised, ZZZ growth |Not rerun|12,443,727|13,220,627|15,864,753|Pass |
|999 active; healthy currencies synchronised, one faulty, ETH |Not rerun|15,868,807|16,564,607|19,877,529|Pass |

Rotated cases save7,356,840–7,774,149 traced execution gas, about26–28%; opening
saves1,422,252. The failure rows still require more gas than this exact reviewed
envelope permits. Even a trace slightly below20M does not establish a20M estimate
or its mandatory margin.

[Machine results](final/RESULTS.json) · [All eight original case records](final/rpc/SUMMARY.json) ·
[Five-case source baseline](baseline/BASELINE_RESULTS.json).

## What the full flow actually verifies

The producer really mints1,000 NFTs through pinned SeaDrop code and performs999
prior Entry contributions. Stock is599 Commun/300 Rare/100 Legendary active plus
one dormant Commun: actual total prefix weight1499, then1500. It uses current
Entry/Vault/LP/Rewards/Membership/Royalty code and actual v4 core/periphery, with
explicit controlled authority/registry, ETH publications, VRF, Permit2 and external
depth. There are two holder addresses and one physical main LP, not1,000 distinct
wallets, an LP2 stress test or qualified live services.

Sixteen admitted6-decimal ERC20 royalty currencies plus native ETH are present.
The fault consumes the existing1M isolated allowance. Inputs use native ETH or
the fixed18-decimal ZZZ. The checks verify:

- At least97% actual marginal deployed LP; net-NAV share issuance includes
  incumbent idle and designated compound. Existing shares, main ID/ticks/centre
  and rebalance clock remain unchanged; entrant approvals/prefunds are exact.
- Rejected calls roll back principal, shares and royalty state. The32M call only
  permits diagnostic accounting assertions; it never approves a higher budget.
- Old pending2996 units per currency go to the correct earlier1499 tickets.
  The newcomer gets zero past units, including after faulty-currency recovery.
- All999 prior NFTs and the new NFT then claim through real owner paths across
  all17 currencies. A further1500-unit receipt pays1499 old/one new unit.
  Every balance, accounted liability, opening/pending/orphan category drains to
  zero where expected; repeat claims pay zero. LP backing remains separate.

[Final producer scope](FINAL_FULL_FIXTURE_SCOPE.json) ·
[Actual producer outcome](final/full-flow-01/EXECUTION.json).

The aggregate historical-setup/export harness uses a10B test gas limit and512MiB
memory for its large unmetered setup and state serialization. These are **only
harness resources**. Each measured Entry remains capped20M, the diagnostic32M
stays separate, and all independent RPC nodes have32M block gas. They cannot be
used as production configuration or evidence of relaxing the20M budget.

## Verification and rejected alternatives

- Two current full-flow methods pass; the first is re-executed because production
  dependencies changed, the second adds the bounded pre-sync/ZZZ-growth states.
  Baseline trace-control success is reused, not rerun. Eight cold final RPC cases
  and five baseline cases are workflows, not13 additional test methods.
- Five actual royalty integration methods pass at baseline and changed-source
  stages: homogeneous-to-mixed rights, cutoff/fault/transfer, funded flat import,
  funded abort, and repeated UINTMAX payout cycles. They are five distinct methods,
  not ten. [Integration scope](INTEGRATION_TEST_SCOPE_FINAL.json),
  [final execution](integration/candidate01/PUBLICATION.json).
- Five distinct new validation-boundary methods pass, with two successful cases
  reused and three corrected/new cases executed later. Their exact source stages,
  including the pre-Royalty-port compile, remain explicit; source changes outside
  their compiled closure do not become whole-current-graph approval.
  [Case registry](validation-reuse/VERIFICATION.json).
- Thirteen new allocator-model methods retain separate prototype scopes:
  counter4, selected global-bound5, rejected envelope4. A second per-book counter
  was not adopted. The envelope alternative passed its maths cases but exceeded
  EIP170 by224 bytes and materially increased some cold claims; it is rejected.
  [Method index](ALLOCATOR_METHODS.json).
- Seventeen selected Python methods pass:11 new payload/consumer/planner checks,
  three corrected current-build expectations, three corrected historical-schema
  fixtures. No unchanged old suite was rerun. Old schema16/F3 and14/F2 retain their
  own meaning. [Final consumer evidence](consumer/final01/PUBLICATION.json).
- Final actual02 normal compilation and strict reference import pass:100 closed
  sources, four build-input bindings, all48 runtime/initcode gates, identical
  prepared/actual compiler bytes and identical public ABI/semantic storage.
  Royalty24,551/25 bytes headroom; Manager24,537/39; Vault24,544/32;
  Oracle24,573/3. Access constructor with its96-byte arguments leaves748 bytes.
  [Admitted build](build/current/README.md).

Original compiler/setup/fixture failures and false preliminary attestations are
preserved, not called passes. These include setup seeding/slippage diagnostics,
aggregate harness resource failures, a transient incomplete source write seen by
a concurrent compiler, two callback fixtures that expected a nonexistent zero-
token refund, and Forge's CRLF-to-LF metadata normalization. The normalization
correction is an offline exact-byte proof, not an EVM rerun. Actual01 compiled
successfully but lacked mandatory admission metadata; the corrected producer
performed actual02 without changing compiler input/output or safeguards.

The RPC report verifier was also corrected before final execution: verified
financial trace measurement is now required for profile qualification, and an
exception clears qualification. Baseline successful records already had verified
financial traces; the original baseline verifier/results remain unchanged.

## Operator procedure and unresolved work

Keep the12M default, reviewed20M contribution policy/full20%,1M isolated currency
allowance and all financial/idle/source/caller limits. When exact preparation
refuses gas, do not sign, raise defaults, omit healthy currencies or label an
opaque refusal a broken token. An operator may separately simulate and pay for
`Royalty.sync(asset)` or healthy atomic `syncAll()`, then prepare the Entry again
against fresh state. A faulty asset can make `syncAll` revert; use individual
healthy assets and preserve its deferred rights. Operator sync costs are separate
and are not part of the holder20M qualification.

An adversary can transfer tiny royalty amounts with expensive remainders before
entry. New receipts after sync can recreate the same gas work. Therefore these
assisted results do **not** establish universal activation liveness. Capacity16
is not an admitted launch list; qualify the actual selected currencies and
maximum workloads before admission/expansion. Arbitrarily many full-budget
failing token reads cannot be guaranteed inside20M.

Remaining: independently qualified prices/routes, actual target provider and
complete fees; selected currency behavior and worst-case LP2/state workloads;
maximum claim/canonical/host recovery; actual fresh constructor/consumer rollout;
VRF/OpenSea/authority/operating acceptance; independent audit. No source-only
check supplies those approvals. Q03 and broad release tasks remain open.

Existing Anvil8902, NFTs/LP/balances, databases, journals, website distributions,
signer, sites/services and paused heartbeat are untouched. All13 owned RPC nodes
are stopped. Four protected unrelated dirty files remain byte-identical and are
excluded from publication. No key, public transaction, deployment or seal occurs.
