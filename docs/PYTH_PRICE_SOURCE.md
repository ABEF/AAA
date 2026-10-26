# Optional Pyth Core price reader

## Implemented capability and release boundary

[ZZZPythPriceFeed](../src/ZZZPythPriceFeed.sol) is an optional immutable, read-only
source adapter for the existing Oracle. It implements the two methods PoPL uses:
`decimals()` and `latestRoundData()`. It does not implement historical round queries,
publish prices, verify Pyth updates itself, accept payments, own funds, change a
source, or add a new protocol authority. No production reader is deployed or admitted.

This is a compatible source shape, **not approval of Pyth or a production source
pair**. The dated [research and evidence](../reports/release-services-20261025/feeds-routes/REVIEW.md)
identify candidate ETH/USD, USDG/USD and USDC/USD products. No ZZZ/USD entry was
found in the downloaded Chainlink or Pyth catalogs. Catalog absence is not proof
that no custom service exists. ZZZ still needs two independently reviewed sources,
even if users contribute only ETH: the final LP contains and values ZZZ.

## Exact constructor policy

Deploy a separate reader per reviewed feed. Its seven constructor arguments are:

| Argument | Required review |
| --- | --- |
| `source` | Correct-chain Pyth **Core** address, with real runtime and upgrade/administration review. Pyth Pro has a different interface and is not interchangeable. |
| `codeHash` | Exact nonzero runtime hash of that Core address. Proxy implementation/admin pins and monitoring remain separate requirements. |
| `id` | Exact nonzero 32-byte **Core/Hermes** feed ID for the intended asset and USD denomination. A Pro numeric ID or similarly named asset cannot substitute. |
| `exponent` | Fixed expected precision, from -18 through 0. The reader exposes `decimals = -exponent` and never rounds or rescales the answer. |
| `age` | Explicit maximum observation age, 1 through 86,400 seconds. Choose from measured update behavior and risk; no production value is selected. |
| `confidenceBps` | Explicit maximum `confidence / price`, from 0 through 300 bps. Zero permits only an actual zero-confidence observation. The ceiling is not a recommended production value; the production setting remains unset. |
| `review` | Nonzero hash referencing the reviewed source/product/update/precision/freshness/confidence/administration policy. A hash alone does not perform that review. |

These settings cannot be changed inside a deployed reader. A replacement reader
can be deployed and reviewed, then selected through the Oracle's existing
immediate-governance `setDualFeed` path, including after sealing compatible core
contracts. This introduces no new timelock. The reader is not a replacement Vault,
protocol module, custody recipient or arbitrary executor.

## What each read enforces

The reader checks the Core runtime and makes one `getPriceUnsafe(bytes32)` static
call with at most 300,000 gas. Success must return exactly 128 bytes. It validates
the full ABI words before narrowing: positive canonical `int64` price, canonical
`uint64` confidence, the fixed `int32` exponent, and a positive publish timestamp
that fits `uint80`, is not in the future and is within the reader's maximum age.
The confidence check compares the exact products; division cannot round a wider
interval into acceptance. Malformed, oversized, reverting or gas-exhausting reads
fail with a bounded error and no alternate source.

`answer` preserves the source integer. Both `startedAt` and `updatedAt` preserve
the original `publishTime`. `roundId` and `answeredInRound` use that publish time
as an explicitly synthetic identity. Reading never changes an observation's age;
there is no invented heartbeat or historical Chainlink round. The Oracle retains
its own admission, source runtime, freshness, normalization, fingerprint and
two-source agreement checks. An Oracle maximum age may be stricter than the
reader's age. Neither the 3% agreement band nor this confidence ceiling changes
the separate contribution/conversion/maintenance execution-loss policy.

The reader forwards a midpoint observation with a confidence guard; it does not
turn statistical confidence into a guarantee that the real market value lies
inside that interval. Two providers can still share markets, publishers or other
dependencies. Pyth Core, Pro and Core Compatible share the Pyth backend and cannot
be counted as independent providers merely because their addresses differ.

## Operator sequence before admission

1. Verify the official correct-chain Core address and exact feed identity;
   inspect actual code, proxy/implementation/governance authority and the current
   proof/signing/update architecture. Pin and independently review these upstream
   dependencies. The reader's runtime check does not detect a proxy implementation
   change behind unchanged proxy bytecode.
2. Agree and fund an update service. The 2026-10-25 research snapshot found no
   Robinhood sponsored feed; recheck actual current service coverage and terms
   during qualification. A deployment address does not promise fresh prices. Core updates may require an authenticated data subscription,
   signed-update submission, update fees and network gas. Keep credentials in
   the service's protected secret mechanism, outside reports, Git and logs.
3. Select and document the maximum age and confidence policy from real data.
   Measure round availability, confidence, actual read gas, fees, outages and
   recovery on the target chain. Read-only mocks do not close this step.
4. Deploy and verify the reviewed immutable reader in the separately authorized
   deployment campaign. Verify its seven public bindings and exact runtime.
   No deployment is performed by the research scripts or this documentation.
5. Independently assess the complete source pair, including shared upstream
   markets and administrators. Use distinct nonzero independence IDs backed by
   that review; do not invent them from provider names alone.
6. Through existing governance, call `Oracle.setDualFeed` with the two reviewed
   source policies, intended 300-bps agreement band and review hash. Native ETH
   uses asset address zero. Admission requires both sources to be valid now;
   there is no fallback to one source, a peg, the target pool or old prices.
7. Update and verify the approved production inventory, API/keeper source
   policies and dependency monitoring. Reprepare any stale unsigned reviews.
   Rehearse updater failure/recovery and changed dependency pins before launch.

If an updater stops, new price-dependent operations fail once the approved age
expires. Repair the update service or admit a separately reviewed replacement
pair; do not extend freshness or uncertainty merely to bypass an outage. Existing
funded claim rights remain governed by their own contract paths. Sealing does not
make upstream providers immutable or remove their operational trust.

## Primary references

- [Official Pyth network addresses](https://docs.pyth.network/pro/contract-addresses)
  and [feed identities](https://docs.pyth.network/pro/price-feed-ids).
- [Core `getPriceUnsafe` API](https://api-reference.pyth.network/price-feeds/evm/getPriceUnsafe)
  and [maintained Solidity price struct](https://github.com/pyth-network/pyth-crosschain/blob/main/target_chains/ethereum/sdk/solidity/PythStructs.sol).
- [Core versus Pro](https://docs.pyth.network/pro/use-prices-on-blockchain),
  [sponsored updates](https://docs.pyth.network/pro/sponsored-feeds),
  [post-upgrade authentication](https://docs.pyth.network/pro/pyth-core-upgrade)
  and [confidence/freshness guidance](https://docs.pyth.network/pro/best-practices).

Production remains **NOT APPROVED**. Current profiles remain unset, public
signing disabled, and no existing chain, website service or wallet state is changed.
