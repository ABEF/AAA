# Security review of the 2026-10-18 changes

**Internal review, not an independent audit or production approval.** Reviewed
published `main` from `79f205a7933107f61f26892109f14ee52821700e` through
`485a089a6a06f0010c13b222ad84881123c28812`: 13 commits dated October 18 in
Europe/Paris; review completed October 19. [Scope and source hashes](scope.json) identify 84 changed code,
test and configuration files, including 25 production Solidity files.

No new unauthorized principal-withdrawal path, hidden privileged recipient,
ordinary-caller authorization bypass or reproducible double claim was identified
in the reviewed changes. This is a bounded review result, **not a proof that no
vulnerability exists**. The candidate is not ready for real funds. In particular,
explicit governance authority can harm holders, and important recovery and
service-availability requirements remain unresolved.

The review covered migration/accounting, activation preparation, lifecycle and
claim-history APIs, keeper changes, valuation, execution budgets, range changes,
zero-delay governance and the isolated dollar rehearsal. Existing unpublished
API/quote/process-runner drafts were inspected separately; their hashes are in
[the local-draft scope](local-drafts.json). They are not part of the published
candidate. No production code, external service, private key or live deployment
was changed or used in this review.

## Material findings and boundaries

### AUD18-01 - High-impact accepted trust: immediate governance

[AccessController](../../src/ZZZAccessController.sol) retains role checks, exact
operation hashes, cancellation, predecessor ordering and replay protection, but
its scheduling delay is zero and cannot be increased. The additional migration
waiting period is also zero. This implements the user's explicit policy; it is
not an accidental public authorization bypass.

Compromised or malicious authorized governance can immediately approve harmful
feeds, external dependencies or compatible successor code. The accepted ability
to approve different successor code means that an approved malicious replacement
could divert LP. Code hashes authenticate selected bytes, not their honesty.
Sealing and execution-loss checks cannot compensate for malicious approved
valuation or replacement semantics. A guardian pause is not a veto over governance.

Before release, independently review the actual multisig, signers, role holders,
operation review procedure and dependency/code admission. There is no advance
reaction window. This report does not reinstate a timelock or an identical-code
restriction. Owner: [governance security](../../TODO.md#task-security-governance).

### AUD18-02 - High availability impact: randomness failure also blocks handoff

[NFT ordered reveal](../../src/ZZZNFT.sol) cannot skip an earlier unfulfilled
request. The configured coordinator is fixed after sealing; there is no admin
reroll, cancellation or timeout fallback. The new
[canonical capture](../../src/ZZZNFTCanonical.sol) requires
`nextToFinalize == mintedCount + 1` and complete revealed inventory before freeze.

Consequently, one permanently unfulfilled mint request prevents subsequent
reveals **and prevents the current whole-collection handoff**, even while the
home chain works. Pausing new minting does not repair that existing request.
Already active NFTs do not automatically lose claims or LP maintenance from this
condition; it is a reveal/relocation liveness limitation, not a demonstrated theft.

This is supported by source and the existing
`testFreezeRequiresTimelockAndFullyRevealedMintInventory` case in
[the handoff suite](../../test/CanonicalHandoff.t.sol). The historical test name
does not imply a current governance delay. That unchanged case was not rerun.

Qualify provider fulfillment/retry and permanent-request-failure behavior before
sealing. If continuity cannot be established, a separately reviewed design must
preserve pending proof commitments and ordered assignment through recovery or
handoff, without creating a reroll/admin trait selector. Merely appointing a new
server or approving a successor cannot bypass this condition in sealed source.
Owners: [fair draw](../../TODO.md#task-fair-draw),
[canonical recovery](../../TODO.md#task-security-chain-recovery).

### AUD18-03 - Medium availability gap: preparation lacks a total work deadline

[Activation preparation](../../frontend_api/activation.py) verifies freshness at
the beginning and end, but runs many serial RPC reads and two traces in between.
[RPC timeouts/retries](../../zzz_ops/rpc.py) bound individual calls; they do not
bound total request duration or cancel work when a draft expires. The
[HTTP server](../../frontend_api/server.py) processes requests serially.

A new [targeted reproduction](availability-reproduction.json), using the actual
published preparer and synthetic RPC fixture, advanced the clock past expiry
after the first pinned code read. Preparation continued with **134 RPC calls,
including two traces**, before rejecting the stale snapshot. **No unsigned
transaction was returned.** This proves late detection and continued work, not
a public denial-of-service incident or measured network latency.

The current endpoint is loopback-only. Exposing it through a public proxy without
aggregate work limits could occupy its serial worker and consume RPC capacity.
A proxy response timeout alone does not stop backend work. Before hosting, add a
monotonic request-wide deadline/cancellation and RPC-work budget, bound upstream
retry time by remaining budget, and qualify admission/rate limits and sanitized
timeout metrics. Preserve final canonicality/freshness checks. Apply equivalent
bounds to long ownership/history reads. Owners:
[host services](../../TODO.md#task-host-services),
[activation preparation](../../TODO.md#task-activation-quotes).

### AUD18-04 - Conditional holder liveness: old escrows may not handle successors

[NFT import](../../src/ZZZNFT.sol) preserves the exact owner address using `_mint`
without an ERC721 receiver callback, and old approvals are not imported. This
avoids callbacks during inert state import, but does not establish that a contract
owner or marketplace escrow can transfer a token from the replacement collection.
An escrow hardcoded to the old collection could strand its replacement NFT and
associated rights after an otherwise correct handoff.

This known compatibility boundary needs concrete supported-wallet/escrow
rehearsals and a cutover procedure before migration approval. Do not silently
change owners or restore obsolete approvals as a workaround. Owner:
[canonical recovery](../../TODO.md#task-security-chain-recovery).

### AUD18-05 - Accepted economic limit: per-operation budgets are not cumulative

The [budget helper](../../src/ZZZMigrationBudget.sol) snapshots starting prices,
accounts for released compound and requires at least 97% retained LP plus
attributed idle for supported local moves/rebalances; the idle ceiling remains.
It does not promise 97% actively deployed LP, cover gas, protect against malicious
approved feeds, or impose a lifetime loss budget. Multiple allowed operations can
compound losses. Activation/top-ups retain the separate 99% marginal LP rule.

Cooldown/trigger checks remain, including after an immediate range change. Review
real widths, turnover, MEV and cumulative costs with target-chain observations.
Do not equate the ten-minute polling interval with a forced rebalance schedule.
Owner: [strategy security](../../TODO.md#task-security-strategy).

## Security paths reviewed

| Boundary | Review result and limit |
| --- | --- |
| Handoff authorization and uniqueness | Fixed coordinator/owner bindings, same-chain preparation, six ordered domains, complete roots/counts, exact classified backing and atomic source retirement/single-successor activation. Abort restores sent backing before reopening; source economic paths stay terminal after retirement. Different successor code remains an explicit trust boundary. |
| NFT ownership and rewards | Current-owner claims, exact fractions/ledgers across handoff, frozen ownership/accounting, callback lifecycle guards, one-hop late receipt forwarding and no caller-selected principal recipient. Unpaid rights follow the NFT. Marketplace/escrow compatibility and external payment remain distinct requirements. |
| Shared LP and maintenance | Starting-price aggregate budget, exact released compound, attributed idle, unchanged marginal deposit floor, guarded spot/oracle valuation and cooldown-aware range updates. Donations or claimable rewards are not credited as fresh deployed contribution. Different-pair/asynchronous migration is not supplied by this budget. |
| Backend projections and drafts | Canonical hash/code/role/route/feed pins, lifecycle rejection, exact full-operation simulation, typed unsigned transaction construction, gas separate, complete predecessor histories or failure, final canonicality/expiry checks. AUD18-03 remains. No signer or broadcast path was added. |
| Keeper lifecycle | Strict lifecycle checks block new work during import/freeze/retirement; pending receipt recovery remains. Code review and local evidence do not qualify the old isolated staging deployment against the new controller. |
| Governance and deployment | Zero-delay caller checks, fixed sealed module bindings, local-only deployment/rehearsal scaffolding, production activation floor unchanged. No generic proxy upgrade or holder withdrawal was added. AUD18-01 remains. |
| Local unpublished drafts | Optional mint/claim preparation, quote pinning and process-tree cleanup examined separately. Their presence in the working tree does not qualify or publish them. |

The [narrow boundary scan](boundary-scan.json) found no matching credential pattern,
new literal 20-byte production recipient, or added non-comment `delegatecall`,
`selfdestruct` or `tx.origin` expression. These are limited checks, not a secret
scan certification or a substitute for following authority/data flows. Dynamic
governance-selected addresses still carry the trust described above.

## Evidence used without unnecessary reruns

The [source-binding comparison](source-binding-check.json) matched all **78**
recorded file hashes, including **39 production sources**, in the latest
[normal-build receipt](../immediate-governance/size-gates.json). Its 30 object
gates and latest governance evidence remain scoped to their recorded source.
Vault runtime is 24,557 bytes: only **19 bytes** below the runtime limit.
Constructor arguments require separate initcode allowance. This is a maintenance
and deployment constraint, not an identified exploit.

Reviewed existing [228 affected Solidity passes and internal Slither dispositions](../immediate-governance/VERIFICATION.md),
[canonical handoff evidence](../canonical-handoff/VERIFICATION.md),
[activation preparation](../activation-preparation/VERIFICATION.md),
[dynamic liquidity](../dynamic-liquidity/VERIFICATION.md) and
[range-policy evidence](../range-policy/VERIFICATION.md). Earlier full regressions
and pool forks retain their earlier source/configuration scope. Counts from
different snapshots are not summed into a new current-source regression.

Only the new availability reproduction was executed for this audit, plus hash,
documentation and Todo consistency checks. No unchanged broad Solidity/Python
suite, fork or static analyzer was rerun. Reproduce the availability observation
with [the supplied script](reproduce-availability.py) against an isolated archive
of the reviewed commit; the receipt binds all loaded repository Python modules.
Its clock/RPC are synthetic; no real wallet or network is used.

Production approval still requires qualified routes, tokens, fees, prices,
randomness, authority addresses, creator funding, wallet/backend/keeper operating
rehearsals and independent audit/remediation. Different-pair conversion and
future-chain canonical finality/transport remain incomplete. This review leaves
the [release decision](../../docs/RELEASE_CHECKLIST.md) **NOT APPROVED** and records
remaining work only in the [central Todo](../../TODO.md).
