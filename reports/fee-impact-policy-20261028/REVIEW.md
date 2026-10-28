# Fee-adjusted execution quality: implementation and internal review

Fresh undeployed source,28October2026. **Production NOT APPROVED.**
[Verification](VERIFICATION.md) records exact checks, failures and remaining gates.

## Authorized scope

The user requested separating known trading fees from additional execution loss,
chose1% additional loss, and authorized publication. Preserve stronger existing
gross venue, contribution/maintenance, converter and caller safeguards. The later
40% displacement trigger, passive inventory and one-sided second position are
discussion only and are not implemented. No service, Anvil, journal, website,
signing, custody, NFT-rights, allocation or maintenance-eligibility policy changes.

## Material implementation

| Finding | Correction and limit |
| --- | --- |
| A single gross output floor could not express a separate cap after known fees. | Strategy-owned `additionalLossBps`, default100bps, governance0-1000 with nonzero review hash, monotonic quality revision and previous/new event. Actual directional v4 protocol/LP composition and raw fee-net input feed a conservative independent USD quote; the extra floor rounds up. Existing gross floor and positive caller floor remain stronger when applicable. |
| LP route search and direct Manager/buyback swaps must obey the same floor. | Balancer captures the cap with its existing price vector; Strategy exposes the direct calculation. Zero/one selected actual swap and exact settlement checks remain. Separate LP/royalty converter executors retain their own all-in policy and are outside this new capability. |
| A token callback could change or change-and-restore policy. | Monotonic quality revision joins existing Registry/source/target fingerprints. Direct Manager swap captures complete context before input pull and checks it after output/native settlement; balancing retains its end-to-end context checks. |
| A weak positive caller minimum could cause unnecessary rejection even if the stronger protocol floor is met. | Manager raises that positive minimum to the stronger protocol floor; zero still rejects. Stronger caller minima are retained. This changes acceptance behavior without weakening actual monetary floors. |
| A new getter cannot silently be assumed on old deployments. | Explicit `execution_quality_version:1` and Strategy/Manager/helper capability/runtime/Access-owner/cap/MAX/revision observations at one pinned block. Historical absent/0 reads and journals retain their old ABI/profile. Metadata does not pretend an unsigned review freezes governance policy until inclusion. |
| Initial helper-only code exceeded Manager constructor size because Manager creates the helper. | Move the public policy/quote into the existing fixed Strategy; retain captured pure route math in Balancer. Normal compiler/gates remain unchanged. Failed initcode and intermediate stack attempts are preserved, not approved. |

## Review conclusions and intentional boundaries

Four production files changed: Strategy, LPBalancer, LiquidityManager and the
shared interface. A separate read-only review found no additional actionable
monetary bug in this scoped diff. That is not independent audit or a security
guarantee. Installed v4 fee composition is checked directionally; both packed
protocol halves are bounded and static LP fee must match the admitted key.

The1% extra measure is oracle-relative, including spread, source uncertainty,
rounding and price impact. It is not isolated AMM impact. Known fees still consume
gross and total budgets:1.101% fee followed by1% extra permits about2.08999% total
before raw rounding, so an existing2% gross floor remains stricter.
No automatic widening, price fallback or profitability/anti-MEV claim is added.

New Strategy state precedes old mappings, shifting storage offsets. It is a fresh
undeployed layout; never relabel or upgrade preserved deployment/storage profiles.
Direct Manager swaps now require a constructible complete Strategy target context;
extreme TickMath ranges can fail closed even where spot-only swapping once passed,
and context reads cost gas. Review real target settings rather than bypassing them.

Manager runtime is24148bytes, but creation48938+160static arguments leaves only
54bytes of initcode headroom. Vault512/NFT176runtime headroom remains tight.
Future code or constructor changes require fresh normal-limit verification.
Actual independent feeds, pool depth/fees/routes, target gas/order economics,
operating rollout, OpenSea/VRF and independent audit/remediation remain open.

## Operator and documentation

Use [the owning guide](../../docs/EXECUTION_QUALITY.md) and
[exact setter procedure](../../docs/OPERATOR_MANUAL.md#set-additional-execution-loss).
Current Todo, feature/reference, roadmap, release record, profile, service guides
and repo context are reconciled with this scope. Historical reports keep their
original bytes/source claims. Source publication does not deploy or restart anything.
