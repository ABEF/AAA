# Remaining271 findings — individual review and corrections

**All271previously unreviewed records have now been checked individually against
the current project.** Combined with the earlier39, every original ID in the
310record registry has an individual review across these two source-scoped
passes. This is not310independent bugs, a single fresh full-project execution
campaign, or a declaration that every obligation is resolved. Production remains
**NOT APPROVED**.

[Reading index: every271ID](INDEX.md) | [Coverage and record hashes](COVERAGE.json) |
[Implemented corrections](FIXES.json) | [Verification](VERIFICATION.md)

## Method and coverage

The frozen contract baseline is `6cfa4f1d478c3d15470519801f9703f9f8a8d656`;
website references use `e1d698868d32572bc5f04b3f683d2919234f5f19`. Each original
record was read, including its distinct subclaims, failed attempts, retained
evidence and remaining requirements. Current functions, call boundaries,
configuration/procedure or exact historical artifacts were inspected for the
relevant claim. Conclusions are individual rather than inherited from topic,
age, a similarly named feature or an aggregate passing count.

| Partition | Individually reviewed | Full assessments |
| --- | ---: | --- |
| Contract ownership, custody, entry, pricing, routing and authority |60| [Contract review](contracts/REVIEW.md), [records](contracts/FINDINGS.json) |
| Backend, history, keeper, operations and release |94| [Backend review](backend/REVIEW.md), [records](backend/FINDINGS.json) |
| Evidence, frontend and metadata |87| [Evidence/frontend review](evidence-frontend/REVIEW.md), [records](evidence-frontend/FINDINGS.json) |
| Additional entry, portfolio, confirmation and routing records |30| [Contract supplement](contracts-supplement/REVIEW.md), [records](contracts-supplement/FINDINGS.json) |

The four sets are disjoint and exactly cover the previously remaining set.
The global verifier checks271unique IDs, original JSON pointers and record
identities, existing Todo owners and210distinct referenced source/evidence
files. That file count is not210new full-file audits or execution tests.
Original sections/report identities remain available; full original records
already preserved in the earlier tracked registry are not duplicated here.

Baseline-labelled source hashes/excerpts come from the exact Git blob, not a
simultaneously edited working file. New corrections have separate post-baseline
hashes and proof. The index's baseline defect descriptions therefore do not
assert that corrected code still has the defect; use [FIXES](FIXES.json) and
the explicit coverage overlays. No original report or failure is relabeled.

## Concrete improvements implemented

| Correction | Result and boundaries |
| --- | --- |
| Initial keeper simulation work was not explicitly gas-bounded | Both initial `eth_call` and `eth_estimateGas` now request the existing `max_gas_limit`; invalid new-work caps reject before new-work provider calls. Separate simulation data preserves the eventual intent/journal shape. Signing still uses the rounded125%estimate and the same gas-price, transaction/day, nonce, lifecycle and pending-first guards. No automatic wider retry or budget increase. Requested gas is not a hard DNS/socket timeout or provider-honesty guarantee. |
| Successor execution1 leaked into historical peers | Each predecessor accepts its own exact `execution_price_version:0/1`, with omitted0 and no inheritance. Actual runtime/getter/canonical/role checks remain. Compatible V10/accounting7 LP2/LP3 peers no longer fail solely because the successor uses another execution capability. Provenance emits1 only for execution1, preserving original0 shape and financial totals. No new live Oracle dependency for healthy claims/history. This reader correction is not an actual mixed-runtime EVM handoff rehearsal. |
| Offline artwork catalogue admission accepted ambiguous values | Strict duplicate/nonfinite/exponent-overflow JSON rejection, exact integer code lists and nonempty integer byte masks prevent boolean/fractional values or zero masks from producing source. Valid catalogue/library output remains exact, including normal/optimized Python behavior. No catalogue, artwork, assignment or Solidity library was regenerated. This is an offline build-admission defect, not a demonstrated deployed financial exploit. |
| Operator errors named obsolete profiles | Five keeper error descriptions now match threshold-based maintenance and actual supported accounting/portfolio/routing profiles. The original predicates are unchanged; reversing only those strings proves whole-module AST equivalence to the tested source. |
| New regressions were absent from the specialized keeper selection | The keeper runner now includes the six new simulation-envelope methods; inventory-only verification executes zero tests. A stale accounting5/6 lineage assertion now checks its actual four Uniswap dependencies and no SeaDrop; mint2 shared-SeaDrop coverage remains. The original failed attempt is retained. |

See [backend corrections](backend/CORRECTIONS.json) and
[catalogue admission](evidence-frontend/GENERATOR_ADMISSION.json) for exact
before/final source hashes, execution scopes and limitations. No Solidity
implementation, ABI, economic allocation, entitlement, authority, risk cap,
default gas budget or service policy changed. All61production Solidity sources
retain the earlier exact normal-build identity.

## Historical conclusions that matter now

- Earlier outside-only/one-percent-centering and900-second policy descriptions
  are superseded by approved85%-of-centre-to-boundary triggering,600seconds of
  sampled confirmation, maximum gap300, checks240, durable jitter60–300 and the
  hard12-hour minimum. Sampling is not uninterrupted history or MEV immunity.
- The original active-main route-viability gap is source-corrected: actual stored
  post-swap ticks are screened before route ranking and rechecked at execution.
  Bounded search still does not guarantee a feasible global best route.
- Main/residual tracking, same-main consolidation, raw residual-only close,
  desired mode changes, parking and terminal holder return are distinct. Raw
  close can leave owned attributed idle. No third physical leg, principal sweep,
  external custodian, bridge or automatic reopening is restored.
- Exact-unit LP/royalty allocation solves allocated rounding leftovers, not
  upstream fees never received, sub20raw fee-split carry, zero-cohort funds,
  missing history or the transferability of every pathological token.
- Original-currency royalty4 supersedes royalty swaps; retained LP ZZZ-to-ETH
  conversion is a separate feature. Intrinsic rarity1/2/3 differs from dormant
  eligibility. One-hour opening, deferred currencies and reviewed capacity remain.
- Mint2/SeaDrop, V10 and source10 unsigned readers are source-implemented.
  Source9 retains LP2; source10 alone optionally admits execution1/LP3. Actual
  marketplace/provider/site acceptance and rollout are still open. Historical
  direct mint and extension fixes do not authorize public signing.
- Governance-only terminal batches supersede earlier permissionless/keeper
  principal-delivery guidance. Holder reward/royalty claims remain owner actions.
  Preserving an escrow address during canonical handoff is not proof of its
  successor compatibility. Permanent bucket reservations must be planned.
- Earlier compiler/build/static/gas/browser counts and reports retain exact
  source scope. Current size margins are not their older635/237/39/360figures.
  The inherited indexer tool-result claim of seven checks was corrected to its
  original25+3=28; no historical result was rerun or edited.

Current owning guides were corrected: governance/OpenSea source-versus-live
status; accounting7/V10 and optional LP3; custody5 versus historical4; terminal
metadata7; exact per-peer execution inputs; requested simulation gas versus
signed/fee budgets; source-bound evidence reuse; and catalogue admission.
Function/input/permission tables remain unchanged because contract ABIs did not
change. README, sole Todo, feature reference, findings, roadmap, release record
and repository context/handoff are synchronized to these boundaries.

## Still open, accepted or dependency-qualified

The individual maps retain concrete remaining actions under existing stable
Todo IDs, rather than inventing a competing checklist or marking all rows green.

| Area | Remaining work / decision boundary |
| --- | --- |
| Real prices and execution | Two genuine ZZZ source paths, ETH publication/liveness, bidirectional external depth excluding PoPL LP, useful conversion/activation routes and actual token/proxy/burn behavior remain unqualified. Spot/no-TWAP and immediate governance are selected design choices, not manipulation resistance proofs. |
| Gas and deployability | Controlled cold Entry still exceeds the unchanged12M default. Qualify optional policy2 against actual transaction/block/provider limits, headroom and total fees. Retained normal runtime headrooms remain Vault32/Oracle88/Manager190bytes; exact constructor/deployment work remains a gate. |
| Strategy trust and economics | The user's keeper-side compound wait is not an on-chain restriction against a compromised authorized keeper. Repeated permitted losses, realized swap economics, idle recovery thresholds and variable range/residual economics remain reviewed operating choices. |
| Dependency fee timing | A malicious/upgraded admitted callback producing a late fee credit during increase remains an unverified, dependency-qualified question. Ordinary transactions cannot interleave atomically. No speculative guard, share-loss assertion or new custody right was introduced. |
| Long-term availability | Actual RPC/OS supervision, Linux locking/child containment, signer fencing, off-host alerts, key/funding/host loss, archive completeness/WAL restore, expanded currency and maximum-state workloads need real operating evidence. Code/hash consistency alone cannot attest a running host or disprove coherent dishonest data. |
| Release acceptance | Actual authorities, OpenSea phases/fees/payers/eligibility, VRF, metadata hosting, matching API/site rollout, real escrow cutover, sustained recovery and independent audit/remediation remain open. |

A stale explanatory WETH comment remains a nonfunctional maintenance note; the
actual Registry admits only native ETH/fixedZZZ. A comment-only Solidity edit
would change metadata/runtime identity without improving execution, so no
needless compiler/static/rebinding campaign was introduced. Historical codecs
and the distinct optional v3/WETH earned-LP conversion remain intentionally.

Source/docs publication is main-only. It changes no deployed contract, public
transaction/signing, site/service, existing Anvil/NFT/LP/balance/journal,
checkpoint or user-paused heartbeat. Protected unrelated changes stay intact.
