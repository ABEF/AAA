# ZZZ Protocol v0.2 — reviewed implementation candidate

**DO NOT DEPLOY WITH REAL FUNDS. Solidity compilation and EVM execution were not possible in the delivery environment. This is a substantial source rewrite with a self-review, not an independent audit or production approval.**

All **16 requested Solidity modules** are retained. The original disabled liquidity/bridge skeletons have been replaced with typed Uniswap integration source, explicit custody/reward accounting and a constrained migration state machine. There is a real Python keeper and SQLite indexer, not just TypeScript placeholders.

## Evidence delivered

| Check | Result |
|---|---|
| Python tests actually executed | **84 passed, 0 failed, 0 skipped** |
| Off-chain implementation tests | 66 tests: codec, RPC, persistence, keeper, indexer |
| Separate accounting/mathematical specification tests | 18 tests; **not Solidity execution** |
| Project-source consistency checks | 20 Solidity files checked; no missing local imports or unbalanced delimiters detected |
| Solidity/Foundry tests written | **70 test functions**, including fuzz entrypoints; **not compiled or run** |
| Solidity compilation, contract bytecode size, fork tests, Slither | **NOT RUN / BLOCKED** |
| Real transaction signing, Uniswap transactions, bridge-provider integration | **NOT RUN** |
| Independent external audit | **NOT PERFORMED** |

See `reports/python-tests.json`, `reports/python-tests.log`, `reports/verify-attempt.log`, and `docs/AUDIT.md`. Package installation failed with `EAI_AGAIN`; `forge` and `solc` were absent. No passing compiler or EVM report has been fabricated.

## Architecture

```text
CANONICAL CHAIN
User -> ZZZVault -> ZZZLiquidityManager -> existing compatible Uniswap v4 pool
          |                    |
          | owns LP NFTs       | typed mint / increase / collect / close / swap
          +-> ZZZNFT (user owns transferable economic rights)
          +-> ZZZFeeController -> ZZZRewards <-> ZZZPower
                     |          50% individual + 30% collective
                     +-> 10% compound reserve -> vault, via ZZZCompounder/ZZZStrategy
                     +-> 10% buyback reserve -> ZZZBuyback

ZZZKeeper -> narrowly authorized entrypoints; no permission to redeem principal
ZZZIndexer -> confirmed events and reorg-aware SQLite data; not an authority

MIGRATION
ZZZMigration -> source vault closes LP -> ZZZBridgeAdapter
   -> separately supplied, reviewed transport -> destination adapter
   -> ZZZMigrationReceiver -> satellite vault INBOUND custody -> activate LP
   -> authenticated acknowledgement -> source marks economic position REMOTE
Remote 80% NFT rewards bridge to the canonical chain for accounting and claims.
```

The hookless adapter accepts conventional ERC20/ERC20, static-fee, no-hook pools. **Use WETH, not native ETH.** It does not manage arbitrary hooks or fee-on-transfer/rebasing assets.

## Explicit policy choices in this candidate

These are implementation choices requiring product approval, not assumptions silently presented as settled requirements.

- One **canonical NFT chain**. Satellite vaults cannot accept new user deposits/mint a second collection. One economic NFT normally has one active underlying LP NFT, replaced during rebalancing.
- Principal is non-redeemable. It can be temporarily idle, swapped, rebalanced and bridged; neither token quantities nor dollar value are guaranteed.
- Deposits/top-ups are balanced before placement. After placement, at least **95% of the position's oracle-valued assets must be deployed**; excess idle capital cannot silently receive Power while mostly undeployed.
- **Power = lifetime user-contribution USD value at deposit**, 18 decimals. Compounding/price appreciation do not add Power, and market losses do not subtract it. Power remains eligible while principal is remote/in flight.
- Collective rewards use Power at **fee settlement/collection time**, not retroactive per-swap historical weights. Checkpoints protect already-published reward indexes, not all previously uncollected pool fees. This distinction needs explicit approval.
- Claims follow the NFT's current owner, including unclaimed balances. Approved NFT operators cannot directly claim rewards.
- At most **32 reward assets** on a deployment. Large meme-token support requires sharding or a different checkpoint design.
- Each pool chooses its range; configure `rangeBps = 1000` for approximately **+-10%**, rounded outward to valid ticks. A keeper polls every 600 seconds; rebalancing requires a deviation trigger and cooldown.
- Buyback supports direct token/ZZZ pools, or burning fees already denominated in ZZZ. **Multi-hop buybacks are not implemented.** A supported `burn()` must actually reduce the configured token's supply; wrapped-token global burn semantics need separate review.
- Migration is **one hop from the canonical chain to a configured satellite**. Return/onward migration and cross-chain user top-ups are not implemented.
- Module addresses and migration route identities are immutable after `seal()`. Routes can be disabled/re-enabled, but **arbitrary new chains/destinations cannot be appended later** to this deployment.
- `ZZZBridgeAdapter` is a typed boundary for `IZZZTransport`, **not a ready-made CCIP/LayerZero/etc. integration**. A reviewed bridge-specific transport is still required.

## Repository

| Path | Content |
|---|---|
| `src/` | 16 modules, shared interfaces/types and token safety helper |
| `test/` | Foundry tests and explicitly test-only mocks |
| `keeper/`, `indexer/`, `zzz_ops/` | Python 3.11+ off-chain services and utilities |
| `tests_python/` | Runnable off-chain and mathematical specification tests |
| `script/DeployCore.s.sol` | Local-only deployment template; does not seal/open deposits |
| `scripts/` | Dependency setup, test runner and narrow source checks |
| `docs/AUDIT.md` | Findings, source changes, limitations and open risks |
| `docs/OPERATIONS.md` | Keeper, indexer, governance and migration procedures |
| `docs/RELEASE_CHECKLIST.md` | Mandatory blockers before any live deployment |
| `reports/` | Actual test evidence and blocked-toolchain logs |

## Run the available tests

```bash
python3 scripts/run_python_tests.py
python3 scripts/source_checks.py
```

Python tests use only the standard library. Source checks do **not** compile Solidity.

On a networked development machine with a reviewed Foundry installation:

```bash
bash scripts/install-deps.sh
bash scripts/verify.sh
# Separate static analysis, after installing a reviewed/pinned Slither release:
slither . --config-file slither.config.json
```

Direct dependency versions are requested in `package.json`; they could not be installed/resolved here. No lockfile is fabricated. Review the resolved packages, retain `package-lock.json`, and pin all upstream revisions/actions before a release.

## Off-chain operation

Copy and fill the example configuration, retaining dry-run mode:

```bash
python3 -m keeper.monitor --config keeper/config.example.json --once
python3 -m indexer.monitor --config indexer/config.example.json --once
```

Example addresses are **placeholders**, not deployments. Live signing uses an encrypted Foundry `cast` keystore, a 0600 password file, explicit reviewed-deployment consent, bytecode hashes and bounded spending. No real signing was performed here. See `docs/OPERATIONS.md` before enabling any service.

**Read `docs/AUDIT.md` and complete `docs/RELEASE_CHECKLIST.md` before treating this as deployable software.**
