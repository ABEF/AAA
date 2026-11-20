# Current F6 direct production swap partition

20 November 2026. Supplied test pool remains
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`, at authentic
Robinhood fork block119107223. Final launch-pool selection remains deferred.

## Result and precise scope

**Both direct production Manager swap directions pass.** The new test-only caller
invokes the trusted current F6 `ZZZLiquidityManager.swap`; Manager calls the real
`ZZZLPBalancer.quoteSwap`, predicted-transition Oracle checks, actual Uniswap core
unlock/swap/settlement and exact recipient-output checks. No production Solidity,
financial guard, gas limit, source/build profile or operating environment changed.

| Newly verified action | Actual input | Actual output | Estimate | Full25% transaction allowance | Actual gas |
| --- | --- | --- | ---: | ---: | ---: |
| ETH to ZZZ | 1,000,000,000,000wei ETH | 281,614,777,422,126,843raw ZZZ | 1,847,484 | 2,309,355 | 1,774,899 |
| ZZZ to ETH | 140,807,388,711,063,421raw ZZZ | 489,051,332,045wei ETH | 1,949,004 | 2,436,255 | 1,799,087 |

Both use the existing24M/full25% maintenance envelope. The reverse input is half
the actual forward output; the new caller has no substituted ZZZ funding. Exact
included core Swap events independently reconcile inputs, outputs, caller balances,
pool liquidity and final pool state. Both events record combined directional fee
11010millionths; a passing direct swap **does not qualify the separate1% earned-LP
ETH-conversion budget**.

A too-high caller output floor returns exact `Slippage()` in `eth_call`, leaving
caller funds/allowance, Manager/child balances, pool slot0 and active liquidity
unchanged. This is **simulation-only rollback**, not an intentionally mined failed
transaction. Caller minimum1 is supplemented by the unchanged stronger on-chain
execution floor and live price/control checks; it is not a replacement policy.

All six final receipts succeed: caller deployment, explicit test binding,
synthetic depth setup, **two newly covered swaps**, and depth cleanup. Setup/cleanup
receipts are not six new behavioral tests. Manager/LP-child native and ZZZ balances,
caller-to-Manager allowance and checked ERC20/Permit2 spend amounts finish zero.
The synthetic LP closes and active liquidity returns to zero. The current Manager
callback hash and expected output checks are enforced by the source-bound successful
transaction; the private callback hash is not separately read through a getter.

## Explicit test seams and exclusions

The previously verified owned-state dump is restored into a **new** isolated node.
Its archive bytes, dump, capture and original construction receipts are authenticated
before deriving addresses. Fresh chain/anchor/genesis verification precedes importing
the145-entry read-only warm cache. The trusted F6 source files are checked unchanged.

`MockAccess` is deliberately retained. The new typed fixture is bound as BUYBACK,
using that mock's documented test-only unrestricted bind. The original typed Vault
binding and other observed module bindings remain unchanged. This is not real
production Access authorization or buyback reserve accounting. Existing correlated
USD feed fixtures remain correlated; they do not qualify independent pricing.
One physical main is temporarily reopened solely as **synthetic local swap depth**.
Its setup replays necessary construction state, without rerunning the old lifecycle
suite or relabeling its evidence.

Direct Manager.swap quotes the **caller-supplied admitted pool**. It does not search
the execution catalog, select the best venue or prove `Manager.balance`/Entry route
selection. No catalog configuration was added to make this test pass. Full Entry,
NFT shares/ownership, incumbent checkpoints, fee splitting, royalty rights, optional
hybrid placement,1,000-NFT workloads, actual market depth, independent feeds and
complete Robinhood/provider fees remain separate qualifications.

## Restore-clock correction and preserved failure

Attempt1 restores the exact saved latest block but Anvil's next-block clock remains
behind it. Two disposable setup transactions then produce a timestamp before the
mock feeds' timestamps; Oracle correctly refuses with `InvalidPrice(ETH)`. This is
a report-driver restoration defect, not a source-contract vulnerability.

Attempt2 reads the pending clock, sets the next timestamp to the authenticated
saved timestamp plus one second, mines one owned empty block and verifies latest
and pending timestamps **before any transaction**. Subsequent operation deadlines
are refreshed from an owned recent head plus300seconds, within the existing600second
contract maximum. This changes only the newly owned test node. The original failed
stage, wire, source copies, outputs and cleanup remain in the archive.

The passing run uses26 read-only public requests/104 cache hits; the failed stage
uses7 public requests/101cache hits. All33 public HTTP responses are200, with no
retry or upstream refusal. Each local relay separately rejects2 requests as
not admitted, before any public forwarding. These4 local rejections are not
upstream/provider failures. The [offline count correction](NETWORK_COUNTS.json)
reads exact immutable relay summaries; the earlier22/7 cached-event counts did
not represent the full cache-hit totals. No raw archive was rewritten.
The bounded Windows kill-on-close job supervises the full process tree; both owned
node PIDs12376 and21208 are stopped with no pending transaction. Existing Anvil,
wallets, journals, services, websites, user-paused heartbeat and all public funds
are untouched.

## Reproducible saved evidence

- [Offline independent wire/event verification](VERIFICATION.json), produced by
  [verify_saved.py](verify_saved.py):179immutable local rows, all6send/receipt
  payloads and both actual core events reconcile. This verifier performs no RPC.
- [Final execution](EXECUTION02.json):53.89seconds, successful return, exact source
  identities and process supervisor. [Failed execution](EXECUTION01.json) retained.
- [Archive manifest](EVIDENCE_MANIFEST.json):62members,6,144,859bytes,
  SHA256 `1bc0e50a93d6734b48351dc98c27c630b4266de738bba4653896c7aeae278b78`.
  Every member's exact length/hash was independently checked after packaging.
- [Runner](run_swap.py), [typed fixture](SwapCallerFixture.sol), report-only
  [node driver](driver_base.py), [authenticated cache importer](warm_cache.py)
  and [process supervisor](supervise.py) retain source-scoped execution copies
  inside both attempts. Fixture-only compilation uses0.8.26/Cancun/viaIR with
  the existing optimizer profile; production objects are reused unchanged.

Source publication is not deployment, adoption or production approval.
