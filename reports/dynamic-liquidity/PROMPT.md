# Revised execution brief: dynamic liquidity and NFT value

## Corrections to the supplied prompt

The supplied prompt correctly separates stable NFT shares from replaceable
physical LP positions and asks for independent economic checks. Apply these
clarifications before implementation:

- The $1 ZZZ / $0.50-$1.50 ZZZ/USDC example is an illustrative, ordered and
  decimal-normalized test market. Production targets the reviewed Robinhood
  native-ETH/ZZZ Pons pool. Do not substitute a mock stable pool for production
  route, hook, feed, gas or creator-funding qualification.
- Current LP value is an oracle-marked attribution of actual pool principal,
  recorded idle and designated compound reserves. It is neither original
  deposits, a redeemable balance, an executable liquidation quote nor an NFT
  market price. Mark unavailable when the required dependencies cannot be trusted.
- Share quantities survive maintenance; percentages can change when fairly
  priced new shares are issued. Market/entry-induced repricing belongs to the
  incumbent assets, and floor rounding needs an explicit bound. Neither share
  preservation nor the 1% contribution limit promises principal-value preservation.
- The user approved allowing out-of-range contributions with an explicit warning
  on 2026-10-18. Do not add a blanket range or keeper-availability gate, automatic
  user-triggered rebalance, pending deposit queue or invented near-edge threshold.
  All original price, custody, admission, minimum-LP and 99% safeguards still apply.
- The 3% approved migration budget applies to move/resume, not automatically to
  normal rebalance. Assess maintenance guards and any missing aggregate budget;
  do not silently choose a new economic loss limit.
  **Subsequent explicit decision:** the user approved applying the same 3%
  aggregate starting-price budget to ordinary rebalances on 2026-10-18. Implement
  it in addition to the existing guards; keep gas separate and the idle cap.
- Creator revenue is externally funded and the selected pool has zero conventional
  LP fees. Out-of-range liquidity is inactive in Uniswap; warning text must not
  cancel funded claims, royalty rights or imply creator payments are guaranteed.
- On-chain reads change with state, but no blockchain emits events merely because
  time or external market prices pass. Separate live views, confirmed snapshots,
  bounded metadata notifications and third-party caches; avoid a 1,000-NFT loop.
- Tests support bounded claims, not a universal proof or an independent audit.
  Reuse exact-source evidence, run new reproductions and affected regressions, and
  record actual fixture/provider limits. Do not repeat unchanged broad suites.

## Objective

Review, improve and verify the contribution -> shared custody -> replacement LP
-> per-NFT value path without changing the accepted economics or permissions.
Preserve the 1,000 NFT supply, 80/10/5/5 allocation, equal active-NFT collective
share, separate rarity-weighted royalties, permanent holder-nonredeemable
principal, 1% marginal contribution limit and separate user-paid network gas.
Work on main, retain unrelated drafts and update the single central task ledger.

## Execution

1. Read the current source, architecture, handoff and evidence. Bind findings to
   actual functions. Trace Entry, original-source valuation, current-range token
   balancing, fee synchronization, idle/compound movements, share issuance,
   rebalance, metadata, keeper and API/indexer consumers. Review the demo as a
   simulation; produce a testable integration contract rather than fake live data.
2. Establish explicit accounting identities: attributed NAV and exclusions;
   incumbent mark after entry-induced repricing; net new value; share rounding;
   preservation through LP replacement; reward and royalty receipt cutoffs.
   Inspect actual current ticks, token ordering/decimals and concentrated-liquidity
   amounts. Detect stale LP IDs, double counting and inappropriate historical USD.
3. Document admission policy and maintenance trade-offs before major changes.
   Existing-range entry is independent of a due keeper rebalance. Show the current
   range, range activity, rebalance eligibility and timing constraints in prepared
   transactions, with an explicit out-of-range warning. Preserve safe atomic
   failure for stale/misaligned prices, costs, custody states and pending plans.
   If rebalance ordering makes the old quote inappropriate, require a new quote.
   Show the cooldown end/eligibility state in the warning. A keeper's example
   ten-minute polling period is not an execution schedule; unknown/offline next
   checks must remain unavailable, not a fabricated countdown.
4. Reproduce and fix confirmed valuation/accounting/API defects. Use the smallest
   auditable change; preserve EIP-170/EIP-3860 headroom and sealed helper bindings.
   Fresh USD feeds alone must not disguise an invalid pool spot-price observation.
   Unavailable value stays distinct from verified zero and does not remove rights.
5. Add an independent arithmetic/range matrix for prices 0.40, 0.50, 0.75, 1.00,
   1.25, 1.40, 1.49, 1.50 and 1.60, with real TickMath rounding and both token
   order/decimal cases. Cover single-token, proportional dual-token, $100/$10,000,
   initial activation and existing-range additions where supported. Document
   exact-boundary tick-direction subtleties, swap assumptions and real venue gaps.
6. Exercise real Vault/NFT/reward accounting across price changes, repeated LP
   replacement, compounding, later deposits, transfers/claims and failed
   maintenance rollback. Check current position identity, unchanged share counts,
   correct marked value, reward continuity and no retroactive fees. Reuse existing
   adversarial/donation/callback/scaling evidence where source bindings permit.
7. Test changed metadata/API paths and bounded refresh behavior. Confirm displays
   use the current physical LP and current bucket denominator, with canonical
   block provenance; retain unavailable remote/parked/migration/failed-feed states.
   Explicitly separate cumulative contributions, LP value, fees, royalties and
   lifetime claims. Review indexer event support without treating events as prices.
8. Run only affected tests and new reproductions, normal size/compilation gates
   where production code changes, and an internal review of every changed path.
   Reuse unchanged tests with a recorded hash/dependency check. Re-run forks only
   where affected source or an unresolved venue question makes it meaningful;
   identify any actual RPC/dependency blocker without substituting mock evidence.
9. Record an assessment for each area: verified within stated scope, evidence gap,
   confirmed defect fixed, remaining risk, missing implementation or external
   qualification. Update features, central Todo, roadmap references, handoff and
   repository memory; commit/push the scoped work to main. Do not deploy contracts,
   send public transactions, resume the paused monitor or modify server services.

## Deliverables and double-check

Provide the architecture/admission rationale, numeric examples, scoped execution
receipts, changed-file reasons, internal findings/dispositions and explicit open
gates. Check twice that formulas match units and source behavior, that the tests
exercise independent expectations rather than copying implementation, and that
all readiness statements match the source and evidence. The website can stay
simulated with an explicit live-integration specification. Release remains NOT
APPROVED until the central production requirements and independent review close.
