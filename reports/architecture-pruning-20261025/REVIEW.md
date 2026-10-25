# Remaining-architecture pruning

Baseline is `280fb28d8a848425283dc3129de50fe5ddbea7f5`. The user requested a
skeptical whole-project necessity review, approved removal of obsolete Position
fields under a new explicit profile and then asked to resolve related cleanup
together, including removal of the zero-delay timelock machinery. This is an
architecture-changing simplification with preserved economic/custody rules,
not merely an unused-import sweep or an independent audit.

The earlier orphan scan and31-contract purpose inventory were useful screening,
but did **not** prove every inherited function or compatibility field was needed.
This pass challenged those assumptions against actual current execution, public
callers, legacy readers, setup, services and operator procedures.

## Removed or isolated

| Area | Change and reason |
| --- | --- |
| Governance | Replace the full zero-delay TimelockController with a selected wallet calling modules directly. Remove scheduler/batch execution, operation IDs/timestamps/predecessors, role machinery, generic execution, receive hook and always-reverting delay setter. Wallet signatures/nonces now authorize calls. Two-step no-delay governance handover protects against address typos; separate roles stay separate. |
| Position model | Remove seven cross-chain home/location/receiver/currency fields and unused Remote/Inbound states. Actual local Position is8words, with an explicit accounting3 codec/status map and canonicalV4. Old profiles stay separate. |
| Membership/NFT handoff | Membership no longer inherits empty financial-backing arrays/maps/asset-transfer hooks. NFT codec's four always-reverting backing hooks are removed. Both migrate zero-asset records; funded Rewards/Royalties retain exact backing. |
| Oracle | Remove the unused single-feed compatibility mapping/getter/event write. Current prices still require complete dual-source policies. Old event decoding and pricing1 readers target old bytecode only. |
| Custody | Remove the movePool convenience alias, duplicate per-plan ZZZ identity/ZZZ amount and public-only-internal handoff-minimum helper. Use moveFunds, the fixed ZZZ and original sent-currency quantities. Request ABI, captured budgets, normal/raw modes and original-currency full return remain. |
| Registry | Remove obsolete nativeAsset getter from new code; old accounting1 readers retain calls to old pinned deployments. Generic ERC20 admission now requires the same fixed ZZZ in its pair, preventing arbitrary non-ZZZ pools. Native admission retains its independent identity/runtime guard. |
| Current release command | Separate the873-line historical validator from the102-line current CLI. Default current validation never loads/evaluates the old bridge engine. Explicit historical inspection lazy-loads it and cannot qualify the current release. Bounded JSON and atomic output remain. |
| Research and tests | Retire the Pons verifier, unused stablecoin-activation research reader/tests and three toy bridge models. Preserve exact committed archives and unpublished dirty-draft backups. Retire obsolete queue/foreign-position/token-replacement fixtures; port real authorization, financial and handoff assertions rather than replacing them with fake passing tests. |
| Historical events | Preserve all133 prior descriptors exactly, explicitly moving16 removed-source layouts into historical decoding. Add only the two new governance events, giving135 total descriptors. Old event support grants no live authority. |

Current source-bound callable documentation shrinks from643 to608 functions;
concrete classes remain31 because the retained compartments each serve actual
custody, accounting or bounded-bytecode duties. A lower contract count alone
would not establish simpler or safer behavior.

## Safety and consistency decisions

- Direct governance is intentional. Controller operation replay/predecessor and
  cancellation semantics are removed, not claimed to remain. Review exact target,
  value, calldata and wallet signers/threshold; the wallet owns transaction replay
  protection. There is no advance intervention window or generic controller call.
- Only the selected governance wallet drains during preparation or authorizes
  canonical handoff. Merely changing ordinary configuration authorization would
  have stranded those paths; both were updated. Terminal lifecycle states still
  prevent configuration/revival; guardian unpause and module rebinding stay denied.
- Zero-asset modules report zero backing count; coordinator funding bounds prevent
  dispatch to nonexistent transfer hooks. No financial ledger backing is skipped.
- Currency identity comes from admitted pool keys. Source/pool/immutable Buyback/
  normal exit still share one fixed ZZZ; native ETH, wrapped assets and separate
  royalty currencies cannot be confused. No automatic token relabelling exists.
- New Position rows require their explicit version, exact size and local statuses.
  Canonical imports reject old/trailing row encodings and remain source-derived,
  ordered, fully funded and abortable. Existing local deployments/journals keep
  their original source/profile; no reinterpretation or automatic upgrade occurs.
- API current Dormant3 valuation must be confirmed zero, not unavailable. Historical
  keeper parked checks preserve their original location-only semantics rather
  than accidentally imposing the new model on old predecessor provenance.
- An external issuer exchange/bridge is still trusted custody. Exit alone cannot
  relocate NFT ownership/reward accounting; converting old tokens may make the
  old original-currency return impossible. A reviewed continuity plan is required
  before irreversible exchanges. No universal issuer/chain cutover is promised.

## Bytecode facts

[Exact comparison](bytecode-comparison.json) uses identical compiler/EVM/optimizer
settings and36 normal object gates. Among31 concrete contracts,13 runtimes shrink,
16 retain their size and2 grow. Controller runtime14,904→9,207 and total initcode
with arguments49,123→42,177; Vault runtime23,889→22,852; Membership10,336→7,389;
Oracle10,939→10,242. These are compiled sizes, not transaction gas benchmarks.

Registry grows138runtime bytes for fixed-ZZZ pair admission. Handoff grows155 for
the direct governance authorization read. Those are necessary new guards, not
unexplained cleanup regressions. The old29-byte Access argument margin is resolved:
three static addresses leave6,975 bytes. Vault runtime headroom is1,724 bytes.
RoyaltyFactory still has only69 runtime bytes, so future changes must respect its
normal gate. No size waiver or optimizer/EVM change is used.

## Retained code is not obsolete solely by name

WETH/stablecoin royalty receipt and approved ETH conversion, optional cheaper
contribution conversion, correct Uniswap ABI methods, dual price feeds, original
transaction recovery, old deployment/event readers, per-NFT reward ledgers,
incumbent dust, attributed idle and full same-chain handoff remain actual duties.
Only ETH/fixed ZZZ are contribution inputs. Whole-collection same-chain handoff
is distinct from the deleted cross-chain bridge and from external custody exit.

Public/operator functions can have external callers. Optional price adapters and
routes are not automatically abandoned when a provider is still unqualified.
No universal proof of minimality, gas optimality or exploit absence is claimed.

See [profile guide](../../docs/POSITION_V3.md), [verification](VERIFICATION.md),
retirement manifests and the separate publication receipt for exact source scope.
Actual services/routes/independent feeds/VRF, authorities, OpenSea/native wallet,
strategy/gas economics, operating rehearsals and independent audit/remediation
remain open. Production NOT APPROVED. No deployment, public transaction, website
source/build/server, existing Anvil/NFT/LP/balance/journal or monitor operation.
