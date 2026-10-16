# Project Todo

**Reviewed 2026-10-16 | Contracts undeployed | Not approved for production**

The central task list for the whole PoPL project. There is no Todo page on the public website.

**15 To do | 14 In progress | 9 Implemented locally**

Implemented means built and locally checked, not deployed or independently audited. This list includes the current local development candidate; some code changes still await their own publication. Publishing this checklist does not publish or qualify that code.

[Detailed implementation and evidence](docs/IMPLEMENTATION_STATUS.md) | [Production release gates](docs/RELEASE_CHECKLIST.md) | [Update procedure](docs/TODO_WORKFLOW.md)

## Smart contracts

Custody, ownership and reward accounting.

- [ ] **Qualify the selected Robinhood pool** - In progress. The native ETH / Pons adapter and ETH / ZZZ Entry fork tests pass. Independent venue, wrapper and gas review remain.
- [ ] **Qualify ETH, ZZZ, USDG & USDC inputs** - In progress. Asset controls and entry logic exist. Verify actual routes and feeds; USDC still needs a reviewed, funded route.
- [ ] **Fair random assignment at mint** - In progress. The fixed artwork draw is implemented. Connect and qualify live verifiable randomness; no new images are needed.
- [x] **Minting, activation & NFT ownership** - Implemented. 1,000-NFT cap, 0.05 ETH mint and $100 gross-value activation with at least 99% deployed as LP. Rights follow the NFT.
- [x] **LP fees & separate royalty shares** - Implemented. 80 / 10 / 5 / 5 funded LP allocation with documented raw-unit dust settlement; equal collective shares. Actual royalties go to active NFTs at x1 / x2 / x3, separately from LP shares.
- [x] **Shared LP, maintenance & custody controls** - Implemented. One shared LP per pool/strategy serves many NFTs. The local four-historical-bucket safety bound, permanent allocations, pool-level upkeep, timelocks, parking and guarded resumption are implemented.

## Backend

The data and services behind the app.

- [ ] **Build live fee history & USD values** - To do. Index earned fees and reviewed token prices. Keep revenue received, available rewards and past claims distinct.
- [ ] **Host and monitor the API & indexer** - To do. A bounded read-only RPC compatibility probe exists. Pinax passed its initial checks; the documented public endpoint returned HTTP 403 from this environment. Qualify a second provider, production hosting, backfills, reorgs and external alerts.
- [ ] **Complete activation & top-up quotes** - In progress. Conversion quoting exists. Finish the full route into LP with one 1% execution-loss limit and gas shown separately.
- [x] **Confirmed balances & ownership API** - Implemented. Read NFT ownership and funded balances; reconstruct cumulative claims from complete confirmed history.
- [x] **Prepare unsigned mint & claim requests** - Implemented. Validate and simulate 0.05 ETH mints and up to 32 LP / royalty claim operations. Signing stays in the wallet.

## Frontend

What holders see and use.

- [ ] **Connect real wallet transactions** - To do. Wire minting, activation, LP additions and claims to reviewed deployed contracts.
- [ ] **Show actual holdings & claimable fees** - To do. Replace sample positions with wallet ownership, attached LP and separate LP / royalty balances.
- [ ] **Handle the complete transaction journey** - To do. Show gas, approvals, confirmation, rejection and recovery when an account, network or receipt changes.
- [ ] **Connect live history & cumulative claims** - To do. Display verified 24-hour / all-time fees and lifetime claimed totals, including royalties.
- [ ] **Show execution-time rights when buying an NFT** - To do. Refresh accrued balances and explain that the buyer receives what remains unclaimed at transfer. A seller can claim before the sale; do not promise a minimum balance from an earlier listing snapshot.
- [x] **Collection, artwork & portfolio preview** - Implemented. Browse designs, explore positions, and simulate minting, activation and both reward claims.

## Testing & qualification

Three required testing layers, with source-bound evidence.

- [ ] **Robinhood Testnet end-to-end rehearsal** - To do. Exercise wallet flows, the website, keeper operations and deployment with explicit records of unavailable or mocked dependencies.
- [ ] **Independent audit and release approval** - To do. Complete an external audit, remediation, gas/strategy review and final operating/configuration sign-off before any real funds.
- [ ] **Robinhood mainnet-fork qualification** - In progress. Actual selected-pool cases pass. Qualify production price feeds, full activation routes and real-service assumptions; synthetic calibration and mock authorities do not close those gates.
- [x] **Local contract and integration tests** - Implemented. Minting, activation, reward accounting, royalties, transfers and security cases have local checks. Each new change still needs fresh source-bound evidence.
- [x] **Verify NFT economic rights at full collection size** - Implemented. Internal ownership, 1,000-NFT payouts, buyback rollback and dual-ledger invariants verified: 531 offline Solidity passes, two intentional fork setup skips; extended rights invariants completed 65,536 calls. This closes the scoped local verification task, not independent audit or production qualification.

## Security & audit

Seven audit workstreams. Local checks are partial evidence; independent review and release sign-off remain open. See [the security audit plan](docs/SECURITY_AUDIT_PLAN.md) for acceptance criteria and priorities.

- [ ] **Whole-protocol recovery & canonical chain loss** - To do. Decide before sealing how to handle permanent home-chain loss, lost governance keys and unusable critical contracts. LP migration alone leaves canonical NFT ownership and reward ledgers at home. A full identity/liability migration needs an audited snapshot/finality, duplicate-prevention, in-flight claims and old-chain resurrection policy; it is not implemented.
- [ ] **Governance, permissions & sealing** - In progress. Audit every role, timelock, configuration and external-module trust boundary for a path around nonredeemable custody. Prove sealed bindings stay fixed and supported asset/feed/route/parameter changes remain bounded; review malicious destinations, lost keys and emergency powers.
- [ ] **Shared LP accounting & economic manipulation** - In progress. Verify 1,000 independent NFT share accounts through deposits, top-ups, compounding, rebalancing and migrations. Extend local conservation and gas evidence with adversarial prices, donation/front-running, dilution, rounding and multi-asset economic tests on qualified venues.
- [ ] **Ownership, claims & allocation rules** - In progress. Verify all unclaimed balances and fractions follow the NFT, including transfer/claim ordering, callbacks, operators and pending receipt synchronization. Preserve fixed 80/10/5/5 with documented dust and separate funded rarity royalties. Assess configurable splits against practical benefit and added governance risk before any proposal; no percentage setter is implemented or authorized.
- [ ] **Oracles, keepers, strategies & MEV** - In progress. Test compromised keepers, stale/manipulated prices, repeated rebalances, unfavorable swaps and sandwich/MEV costs. Qualify execution bounds, cooldowns, fee/gas budgets and outage policies with actual venues; access control alone does not prevent economic loss or impermanent loss.
- [ ] **External dependencies & receipt backing** - In progress. Review Uniswap v4, Pons, creator payments, tokens/wrappers, oracles, randomness and future bridges for upgrades, compromise, outages and unexpected behavior. Reconcile every asset liability to actual receipts; test quarantine, duplicate/delayed funding, token failure and provider/destination change.
- [ ] **Cross-contract & infrastructure audit** - In progress. Audit complete transaction paths and failure rollback across contracts, frontend, API/indexer, deployment, keys and keeper services. Rehearse reorgs, replay, stale or compromised data, wrong-chain signing, RPC failure, restore/rotation and monitoring. Independent review and operational sign-off remain open.

## Launch & operations

Decisions and rehearsals before real funds.

- [ ] **Select authorities & price services** - To do. Confirm governance, guardian, keeper and mint-recipient addresses, plus reliable USD pricing and outage policies.
- [ ] **Finalize creator revenue-sharing terms** - To do. Agree the fee basis, liquidity-share measurement, payout asset, frequency and authorized payer. Only actual receipts fund rewards.
- [ ] **Approve reward-token liveness and dust economics** - To do. Review admitted token upgrade, blacklist, rebase and transfer behavior. A broken royalty token can stop new activations; sub-20-raw-unit owner dust is bounded per settlement, not cumulatively. Qualify every asset before admission.
- [ ] **Publish artwork & operate metadata refresh** - In progress. The IPFS upload bundle and refresh watcher are prepared. Pin the files, verify the CID and test marketplace updates.
- [ ] **Harden keeper recovery and monitoring** - In progress. Recovery guards, read-only preflight/health checks and exclusive snapshots are implemented. Isolated server staging and read-only off-host monitoring are operating; desktop availability limits that monitor. Production RPC/fees, independent alerts and review remain open.
- [ ] **Rehearse keeper outage & server recovery** - In progress. 209 Ubuntu safety tests and 14 process rehearsals pass; the same 14 scenarios pass under the isolated server account. Actual systemd crash/restart and off-host snapshot round-trip restore passed. Sustained soak, physical host loss and governance key rotation remain open.

## Future migration

A separate phase. Disabled at initial launch.

- [ ] **Reserve destination capacity** - To do. Reserve space before liquidity travels, including concurrent arrivals, returns and recovery if delivery is delayed.
- [ ] **Qualify bridges & remote compounding** - To do. Review real transport providers, backing and repeated migrations; implement funded compounding when LP stays on another chain.
- [x] **Governed migration framework** - Implemented. Timelocked approval can onboard reviewed future EVM chains and pools while preserving NFT allocations.

---

Generated from [the task ledger](docs/project-todo.json). Update that ledger, then run `python scripts/sync-project-todo.py`; use `--check` to detect stale generated content.

Snapshot SHA-256: `88ad8cf07514548847e5d51402b7db3d4c214a6f0269b7f70e8d4f9a064c1afd`.
