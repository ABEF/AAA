# Existing website connected to disposable contracts

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
4. Activate or add LP with whole 100–99,999 TEST-1. It is already one member of
   the local pair and its test feed marks it at $1. If allowance is insufficient,
   review an exact approval first. This does not activate or add LP. Reopen the
   NFT, retain/check the amount, acknowledge the commitment, then separately
   review the Entry transaction. The contract enforces at least 99% marginal
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
409 from `GET /state` retries (13 attempts maximum, capped backoff, within the
90-second request deadline). Writes, accounting failures and other errors do not
auto-retry. A confirmed transaction followed by a read failure stays **confirmed**;
refresh its balances instead of creating a new transaction. Abandoned browser
connections are closed without attempting a second HTTP response.

## Concurrent users

The disposable launcher deliberately serializes its shared indexer and mutations.
Two browsers can inspect/select their own accounts, but conflicting operations
must refresh/reprepare; this is not a production multi-user server. Exact revision,
ownership, simulation and operation-ID checks remain enforced.

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
