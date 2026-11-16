# Coverage, system interactions and evidence limits

Baseline revisions and exact per-file hashes are in the companion ledgers.
“Reviewed” means the stated source/function-family inspection, not exhaustive
execution, independent approval or absence of defects. Inventory-only entries are
explicit and must not be counted as freshly reviewed bodies.

## Components and entry points

| Component | Scope / authority | Coverage evidence |
| --- | --- | --- |
| Access, bootstrap, policy and factories | Fixed binding graph, seal/role handover, future policy revisions, typed parents and inert code carriers. Governance is one human operator; deployment/bootstrap/keeper/guardian remain distinct capabilities. | [Contract review](FINANCIAL_CONTRACT_REVIEW.json), deployment-authority regressions; prior normal construction/size evidence. |
| NFT, SeaDrop helper, VRF and renderer | Original recipient versus owner, quotas, zero-value callback, no reroll, ordered finalization, trait/activation distinction, four art paths and terminal/successor context. | Contract/consumer/frontend review; exact metadata2 constructor/read evidence reused. Actual OpenSea/VRF/content unqualified. |
| Vault, Entry, Registry and assets | Single contribution pool, ETH/fixed ZZZ only, exact input/allowance, incumbent checkpoints, entrant-only placement, marginal LP and share accounting. | Contract/financial consumer review and prior exact Entry/contribution scopes. |
| Manager, typed executor, Balancer and Math | Both physical legs, actual-core quote/single swap, recipients/callbacks/approval cleanup, active-main and residual-floor checks. | Contract ledger and installed core/periphery source review. No fresh market/ordering proof. |
| Strategy, confirmation and portfolio policies | Manual ranges,85% geometry, independent corroboration, sampled window/gap, cooldown/jitter, mode transitions and optional emergency masks. | Contract/backend/consumer review; prior confirmation/recovery source evidence. |
| Oracle, pricing and composite source | Two paths, rounds/ages/agreement, captured own-transition proof, live final validation, reference versus target, proxy/upstream trust. | Contract/consumer review; dated market evidence reused, no new public reads/admission. |
| Rewards, exact LP engine, fee controller and canonical companion | Raw-unit conservation, share/active membership changes, pending/phase/direct credits, claim/conversion and import/export. | Contract/consumer ledger; exact historical integration and current source/static scopes remain distinct. |
| Royalty ledger/factory and claim router | Original currencies, opening cohort, exact tickets/cursors, registration capacity, outages/deferred rights, current-owner claims and unallocated recovery. | Contract/consumer/frontend review. Malicious-token universal liveness is not promised. |
| Migration, custody validator and canonical modules | Residual close/consolidation, full move/park/resume, terminal allocate/pay, V10 source retirement/import/backing/abort. | Contract/unsigned-tool review and prior actual local manual/holder-return/handoff source scopes. |
| Keeper and persistence | Pending-first reconciliation, nonce fencing, receipt identity/cost, late budget gates, independent harvest scheduling, bounded retries and reset acknowledgements. | [Backend ledger](backend-coverage.json); new state-presence checks. No live service/Unix rehearsal. |
| API, indexer and history | Bounded admission/framing, exact chain/profiles, canonical block/log provenance, reorg/commit boundaries, current ownership and non-double-counted earnings. | Backend/API/financial-consumer records; inventory-only/historical modules remain labelled. |
| Website and signer | Demo versus unconfigured integration, provider/account/chain lifecycle, exact approval/review, saved-hash recovery, confirmed target-only art and financial semantics. | [Frontend ledger](FRONTEND_COVERAGE.json); five new direct-profile tests. No current-profile real wallet/host acceptance. |
| Deployment/reviewer tooling | Exact constructor inputs/build trust, unsigned output, no adoption; archive fixture/provenance closure and historical compatibility. | Authority/bundle baseline and postfix regressions; no deployment/sealing. |

The source-bound callable catalogue is mechanically checked:40 concrete
contracts,963 functions,40 constructors and13 receivers. It also documents
inherited concrete callable interfaces, but is not a substitute for internal
source review. The61-file contract ledger includes implementation/library/
interface functions and reviewed installed dependencies. Python AST function
spans and37 selected website artifacts provide separate inventories. Historical
profile decoders are intentional compatibility, not candidates for blind deletion.

## Financial conservation obligations

Reconcile raw units before USD valuation. For each asset, classified custody
must cover principal, idle, designated compound, earned liabilities, buyback,
royalties, terminal unpaid and canonical obligations without double counting.
Physical LP is custody valued through its token amounts; raw liquidity units
from different ranges are never summed as NAV.

| Transition | Required conservation / separation |
| --- | --- |
| Actual harvest | Received LP fee units equal individual+collective+compound+buyback allocation plus the documented boundary handling. No second split on claim/conversion/import. Upstream Uniswap fee rounding differs from distribution of units actually received. |
| Contribution | New holder shares reflect net added aggregate NAV; incumbent principal/residual/idle/compound and previous claims cannot fund input/deployed-LP floors. Global active membership changes only at authenticated activation. |
| Exact LP allocation | Pending/raw tree phases plus direct credits are backed; claim transfers remove the same liability. Transfer moves the NFT's unpaid rights, not an extra allocation. Whole-unit conservation and distribution fairness are separate questions. |
| Royalties | Allocated outstanding+paid+explicit opening/unallocated/deferred classifications reconcile with observed receipts and balance deltas. Unknown/unreadable receipt timing is not retroactively reconstructed. Recovery cannot consume already-earned or imported backing. |
| Conversion/buyback | Spend only the designated book/reserve; actual output preserves its attribution. Output is not new earned revenue. A burn requires actual fixed-ZZZ sink evidence; ETH is not burned as ZZZ. |
| Compound | Designated compound/attributed idle changes into principal without new shares or extra rewards. It must not consume holder reward, royalty or buyback liabilities. |
| Terminal exit | Actual returned ETH/ZZZ plus allowed compound becomes classified principal, allocated by NFT shares. Paid+unpaid balances reconcile; failures stay backed. Old rewards/buyback and future royalties stay separate. |
| Canonical handoff | Every domain/phase/raw unit and classified backing moves exactly once; source retirement and destination activation are exclusive. Partial/aborted funding cannot become an active second ledger. |

These equations are review obligations supported by the cited exact historical
tests and current source-family review; no new independent accounting simulation
or formal proof is claimed in this audit.

## Lifecycle and cross-operation cases

| Operation/case | Normal behavior and ordered interactions | Failure / recovery boundary |
| --- | --- | --- |
| Mint, team/allowlist/public | Pinned SeaDrop settlement, exact quota/original-recipient count, dormant NFT and authentic VRF request. | No direct paid-mint workaround; pending draws cannot be rerolled. Review platform/payer/sale changes separately. |
| Activate/grow, either asset | Owner/lifecycle/policy/price review → checkpoint → entrant-only swap/increase MAIN → marginal LP/share write → final callbacks → confirmed read/art. | Whole on-chain failure rolls back assets/state; gas remains spent. Exact approval is distinct from the subsequent contribution. Refresh review after change. |
| Concurrent entry/transfer/maintenance | Block execution serializes actual state; later reviews may become stale. NFT identity/owner/state/policy/expiry must match at execution. | Do not reuse stale output, guess zero or auto-resend. Approved spend is not evidence that LP increased. |
| Main in/outside range, either price direction | Raw market need, sampled readiness, cooldown and service jitter are distinct. Physical/reference disagreement blocks ordinary triggered adjustment. | Fresh healthy confirmation required after observed reset. Sampled checks cannot attest movements between observations. |
| Range change while in range | Explicit desired geometry may apply at the next cooldown-eligible replacement. Existing fixed ticks do not move with spot. | Pending identity/control changes invalidate old evidence. New simulation if custody/floors/policy/expiry changes. |
| One→two / two→two | Close/value both old legs, one bounded balancing swap if needed, main floor and at most one residual in the same pool. | Failure atomically restores both; do not add a third leg or ignore mixed/filled residuals. |
| Two→one mode OFF | Guarded full replacement consolidates all backing; raw close merely creates attributed idle. Same-main operation can reinvest residual without closing main if its own guards hold. | No automatic emergency fallback if spot leaves the existing main; explicitly choose guarded fresh bounds or reviewed forced operation. |
| Residual raw close / same-main consolidation | Harvest appropriate legs, retain/reinvest exact principal; preserve main ID/ticks when required. | Raw close is not a complete reinvestment. Price-dependent guarded reverts are intentional; emergency retained guards are operator-selected. |
| Hourly harvest | Collect both legs and allocate actual receipts independently of swap-bearing jobs. | Internal successful harvest coalesces only through authenticated receipt provenance; submission/NAV change is not success. |
| Compound | Increase existing range from designated funds; separate interval and service in-range/threshold priority. | A malicious authorized keeper can ignore service-only selection policy within contract bounds; accepted exposure remains tracked. |
| Claim / transfer before or after claim | Current owner receives backed rights; approved transfer operator is not automatically claimant. Selected token/entry gas batches preserve per-item rights. | Hostile token/recipient isolation and explicit backed fallback;32 entries is not a promise of fitting gas. |
| Mint end / one-hour royalty opening | Governance-selected official sale end, exact cutoff cohort; later activations earn only later eligible receipts. | Zero eligible weight leaves explicit unallocated funds for governance; delaying claims alone would not implement cohort accounting. |
| Royalty currency fault/registration/recovery | Deferred entry protects prior eligible NFTs. Capacity expansion is reviewed, separate from contribution inputs. | Frozen/rebasing/taxed/lying tokens may remain unusable; do not sweep liabilities or manufacture a healthy balance. |
| Park/resume and manual C/D | Pause/governance, exact custody/ticks/amounts, caller floors/expiry, selected financial mask and final proof. | Unknown RPC/revert cause stays unknown. Forced operation may deliberately bypass financial constraints, never authority/custody/accounting. |
| Terminal exit through complete payment | Governance begin/close/allocate/distribute; both physical legs end, current owner receives proportional tokens; NFT/royalty/old-claim continuity. | Failed receiver remains backed. Transfers/payout races resolve at execution, not from an old UI owner list. No principal reopening or post-exit canonical handoff. |
| Pre-exit same-chain replacement | Frozen coherent domains, source/destination/runtime/plan binding, exact raw restore/backing, funded abort or atomic terminal source commit. | Pending reveal, live residual, incompatible holder/successor or missing backing blocks. No bridge/post-halt implementation is implied. |
| Desktop/server/RPC/indexer outage | Preserve pending-first journal, locks, headers/raw logs/WAL/backup and read-only stale/unavailable reporting. | Recover same hash and reconcile nonce/fees before new intent. No journal rewrite, duplicate signer or assumed absent-state reset. |
| Website offline/account/network change | Preserve account/sequence identity, saved transaction hash, confirmed NFT snapshot and unconfigured integration boundary. | No new action on uncertain submission; only the affected confirmed contribution may animate artwork. No stale account or fake demo data substitution. |

## Authority, settings and longevity

Public reads/valid callbacks/holder claims/transfers retain their legitimate
permissions. Governance-only configuration, manual emergencies and terminal
batches remain distinct from limited keeper upkeep. Sealing fixes implementation,
parent and fixed-token identities, while reviewed bounded policy/routes/sources
remain future configurable. No timelock or independent governance veto exists.

Longevity review includes finite four-bucket reservation, reviewed16→64 royalty
capacity, append-only raw history/tree costs, provider/API retirement, price/feed
control changes, metadata persistence, gas/spend budgets, recipient failures,
key/host loss, canonical lineage and unsupported tokens. Perpetual operation is
conditional on usable dependencies and authorized operators; permanent chain
failure, arbitrary successor honesty and hostile-token transferability are not
solved by this code or this review. The user-deferred load campaign remains
deferred; it was not restarted to produce new evidence.
