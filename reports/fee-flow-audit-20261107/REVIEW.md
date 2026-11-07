# LP conversion, claims and gas: audit and corrections

Baseline mainc055684,7November2026. **Source candidate; production NOT APPROVED.**
This audit implements defects rather than promising every dependency/market will
remain usable. [Verification](VERIFICATION.md) separates actual evidence/reuse,
controlled fixtures, failed attempts and remaining qualification.

## Findings and resulting behavior

| Finding | Correction / boundary |
| --- | --- |
| V3's wrapper USD reference could weaken the final nativeETH1% floor. Independently admitted wrapper/native policies could disagree while both were internally valid. | For non-wrapper v3 swaps require BOTH existing wrapper and final nativeETH floors, plus positive/fresh quotes. Verify authenticated wrapper decimals18 before/after external actions. Exact direct unwrap stays1:1 without USD dependency. Native-v4 execution body is unchanged. Missing/stale native data defers conversion with rights intact. |
| Whole32-ID conversion windows could repeatedly exceed keeper gas/cost limits, leaving affordable subsets unconverted. | Fresh7 prepares at most six independent prefixes32→16→8→4→2→1, within original caps. Persist continuation after a successful subset so suffixes remain reachable. Strict sanitized pre-send execution refusals may permit probes but diagnose no token fault. Transport/rate/internal/work-limit failures do not. |
| A conversion review could age or cross into an exhausted new UTC day before signing. | Final fresh7 head/deadline/current-day-cost check before durable intent. Do not rewrite calldata, minimums, deadline, nonce or a saved journal to revive a stale operation. |
| Fresh7 could treat malformed/insufficient RPC conversion simulation output as usable. | Require exactly one uint256 result meeting the captured minimum; unknown/empty/below-min results stop without prefix probes or signing. |
| Valid `LPRewardsConverted(id,ZZZ,0,0,0,0)` rows could permanently make exact earnings replay unavailable. A funded batch may legitimately include a minted dormant/already-claimed ID. | Accept only a genuine zero-source/zero-native no-op, retaining identity/source/context and exact `_take` component checks. Reject native credit without its corresponding source, preserve lazy tree settlement, create no zero direct-credit map and count no income. |
| Backend12M was hardcoded, making future reviewed changes require source edits. | Add opt-in transaction policy2 with an operator-owned decimal gas cap21k–64M, confirmed-block cap binding, full20% estimate headroom and schema2 drafts/plans. Policy1 remains12M/schema1 with unchanged behavior. No automatic widening, financial-policy change or signer extension. |
| Operator prose confused internal LP currencies, royalties and future gas management. | Clarify ETH+sameZZZ internal books, separate keeper swap, ETH normal claims, explicit source-ZZZ fallback, original-currency royalties and distinct backend/keeper/subcall/router/network limits. Fix stale settlement3/current inventory references. |

## Preserved economic and authority rules

The same fixed ZZZ belongs to the LP/contribution identity. There is no second
reward ZZZ token. Actual harvest allocates80/10/5/5; only already-earned holder
components enter LP conversion. Same NFT/components receive output, never a new
current cohort. Conversion/claim/import is not new income. Source claims and
already funded ETH claims need no USD oracle; claims follow current owners,
ordinary pause preserves them, and failed swaps/payouts roll back atomically.
Royalties remain separate exact original-currency settlement4. Principal,
compound/buyback reserves, canonical funding/abort and terminal holder return
are not redirected or made withdrawable by these changes.

Read-only lifecycle inspection also confirms no terminal-exit lock on earned-fee
conversion: governance must unpause permitted reward work, with a still-usable
reviewed conversion route. `Rewards.convertBatch` has no principal-operating gate;
the keeper's exit-blocked set excludes it. Unpause never reopens principal. This
was source inspection, not a fresh terminal-exit EVM rehearsal.

## Deliberate failure and recovery boundaries

- A cheap reviewed route and usable source/ETH prices are still necessary. The
  recorded approximately1.101% selected route cannot satisfy the default1% cap.
  A waiting ZZZ balance is not claimable ETH; select a qualified cheaper route,
  repair dependencies or explicitly claim the source asset. Do not silently widen.
- Tiny positive source components can round to0ETHwei under the existing
  cumulative output rule; the execution floor is aggregate, not a per-component
  USD promise. Economic batch minima and source-claim recovery remain important.
- Batches may legitimately need splitting.32is a router count bound, not gas
  approval; a permanently rejecting/frozen token or lost-owner key cannot be
  fixed by increasing gas. Unknown failures remain unavailable, never guessed zero.
- Policy2 requires matching unsigned schema2 consumers and actual provider/fee/
  chain/workload review. The64M ceiling is backend resource engineering, not a
  Robinhood gas-limit claim. Actual per-transaction/provider limits may be lower
  than the block limit. Existing websites/signers are unchanged and unqualified
  for this optional policy. After sealing, operator configuration is updated via
  the documented reviewed file/restart procedure, not a governance contract call.
- Old checkpoints/runtimes/journals keep their actual profiles. Checkpoint1 is
  not reinterpreted as exact7; checkpoint2/lifetime operation remains separate work.

See [operator procedure](../../docs/OPERATOR_MANUAL.md#lp-fee-conversion-and-claim-gas-operations),
[LP settlement](../../docs/LP_ETH_SETTLEMENT.md), [reviewed gas2](../../docs/FRONTEND_TRANSACTIONS.md#reviewed-gas-policy2-operator-configuration)
and the [sole Todo](../../TODO.md). Nothing was deployed, enabled, signed,
reset, restarted or published to either website. Independent approval remains open.
