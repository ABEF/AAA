# Guarded manual swaps through an external price reference

**Fixed in the fresh source and verified locally. Production remains unapproved.**
Baseline: `da24f65e6e10e5e0185cb0a0b229944f803b58b2`,15November2026.

Priced manual C/D can now execute their exact selected swap through an admitted
external reference pool without rejecting their own authenticated price movement.
Live freshness/agreement, original caller floors, selected economic limits,
governance permissions, pause/lifecycle and callback checks remain. No automatic
route change, safeguard bypass, gas/default increase or public deployment occurs.

| Actual local flow | Estimate | Exact25% padded transaction | Receipt gas |
| --- | ---: | ---: | ---: |
| C14, residual into existing main | 12,798,287 | 15,997,859 | 11,916,187 |
| Active D14, replace both legs | 13,052,693 | 16,315,867 | 12,124,593 |
| Parked D14, actual park→recovery journey | 11,446,251 | 14,307,814 | 10,770,951 |

All full24M-cap and exact padded calls succeed. Worst remaining ceiling margin
is7,684,133.24M is a ceiling, not charged gas. These are Anvil31337 execution
measurements; complete Robinhood4663 fees/provider/maximum-state approval remain
separate.12M defaults stay; these full-padded manual calls would not fit them.

## Why the old path failed

The [previous actual rehearsal](../manual-recovery-rehearsal-20261115/REVIEW.md)
already proved a successful core swap followed by a changed live emergency
fingerprint and atomic rejection, even with feasible original output/L floors.
That source compared against a reference its own trade had changed. Its exact
traces are reused as the baseline; unchanged baseline operations are not repeated.

## Implementation and safeguard boundaries

Six existing production files change; no module, recipient, configurable executor
or authority is added:

| Component | Change |
| --- | --- |
| [MigrationBudget](../../src/ZZZMigrationBudget.sol) | Starts the fixed Pricing scope before the first emergency fingerprint/harvest/unwind whenever bit2 or4 is retained. Ends it after Vault settlement/economic proofs and the final emergency fingerprint. |
| [ContributionPricing](../../src/ZZZContributionPricing.sol) | Reuses its existing maintenance ownership/bucket state for typed `emergencyExecution(bucket,opening)`. Only fixed Budget may call; Budget's nonreentrant wrappers validate active authority/lifecycle immediately before static-only scope setup/cleanup. |
| [CustodyValidation](../../src/ZZZCustodyValidation.sol) | Commits starting bound fingerprints while fully validating live source/policy/market proofs; does not simply omit a changing fingerprint. |
| [LiquidityManager](../../src/ZZZLiquidityManager.sol) | Borrows that scope, obtains a proof for exactly the supplied venue/direction/input, authenticates exact output/full post-state before settlement, then validates later callbacks/placement and returns its loan. |
| [LPBalanceMath](../../src/ZZZLPBalanceMath.sol) | Adds captured exit price/output reads without reinstating a deliberately omitted operations bit. Ordinary admission still checks operations immediately before the shared floor, with only static/local work between them; final ordinary price/context checks remain. |
| [LPBalancer](../../src/ZZZLPBalancer.sol) | Reuses fixed-Manager-only, fully reverting `quoteSwap`. Quote-only reads omit the duplicate operations-enabled flag; every structural check stays and actual execution independently enforces ordinary/retained-bit8 controls. Solver/configuration pool admission still requires operations enabled. |

The proof is the existing execution1/LP3 own-swap mechanism: actual-core quote,
complete expected sqrt price/stored tick/directional protocol fee/LP fee/liquidity,
and exact output checked immediately after `core.swap`, before token settlement.
No operator supplies an acceptable replacement price or post-state. Public Oracle
views remain live. Other feeds, unexpected market changes, source/configuration
changes and settlement callbacks cannot hide behind the own-swap exception.

Retained bit2 uses captured-reference price bands. Bit4 uses the same starting
USD vector for output/gross/additional/retained-value/idle checks, even with2 off.
Masks0/8 do not start a price scope or acquire an Oracle dependency; bits1/16 keep
their own pre-existing eligibility reads. No bit is silently removed or added.
Caller minOut/minimumLiquidity/deadline and structural custody checks remain.

C's final static custody verification and controlled local Portfolio mode/revision
writes follow price-scope cleanup; no mutable token/core/refund call occurs there.
Current-owner rights, exact NFT shares, classified reward/buyback backing, compound,
physical custody, clocks and pause state reconcile. C keeps main/ticks/rebalance
clock, closes the residual, consumes nonce/epoch and completes mode OFF. D creates
one main, releases designated compound and updates rebalance time; desired residual
mode stays as configured. All successful manual flows remain paused.

This does not permit a same-core PoPL principal destination to become its own
independent reference. Nor does it guarantee every trade: live source agreement,
freshness, actual depth/fees, spot bands, caller floors and loss/idle limits may
still legitimately reject execution. Spot-source independence and MEV risks are
not solved by authenticating our own trade.

## Verification, including failed attempts

- **25 distinct new methods and three deliberately adapted methods pass.**
  Twenty successful new checks are retained at their exact stages; only five
  reverse-fixture failures are rerun after their shared setup is corrected.
  The original unchanged D0 method and other old suites are not rerun.
- **34 invocations:**28 unique successes plus six retained fixture failures.
  One initial getter consumed a one-call prank; five reverse setups attempted
  keeper harvesting while paused. These are test setup defects, corrected using
  legitimate getter ordering and governance-unpause/harvest/repause, not relaxed
  production authorization. Branch/source equivalence records preserve scope.
- Both swap directions, C/D/Parked, price-only/value-only with operations disabled,
  unpriced oracle-outage choices, no-swap, sequential recapture, ordinary guarded
  consolidation, exact floors and unauthorized nested scope calls are checked.
- **Nine actual adverse callbacks return successfully and complete their intended
  mutation before a later production guard rejects.** Feed round/staleness,
  primary/independent markets, disagreement, disable/restore, execution quality,
  source gas and maintenance policy are covered. Atomic rollback is verified;
  callback assertions/errors cannot count as the expected production failure.
- **Three actual unchanged-production-CLI manual receipts**, plus the park receipt
  in the same-chain Parked journey. Real clock, genuine canonical headers,
  original25-second work budget, exact selected inputs/floors/expiry, full25%
  padding and once-only local submission remain. No successful transaction is
  resent. Owned nodes stop afterward.
- **All48 normal runtime/initcode gates pass at original settings.** Failed
  changed-source normal stages1–3 are retained; no limit is raised. Final Manager
  runtime24,475/101-byte margin, Vault24,544/32, Oracle24,573/3. Oracle initcode
  plus64argument bytes is49,073/79-byte margin. These margins remain tight.
- The accepted100-source normal AST is reused for actual Slither, without another
  compile. **565 records:**113 individually reassessed current contexts and452
  unique exact referenced-source reuses. This is internal review, not independent
  audit. Detector-present Windows exit4294967295 is retained; JSON success and
  explicit complete coverage are checked separately, not misreported as exit0.

The initial new wrapper refused before node creation because Forge metadata uses
LF-normalized sources while repository files preserve mixed line endings. The
corrected wrapper checks that exact compiler normalization and separately pins
raw bytes. Failed admission and original wrapper source remain recorded. This
does not relabel old runtimes or relax actual configured runtime checks.

## Adoption and evidence

Existing public signatures/storage declarations, accounting7, canonicalV10,
execution1's49-word codec and capability values stay. Three fixed helper methods
extend the ABI; the complete reference has959 functions and1012 operator examples.
Existing1009 example arguments/roles and existing ABIs remain unchanged. Exact
new source/runtime/configuration pins and freshly prepared reviews are required.
Old review hashes, journals, source profiles and Catalog provenance labels remain
historical. Source publication does not update a sealed instance or authorize
deployment, signing, service restart or website rollout.

See [verification](VERIFICATION.md), [gas/transactions](GAS_AND_TRANSACTIONS.json),
[normal build](build/production-size-gates.json), [bytecode comparison](build/EQUIVALENCE.json),
[current strict review](static-review.json), [callback trace review](CALLBACK_TRACE_REVIEW.json),
[method inventory](UNIT_METHODS.json), [operator procedure](../../docs/OPERATOR_MANUAL.md#local-manual-recovery-rehearsal)
and [exact manual inputs](../../docs/MANUAL_LP_PREPARATION.md).
The portable [core](public-evidence.zip) and [complete unit](unit-evidence.zip)
archives can be checked offline without executing a test or transaction; commands
and exact scope are in [verification](VERIFICATION.md#inspect-original-evidence-without-replaying-transactions).

Existing Anvil/journals are not administered; the historical read endpoint was
unavailable before/after, so old live state-root/balance equality is not claimed.
All5,598 website dist files and three signer/public-config sources remain
byte-identical; public configurations stay null, signing remains Anvil-only and
the heartbeat stays user-paused. No public transaction, key or provider probe is
used. Four unrelated tracked dirty files remain byte-identical and unstaged.

Real independent markets/routes/depth, complete target fees/provider capacity,
maximum workloads, contract-wallet/host operation and independent audit remain
open. The sole Todo closes this bounded defect and its local evidence only.
