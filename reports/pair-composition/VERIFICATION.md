# Local pair-conversion verification - 2026-10-23

**Undeployed candidate; production NOT APPROVED. Internal review, not an independent audit.**
Publication is recorded [separately](PUBLICATION.md). The website, public signing,
running 8902/Anvil/NFT/LP state, browser journals and paused monitor are unchanged.

| Check | Evidence and scope |
| --- | --- |
| Final affected Solidity | [141 passes](final/attempt1/receipt.json), including 14 new composition cases and the aggregate-loss fuzz property with 1,001 recorded runs. Real Vault, NFT, Fees, Rewards, Membership, Oracle and Migration; deliberately fake venue, token markets, price feeds, authority fixtures and VRF. |
| Normal production build | [33 object gates](build/final/size-gates.json), [successful command receipt](build/final/receipt.json). Solc 0.8.26/Cancun and unchanged normal optimizer/via-IR profile; no raised EVM limits. Metadata/AST bind results to exact sources. |
| Backend/configuration | [176 Python passes](python/receipt.json): activation preparation/HTTP, both exact Budget ABI variants, historical reserve price/share verification and production manifest admission. These are mock-RPC/offline configuration tests, not real-provider qualification. |
| Source/document hygiene | [Source consistency](source-checks.json); generated Todo and changed-document links checked separately. Narrow consistency checks are not a vulnerability scanner. |

The final Solidity run covers pair conversion, same-pair switches, Vault accounting,
pooled entry, original-source atomic activation, entry execution limits, global
membership dust, Rewards/Fees, native liquidity and manager encoding. No unrelated
browser suite, public transaction, fork campaign or deferred load campaign ran.

## What was verified

- Stable NFT/bucket/home identity and share supply; old funded rewards remain
  claimable by the NFT's next owner. The old immutable creator inbox still works.
- One fixed starting price vector across close/conversion/deployment; a later
  price change cannot conceal execution loss. A 2,000-unit starting position
  must retain at least 1,940 units at $1/unit; 1,939 rejects atomically.
- Pre-existing helper/Vault donations do not subsidize the floor. Failed swaps,
  unfinished source conversion, invalid review identity/epoch/deadline and mint
  failures roll back custody, allowances, reservations, rewards and epoch.
- Historical compound remains incumbent NAV for new share issuance and NFT
  valuation, without becoming the entrant's marginal deployed LP. Old venue dust
  cannot enter a new NFT's collective membership. Selected old compound can be
  consolidated, including without changing the current pool.
- Unselected historical reserves remain in Fees and cannot force unrelated
  feeds/tokens into a healthy principal move. Pause/park/resume retains the
  separate raw-close and atomic-conversion boundaries.
- Current composed parked records carry their authenticated epoch and classify
  idle under current accounting currencies. The focused record roundtrip uses
  mock authority; it is not a complete real-controller composed cutover rehearsal.
- Legacy V3 principal proposals reject composed buckets, including after returning
  to the original pair. This is not a new bridge implementation.

## Review findings and fixes

1. **Historical reserve dilution:** include non-current compound in the incumbent
   share denominator and marked NAV; never use it to satisfy new input's 99% floor.
2. **Unrelated currency liveness:** do not sweep/price every historical reserve
   during every move. Only currencies present in source/destination/typed route
   are selected; other reserves remain backed and can be consolidated separately.
3. **Caller boundaries:** preserve `access.moduleAuthorized(VAULT,caller)` for
   ordinary reserve release. The fixed companion may release only its active
   bucket while taking reserves inside the guarded Vault operation. Liquidity
   swap admission is limited to the constructor-created companion, not an EOA.
4. **EVM size:** extract typed read checks and fixed custody dispatch into existing
   immutable companions. Entry.validateOwner and Registry source valuation still
   run with Vault as caller. No arbitrary executor, rescue, delegatecall or proxy.
5. **Backend compatibility:** recognize the exact bucket-aware eight-argument
   result ABI alongside the explicit legacy seven-argument ABI; ambiguous frames
   fail. Historical Oracle.value calls are isolated to the Budget result frame,
   checked against reviewed same-block token/feed pins, then used in share math.
   Unknown currencies/prices do not produce a wallet draft. Public response
   shape and local-only signing policy are unchanged.

Runtime/initcode-object bytes: Vault **24,567 / 46,945**, Migration
**24,035 / 45,087**, PairMigration **19,765 / 20,404**. Vault has only **9 runtime
bytes** of margin. Its 96 constructor-argument bytes also fit the 49,152 initcode
limit. All other object gates explicitly exclude constructor arguments; qualify
actual deployment calldata/URI and gas. Future Vault additions need further
extraction, not relaxed limits.

## Incremental evidence and development diagnostics

The [broader preceding-draft run](affected/attempt1/receipt.json) executed 360
cases: 357 passed and three new fixture assertions failed. All 349 cases outside
PairComposition passed. The fixture errors were a 1,970 threshold instead of the
correct 1,940 on a 2,000-unit position, the matching fuzz assertion, and an
expected-revert placed before an external getter. These were corrected; final
focused checks passed. The remaining code changes then narrowed historical
reserve selection and restored module authorization; affected paths were rerun
in the final 141-case run. Do not sum these counts or call the earlier broad run
a fresh full regression of the final tree.

Early development builds exceeded standard code sizes; the source was refactored.
An otherwise size-compliant sandbox build also failed Foundry's Windows cache
lookup. The final authorized offline build completed with exit 0. Earlier
[attempt4](build/attempt4/receipt.json) and [attempt5](build/attempt5/receipt.json)
retain failures; they are not passing final evidence.

## Remaining qualification

Actual assets/routes, hooks, wrappers, oracle services, MEV and bounded execution
gas; complete composed-bucket controller cutover; new external payout currencies;
authenticated multi-currency bridge/message/ACK accounting, verified finality and
future-chain canonical relocation; exact-commit Ubuntu CI; and independent audit
with remediation remain open. Existing per-leg venue guards remain in production;
the fake venue injects larger artificial leg losses to isolate the aggregate cap.
No mock result qualifies real Uniswap execution or external revenue terms.
See the [operator procedure](../../docs/PAIR_MIGRATION.md) and
[sole task ledger](../../TODO.md#task-custody-composition).
