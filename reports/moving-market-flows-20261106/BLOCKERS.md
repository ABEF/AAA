# Blockers, diagnosis and operator recovery

The goal is to remove accidental failures, not to let every trade execute at
arbitrary loss. Always resolve a known pending transaction before preparing
another. Never automatically translate a blocked ordinary action into force.

| Observed condition | Meaning / impacted flow | Correct response |
| --- | --- | --- |
| Old main outside its band | Normal reason A may need replacement; not a prohibition on A | Let current readiness/independent reference and new active-range execution decide. Do not require old main to remain active for replacement |
| Preserved main outside before B | Cannot keep immutable bounds AND promise active LP at that spot | Wait, or explicitly review full replacement; C can deliberately add inactive one-sided LP. Do not misreport it as active recovery |
| Selected swap would push preserved main outside | Avoidable B route selection failure | New active-aware search considers only physically qualifying candidates. If none fits financial/caller limits, do not trade |
| New normal range outside after rounded geometry/our swap | A cannot promise active placement | Current router and pre/post mint physical checks reject atomically. Review range/deviation/source freshness or a different admitted route |
| Narrow range versus delayed reference | Price agreement may pass while placement is impossible | Review width, conservative rounding and feed/deviation qualification. Do not equate USD retention with active LP |
| 12-hour minimum / sampled window / strict max gap / jitter | Distinct timing controls for ordinary automation | Wait/observe/reset with provenance; configure approved policy explicitly. Manual governance recovery is a separately reviewed action |
| Pending deliberate mode/width | A's geometry exception is due after cooldown; B preserves main geometry | A applies current policy in a new portfolio. B can stop residual while leaving independent width pending. No false acknowledgment |
| Mode already OFF / residual still present | Desired versus actual state differ | B supports it without duplicate same-value setter. Raw close alone leaves attributed idle; unpause does not reinvest it |
| Healthy main plus large attributed idle | Idle is holder-owned backing, not sweepable dust | Use eligible compound, B or an explicitly reviewed replacement. B excludes designated compound; ordinary compound/A may release it |
| Idle-only worker disabled or main not eligible for compound | Service policy can deliberately defer funds | Review scheduling/configuration or use governance management. Do not spend entrant funds to deploy incumbent idle |
| Contribution blocked by existing idle ceiling | Separate whole-account idle policy, not necessarily a bad entrant quote | Reinvest/recover through the proper existing operation. Do not count incumbent principal as marginal new LP |
| Loss/output/additional-loss/main-floor/idle/caller L fails | Different financial quantities/rounding, not redundant switches | Read the exact limit and current units; review better execution or explicitly govern future bounded settings. Never auto-lower caller minima |
| Known fee exceeds a conversion budget | Real economic incompatibility | Qualify cheaper admitted route or explicitly change bounded policy. Original-currency royalties do not need conversion |
| No active/affordable route | Bounded solver or real depth/fee limitation | Re-simulate changed valid input/route; admit a reviewed compatible route through governance. No fabricated zero quote/unbounded search |
| Failed/disabled route but another is healthy | Optional route must not freeze all candidates | Existing bounded per-candidate isolation remains. Target operations disabled still blocks ordinary work by design |
| Stale/faulted/disagreeing feeds or sequencer | No trustworthy ordinary valuation/reference | Restore/qualify data. Healthy raw funded claims and specifically reviewed raw custody recovery retain their separate paths |
| Wrong chain/runtime/helper/profile/custody | Unsafe mixed or stale deployment/configuration | Stop and authenticate exact graph. Source publication is not upgrade, service adoption or journal migration |
| Stale manual custody hash / nonce / epoch / L / shares | Real operation identity changed | Confirm pause, take one canonical snapshot, simulate and review again. Never replace hash with arbitrary nonzero text |
| Expired/future-invalid deadline or late UTC budget change | Operation review is no longer valid | New late check defers before intent/signing. Prepare a fresh operation on a later eligible cycle; no automatic extension |
| Late simulation reverts or return is not exact void0x | Operation/gas/provider evidence is unavailable or contradictory | No new pending/spend/sign. Inspect sanitized reason/provider; do not claim an exact inequality from an opaque RPC revert |
| Nonce moved / funding insufficient | External signing or depleted gas wallet | Reconcile actual nonce/receipt/spend and fund the correct limited keeper wallet. Never copy governance credentials onto its host |
| Pause / permission / preparation / canonical / terminal transition | Independent authority/lifecycle restrictions | Use the specific reverse/cancel/drain procedure. Global unpause cannot reopen terminal principal or erase canonical locks |
| Confirmed revert | Old portfolio/accounting restored by atomic rollback; gas was spent | Recover receipt, charge actual fees, honor configured per-action retry and confirmation reset. Independent healthy jobs remain separate |
| Hashless/unknown submission / receipt reorg | May already have broadcast | Recover same intent/hash/nonce and canonical state. Never delete journal or blindly resend |
| Fees/claims/transfers while paused | Separate rights, not management authority | Current owner may claim healthy funded rewards; external fees continue accruing. LP manager actions still use their own roles/lifecycle |
| Failed raw token/core or lost chain | Not repairable by changing a slippage setting | Follow explicit parking/terminal and incident procedures where dependencies work. No code can promise transfer of a permanently broken token |
| Post-confirmation price immediately exits | For A/B, success proved activity at execution, not perpetual future activity; forced C/D can succeed inactive | Ordinary monitoring/maintenance resumes after explicit unpause; review chosen ranges/cooldown. Do not label later market movement a partial transaction |

## Recovery states remain distinct

- Active one/two positions: normal shares/rewards continue; actual residual fill
  never deactivates or duplicates its accounting.
- Raw residual close: main stays; proceeds remain attributed idle. B reinvests
  them without a residual ID; it is not a sweep or holder payout.
- Parked: both legs closed into Vault; explicit validated resume redeploys and
  destination mode determines whether one or two positions may open.
- Terminal collective exit: no reopening, activation/growth or rebalance. Bounded
  governance principal allocation/distribution and owner reward/fallback claims
  remain their separately authorized operations.
- Canonical preparation/import/retirement: permitted drains and verified
  restoration/cancellation are not ordinary keeper shortcuts.

Reviewing force does not remove fixed native ETH/ZZZ identity, exact custody,
classification, recipients, positive caller floor, deadline or lifecycle. It
may waive financial protections and lose nearly all principal. Both the operator
procedure and actual dependency/provider/host rehearsals remain required.
