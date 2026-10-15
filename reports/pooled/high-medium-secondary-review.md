# Internal secondary High/Medium review — 2026-10-15

Reviewed all **83** High/Medium findings from the frozen shared-pool candidate: 27 High and 56 Medium. No additional actionable source issue was identified under the stated deployment assumptions. This is an internal AI-assisted review, not an independent external audit.

The JSON companion binds each individual finding ID and rationale to the raw Slither output and LF-normalized Solidity source hashes. It does not suppress detectors or certify arbitrary future assets/providers.

The final private guard, token-balance and unwind/redeploy helpers preserve original checks and atomic call ordering. NFT lifecycle is now read through `nftStatus`; physical LP custody is read once through `group(bucketId)` and NFT rights through explicit share/contribution getters.

Shared entry accounting checkpoints incumbent fees before share changes, prices against the post-entry-swap old LP plus incumbent idle/compound value, rejects zero incumbent NAV, and requires $500 of new marginal deployed LP per activation. The remote drain barrier propagates lifetime allocations, including unsent reserves, and prevents later members from acquiring old remote owner fees.

Rounding policy has an explicit economic assumption: at most nine **raw token units** settle entirely to incumbent owners before a membership change. That is negligible for 18-decimal ZZZ/WETH but may be material for future low-decimal, high-unit-value tokens; token admission must assess it rather than treating every raw-unit remainder as economically negligible. **This remains an open product/admission policy tradeoff**, including holder-triggered settlement frequency. No additional token restriction was inferred in this implementation.

Production remains conditional on ordinary reviewed ERC20 behavior, defensible feeds/outage handling, bridge authentication/backing/finality, reserved destinations and the still-deferred reward-market decision. Final tests, standard code-size checks and independent audit remain separate evidence.
