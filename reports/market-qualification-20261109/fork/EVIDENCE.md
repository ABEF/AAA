# Original-market fork diagnostic evidence

This package binds source `99a01e97887156be0d31b61d453df4e29eb8a055` and the
90-source normal build `opensea-integration-20261109/contract/normal-final-05f7ac32db`.
It reuses those exact production objects and the unchanged, previously compiled
controlled feed/VRF fixtures. No production source was compiled or edited, and no
unchanged Solidity suite was rerun. The predeployed renderer matches the current
three-argument NFT constructor. Minting is an explicitly unbound direct-mint
fixture; this does not qualify the production mint2/OpenSea path.

The anchor is Robinhood block **109785803**, hash
`0x4a55b88b470e9dd41d7bf885c80f33a0886d66444cf1ba4223ff2128c9da9498`.
Selected-pool depth, ticks and upstream contracts were left unchanged. Conditional
prices use one observed Chainlink ETH reference and the selected DEX ratio in
four controlled observations; these are correlated and **not independent USD
feed qualification**. Native and ZZZ $100 contributions each reverted atomically;
their actual receipts and exact balance/LP rollback witnesses are retained.
Both $5 growth cases remain blocked because no genuine activation succeeded.
No synthetic incumbent, extra venue liquidity or relaxed financial guard was used.

The ETH trace would deploy **$50.882607835024253894** and retain
**$48.803348659196923858** idle. The configured 1% post-swap spot guard limits the
selected partial trade; the larger initial candidate also misses the venue's
2% gross output floor. The final 5% idle check rejects it. All eight native
candidates successfully quote within 74,000 gas, below the 200,000 allowance:
these results do not establish a solver-budget bug or a globally empty market.
An independent read-only actual-core trace requests 1 ZZZ but consumes only
388,557 raw token units for 1 wei ETH; the callback rejects this partial fill.

`evidence.zip` contains all three attempts, exact scripts and adapter provenance,
the 59 local deployment/configuration receipts, direct fixture mints, exact ZZZ
approval/funding records, both authentic full call traces, rollback witnesses,
blocked-growth classifications, and owned-child cleanup. Attempt 1 is an offline
Git ownership preflight failure; attempt 2 is a restricted-network preflight
failure before Anvil started. Attempt 3 is the completed diagnostic. Neither
original failure was overwritten. The new hidden Anvil child and read cache
were stopped; existing chains, services, journals, sites and signers were untouched.

The ZIP uses lossless deflate. `evidence-manifest.json` records every original
entry's raw byte count and SHA-256; `lossless-trace-verification.json` separately
records the decompressed full-trace hashes. All 67 raw entries were rechecked.
No compiled output/cache, executable binary, key or keystore is included. Paths
named `public-read-cache` contain sanitized request audit events and summaries
only; actual cached state was memory-only. `source90-provenance.json` preserves
the exact original normal source scope. `tool-provenance.json` explicitly labels
post-campaign tool hash/version observations; the reused compiler output and
fixture already bind their original compiler hash.

This is negative market-compatibility evidence and positive rollback evidence.
It is not successful activation/growth, independent pricing, production gas,
wallet, provider, VRF, OpenSea or operating qualification. The 1% spot value is
this diagnostic's operating choice, not an approved production policy.
