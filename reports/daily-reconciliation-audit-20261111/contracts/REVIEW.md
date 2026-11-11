# Contract change and evidence review

Scope: main `872a5a5`, compared with `0acb123`, including fixed-pair cleanup
`8785728` and the reference-execution follow-up. This is a defensive source/call-
boundary review of14 changed Solidity files and their invoked dependencies. It
is not another full-project execution campaign, independent audit, or proof that
all defects have been exhausted. Production Solidity remains unchanged.

## Confirmed correction: authority descriptions

Two descriptions in the earlier current static record named Fees where the
actual authorization is Buyback. `LiquidityManager.swap` accepts only the sealed
fixed Vault or Buyback (`src/ZZZLiquidityManager.sol:220–223`); typed custody and
position-executor callbacks have separate fixed callers. The source and generated
function reference already state those permissions correctly.

The [immutable errata](AUTHORITY_ERRATA.md) preserve exact old/new text, detector
fingerprints and source hash. The new complete strict record retains567 finding
identities and all dispositions, with only two rationale fields corrected plus
top-level provenance/reviewer labels. It preserves the original162current/405reuse
scope; the other565records are not claimed freshly re-audited. The original
reference-execution record is byte-for-byte unchanged.

The strict checker now selects the corrected record. Coverage against the
existing actual analyzer output and44checker regression tests pass. No analyzer
or compiler rerun accompanies these prose corrections.

## Source boundaries reconsidered

| Area | Current source conclusion and limit |
| --- | --- |
| Fixed-pair cleanup | Rewards starts with ETH; ordinary additional admission and canonical asset writes are bound to the one fixed ZZZ with at most two assets. Current pool admission and fee intake use that pair. Removed foreign-principal loops do not remove royalty currencies, pair compound or historical codecs. Arbitrary malicious replacement-code honesty remains a separate governance trust. |
| Share accounting | Entrant-only balancing, the three contribution NAV phases, repriced incumbent physical LP, exact marginal deployed LP and net-NAV issuance remain distinct. Main/residual/idle/current-pair compound stay backing; residual L and rebalance clocks are not modified by contributions. |
| Context owner | Only the fixed Pricing child owns a whole-operation scope. Fixed Manager may own a standalone scope or borrow Pricing through its authenticated Vault branch; existing loan/nested unrelated borrowing rejects. No public context setter or generic execution target exists. |
|49-word codec | The static typed ABI shape is exactly49words/1568bytes. Only compiler-encoded private writes populate it; full loaders retain typed decoding. Quote loaders select named ABI words, retain controls/pending rejection, and do not assume Solidity's internal struct-memory layout. A future shape change fails the exact-length assertion until deliberately reviewed. |
| Context lifecycle | Successful owner end performs full validation then clears every transient word. Transaction revert/end also prevents cross-transaction persistence. Quote values alone grant no authority; full proof remains at mutable boundaries. |
| Source proof | Original bounds/full rounds/policy IDs remain captured. Registered composite proofs reconstruct the original observation under current pinned ETH data while returning separately validated live rounds. Generic sources retain exact original-round checks. No public live Oracle getter is replaced by a frozen cache. |
| Market identity | Reference matching and LP-destination exclusion use core plus PoolId, retaining exact StateView binding. Equal keys/PoolIds on different cores do not collide. Two distinct addresses alone do not establish source independence. |
| Own swap | Normal Manager execution uses one actual-core quote and exact output/full-state proof before settlement, then post-settlement/refund/final checks. No keeper supplies predicted state. Only a verified own transition may advance a reference; live agreement/freshness still apply. |
| LP writes | Expected reference/external-venue L stays fixed. Only a nonreference destination's active-L comparison may be released after validated balance completion for legitimate LP writes; exact spot/tick/fees and actual position owner/ticks/L checks remain. |
| Maintenance | Ordinary capture starts before harvest/close and closes after custody/loss/main-floor proofs. At most one balancing swap is used. Both physical legs are included. Sample/control identity is preserved across intentional replacement rather than reinterpreting the new LP as old evidence. |
| Force/recovery | Explicit paused governance emergency retains its separate manifest/mask and intentionally can waive financial constraints. Raw harvest, parking, terminal holder return and funded claims do not acquire a normal execution-price scope. Broken actual tokens/core can still prevent progress. |
| Read-only factoring | Math remains the fixed Balancer-created child with no approvals, state writes, callbacks or custody. Pricing/Budget/Manager retain actual caller checks and emergency-mask decisions. Public supplied-data Math queries are advisory. |
| Mint/rewards | Changes add no mint-payment, VRF or royalty entitlement rule. Current-owner exact-unit rights,80/10/5/5 and canonicalV10 remain. Sealed runtime adoption and actual services remain separate from source publication. |

These conclusions are supported by source inspection and the existing explicitly
scoped evidence; they are not567 newly reviewed analyzer decisions or fresh tests
of every row. The prior77-method compatibility run and actual reference/Entry
tests retain their own source, fixture and failure limits. No unchanged broad
suite was rerun for this review.

## Unverified question: fees appearing after the last checkpoint

The current flow harvests before growing an existing LP
(`src/ZZZVault.sol:490–493`, and the contribution sequence around318–332).
`_put` later approves/calls the fixed position executor, which pulls/approves the
fixed token before PosM increases (`src/ZZZLPPositionExecutor.sol:139–208`).
The pinned periphery's `PositionManager._increase` separates `feesAccrued` for
principal slippage validation but settles the resulting net currency delta
(`node_modules/@uniswap/v4-periphery/src/PositionManager.sol:287–302,491–525`).

The unresolved defensive question is whether a late fee credit from an admitted
mutable dependency callback could be netted against the new principal debit,
then appear as refunded attributed idle in contribution NAV instead of passing
through80/10/5/5. This review did **not** reproduce or verify that accounting
effect. It must not be reported as demonstrated share inflation, loss or an
unconditional outside-trader exploit.

Ordinary outside transactions cannot interleave inside atomic harvest/increase.
Relevance requires a reachable mutable callback or compromised/upgraded admitted
fixed-token/Permit2/periphery dependency after the last fee checkpoint and before
the increase; a plain fixed ERC-20 and unchanged trusted periphery do not establish
that prerequisite. Current code pins do not universally freeze upstream proxy
behavior. The exact dependency implementation/permissions remain qualification
work, rather than an assumed malicious capability of every NFT holder.

Related historical reviews already retain late collect/burn callback fees as a
dependency-qualified boundary: [residual lifecycle](../../residual-lifecycle-20261106/REVIEW.md),
“Open dependency and economic boundaries”, item1, and
[harvesting](../../harvesting-audit-20261106/REVIEW.md), “Remaining risks and
qualification”, first paragraph. Increase netting is an analogous separate
question; those reports did not prove this specific behavior.

If future evidence establishes the issue, assess principal-debit verification
against the exact rounded-up debts independently of fee credits. Any proposed
guard must preserve legitimate rounding/fee settlement, one-sided contributions,
single/hybrid layouts, both settlement currencies and explicitly forced paths.
No speculative production guard, accounting rule or new permission was added.

## Remaining release limits

The existing full cold Entry results remain around15.32M/15.64M gas, above the
unchanged12M default. This review neither raises that budget nor removes financial
proofs. Source/runtime/initcode headroom, real independent references and depth,
feed publication/liveness, actual OpenSea/VRF/authority configuration, service
adoption/recovery and independent audit remain separate release work.

The selected spot/no-TWAP decision and reviewed manual-emergency trust remain
explicit. This review changes no deployed contract, site/service, existing Anvil,
journal, signer, custody or economic right, and does not restart the user-paused
heartbeat.
