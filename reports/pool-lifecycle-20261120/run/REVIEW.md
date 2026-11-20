# Current F6 physical LP lifecycle on the supplied pool

20 November 2026. Baseline main `4b6497be76191a8a3a5295267b4706f811d5a899`.
The supplied pool `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`
remains a test target, not an approved production selection.

**The final finite physical-LP partition passed. Production remains NOT APPROVED.**

## What actually passed

The new owned fork uses Robinhood4663 block119107223, hash
`0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335`.
Fresh read-only chain, exact anchor and genesis number0/hash
`0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c`
are checked before loading retained exact-anchor cache entries. Original
StateView active liquidity is0; this does not prove all distant ranges empty.
Native core/periphery/Permit2/ZZZ runtime hashes and wiring match the pinned target.

Trusted F6 production creation objects and the exact previously compiled fixture
output are reused, with100 normal source pins and build inputs checked. No
production compile, old population, historical eleven-method fork suite or
unchanged behavioral suite is rerun. Necessary local setup and earlier partial
phases are repeated to reach the remaining journey; they are not extra coverage.

| Final journey | Observed result |
| --- | --- |
| Mint through real F6 Manager | One actual Uniswap position, owned by typed test custody; L180704995773128430458. |
| Increase through real F6 Manager | Same position and ticks121400/132600; L198775495350441273503. |
| Impossible minimum only | Same amounts/value as the successful increase, only minL changed toMAX128. Full-cap simulation returns exact `Slippage()`; actual failed receipt uses858,751 of1M and restores custody balances, L and allowance. |
| Controlled external trades | Test `Source9RehearsalTrader` executes both directions against actual Core. Reverse input is half the exact immediately measured ZZZ gain, independent of older wallet balances. |
| Harvest | Actual custody gain10,009,999,999weiETH and1,409,486,118,578,156rawZZZ, with unchanged L. |
| Repeat harvest | No new ETH/ZZZ income or principal change without another trade. |
| Close | Actual principal110000499938733592weiETH +20090434875760894260190rawZZZ returns to the fixture; LP NFT returns exact `NOT_MINTED`; activeL returns0. |
| Cleanup | Manager/typed child ETH+ZZZ residuals and ERC20/Permit2 spend amounts are0. Owned PID15904 stops, no pending submission; existing environments are untouched. |

The final run includes39 local transactions:38 successful setup/action receipts
and one intentionally reverting guard transaction. Such a revert still consumes
its sender's local gas/nonce; rollback refers to position/custody state, not gas.
The full parent process-tree supervisor completes in42.312seconds. Last-run
public work is19 read-only HTTP posts,137 cache hits, zero429 and zero retries.
These observations do not qualify public-provider capacity or complete fees.
Across all new online attempts, the total is107 public posts (55+33+19),
314 cache hits (64+113+137), no429 and no retries. Attempt1 is offline only.
All three owned PIDs12044,28268 and15904 stop with no pending submission.

## Independent saved-wire checks

[Verification](VERIFICATION.json) reconciles448 immutable serialized request/
response rows,38 positive full-cap/estimate/padded preflights and included
envelopes, plus the separate intended-failure simulation/envelope/receipt.
Actual from/to/nonce/value/gas/gasPrice/type and receipt identity are bound.
[Included transactions](INCLUDED_TRANSACTIONS.json) retain the detailed records.

The verifier independently derives L, ownership, unchanged ticks, rollback
balances, actual fee gains, no-repeat balances, closed principal and zero
residuals/approvals from raw getters/events; RESULT booleans are not its sole
basis. The burned-position error is bound to code3 and exact `Error("NOT_MINTED")`,
not any RPC error. The verifier's first source stage mistakenly required setup
labels globally unique; legitimate repeated feed/bind labels were corrected to
exact unique phase selection. [Erratum](VERIFIER_FAILURES.json) preserves that
analysis error; no EVM case was rerun to correct the verifier.

[Deadline checks](DEADLINE_VERIFICATION.json) bind six actual calldata deadlines
to their observed owned-local review headers plus300seconds, inside the existing
600-second source maximum. One empty owned-local block is explicitly mined
before each LP review, with no pending transaction. Each actual receipt follows
in the next owned block. Receipts omit `blockTimestamp`; all execution timestamps
are not independently recovered. Source-pinned guard execution and actual
receipts remain the acceptance basis. No deadline guard is lengthened or skipped.

## Cache integrity and provider use

The older report did not export cached payloads. The first64 entries are explicitly
**derived hash-verified witnesses**, not relabeled raw responses: exact candidate
method/parameters and result must both match a successful cached event in the
immutable previous archive. Unknowns remain live misses. No latest, error,
transaction or receipt result is imported as a cache hit.

Later115/139-entry full exports are authenticated with their exact serialized
upstream HTTP bytes and ordered prior-cache provenance. The final145-entry full
export is retained for future review, alongside immutable requests and replies.
Live cold reads are configured at0.5requests/second, with immediate stop on a
provider HTTP/resource refusal and fixed work/size bounds. The900-second work
deadline is checked between calls; it is not universal DNS/body preemption.
The separately retained Windows kill-on-close job applies a1020-second wait
limit to the runner and its descendants, followed by bounded termination/handle
cleanup. It does not rely on a blocked HTTP worker returning cooperatively.

## Retained stages and corrections

1. Attempt1 refuses offline: the retained compiler source-unit name uses Windows
   backslashes. Its exact key is now derived by unique filename/content match;
   input/output hashes and original compilation unit identity are preserved.
2. Attempt2 gets through setup without429, but first mint simulation rejects
   `Expired()`: inherited test input used latest+3600 despite the source's
   maximum+600. Fresh per-operation+300 fixes the fixture input, not the contract.
3. Attempt3 proves mint/increase/minL rollback but stops before its first trade:
   Cast rejects Python's `True` spelling. The formatter now uses ABI `true/false`.
   Those earlier successes remain valid partial evidence, not additional passes.
4. Attempt4 completes the whole journey. Before cleanup it captures an881,747-byte
   owned-state dump with exact hash/header for reviewed future local recovery.
   Every owned node stops. No old state or failed artifact is overwritten.

Root's separate new offline controls exercise the recorder/cleanup, deadline and
Boolean rendering boundaries at their exact source stages. Those are not new
Solidity test methods or actual-market acceptance.

## Scope that remains excluded

This is **one physical main LP**, controlled with MockAccess, typed test custody/
budget/asset admission, correlated fixture USD prices and explicit local balances.
It does not instantiate PoPL NFT shares, Vault revenue allocation, membership,
claims, activation or Entry growth accounting. The external fee-generating trader
does not test production `Manager.swap`, balancing-router execution quality or
conversion routes. No two-leg/hybrid/terminal-holder-exit proof is added here.
The fixture deliberately receives more test ZZZ than the declared LP budgets;
its large final token balance includes unused test funding plus returned
principal/fees. It is not evidence of production entrant idle, deployed-LP
percentage or a passed3% contribution loss check.

Construction remains bounded32M, non-constructor setup/physical actions24M with
full25% padding, and the intentional failure's1M is a local test envelope rather
than a production policy. This is not whole Entry32M or keeper24M qualification.
Actual independent sources, market depth excluding PoPL, conversion feasibility,
target-chain full fees/providers/authorities, services and independent approval
remain open. Final production-pool selection stays deferred.

[Evidence archive](evidence.zip) and [manifest](EVIDENCE_MANIFEST.json) preserve
all four attempts, exact executed source stages, original failures, cache/HTTP
bytes, receipts, snapshots, cleanup and supervisor outputs. No public transaction,
production deployment/sealing, financial-right/cap change, signer expansion,
website/service/journal change or heartbeat restart occurred. The local MockAccess
fixture is sealed solely to exercise its configured ordinary typed LP path.
