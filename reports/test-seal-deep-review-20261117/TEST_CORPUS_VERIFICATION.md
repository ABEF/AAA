# Selected test-corpus fixture verification

Eight distinct changed-fixture methods pass. This is not a full-corpus/full-invariant or public-fork pass.

| Stage | Method | Result |
| --- | --- | --- |
| production_seed | `testConstructorActivationAndHarvestReachable20261117()` | Success |
| rights_seed | `testConstructorActivationAndRoyaltyClaimReachable20261117()` | Success |
| native_fee_split | `testNativeFeeSplitIsIndexedAndSeparatelyBacked()` | Success |
| pooled_rewards | `testOwnerFeesFollowSharesAndCollectiveIsEqualAcrossBuckets()` | Success |
| fee_split | `testFeeSplitIsExactAndBacked()` | Success |
| buyback_authority_prior_quote_adapter | `testUnauthorizedCallerAndDirectReserveReleaseRejected()` | Success |
| buyback_final_quote | `testApprovedDirectSwapBurnPreservesRewardAndCompoundBalances()` | Success |
| buyback_final_quote | `testSwapFailureRollsBackThenClaimsAndRetryRemainAvailable()` | Success |

The two new handler smokes prove real positive activation shares/membership, exact funded LP allocations and a positive post-opening royalty claim. Three changed positive-URI ledger setups prove their intended owner/equal-collective/split backing again. The native buyback fixture now validates the actual local reciprocal venue graph, observes deterministic quote liquidity and proves swap/burn preservation, failed-swap rollback with successful retry, and unchanged authority. Its negative case explicitly expects an actual core swap call before accepting the quoter's wrapped error.

The already-passing buyback authority method retains its prior stage; only failed quote-dependent methods were rerun. Original failed raw output/source/artifact hashes are retained. The current-context table is a declaration inventory, not claimed runtime coverage. Exact compiler inputs, stage differences and original raw trace hashes are in [TEST_CORPUS_VERIFICATION.json](TEST_CORPUS_VERIFICATION.json). Independent later fixture ports retain their separate scope; no production source, default, signer, network, existing chain or service changed.
