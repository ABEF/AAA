# Who can call PoPL functions

Fresh **accounting7 / LP-allocation1 / canonicalV10 / custody5 / schema17 / residual-reinvest1 / direct Entry3** candidate; undeployed,
production **NOT APPROVED**. One human operator controls governance. This does not
make every callable function operator-only: NFT owners must retain their rights,
the keeper its limited work and dependencies their authenticated callbacks.

| Caller | Allowed purpose | Important limits |
| --- | --- | --- |
| Governance/operator wallet | Reviewed configuration, role grants/revocation, pause/unpause, same-pair movement, parking/residual close, same-main residual consolidation, emergency and terminal LP return | Immediate authority with no timelock; sealed identities and lifecycle remain. Explicit emergency financial bypass can lose nearly all principal. |
| Bootstrap | Initial one-time graph/policy configuration and seal | Erased permanently at seal. Preseal configuration is not permission for a distinct governance address. |
| Guardian | Emergency pause | Cannot unpause, change strategy, move LP or claim holder funds. |
| Authorized keeper | Guarded rebalance, compound, buyback, observation and applicable reward conversions | Not governance. Cannot approve new dependencies, initiate/close terminal exit, allocate its principal or distribute it in custody5. |
| Current NFT owner | Activate/grow with own funds; claim accrued LP rewards and royalties; owner-controlled principal fallback after exit | Governance and ERC721 transfer approvals do not let someone claim another owner's money. Fixed ClaimRouter authenticates current ownership. |
| Owner/approved ERC721 transfer operator | Standard approvals/transfers | Transfer approval is not authority to activate with another owner's funds, claim rewards or redirect exit proceeds. |
| Fixed module/self/factory | Narrow typed internal work | Exact sealed binding, parent/module identity or self-only checks. Not an arbitrary operator executor. |
| Uniswap / original randomness service | Expected callbacks | Exact caller, active payload/request and lifecycle checks; no caller-selected authority. |
| Any address | Public reads; bounded fee collection; royalty funding/synchronization; metadata refresh/finalize of fulfilled draws; phase-bound canonical progress relays; caller-bound factory deployment | Cannot choose another holder's recipient, change splits/traits, start migration or authorize a successor. Canonical imports authenticate each row against the fixed source. |

## Reward claims versus principal distribution

**Reward claims stay available to the current NFT owner.** Rewards.claim,
RoyaltyRewards.claim and the fixed ClaimRouter pay the authenticated holder.
They are distinct from principal returned when governance permanently shuts LP.
Old rewards and future eligible royalties survive that shutdown.

Only governance calls Migration.allocatePrincipal(maximum) and
Migration.distributePrincipal(ids) in custody5. Allocation determines each NFT's
proportional actual ETH+ZZZ; distribution pushes it to its current owner. Each
batch has at most32 entries. The submitting governance wallet pays gas. Failed
receivers remain backed and isolated; their actual owner retains claimPrincipal
fallback. No operator-selected external custody recipient exists.

See the [complete exit procedure](HOLDER_COLLECTIVE_EXIT.md#operator-procedure).
Keep ordinary keeper principal_distribution disabled for custody5; do not put
governance credentials on that server. Lost governance can delay closing or
allocation; owner reward claims do not require that wallet.

## Hashes are public review data

reviewHash records reviewed intent; custodyHash, portfolioHash and policy
fingerprints bind state/controls. They are not passwords or permissions. Knowing
or copying them never satisfies governance, owner, keeper or callback checks.
A read-only explorer call cannot change state. Verify the actual deployment,
chain, ABI, caller and full ordered inputs before any write.

The [function reference](CONTRACT_FUNCTIONS.md) lists every current input, output
and caller class across38 concrete contracts. The source-scoped historical
[authority inventory](../reports/authority-audit-20261103/AUTHORITY_INVENTORY.json)
resolves241 mutable ABI entries to effective implementations, including inherited
ERC721 functions, across37 concrete contracts.577 reads,37 constructors and13
native receivers are its historical counts, not current catalog totals or executed tests. The
[review](../reports/authority-audit-20261103/REVIEW.md) records scope and limits.

## Fresh versus historical profiles

Fresh inventory17 requires accounting7/LP-allocation1/custody5, canonicalV10,
the fixed Rewards canonical child and residual-reinvest1/raw-exit1 capabilities.
Schema15/accounting6/V8 and earlier inventories retain
their original profiles. Governance-only consolidation is never a keeper action.
[Exact procedure](OPERATOR_MANUAL.md#same-main-residual-consolidation). Read/keeper configurations explicitly
set custody_version:5 and check the actual getter/runtime. Omission retains the
historical default4 for accounting6/5; accounting7 requires explicit5 and fails
on omission. Each predecessor in a custody5 lineage declares its own custody_version; successor
permissions never overwrite historical predecessor configuration.

Schema9/custody4/direct Entry3 and older deployments keep their original callable
permissions and journals. Publication does not upgrade a runtime or service.
Public signing remains disabled; existing Anvil, sites and journals stay unchanged.

This internal review is not a guarantee against hacks. Key compromise, reviewed
malicious successor code, upstream changes, dependency failure and explicit
emergency powers remain material trust/liveness risks. Select/secure authorities,
rehearse actual operation and obtain independent review before production.

## Restricted exact-LP companion calls

Vault alone synchronizes NFT LP shares; Membership alone synchronizes the equal
collective weight. NFT-owner claims do not gain either permission. The immutable
Rewards canonical child alone may call parent canonicalBarrier/canonicalSeed/
canonicalNode reads, typed canonicalWrite or canonicalSend. Even a read-only
call can have a caller restriction; these are not ordinary governance or holder
actions. The child enforces canonical phase, source rows and classified funding.
canonicalWrite accepts only the closed asset/seed/node formats; it cannot select
arbitrary storage slots. There is no delegatecall or generic operator executor.
Record Rewards.canonicalModule(), child access()/rewards(), Handoff.moduleAt(3)
and independently reviewed runtime pins; LP reward balances remain held by Rewards.

## Restricted royalty recovery

Current governance alone calls RoyaltyRewards.allocateUnallocated with the exact
inputs in the [operator procedure](ROYALTY_SETTLEMENT.md#unexpected-currencies-and-unallocated-recovery).
An authorized keeper cannot recover unsupported/orphaned funds. Existing
royalty swaps/unwraps and converter binding are removed from settlement4. Allocation has no
arbitrary recipient or earned-balance override; it credits the SAME admitted currency
to active weights at execution. Retired forwardLate fixes its successor. Original
owner claims and32-entry mixed claim batches stay owner-authorized; LP conversion
retains its separate keeper permission. Historical royalty conversion profiles remain separate.
