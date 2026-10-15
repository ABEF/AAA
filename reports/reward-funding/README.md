# Creator-funded reward intake and internal review

Date: 2026-10-15. Baseline: `e62d32aba10e9aa0f11c14a0e5a5ee0d1ba38a5d`. The user authorized a payment address where the Pons creator can send funds, which PoPL allocates to NFT rights. This is an undeployed development candidate, reviewed internally by Codex and a separate AI agent. It is **not an independent external audit or funded-deployment approval**. No public-chain transactions, signing, website or server changes occurred.

## Implemented behavior

`ZZZFeeController` creates one permanent `ZZZRewardReceiver` for an already-active canonical bucket after sealing, through existing timelocked governance. There are at most 16 inboxes; they are immutable helpers rather than another sealed module. Their controller, bucket, original currency pair and optional 18-decimal native wrapper cannot change. An inbox cannot be the immutable mint-proceeds recipient.

The creator sends plain ETH or admitted pair ERC20 tokens. Anyone can process pending funds; the keeper does so using the existing constrained signing, nonce, receipt and budget path, including during pause/remote custody. ETH becomes the configured ERC20 wrapper. Actual measured funding receives the existing 50% bucket-share owner / 30% global contribution Power / 10% compound / 10% buyback allocation. Current NFT owners claim funded ERC20 rewards. No expected creator percentage, historical revenue or 34% TVL entitlement is assumed.

Before any activation/top-up changes shares or Power, Vault settles every registered inbox and its old raw-unit dust. It repeats global settlement after entry balancing and after the final LP mint/increase. Late compounding belongs to incumbent NAV; deployment is rechecked and a final pending-payment/dust barrier precedes the owner checkpoint and share issuance. This prevents new contributions capturing already-received funds, including payments delivered by token callbacks and another bucket's collective allocation. Late idle cannot satisfy the $500 marginal deployed-LP activation minimum. NFT transfers carry unclaimed rights; claims remain available while strategy operations are paused.

Creator receipts have a separate cumulative funded counter and cannot discharge authenticated remote-reward liabilities. Payments can be allocated at home while custody is away; the home compound reserve awaits compatible maintenance after return. Constructor-time prefunding is quarantined. Unsupported tokens remain unallocated, with no administrator rescue, redirection, withdrawal or receiver replacement. [Payment/operation details](../../docs/EXTERNAL_REWARDS.md).

## Executed verification

| Check | Result | Evidence |
|---|---|---|
| Full offline Solidity | 279 passed, zero failed; one expected opt-in fork setup skip; 20 suites | [tests and mock gas report](final-tests-gas.log) |
| Funding integration/security | 43 cases passed, including a 1,000-case funding conservation fuzz test and seven late-callback regressions | [complete 45-case targeted run](external-agent-audit.log) |
| Funding stateful stress | 256 runs x 256 depth = 65,536 scheduled handler calls; zero unexpected reverts; invariant and deterministic sequence passed | [seed/source identities](extended-funding-invariants.json), [log](external-agent-audit.log) |
| Python | 255 inventory; all 251 portable Windows cases passed with no skips; four unchanged Unix-only assertions retained for Ubuntu CI | [summary](python-windows-portable.json), [log](python-windows-portable.log) |
| Real dependency fork | Nine passed with zero failures/skips; new plain ETH/ZZZ payments wrap through deployed WETH and fund claims without changing LP/shares | [fork log](robinhood-fork-final.log) |
| Standard EVM sizes | All 17 core modules and the helper pass; Vault runtime 24,212 / init 25,091; Fees 24,203 / 24,764; inbox 4,265 / 5,801 | [artifact sizes](module-sizes.json), [full build](final-build.log) |
| Slither 0.11.6 | Successful 89-contract / 102-detector analysis; all 160 findings reviewed: 78 conditional false positives, 62 accepted risks, 20 informational | [raw report](slither-final.json), [source-bound coverage](../production/slither-review.json), [log](slither-final.log) |
| Separate internal review | All 91 High/Medium findings reviewed against 26 final source/toolchain hashes; the discovered entry-callback accounting window was fixed and regression-tested | [review scope and result](secondary-review.md), [individual findings](secondary-review.json) |
| Retained Forge diagnostics | 48 warnings individually reviewed: 42 casts and six test-only unchecked transfers; 33 production / 15 test. All 98 informational notes are separately recorded, including 20 positional-struct field-order checks | [dispositions](forge-lint-review.json) |
| Source/event consistency | 23 Solidity source files; 17 core modules plus one helper; 53 event schemas | [source report](../source-checks.json), [schema](../../indexer/event_schema.json) |
| Production inventory | External funding requires exact-block complete inbox/wrapper identity observations and independently reviewed admission; the example remains blocked with 244 issues | [blocked gate result](production-config-check.json) |

The funding handler independently tracks received funds, pending balances, deposits and paid claims. It checks principal plus all custody/reserves and paid amounts against deposited principal plus actual external funding, including owner/Power checkpoints, transfer, pause and maintenance. It uses real accounting/custody contracts behind a fake LP venue and synthetic feeds. Ineligible handler calls may return without transitions; scheduled handler count is not a count of successful user transactions. Native-wrapper failure/reentry/quarantine are separate deterministic cases.

The fork remains pinned to Robinhood block 88,544,093 / hash `0xc44dc8c95c6011b991312179f532935c2d94e4f21b84899d23896fd0fe01d490`, enforcing eight deployed dependency runtime identities. It uses an explicitly different hookless WETH/ZZZ pool created only on the local fork, synthetic $1 feeds and a mock access controller. The actual selected native-ETH/Pons-hooked pool is checked and rejected. The new test proves actual WETH deposit/token transfer/claim behavior within that boundary; it does not prove Pons revenue entitlement, support its hook, establish a production ZZZ price or send a public transaction.

The compiler is unchanged: Solidity 0.8.26, Cancun, via IR, optimizer runs 1, Yul optimizer disabled. EVM size limits were not raised, and no delegatecall/library custody authority was added. Artifact hashes contain immutable placeholders and are not actual deployed runtime hashes. Constructor arguments add to creation-code size. The runtime margins of 364 bytes for Vault and 373 for Fees still require deployment review.

## Remaining release and economic limits

- The actual native/Pons LP adapter, production bridge/asset backing, production valuation/outage policy, authorities, staged operating recovery, independent external audit and remediation remain required.
- Rewards describe actual received and processed funds. No historical-period reconstruction or creator payment guarantee exists. A late payment may benefit NFTs that joined before it arrived.
- Sub-ten-unit dust settles to incumbent owners before membership/departure, including all inbox buckets before global Power changes. This deliberately differs from exact 50/30/10/10 for those raw units and is not universally negligible USD; asset values and top-up frequency need economic review.
- A broken admitted token/wrapper may block global membership settlement and its bucket's maintenance. The bound of 16 limits iteration, while worst-case funded gas and availability still need staging/admission review. No administrator can erase liabilities or discard an inbox to bypass that barrier.
- Wrapped-native rewards are claimed as ERC20 tokens. Unsupported or constructor-prefunded assets have no rescue path. Home compound reserves paid while away are not automatically transported or reinvested remotely.

Historical shared-LP evidence in [pooled](../pooled/README.md) and the [previous source-bound review](../history/slither-review-e62d32a.json) is retained for its original revision, not reused as verification of the new intake. Passing coverage/tests demonstrates the documented scope and assumptions, not exploit absence or permission to deploy.
