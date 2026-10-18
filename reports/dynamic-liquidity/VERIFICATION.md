# Dynamic liquidity verification - 2026-10-18

**Development evidence; release NOT APPROVED.** No independent audit or public
deployment is claimed. The website, server and paused monitor are unchanged.

| Check | Result and scope |
| --- | --- |
| [Affected Solidity suites](solidity-verification.json) | **119 passed**, no failures/skips, 391.23 seconds. Real contribution/share/reward/NFT modules; actual manager/strategy amount math with independent vectors; controlled fake venue/feeds/authority/VRF where specified. Includes two 1,000-run fuzz cases. |
| [Independent range matrix](range-vectors.json) | 36 vectors: nine prices and four token order/decimal cases. $100/$10,000 single-token and proportional dual-token plans; initial target vs existing range. Decimal/rational expectations do not import Solidity math. |
| [Isolated backend checks](python-verification.json), [log](python-tests.log) | **138 passed**, no failures/skips, 52.860 seconds. Tracked HEAD plus only intended changes; unrelated unpublished server/transaction/history drafts excluded. Includes API, lifecycle, predecessor history, activation, HTTP, range/timing and RPC boundaries. |
| [Normal size/source gates](size-gates.json) | **30 objects / 39 production sources**, all pass. Vault runtime **24,557 bytes (19 free)**; Migration **24,518 (58 free)**; NFT initcode object **43,044**. Constructor arguments and actual chain limits still require deployment allowance. |
| [Selected native/Pons fork](selected-fork.json) | **1 targeted rebalance case passed**, no failures/skips, block 88,544,093. Real pinned venue/wrapper/hook, synthetic USD prices and mocked VRF/trigger. No public transactions. |
| [New ABI reads](abi-checks.json) | Six getter layouts match source-bound normal artifacts, including signed int24 ticks and StateView slot0. |
| [Fresh static execution](static-execution.json), [review summary](static-review-summary.json) | Slither 0.11.6 completed on the current full production build: **376 findings reviewed internally**, 155 false positives / 75 accepted risks / 146 informational. Coverage passes and five mutations reject; not independent audit. |

The source-bound Solidity receipt records 11 suites and their artifact/dependency
bindings. The two new fuzz cases exercise varied contribution size/repeated
replacement and the exact 3% loss boundary. This is not a new full stateful
invariant campaign or a new 616-case whole-repository regression. Existing wider
historical results keep their original source/workload scope. The unchanged
keeper watcher was inspected; no sustained server rehearsal was repeated.

The fixed metadata guard is supported by a before/after reproduction: four other
new range tests passed before the fix, while manipulated spot with fresh USD
feeds incorrectly remained available for valuation. After the fix all five pass. An intermediate
affected run had 93 passes and one test-harness error: an NFT royalty-ledger getter
consumed `vm.prank` before the claim. Caching the ledger before setting the caller
fixes the harness without relaxing the authorization assertion. New API reads
also exposed a lineage fixture that translated the integer status 1 as an address;
the fixture now supplies the actual successor-custody tuple explicitly.

The first normal compile produced bound artifacts and passed object sizes but
could not write Foundry's signature cache in the restricted process. The authorized
cached build completed with exit zero using those same artifacts. It was not a
second fresh compilation. [Attempt receipts](attempts.json) preserve those limits.

The targeted actual selected-pool rebalance fork passed in 372.05 seconds with
current compiler/source bindings. Its reported test gas includes the scenario's
setup and operations; it is not a production rebalance gas quote. The bounded
read-only relay used the existing unpublished Windows process-runner draft,
identified by hash in the receipt; that draft is excluded from this publication.
Real venue execution with synthetic prices and a mocked trigger does not establish
production pricing, strategy profitability, provider uptime or creator terms.

Read [the internal assessment](REVIEW.md) and
[the integration contract](../../docs/DYNAMIC_LIQUIDITY.md). Actual route/service/
strategy/operating qualification and independent audit remain central release gates.
