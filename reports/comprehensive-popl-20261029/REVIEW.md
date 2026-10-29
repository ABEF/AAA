# Complete-project audit and improvement pass

Source baseline: contract `main` at `93ceee1b78ad1e8532932961b934177b558f13c3`;
website `main` at `997f8c3524ea75d613dbb752f67b33a69fe7992f`. Reviewed2026-10-29.
This is an internal, source-scoped audit and implemented improvement campaign.
**Production remains NOT APPROVED.** It is not a promise that every possible
failure was executed or that no vulnerability exists.

## Understanding and revised scope

PoPL is a1,000-entry ERC721 collection with shared physical ETH/fixed-ZZZ LP and
independent per-NFT shares. Activation creates permanent eligibility, while
current marked LP selects artwork. Actual harvested fees fund80/10/5/5:
individual shares, equal activated collective, compound and fixed-ZZZ burn.
Actual marketplace royalties form a separate rarity1/2/3 ledger. Current owners
inherit unclaimed rights; reserves, income, claims and returned principal differ.

Ordinary upkeep, independent harvest, compounding and conversion have distinct
clocks, permissions and financial guards. Governance can move/park same-pair LP,
perform an explicitly risky paused emergency, replace the whole collection before
exit, or end LP irreversibly and return actual principal to current holders.
Services observe/prepare/operate; they cannot replace on-chain authorization.
Public signing remains disabled. Popldemo is a simulation; served poplint is
current3 read/unsigned integration, not fresh accounting4 qualification.

The [canonical final prompt](../../docs/THIRD_PASS_AUDIT_PROMPT.md) was revised
after the two supplied methodology/checklist files, both READMEs, current code,
runbooks, the historical disposition ledger and primary technical references were
examined. Two sequential challenges are preserved in [prompt review](PROMPT_REVIEW.md).
Material adaptations:

- Replace resolved494-body/122-output gaps and historical baseline assumptions
  with actual inventory refresh and precisely scoped reuse.
- Audit complete journeys and interactions, including normal-operation liveness,
  interrupted accounting, terminal/canonical states and operator mistakes.
- Include evidence producers, lifetime data growth, operating funding and loss
  of keys/providers/venues; exclude nonexistent bridges, AI services, password
  accounts or mandatory committees.
- Implement reproducible defects; preserve economic rights and require an
  explicit decision for consequential behavior changes. A test fixture or local
  hash is not provider, runtime, browser or deployment qualification.

[Coverage](COVERAGE.md) distinguishes fresh source traces, unchanged body evidence,
targeted execution, source-only conclusions and external release limits.

## Implemented changes

| ID | Confirmed problem | Correction and actual verification |
| --- | --- | --- |
| C-P2-01 | After collective exit, disabling the last admitted buyback venue made the remaining ETH buyback reserve impossible to route: full pool configuration was permanently principal-locked. | User approved validated swap-venue recovery. After terminal exit begins, governance may call `configureNative` only at Migration `Ready(3)` with deposits disabled. Fixed ETH/ZZZ, native/runtime, prices, assets and parameter validation remain.16 focused Solidity methods pass; fresh39 production gates and ABI/storage comparison pass. |
| K-P2-01 | A pool-occupancy RPC fault, contradictory occupancy or invalid active/parked physical identity could leave the affected old confirmation window/jitter usable after recovery. | Relevant identity faults now durably require reset only for that bucket. Pending recovery, clear acknowledgements, unrelated share-read failure and independent harvest remain distinct.11 reset methods are included in the final18-method keeper scope. |
| K-P2-02 | Telemetry could label an old anchor confirmed after the latest head retreated below required depth during the read. | Final head/depth/chronology, same-height identity, canonical anchor and freshness are checked before publishing confirmed quality evidence. Failure retains old evidence as unavailable and cannot advance healthy time. Seven telemetry methods complete the18-method keeper scope. |
| B-P2-01 | Restored/older SQLite history could contain invalid or regressing timestamps in eventless or filtered blocks while appearing complete. | The existing ancestry query now validates the entire stored prefix's timestamp consistency before replay; the confirmed target timestamp is an exact bounded integer. Equal L2 timestamps remain valid. Four new plus seven affected methods pass, with real temporary SQLite and no extra RPC/query/schema. |
| T-P2-01 | Static analysis deleted/truncated old outputs; ambiguous review/report JSON could pass CLI parsing, and analyzer-log capture failures were ignored. | Every run reserves a new directory before tools, retains version/report/log/review output, checks both pipeline statuses and propagates review failure. Strict object parsing rejects duplicate/nonfinite inputs; malformed identities and diagnostics do not echo arbitrary input. CI uploads the new output directories.15 distinct methods verified across the recorded final scopes. |
| T-P2-02 | Keeper/source-check runners overwrote outputs after work; full Python runner reserved only after execution, leaving an admission race. | Shared exclusive JSON/log admission precedes imports/tests/scans. Durable nonpass markers and owned handles preserve incomplete evidence. Source checks default to unique outputs; both new keeper suites enter dedicated selection.Source hashes now precede imports and include lazy script helpers.35 focused methods (33pass/two Windows skips), followed by eight targeted provenance checks with five overlaps, give38distinct methods across stages; this is not one fresh38-method run. |
| D-P2-01 | Several current operator/callable descriptions still offered a removed generic `configure` pool function. | Current procedures use actual `configureNative`, explain post-exit reserve recovery, controlled worker cutover, chronology failures and new artifact paths. Callable reference is regenerated from the fresh compiler artifacts; all696functions/33constructors/13receivers retain explained inputs/outputs. |

The failure sequences and precise source/evidence identities are in the domain
ledgers and [verification record](VERIFICATION.md). Earlier partial/failed attempts
remain visible and are not counted as additional coverage.

## Post-exit change: exact authority and effect

`Ready` means all LP buckets are closed and principal has been allocated. Owner
payout batches may still be pending. The principal remains separately backed in
Migration; the separate FeeController buyback reserve can use a validated venue.

Governance configures a full native pool with `depositsEnabled=false`; Closing,
Allocating, unknown/malformed phase and deposits-enabled terminal configurations
reject. Existing preparation/canonical/governance checks and final rechecks remain.
Admission does not trade, spend reserves, redirect payouts, restart LP or reverse
`lpExitStarted`. Actual buyback still requires the limited keeper, ordinary
unpause, approved parameters, prices, execution quality and actual ZZZ burn.

The production native-binding validation body is unchanged. Its visibility is
now internal/virtual solely to let an explicit synthetic test subclass exercise
the inherited configuration path. It adds no external selector or configurable
bypass; the concrete production contract still rejects unpinned dependencies.
Synthetic successful admission does not qualify Robinhood runtimes or market
depth. The whole fixture limitation is recorded, rather than presented as a live
venue test.

Fresh compilation changes only Registry's bytecode: runtime10448→10718 and
creation42092→42362. All39 compiled objects retain semantic ABI and recursively
resolved storage layout. The other38 bytecode objects remain identical. Manager
initcode still has37bytes of margin; Vault runtime59bytes. Exact constructor
arguments and target-chain gas remain release requirements.

## Preserved financial invariants

1. **Entrant isolation:** activation/growth checkpoint incumbents, spend only the
   entrant's exact funds, verify actual marginal LP and issue shares from net
   added NAV. Contributions do not recenter or reset the rebalance clock.
2. **Funded allocation:** actual harvest funds fixed80/10/5/5; owner/member indices,
   fractions and boundary dust retain their defined attribution. Claiming does
   not reallocate gross fees or trigger compounding/buyback.
3. **Ownership and entitlement:** current ERC721 ownership controls unclaimed
   LP/royalty rights. Conversions preserve the earning NFTs' entitlements and are
   not new income. Dormant NFTs do not dilute activated collective membership.
4. **Custody separation:** principal/idle/compound, holder liabilities, buyback,
   royalty cohorts and quarantine remain separate. Normal holder redemption is
   unavailable; terminal return and pre-exit replacement retain their distinct
   irreversible boundaries.
5. **Authorization and execution:** fresh/captured prices and policy, exact deltas,
   typed venues, callback settlement, current keeper/governance and lifecycle
   controls remain. No default loss budget, timing policy, allocation or public
   signing permission changed. Governance-only emergency financial bypass remains
   an explicitly accepted potentially near-total-loss trust risk.

These are source/traced invariants with scoped verification, not a fresh
execution of every historical invariant campaign or a compiler-correctness proof.

## Decisions challenged and work that remains

- **Perpetual rights versus perpetual operation:** chain custody does not fund
  keeper gas, randomness, RPC/archive access, hosting or permanent art retrieval.
  Long operator/provider outages, token freezes, unusable venues or lost keys can
  stop progress. No protocol can promise recovery from every chain/token failure;
  current post-halt and post-exit canonical relocation remain unsupported.
- **Lifetime data growth:** complete raw block/event/lineage replay and the
  bounded event limit eventually need a reviewed archival/checkpoint/read-model
  evolution and measured latency. Removing limits or trusting an unauthenticated
  cache would weaken integrity. Current contracts/claims and history-service
  availability are separate concerns; no speculative checkpoint engine was added.
- **Testnet scope:** production Registry pins chain4663 and mainnet dependency
  runtimes. A byte-identical full native venue rehearsal cannot simply target
  another chain. Preserve the three testing layers, but explicitly identify a
  separately reviewed test-only/testnet profile and which behavior it can qualify;
  use actual mainnet-fork evidence for the real venue. Never weaken production
  pins or relabel mocks to make a testnet gate pass.
- **Pricing and execution feasibility:** two qualified independent feeds, actual
  venue depth and cheaper ZZZ conversion routes remain necessary. Source
  disagreement consumes execution margin; a valid configuration may still have
  no executable quote. Do not widen budgets automatically.
- **Market/governance exposure:** sampled confirmation, jitter, bounded routes,
  fee-adjusted/gross floors and cooldowns constrain risk, not guaranteed attacker
  unprofitability. Repeated bounded losses, public ordering, common-mode oracles
  and explicitly trusted governance still need economic/security qualification.
- **Compiler and static review:** pinned0.8.26 advisory applicability has specific
  source/settings exclusions and fresh structured IR graphs with no mutual-recursion
  witness for two named advisories. Independent graph QA corroborates the scoped
  result; later backend/compiler correctness remains unproven. No compiler
  safety PASS or silent upgrade is claimed. Refreshed source-bound Slither triage
  is still required; repairing its runner does not approve old analysis.
- **Actual release services:** feeds/routes/VRF, authority addresses, compatible
  OpenSea primary mint, fresh4 website/service/wallet acceptance, metadata
  publication, target gas, operating/recovery rehearsals and independent audit
  with remediation remain open in the sole Todo.

The user-approved post-exit question was implemented. Remaining provider/product
decisions are recorded with concrete acceptance criteria; no default address,
funding arrangement or operating qualification was invented.

## Preservation and rollout

Existing report bytes and original failures/skips remain unchanged; only the
reports navigation index points here. The four original dirty files and old
local-only drafts are excluded from publication. No installed service, Anvil
deployment/NFT/LP/balance, journal, shared browser signer, website source/build/
server, public transaction, deployment, sealing or paused heartbeat changed.

Runbook/source publication does not install the fixes. Review matching source and
configuration, preserve pending work, and use the existing controlled rollout
procedures when separately authorized. [Verification](VERIFICATION.md),
[coverage](COVERAGE.md) and the [sole Todo](../../TODO.md) retain the remaining gates.
