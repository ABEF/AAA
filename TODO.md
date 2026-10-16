# Project Todo

**Reviewed 2026-10-16 | Contracts undeployed | Not approved for production**

The central task list for the whole PoPL project. There is no Todo page on the public website.

**13 To do | 7 In progress | 8 Implemented locally**

Implemented means built and locally checked, not deployed or independently audited. This list includes the current local development candidate; some code changes still await their own publication. Publishing this checklist does not publish or qualify that code.

[Detailed implementation and evidence](docs/IMPLEMENTATION_STATUS.md) | [Production release gates](docs/RELEASE_CHECKLIST.md) | [Update procedure](docs/TODO_WORKFLOW.md)

## Frontend

What holders see and use.

- [ ] **Connect real wallet transactions** - To do. Wire minting, activation, LP additions and claims to reviewed deployed contracts.
- [ ] **Show actual holdings & claimable fees** - To do. Replace sample positions with wallet ownership, attached LP and separate LP / royalty balances.
- [ ] **Handle the complete transaction journey** - To do. Show gas, approvals, confirmation, rejection and recovery when an account, network or receipt changes.
- [ ] **Connect live history & cumulative claims** - To do. Display verified 24-hour / all-time fees and lifetime claimed totals, including royalties.
- [x] **Collection, artwork & portfolio preview** - Implemented. Browse designs, explore positions, and simulate minting, activation and both reward claims.

## Backend

The data and services behind the app.

- [ ] **Build live fee history & USD values** - To do. Index earned fees and reviewed token prices. Keep revenue received, available rewards and past claims distinct.
- [ ] **Host and monitor the API & indexer** - To do. Qualify RPC providers, backfills, chain reorganizations, request limits, backups and service alerts.
- [ ] **Complete activation & top-up quotes** - In progress. Conversion quoting exists. Finish the full route into LP with one 1% execution-loss limit and gas shown separately.
- [x] **Confirmed balances & ownership API** - Implemented. Read NFT ownership and funded balances; reconstruct cumulative claims from complete confirmed history.
- [x] **Prepare unsigned mint & claim requests** - Implemented. Validate and simulate 0.05 ETH mints and up to 32 LP / royalty claim operations. Signing stays in the wallet.

## Smart contracts

Custody, ownership and reward accounting.

- [ ] **Qualify the selected Robinhood pool** - In progress. The native ETH / Pons adapter and ETH / ZZZ Entry fork tests pass. Independent venue, wrapper and gas review remain.
- [ ] **Qualify ETH, ZZZ, USDG & USDC inputs** - In progress. Asset controls and entry logic exist. Verify actual routes and feeds; USDC still needs a reviewed, funded route.
- [ ] **Fair random assignment at mint** - In progress. The fixed artwork draw is implemented. Connect and qualify live verifiable randomness; no new images are needed.
- [x] **Minting, activation & NFT ownership** - Implemented. 1,000-NFT cap, 0.05 ETH mint and $100 gross-value activation with at least 99% deployed as LP. Rights follow the NFT.
- [x] **LP fees & separate royalty shares** - Implemented. 80 / 10 / 5 / 5 LP allocation; equal collective shares. Actual royalties go to active NFTs at Ãƒâ€”1 / Ãƒâ€”2 / Ãƒâ€”3.
- [x] **Shared LP, maintenance & custody controls** - Implemented. Pool-level upkeep, permanent NFT allocations, timelocked controls, paused parking and guarded resumption.

## Testing & security

Three required testing layers, then independent review.

- [ ] **Robinhood Testnet end-to-end rehearsal** - To do. Exercise wallet flows, the website, keeper operations and deployment with explicit records of unavailable or mocked dependencies.
- [ ] **Independent audit and release approval** - To do. Complete an external audit, remediation, gas/strategy review and final operating/configuration sign-off before any real funds.
- [ ] **Robinhood mainnet-fork qualification** - In progress. Actual selected-pool cases pass. Qualify production price feeds, full activation routes and real-service assumptions; synthetic calibration and mock authorities do not close those gates.
- [x] **Local contract and integration tests** - Implemented. Minting, activation, reward accounting, royalties, transfers and security cases have local checks. Each new change still needs fresh source-bound evidence.

## Launch & operations

Decisions and rehearsals before real funds.

- [ ] **Select authorities & price services** - To do. Confirm governance, guardian, keeper and mint-recipient addresses, plus reliable USD pricing and outage policies.
- [ ] **Finalize creator revenue-sharing terms** - To do. Agree the fee basis, liquidity-share measurement, payout asset, frequency and authorized payer. Only actual receipts fund rewards.
- [ ] **Rehearse keeper outage & server recovery** - To do. Test several days offline, restore backups on a new server, reconcile pending transactions and budgets, and rotate a lost keeper key safely.
- [ ] **Publish artwork & operate metadata refresh** - In progress. The IPFS upload bundle and refresh watcher are prepared. Pin the files, verify the CID and test marketplace updates.
- [ ] **Harden keeper recovery and monitoring** - In progress. Recovery guards, retry cooldowns and health logs are published; 183 keeper/RPC/state tests and service validation pass on Ubuntu. Real RPC/fee qualification, off-host alerts, recovery rehearsals and independent review remain.

## Future migration

A separate phase. Disabled at initial launch.

- [ ] **Reserve destination capacity** - To do. Reserve space before liquidity travels, including concurrent arrivals, returns and recovery if delivery is delayed.
- [ ] **Qualify bridges & remote compounding** - To do. Review real transport providers, backing and repeated migrations; implement funded compounding when LP stays on another chain.
- [x] **Governed migration framework** - Implemented. Timelocked approval can onboard reviewed future EVM chains and pools while preserving NFT allocations.

---

Generated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.

Snapshot SHA-256: `692d530f11637bbe64330a2237581dbe509058b4e3b2021abaaf312d2df9f7bf`.
