# Exact-unit LP integration scope

Baseline main `64f9bfb1b0db28c9c8eafc42394afad2263637b6`, 6 November 2026.
Production NOT APPROVED. Source publication only; preserve all environments,
historical runtimes/readers, journals and unrelated changes.

## Target and invariants

Replace fresh LP indices/fractions with the verified bounded exact-unit engine,
across actual Rewards, weight synchronization, current-owner claims, same-NFT
conversions and lossless same-chain canonical accounting. Retain fixed 80/10/5/5,
equal activated collective shares, independent rarity royalties, principal and
reserve separation, hourly actual-receipt harvesting and main/residual ownership.
No administrator sweep, new payout recipient or extra custody authority.

1. Move the Vault's typed share hook after authenticated share writes. The tree
   settles old money using its stored old weights before installing new weights.
   Synchronize Membership only after eligibility/count updates; top-ups never
   increase collective weight. Authenticate immutable mint ordinals and totals.
2. Restrict fresh LP books to native ETH and the deployment's fixed ZZZ. Reject
   third-currency/identity mutation; royalty currencies remain independent.
3. Claims take both whole components with current-owner/router checks and atomic
   rollback. Conversion consumes exact historical components and credits only
   the same NFT/component, without new cohort allocation or new income.
4. Canonical export/import preserves raw pending nodes, both fairness phases,
   direct whole credits, exact liabilities/backing and all authenticated weights.
   Seed all weights before importing monetary nodes. Page bounded node records;
   no one-shot 1,000-NFT capture/rebuild. No flattened-rights/old-phase mismatch.
5. Introduce explicit fresh accounting7 / LP-allocation1 / canonicalV9 and
   schema16/profile7 consumer boundaries. Preserve old6/V8 readers, checkpoints
   and evidence; never reinterpret old money, runtime identities or journals.
6. Update actual read/replay/claim/keeper/inventory consumers and focused tests.
   Reject incompatible checkpoints rather than guessing. Synchronization,
   conversion, import and claim events are not new fee income.
7. Verify funded conservation and individual rights through activation, growth,
   transfers, claims, conversion, both-leg upkeep, handoff and fully funded abort.
   Include 1,000 ordinals, tiny final units, invalid/callback/outage cases and
   independent producer/consumer checks. Maintain obsolete tests explicitly.
8. Compile and size the complete real host graph; review actual static output
   and update strict CI default/reference/operator examples. Measure complete
   host gas separately from prior library samples. Retain failures and limits;
   do not inflate operating budgets or infer independent production approval.

The installed pinned dependencies are the build authority. Relevant review
guidance: [Solidity 0.8.26 security](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
for callbacks, state order and bounded loops; [OpenZeppelin math](https://docs.openzeppelin.com/contracts/5.x/api/utils#Math)
for full-precision arithmetic. These references do not prove the custom allocator.

Update the sole Todo, feature/evidence, operator procedure/function inputs,
economics, architecture, release boundary and repository context. Distinguish
verified fresh source from installed deployments and external qualification.
