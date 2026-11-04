# Whole-history findings reconciliation and improvement

November 4, 2026. Baseline main `a915b6a12e42dac0685ff9cad5f0fa17bfd78e23`.
**Production NOT APPROVED.** [Execution prompt and two scope reviews](AUDIT_PROMPT.md),
[original finding records/current interpretation](FINDINGS.json),
[corpus catalogue](REPORT_CATALOG.md), [task history](TASK_HISTORY.json),
[verification](VERIFICATION.md).

## Result

Not every historical concern is solved. Some mechanisms were deliberately removed,
some defects were corrected at their recorded source revisions, and several
implementation and operating requirements remain open. This reconciliation
preserves those distinctions instead of treating an old PASS, a completed source
task or an obsolete design as current production acceptance.

The investigation reproduced and fixed a recurring verification defect: the
static-analysis CI entrypoint still selected the authority review from before
two manual-recovery view changes. Current analysis and internal dispositions
existed, but the strict default rejected four differences. The new default uses
a complete current-source record derived from that captured analysis, retaining
all 471 finding descriptions, fingerprints, rationales and review provenance.
The matching rules are unchanged. A regression now checks that the published
default binds the actual source inventory even before an analyzer job runs.

No production Solidity, ABI, storage, financial policy, owner entitlement or
permission changed. No deployment, public transaction, service/site rollout,
Anvil reset, journal rewrite, signer change or heartbeat restart occurred.

## What was covered, and what the counts mean

- 530 tracked current contract narratives: 426 report Markdown files, 99 guides and
  five root documents. The report index is mutable navigation; original reports
  remain immutable inputs.
- 3,098 distinct contract-main narrative/ledger blobs from the first October 14
  main commit through the baseline; 2,407 historical-only text versions, 162 structured
  task-ledger versions and five deleted guides. Identical normalized current
  text reuses its reading rather than pretending to be a new obligation.
- Nine current website narratives and 233 distinct website-main narrative blobs,
  read-only. Two unrelated local-only October 16 draft reports were also read,
  hashed and preserved without staging or promoting them to published evidence.
- 310 overlapping imported finding rows retain their full original JSON records,
  exact matrix pointers/hashes and current-domain ownership. The earlier 41-row
  five-report matrix was already subsumed by the 75-row later matrix; it is not
  added again. Five subsequent November 3 findings and later authority, exit,
  lifecycle, indexer, confirmation and manual reviews are mapped separately.
- 398 unique pre-ledger unchecked lines and 6,789 deduplicated recommendation/open-
  context paragraphs were extracted for comparison. These include repeated
  snapshots, generated references, historical plans and limitations; they are
  neither 6,789 bugs nor 6,789 independently executed closures.

Full-text extraction and provenance coverage are not a claim of exhaustive
state-space security review. Private conversations/attachments not preserved in
the repositories, abandoned branches and every raw historic log were not newly
audited. Reported executions retain their original artifact/source boundaries.

## Corrections and materially different interpretations

| ID | Finding / correction | Current consequence |
| --- | --- | --- |
| HR01, low/verification integrity | CI's default source-bound static review became stale again after manual-view edits. | Corrected default/full strict record plus current-source regression.44focused methods pass; no analyzer or contract-suite rerun. Historical HC-51, RO-11 and later/T05 retain their prior source scopes and now point to this recurrence. |
| HR02, documentation | The development guide still called475old flags/current LP-lifecycle review the current default. The idle task called Budget3/upkeep2/outside-only current; history wording called accounting3 current. | Replace current-looking labels with compound4/maintenance3/85%threshold/accounting6 and the actual strict default. Dated historical acceptance evidence remains historical. |
| HR03, obligation classification | Lifetime complete history can be mistaken for a provider-only gate after streaming/startup fixes. | Explicit OPEN IMPLEMENTATION/design for authenticated long-lived archive/checkpoint/read-model evolution; current bounded replay and streaming do not supply it. Existing financial-history owns it. |
| HR04, decision provenance | Removed tasks can look forgotten, while obsolete mechanisms can look unfinished. | All five disappearing structured IDs were deliberately retired in82ba6ed: four creator-payment tasks and bridge-operation. Preserve funded receipts, safe recovery and dependency review under current tasks; do not revive inboxes/bridges. |

## Important old recommendations assessed against current behavior

| Earlier concern | Current interpretation |
| --- | --- |
| Redundant pre-Vault Entry conversion | Removed in explicit direct Entry3. Historical tuples/readers remain; earned-reward converters are still necessary. |
| Power, per-NFT physical LPs, Pons creator payments, third contribution inputs | Superseded by fixed ETH/ZZZ, shared NAV shares and actual hookless LP fees. Receipt backing, cohort checkpoints and per-NFT rights remain essential. |
| Zero-delay timelock and governance/operator distinction | Direct one-human governance is the approved authority model. Keeper/guardian capabilities remain separate; malicious configuration and lost keys remain real trust/liveness risks. |
| Custody-address/bridge exit | Removed. Paused governance terminal return pays actual ETH/ZZZ to current NFT owners; old claims/transfers/future royalties remain. Pre-exit same-chain canonical replacement is separate. |
| Outside-only/15-minute buffer, cooldown observation proposed | Superseded by85%centre-to-boundary,600s sampled window/maxgap300/source240 and near-end cooldown enrollment. Sample gaps/inclusion, not continuous history, remain operating limits. |
| Optional residual would accumulate unbounded positions | At most one residual in the same pool. Both legs remain valued/harvested/closed; modefalse requests merge, not backing deletion.60/40 is a replacement-time tradeoff, not a continuous optimum. |
| Highest quote can hide an active-main alternative | Later lifecycle code validates main activity before ordinary candidate ranking; final callback/mint checks remain. Bounded candidate search cannot promise a global optimum. |
| Closing residual or forced replacement must bypass every failure | Manual guard groups are explicit; mandatory custody, exact balances, structure, terminal lifecycle and external dependency failures remain. Emergency current-pool redeployment can lose almost all principal. |
| Idle-only jobs versus new contributions | Mechanism exists; job/threshold economics remain an operating choice. Idle stays incumbent principal and can reach the separate5%entry-blocking ceiling. No entrant subsidy or generic sweep is authorized. |
| Historical stablecoin input tests versus royalties | Stablecoins are not current principal inputs. Separate royalty currencies/outage cohorts and optional conversion-wrapper dependencies can still be valid. |
| Failed royalty currency blocks every activation | Isolated deferred registration preserves prior cohorts; healthy rights continue. Exact whole-ledger capture can still fail on unreadable backing; do not waive liabilities. |
| Old local nonce35 mint cleanup | Historical, narrowly authorized incident; browser completion was not established. It is not new permission to delete pending records or reset the current Anvil. |
| Broader100-user testing | Deliberately deferred by the user. Two-wallet reports are scoped evidence, not production scale acceptance. |
| No1000mint sellout, lost owners, rejecting receivers | Supply is a cap, not required participation. Shares/memberships follow actual NFTs. Lost/dead-address ownership and rejecting/frozen recipients cannot be solved by silently redistributing rights or inventing administrator recovery. |
| Long-lived canonical aliases and four buckets | Bounded custody slots do not bound lifetime aliases or relay work. Reservations are permanent; practical cutover capacity/relay/escrow/gas still need qualification. |
| Hashes prove audit/keeper behavior | reviewHash identifies reviewed material; source/runtime/snapshot commitments have different jobs. None proves honest live execution, proxy behavior, author identity or independent approval. |

## Material work still open

These are reconciled requirements, not a second task-status checklist. The
[sole Todo](../../TODO.md) owns their statuses and detailed acceptance criteria.

| Remaining requirement / unanswered evidence | Owner |
| --- | --- |
| Actual independent ETH/ZZZ USD feeds, proxy/update/sequencer assumptions,3%agreement, reviewed RPC/trace support and fail/recovery behavior | [Dual feeds](../../TODO.md#task-dual-price-qualification), [ZZZ-team questions](../../TODO.md#creator-tasks--zzz-team) |
| Actually usable balancing and ETH-settlement routes at captured caps/depth, including retained default1%conversion; token transfer/burn behavior | [Routing](../../TODO.md#task-lp-execution-routing), [LP settlement](../../TODO.md#task-lp-eth-settlement), [royalties](../../TODO.md#task-royalty-eth-settlement) |
| Supported VRF/coordinator/subscription funding and original pending-draw drain; no reroll | [Fair draw](../../TODO.md#task-fair-draw) |
| Recipient-aware supported OpenSea primary-mint code, exact gross/net platform economics and actual drop/reveal rehearsal | [OpenSea](../../TODO.md#task-opensea-mint) |
| Fresh source8/schema10 services and website consumer/receipt/approval/history integration, separate from served current3 and demo | [Preflight](../../TODO.md#task-native-production-preflight), [portfolio](../../TODO.md#task-portfolio), [wallet](../../TODO.md#task-wallet) |
| Authenticated lifetime incremental/archive/checkpoint/read-model implementation and integrity-preserving long-history performance | [Financial history](../../TODO.md#task-financial-history) |
| Chosen authorities, custody of keys, recurring gas/RPC/VRF/hosting/storage funding, backups/retention, Unix watchdog/lock and off-host restore/rotation | [Authorities](../../TODO.md#task-authorities-prices), [hosting](../../TODO.md#task-host-services), [recovery](../../TODO.md#task-keeper-recovery) |
| Economic idle thresholds, manipulation/front-run/back-run/turnover and hybrid residual risk at actual depth | [Idle/liveness](../../TODO.md#task-asset-liveness-dust), [strategy](../../TODO.md#task-security-strategy), [keeper](../../TODO.md#task-security-keeper-manipulation), [external actors](../../TODO.md#task-security-external-manipulation) |
| Exact constructor arguments, tight runtime limits, maximal two-leg/royalty/batch gas and realistic inclusion/sample timing | [Deployment/gas](../../TODO.md#task-deployment-initcode), [operating services](../../TODO.md#task-keeper-guardrails) |
| Permanent artwork hosting/CID/provider, complete evolution/metadata publication and marketplace refresh | [Metadata](../../TODO.md#task-metadata-ops) |
| Current-pair fork and distinct actual testnet rehearse boundaries; a mocked mainnet-pinned Registry is not testnet acceptance | [Fork](../../TODO.md#task-mainnet-fork), [testnet](../../TODO.md#task-testnet-rehearsal) |
| Practical same-chain canonical cutover/backing/escrow/alias/batch/abort budget; no post-exit or post-halt revival | [Chain recovery](../../TODO.md#task-security-chain-recovery), [destination capacity](../../TODO.md#task-destination-slots), [holder preflight](../../TODO.md#task-holder-preflight) |
| Frozen-release independent audit, remediation and explicit accepted-risk/sign-off decision | [Release](../../TODO.md#task-audit-release) |

No new question is required to settle the retired architecture. Provider choices,
authority addresses and actual deployment/operating evidence remain genuinely
unavailable, not inferred from old reports. Existing source features, old
qualification failures and deliberate deferrals remain visible together.

## Preservation and maintenance

Original reports, deleted-file Git blobs, untracked drafts and four protected dirty
files are preserved. Source scope/reference hashes and staged Python closure are
checked separately. Current README, findings, features, roadmap, release record,
development/operator procedure, context and sole Todo are updated to this map.
Nothing in this publication installs that source into an operating environment.
