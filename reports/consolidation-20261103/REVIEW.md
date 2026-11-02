# Three-audit reconciliation and shared-client consolidation

Reviewed3November2026, Europe/Paris. Base main `cf4e161b04c52325022e8fead7e3ca417fd8cc86`.
Internal source review and focused fixes; production remains NOT APPROVED.
[Verification](VERIFICATION.md) distinguishes executed checks from unchanged
contract evidence. Earlier reports retain their bytes and original scopes.

## Last three reports reconciled

| Report | What remains implemented | What remains open |
| --- | --- | --- |
| [Action resilience](../action-resilience-audit-20261102/REVIEW.md) | RPC body progress limits, strict maintenance fields, saved-intent recovery before new jobs, action/output and fault distinctions. This consolidation retains those safeguards. | Body progress is not hard DNS/header/socket preemption. Actual provider/watchdog/Unix and source6 operating acceptance, long-lived history and independent audit remain open. |
| [Multi-day portfolio](../portfolio-long-horizon-20261102/REVIEW.md) | Main-only entrant deployment, aggregate share accounting, bounded two-leg lifecycle and both serialized user/keeper orderings. Its stronger fixture minimum was valid rejection, not a production bug. | Four virtual-time journeys do not qualify live economics, gas, concurrent signed browser traffic, service jitter or sustained recovery. Effective pool/action minima still need actual integration qualification. |
| [LP lifecycle](../lp-lifecycle-audit-20261102/REVIEW.md) | Ordinary active-main candidate filtering, exact stored-tick quotes, preserved final checks and both-leg reward accounting. Harvest geometry coherence is explicitly not independent source evidence. | Bounded quote search does not prove a global optimum or residual feasibility at all inventories/depth. Real venues/feeds, placement gas and independent review remain required; no unsafe fallback. |

The52 production Solidity sources and31 normal-build dependencies are unchanged.
Prior43 normal gates and475-record internal static review remain applicable only
at their exact pins. No recompilation or repeat of unchanged Solidity suites is
presented as a new audit. The three reports are complementary, not three complete
independent approvals.

## Implemented improvements

| Finding / change class | Correction and consequence |
| --- | --- |
| Mutable RPC configuration alias; input-isolation fix | `Rpc` now snapshots and validates an immutable endpoint tuple. Editing/clearing/extending the caller's configuration list can no longer redirect a running client, empty its failover set or enlarge its bounded attempts. This is protection against mutable local configuration, not proof that a reviewed endpoint is honest. |
| Contract-read shortcut bypassed wrapper budgets; interface hardening | `BudgetedRPC.eth_call` now builds the standard exact call and uses the wrapper's metered `call`. Call exhaustion/expiry is enforced before transport and expired results are discarded afterward, including injected transports. Sender and canonical block selectors are preserved. Current principal consumers already use `call` or their own pinned adapter; no reproduced holder accounting corruption is asserted. |
| Maintenance validation carried a misleading permissive switch; behavior-preserving consolidation | Remove `allow_retired` from both private validators. They are always strict. The constructor explicitly defers only new maintenance-value validation when an existing validated intent requires recovery. `cycle` and `submit` keep strict checks before new work. Legacy pending receipt recovery remains supported; no retired bridge scheduling is restored. |
| Impossible override identifiers accepted; input-domain fix | Bucket override keys must be canonical positive uint256 IDs, matching chain/state readers. Oversized IDs now fail at startup rather than silently targeting no possible bucket. The maximum valid uint256 remains accepted; this is not a claim that a bucket with that ID exists. |

The supported maintenance fields have one immutable definition. Historical empty
`reward_routes` compatibility and saved receipt handling remain; nonempty retired
routes still cannot schedule work. There is no new stop toggle, route, signer,
retry/adoption, permissive exception or journal migration.

## Safety and operating consequences

The maintained guides are synchronized. One stale current-custody qualification
line in the Todo now correctly names accounting6/custody4; historical reports
and task statuses/order remain unchanged.

- A running RPC client uses the reviewed endpoint snapshot from construction.
  Review config and restart through the existing controlled recovery procedure
  to apply new endpoints; editing the old list is not live rotation.
- Missing prices/API data remain unavailable, never fabricated zero. The budget
  wrapper is cooperative: it cannot interrupt a blocking injected method, DNS or
  header read. API process supervision and keeper host watchdog remain separate.
- Invalid new scheduling values cannot authorize work. Existing transaction
  sender/chain/deployment/calldata/nonce/receipt/spend checks remain; structural,
  signer or other job configuration can still require restoration before recovery.
- No economic rights, ETH/fixed-ZZZ identity,80/10/5/5 allocation, rarity royalties,
  contribution/routing/loss settings, range geometry, hard12-hour interval,
  confirmation/jitter or terminal holder-return policy changed.
- High volatility can still leave LP inactive during the chosen cooldown, and
  faults can restart samples. Retain atomic rollback and explicit blockers; do
  not automate the paused emergency path or relax guards as an implicit fallback.

Real dependency/economic/host qualification, authenticated lifetime-history
scaling, source6 website rollout and independent audit/remediation remain in the
[sole Todo](../../TODO.md). This source publication changes no running service,
site, Anvil, LP, balance, journal, signing profile or user-paused heartbeat.
