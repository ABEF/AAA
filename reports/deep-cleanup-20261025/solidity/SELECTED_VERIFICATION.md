# Affected Solidity verification

Exactly **32 selected methods passed** in one isolated Forge run, with no failed,
skipped, missing, unexpected or inherited extra methods. The run took 352.453
seconds including fresh compilation. It used the unchanged hash-pinned
[AST-selection driver](../../simplification-20261025/solidity/run-focused.py)
through [this wrapper](run-selected.py). The complete selection, body hashes,
case outcomes and artifact hashes are in [the receipt](selected-verification.json).

| Scope | Methods | What this verifies |
| --- | ---: | --- |
| NativeLiquidityTest |20| Actual installed Core/PosM native mint, increase, fee collection, close, swaps, exact value/prefund/approval guards and rollback; the replaced wrapped-only fixture is mapped separately. |
| DirectGovernanceTest |4| Constructor/grant/revocation role logs agree with actual stored authority; invalid/unauthorized updates emit no events or authority changes. |
| V3VenueValidationTest |2| Both endpoint orders and the exact rejection selector/short-circuit dependency-read order. |
| NFTOwnershipRightsTest |1| Real LP activation succeeds while only an unavailable royalty currency defers eligibility; old receipts remain protected. |
| RoyaltyCustodyTest |2| Exact ERC20/native custody return is not new income, and accrued rights follow the NFT owner. |
| RoyaltyConversionTest |2| Only earned balances convert, existing native entitlement remains, and loss-limit failure fully rolls back before retry. |
| CanonicalHandoffTest |1| Converted native LP rewards reach the current owner through complete same-chain handoff. |

The wrapper checked all 265 final AST inputs before and after execution:
131 project inputs and 134 installed dependency inputs. It also matched every
input in the separate closed normal build: 44 production files and 31 dependencies.
All bindings and the selected test bodies remained exact. No retries or test
relaxations were needed. Normal compiler/optimizer settings and size guards were
preserved; the separate 37 production-object gates are root's normal-build evidence.

NativeLiquidityTest uses installed PoolManager 1.0.2, PositionManager 1.0.3 and
StateView. Authority, native admission and USD prices are explicit local seams.
FactualPermit models the used Permit2 allowance/expiry path; actual Permit2 pins
Solidity 0.8.17 and is not instantiated by this 0.8.26 profile. The royalty and
handoff cases use actual PoPL accounting with substituted venue/router/feed/VRF
dependencies. These boundaries are not deployed-market or production approval.

This is an affected-behavior run, not a fresh full regression, maximal gas or
strategy qualification, live provider/route/feed/VRF/OpenSea/operating rehearsal,
or independent audit. No RPC, public transaction, existing Anvil/NFT/LP/balance
state, wallet journal, service or website was used or changed.
