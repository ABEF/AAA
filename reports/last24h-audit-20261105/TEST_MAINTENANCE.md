# Current tests and historical compatibility

Follow-up to the user's question about obsolete tests. Production source remains
unchanged from the final normal/static/source-wire records. This maintenance
does not relabel older evidence or claim a green full suite.

| Area | Correction |
| --- | --- |
| Current Python templates/defaults | Use schema13,18helpers and collective holder return. A current mint template must exercise production_v11, not an old validator. Historical schema8 coverage explicitly loads its archived template. |
| Native accounting identity | Expect actual canonicalV8 and explicitly reject old V6/V7 identities. No runtime is selected by tuple length. |
| NFT metadata royalties | A single eligible Legendary receiving1ETH can claim all1ETH. Remove the old `1 ether - 1` rounding-loss expectations; retain ownership/outage/artwork checks. |
| Preparation, terminal return and portfolio scenarios | Mint all required NFTs before closing the sale, cross the actual one-hour opening, refresh only intended healthy mock prices and synchronize. Preserve late activation, pending-reveal, pause, transfer and both-leg behavior. Assert nonzero existing rights so preservation cannot pass vacuously. |
| Combined currency/bucket gas | Preserve pending receipt stress by funding AFTER the initial empty opening sync. At16faults×1M,12M must fail atomically with balances, LP identity, shares and eligibility unchanged. A separately labeled larger LOCAL call demonstrates isolation; it is not a production/provider gas increase or qualification. |
| Canonical domain/supply fixtures | Mint dormant extras before closure; enroll them later where necessary to retain incumbents' already-earned rights. Closing a sale early in a helper must not make later required mints impossible. |
| Undrawn inventory after handoff | Preserve remaining quotas/artwork inventory, but assert closed minting stays closed on both deployments. The old expectation of resuming primary minting after a V8 handoff contradicts its required finalized opening and imported closed end. |
| Collection-scale accounting | Receipts during minting belong to held openingPool, not automatically orphaned funds. Calculate the cutoff cohort's exact whole-unit allocations independently; test the supply-cap rejection BEFORE sale closure. Keep an explicit zero-cohort case separately. |
| Stateful NFT-rights model | Model locked holding and the observed opening cohort, handle locked claims as expected atomic failures, require exact healthy-currency conservation after opening, and demonstrate real funded claim activity/drain. Preserve distinct LP fractional inequalities. |

The [verification](VERIFICATION.md) and final supplement receipts record actual
executed selections and retained failed stages. Correcting a fixture is justified
by the chosen rule; changing a financial guard merely to pass a test is not.

Historical `RoyaltyConversion`/`TypedV4Rewards` tests explicitly import historical
ledger implementations. Their index/fraction/conversion checks remain useful.
Likewise original-currency2/window3 readers, archived configurations and old
journals need explicit compatibility and rejection coverage. They are not current
royalty4 proof, and age alone does not justify deleting them.

Current targets, legacy fixtures, negative compatibility cases, model-only checks,
actual local EVM, target fork/operating rehearsals and independent audit are
different categories. See [development classification](../../docs/DEVELOPMENT.md#current-tests-versus-historical-compatibility).
