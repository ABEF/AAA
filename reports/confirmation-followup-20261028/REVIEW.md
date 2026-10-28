# Confirmation follow-up review

Reviewed 2026-10-28 against published baseline
`ae56de6d3b4c57e0ffb60f0a54cd3d74084d0b31`. This is an independent follow-up to
the [previous implementation/audit](../practical-improvements-20261028/REVIEW.md),
not a replacement for its immutable receipts or an independent external audit.
**Production remains NOT APPROVED.**

## Findings and repairs

| Finding | Consequence and implemented repair | Source |
| --- | --- | --- |
| Foreign evidence after an acknowledged clear | After a healthy empty read, the old keeper dropped its clear acknowledgement when another record appeared, adopting observations it had not maintained. Any nonempty record while the acknowledgement remains now requires another reset; only the keeper's own atomic observe intent removes that acknowledgement. This closes a service-level evidence gap; the contract still enforces sampled readiness. | [Keeper](../../keeper/monitor.py), [regressions](../../tests_python/test_keeper_confirmation_followup.py) |
| Initial raw-read failures bypassed reset handling | Unreadable/malformed Vault group or pool/accounting input, or an initial global Access/clock failure, could leave an old window and jitter reusable after recovery. Relevant bucket faults now invalidate that bucket; initial global faults invalidate known fresh windows. Pending recovery runs first and never acquires these new dependencies. Unrelated share/job failures remain separate. | [Keeper](../../keeper/monitor.py), [failure-isolation cases](../../tests_python/test_keeper_confirmation_followup.py) |
| Physical position and condition were insufficiently cross-checked | A coherent opposite-side/raw-false report or a foreign pool's LP could pass inventory consistency. The observer now reads actual ticks and the pinned PosM PoolKey/packed PositionInfo; the gate binds the complete key hash, packed prefix/ticks and subscriber flag to the Vault pool. Exact integer recorded-centre range calculation independently checks manual range changes, raw eligibility and direction. This is read-admission hardening, not a discovered Manager write bypass. | [Observer](../../zzz_ops/production_observer_v4.py), [gate](../../zzz_ops/production_v4.py), [cases](../../tests_python/test_production_physical_confirmation.py) |
| Wallet totals accepted custody contradictions rejected by NFT detail | Profiles3/4 now read canonical nftStatus beside royalty eligibility. Unknown/unsupported statuses, parked/outbound available NAV, contradictory dormant values and invalid terminal state fail closed. Actual valuation outages keep LP unavailable while preserving independent funded ETH totals. This fixes inconsistent RPC-data acceptance, not contract-side reward allocation. | [Portfolio](../../frontend_api/portfolio.py), [cases](../../tests_python/test_wallet_custody_totals.py) |
| Cooldown/no-compound preflight and health did not prove every gate binding | Actual confirmation helper/Budget runtime, parents and capabilities are now validated independently of quality version, even without a candidate. Latest canonical policy-only observations are separate from confirmed quality observations. Pending intents skip the new dependency; failed reads retain old observations explicitly stale. | [Preflight](../../keeper/ops.py), [health](../../keeper/health.py), [cases](../../tests_python/test_keeper_confirmation_health.py) |
| Late metadata failure could refresh the last healthy time | A completed cycle followed by a failed metadata observation now preserves the previous healthy timestamp, increments failures and returns failure instead of reporting successful readiness. Independent cycle work is not cancelled retroactively. Only intentional stop/cadence warnings become informational after irreversible LP exit; bad bindings, malformed data or stale reads still fail. | [Writer](../../keeper/monitor.py), [real heartbeat-path cases](../../tests_python/test_keeper_confirmation_writer.py) |

The gate additionally asserts zero idle balances for Exited5 buckets. The earlier
end-to-end negative control already rejected a positive-idle terminal fixture
through its aggregate release check; this is explicit local consistency defense,
not a newly demonstrated release-admission bypass.

## Boundaries reviewed

- Lower ticks are inclusive and upper ticks exclusive, including legitimate
  downward boundary slot0 observations. Integer floor/ceil and negative-tick
  rounding match the installed Strategy implementation.
- Paused conditions retain raw eligibility and stored history, but do not invent
  manual readiness. Explicit range changes retain the hard cooldown. Compounding
  changes LP liquidity/NAV without changing its physical tick range or centre.
- Parked/outbound rewards remain claimable. Exited principal stays separate from
  rewards and current NAV. No zero substitutes for missing or inconsistent data.
- Pending receipt recovery, historical profiles and transaction journals stay
  intact. No new recipient, role, economic split, signing capability or Solidity
  ABI/storage change is introduced.

## Operating and documentation consequences

Recollect earlier schema6 observations: active rows now require physical ticks,
raw full PoolKey/PositionInfo, and range_pending when lifecycle permits the read.
Do not insert defaults or relabel schema5 data. The pinned PosM read adds one
call per active LP. Portfolio profile3 adds one custody read per NFT; profile4
strengthens its existing status read. Existing chunks and RPC budgets are
unchanged and actual latency must be qualified.

Deploy matching health writer/checker only under a separately authorized rollout.
Policy-only health proves an observed canonical policy, not continuous price
evidence or runtime attestation. gap0 is stopped; a nonzero gap below the selected
300-second service cadence is incompatible. Strict 300-second receipt gaps can
restart repeatedly with delay; this user-selected rule was not relaxed.

The [operator manual](../../docs/OPERATOR_MANUAL.md), service/recovery/safeguard
guides, preflight instructions, feature/evidence reference, roadmap, release
record, repository context and [sole Todo](../../TODO.md) are synchronized.
Superseded external-custody requirements in current Todo acceptance text are
replaced with holder-return semantics. Historical reports retain original bytes.

## Remaining risks

No new on-chain accounting defect was confirmed in this follow-up; that does not
prove absence of undiscovered defects. Coherent malicious RPC answers remain a
trust risk despite consistency checks. Sampled observations miss movements
between checks; neither the buffer nor routing guards eliminate economic MEV or
keeper personal trading. Actual feeds/routes, authorities, VRF/OpenSea, current
website/services, complete-operation gas, Linux/host recovery and independent
audit/remediation remain open. No service, website, Anvil, journal, public
transaction, deployment, signer policy or paused heartbeat was changed.

See [verification and exact scopes](VERIFICATION.md).
