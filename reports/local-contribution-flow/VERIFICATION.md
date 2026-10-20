# Local contributions and read-clock verification - 2026-10-20

Scope: local browser UI, disposable launcher/fixture, and production unsigned
approval preparation. No production Solidity changed; reused source-bound core
artifacts were authenticated by the launcher. Only the new native admission
fixture was compiled with Solidity 0.8.26 and the existing optimizer settings.

## Checks and observations

- 51 focused Python cases passed, then 18 supplemental cases passed after adding
  the reset-only/false-return case and final state capability response. These
  overlap: 52 distinct cases, not 69 independent tests. Includes monotonic expiry,
  chain resampling, fixed local $100 activation, decimal-aware exact approvals,
  atomic ETH, rejected legacy wrap flow and normal unsigned activation guards.
- 51 affected Node checks pass; JS syntax and website selector/artwork check pass.
- Browser: read-only activation amount is 100 local tokens, visibly $100 at the
  $1 mock price. Native ETH activation submitted one successful Entry transaction;
  PoPL #1 changed Dormant to Activated with $100 displayed attached LP.
- Browser: five USDC approval was followed automatically by the distinct Add
  attached LP review. Both confirmations stayed explicit. No third transaction,
  zero-reset or wrap occurred. Final displayed LP is $105.00; raw marked value
  is 104999999999999999999 due to one unit of share rounding. An initial probe
  expected >=105e18 and failed; inspection established this one-unit difference,
  which is retained here rather than treating display rounding as raw equality.
- [Sanitized local receipts and snapshot](local-observation.json) include other
  concurrent user rehearsal actions; they are not all assistant test actions.
- Existing 8896 fixture: all eight LP values available; full read 5.875 seconds.
  A single-NFT profiling comparison reduced clock reads from 1573 to four and
  elapsed time from 8.188 to 2.594 seconds. This is local observation, not SLA.
- Existing Anvil/NFTs/LP were preserved through web-only restarts. Separate
  native fixture on 8898, chain 31337. No public keys/funds or paused monitor used.

## Safety and limitations

Direct exact approval must simulate successfully (including ERC20 return value);
reset-only tokens fail closed instead of requiring a third send. Entry is an
owner-authenticated spender. Already sufficient allowance is reused, not revoked.
Approval itself does not deploy LP; each final Entry call is simulated again.
Lost responses recover the same operation ID; submissions are not auto-retried.

LocalNativeRegistry substitutes production native venue admission and is restricted
at construction to chain 31337. The mock venue/feed/VRF are not Uniswap/Pons or
live price qualification. Production registry pins remain unchanged. Normal
launcher restart creates a new chain; the external one-session recovery scripts
are not a general production recovery facility. Snapshot freshness still samples
actual chain time before and after reads; work deadlines advance monotonically.

Fixed $100 is enforced by the local UI/API; production Entry retains its $100
minimum. Live fixed-value quoting/rounding policy remains an open release task.
No public website/server deployment. Independent audit, production wallet signing,
live routes/feeds and operating qualification remain open. Release NOT APPROVED.
