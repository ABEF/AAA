## Residual obsolete-code cleanup - 2026-10-25

Read [review](../reports/obsolete-code-20261025/REVIEW.md) and
[verification](../reports/obsolete-code-20261025/VERIFICATION.md), with publication
status checked separately in Git/receipt. Removed Registry-only WETH metadata
bookkeeping (five selectors/twoevents), orphan creator-payment measurement/tool
tests, unused finality/import declarations/imports and unreachable NFT_baseURI.
Actual converter wrapper checks, historical events/journals, Position/status ABI,
source/exit ZZZ pins, preparation lifecycle, same-chain handoff and custody remain.

Registry runtime9,987/creation41,366 saves2,040bytes. Its contributionPool storage
moves slot5to2: fresh-deployment source only, never patch existing Anvil/storage.
NFT/Vault/Rewards and four other runtime bodies match excluding compiler metadata.
31contracts/644functions; zero missing purpose/caller/value or top-level input notes.
10selected Solidity cases,3keeper-example and3API-profile cases pass.122inputs
ABI/AST compile and36normal gates pass. No fresh full regression/real-provider or
independent-audit approval. Access's29-byte minimal argument margin remains open.

Current keeper example explicitly uses accounting2/fee1 with separate journal
paths, no creator job, missing pins and live review still blocked. Operator/docs/
security/Todo requirements are current;65taskIDs/statuses preserved, no external
gate closed. Historical source and tests are archived, not current passing cases.
Preserve unrelated drafts, main only,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signer/null public DEPLOYMENT and paused monitoring. No deployment,
public transaction, website code/build/server or service operation. Production NOT APPROVED.

## Simplified ETH/ZZZ candidate - 2026-10-25

Latest user scope: native ETH and fixed ZZZ only for activation/growth. ZZZ is
bound once before sealing; no governance token replacement. Issuer migration
uses source-chain custody exit and a fresh reviewed deployment. Normal exit
converts to ZZZ; explicit raw exit sends the actual ETH/ZZZ pair without a swap.
Sealing requires matching nonzero contribution/normal-exit ZZZ identities.
Do not confuse the source-token restriction with marketplace royalty currencies.

Creator-payment receivers/factory, remote fee/proof intake, unused bridge types
and failure-only selectors are removed. Same-chain pool moves, trusted custody
exit/full return, royalties and complete same-chain ownership/ledger handoff stay.
Current fee profile1 uses15 helpers (new source-policy factory replaces the old
receiver factory), custody version2 and LP-only V3 canonical schema. Historical
profiles/events/journals stay distinct; no automatic migration or dummy bindings.

Read ../reports/simplification-20261025/REVIEW.md and VERIFICATION.md. Source-bound
reference covers31 contracts/649 functions;36 normal object gates pass. Access
creation plus minimal288-byte role arguments is49,123/49,152 (29 margin);
actual release role arrays need exact qualification. Vault runtime23,889/687margin.
122 Solidity inputs ABI/AST pass;87 selected methods pass on the recorded
pre-terminal-comparison source. Six final Access/retirement checks pass, including terminal-state fuzz1,000.
Four repeats are not extra coverage:89 distinct selected behaviors across two
source scopes, not a fresh full final-source regression. Backend40, API/keeper6 and fork-runner16 published-candidate (21dirty-worktree)
scoped methods retain their exact evidence boundaries. Current livefork
qualification is explicitly blocked before RPC/Forge until a native fixture
replaces the archived wrapped one. Publication is separate: inspect
Git and the eventual receipt, never infer a push from a local save.

Maintain sole Todo, features, roadmap, operator and callable-reference docs.
Preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signer/null public DEPLOYMENT and paused monitoring. No public
transaction/deployment/seal, website build/server or operating-service change.
Production NOT APPROVED; real dependencies/OpenSea/authorities/operations and
independent audit remain open. Main only.

## Service and callable-reference publication verified - 2026-10-25

Contract implementation `03a0d76` and website memory-only `e96cc38` are pushed
on main; remote hashes verified. Read [publication](../reports/release-services-20261025/PUBLICATION.md)
and [verification](../reports/release-services-20261025/VERIFICATION.md). Optional
Pyth reader, hardblocked current OpenSea/VRF qualification, frozen review tool
and32-contract/698-function reference are implemented. All top-level inputs
have notes; exact outputs/types/tuple fields and permissions are preserved.
17new Solidity/68gate+19package Python across scoped runs/10generator/38normal
object gates retain their exact scope. No broad fresh regression/audit claimed.

Frozen external review archive source is `03a0d76f086d3d789d03ca0fe4a8c80d0af08d46` with SHA-256
`6d57a653101f67cbb0ecf40ab2f814a8d126e2c25085dc8d4ea05b35bd0950d0`; separately verified, dependencies not bundled,
no tests executed by export and no final release approval. The docs-only receipt
checkpoint does not alter that source identity. Current actual sources/routes/
updater/VRF/authorities/OpenSea/native operating qualification and external audit
remain open. User OpenSea price is0.05ETH gross; recipient net of actual platform
fee, gas separate. Current direct mint remains all0.05ETH; integration unfinished.

Maintain function notes/reference for changes to ABI/behavior/permissions/params;
normal verification rejects stale or incomplete function/input docs. Sole Todo,
feature evidence, operator/roadmap and both memories are aligned. Main only;
preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signer/null public DEPLOYMENT and paused monitoring. No website
source/build/server, service, public tx/deployment or seal. Production NOT APPROVED.

## Comprehensive review publication verified - 2026-10-25

## Service qualification and function-reference handoff - 2026-10-25

Read [service review](../reports/release-services-20261025/REVIEW.md),
[verification](../reports/release-services-20261025/VERIFICATION.md) and Git/publication.
Optional immutable Pyth reader adds bounded original-time/precision/confidence/
runtime checks;17new Solidity cases and38normal object gates pass. All37previous
objects remain byte-identical. ETH/stable candidates exist; no ZZZ pair, updater,
actual feed/route or provider is qualified. Pyth midpoint confidence is a screening
ceiling, not widened Oracle bounds; proxy implementation/upstream review remains.

Current schema5/mint profile1 fails closed on incompatible OpenSea primary mint;
legacy CLI inspection requires --historical-consistency and never qualifies release.
68distinct affected gate/CLI and19review-package methods pass across scoped runs.
Frozen committed-source export is implemented, not dependency bundling, operating
rehearsal, final release selection or independent audit. Exact final package is
regenerated after implementation commit and recorded in publication separately.

User selected OpenSea buyer gross0.05ETH; actual platform fee comes out of recipient
proceeds, gas separate. Current direct mint still forwards all0.05ETH; compatible
buyer/payment/VRF integration remains pre-seal work. Authority addresses deferred.
The callable reference is implemented:32 contracts,698 functions,32constructors,
15receive hooks; all top-level inputs are explained, with exact outputs/tuple
fields and purpose/caller/payable conditions.10focused generator checks pass.
The normal verifier rejects stale source/reference or incomplete function/input
notes. Maintain it whenever behavior, ABI, permissions or parameters change. Sole Todo/features/roadmap/operator are aligned.

Preserve unrelated drafts, main only,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signer/null public DEPLOYMENT and paused monitor. No public transaction,
deployment/seal, website source/build/server or service action. Website memory-only
update is distinct. Production NOT APPROVED; verify commits/remote publication.

## Native integration / Vault / RPC handoff - 2026-10-25

Read [current review](../reports/native-readiness-20261025/REVIEW.md),
[verification](../reports/native-readiness-20261025/VERIFICATION.md) and Git/
publication receipt before describing what was pushed. Vault private refactors
preserve ABI/storage and save256 runtime bytes (313margin). Native schema-2
website reads/unsigned reviewed calldata are locally applied; signer/client/
coordinator and public null DEPLOYMENT are unchanged. Both native ETH ledger
rows are mandatory; NFT earnings cannot bypass arithmetic validation.

The existing RPC probe has strict outage classification and explicit discarded
Approval(0) tracing. Complete actual identity/trace/provider, native chain/wallet,
feeds/routes/VRF, OpenSea, authority, strategy/gas and operating qualification.
Keep the independent audit/remediation gate open. Do not reset8902/Anvil/NFT/LP/
balances/journals or dist repair overlay, restart services/monitoring, deploy or
enable public signing. Main only; maintain sole Todo/features/operator/memories.

Contract implementation `5790763` and website memory-only `92c090b` are
pushed on main; remote hashes verified. Read [publication receipt](../reports/comprehensive-improvement-20261025/PUBLICATION.md),
[findings](../reports/comprehensive-improvement-20261025/REVIEW.md) and
[verification](../reports/comprehensive-improvement-20261025/VERIFICATION.md).
77distinct scoped Solidity behaviors,148backend methods and37normal object gates
pass with explicit failures/repairs/reuse.42published production source hashes
match; no fresh full-regression/green-CI/real-service or independent-audit claim.
Registry818initcode margin; Vault57runtime margin. Production NOT APPROVED.

Next: matching native reviewed EntryV1 website/wallet integration; actual independent
feeds/input and cheaper ZZZ-conversion routes/VRF/authorities/OpenSea/artwork/services;
strategy economics/maximal real gas, operating rehearsals and independent audit.
Preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signing/null public DEPLOYMENT and paused monitor. No public tx,
deployment, service/server/build change. Main only; sole Todo/features/operator/
roadmap and both repository memories remain aligned.

## Comprehensive improvement candidate - 2026-10-25

Read [improved executable prompt](../reports/comprehensive-improvement-20261025/PROMPT.md),
[coverage/decision review](../reports/comprehensive-improvement-20261025/COVERAGE.md),
[findings](../reports/comprehensive-improvement-20261025/REVIEW.md) and
[verification](../reports/comprehensive-improvement-20261025/VERIFICATION.md).
Reviewed Entry/Pricing/ABI policy binding, indexer ancestry preservation, no-redirect
RPC, fixed rarity metadata and conservative buyback ceilings are implemented locally.
Publication must be read from Git and the separate receipt; local saves alone
are not proof of push. Production NOT APPROVED.

Next: exact native-V2 website/wallet version integration, independent actual feeds,
input/cheaper ZZZ-conversion routes, VRF/authority/OpenSea/artwork/services, strategy
economics/real maximum gas, operating rehearsals and independent audit. Do not
repeat unchanged tests for counts. Keep historical scope and ordinary size gates.
Preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signing/null public DEPLOYMENT and paused monitor. No public tx,
deployment, service or server/build change. Main only; sole Todo/features/operator
and both memories must stay aligned.

## Liquidity operations publication verified - 2026-10-25

Contract implementation `593a212` and website memory-only `1e1a9ba`
are pushed on main; remote hashes verified. Read [publication](../reports/liquidity-operations-20261025/PUBLICATION.md),
[verification](../reports/liquidity-operations-20261025/VERIFICATION.md) and [review](../reports/liquidity-operations-20261025/REVIEW.md).
68scoped Solidity cases,297Python passes/one Unix-only skip and37normal object
gates pass.111published functional/evidence inputs match; one unrelated unexecuted
research-reader draft remains explicitly outside publication. No full regression,
real-provider qualification or independent audit is inferred.

Defaults2%contribution/1%conversion/3%maintenance, gas separate. Bounded two-pass
placement and attributed-idle reinvestment preserve shares/fees/backing with no
sweep. Explicit ZZZ-price-in-ETH mode and reviewed keeper25/50policy are opt-in;
old profiles/physical LP/journals retain original semantics. Current migration
scope is local pool movement plus source-chain external custody; integrated
bridges/remote ownership-ledgers are optional/deferred. Same-chain handoff stays.

Next: caller-bound reviewed Entry policy (still absent), actual services/routes/
dual feeds, strategy economics/max-state real gas, native website/OpenSea/VRF/
authorities and independent audit. Vault57-byte runtime/Registry31-byte initcode
margins require a size-safe next design. Production NOT APPROVED.
Preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signing/null public DEPLOYMENT and paused monitoring. No website
code/build/server, public transaction/deployment, service or monitor action.
Main only; keep sole Todo/features/operator/roadmap and both memories aligned.

## Liquidity operating candidate and resume priorities - 2026-10-25

Read [scoped verification](../reports/liquidity-operations-20261025/VERIFICATION.md),
[internal review](../reports/liquidity-operations-20261025/REVIEW.md),
[idle ownership](IDLE_AND_DUST.md) and [range policy](RANGE_POLICY_UPDATES.md).
User decisions: contribution default2%; conversion1% and maintenance3% unchanged;
gas separate. Keeper chooses only reviewed±25/±50 ranges in **ZZZ price in ETH**,
not inverse rawquote. Mode1/policy/keeper features are explicit default-disabled
opt-ins; old profiles and existing physical LP keep their original semantics.

Implemented candidate: bounded two-pass balance, safe idle-only compounding and
cooldown, range orientation and reviewed Strategy-only width callback, strict
keeper/unit/retired-route handling, API/observer metadata and typed events.
No sweep, generic executor, operator dust recipient or holder redemption.
Vault runtime24,519/57margin; Registry creation+args49,121/31margin. Future embedded
Entry changes need a size-safe design under normal gates. Source-scoped evidence
is not a full regression, actual service qualification or independent audit.

Next: caller-bound reviewed loss policy in versioned Entry/API/wallet before
public activation signing; actual independent feeds/routes, maximal real venue
gas and threshold economics; native website/OpenSea/VRF/authorities, Linux/target-
chain rehearsals and independent audit. Integrated bridge/remote NFT/reward
transport is deferred optional scope. Use source-chain external custody for
external bridge/issuer exchanges; this does not relocate ownership/reward ledgers.
Same-chain whole-collection handoff is retained; no post-halt recovery is promised.

Preserve all unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signer/null public DEPLOYMENT and paused monitoring. No website source/
build/server, service, public transaction or deployment action. Main only; update
sole Todo/features/operator/roadmap and both memories. Check Git and the new
publication receipt separately; local saves are not proof of push.

## Pre-production audit publication verified - 2026-10-25

Audit implementation/evidence `d6faad4` and website memory-only `29d7807`
are pushed on main; remote hashes verified. Read [publication](../reports/preproduction-audit-20261025/PUBLICATION.md),
[findings](../reports/preproduction-audit-20261025/REVIEW.md) and [scoped verification](../reports/preproduction-audit-20261025/VERIFICATION.md).
Keeper budget/preflight fixes are published, not installed into a running service.
Five composed v4 scenarios, the4096-call invariant and199scoped backend passes
retain exact reuse/skip limits. Two activation gaps remain open: thin-market
deployment feasibility and signed review-cap binding. Public signing stays disabled;
production NOT APPROVED. All42production Solidity sources are unchanged.

Preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signing/null public DEPLOYMENT and paused monitoring. No website
source/build/server/service, public transaction or deployment action. Main only.

## Pre-production internal audit - 2026-10-25

Read [internal findings](../reports/preproduction-audit-20261025/REVIEW.md) and
[scoped verification](../reports/preproduction-audit-20261025/VERIFICATION.md).
Keeper now preserves the signing-time fee review before signing, binds actual
chain/gas/max-fee, derives dynamic spend from signed caps/canonical base fee and
enforces captured L1/total semantics. Preflight checks accounting version. Old
pending records remain intact; missing original reviews need operator reconciliation,
never guessed historical limits, deletion or resend. No existing journal was upgraded.

Current native/schema-5 operations, captured/default loss floors, pause-versus-
custody authority and retired bridge instructions are corrected in place. The
operator/recovery guides, architecture, sole Todo, features, roadmap and release
record align. New composed installed-v4 and repaired non-vacuous growth-invariant
evidence is scoped with explicit local substitutes; no fresh full regression,
real-service or independent audit approval is implied. Production NOT APPROVED.

Two activation gates found in this audit remain open: selected-fee thin-market
deployed-LP feasibility, and versioned caller maximum-loss binding. Current
Entry captures execution-time policy, not the earlier reviewed cap. Do not
promise review-pinned1% or enable public activation before this is resolved.
Keep safety floors; the explicit thin-market rejection must roll back all
economic changes, with earlier approval/gas correctly distinguished.

No new unprivileged theft/replay exploit was confirmed in inspected paths; accepted
immediate governance/recipient trust, actual feeds/routes/VRF/authorities/OpenSea,
native website/Linux operations, future-chain canonical transport and independent
audit remain open. Vault's prior normal runtime margin is25bytes; no size/gas
guard is relaxed. Solidity production source remains unchanged in this audit.

Preserve unrelated drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay,
Anvil-only signing/null public DEPLOYMENT and paused monitoring. No website
source/build/server/service, public transaction, deployment or monitor action.
Main only. Inspect Git and the audit publication receipt for actual push status.

### Resume priorities

1. Read the current audit verification/publication records and exact Git status;
   older unrelated drafts are deliberately not part of this audit publication.
2. Qualify actual dual price sources and feasible input/conversion routes with
   independent provider/proxy review. Local feeds and a pool spot estimate do not
   close the source-qualification task.
3. Finish required pre-seal future-chain canonical capability and native profile/
   OpenSea integration; keep unsupported ETH/WETH atomic conversion explicit.
4. Stage fee-journal upgrade/recovery, original signed-cost evidence, Linux locking,
   host fencing/rotation and actual chain fee semantics. Do not touch existing
   local fixtures or restart paused monitoring as a side effect.
5. Require independent audit and exact-release qualification before approval;
   reuse unchanged evidence and run affected checks only for justified changes.

## Pricing documentation publication verified - 2026-10-25

Documentation `14ee92e` and website memory-only
`3a6a69c` are pushed on main; remote hashes verified.
See [publication](../reports/price-reference-20261025/PUBLICATION.md).
The dated ETH/ZZZ references are not configured PoPL prices. Feed pairs, product/
proxy independence and service costs remain unqualified. Corrected setDualFeed
operator/recovery guidance and latest gas margin; sole Todo, features, roadmap
and both memories align. All 120 Solidity bindings are unchanged; prior tests
are reused, not rerun. Preserve older drafts, existing8902/Anvil/NFT/LP/journals/
dist overlay, null public DEPLOYMENT, Anvil-only signing and paused monitoring.
No website code/build/server/service, public transaction or configuration change.
Production NOT APPROVED; main only.

## Price references, fees and qualification status - 2026-10-25

[Saved reference observation](../reports/price-reference-20261025/OBSERVATION.md)
records Robinhood block97,093,373 at25October00:02:43 Paris. ETH candidate
Chainlink answer was$2,340.61, last updated24October22:01:14 Paris. ZZZ's
approximately$0.01031019 is selected-pool spot times that ETH answer, NOT an
independent USD feed or configured PoPL output. No PoPL source pair is configured
or qualified. The catalog's primary/secondary Shared-SVR proxies do not establish
independence. Do not copy these dated prices into runtime configuration.

Ordinary public push-feed reads have no separate per-read LINK charge; on-chain
reads consume gas. RPC/custom provider/product/hosting costs remain unsettled.
The500,000-gas call ceiling is a maximum, not a flat fee. Post-seal immediate
governance uses setDualFeed with full admission/history and downstream inventory
updates; setFeed is retired. Selected3% agreement and default1% execution floors
remain separate. Actual services, source/proxy/common-mode review and independent
audit stay open. Production NOT APPROVED.

This update is documentation/evidence only. Prior145Solidity/83backend/37object
checks retain their source scope; no unchanged tests were rerun. Preserve older
drafts,8902/Anvil/NFT/LP/balances/journals/dist overlay, null public DEPLOYMENT,
Anvil-only signing and paused monitoring. No website code/build/server/service or
public transaction. Main only; inspect the publication receipt/Git for push status.

## On-chain safety/cost publication verified - 2026-10-24

Contract `8d0234d` and website memory-only
`7176278` are pushed on main with remote hashes verified.
Read [publication](../reports/onchain-safety/PUBLICATION.md),
[review](../reports/onchain-safety/REVIEW.md) and
[verification](../reports/onchain-safety/VERIFICATION.md). 145 distinct Solidity
cases,83 backend checks,37 normal object gates and120 final bindings are scoped;
no fresh full regression or actual provider qualification is claimed. Cold
combined activation11,507,856 passes unchanged12M gate. Production NOT APPROVED.
Operator/Todo/features/roadmap and both memories align. Preserve older drafts,
8902/Anvil/NFT/LP/journals/dist overlay, null public DEPLOYMENT, Anvil-only signing
and paused monitoring. No website/server/service or public transaction change.

## On-chain safety and cost follow-up - 2026-10-24

The [internal review](../reports/onchain-safety/REVIEW.md) hardens sequencer reads
with bounded gas/exact return data and reduces repeated static price reads,
contribution storage and reward checkpoint work. Strategy uses a memory-only
pair vector; final execution/fingerprint/physical LP checks remain independent.
Price/share/quote rounding, exact approvals, owner rights and execution limits
are preserved. Source uncertainty, qualified provider/proxy independence and
accepted immediate governance/custody trust remain explicit.

[Scoped verification](../reports/onchain-safety/VERIFICATION.md): 145 distinct
Solidity cases, 83 affected backend checks, 37 normal source-object gates and
120 final source/test/script bindings. Original negative controls and one repaired
stale fixture retain their scope. This is not a fresh full regression or actual
provider qualification. Cold combined activation is11,507,856 under the unchanged
12M gate. Production NOT APPROVED; real services and independent audit remain open.

No public transaction/deployment, website code/build/server, existing8902/Anvil/
NFT/LP/balances/journals/dist overlay, signer or service/monitor change. Public
DEPLOYMENT null; signing Anvil-only; monitoring paused. Main only; preserve older
unrelated drafts. Publication must be checked separately from Git and the receipt.

## Dual pricing publication verified - 2026-10-24

Contract implementation `b5002df` and website memory-only
`ea39eb0` are pushed on main; remote hashes and intended blobs
verified. Read [publication receipt](../reports/price-security/PUBLICATION.md).
The selected3% agreement band is separate from the default1% execution floor.
174 source-scoped Solidity cases,187 Python cases,36 normal object gates and115
final Solidity bindings are recorded with their diagnostics/reuse boundaries.
No fresh full regression or actual feed/service qualification is claimed.
Production NOT APPROVED. Existing8902/Anvil/NFT/LP/journals/dist overlay, Anvil-only
signing, null public DEPLOYMENT and paused monitoring remain unchanged. Main only;
preserve older unrelated drafts. No website/server/service or public transaction.

## Dual pricing and factual LP security - 2026-10-24

Read [current verification](../reports/price-security/VERIFICATION.md),
[internal review](../reports/price-security/REVIEW.md) and
[operator/design guide](PRICE_SECURITY.md). Oracle PRICING_VERSION2 now
requires two independently reviewed USD sources per priced asset. User-selected
agreement tolerance is3% (300bps); this is not the separate default1% execution
loss cap. The bounded setter retains a500bps ceiling. Actual source addresses,
ages, common-mode/proxy policies and real provider/route qualification remain
unset. No stable peg, single-source, pool-spot or stale fallback is permitted.

The Oracle-created fixed ContributionPricing helper freezes source/pair prices
and contribution/venue limits before Entry pulls/conversion. Direct contributions
freeze before pulls. Lower minimums, upper-source/lower-LP execution floors,
exact round fingerprints, actual position ownership/key/ticks/liquidity and
unchanged deployment spot are checked. Later historical compound stays
incumbent-only; epoch-zero skips only irrelevant historical scans. Source-scoped
tests/repairs and gas findings must be read precisely; no fresh full regression,
real provider approval or independent audit is inferred.

Backend pricing_version2 is explicit alongside native accounting/routing2;
schema5 now inventories15helpers. Old profiles stay distinct. Fresh legacy local
scaffolds reject current incompatible pricing-V2 artifacts before state/process
creation. Existing8902/Anvil/NFT/LP/balances/journals/dist overlay stay untouched.
Public DEPLOYMENT null, signer Anvil-only, monitoring paused. No public signing,
deployment, website build/server or service action. Preserve older unrelated
drafts, use main only, maintain the sole Todo/features/roadmap/operator guidance
and both repo memories. Publication is separate: inspect Git and the receipt.
Production NOT APPROVED.

## Native production preflight publication - 2026-10-24

Contract tooling7e6702d and website memory-onlyed966e4 are pushed on main;
exact remote hashes verified. Publication is recorded separately below. The
schema-5 native/accounting-V2/routing-V2/governed gate and bounded read-only
observer are implemented, with actual pins/bindings/caps/source/routes/ledger
observations separated from approved policy and qualification.

73 distinct focused Python cases pass across scoped runs. All131 prior source/
test bindings match; unchanged Solidity/build/size/fork suites were reused,
not rerun. No fresh full regression, actual provider or independent approval.
Historical qualification retains its real block and current configuration/fee
scope; current snapshots/history remain separate. Actual addresses, feeds/routes,
VRF/services/OpenSea/artwork, gas/recovery and audit remain open. Example blocked;
production NOT APPROVED.

No Solidity, website source/build/server, existing8902/Anvil/NFT/LP/balances/
journals/dist overlay, shared signer, service or monitor change. Public DEPLOYMENT
null; signing Anvil-only; monitor paused. Main only; older drafts preserved.
Sole Todo/features/roadmap/operator guidance and both memories are updated.

[Publication](../reports/native-preflight/PUBLICATION.md), [verification](../reports/native-preflight/VERIFICATION.md) and [operator runbook](PRODUCTION_PREFLIGHT.md).

## Native V2 production preflight checkpoint - 2026-10-24

The [schema-5 runbook](PRODUCTION_PREFLIGHT.md), native/accounting-V2/routing-V2/governed inventory and bounded
read-only observer are implemented. Publication is recorded separately; inspect
Git and the publication receipt rather than inferring a push from this note.
The gate checks17 core identities/14 helpers, native-zero semantics, exact
runtime/getter/parent/ledger bindings, current governed0..10% limits and explicit
typed source/conversion routes. Approved pins and actual observations stay
separate. Unavailable reads never become zero or approval.

73 distinct focused Python cases pass across recorded scopes, including mock
observer-to-gate composition. Repeated cases count once. All131 earlier typed-v4
source/test hashes match; unchanged Solidity/build/size/fork suites were reused,
not rerun. Historical qualification keeps its real tested block and current
configuration/fee scope; fresh admission history must reach the actual anchor.
These are offline/mock checks, not real provider or independent qualification.

Current scope excludes nonzero external creator-reward inbox inventories,
cross-chain canonical activation, legacy V1 import and atomic ETH/WETH principal
conversion. Actual public PoPL/authority addresses, independent feeds, qualified
routes/RPC/VRF/keeper/API/artwork/OpenSea operation, gas and independent audit
remain open. The example stays blocked. Production NOT APPROVED.

No Solidity, website source/build/server, existing8902/Anvil/NFT/LP/balances/
journals/dist overlay, signer, service or monitoring change. Public DEPLOYMENT
remains null, signing Anvil-only, monitor paused. Main only; preserve older
unrelated drafts. Sole Todo, features, roadmap, operator guide and memories are
updated; publication must be verified separately.

[Verification](../reports/native-preflight/VERIFICATION.md) and [internal review](../reports/native-preflight/REVIEW.md).

## Typed v4 and governed limits publication checkpoint - 2026-10-24

Contract implementation59a2563 and website memory-onlybd2c354 are pushed on
main; exact remote hashes verified. Read [publication](../reports/typed-v4-routes/PUBLICATION.md),
[verification](../reports/typed-v4-routes/VERIFICATION.md) and [internal review](../reports/typed-v4-routes/REVIEW.md).
Typed v4 Entry/LP/royalty conversion is implemented as an undeployed candidate.
All three loss categories are immediate governance settings0..10%, defaults
1%/1%/3%; this latest user decision supersedes old fixed-cap requirements.
Gas, stronger caller/venue minima, captured operations and original approved
normal custody floors remain. See [operator policy](EXECUTION_LOSS_POLICY.md).

83 distinct scoped Solidity and112 Python passes,35 normal object gates,
79 matching production compiler inputs,109 ABI/typecheck inputs and131 final
source/test hashes are recorded. Current125 event descriptors retain all119
previous entries. No full fresh regression, actual-provider qualification or
independent approval is claimed. Vault runtime24,508 and creation48,444including
arguments pass normal limits; keep its68-byte runtime margin under review.
Budget read-only validation delegates to existingfixed-VaultCanonical under
actualBudget authentication, with no new custody authority or codec change.

Actual routes/feeds/services, native website/inventory, ETH/WETH principal
boundary, OpenSea mint, future-chain handoff and independent audit remain open.
Production NOT APPROVED. Public DEPLOYMENT null; shared signer Anvil-only;
monitor paused. No source website/build/server, existing8902/Anvil/NFT/LP/
balances/journals/dist overlay, service or public transaction changed. Older
unrelated drafts remain local. Main only; sole Todo/features/roadmap/operator
guidance and both memories are aligned. This final receipt changes docs only;
implementation publication is59a2563 above.

## Typed v4 conversion and governed execution limits - 2026-10-24

Current local candidate implements typed hookless static exact-input v4 routing
for Entry and earned LP/royalty balances through immutable parent-bound helpers.
Native v4 settlement needs no wrapper; v3 descriptors remain separate. Read
[route setup](TYPED_V4_ROUTES.md) and [loss policy](EXECUTION_LOSS_POLICY.md).
The user's latest decision supersedes earlier fixed1%/3% requirements: default
contribution100bps/conversion100bps/maintenance300bps, immediate governance with
hard1000bps (10%) maximum for each. Gas remains separate. Budget.setLossLimits
sets contribution/maintenance; each converter.setConversionLossBps is separate.
Captured contribution/maintenance policy and original normal custody approval
floors persist despite later changes. Stronger venue/caller minimums still apply;
raw emergency remains explicit, not an automatic downgrade or USD guarantee.

Budget's read-only owner/contribution validation delegates to the existing bound
VaultCanonical, authenticated to actual vault.migrationBudget(), to stay inside
normal creation-size limits. No canonical codecs/funding or new custody authority
is added. Explicit activation routing_version2 and converter/worker/reporting
profiles read current governed policy; historical profiles retain old semantics.

[Scoped verification and review](../reports/typed-v4-routes/VERIFICATION.md) separate
real installed v4 conversion from mocked LP/feed/VRF fixtures and reused checks.
No full fresh regression or real-provider qualification is claimed. Actual routes,
feeds, native website/inventory, ETH/WETH principal boundary, OpenSea mint, future
chain transport and independent audit remain open. Production NOT APPROVED.

No website source/build/server, existing8902/Anvil/NFT/LP/balances/journals/dist
repair overlay, service/monitor or public transaction change. Public DEPLOYMENT
remains null; shared signer Anvil-only; monitoring paused. Preserve older unrelated
drafts and use main only. Sole Todo/features/roadmap/operator guidance and both
memories must stay aligned. Check Git and the separate publication receipt before
claiming this candidate committed/pushed.

## Operating controls publication checkpoint - 2026-10-24

Contract implementation `143734c` and website memory-only `34f53d6` are pushed
on main and remote hashes verified. Read [publication](../reports/post-seal-controls/PUBLICATION.md),
[verification](../reports/post-seal-controls/VERIFICATION.md) and [internal review](../reports/post-seal-controls/REVIEW.md).
NFT future confirmations/callback gas and Buyback operating ceiling are now
bounded immediate governance settings. Provider/lane/subscription/payment,
pending draws, exact traits, rights, allocation and backing remain protected.

Nine new VRF plus six affected existing cases and 35 distinct buyback cases pass
across scoped runs; only repaired/changed cases were repeated. Twenty-six inventory
and five final event cases pass. All 34 production size gates pass (32 source
objects unchanged); 78 compiler bindings and 111 source/test hashes match;
104 Solidity inputs typecheck. Existing 103 event decoders are retained unchanged,
with 16 additions including the two controls. Retired descriptors do not enable
old modules. No full fresh regression, fork or real-service approval is claimed.

Future VRF tuning cannot repair a submitted callback. Qualify actual provider
bounds/funding/recovery. Zero operatingTradeUSD stops new swaps/direct ZZZ burns
before oracle/reserve calls; use USD18 per-trade limits and resize/remove fixed
keeper buyback tasks to avoid intentional failures/backoff. Successor settings
are independently reviewed local policy, not imported economic rights.

Typed v4 conversion is the next pre-seal implementation slice. Atomic ETH/WETH
moves, native website/inventory, actual routes/feeds/services and independent
audit remain open. Preserve 1%/3% execution limits and separate gas. Production
NOT APPROVED; public DEPLOYMENT null; shared signer Anvil-only.

No website source/build/server, existing 8902/Anvil/NFT/LP/balances/journals/dist
overlay, services or paused monitoring changed. No private key access or public
transaction. Main only; preserve older unrelated drafts. Sole Todo, features,
roadmap, operator guidance and both memories are aligned. This final receipt
is documentation only; implementation publication is the hash above.

## Bounded post-seal operating controls - 2026-10-24

The local candidate adds NFT.setRandomnessRequestSettings(uint16,uint32) for
future confirmations/callback gas and Buyback.setOperatingTradeUSD(uint256)
beneath immutable maxTradeUSD. Zero stops swaps/direct ZZZ burns before oracle
or reserve calls. Immediate governance, ordinary-pause support, preparation/
canonical locks and reentrancy guards remain. Provider/lane/subscription/payment,
pending draws, ordered traits, NFT rights and classified funds are unchanged.
Read [scope and evidence](../reports/post-seal-controls/VERIFICATION.md) and
[internal review](../reports/post-seal-controls/REVIEW.md).

Nine distinct new VRF cases plus six affected existing cases and 35 distinct
buyback cases pass across scoped runs; only repaired/changed cases were repeated.
All 34 production size gates pass (32 source objects unchanged); 78 current
compiler bindings match; 104 Solidity inputs typecheck. The event schema keeps
all 103 earlier decoders unchanged and adds 16 current topics, retaining 17
retired descriptors without enabling old modules. Inventory observations now
separate immutable provider policy from two mutable future-request parameters.

Actual VRF/provider limits and original-request recovery remain unqualified;
future tuning cannot repair an old callback. Resize/remove keeper buyback tasks
after lowering/stopping its cap, or intentional simulation failures can back off.
Successors review their own settings; no economic record copies operating policy.
Keep the 1%/3% execution limits and separate gas. Typed v4 conversions, native
website/inventory/services and independent audit remain open. Production NOT
APPROVED; public DEPLOYMENT null; signer Anvil-only.

No website source/build/server, existing 8902/Anvil/NFT/LP/balances/journals/dist
repair overlay, services or paused monitoring changed. No public transaction or
private-key access. Main only; preserve older unrelated drafts. Todo, features,
roadmap, operator guidance and both memories must remain aligned. Check Git and
publication receipt before claiming this local candidate pushed.

## Native ETH V2 publication checkpoint - 2026-10-24

Contract implementation `f907733` and website memory-only `cb43349` are pushed
on main and both remote hashes verified. Read the [publication receipt](../reports/native-eth-port/PUBLICATION.md),
[scoped verification](../reports/native-eth-port/VERIFICATION.md) and [internal review](../reports/native-eth-port/REVIEW.md).
The native port is implemented as an undeployed V2 candidate; older unimplemented
notes below are superseded. Actual ETH spans typed Entry/Vault/manager funding,
indexed fees, reserves, claims, buyback, raw exit/return and canonical backing/abort.
Explicit API/keeper accounting versions preserve legacy WETH history and journals.

Focused affected checks pass with documented source scopes and targeted repairs;
no full fresh regression or new target-chain fork is claimed. All 34 production
object gates pass; 78 production compiler bindings and 113 final source/test
hashes match. The final adversarial freeze uses 11,713,754 gas under 12M and
preserves all 132 companion plus 12 inbox prefunds through funding and abort.
Vault runtime is 24,504 bytes (72 margin); review size before further changes.

Keep 1% contribution/reward conversion and 3% ordinary maintenance limits, gas
separate. ZZZ needs a cheaper qualified route. Atomic ETH/WETH conversion, legacy
V1 import, native website profile, reviewed release inventory, typed v4 conversion,
post-seal operating extensions, real services and independent audit remain open.
Production NOT APPROVED; public DEPLOYMENT null; signer remains Anvil-only.

Website source/build/server, existing 8902/Anvil/NFT/LP/balances/journals/dist overlay,
services and paused monitoring are unchanged. No public transaction/deployment
or private key access. Main only; preserve older unrelated local drafts. Sole
Todo, feature reference, roadmap, operator guidance and both memories are aligned.
This receipt is documentation only; implementation publication is the hash above.

## Native ETH accounting V2 candidate - 2026-10-24

Native V2 is now implemented locally, superseding the older notes saying no port
exists. Read [implementation and scoped evidence](../reports/native-eth-port/VERIFICATION.md)
and [internal review](../reports/native-eth-port/REVIEW.md). Actual ETH identity spans
Entry, Vault, manager, fee reserves, indexed owner/collective rewards, claims,
buyback, raw exit/return and two-stage canonical funding/abort. Explicit native
API/keeper version profiles preserve legacy WETH epochs and existing journals.

Preserve1% contribution/reward conversion,3% ordinary maintenance and separate gas.
ZZZ still needs a cheaper qualified conversion route. Atomic ETH/WETH conversion
and legacy V1 canonical import remain unsupported and fail closed. Native website
profile, release inventory, actual routes/feeds/VRF, fork/services and independent
audit remain open. Production NOT APPROVED; public contracts undeployed.

No website code/build/server, existing8902/Anvil/NFT/LP/balances/journals/dist overlay,
shared signer policy or paused monitor changed. Public DEPLOYMENT stays null;
shared signing is Anvil-only. Main only; preserve older unrelated drafts. Maintain
sole Todo/features/roadmap/operator guide and both memories. Read Git and the
separate publication receipt before claiming this candidate pushed.

## Audit publication and native port handoff - 2026-10-24

Contract audit fixes `e6b5872` and website memory-only `7849376` are pushed
on main and remote hashes verified. Read [publication receipt](../reports/daily-security-20261024/PUBLICATION.md)
and [internal review](../reports/daily-security-20261024/REVIEW.md). Four new regressions
pass;58 existing passes plus2 repaired-case reruns and9 observer cases are scoped,
not a fresh full regression. All95 final source/test hashes match. Strategy runtime
12,862 bytes passes normal limits;32 unchanged source-object gates are reused.

The broader native ETH redesign WAS included as a design audit. No native port
is implemented. Its cross-contract/schema/backend requirements remain pre-seal
gates, including native indices, historical reserves, two-stage funding/abort,
nonduplicated backing and wrapper-independent raw exit/recovery. Current custody
still uses WETH. Preserve1% conversion/3% ordinary maintenance limits and cheaper
route requirement. Real services and independent audit remain open.

No website source/build/server, existing8902/Anvil/NFT/LP/balance/journal, signing
policy or monitoring change. Public DEPLOYMENT is null; signer Anvil-only; production
NOT APPROVED. Both memories, Todo/features/roadmap/operator guidance are aligned.
Older unrelated drafts remain local. Main only; follow the source-scoped evidence.

## Internal audit and native-design review - 2026-10-24

Read [audit findings and scoped evidence](../reports/daily-security-20261024/REVIEW.md).
Today's implementation fix extends actual directional static fee sizing to native
and ERC20 v4 pools; floors and authority are unchanged. Four new regressions pass.
Affected existing tests:58 pass plus2 stale fixture failures; only the two repaired
fixtures were rerun, both pass. Final source/test snapshot95 matches; no full fresh
regression or fork is claimed. Strategy runtime12,862/initcode13,318 passes normal
gates;32 unchanged object gates reused. Nine offline observer cases pass; the
reader now has bounded strict hash-pinned reads, runtime pins, sanitized failures
and atomic output. No real provider is qualified by those mocks.

The broader native ETH redesign WAS included as a design audit. It is still NOT
implemented. Explicit requirements now cover zero/unset identity, native reward
indices/converted credits, historical native reserves, two-stage canonical
funding/abort, nonduplicated receiver protection, transitive wrapper-independent
exit/recovery, versioned per-epoch accounting/backend profiles and typed child
call values. Raw royalty donations follow receipt/cohort policy; sender provenance
cannot be invented. These are pre-seal implementation/verification blockers.

Exit procedure now uses pause, reviewed park, stable parked snapshot, approval
and exit, keeping original rounded-up pre-parking ZZZ minima. No strict snapshot
was bypassed; parking and later approval do not automatically share one cached
on-chain budget. Normal3% and raw explicit minima remain distinct. Selected
hookless LP fees replace mandatory Pons creator funding; optional history remains.

Maintain sole Todo/features/roadmap/operator manual and both memories. Production
NOT APPROVED; WETH remains until the versioned port is implemented. Preserve
8902/Anvil/NFT/LP/balances/journals/dist overlay, Anvil-only signing/null public
DEPLOYMENT and paused monitoring. No public transaction/deployment, website/server
code/build or service action. Older unrelated drafts remain local; main only.
Publication must be verified from Git and the separate audit publication receipt.

## Publication checkpoint and resume priorities - 2026-10-24

Contract checkpoint `7a1d564` and website memory-only `5c5a1de` are pushed on
main and remote hashes verified. See [publication receipt](../reports/hookless-pool/PUBLICATION.md).
Source-bound evidence preserves106/native24 earlier scope, final exit-floor53
passes plus2 stale fixture failures, corrected custody24, and fork8 earlier passes
plus2 repaired-path reruns. All94 final source/test bindings match;33 object gates
pass;9 exact-publication Python checks pass. No fresh full regression is claimed.

Next pre-seal implementation: native ETH custody/accounting/recovery, bounded
post-seal operating controls, and typed v4 conversion support. The current code
still uses WETH and v3 conversion. Retain1% ZZZ reward conversion limit, gas separate,
and require a cheaper qualified route. Real services, inventory and audit remain
open. No reset/burn or arbitrary sweep; separate mainnet rehearsal and final
collection identities. Public contracts remain undeployed; production NOT APPROVED.

Website code/build/server,8902/Anvil/NFT/LP/balances/journals and dist overlay are
unchanged. Anvil-only signer/null public DEPLOYMENT and paused monitor preserved.
Older unrelated drafts remain local and must not be bundled into publication.
This final receipt is documentation only; source-code publication is the commit
above. Use main and maintain the sole Todo, features, operator guide and memories.

## Post-seal flexibility and mainnet rehearsal policy - 2026-10-24

The user requires noncritical operating settings to remain configurable after
sealing; this is a design requirement, not a claim all controls exist. Existing
assets/routes/feeds/pool parameters/roles are governed immediately. Current VRF
request settings and buyback maximum are fixed; Entry and LP/royalty conversion
are single-hop v3 only. Review bounded future-request tuning, an operating buyback
ceiling and typed v4 support before sealing. Preserve ownership, exact traits,
earned entitlements, backing, execution floors and canonical uniqueness; no reset,
arbitrary executor or sweep. New controls require implementation and scoped tests.

The user reconfirmed 1% maximum ZZZ LP-fee conversion loss, gas separate; require
a cheaper independently qualified conversion route. Selected pool's observed
approximately 1.101% fee does not qualify that full conversion at reference prices.
No automatic cap increase or invented route. Native ETH accounting is now the
requested architecture direction for robustness/efficiency; the specification is
prepared but the current implementation still uses WETH. Earlier notes saying
this direction was not approved are superseded; no native port is claimed done.

A real-funds production rehearsal should use a separate clearly named deployment,
then a fresh final collection. No burn/reset exists; paused principal exit does
not clear NFTs, reward liabilities, reserves, mint payments or public history.
Canonical retirement needs a real funded successor and preserves all rights.
No deployment, signing, public transaction, service/reset/monitor change follows
from this design discussion. Shared signer remains Anvil-only, public DEPLOYMENT
null; preserve 8902 and all existing journals/state. Production NOT APPROVED.

Read [policy and operator boundaries](POST_SEAL_POLICY.md) and the sole Todo.
This follow-up changes documentation/requirements only; unchanged tests are reused,
not rerun. Local saves/publication must be distinguished; preserve older drafts.

## Hookless selected pool and move/exit candidate - 2026-10-24

The user selected existing Robinhood v4 native ETH/ZZZ pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`:
static LP fee10020 pips (1.002%), spacing200, zero hook. Observed protocol fee1000
pips per direction gives approximately1.101% combined. Pons and the earlier
proposed0.30% pool are superseded, not launch dependencies.

Current local code admits runtime-pinned static hookless native ETH/ZZZ markets,
including future initialized fee tiers; WETH/ZZZ uses ordinary hookless admission.
Native Strategy reads actual directional protocol/LP fees. `Migration.moveFunds`
is the atomic same-accounting-pair path; `movePool` is retained as an alias. It
preserves NFT shares and one fixed3% aggregate cap, gas separate. Contribution
pool/routes must be switched deliberately after actual destination LP is checked.

Separate approved paused `exit` remains normal all-ZZZ or explicit no-swap raw
custody to an EOA/contract; no automatic fallback, holder redemption or sweep.
Current raw native-pool exit sends WETH/ZZZ and still depends on wrapper health.
The user questioned wrapping; recommendation now distinguishes minimizing changes
from the longer-term native-ETH architecture/recovery goal. A full native-accounting
rewrite, wrapper-independent emergency exit and native custody payout are requested
but NOT implemented. Track the explicit pre-seal native architecture task.
Do not claim raw exit works through wrapper/pool/token failures.

Read [decision](POOL_SELECTION.md), [operator steps](GOVERNED_CUSTODY_HANDOFF.md),
[scope/evidence](../reports/hookless-pool/VERIFICATION.md) and the sole Todo. Local checks
and completed scoped fork results are recorded separately; publication must be read from
Git, never inferred. Production NOT APPROVED. Preserve all older unrelated drafts,
8902/Anvil/NFT/LP/balances/journals and the dist repair overlay. Signer stays
Anvil-only; public DEPLOYMENT stays null. No website/server deployment, service
control, public transaction or monitoring restart. Main only, maintain both memories.

## New ETH/ZZZ pool decision - 2026-10-24

The user plans a new Uniswap ETH/ZZZ pool instead of the former Pons venue.
Desired displayed fee breakdown: 0.25% LP / 0.05% Uniswap protocol / 0.30%
effective. Chain confirmation, version, hook and actual new pool identity are
pending. v4 without a custom hook is a recommendation, not an approved choice.
Do not assume that v3's displayed split is a v4 setting or that PoPL receives
Uniswap's protocol fee. Existing native admission is pinned to old Pons; a new
native hookless pool needs reviewed support before sealing. Ordinary LP income
would replace the former creator-payment dependency if a standard pool is chosen.

Read [pool decision](POOL_SELECTION.md) and the sole Todo. Old Pons research,
tests and creator questions are historical/conditional, not new-pool qualification.
The old pool was removed from the blocked production template's active selection.
No Solidity, source signing policy, public funds, deployment, website/server,
existing Anvil/NFT/LP/journal state, service control or paused monitor change.
Preserve unrelated drafts, use main and maintain the operator guide and memories.
Production remains NOT APPROVED. Check Git/publication for what was pushed.

## Governed custody handoff candidate - 2026-10-23

Publication: contract implementation `e36a581` and website memory-only `0c45c28` are pushed on main. Read [publication receipt](../reports/custody-handoff/PUBLICATION.md); no website/server deployment or fresh Anvil custody rehearsal occurred.

Local follow-up: final affected custody/royalty/parking/access tests pass 64/64;
33 source-object size gates pass (Migration runtime 23,754 bytes, 822 margin).
The delayed local destination binding preserves the original exit/budget. Prior
183-case accounting and 34-case canonical results retain their earlier source
scope; this is not a fresh full regression or Anvil custody rehearsal. Read the
verification and Git/publication record for status; production remains unapproved.

The user approved replacing old LP migration/bridge paths with governed external
custody, while retaining the whole-collection NFT/accounting handoff. Ordinary
Migration Exit closes and converts principal to configured ZZZ; explicit
`rawExit` is a separately approved no-swap emergency transfer with raw minima
and no 3% USD guarantee. Never automatically downgrade a failed normal exit.
Recipients can be EOAs/contracts; governance explicitly trusts their custody
and liveness after departure. No holder redemption or general sweep is added.

Original NFT shares and LP/royalty liabilities stay recorded. Local completion
requires actual destination LP; normal mode reuses the original 97% fixed-price
floor. Recovery requires the full actual sent assets. Cross-chain delivery and
return require pinned finality/closure proofs, with no multisig/timeout override;
no real verifier/provider/remote ledger is supplied. Whole-collection capture
cannot proceed with pending principal or royalty custody. Royalty currencies
have a separate paused, full-balance exit and exact raw return; claims/valuation
for the exited currency are explicitly unavailable, not zero. Restoration is
not new income. Buyback ZZZ targeting is separately governed and reviewed.

Read [operator procedure](GOVERNED_CUSTODY_HANDOFF.md) and
[verification scope](../reports/custody-handoff/VERIFICATION.md). Checks and
publication must be read from that record/Git, not inferred from this note.
The old v3 transport implementations and pair executor are removed from src;
obsolete tests are preserved as historical text, not passing current tests.
Current production inventory/provider/backend qualification must be adapted and
independently reviewed. Existing source-bound reports keep their original scope.

Preserve 8902/Anvil/NFT/LP/balances/journals and its temporary dist repair overlay.
No public deployment, holder transaction, website build, service control or
monitor restart is authorized by this work. Signer stays Anvil-only; public
DEPLOYMENT remains null. Main only, preserve unrelated drafts, maintain the sole
Todo/features/operator guidance and both memories. Production NOT APPROVED.

## Typed local pair conversion - 2026-10-23

The candidate implements atomic local LP pair conversion through the immutable
`Migration.pairMigration()` companion: at most eight typed v4 legs, one fixed-price
3% aggregate loss floor, gas separate, no arbitrary router/recipient or sweep.
NFT shares/home identity and old reward currencies/inboxes persist. Current and
selected historical compound move; unselected reserves stay backed in Fees.
Historical compound remains incumbent share/NAV backing; old venue dust cannot
cross new membership. Same-chain group records carry epoch/current-token backing;
V3 principal proposals reject composed buckets, even after returning home.

[Operator procedure](PAIR_MIGRATION.md) and
[scoped evidence](../reports/pair-composition/VERIFICATION.md): 141 final affected
Solidity passes (14 new cases; aggregate fuzz 1,001 runs), 176 backend/configuration
passes and 33 normal object gates. The preceding broad run retains its own scope
and failed fixture diagnostics; do not call it a full final-source regression.
Vault runtime is 24,567 bytes (9 bytes margin); normal compiler limits unchanged.
Backend preparation checks the exact current/legacy result ABIs and reviewed
historical prices without widening public signing. Inventory gate requires the
new helper's exact bindings, empty contexts and independent qualification.

Publication is [recorded separately](../reports/pair-composition/PUBLICATION.md).
No public contract transaction/deployment or website/server code change. Existing
8902/Anvil/NFT/LP state, repair overlay, browser journals and paused monitoring
are preserved. Signer remains Anvil-only; public DEPLOYMENT remains null.
Actual routes/services, composed controller cutover, new payout currencies,
multi-currency bridges/future-chain handoff and independent release approval
remain open before sealing. Main only; preserve older unrelated drafts. Maintain
the sole Todo, features, operator manual, roadmap and both repository memories.

## Confirmed collection explorer - 2026-10-23

Publication: backend `d1b11eb` and website `9be6d11` are on main. The static
server serves `9be6d11`; 5,598 server checksums and 50 scoped public checks pass.
Public DEPLOYMENT remains null; local repair overlay/journals are preserved.
See [publication receipt](../reports/collection-reads/PUBLICATION.md).

The production read API and opt-in website profile now expose complete collection
positions and total attached LP at one confirmed block, in bounded 16-NFT chunks.
Canonical owners, reverse mint identities, immutable traits and NFT.currentLPValue
are checked; unknown values/pages never become zero or partial totals. Includes
filters/search, 16-row pagination, actual artwork and read-only current details.
Activated counts eligibility, not current fee earning. Rounding follows NFT views.
Read [operator procedure](COLLECTION_READS.md) and [scoped evidence](../reports/collection-reads/VERIFICATION.md). 74 affected Python, 75 JS, 12 isolated browser and
34 actual isolated Nginx cases pass; real providers/history/latency remain open.

Different-pair migration still needs composition epochs/historical intake work;
the existing pair guards remain. OpenSea primary mint is still unqualified.
Shared signer/coordinator are unchanged and Anvil-only; public DEPLOYMENT is null.
No public API/contract/financial action, local chain/NFT/LP/journal change or paused
monitor restart. Preserve 8902 and its temporary dist overlay; build outside dist.
Actual user MetaMask reset/browser archival remains pending. Main only, keep the
sole Todo/features/operator manual and both memories aligned; preserve old drafts.
Check Git and publication evidence for what is actually published.

## Production earnings and OpenSea mint scope - 2026-10-22

Publication: backend `31e5ac4` and website `35c7843` are on main; the static
server serves `35c7843`. All 5,598 checksums and 50 scoped public checks passed.
Public DEPLOYMENT remains null and local repair overlay/journals are preserved.
See [publication receipt](../reports/wallet-earnings/PUBLICATION.md).

The user clarified that production minting is intended for OpenSea; the website
Mint page demonstrates the product. Local Anvil minting remains a test tool.
The production website profile now refuses mint preparation. OpenSea chain/product,
caller/recipient compatibility and exact collection URL are an explicit pre-seal
qualification task; no marketplace integration has been approved or deployed.

Shared production API/website earnings now cover all currently held NFTs in
bounded same-block chunks and collection holder allocations. Independent NFT
rounding, original-currency/current-price valuation, transfer history and complete
same-chain lineage remain; claims/conversions are not new income. Missing history
or prices stays unavailable. 86 affected Python, 89 distinct JS and six isolated
production-profile browser cases pass; actual services/feeds/audit remain open.
See [scoped evidence](../reports/wallet-earnings/VERIFICATION.md). Full collection inventory/LP aggregation is still separate.

Signer/transaction coordinator remain local-only and unchanged. Public DEPLOYMENT
is null. Running 8902, Anvil, browser journals and paused monitoring are untouched.
Its temporary local mint-repair dist overlay remains; do not deploy it. The clean
build is external and contains 5,598 files. Actual user MetaMask reset/browser
archival is still pending. Main only; preserve unrelated drafts, maintain the sole
Todo, features/operator procedures and memories. Check Git/publication evidence.

## Authorized local mint cleanup and sleep handoff - 2026-10-22

The user explicitly approved reconciliation of the exact unmined local mint
7df63a...00cc6. It is removed from the 8902 Anvil queue, not mined or confirmed.
Complete stateRoot, Wallet A/B balances and nonces are identical before/after;
NFTs, LP and reward storage are preserved. No chain/service reset or new holder
transaction. No public source/deployment or paused-monitor change.

**Tomorrow:** user selects Wallet A and PoPL local network in MetaMask, clears
activity/nonce data, refreshes 8902 in the original browser, then uses **Archive
the abandoned mint and reconnect**. The one-time exact-fixture control archives
and verifies only that pending journal under the same wallet lock. Actual user
MetaMask and browser storage are untouched so far; do not call them reconciled.

[Procedure/evidence](../reports/browser-wallet/local-mint-reconciliation/RECONCILIATION.md): 13 focused checks and one isolated headless browser
scenario pass; user journal not accessed. A temporary overlay exists only in
website dist/deployment-view.js. Source remains published 9aaedec behavior. Do not
deploy that dist; after verified browser archival, restore dist from committed
source without restarting Anvil. External api-chain-rehearsal/pending-fix holds
the original bytes, cleanup evidence and overlay hashes. Main only; preserve older
drafts. Todo/features/operator/memories are updated; production NOT APPROVED.

## Pending mint nonce diagnosis - 2026-10-22

Publication: website `9aaedec` and contract evidence `1bb8668` are on main. The
static server serves `9aaedec`; all 5,598 file checksums and 50 scoped public
checks pass. Public DEPLOYMENT remains null. [Receipt](../reports/browser-wallet/pending-nonce/PUBLICATION.md).

The user explicitly authorized a narrowly scoped read-only confirmation/recovery
change in browser-wallet.js. Earlier byte-identical instructions remain historical;
this exception does not authorize nonlocal signing or journal deletion. BrowserClient,
transaction submission policy and deployment coordinator remain unchanged.

Submitted transactions are checked before receipt polling. Queued/changed/consumed
nonces return specific diagnostics promptly; normal canonical confirmation guards
remain. The UI moves past wallet-confirmation text after a hash and keeps Close
available. No resend, nonce rewrite, transaction drop, chain reset or journal clear.

[Evidence](../reports/browser-wallet/PENDING_NONCE.md): 175 affected cases, two mocked headless browser scenarios,
and six actual read-only recovery observations pass. Syntax/build pass. The actual
local mint 7df63a...00cc6 uses nonce 35 while the node expects 25 and remains unmined.
Replay reviews were reconstructed in memory, not taken from the user's browser.
Controlled queue reconciliation and actual extension acceptance remain open.
Preserve the running 8902 chain, NFTs/LP, saved transaction and paused monitoring.
Public DEPLOYMENT remains null; production NOT APPROVED. Use main and maintain
the sole Todo, features, operator guidance and both memories. Publication is separate.

## Real local API rehearsal and wallet totals - 2026-10-22

Publication: backend `f068f9f` and website `777fd05` are pushed on main. The
static server serves `777fd05`; all 5,598 checksums and 50 scoped public checks
passed. Public DEPLOYMENT remains null. See [receipt](../reports/api-chain-rehearsal/PUBLICATION.md).

The reviewed API coordinator now has actual local-chain evidence: mint, native
activation, exact USDC approval, $5 growth and a combined ETH claim. A deliberately
interrupted post-claim API read recovered the same confirmed hash with one send.
Wallet-wide LP and funded ETH totals use bounded 16-NFT chunks at one confirmed
block and complete inventory; missing/partial/mismatched data never becomes zero
or a partial total. Historical earnings remain per NFT; collection-wide aggregation
and portfolio-wide historical earnings are still separate open work.

Read [runbook](LOCAL_API_REHEARSAL.md) and
[scoped evidence](../reports/api-chain-rehearsal/VERIFICATION.md). APIs, core contracts,
receipts and transfers are real on isolated Anvil; venue math, token markets,
feeds and VRF are explicit local substitutes. The signing test uses an EIP-1193
RPC shim, not actual MetaMask/Rabby acceptance. Shared BrowserWallet/BrowserClient
remain byte-identical and local-only; public DEPLOYMENT remains null.

Separate fixture: port8902, external api-chain-rehearsal/runs; read running.json
before process control. Prior8900 processes were already absent; its saved files
were untouched. Monitor remains paused; the deferred load campaign was not run.
No production Solidity change or public transaction. Main only; preserve unrelated
drafts and keep the sole Todo, feature evidence, operator guidance and memories aligned.
Publication is recorded separately; inspect Git and the publication receipt.

## Local API wallet coordinator - 2026-10-21

Publication: website code `d786286` and contract evidence `59739ea` are on main;
the static server serves `d786286`. All 5,598 server checksums and 50 scoped public,
host/redirect/privacy checks passed. Public DEPLOYMENT remains null. See
[publication evidence](../reports/deployment-local-wallet/PUBLICATION.md).

The user explicitly chose **Keep the signer restricted to local Anvil** after
automatic approval review rejected the broader signer proposal. That proposal
was not executed. Shared BrowserWallet/BrowserClient remain byte-identical;
never generalize public signing from this work or treat it as release approval.

The reviewed API profile now has a local-only coordinator for mint, exact approval,
activation/growth and ETH claims. It requires environment rehearsal, chain 31337,
HTTP literal-loopback page and RPC. Nonlocal profiles remain unsigned. Approval
continues to a fresh complete LP review, never an automatic send or second approval.
Recovery retains the original journal/hash. Confirmed receipts with a lagging API
are labeled confirmed, with balances catching up. LP/artwork require the matching
Entry event and a confirmed active NFT position; claims do not mark artwork pending.

Read [operator procedure](DEPLOYMENT_WEBSITE.md#local-api-wallet-rehearsal)
and [scoped evidence](../reports/deployment-local-wallet/VERIFICATION.md): 84 affected
cases (57 API/session plus 27 coordinator) and nine headless browser scenarios.
The wallet/RPC are mocked; no actual extension or chain transaction was performed.
All 13 prior shared signer/backend bindings remain unchanged. Existing Anvil/8900,
wallet state, paused monitoring and the deferred load campaign remain untouched.
Public DEPLOYMENT is null. Production integration/qualification and independent
audit remain open. Use main; preserve unrelated drafts; maintain the one Todo,
features, operator guidance and both memories. Check Git/publication receipts.

## Reviewed website API profile - 2026-10-21

Publication: website code `757a8de` and contract docs `1dc05d3` are pushed on
main; the static server serves `757a8de`. All 5,597 server checksums and 41 public
assets, four host/redirect and four private-path checks passed. The public
configuration is null and financial actions remain simulated. See
[publication receipt](../reports/deployment-adapter/PUBLICATION.md).

The separate website now has a build-configured, default-disabled read and unsigned-
review profile for the existing APIs. Ordinary authorized accounts, eight-card
holdings pages, confirmed LP/ETH rewards, matching-block earnings and typed
mint/approval/Entry/claim reviews are implemented. Token-unit quotes target $100
activation (minimal raw-unit round-up) and at least $5 growth, with a 99% marginal
LP floor and separate gas. No signing or broadcast method exists in this profile.

Read [operator setup](DEPLOYMENT_WEBSITE.md) and
[scoped evidence](../reports/deployment-adapter/VERIFICATION.md): 57 focused cases,
eleven actual Python API response fixtures and eight headless browser scenarios.
Dependencies/wallets are mocked; this is not live provider/extension acceptance.
All thirteen earlier chain-reader bindings still match; unchanged signer/contract
suites and the deferred load campaign were not rerun. Build: 5,597 static files.

Automatic approval review rejected expanding the shared signer beyond local mode;
that proposal was not executed. Preserve its chain-31337 restriction and pending
journals. Public signing/qualified deployment config, routes, feeds, hosting,
full collection aggregation and independent release approval remain open. The
shipped DEPLOYMENT is null, so the public website stays simulated. Existing
Anvil/8900/session/NFT state and paused monitoring were not changed. Use main,
keep the single Todo/evidence/operator procedures aligned, preserve unrelated
drafts, and check Git/publication receipts rather than inferring publication.

## Publication checkpoint - 2026-10-20

The verified wallet implementation is published on main: contract/backend
df8a98a and website f060d66. The static Ubuntu site now serves website f060d66;
full server checksums and scoped public HTTPS/redirect/privacy checks passed.
See [publication evidence](../reports/browser-wallet/PUBLICATION.md).
The public site remains simulated; this is not a public contract/API deployment
or release approval. Local port 8900, Anvil and saved wallet/NFT state were not
reset. Thirteen source bindings still match the prior focused test evidence;
unchanged suites and the deferred load campaign were not rerun.

Actual MetaMask acceptance of the latest confirmation fix, production pins,
routes, feeds, services and independent audit remain open. Keep the single Todo
ledger and operator procedures authoritative. Preserve older unrelated local
drafts; they were not included in this publication. Monitoring remains paused.

## Independent chain confirmation - 2026-10-20

Shared wallet flows now read balances, simulation and confirmation through the
reviewed deployment RPC instead of extension-formatted transaction responses.
Wallet permissions/signing stay in the selected extension. Node and wallet chain/
genesis checks, exact approvals/calldata/fees and saved-hash recovery remain.
Legacy missing chainId resolves only through replay-protected EIP-155 v; typed
missing IDs fail closed. Approval never changes LP or artwork; Entry receipt plus
confirmed on-chain position remains required for activation/growth presentation.

[Evidence](../reports/browser-wallet/CHAIN_READER.md): 232 distinct website and 43 backend cases;
read-only recovery of the actual successful nonce-36 mint, exact-node CSP/CORS,
syntax/build and preservation of all 13 NFTs/LP/session after web-only restart.
Anvil 10988 was not reset. No signing/public transaction/server deployment or
paused-monitor change. Actual extension acceptance and production pins/routes/
RPC/fee qualification remain open; public signing is not enabled. Use main,
preserve unrelated drafts and check Git for publication. Keep Todo, feature
reference, operator guidance and both repo memories aligned.

## Canonical dynamic-fee receipt recovery - 2026-10-20

The user's mint 0xa7f91e…ac3891 succeeded at block 351. Anvil's derived fee fields
reported 1,000,000,014 wei/gas although signed cap and actual balance charge were
1,000,000,007. Shared signing and independent observation now derive EIP-1559
execution price from signed caps and canonical block base fee; original gas/unit/
paid-cost limits remain. Raw reported fee is retained separately. Deterministic
verification failures surface immediately with their specific reason.
[Evidence](../reports/browser-wallet/DYNAMIC_FEE_RECEIPTS.md): 142 signer/client and
40 observer tests, actual read-only mint receipt/balance replay, syntax/build pass.
Only local web worker restarted; session, 12 NFTs/LP and Anvil preserved. No new
holder/operator transaction or public deployment. Actual extension recovery retest
and production fee/profile qualification remain open.

## Mint loading presentation - 2026-10-20

Mint button loading now follows the actual activity instead of a generic busy
flag. Initial/refresh reads, connection, mint preparation, wallet confirmation,
receipt waiting and confirmed-state reconciliation have separate labels. Claims,
approvals and LP actions cannot label the button as a mint in progress. Existing
readiness/pending guards remain. See [evidence](../reports/browser-wallet/MINT_LOADING.md):
44 affected UI/lifecycle/contribution cases, syntax/build and served-source checks
pass. No signer, contract, backend, transaction, service or public deployment change.

## Numeric wallet nonce compatibility - 2026-10-20

The user supplied the exact failure: eth_getTransactionCount returned a number.
The shared website signer now accepts only exactly representable nonnegative JS
integers at its RPC response boundary, converting directly to BigInt. Hex responses
remain supported; prepared transactions/journals remain canonical hex. This has
no local-chain/address exception and keeps exact nonce, gas and receipt guards.
139 affected signer/client cases pass after reproducing the original failure.
See [evidence](../reports/browser-wallet/NUMERIC_NONCE.md). Actual MetaMask retest is
pending; public signing/Robinhood manifest qualification remains open. No backend,
contract, chain reset, public transaction, deployment or monitor change.

## Wallet lifecycle review - 2026-10-20

The browser connection/signing flow now separates provider discovery, account
selection, deployment verification, submission, receipt and balance refresh.
EIP-6963 providers take precedence over the legacy slot. Cancelled account choices
cannot poison later connections; network addition is followed by a verified switch;
account events and late provider restoration revalidate without transaction prompts.
The review identifies the extension/full sender and distinguishes unsent failures,
rejections, pending recovery and confirmed receipts. Existing exact approval,
calldata/gas, journal and confirmed-artwork safeguards remain.

[Scoped lifecycle review](../reports/browser-wallet/LIFECYCLE_REVIEW.md): 203 affected
website cases, syntax/build and served-source checks pass. The saved mint preflight
passes through direct local RPC without sending. Actual MetaMask acceptance and
its reported pre-prompt failure remain unresolved; Chrome inspection hit an app
approval timeout. No transaction, chain/service reset, backend/contract change,
public deployment or load campaign. Release remains NOT APPROVED.

## Review-dialog diagnostics follow-up - 2026-10-20

The transaction dialog now shows the escaped underlying failure instead of only
Review required. At observed local block 333 no new Wallet A mint was mined;
next nonce remained 0x23. Direct node balance/nonce/gas/estimate reads returned
canonical quantities. Actual browser-provider error is still needed; no confirmed
root cause or successful mint is claimed. Syntax and build pass; unchanged
signer/client tests were not rerun. No transaction/service/contract change.

## Wallet numeric-response failure - 2026-10-20

Reload updated frontend files. A failed preflight identifies the RPC field and
states that this operation was not submitted; refresh balances before another
review. If a saved submission exists, recover its original hash instead. Never
delete the journal or repeat a potentially confirmed approval/mint. Collect the
exact field diagnostic and wallet transaction hash when investigating; no keys
or full session data. Bounded hex padding is accepted only for provider reads.
[Evidence](../reports/browser-wallet/RPC_QUANTITIES.md): 123 focused passes.
The user's actual MetaMask response/root cause remains unconfirmed.

## MetaMask explicit reconnect follow-up - 2026-10-20


### Fresh MetaMask selection (2026-10-20)

This supersedes the earlier statement that explicit reconnect retains a chosen
sender. Refresh can retain a completed authorized selection, but clicking the
MetaMask button starts a fresh permission choice. Select the intended account in
MetaMask; if multiple accounts are shared, use its exact address in the website
picker. An unfinished choice cannot restore the previous sender. Pending
transactions must still recover under their original sender before switching.
No network or service configuration change is required; reload the updated app.
[Scoped evidence](../reports/browser-wallet/FRESH_SELECTION.md): 90 affected
passes; actual Chrome extension acceptance remains open.

## Authorized wallet account selection and clean picker - 2026-10-20

Fresh wallet picker sessions hide previous-attempt diagnostics and old provider
controls; actual pending-recovery notices and internal connection guards remain.
After choosing a provider, its authorized fixture accounts are selectable in the
website. Never infer the intended account solely from eth_accounts[0] or silently
choose a different allowed account. Wallet A may be selected even if an older
address is returned first; selection survives reload while still authorized.
The extension's private popup selection is not readable by the website.

Signer checks now require the explicitly reviewed sender to remain a valid member
of eth_accounts, plus unchanged account-event revision, network/genesis and all
existing economic/receipt checks. Revocation, wrong chain/genesis and pending
journals still block operations. Missing account permission requires one explicit
wallet authorization; no permission request on refresh and no silent substitution.

180 affected tests pass across 171 existing and nine new focused cases; syntax
and 5,593-file build pass. Read reports/browser-wallet/AUTHORIZED_ACCOUNTS.md.
No holder transaction, backend/contract change, chain/service restart, public
deployment or monitoring change. Actual MetaMask UI acceptance remains open.
Use main, preserve unrelated drafts, maintain the central Todo, feature evidence,
operator notes and both memories. Production remains NOT APPROVED.

## Main wallet button account retry - 2026-10-20

The user clarified that refresh restored the rejected MetaMask address and
clicking the main MetaMask button appeared to do nothing. The previous separate
chooser did not fix that normal button's read-only retry path. Main provider
click now rereads a previously rejected/restored account and invokes its selected
extension's chooser if that address is still inadmissible. If external wallet
selection already corrected it, normal verified reconnect avoids another prompt.
Refresh itself never opens permissions. Pending journals and exact deployment
checks remain; no silent account substitution or transaction send.

53 client tests pass, including four new rejected/restored/cancelled/corrected
retry cases. See reports/browser-wallet/ACCOUNT_CHOOSER.md (follow-up) and
docs/BROWSER_WALLET.md. Actual MetaMask acceptance still needs the user's click.
No backend/contract change, service/chain reset, public deployment or monitoring
change. Use main and maintain Todo/features/operator notes and both memories;
preserve unrelated drafts. Production remains NOT APPROVED.

## In-page wallet account selection - 2026-10-20

The user reports Rabby works but MetaMask exposes a previous site-authorized
address while another account is visible in the extension. Do not assume the
website can silently change wallet permissions. The local connection dialog now
offers Choose a different account in the selected extension. Its explicit click
requests only eth_accounts permissions, then reads current accounts/network and
verifies the admitted fixture account and exact deployment. Ordinary reconnect
remains read-only when already authorized; no automatic permission prompts.

Expected account-change events during the chooser do not invalidate the final
fresh verification. Cancellation, unsupported methods, busy prompts, empty/wrong
accounts and wrong networks stay unverified. Pending transactions block account
selection and retain their journals. No signing/transaction/approval occurs.
49 client checks pass including seven new cases; JS syntax and 5,593-file build
pass. See reports/browser-wallet/ACCOUNT_CHOOSER.md and docs/BROWSER_WALLET.md.
Actual MetaMask chooser acceptance remains user verification. No backend,
contract, Anvil/service/public deployment or monitoring changes. Use main;
keep Todo/features/operator procedures and both memories consistent, preserve
unrelated drafts. Production remains NOT APPROVED.

## Automatic receipt confirmation follow-up - 2026-10-20

The user still saw manual recovery after mint. The reported b041662e...6822560
receipt succeeded at block274. Read-only replay with its original review
reproduced old pending behavior under a synthetic lagging eth_blockNumber;
this cache condition was not directly observed in the extension.

One-confirmation inclusion now requires two canonical block hash/number reads,
without a separate cached head veto. Additional confirmations still require
the configured depth. Automatic polling is 21 attempts/1500ms, bounded by a
45-second monotonic read budget (each RPC also has its existing 15-second cap).
This supersedes the previous three-attempt/750ms note. The separate 90-second
wallet response wait remains. Same hash only; no automatic resubmission.
Persistent faults retain recovery, and the client displays the specific pending
reason. Economic, original gas, identity, genesis and reorg checks remain.

54 wallet and 42 client checks pass, with seven new cases. Read-only replay
confirms the actual mint without signing, acknowledgement or backend writes.
See reports/browser-wallet/AUTO_CONFIRMATION.md and docs/BROWSER_WALLET.md.
Refresh Chrome to load the changed client; actual extension acceptance remains
open. No service/Anvil restart, contract change, public deployment or monitor
restart. Keep main, preserve unrelated drafts, maintain Todo/features/operator
procedures and both memories. Production remains NOT APPROVED.

## Mint confirmation and local read latency - 2026-10-20

The user confirmed the minted NFT appears after Recover status. The successful
mint was inspected on-chain; the original UI failure cause is not established.
Wallet submission now has a separate 90-second response wait (read RPCs retain
15 seconds), and receipt faults retry the same hash up to three times. Never
resubmit a payment automatically or erase unresolved recovery records.
Same-account/session refresh preserves labeled confirmed cards with actions
disabled; failed reads and account changes do not present cached values as current.
Confirmed LP execution still controls artwork and sound.

The local serialized portfolio read now reuses its literal-loopback HTTP
connection, closing it at the end or on failure. Chain, canonical hash, response
identity, size and work-budget checks remain. Default production RPC transport
is unchanged. Eight-NFT state reads measured 6.057s before, 3.723s cold and 1.904s
warm after. This is not production capacity qualification.

48 signer, 8 contribution-flow and 35 Python cases pass; website build passed.
Read reports/browser-wallet/MINT_WAIT_PERFORMANCE.md and docs/BROWSER_WALLET.md.
Only the web process changed to 21472; original Anvil10988/RPC61752, session,
revision22 and eight NFT owner/LP/reward/trait records were preserved. Always
read running.json before process control. No holder/operator test transactions,
public deployment, unchanged Solidity rerun or paused-monitor restart.
Use main, preserve unrelated drafts, keep the single Todo ledger/features/operator
procedures and both memories consistent. Release remains NOT APPROVED.

## Browser-wallet local integration - 2026-10-20

Read [the browser-wallet procedure](BROWSER_WALLET.md) and
[scoped evidence](../reports/browser-wallet/VERIFICATION.md). The explicit local
/app/?wallet=browser profile uses injected EIP-1193 signing, independently checked
typed calldata, exact approvals, chain/genesis/runtime/nonce/gas checks and durable
per-account recovery. Browser drafts cannot use the service holder signer. Never
automatically retry a payment or erase an unresolved journal. Confirmed receipts
and actual LP reads still govern artwork/sound; approval alone changes no LP.

43 affected Python and 167 distinct JS cases pass across scoped runs. A five-user-
transaction Anvil journey covers mint, native activation, exact USDC approval and
top-up, and ETH combined claim, preserving the original four positions. The probe
uses an EIP-1193-shaped RPC test provider, not an actual extension. Chrome/MetaMask
acceptance remains open. Production deployment pins, live endpoint adaptation,
routes/services and independent release approval remain open; public signing is
disabled and release remains NOT APPROVED. The large load campaign stays deferred.

The previous 8898 processes were already gone. Separate 8900 fixture data is in
EXT/browser-wallet-lab/run-20261020-180024-5688c6; read running.json before process
control. No old live chain reset, public deployment or monitor restart. Use main,
preserve unrelated drafts, and verify Git for publication. Keep central Todo,
feature evidence, operator procedures and both repository memories consistent.

## Manual acceptance and next priority - 2026-10-20

The user reports all six proposed local 8898 two-wallet scenarios passed; read
[manual acceptance](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md). This is
user-reported evidence, not new automated tests or independently captured receipts.
The user deferred the proposed 10/25/100-user load campaign; do not run or schedule
it without a later request. Production capacity remains UNVERIFIED. Next focus is
real browser-wallet integration with unsigned preparation and independent signing.
Basic bounded service concurrency, safe transaction recovery and dependency/release
qualification remain required before real funds. The shared local signer/lock is
test-only. Release remains NOT APPROVED. Use main; preserve unrelated drafts.
No code/test/service/deployment/monitor change is included in this documentation
update. Keep Todo, feature evidence, operator procedures and both repo memories
consistent; docs/project-todo.json is the sole task-status ledger.

## Independent sender nonce checkpoint - 2026-10-20

Current 8898 web PID20672 uses per-sender nonce-bound wallet drafts, resolving the
remaining cross-wallet global revision rejection. Anvil PID35896 was preserved.
Both real local mints reviewed at revision34 confirmed at35/36, adding dormant
#15 and #16 (one per owner); 14 existing owner/LP records unchanged. Read
[verification](../reports/local-wallet-concurrency/NONCE_VERIFICATION.md).
70 distinct affected Python cases pass. Reload browser pages; old unsigned reviews
were invalidated by the guarded web-only restart. Preserve saved pending intents
for identical-ID recovery. Legacy operator actions retain global revision checks.
No production Solidity/public server/monitor change. Port8896 not upgraded.
Main only; preserve unrelated drafts and verify Git for publication.

## Second-wallet submission lock follow-up - 2026-10-20

The browser error was the exact pre-handler /action busy response. Client now
waits with the identical durable envelope only for that response. Ambiguous
responses keep recovery; stale reviews are not automatically submitted. 64 cases
and real local lock/rejection probe pass; see reports/local-wallet-concurrency.
Reload pages, preserve pending intents and Anvil; no service restart needed.
No public deployment or production contract/backend change. Main only.

## Cross-browser local wallet continuation - 2026-10-20

Chrome/Codex stale-cache confirmation mismatch fixed in website local-client.js;
read [evidence](../reports/local-wallet-concurrency/VERIFICATION.md). Reload both
8898 pages to load it; do not restart or reset either Anvil chain. Newer unsigned
drafts reconcile actual confirmed state with bounded retries. Post-review changes
still require fresh review; backend global revision protection remains. Ambiguous
submissions keep the identical pending ID. Only confirmed pre-handler rejections
clear saved intent. No production contract/server/monitor changes. Main only,
preserve unrelated drafts and verify Git publication.

## Latest local continuation - 2026-10-20

Local read-clock bottleneck and contribution flow corrected; see
[verification](../reports/local-contribution-flow/VERIFICATION.md). Existing
8896 Anvil/NFTs/LP were preserved through a web-only recovery. A separate native
fixture is available at http://127.0.0.1:8898/app/#my-nfts with mock native venue
admission. ETH is one atomic Entry call; supported ERC20 needs at most exact
approval plus Entry. The current processes use external session recovery launchers;
consult the external run directory/running.json before process control. Do not
reset either chain or assume normal launcher restart resumes its persisted state.
Only the web processes were replaced; old unsigned drafts are invalidated.
No public deployment/server/paused-monitor change. Main only; preserve unrelated
drafts and verify Git publication. Production still requires live route/service
qualification and fixed-$100 pricing policy alignment.

## Local activation busy-response fix - 2026-10-20

The current local website adapter retries only pre-handler busy unsigned
preparation, with bounded waits, account/state cancellation and unchanged expiry.
Never auto-retry submission. Reload the page; preserve the running 8896 Anvil
state. No contract/backend restart or public server change is needed. Read
[scoped evidence](../reports/local-preparation-busy/VERIFICATION.md). Production
wallet integration remains open; check Git for publication.

## LP holder ETH settlement checkpoint - 2026-10-20

The user approved a 1% maximum LP reward conversion loss, gas separate. Read
[the operator procedure](LP_ETH_SETTLEMENT.md) and
[scoped verification](../reports/lp-eth-settlement/VERIFICATION.md). A dedicated
pre-seal-bound converter checkpoints earned 80% individual/10% collective
balances and credits ETH to the same NFTs. Principal, compound/buyback, dust
and rarity economics are unchanged. Source claims remain an explicit fallback.
Native payouts, exact backing/abort and same-chain handoff, bounded keeper
priority, history/earnings reconciliation and ETH-default local UI are implemented.
Vault/Fees handoff helpers skip the Rewards-only native slot. Do not reintroduce
ERC20 reads at asset zero or count conversion as new earnings/claimed income.

142 distinct affected Solidity cases pass across scoped runs, with 32 normal
object gates/41 production bindings and a 33-assertion fresh local Anvil journey.
Backend/UI results, initial failures and corrected fixtures are recorded in the
report. This is not a full fresh regression or independent audit. Actual routes,
feeds, wrapper policy, operator pins, Linux/gas/settlement-latency qualification
and release approval remain open. Core sealing alone does not certify converter
setup; require the binding before sealing. Production remains NOT APPROVED.

Use main; check Git and deployment receipts for publication. The separate new
local fixture uses port 8896; prior user fixtures were not reset. No public
contract transaction/deployment or paused-monitor restart. Preserve unrelated
drafts; keep Todo, feature evidence and operator procedures together.

# Client admission continuation - 2026-10-20

The current change closes the local per-client admission implementation gap in
host services: bounded IP concurrency/state, separate read/preparation rate
budgets, explicit local-proxy identity and exact-origin validation, and restricted
Nginx includes. Read [the operator procedure](API_INGRESS.md) and
[scoped verification](../reports/api-admission/VERIFICATION.md): 47+3 distinct
Python passes, 22 actual local Nginx assertions, sanitized logs and matching hashes.
The first Nginx harness attempt lacked a temporary directory; the corrected
isolated run passes without a policy change. No unchanged contract tests rerun.

Linux/TLS/default-host/CDN policy, real RPC/provider load, multi-host quotas and
off-host alerts remain open under the central service task. The test uses local
HTTP and fake projections, not real transactions. No public website/server,
contract deployment, Anvil user-state reset or paused-monitor restart. Use main;
check Git HEAD/origin for publication. Older unrelated drafts remain separate.


## Contribution floor and NFT earnings checkpoint - 2026-10-19

The user requires $5 minimum LP increases; initial activation remains $100.
Entry and the fixed Vault budget helper enforce both, including direct Vault
calls and higher pool minima. The original-source 99% new-LP requirement and
separate gas remain. Backend preparation and new website actions agree; legacy
v7 preview events are preserved rather than resetting saved holdings.

Read [minimums](CONTRIBUTION_MINIMUMS.md), [scoped verification](../reports/topup-and-reward-review/VERIFICATION.md)
and [internal review](../reports/topup-and-reward-review/REVIEW.md). Fresh evidence:
91 Solidity passes, 32 normal compiler-object gates (Vault 19 runtime bytes spare),
74 distinct Python and 102 distinct JS cases across documented scoped runs.
No full fresh regression, independent audit or public-chain qualification.

Cards/details use NFT net earned individual+collective+royalty totals. The fee
labels and regular-weight values share one compact line below centered LP attached;
Rewards to claim is separately centered. No gross fees on NFT cards. Original
demo 24h net history is unavailable; local totals require exact snapshot identity
and all price components. Optional local history failures retain core balances;
terminal budgets/core errors remain fatal, dormant reads skip history.

Main only, preserve unrelated drafts and establish publication through Git. No
public server update, public transaction or monitor restart. Existing local
8892 contracts were not replaced: start a separate source-matched disposable
fixture to test the new binary without deleting the current session. Central
Todo, feature/evidence and operator procedures are updated together.

## Local website integration checkpoint - 2026-10-19

Read [the website local-mode guide](LOCAL_WEBSITE.md) and
[scoped verification](../reports/local-website/VERIFICATION.md). The existing website
can run at the local launcher's /app/ mount with confirmed contract ownership,
current LP, earnings, royalties and lifetime claims. Explicit confirmations cover
mint, exact approval, Entry/top-up, transfer and bounded combined claims. Failure
clears projections; identical operation IDs recover lost responses. Source assets,
public demo behavior and v7 storage remain separate.

The user accepted local integration before public deployment. Only disposable
launcher-owned Anvil accounts are used; production EIP1193 signing is still open.
No production Solidity, public transaction, server deployment or paused-monitor
restart occurred. The four frontend tasks are in progress, not production complete.
Keep main only, preserve unrelated drafts, update Todo/features/operator procedures,
and verify Git publication. Repository context is durable local memory only.

## Local browser stack continuation - 2026-10-19

The user requested that we set up and run the local test environment. Read
[the local runbook](LOCAL_TEST_STACK.md) and
[scoped verification](../reports/local-stack/VERIFICATION.md). The separate local
panel at port 8890 uses real sealed core contracts, Entry, Strategy, budgets,
funded LP/royalty ledgers, ClaimRouter and confirmed indexed API projections.
LocalDemoVenue replaces LiquidityManager/Uniswap, LocalFeed is an always-fresh
$1 mock and MockVRF has no proof. It is not a public-chain/provider qualification.
The completed journey verifies mint, activation/no retroactive income, top-up,
funding, rebalance, ownership transfer and repeated combined claims/lifetime totals.
The expanded 39-assertion Anvil journey passes, including adversarial input/replay checks;
35 focused launcher/HTTP/recovery cases pass. Strict action schemas, revision
checks, durable operation IDs, bounded workers/timeouts and atomic evidence writes
protect the local panel. Refresh recovers a lost response with the same ID;
uncertain submissions block new operations. Production sources are unchanged
and their suites were not rerun. The public website/server and paused
monitor are unchanged. Production website wallet integration remains open.
Local state and full receipts are external, disposable and not recoverable as a
chain after shutdown; restarting creates a fresh deployment. Source and metadata
are verified against reused artifacts. No private key or public funds are used.
Use main; preserve unrelated drafts and check Git for publication. Update the
central Todo, feature/evidence reference and operator manual with future changes.

## Earnings ingestion audit continuation - 2026-10-19

The earnings backend and unsigned mint/claim preparation are already published;
do not reimplement the older quoted plan. This follow-up adds a read-only
[history audit](HISTORY_AUDIT.md) comparing one configured current/predecessor
epoch window with a separately reviewed RPC. It requires all seven emitters,
exact cursor/header/log identity, confirmed ancestry and bounded work. Missing,
conflicting or unavailable data never yields a matched window. The indexer adds
one ordered block/log SQLite index; no economic replay or contract code changes.

[Scoped evidence](../reports/history-audit/VERIFICATION.md) covers 41 distinct affected
cases across new execution and exact-body reuse, including 10,000 logs/128 blocks
and protected CLI output paths. No unchanged Solidity or earnings suites rerun.
Actual independent providers, full backfills, reviewed prices, large-history/load
qualification and website integration remain open. Provider agreement and a
partial window report are not completeness/finality proofs. Follow the linked
operator procedure; no server, website, public-chain or paused-monitor change.
Use main, preserve unrelated drafts and check Git for publication. Keep creator
questions in their central section; release remains NOT APPROVED.

## Unsigned wallet preparation continuation - 2026-10-19

The saved mint/claim draft is now hardened for the current lifecycle and promoted
with [operator instructions](FRONTEND_TRANSACTIONS.md) and
[scoped evidence](../reports/wallet-preparation/VERIFICATION.md). Typed 0.05 ETH mint
and 1-32 mixed LP/royalty claims simulate at a confirmed canonical hash. Mint-only
pause and preparation block mint; eligible claims remain available. Unselected
currency faults can be isolated, while selected assets, inventory/core mismatches,
canonical locks, expiry and work budgets fail closed. A required reviewed policy
binds the read configuration and separately bounds/estimates gas; no signer or
broadcast exists. Default GET-only; explicit transaction config enables POST in
a supervised serial worker. Browser integration and live fee/RPC qualification
remain open. The 149-test affected inventory has passing evidence across two
scoped runs; the initial reorg fixture correction is recorded. All 40 Solidity
source bindings and six compiled ABIs match reusable artifacts; no contract rerun.

Use main and Git to establish publication. Preserve unrelated route/process-runner,
history-test and artwork drafts. No website/server/deployment/public transaction
or paused-monitor change. Update central Todo, features and operator manual with
future changes; release remains NOT APPROVED.

# Resume handoff - 2026-10-19

This is a continuation record, not another task list. Remaining work and acceptance
criteria live in the [central Todo](../TODO.md#task-security-chain-recovery).

## Current checkpoint

Implemented [processed earnings and today-price USD](EARNINGS_HISTORY.md).
The user chose current prices for both all-time and 24h earned source amounts.
Read [the 186-test scoped evidence](../reports/earnings-history/VERIFICATION.md)
for exact reuse/corrections; no Solidity rebuild/tests repeated. Per-NFT payouts,
conversions, fractions, deferred royalty cohorts and same-chain imports reconcile.
The current profile requires all seven emitters from creation; preserve old
indexes when backfilling. Missing prices are null, not assumed stablecoin pegs.
Next qualify actual providers/feed pins, complete ingestion/load/reorg operation
and the live frontend consumer. Keep this reporting separate from claimable and
previously-claimed fields. Main publication is established by Git; unrelated drafts
remain local. Website/server/paused monitor and public-chain state are unchanged.


The [royalty reporting profile](ROYALTY_REPORTING.md) now exposes confirmed
ETH/source balances, per-currency deferred eligibility and pinned converter enable
control. Exact conversion replay and same-chain predecessors preserve conversion
credits separately from actual lifetime LP/royalty claims. Current ETH claimable
already includes unclaimed converted amounts. Read [scoped evidence](../reports/royalty-reporting/VERIFICATION.md):
138 affected Python passes followed by 20 supplemental passes, 40 unchanged
Solidity bindings reused, ten getter ABIs and 26 added schema events verified.
The test trees exclude unrelated unpublished wallet/server/route/history-test drafts.

That reporting milestone is now followed by the processed earnings profile above.
Remaining integration work is actual price/ingestion qualification, live frontend
wallet/data behavior and actual service/route qualification.
Use the central Todo and keep operator procedures in sync. No website/server,
paused monitor, deployment or public transaction changed. Use main; Git establishes
publication. Preserve unrelated drafts and reuse unchanged contract evidence.

The read-only [replacement holder preflight](HOLDER_PREFLIGHT.md) now inventories
confirmed ownership/code, flags unresolved escrows/delegated accounts and detects
incomplete/mixed pages. Actual release/claim rehearsals remain open. See
[scoped evidence](../reports/holder-preflight/VERIFICATION.md); no Solidity changed
in this follow-up, so the royalty verification was reused without rerunning it.

The royalty conversion continuation implements guarded batches, per-currency
outage recovery and optional keeper automation. Read [the runbook](ROYALTY_SETTLEMENT.md)
and [source-bound verification](../reports/royalty-conversion/VERIFICATION.md).
The approved 1% cap excludes gas; older unapproved/not-implemented statements
below describe the earlier checkpoint. Live qualification remains open, release
NOT APPROVED, website/server/paused monitor unchanged. Use main and preserve drafts.

Historical October 19 royalty clarification (superseded by the implemented checkpoint above): [the accepted direction](ROYALTY_SETTLEMENT.md)
is ETH pricing and verified ETH/WETH royalty receipts first. If USDC/USDG royalty
settlement cannot be excluded, implement guarded automatic ETH conversion. OpenSea
documents Robinhood ETH/USDG pricing selection; it does not establish a universal
currency ban or qualify actual collection settlement. Buyer checkout assets may
differ from receiver settlement. No royalty conversion or failure-isolation code
has changed. Delayed per-currency eligibility was discussed, not approved. The
central Todo, operator procedure and feature boundary distinguish this planned work
from current direct per-currency claims. Documentation-only verification does not
require repeating unchanged contract tests. No marketplace/service action occurred.

The October 19 operator-controls continuation adds dependency-independent,
disable-only `PoolRegistry.disablePool` and governed `NFT.setMintPaused`.
Pending original reveals and existing economic rights retain their own guards;
mint callbacks cannot commit after setting the mint pause. Reopen pools through
full validation. The confirmed API reports mint-only pause separately.
Read [current evidence](../reports/operator-controls/VERIFICATION.md) and the
[updated operator manual](OPERATOR_MANUAL.md). Prior full/static evidence retains
its original scope; no website/server/deployment/monitor action is included.
Unrelated unpublished drafts remain preserved. Use main and Git for publication.


The October 19 continuation adds [the operator manual](OPERATOR_MANUAL.md) with
mandatory same-change maintenance in repository instructions/Todo workflow, API
request-wide work limits and supervised workers, plus confirmed mint readiness.
Read [scoped verification](../reports/api-work-limits/VERIFICATION.md) for results
and source bindings. Solidity is unchanged; do not repeat unchanged suites.
Randomness policy is qualified/funded service plus draining original requests
before replacement; no reroll/carry. Keep the 3% cap per operation only. Production,
provider/escrow/hosting qualification remain open; main publication is established
by Git. Website/server/paused monitor and unrelated drafts remain unchanged.


The [review of October 18 changes](../reports/daily-security-20261018/REVIEW.md)
was completed October 19 against 13 commits through `485a089`. No production
code changed. Existing build/source hashes matched; unchanged suites were not
rerun. A new synthetic expiry check reproduced continued API work before safe
rejection. Request-wide deadlines and RPC-work limits belong to host-services;
the unfulfilled-VRF/handoff dependency belongs to fair-draw and canonical recovery.
Successor escrow compatibility, immediate governance trust and cumulative
maintenance costs remain recorded risks. The central Todo contains acceptance
criteria. Release stays NOT APPROVED; preserved local drafts remain unpublished.

Governance now has **no mandatory waiting period**, including the additional LP
migration delay. The user explicitly superseded the earlier delayed policy and
proposed route-only exception. Read [authority semantics](GOVERNANCE.md) and
[scoped evidence](../reports/immediate-governance/VERIFICATION.md). Target safety
checks, sealing and finality remain; there is no advance warning window. Update
production authority/runtime records and operating procedures before approval.
No deployment or website/server change occurred; monitor stays paused. The
randomness provider decision remains open and unchanged. Use Git for publication.


The [read-only route campaign](INTEGRATION_CAMPAIGN.md) now records a successful
paced USDG/ETH feed and four-route conversion observation. This is not complete
activation, a public transaction or a new fork/test pass. See [its scope](../reports/activation-route-observation/VERIFICATION.md).
Actual PoPL deployment, qualified services and operator-run transactions remain
open; the private key was not accessed. Earlier HTTP failures remain preserved.

The [local $1 rehearsal](ONE_DOLLAR_REHEARSAL.md) is separately implemented and
verified (10 Solidity / four Python). Production $100 activation / 0.05 ETH mint rules
are unchanged; no public transaction or website/API deployment was made. Read
[its evidence](../reports/one-dollar-rehearsal/VERIFICATION.md) for the original
fixture failure and successful corrected run. Real defects found in later tests
must be fixed in production with targeted evidence; the $1 override stays isolated.

The latest [range-policy path](RANGE_POLICY_UPDATES.md) is implemented. After a
governance-approved range update, ordinary keeper rebalance becomes eligible once cooldown
passes even at a flat price. It compares current LP ticks at the recorded center,
preserves existing Vault guards and clears the mismatch on success. No forced
execution role/state was added. Backend context now reports the pending range
cause and checks both triggers. Read [current evidence](../reports/range-policy/VERIFICATION.md).
Only Strategy production Solidity changed; broad unchanged suites were not
repeated. Vault still has 19 runtime bytes of headroom. Runtime manifests, real
range/MEV/gas qualification, services and independent review remain open. The
website/server and paused monitoring are unchanged. Check Git for publication.

The [dynamic-liquidity review](DYNAMIC_LIQUIDITY.md) adds the user-approved
out-of-range warning with honest eligibility timing, the 3% aggregate ordinary
rebalance budget, guarded current NFT valuation and current-LP API context.
[Verification](../reports/dynamic-liquidity/VERIFICATION.md) binds affected
checks to these changes; the earlier full handoff regression below is historical
for its source snapshot and must not be presented as a new full regression.
Vault has 19 runtime bytes of headroom. Use the central Todo for live range/
strategy qualification, next-check telemetry, wallet integration and audit.
No website/server or monitoring service changes are included.

Complete activation/top-up preparation is implemented separately from the old
mint/claim and conversion-only drafts. Read [the integration contract](ACTIVATION_PREPARATION.md)
and [scoped evidence](../reports/activation-preparation/VERIFICATION.md): 38 focused
checks passed on the exact publication snapshot; 63 ABI getter layouts and local
Anvil trace/gas/budget mechanics were verified using source-matched artifacts.
The backend returns the current NFT on-chain marked value separately from the
new marginal LP contribution, an exact unsigned Entry call and separate gas.
Insufficient approval returns only an approval/reset step and requires re-quoting
after confirmation. Production manifests/routes/feeds/RPC fee semantics and the
wallet/hosted-service integration remain open; no website/server changes occurred.
Source/evidence/docs are published together on main; use Git for exact identity.


The latest [claim-lineage checkpoint](FRONTEND_LINEAGE.md) extends the schema-2
lifecycle API with complete explicitly configured same-chain predecessor replay.
It verifies both handoff directions, canonical retirement/activation receipts and
terminal source commitments, then includes all prior LP/royalty claims and owners.
Old indexes may stop at retirement; historical-only assets remain visible.
Missing configuration stays unavailable; invalid lineage fails closed.
[Scoped verification](../reports/frontend-lineage/VERIFICATION.md): 91 passing
API/lifecycle/history cases on the exact publication snapshot, plus two getter and
two event layouts checked against source-matching existing compiler artifacts.
Production Solidity is unchanged and its tests were not repeated. Live archive
services, independent peer review and website integration remain open.
The optional wallet POST drafts remain outside this scoped publication.

The earlier handoff's saved bridge-fixture fixes and final cold-gas checks were
verified. That regression passed **582 cases with zero failures and two intentional fork setup
skips** across 49 suites. The unchanged 34-case focused handoff run is reused after
checking all compiled dependencies, giving 616 successful cases in combined scope.
These are separate source-matched runs, not one new 616-case execution.

This checkpoint accompanies the scoped canonical-handoff publication on **main**.
Use Git HEAD/origin/main to verify the exact publication; the earlier
`79f205a7933107f61f26892109f14ee52821700e` checkpoint and its uncommitted wording
are historical. Unrelated wallet/API, quote/process-runner and artwork drafts
remain outside this publication. Do not use `git add .` to include them later.
No contract has been deployed and no website/server service was changed.
Release remains **NOT APPROVED**.

## Implementation and accepted trust

Read [the implemented handoff boundary](CANONICAL_HANDOFF.md). It supports only
same-chain replacement: all mints revealed, buckets Parked/None, no active plans
or historic legacy bridge activity. Freeze captures all six receipt cutoffs
atomically; phase 8 settles domains once in strict order before export. Complete
state/import and exact classified backing precede atomic source retirement and
single-successor activation. Restored abort and one-hop late forwarding exist.

The user accepts different reviewed replacement code approved through timelocked
governance, including the risk of a malicious approved successor diverting LP.
Do not impose identical-code admission. Future-chain activation still requires
verified source finality with no multisig/timeout override. Authenticated channel
closure, new lineage/message semantics and exact cross-chain transport/backing
remain pre-seal work. Sealed code cannot acquire absent capabilities later;
post-halt recovery is deferred.

## Evidence to reuse

The [verification record](../reports/canonical-handoff/VERIFICATION.md) separates:

- The new 582-case regression, including repaired bridge suites and ten cold-gas
  cases, with unchanged sources and explicit fork skips.
- The reused 34 focused passes, 30 normal object gates/39 production bindings,
  141 configuration checks and 88 keeper lifecycle checks.
- The current-source internal review of 374 Slither findings, coverage and ten
  mutation rejections. Internal review does not replace an independent audit.
- 123 additional successful keeper cases; one Unix permissions case awaits
  Ubuntu. The venue fixture and local deployment script compile/type-check,
  without implying deployment or operating rehearsal.

[Reuse verification](../reports/canonical-handoff/reuse-verification.json) binds
prior evidence to unchanged source dependencies. Do not repeat checks solely to
increase counts. Vault has 33 runtime bytes of headroom and Migration 58;
constructor arguments still need deployment allowance.

## Next work boundaries

Follow the owning tasks in the central Todo for exact-commit Ubuntu CI, keeper
operating qualification, live API/indexer and same-chain history integration,
marketplace/contract-owner cutover, qualified live services and independent audit.
The cross-chain requirements remain implementation work, not completed by the
same-chain tests. The initial release still requires migration disabled.

The chat health monitor was **paused at the user's request on 2026-10-17**.
Do not restart it without authorization. That action did not stop the isolated
server service; the period after pause has no chat-monitor observation coverage.

## Artifact and publication discipline

External artifacts and runner scripts remain under:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/handoff-20261017`.

Current broad receipt: `regression/attempt2/receipt.json`; reused focused receipt:
`focused/attempt5/receipt.json`; normal production build: fresh attempt9 and
successful cached attempt10. Fresh static analysis is in
`static-analysis-settlement/`. Continuation tooling is in `resume-20261018/`.
Original failed/stale diagnostic attempts remain preserved and are not merged
into passing results. Raw large logs stay external with hashes and full compact
case outcomes in the repository. Do not overwrite existing attempt directories.

Do not rerun `publish_local_evidence.py` blindly: its historical review assumption
is obsolete. Preserve strict reentrancy write-bundle comparison metadata when
updating the review. Keep compiler/profile and tested source unchanged during a
verification run. Current CI allows 60 minutes for local checks and includes
canonical/preparation keeper tests; that timeout does not relax gas assertions.

For every change, update `docs/project-todo.json`, regenerate `TODO.md`, run the
sync tool with `--check`, and reconcile affected evidence/release references.
This is durable repository context, not a claim of global personal memory.

Latest user clarification: holder LP rewards must also settle in ETH. The
[audit](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md) finds LP conversion
and unwrap absent; royalty-only conversion is not sufficient. The local read-only
claim trace confirms source ERC20 plus native royalties and leaves claims intact.
Track implementation before sealing; no new LP conversion-loss policy is assumed.
The current local input balance was replenished without restarting the chain.
Palette names now use their own text colors in both website modes, without pills.

Contribution UI follow-up: four visible input choices (ZZZ/USDG/USDC/ETH), WETH internal only, dedicated contribution dialog and confirmed per-NFT evolution refresh. See [named local rehearsal](LOCAL_TEST_STACK.md#named-input-local-rehearsal). No production authority/procedure change; public routes, ETH-only LP settlement and hosting remain open.
