# Confirmation and operational improvements

Reviewed2026-10-28, starting at `cd10e35599b00d79b00c46553e96cdb0b3248cfb`.
Internal scoped review; **production NOT APPROVED**. [Verification](VERIFICATION.md)
owns exact runs/pins, failures and reuse. Historical reports retain their bytes.

## Decisions and scope

The concrete-improvement request was adapted to the actual accounting4/native
release. Implement current preflight rather than relabel accounting3; export
truthful diagnostics rather than invent service attestation; retain fresh signing
checks rather than cache authorization; remove unreachable non-native LP branches
rather than change custody; verify affected behavior rather than repeat all suites.
No mock can qualify real RPCs, independent feeds, VRF or OpenSea.

The user selected recorded on-chain samples, a15-minute window, five-minute
eligible checks and **exactly300seconds maximum confirmed-observation gap**.
Greater gaps restart, without grace. With a300-second cadence, receipt/RPC delays
can repeatedly restart the window. This was explained and is deliberately kept
strict. Actual operating timing/cost remains a release gate. No passive second
position,40% trigger or uninterrupted-history proof was selected.

## Material changes

| Finding | Implemented correction | Remaining boundary |
| --- | --- | --- |
| Raw eligibility plus jitter did not establish sustained evidence. | Strategy creates a fixed confirmation helper; Budget requires buffered readiness. Side/LP/config/source-policy identity, duration and gap are checked. | Sampled observations can miss moves/faults/pause cycles entirely between them. |
| Reverting after a fault reset would restore old evidence. | `observe` catches an observed read failure and clears in a successful transaction. Clear-only keeper reset works during ordinary pause; worker clears its durable reset requirement only on a canonical successful receipt. | A failed/OOG transaction or off-chain error cannot clear chain state by itself. Startup/recovery/fault resets need gas and confirmed transactions. |
| An approved policy could change during the complete close/swap/deploy sequence. | Budget captures Registry monotonic revision, active ETH/ZZZ/sequencer policy identities, quality revision and confirmation revision before maintenance; compares after the whole operation. Physical/ordinary feed-round changes are excluded from this stable control fingerprint. | Trusted governance/dependency behavior and actual price-source independence still require qualification. |
| A helper-only keeper check could accept a Budget lacking the execution gate. | Fresh confirmation profile pins actual Vault Budget runtime, access/vault bindings and capability1 as well as Strategy/helper. | Immutable old deployments keep their historical profiles. |
| Receipt latency could skip one entire renewal cycle. | Every due ordinary outside check requests an observation, even if the previous receipt is only298seconds old. No earlier cadence or hidden gap allowance. | Actual receipt gaps above300seconds still restart. Nonzero configured gaps shorter than the fixed worker cadence are refused without paid looping. |
| Buffer invalidation accidentally blocked post-exit range orientation. | Restore only the Strategy-authenticated revision invalidation after exit; governance orientation remains available for buyback context. | Observation/configuration/reset stay principal-locked; no LP reopening. |
| A reset during an authorized callback could invalidate evidence after entry but still complete maintenance. | Budget hashes the existing raw observation tuple with stable controls and compares at completion; actual-v4 positive-control/rollback verification is scoped separately. | A reverted transaction cannot persist its attempted reset. Worker/manual recovery must explicitly invalidate after a known failure. |
| Broad maintenance catches reset healthy evidence after unrelated outages. | Narrow resets to confirmation/raw-condition and relevant receipt failures; unrelated compound/router/health failures no longer discard the window. | Source readiness and freshness remain mandatory; outages still delay operations. |
| Persistent faults could cause repeated paid clear transactions. | Canonical reset acknowledgement suppresses duplicate clears while waiting for healthy reads; fresh nonempty foreign evidence forces a new reset and observe intent invalidates the acknowledgement atomically. | No cached readiness, receipt bypass or automatic budget increase. |
| New windows could reuse old off-chain jitter. | Bind jitter to ordinary condition identity and firstSeen, not lastSeen; clear old schedule atomically when invalidating evidence. | Software-only jitter remains bypassable by an authorized key. |
| A600-second outer loop could be accepted for strict300-second samples. | Fresh confirmation profile requires an explicit compatible main interval; historical defaults stay historical. | Actual work/receipt latency still requires qualification; no hidden grace. |
| Inventory/readers could accept contradictory conditions. | Reject impossible lifecycle/raw candidates, cross-check Strategy readiness/manual exception and require canonical ABI word shapes. | Consistent fabricated RPC results still require independent provider qualification. |
| Old production inventory could not reconcile terminal holder exit. | Explicit schema6 observer/gate checks accounting4/custody3/V5,17helpers, complete bounded NFT/bucket shares, cumulative-floor principal allocations, paid/remaining/backing and lifecycle/cursors. | Synthetic consistency is not actual-provider or deployment approval. Missing real bindings/reviews and unsupported OpenSea mint remain blocked. |
| Keeper quality checks were absent from public health. | Healthschema2 records confirmed block/config/runtime/policy, separates last success/current failure, and adds sanitized estimate/padded-gas/refusal diagnostics. Matching new success statuses fail closed under an old checker. | Local file hashes are not running-code attestation. Writer/checker rollout and external monitoring remain unqualified. |
| Discovery repeated immutable-block reads. | Cache only within the same canonical hash/config/cycle; fresh pre-simulation/pre-signing validation bypasses it. Pending recovery does not acquire new-policy dependency. | No stale-head, persistent or authorization fallback. |
| Manager initcode had54bytes of margin and retained unreachable generic-pair paths. | Remove generic ERC20-pair mint/collect/close branches; reject non-native pair before pulls. Preserve ETH/ZZZ exact deltas, native refund checks, approvals and both swap directions. | Only fresh release source changes. Old immutable deployments are preserved; production is already native ETH/fixedZZZ-only. |
| Parking/profile/timing/operator guides described superseded behavior. | Replace obsolete instructions; update sole ledger, callable reference, feature/roadmap/release/context and actual controls. | Historical reports and deployments retain original scope; publication changes no service or funds. |

## Timer semantics and rights

- `needsRebalance` stays raw cooldown/outside or deliberate operator-width
  eligibility. `rebalanceReady` additionally checks confirmation. Governance's
  explicit width change keeps its existing exception after hard cooldown.
- Constructor duration900/gap0 is stopped ordinary confirmation. Intended reviewed
  configuration is900/300/nonzero review hash; placeholders are not approval.
- Inside/opposite side, changed physical LP/control policy or stale gaps restart.
  Healthy price rounds, contributions and NAV balances do not restart by themselves.
- Worker jitter begins after readiness and continues samples while waiting.
  Reset and observation transactions use existing authority, simulation, budgets,
  nonce/journal/receipt recovery. No direct public signing path is added.
- Compound yields to raw eligible rebalance while confirmation is pending.
  Hourly fee collection, funded claims and receipt recovery stay independent.
- The helper cannot receive custody, approve tokens, choose a recipient or move
  LP. Clearing observations is only availability authority; the keeper could
  already refuse to run. Public sample timestamps can advertise upcoming upkeep.
- No80/10/5/5, royalty weight, owner entitlement, principal guarantee, exit
  recipient or supported contribution currency changes.

## Review limits and next gates

Actual900/300 timing/gas, maximal full-operation catalogs/depth, independently
reviewed sources/routes, providers, VRF, authority wallets, OpenSea-compatible
primary mint, metadata hosting, Linux operations and independent audit/remediation
remain open. Per-operation loss bounds and samples are not guarantees against
profitable surrounding trades, correlated prices or governance compromise.

The blocked keeper example retains its2.5Mgas cap; diagnostics never raise it.
The current site/Anvil/service/journal/signing configuration is unchanged.
[Operator procedure](../../docs/OPERATOR_MANUAL.md#configure-rebalance-confirmation)
and [sole Todo](../../TODO.md) own operation and remaining work.
