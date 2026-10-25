# Pyth reader and candidate research: exact verification scope

Baseline: `ac98b5b`. The [receipt](receipt.json) binds the final new source/test,
report drivers and exact evidence. [Review and remaining decisions](REVIEW.md)
and the [operator guide](../../../docs/PYTH_PRICE_SOURCE.md) remain authoritative.
Production is **NOT APPROVED**.

## New code checks actually executed

The isolated [runner](run-solidity.py) used the normal Solidity0.8.26/Cancun,
via-IR, optimizer-runs1, Yul-disabled profile. It copied only the new test and
its dependencies into an external profile; no repository out/cache, running
Anvil, test-chain state, service or journal was changed.

[17 new Solidity methods pass](pyth-reader-summary.json), including one
1,000-run exact rational confidence fuzz test. The 1,000 samples are not counted
as 1,000 additional distinct cases. [Raw JSON](pyth-reader.json) retains the
actual fuzz run count and results. No fixture failed and no unchanged full suite
was rerun.

Coverage includes:

- Exact integer price, feed binding, original timestamps and synthetic identity.
- Constructor identity/runtime/review/precision/age/confidence policy rejection.
- Exact freshness boundary and no freshness renewal through repeated reads.
- Zero, future and wider-than-uint80 timestamps; zero/negative/wide prices.
- Fixed exponent and malformed int32 sign extension; wide confidence words.
- Exact confidence boundary, one raw unit outside it, and explicit zero tolerance.
- Changed Core runtime, short/oversized/reverting returns and bounded gas exhaustion.
- Rejection of native payments and arbitrary update calldata.
- Decimal endpoints without rescaling or truncation.
- Existing native-ETH Oracle integration: independent fixture controls, dual
  bounds/fingerprint, exact3% disagreement boundary and no stale/confidence/
  runtime failure fallback.

The Core and the other source are controlled offline fixtures. This does not
verify a live Pyth signature/proof, actual publisher independence, proxy policy,
authenticated update service, fee, freshness or operational availability.

## Production compile and size

The [normal build driver](build-source.py) compiles **43 production Solidity
sources** with unchanged compiler/settings/limits. All **38 object gates pass**;
[size and input hashes](source-size-gates.json) are recorded.

| Object | Runtime | Creation including static arguments |
| --- | ---: | ---: |
| New optional Pyth reader | 2,193 bytes | 3,483 bytes |
| Vault | 24,263 bytes / 313-byte margin | 47,102 bytes |

[Exact bytecode comparison](prior-object-comparison.json) finds all37 preceding
production objects unchanged, against the previous readiness compiler result.
This supports reusing their existing source-scoped tests; it is not a new full
regression or formal proof. Dynamic release constructor arguments still require
exact ABI-encoded qualification. No gate or gas limit was relaxed.

## Actual external observations

[Catalog receipt](catalog-receipt.json) records official download sizes/digests.
Exact [Chainlink](chainlink-selected.json), [Pyth](pyth-selected.json) and
[Uniswap deployment](uniswap-selected.json) extracts are retained. Full raw
downloads are preserved in the external release workspace, outside Git.

Fresh public reads did not produce a usable chain snapshot:

| Attempt | Saved result |
| --- | --- |
| Pinax initial | [HTTP429](feeds-attempt1.json) before a usable snapshot. |
| Pinax one delayed retry | [HTTP429](feeds-observation.json) before a usable snapshot. |
| Documented Robinhood endpoint | [HTTP403](feeds-official-observation.json) before a usable snapshot. |

Initial sandbox catalog access was unavailable; approved external access then
succeeded. No transport error is a missing price, zero balance, absent pool or
qualification pass. The route mode of the [discovery driver](observe-candidates.py)
was not executed after these failures; no fresh quote or cheaper route is claimed.

No public transaction, key, signing, deployment, sealing, inventory admission,
website build/deployment, service/restart, existing NFT/LP/balance/journal or
paused-monitor action occurred. Actual source pairs/routes/RPC/update operations,
authorities, randomness, marketplace acceptance and independent audit remain open.
