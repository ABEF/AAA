# Verification scope

Baseline e007618; fresh royalty recovery1 implementation. Internal verification,
**not production approval**. Full hashes, selected identities/stages and unchanged
report/protected-file proof are in [evidence.json](evidence.json). Raw commands,
compiler output, failures and logs are retained in the exclusive external
`royalty-audit-20261105` evidence directory referenced there.

| Check | Actual result and limits |
| --- | --- |
| Production delta | Only `src/ZZZRoyaltyRewards.sol` changes among52production source files.31dependency source pins and build settings remain exact. New ABI/event capability is recovery1; accounting6/custody-format/canonicalV6 wire remains unchanged. |
| Normal compiler | Exact Solidity0.8.26/Cancun/viaIR/optimizer1/Yulfalse;83closed sources and43normal EIP170/EIP3860 object gates pass. Dynamic constructor arguments still need actual deployment qualification. |
| Selected EVM |72distinct successes across explicit stages. Includes13recovery methods, actual local v4 recovery and a real-NFT no-enforcement transfer case. Existing royalty/typed-conversion tests cover outage cohorts, malicious/taxed/rebasing/read failures, stale feeds, price floors, duplicates, claim races, callbacks, transfers, pauses, canonical import and fraction conservation. No full contract suite rerun. |
| Scale/fuzz | Final mixed fixture has exactly1,000NFTs:999activated across all three weights and one dormant. Recovery allocates once; every active entitlement and no dormant dilution are checked, plus transfer/current-owner claim. A separate new method runs1,000fuzz inputs conserving pre-existing and recovered ETH. Other existing selected fuzz checks retain their normal1,000-input setting. These are explicit fixtures, not target-chain gas or actual marketplace acceptance. |
| Python |141affected methods pass at the corrected stage.103final static/reference/event/recovery methods pass after final catalogue/default updates. Counts overlap; no combined244claim. No skips and no source drift during either successful stage. |
| Static analysis | Fresh Slither0.11.6/crytic-compile0.4.2 on the exact closed normal artifacts completes with474alerts and a nonzero detector CLI status.33changed-source/ambiguous-match contexts reviewed;441unique contexts reuse exact referenced source plus normalized detector text. [Full strict review](static-review.json); checker default updated together, rules unchanged. Alerts are not474confirmed vulnerabilities or proof of exploit absence. |
| Storage and callable reference |179compiled objects retain semantic storage layouts, excluding compiler AST identity numbers. [Compatibility](compatibility.json). Current reference37contracts/820functions/37constructors/13receivers has no explanation/input/output gaps. Runtime identity is not implied by layout compatibility. |
| Preservation |2,776earlier evidence/report files unchanged; maintained reports/README navigation is intentionally updated. Four unrelated tracked dirty files remain byte-identical and excluded from staging. Existing environments and recovery records remain untouched. |

Initial3EVM failures exposed missing current-policy fixture bindings. The first
141-method Python stage retained3failures: two retired VRF descriptors were absent
and one test hardcoded an obsolete catalogue size. Exact Git declarations and a
semantic compatibility assertion repair these without weakening decoder checks.
Schema regeneration also retained the retired Entry route event instead of
silently dropping it. The earlier scale fixture had1,000active plus an extra
dormant mint; the final corrected scale case respects the actual1,000supply cap.
Old attempts remain preserved and are not counted as additional current coverage.

Royalty runtime21037→22559bytes; factory22584→24113(runtime margin463). Access
runtime10438unchanged, constructor41519→43048due to embedded factory creation.
Vault635/Budget237/Migration39/Balancer360runtime margins remain. These gates are
not actual deployed gas measurements, strategy profitability, public CI or an
independent review. Oversized test-fixture allowance is separate from the normal
production compilation.

Primary references reviewed: [ERC2981](https://eips.ethereum.org/EIPS/eip-2981),
[OpenSea creator-fee enforcement](https://docs.opensea.io/docs/creator-fee-enforcement),
[OpenSea creator earnings settings](https://support.opensea.io/en/articles/8867026-how-do-i-set-creator-earnings-on-opensea)
and [Solidity0.8.26 security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html).
The installed exact-transfer, access, converter and callback implementations
were inspected; external documents do not establish Robinhood deployment support.
