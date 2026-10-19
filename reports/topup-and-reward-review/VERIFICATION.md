# Contribution minimum and NFT earnings: scoped verification

2026-10-19. Source candidate only; production NOT APPROVED. See the
[internal review](REVIEW.md), [operator procedure](../../docs/CONTRIBUTION_MINIMUMS.md)
and [source bindings](source-bindings.json). Main-only publication is established
by the enclosing commits in each repository, not by a deployment claim.

## Contracts

The recorded fresh offline run passes **91 Solidity cases**, zero failures/skips,
in AtomicActivationIntegration, ActivationEntry, EntryExecutionBudget,
VaultAccounting and PooledEntry. It includes existing fuzz/ownership/budget cases
and new exact/below-$5, native, converted six-decimal, depeg, direct-Vault and
higher-pool-minimum coverage. Test and production hashes remained unchanged
during the run. [Receipt](contract-checks.json) retains commands, hashes and results.

The same normal compiler run supplied **32 compiler-object size checks**, with
40 production source bindings: [size report](build-review.json). These are
objects, not 32 deployed protocol modules. Solidity 0.8.26/Cancun, via-IR and the
existing optimizer profile remain unchanged. Entry runtime is 13,592 bytes;
budget 15,172; Registry 12,619; Vault 24,557 (19 bytes spare). Dynamic constructor
arguments still require a concrete deployment check. No redundant full build,
full regression, fork campaign or static-analysis rerun was performed.

Earlier [royalty conversion](../royalty-conversion/VERIFICATION.md),
[operator controls](../operator-controls/VERIFICATION.md) and
[pool selection](../position-summary/VERIFICATION.md) evidence retains its original
source/dependency scope. Those reports inform the review; their totals are not
claimed as freshly executed tests of this entire changed candidate.

## Python/backend

**74 distinct affected cases pass** in three scoped executions: 64 activation,
local-edge, local-wallet and isolated-dollar-rehearsal cases; nine local-stack
cases after optional-history isolation; then one supplemental aggregate-state
case. These are separate runs, not a fresh 74-case combined command. No remaining
failure or skip in this inventory. [Run logs](python-tests.log),
[history isolation](local-history-tests.log), [supplement](local-history-supplement.log).

Coverage includes $5 early quote checks before approval/trace, exact currency units,
strict action/amount boundaries, sanitized optional history failure, fatal core
failure, non-retried terminal work budgets and skipping dormant earnings reads.
Existing $1 copied activation-generator anchors remain valid.

## Website

The affected inventory contains **102 distinct passing JavaScript cases**, including six supplemental calculation-audit cases. Initial
execution passed 94 and exposed two concurrency fixtures that still attempted $1
new top-ups. Correcting those inputs to $5 produced 58 passing UI/client cases;
the unchanged 38 domain cases retain their first passing result. The final markup
refinement reruns the affected local-client suite; unchanged domain/state tests
are not repeated. This is combined scoped evidence, not a single fresh 96-case run.
See [initial log](website-tests.log), [follow-up](website-followup.log) and
[final layout check](website-layout-tests.log). The subsequent [calculation audit](REWARD_CALCULATION.md) adds six cases and a fresh passing 37-case client run after aggregate-overflow isolation. Rarity, color style, palette and royalty weight share one row; pattern labels are hidden on cards/details while artwork and metadata retain them.

Syntax and the 5,588-file static build pass. Browser verification on localhost:4179
checks preserved wallet/holdings, compact regular-weight fee labels/values on one
line under centered LP attached, centered claimable and separate detail components.
The $4.99 top-up input rejects without financial submission. No demo reset was
performed. A saved $5 increase subsequently appears in the browser; this observation
is a simulation, not a public-chain receipt. Local contract-valued history requires
exact current NFT/chain/block provenance and all three priced components.

The saved demo has lifetime net credits but no dated net history for its original
NFTs. Displayed 24h is **Unavailable** where absent; newly activated zero-income
examples can show zero. Claims do not reduce total earned. Public website/server
and the existing port-8892 deployment were not upgraded. Restarting a separate
fresh disposable fixture is required to exercise the new contract binary there.

### Subsequent palette and payout-currency review

The palette text follow-up passes all **48 artwork/client cases**: 37 previously
listed client cases plus 11 artwork cases. This overlaps the earlier 102-case
inventory; it is not 48 additional unique tests. Syntax, artwork integrity and
static build pass again after the color renderer change. See
[the focused run](website-color-tests.log). A browser screenshot confirms Blue
and Ivory use separate colored text without highlights in the existing local app.

The [ETH payout audit](ETH_PAYOUT_AUDIT.md) adds source inspection and one read-only
local `debug_traceCall`, not a Solidity rerun. It reproduces mixed ERC20 LP/native
royalty payouts and verifies that claims were not consumed. ETH-only LP settlement
remains an open pre-seal task. A separate local input-token mint replenished the
user's test wallet without resetting the chain or changing payout currencies.

### Contribution flows, named fixtures and rollback follow-up

Latest selector decision: ZZZ/USDG/USDC/ETH; WETH remains internal. The old
TEST-1 session on 8892 is preserved. A separate named local deployment on 8893
uses the unchanged compiler-bound production core, disposable tokens, explicit
$1 mock marks, six-decimal stable inputs and pinned typed 1:1 fixture conversion.
Local ETH wraps separately before exact WETH approval/Entry. This is not evidence
of the real selected native pool or live public routes.

[The recorded rehearsal](named-input-rehearsal.json) contains **30 successful
local receipts**, including four mints and activation plus $5 top-up for each of
ZZZ, USDG, USDC and ETH. Each contribution checks confirmed LP value increased by
at least 99% of the selected mock input value. Wallet B was used; wallet A retains
the four seeded positions and its claimable balances. No public wallet was used.

[The forced-failure receipt](contribution-rollback.json) reaches ten nested token
movement calls before a deliberately impossible minimum-liquidity bound reverts
the LP addition. All tracked owner/Entry/router/Vault/venue token balances remain
identical. Native balance loss equals receipt gas exactly; the earlier explicit
token allowance remains. The transaction is intentionally failed, not a passing
real-market integration test. Production atomic Entry also wraps native ETH inside
the same transaction, unlike the explicit local wrapper preparation step.

The affected website run returned 81 passes and one bad new artwork-test ID; the
fixture ID was corrected from `flowing-arcs` to the existing `arcs`. Its seven-case
rerun passes, covering target-only contribution markers, claim-only reward refresh,
approval/wrap neutrality, unavailable unknown/failed reads, source-bound consent,
four fixed-identity preload states and the four-choice selector. The initial
backend run had six mock-fixture errors because the Mock fabricated an iterable
input inventory; explicitly declaring the legacy fixture inventory fixed these.
There are 40 passing launcher/HTTP cases, 12 wallet cases and five new named-input
cases across scoped runs. The final optional approval-label field has the five
named-input cases rerun. No broad unchanged Solidity regression was repeated.

New local fixture compilation succeeded; Forge's subsequent signature-cache write
initially lacked permission. The authorized cache follow-up skipped compilation
and exited successfully. The ordinary core artifacts remain source-matched.

Browser verification confirms Grow contains only LP amount and contribution
controls, with ZZZ/USDG/USDC/ETH options and no claim button. Image/details retains
the reward breakdown. Rarity is bold. Preload never chooses a future evolution:
the UI keeps confirmed artwork through approval/pending execution and reads actual
LP before selecting the updated state. The static 5,588-file build and syntax
checks pass. Native-only LP payout, production wallet hosting/concurrency and live
route/feed qualification remain open; release is NOT APPROVED.
