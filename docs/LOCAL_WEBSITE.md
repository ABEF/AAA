# Existing website connected to disposable contracts

This guide records the historical pre-native/pricing-V2 Anvil `/app/` fixture.
Its mock assets, 1% guard, calldata and journals belong to that exact profile.
Fresh current-artifact launcher startup is blocked; the fresh accounting4
candidate accepts ETH/fixed ZZZ and defaults to2% contribution loss. The later
accounting3 local/API profile also remains historical. Do not relabel or reset an
existing fixture to match it. See [current compatibility](LOCAL_API_REHEARSAL.md#current-compatibility-boundary).
No URL or port in this history establishes a currently running service.

**Browser-wallet option (2026-10-20):** open the local mount with the exact
`?wallet=browser` query to use independent EIP-1193 signing and the separate
unsigned/receipt-observation path. Read [setup, approvals and recovery](BROWSER_WALLET.md)
before testing. Only disposable chain 31337 is enabled; public hosting remains
a simulation. The ordinary `/app/` route described below keeps the launcher-owned
local wallets. Do not mix their recovery records or resend a browser transaction
through the local signer.

The original website now has an explicit **local contract mode** at
`http://127.0.0.1:8890/app/#my-nfts` when served by the
[local launcher](LOCAL_TEST_STACK.md). The port follows `--port`. Normal static
hosting still runs the existing simulation. No public deployment is enabled.

## Start and use

Start `scripts/local-stack.py` with the paths in the local setup guide and the
website checkout as `--website`. Open `/app/` on that same loopback origin.
The launcher serves only the website's public files and assets, not repository
configuration. The root `/` retains the separate operator test panel for funding
fees and exercising a local rebalance. Never expose this server to the Internet.

1. Choose **Test wallet A** or **Test wallet B** using the website's wallet button. These are
   disposable unlocked accounts on the launcher's own Anvil child, not a browser
   extension or a production signer. Refresh first if the service restarted.
2. My NFTs and Collection read confirmed ownership and `NFT.currentLPValue`.
   Display labels use mint ordinals; full uint256 identity strings remain in
   details and all transactions. Artwork uses the actual revealed palette,
   pattern and rarity plus the contract's current-value evolution.
3. Mint costs 0.05 **test** ETH. The core draws one unused inventory entry;
   the local operator fulfills its original mock randomness request. The art
   explorer does not choose mint traits. The interactive fixture caps minting
   at 20, while the unmodified NFT supply cap is 1,000.
4. This fixture activates with exactly 100 TEST-1 and grows LP with whole 5–99,999
   units. TEST-1 is a local pair member marked at mock $1. If allowance is
   insufficient, review an exact approval first; approval adds no LP. After its
   confirmation, prepare and explicitly confirm a fresh complete Entry review.
   This historical contract requires at least 99% marginal
   deployed LP; gas is shown separately. This does not qualify a public swap route.
5. Claim LP fees and royalties together for one NFT, or review a wallet batch
   of at most ten NFTs / 32 currency operations. Larger portfolios require a
   separate confirmation for the next batch. Transfers move the NFT and its
   unclaimed rights to the other explicitly displayed local account.

The A/B transfer control rehearses ownership accounting only. This website is not
a marketplace; secondary sales happen on external marketplaces such as OpenSea.
The old Holder/Buyer labels were fixture account names, not buying/selling flows.

## What the numbers mean

| Display | Source and boundary |
| --- | --- |
| LP attached | Confirmed current on-chain USD mark, including attributed idle/compound, not cumulative contributions. |
| NFT LP fees earned, 24h/all time | Actual individual plus equal-collective processed earnings, valued at today's configured prices. Detail expands both components. |
| Collection fees | Actual processed collection revenue, before the 80/10/5/5 allocation. No synthetic seven-day chart or assumed trading volume. |
| LP fees to claim | Exact combined contract claimable balance, per currency. It is not a guessed split of unsettled individual and collective components. |
| Royalties earned / claimable | Separate raw currency amounts. ETH has no reviewed USD feed in this fixture and is not assigned an invented USD value. |
| Royalty weight badge | Fixed revealed rarity multiplier: Commun ×1, Rare ×2, Legendary ×3. Grayed while dormant; Unrevealed before traits are known. This is separate from effective accounting weight, which remains zero before activation. |
| Previously claimed | All actual LP and royalty payouts in the configured lifetime history. Transfers, conversions and claims do not count again as earnings. |

Dormant cards/details omit claims, earned-fee history, royalties and previously
claimed amounts. Activation, traits and attached LP remain visible. Activated
cards have separate **Claim** and **Grow attached LP** buttons; the claim action
requires funded balances. Sticky activation controls eligibility even when current
market value downgrades the artwork.

The session handshake supplies the two wallet addresses without waiting for the
portfolio. Selection survives navigation and soft reload in this tab's session
storage, scoped to the exact disposable deployment token. Disconnect is saved;
a new deployment requires selection again. No signer or key is stored.

During refresh, cards retain only last-confirmed identity/artwork, labeled as
updating, while financial values and actions wait for a fresh snapshot. A confirmed
evolution change crossfades the old image to the loaded new one; reduced-motion
preferences remove the animation. Rarity and palettes come from confirmed traits,
never an optimistic contribution estimate. Failed reads show unavailable balances
and retain a clearly labeled old artwork, never an enabled old position.

An API failure clears financial projections and disables new confirmations;
example holdings are never substituted. The default public demo remains separate
and retains its v7 simulation storage. The local read scope still inherits the
existing fixture's mock venue, prices, randomness and one-block confirmation.

## Confirmation and recovery protocol

`POST /prepare` uses the same strict Host, Origin, session token, JSON and serial
work checks as `/action`. It accepts only typed holder actions: `mint`, `activate`,
`increase`, `claim`, `claim_all`, `transfer`, with one of two local accounts.
No caller-supplied destination or calldata is accepted. It simulates and estimates
the exact step and stores at most 32 outstanding confirmations for 60 seconds.
Activation approval also checks lifecycle, owner and balance first.

Confirmation calls `/action` with the existing durable operation ID/revision
envelope and `payload = {action: "execute", account, draft_id}`. Account, revision,
wall-clock and chain-clock expiry, ownership, fresh simulation and the accepted
gas/price ceiling are checked before submission. A changed gas requirement needs
a new confirmation; a consumed draft cannot execute twice. Exact calldata and
gas limits are retained. Mint's mock callback/finalization is an explicitly local
operator fixture action after the holder transaction.

The browser saves the pending operation in session storage **before** sending.
If storage is unavailable, nothing is sent. After response loss, Refresh submits
only that identical ID and inputs to obtain the recorded outcome. Failed or
partial operations retain receipt hashes. An uncertain submission blocks new
actions; inspect external `operations.json`, `submissions.json`, `receipts.json`
and `errors.log`, then restart the disposable chain if required. A new launcher
session discards old pending intent and wallet selection without replaying it.
Closing/cancelling a confirmation sends nothing. Account or route changes discard
the confirmation. A successful approval can remain after a cancelled LP step.

Overlapping refreshes in one client share a request. Only the explicit local busy
409 from `GET /state` retries (30 attempts maximum, capped backoff, within the
90-second request deadline). Unsigned `POST /prepare` also retries only this exact
busy response, which the server returns before preparation begins. Each retry
checks the selected account and client state; busy waiting creates no draft; final-attempt processing time counts against its expiry.
`POST /action`, lost responses, accounting failures and other errors do not
auto-retry. A confirmed transaction followed by a read failure stays **confirmed**;
refresh its balances instead of creating a new transaction. Abandoned browser
connections are closed without attempting a second HTTP response.

## Concurrent users

The disposable launcher deliberately serializes its shared indexer and mutations.
Two browsers can inspect/select their own accounts. Typed wallet reviews bind
sender nonces and exact saved drafts; unrelated-wallet revision changes no longer
invalidate them. Same-wallet nonce changes, expired or invalid execution still
require fresh review. Ownership, simulation and operation-ID checks remain
enforced. Legacy operator actions retain global revision checks. This remains
a serialized disposable launcher, not a production multi-user server.

Production must keep signing in each user's wallet, serve bounded independent
reads, and revalidate quotes/ownership immediately before submission. Qualify
simultaneous users contributing to the shared pool, claiming independently, and
transferring/claiming the same NFT; stale quotes, nonce replacement, provider
failure and peak-load rate limits must not create duplicate or misattributed
actions. These remain acceptance criteria in the central Todo, not a completed
load rehearsal or permission to expose this local signer.

The static `/app/` document permits inline **styles** for the established artwork
renderer; scripts and connections remain same-origin, framing/forms are blocked.
No general file browser or RPC forwarding endpoint is provided.

## Scope and verification

[Scoped verification](../reports/local-website/VERIFICATION.md) records focused
client/server tests, browser checks and the confirmation integration campaign.
Production Solidity is unchanged; its source-bound artifacts are reused.

Production browser-wallet signing, network switching, real receipt replacement /
reorg behavior, full production activation routing, hosted services and independent
review remain open. The local adapter must never be reused as a public signer.
Stopping/restarting follows the local-stack runbook; it creates a new deployment,
not a persistent chain recovery. No contract or governance configuration changed.

### Activation review feedback and targeted artwork status

Contribution validation, preparation progress and errors appear beside the review
button inside the NFT dialog. Invalid amounts or missing acknowledgement explain
what to fix; preparation disables the form and labels the button as preparing.
After a confirmed approval, the acknowledgement carries to the LP step only for
the same deployment, wallet, NFT and exact amount. Changing the amount clears it.
Approval and Entry still require separate explicit transaction confirmations.

Only the NFT receiving a confirmed activation/top-up shows the artwork Updating
badge during balance refresh. Other artwork stays visible without that badge;
stale financial values/actions still wait for the confirmed portfolio snapshot.
A plain refresh or token approval does not label every artwork as changing.

## Local contribution flow - 2026-10-20

The local website fixes activation at $100 of mock-priced input; growing attached
LP remains separate, starting at $5. Inputs are token quantities with an explicit
$1 mock USD estimate, not a live market quote. After exact approval, the next LP
review opens automatically but still requires explicit confirmation. The window
stays open during receipt and balance reads; artwork follows confirmed LP only.

The local wallet and matching historical unsigned preparation replace an insufficient
allowance with the exact requested amount, never an automatic zero reset or unlimited
approval. Direct approval must simulate successfully; reset-only tokens are
unsupported by the two-transaction flow. An already sufficient allowance is reused.
Governed Entry pulls only from its authenticated caller. Native ETH needs no wallet
approval and is wrapped inside this historical Entry for its compatible fixture.
The current accounting 3 native-ETH candidate has a different settlement/profile;
these wrapper instructions do not apply to it.

Use the separate launcher profile `--named-assets --native-input` to test native
ETH. It substitutes `LocalNativeRegistry` admission on chain 31337 and retains the
unmodified production Entry/Vault/budget/ledger implementations above the mock
venue. This is not qualification of Robinhood venue pins or real market prices.
The older WETH-pool session cannot support atomic native input: its three-step
wrap flow is rejected, not hidden. Keep that session intact when starting another
profile. Neither the public website nor public contracts were deployed.

The read clock now samples actual chain time at initial/final freshness boundaries
and advances monotonically between them. Budget checkpoints no longer perform a
fresh RPC per check. Missing/stale data still fails closed. Do not infer ETH/USD
prices from the local input feed; missing history prices remain unavailable.

Production Entry still enforces a $100 minimum, not an exact-$100 upper bound.
The fixed activation amount is a local UI/API product rule; real quote rounding
and price-drift policy must be resolved before asserting contract-level equality.
See [scoped verification](../reports/local-contribution-flow/VERIFICATION.md).

## Independent local wallet confirmations - 2026-10-20

Typed local wallet drafts now pin the sender nonce. Another wallet's transaction
no longer invalidates an otherwise valid review. The server still binds the exact
saved draft/revision/account and freshly simulates unchanged calldata within the
reviewed gas ceiling; same-wallet nonce changes, expiry, owner changes and invalid
execution still require fresh review. Legacy operator actions keep global revision
checks. This supersedes the earlier rule rejecting every cross-wallet revision.

For the historical 8898 upgrade, both browsers needed reloading. Old unsigned
reviews are invalidated: review afresh. Recover saved pending outcomes by the same
operation ID before starting new work; never clear storage to bypass uncertainty.
No new authority or contract function is introduced. Cancel an unsigned review to
stop; restoring old service code restores the global conflict behavior, not prior
chain state. Verify receipts and confirmed ownership/LP after execution. Never
reset Anvil to resolve a browser confirmation issue. The guarded external recovery
script preserves existing contracts and positions; ordinary launcher restart does
not promise persistence. The record's 8896/8898 status is historical; inspect the
actual manifest/process instead of assuming either is running or upgraded.
[70 distinct Python cases and two actual local mints](../reports/local-wallet-concurrency/NONCE_VERIFICATION.md).

## Capacity decision and manual acceptance - 2026-10-20

The user reports the six local two-wallet flows passed; see the
[manual acceptance record](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md).
This report does not change operator functions, roles, configuration, limits or
stop/restart procedures. The dedicated 10/25/100-user load campaign is deferred;
do not run it automatically or raise worker limits as part of this decision.
Continue using bounded API admission, independent user-wallet signing and saved
transaction recovery for the production integration. The shared local signer
and lock remain test-only. Production capacity is unverified, and accepting real
funds still requires the outstanding dependency and release qualification.
