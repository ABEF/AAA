# Supplied-pool composed integration: scoped execution plan

Baseline: `bb5ef4de5afc9dd8cebf4ee96d5b044477a52bf5`, 20 November 2026.
Production remains undeployed and NOT APPROVED.

The previous physical-LP journey exercised Manager mint/increase/collection/close,
but its fee-generating swaps used a test trader. It did not exercise production
swap authorization/routing or Entry-to-NFT share accounting. This work advances
those missing connections without repeating unchanged suites or changing F6.

1. **Production swap partition.** On a new owned clone of the saved exact-anchor
   fork, use a minimal explicitly bound test caller to invoke the real
   `Manager.swap`, quotes, output guards and real native Uniswap core. Cover both
   directions, exact balances/allowances and an impossible caller floor. Preserve
   the distinction between a MockAccess fixture and production role qualification.
2. **Entry/NFT partition.** Reuse current trusted creation objects for a fresh
   normal graph on a separate owned fork. Exercise a small actual Entry/NFT
   activation/growth sequence against real core/periphery. Explicitly label
   controlled prices, funding, VRF/sale and any external-depth fixtures. Check
   owner/activation/share conservation, marginal LP and existing-main identity.
   A genuine financial or gas refusal is retained, never bypassed for a pass.
3. **Evidence review.** Independently reconcile saved requests, receipts and
   before/after reads. Separate setup from scenario coverage and simulated from
   mined failures. Check full estimate padding and original source identities.
4. **Documentation.** Update the single Todo, findings, roadmap, operator manual,
   feature reference and handoff with actual finite outcomes and remaining gates.

Reuse immutable previous source/output/cache/state artifacts only after verifying
their hashes and exact anchor. Restore only into a newly owned ephemeral process;
never overwrite Anvil8902 or adopt its state/journals. Public requests are read-only,
bounded and throttled; stop on a provider refusal. Stop every owned process and
retain failures and partial artifacts. No live site/service/configuration, signer,
financial policy, gas ceiling or sealing change is authorized.

Independent market prices/routes/depth, actual target fees/provider capacity,
full-state/hybrid/canonical/recovery acceptance and independent release approval
remain separate even if both finite partitions pass.
