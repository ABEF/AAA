# NFT economic rights: execution prompt

Reviewed 2026-10-16. This corrects the supplied prompt against accepted product
decisions and the current working source. The original is preserved alongside it.

## Objective and boundaries

Review, repair where evidence warrants, and test the canonical NFT ownership,
shared liquidity, funded LP rewards and separate royalty system. Produce an
adversarial internal assessment with reproducible, source-bound evidence. Do not
call this an independent audit, formal proof or production approval.

Start with PROJECT_CONTEXT.md, AGENTS.md, README, economics, component status,
implementation and release checklists. Inspect actual source, tests, deployment
and off-chain claim interfaces. Record the working-tree baseline: it includes
previous unpublished changes which must be preserved. Do not infer behavior from
the website simulation or silently include unrelated work in publication.

No public contract deployment, signing, asset movement, marketplace listing,
website modification or staging-server change is authorized by this review.
Read-only external verification and isolated local tests are within scope.

## Correct model and acceptance criteria

1. **Identity and custody.** The collection has a fixed 1,000-NFT cap. Canonical
   token IDs are hashes, not ordinal numbers. Each token has immutable rarity,
   palette and pattern, an NFT-to-bucket mapping and nonredeemable shares in a
   shared physical LP position. One pool/strategy serves many NFTs. Rebalances
   replace the venue LP ID without replacing the canonical NFT/share identity.
   Do not add a separate LP for each NFT or increase the collection cap.
2. **Ownership.** All accrued but unclaimed individual, collective and royalty
   balances, including fractional carry, follow the NFT. Claims authenticate its
   current owner and pay that owner directly. ERC-721 approval is permission to
   transfer, not permission to divert claims. Test both transaction orderings,
   repeated and operator transfers, multiple NFTs per wallet, contract receivers
   and callbacks. Transactions are ordered; a valid claim before a sale is not a
   post-sale entitlement. State explicitly that buyers must inspect current
   balances, since a seller can claim before a transfer executes.
3. **LP receipts.** Allocate actual admitted revenue 80% to bucket shareholders,
   10% equally among activated canonical NFTs, 5% to that bucket's compounding
   reserve and 5% to buyback/burn. Individual LP rewards are proportional to shares,
   never rarity. Check the existing 20-raw-unit batching and documented sub-20-unit
   incumbent-dust settlement exception rather than claiming impossible exact
   percentages for every indivisible raw receipt. Exclude principal, idle funds,
   unattributed custody donations and royalties from the fee base. Intentional
   receipts into an admitted revenue inbox are funded revenue.
4. **Eligibility timing.** Activation establishes permanent membership. Market
   declines, pauses, parking and migrations do not deactivate it. Do not invent a
   deactivation operation. Entrants must not share already indexed rewards,
   settled local inbox receipts or incumbent royalty receipts. Unharvested venue
   fees and delayed remote receipts retain the accepted collection/delivery-time
   collective policy; explain its limitations rather than pretending historical
   generation timestamps are available. Top-ups cannot dilute old entitlements
   or create another collective membership.
5. **Royalties.** ERC-2981 requests 5% of sale value to the immutable NFT royalty
   receiver. Actual eligible receipts are shared at Commun x1 / Rare x2 /
   Legendary x3, independently of LP shares. Eventual quotas are 600/300/100,
   drawn without replacement through ordered VRF reveal. Test native currency,
   admitted exact-transfer ERC20s, decimals, prefunds, zero eligibility, pending
   receipts and fractions. Do not fabricate payments or add transfer restrictions
   to force royalties. Verify current marketplace documentation and distinguish
   standards support from an actual deployed/paid marketplace integration.
6. **Venue reality.** Distinguish conventional v4 position fees from the selected
   0%-LP-fee Pons market's separate creator/hook revenue. Trace both paths. Creator
   payment amount, basis and frequency remain unset; actual receipts alone create
   liabilities. LP custody does not establish a right to hook revenue.
7. **Reinvestment and burn.** Check reserve separation, originating-bucket benefit,
   share pricing on entry, exact balances/allowances, guarded price/range changes,
   direct approved swaps, actual token-supply burn, failure rollback and retry.
   Slippage limits are not an MEV guarantee. Do not silently add arbitrary swaps,
   sweeps, recipient choice, proxies or principal withdrawals.
8. **Migration and failure.** Review rights across parked/in-flight/remote states
   and old reward paths, role/timelock/seal controls, replay and funded-liability
   barriers. Immutable code is not universally upgradeable. Record unresolved
   destination capacity, external dependency failure and real bridge qualification
   accurately; do not enable bridging or conceal those release gates.

## Work sequence

1. Independently challenge this scope twice: compare it with accepted economics,
   then with actual call paths and test coverage. Map economic identity, trust
   boundaries, accounting entries and external dependencies before editing.
2. Build a coverage matrix using existing tests. Add focused regressions for
   uncovered risks; reproduce suspected defects before changing production code.
   Preserve correct implementations instead of rewriting functioning economics.
3. Add and execute a combined 1,000-activated-NFT scenario with varied owners,
   rarities and contributions; assert one shared bucket, exact quotas, unique
   canonical IDs, independent claims, transfers of all unclaimed streams and
   reserve conservation. Local venue/VRF fixtures must be explicit.
4. Measure cold transaction-equivalent gas for activation, individual claims,
   bounded batch claims and shared maintenance at realistic maximum populations.
   Separate aggregate setup gas from a user's transaction. Use existing budgets;
   do not relax gas/compiler/size/security gates to make a test pass.
5. Extend meaningful stateful/fuzz coverage across both ledgers and custody where
   missing. Reconcile each asset separately: actual receipts equal paid rewards,
   burned/reinvested amounts and remaining funded reserves/quarantine/dust. Do not
   double-count liabilities and the balances backing them, or add raw units of
   different tokens. Conserved accounting does not guarantee market value.
6. Run targeted regressions, full offline suites, normal production size/source
   gates and relevant adversarial review. Run fork tests when needed to establish
   changed venue behavior, with a pinned block and explicit fixture limitations.
   Bind reused evidence to unchanged source; do not relabel historical checks.
7. Fix confirmed critical/high issues within the scope, add regressions and review
   the final diff independently. Report any unresolved issue plainly and keep its
   release gate open. Coverage percentages must come from an actual coverage run;
   testing cannot prove the absence of all bugs.
8. Update README/economic architecture/runbooks only as needed, central Todo,
   implementation status, release checklist and repository context. Publish only
   scoped verified changes; preserve unrelated unpublished work. No deployment.

## Deliverables

- The corrected prompt and the reasons for its material corrections.
- Architecture and conventional-fee/creator-receipt/royalty flow explanations.
- Test-linked proof of current-owner claims and transfer of unclaimed rights.
- Findings with severity, prerequisites, affected paths, fixes and residual risks.
- Changed-versus-already-correct implementation report.
- Exact executed tests, failures, seeds/profiles, gas measurements, source hashes,
  coverage limitations and mocked-versus-live boundaries.
- Per-component implementation/test/review status and prioritized open release
  actions. External audit, services, governance and live operating qualification
  remain separate requirements even if all local checks pass.
