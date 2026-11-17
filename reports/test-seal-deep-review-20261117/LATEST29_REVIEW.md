# Review of the latest 29 claimed tests

All 29 distinct methods from the previous operator-behavior follow-up were inspected individually. The [method matrix](LATEST29_METHOD_MATRIX.md) identifies each purpose, nonzero setup, assertions, fixture/profile and remaining limitation. Source review is not a rerun or a promise of exhaustive security.

Eight existing methods had useful assertion improvements; one new deterministic test covers an overlooked sequence. No production change is made by this test-review portion. The separate constructor/root fixes and their new cases retain their own evidence.

## Confirmed test weaknesses and corrections

1. **The enabled/disabled harvest-clock test did not assert the due cycle's submission.** Equal read counts could also pass if both fresh reads were removed. It now proves exact enabled-only read overhead, correct due/disabled submissions and unchanged persisted clocks/pending/spend at the mocked boundary.
2. **Seal authority and immutability checks accepted any revert.** They now require exact authorization/configuration errors, unchanged roots and repeated-seal rejection. This avoids passing for an unrelated setup failure.
3. **Preparation payout assertions checked returned amounts but omitted the recipient balances.** They now reconcile actual current-owner ETH deltas, drained LP/royalty liabilities, retained 5% compound/5% buyback reserves and continued Vault LP ownership.
4. **Mint callback rollback checks omitted payer and randomness request state.** Both callback paths now prove refunded native value, no retained request/consumer, no Vault/NFT money, unchanged reveal queue and no activated membership.
5. **Stale-price parking relied on an explanatory time warp.** The case now explicitly observes both Oracle failures before harvesting and parking, then checks both exact principal balances and reward amounts.
6. **The strengthened 1,000-input royalty fuzz still used one tranche and one fixed claim order.** A new case deterministically allocates 1,2,3,4,5,6 raw units across six permanent tickets, transfers one NFT, claims in reverse order after every tranche, independently tracks the rotating cursor, and proves all 21 units reach current owners with zero final liabilities and zero repeat claims. The unchanged fuzz is not rerun.

## Boundaries retained

The canonical-preparation fixture uses actual accounting/authority modules but deterministic native venue/strategy, synthetic admission, correlated prices and MockVRF. These are real accounting/callback tests, not live v4 market, independent feed or OpenSea acceptance. OperatorControls still uses a clearly labelled historical two-ERC20 admission seam. The actual-v4 compound boundary and actual-controller recovery cases are complementary fixtures, not one full production deployment. The user-selected stricter compound wait remains only in keeper software.

Keeper timing cases verify real cycle selection using inert RPC and mocked submission. Most use explicit historical accounting4 scaffolding; one current accounting7/custody5/confirmation3 LP2 case confirms current compatibility. None proves signing, provider latency, receipt finality or execution1/LP3 deployment acceptance.

The three old build results have an explicitly recorded pre-warning source stage and no retained raw terminal log. Their checks cover static exact constructor objects and trust admission, not deployment or complete seal readiness. New production edits invalidate old current-family source admission by design and require separate fresh reviewed pins; old evidence is not relabelled.

## Selected verification

**Nine distinct selected methods pass: eight strengthened existing methods and one new method.** That is eight Solidity methods and one Python method, with zero failures, skips or new zero-selection attempts. The unchanged 1,000-input fuzz and all unchanged suites were not rerun.

The first three seal methods were compiled before the separately approved Vault/metadata changes. The four canonical methods and new royalty method use the final frozen constructor/root source. Exact metadata binds each executed stage to current bytes or, only for the two separately changed production files in the first stage, the explicit `003c8d8` baseline. Only exact raw or explicit CRLF-to-LF normalization is accepted.

[Selected results and source proofs](LATEST29_VERIFICATION.json) preserve raw Solidity result logs, compiler settings and complete metadata source hashes. The Python terminal pass is recorded as an observed result with exact source hashes; a raw terminal log was not captured and no unchanged repeat was made to manufacture one. Gas in multi-operation EVM test bodies includes setup and is not production per-operation gas qualification. No existing chain, service, signer, site, journal or paused monitoring is touched.

The later explicitly authorized `MigrationBudget.validateReservation` restriction is a separate production stage. All nine selected results above precede it and are not relabelled as final-Budget passes. Its new/affected cases have a separate reservation verification record.
