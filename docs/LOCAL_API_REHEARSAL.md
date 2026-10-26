# Local API and browser-wallet rehearsal

## Current compatibility boundary

The commands below describe the historical WETH/single-feed browser fixture.
Fresh `local-stack.py` and `local-api-stack.py` startup with current native/pricing-V2
artifacts is blocked before a state directory, Anvil process or deployment is
created. The old scaffold still assumes wrapper accounting, single-source feed
configuration and legacy unsigned-review traces; changing only its feed setter
would not produce a qualified V2 rehearsal.

Preserve any existing 8902 fixture's NFT/LP balances, journals and original build;
this document does not establish that it is currently running. Inspect its actual
process/manifest first. Do not rebuild it in place or relabel its history as
accounting-3. A fresh isolated native/routing/pricing-V2 lab needs coherent test
venue/accounting fixtures, explicitly correlated test-only dual feed mirrors,
current helper-phase configuration and a complete separate operating rehearsal.
Mock sources never establish independent production pricing. The browser signer
remains Anvil-only; no public signing or service change follows from this warning.

The historical stack ran its matching website profile against actual Anvil,
real API workers and its source-authenticated historical core artifacts. It uses
the unchanged local-only browser signer. No public RPC,
wallet private key or nonlocal signing option exists in the launcher.

## Start and verify

The following is a historical command shape, not a fresh-start recipe for the
current checkout. Use only independently reviewed matching historical
source/artifacts. Current native/pricing-V2 startup deliberately fails its
compatibility gate; do not weaken that gate to run these commands:

```sh
forge build test/local/LocalAPIVenue.sol test/local/LocalInputFixtures.sol test/local/LocalNativeRegistry.sol test/mocks/MockVRF.sol --out /external/fixture-out --cache-path /external/fixture-cache
python scripts/local-api-stack.py --anvil /path/to/anvil --cast /path/to/cast --artifacts /path/to/reviewed-historical-core-out --fixture-artifacts /external/fixture-out --state /external/new-api-runs --website /path/to/AAA-website --port 8902
```

Build the website first with `npm run build` from its own checkout. Quote paths
with spaces; Windows tools may end in `.exe`. All source pins must match; do not
weaken stale-artifact checks. Each start creates a new unique deployment. Existing
fixtures are not resumed or reset. The launcher's static mount is `/`, not `/app/`.
Its generated manifest overrides only `/deployment-config.js` on this loopback
server; the repository and public build retain `DEPLOYMENT = null`.

Read the new run's `running.json`: website URL, RPC URL, chain 31337, process IDs
and disposable account addresses. Configure the extension with this exact RPC
and select its disposable account. A previous network with the same chain ID but
different genesis will correctly fail validation. Do not use public funds or keys.
Connection/reads are unsigned; every transaction still requires explicit approval.

The Holder starts with 18 NFTs to exercise card and summary pagination (three
active positions, the rest dormant). The other local account is funded for a
fresh mint/activation journey. This does not change the public demo's four NFTs.

## What the historical rehearsal establishes

- Real mint, native Entry, exact ERC20 approval then fresh complete LP review,
  top-up and ETH claim execution through the actual preparation/trace validation.
- Canonical receipt/event/position checks and separate network gas. Approval
  alone adds no LP; claims change rewards without marking artwork pending.
- A confirmed transaction with a lagging/unavailable API retains its journal.
  Restore reads that same hash; never repeat approval/payment to fix the display.
- Read-only APIs remain bounded workers with admission limits. This local proxy
  accepts only literal-loopback Host and same-origin POST, bounded bodies, exact
  API paths and public build files. No arbitrary call, service control or signer
  is exposed by its HTTP layer.

The token/feed/venue/VRF contracts are **local substitutes**. LocalAPIVenue records
real token custody and exposes position-manager reads for the production trace
parser, but uses deterministic 1:1 math. Its conversion pools expose funded mock
reserve presence, not Uniswap liquidity math. LocalFeed is always fresh at $1,
including the explicitly configured native ETH mark. MockVRF reveals local mints
without a verifiable proof. None qualifies the selected hookless native pool,
actual routes/feeds, accounting 3 website or VRF.

## Full-wallet totals

`GET /v1/wallets/{address}/summary/{confirmed-block-number}/{offset}` returns at
most 16 holdings and chunk sums. Start at offset 0 using the verified inventory's
block. Follow `next_offset`; validate the inventory SHA-256, exact ordered IDs,
count, owner, NFT contract and identical canonical block on every response.
Recheck canonicality/freshness at completion. Only then display a total.

LP is the sum of `NFT.currentLPValue` at that block. Ready-to-claim ETH sums the
LP ledger (individual plus collective) and royalty ledger native balances. It
excludes unconverted source currencies and is not generated/lifetime revenue.
One missing value makes that complete metric unavailable while the independent
metric may remain available. There is no partial-total or zero fallback. Account
changes cancel the old aggregate, reset card pagination and clear previous totals.
Separate [wallet earnings](EARNINGS_HISTORY.md#current-holdings-totals) and
[collection reads](COLLECTION_READS.md) are implemented in matching reviewed
profiles. That later source support does not upgrade this historical fixture or
qualify the current accounting 3 website and real services.

## Stop, diagnose and restart

Stop the launcher with Ctrl+C. For background operation, first match the saved
PID, executable, command line and owned Anvil parent/child identities; stop only
those processes. Preserve the run directory, receipts and pending journals.
Restarting creates a fresh chain; never reconnect an old journal to a new genesis.
The local chain itself is disposable, not a durable production service.

`maintenance-error.json` means local miner/reveal/indexer upkeep stopped. Diagnose
the recorded error type and actual on-chain receipt before retrying. No automatic
operator transaction retry occurs after an uncertain failure. APIs eventually
reject stale/unindexed state. No startup service or scheduled monitor is installed.

For a failed/expired total, refresh all chunks from a new verified inventory;
never splice old and new chunks. For transaction recovery follow
[the coordinator procedure](DEPLOYMENT_WEBSITE.md#local-api-wallet-rehearsal).
Actual extension acceptance, Linux/TLS/provider operation, production pricing,
routes, capacity and independent review remain release requirements. See
[scoped evidence](../reports/api-chain-rehearsal/VERIFICATION.md).
