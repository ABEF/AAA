# Historical local browser test environment

This is the pre-native/pricing-V2 fixture guide. Fresh current-artifact startup
is blocked by `require_legacy_fixture_artifacts` before Anvil/deployment. Existing
chains, balances and journals retain their original profile. Do not relabel or
reset them. A historical fresh run needs a separately reviewed matching
source/artifact set; this is not an accounting3 or fresh accounting4 production rehearsal recipe.

The [launcher](../scripts/local-stack.py) starts its own loopback Anvil chain,
deploys and seals its matching historical core, seeds four NFTs, and connects the
confirmed read/earnings API and SQLite indexer to a separate local browser panel.
It does not deploy the public website. The panel borrows the website's existing
artwork. The [website itself](LOCAL_WEBSITE.md) is also mounted at `/app/`, using
confirmed local data and explicit per-step confirmations. Production extension
wallet signing and deployment qualification remain separate work.

## What is real and what is substituted

| Component | Local behavior |
| --- | --- |
| NFT, Vault, Entry, contribution/maintenance budgets, Strategy, reward ledgers, ClaimRouter, controller | The historical compiled candidate recorded by that run; hashes must match that reviewed artifact set, never a relabeled current build. |
| Shared LP custody boundary | `LocalDemoVenue` replaces LiquidityManager and Uniswap. Exact local ERC20 balances and recorded quantities; deterministic 1:1 swaps. This does not test Uniswap math, Pons, real liquidity or slippage. |
| Prices | Local, always-fresh $1 test-token feed. ETH royalties have no USD mark; the API reports unavailable USD. |
| Randomness | Existing MockVRF; no proof, subscription or provider qualification. The real finite NFT draw still runs. |
| Accounts | Two disposable holder/buyer accounts plus a local operator. Only this launcher-owned Anvil process accepts transactions. No private key, wallet environment variable or public RPC is used. |
| API/indexer | Current confirmed projections, real raw event ingestion and current-price earnings replay. One confirmation on a local chain is not production finality. |
| Timing | Rebalance advances local time by 601 seconds and changes the range through immediate governance. API freshness uses that same test-chain clock. No production keeper runs. |

Activation and top-ups use TEST-1, an admitted member of the local pair. The pool
now configures a $5 contribution floor; fixed contract guards separately require
$100 activation and $5 increases. The Entry enforces the original-source 99% deployed
LP rule. Exact token approval and the Entry transaction are separate receipts.
Network gas is separate in test ETH. No USDG/USDC/ZZZ public conversion route is
claimed. The browser fixture caps new minting at 20 for bounded interactive reads;
the actual NFT contract still has its 1,000 cap and 0.05 ETH mint price.

Optional earnings RPC errors are reported as unavailable history without dropping
otherwise confirmed core balances. Sanitized logs identify the affected scope;
terminal work budgets and core/lifecycle failures still fail closed. Dormant NFT
reads skip earnings replay. The source update does not patch an existing running
session or its contracts. Preserve wanted receipts, build matching artifacts and
start a separate fresh fixture to test the new [$5 guards](CONTRIBUTION_MINIMUMS.md).

## Start

Requirements: Python 3.11+, Foundry Anvil/Cast/Forge, the pinned Solidity toolchain
and installed repository dependencies. Run from the contract repository root.
These commands belong to the historical revision; compile only its matching
source/fixtures and preserve their bindings. Current artifacts intentionally fail
the compatibility check. A changed version flag is not a current
[development](DEVELOPMENT.md) stack:

```sh
forge build test/local/LocalDemoVenue.sol test/local/LocalInputFixtures.sol test/local/LocalNativeRegistry.sol test/mocks/MockVRF.sol --out /path/to/local-fixture-out --cache-path /path/to/local-fixture-cache
python scripts/local-stack.py --anvil /path/to/anvil --cast /path/to/cast --artifacts /path/to/reviewed-historical-core-out --fixture-artifacts /path/to/local-fixture-out --state /path/to/external-local-state --website /path/to/AAA-website --port 8890
```

Quote paths with spaces. Windows executables use `.exe`; `python3` can be used
on Unix. The launcher refuses stale compiler source bindings. It never silently
rebuilds or modifies production sources. `--state` receives a new unique session
directory, preserving earlier evidence. Open `http://127.0.0.1:8890` after the
launcher prints `OPEN`. The optional `--verify-only` checks deployment/read state
and shuts down its child instead of serving the panel.

## Use the panel

1. The Holder starts with one dormant, two Enhanced and one Singularity NFT.
   Artwork comes from the actual local reveal, rather than copied demo IDs.
2. Mint, then activate with 100 TEST-1. The new NFT has no older fee entitlement.
3. Add LP; the NFT keeps its allocation in the same shared position.
4. **Fund LP fees + royalties** transfers 100 TEST-1 to the venue and 0.01 test
   ETH to the royalty ledger, then processes them through the real contracts.
5. **Rebalance test LP** exercises a governed range change, cooldown and the
   actual Vault maintenance budget against the test venue.
6. Transfer an NFT to the Buyer, switch accounts and inspect its unclaimed
   balances. **Claim both** uses the existing unsigned preparation API and a
   fresh local simulation before submission; lifetime history accumulates.

Only typed actions are exposed. The host, same-origin header, JSON size and
per-session nonce are checked; there is no arbitrary RPC relay or recipient.
Action shapes are exact: canonical string IDs, whole 100..99,999 TEST-1 activation
amounts or 5..99,999 increases in the updated source,
and only the two local accounts. Wrong lifecycle, balance or owner is rejected
before approval. Later Entry checks can still fail after a successful approval.
All operations are serialized, including indexer writes. Concurrent economic
requests return a busy response rather than queue a second transaction. Twelve
HTTP workers, a five-second socket timeout and a 2,048-byte body ceiling bound
local request handling. Duplicate security headers/JSON keys are rejected. Read aggregation only
deduplicates exact block-hash-bound reads within one response; latest/header
checks are fresh. Pure runtime-byte hashes have a bounded cache, never an
address/state cache. This local convenience service is **not a production host**.

## Verification, stop and recovery

Run the focused browser-API journey against a **fresh** session:

```sh
python scripts/verify-local-stack.py --port 8890 --output /path/to/new-evidence.json
python -m unittest tests_python.test_local_stack tests_python.test_local_stack_edges
```

The journey changes only disposable local state. It verifies real receipts,
ownership, LP allocation, funded fees, no retroactive income, rebalancing,
combined claims and cumulative history. See [scoped evidence](../reports/local-stack/VERIFICATION.md).

Both `verify-local-stack.py` and `verify-local-website.py` now require a new
evidence output path. They exclusively reserve it before making any request to
the local lab, then write an `in_progress` marker. Existing files or symlinks
are refused before lab actions; success/failure replaces only that run's reserved
record. A crash or disk error can leave incomplete evidence: preserve it, inspect
actual local receipts/state, and choose a new path. Do not rerun a state-changing
journey merely to replace a missing success report. These tools remain historical
fixture verifiers, not a fresh4 launcher or production acceptance.

Stop with Ctrl+C in the launcher. A same-origin/session-authenticated
`POST /action` with `{"action":"stop"}` also stops this session and its owned
Anvil child. Restart with the same launch command to get a **new** disposable
deployment and fresh indexer; never reuse an old browser session token or API
configuration with the new deployment. Closing the browser alone does not stop
the services. No Windows startup task or recurring monitor is installed.

`deployment.json`, `api.json`, `indexer.json`, `receipts.json`, `submissions.json`,
`operations.json`, `errors.log` and
`running.json` remain in the external session directory. Failed operations may
leave a successful exact approval; inspect receipts and refresh before retrying.
A response failure after a successful transaction must not be treated as a
reverted transaction. The panel stores the pending operation in session storage;
**Refresh** resubmits the same operation ID to recover its saved outcome, never a
new economic action. Confirmed/failed outcomes include any completed transaction
hashes. Pending storage must succeed before the browser submits. A new server
session discards the old browser operation without replaying it.

The typed action protocol is `POST /action` with `operation_id` (32 lowercase hex
characters), `revision` (the latest `/state` revision) and `payload` (the typed
action/account/id/amount). Identical ID + inputs return the recorded outcome;
changed inputs under the same ID or an old revision under a new ID are rejected.
There is a hard 256-operation session limit, with no replay-record eviction.
The standalone authenticated stop payload is unchanged.

Transaction intent is saved before submission; the hash and receipt are saved
as they arrive, separately from fallible balance/history refresh. Files use
atomic replacement. If submission/receipt tracking or durable operation recording
becomes uncertain, new actions are blocked. Inspect the external records and
start a new **disposable** chain; there is no automatic resend or production
nonce-recovery claim. Do not expose the service beyond loopback. The lab does not resume persisted chain state after process
loss; evidence remains readable, but the next run deliberately starts fresh.

No public-chain contracts, production services, public website/server or the
user-paused staging monitor are changed. Production release remains NOT APPROVED.

The current 8892 session uses generic TEST-1/TEST-2 and native ETH royalties.
These labels are not production assets. Its token LP claims do not test ETH-only
payouts; see [the payout audit](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md).
Wallet A received 100,000 additional disposable input tokens on 2026-10-19 after
reporting insufficient funds, with its existing NFTs and rewards preserved.
Named asset fixtures, balance/faucet UX and complete source-to-ETH payout tests
remain under the central integration/settlement tasks.

## Named-input local rehearsal

Use `--named-assets` when starting a **separate fresh** launcher session. Compile
`test/local/LocalInputFixtures.sol` alongside the existing local venue and VRF.
Keep wanted older sessions running; do not reset their holdings or impersonate
public assets by relabeling TEST-1. The website selector shows ZZZ, USDG, USDC,
ETH. The four locally deployed symbols use disclosed $1 mock marks, not live
prices. USDG/USDC exercise six-decimal source admission and pinned typed mock
conversion. The local shared pair is ZZZ/WETH.

The named local ETH scenario has an explicit wrapping receipt, then exact WETH
approval and Entry receipts. Wrapping/approval do not add LP or activate the NFT.
It does **not** exercise production's atomic native-ETH selected-pool branch:
the real Registry restricts that branch to the reviewed Robinhood deployment.
Every ETH value is disposable Anvil ETH; the local launcher has no public RPC/key
option. The UI hides WETH as an input choice, retaining it internally. A legacy
session without an input manifest continues to identify its actual TEST-1 token
and cannot pretend to execute named routes.

Initial activation is $100; later additions are $5. Verify the exact selected
source, decimals, spender and allowance in the confirmation, then verify confirmed
on-chain LP increase. An earlier wrapped-input branch required an allowance reset;
that is not the later exact-replacement/native profile's two-transaction flow.
A sufficient allowance is reused. Historical wrappers retain ETH backing.
Successful conversion is not proof of public market liquidity, pricing, native
pool support or the still-open ETH-only LP payout path.

Stop a named session using its normal launcher stop procedure. Its chain is
disposable; starting again creates a new deployment/session and invalidates old
confirmations. There is no production operator/authority change in this UI/local
fixture work. No server update or paused-monitor restart is included.

## Local read and contribution update - 2026-10-20

A boundary-sampled monotonic clock removes per-check RPC overhead without dropping
initial/final freshness checks. The native fixture uses unchanged Entry for atomic
ETH; supported ERC20 uses exact replacement approval then Entry, with no automatic
reset. The UI retains confirmation continuity and fixes local activation at $100.
See [behavior and limits](LOCAL_WEBSITE.md#local-contribution-flow---2026-10-20) and
[scoped verification](../reports/local-contribution-flow/VERIFICATION.md).
Production venue/service qualification and fixed-$100 price/rounding policy remain open.

For the new atomic-ETH browser rehearsal, add `--named-assets --native-input`
and choose a separate port such as 8898 and a separate state directory.
