# Backend and keeper reconciliation — 11 November 2026

Reviewed the backend, keeper and unsigned operator consumers at `872a5a5`, including the earlier whole-project fixes and the execution-price1/LP-routing3 changes. This is a focused code and evidence reconciliation, with one implemented efficiency correction. It is not an independent audit or a claim that every market, provider or operating condition has been exercised.

## Implemented improvement

An execution-price1 claim plan repeatedly fetched its new constant capability and fixed Math-child binding during admission, its sizing trial and final preparation. A successful one-trial plan made **15 capability reads and 3 binding reads**. The existing request-local cache now includes `EXECUTION_PRICE_VERSION()` and `executionStrategy()`; the same plan makes **5 and 1**, saving **12 RPC calls**.

The change is limited to two selectors in `frontend_api/claim_planner.py`. It preserves the exact canonical block, pinned targets, permitted read shape, bounded cache and request lifetime. It adds no caching of active execution context, source revision, prices, current ownership, balances, lifecycle, gas/fees, heads or simulation results. There is no budget, accounting, entitlement, ABI, signer or operating configuration change.

Three new regression methods demonstrate the complete claim plan, uncached wrong-block/foreign-target/modified-call cases, request isolation and repeated mutable reads. The affected planner/HTTP selection passes **28 distinct methods, zero failures, errors or skips**, with unchanged source hashes during the run. See [baseline](claim-plan-cache-baseline.json), [final record](claim-cache-final.json) and [test log](claim-cache-final.log). These are injected-RPC checks; they are not live provider, wallet, gas or market acceptance.

## Consumer boundaries reviewed

- Omitted execution capability remains historical profile0/LP-routing2. Explicit capability1 requires accounting7/LP-routing3 and matching runtime/capability/fixed-child bindings. A tuple with the same shape is not a substitute for those identities.
- Healthy holdings and original-currency claims retain their read semantics and do not acquire a live Oracle/source-revision dependency. Financial contribution, LP execution and unsigned management review validate their additional execution-context graph and controls.
- The initial two-source valuation and its exact original pricing2 fingerprint remain distinct from authenticated swap transition validation. The capability1 trace uses the actual begin-before-pull through end-Entry context and full post-quote market state; historical trace epochs remain historical.
- Keeper pending records preserve the explicit execution version; an omitted old record cannot be silently adopted as capability1. Current LP snapshots, health/source proofs and unsigned reviews require the matching profile rather than interpreting the retained service-family name as a routing capability.
- Claims, original-currency royalties, LP earned conversion, compounding, harvesting and terminal principal distribution remain separate actions. No old royalty swap or bridge workflow was restored.

The source manifest records the files used for this review. These observations describe inspected code paths, not a claim that every listed file received a new full test run.

## Historical findings reconciled

| Earlier finding | Current disposition |
| --- | --- |
| Shared ABI numeric coercion | Earlier correction remains; codec source is unchanged. Prior 117-method evidence retains its original scope. |
| Indexer duplicate/malformed contract inventory | Earlier pre-database validation remains; indexer source is unchanged. No existing database was rewritten. |
| Keeper late UTC-day/deadline checks and strict simulation output | Retained. `submit`, final LP review, pending polling and confirmation scheduling have the same AST as `8785728`; prior keeper evidence is reused in that scope. |
| Spot reference also used by a swap venue | Addressed only through explicit execution1/LP3 authenticated transitions. This does not admit arbitrary source movement or same-core destination/reference LP changes. Actual source/route qualification remains open. |
| Lifetime history, archive restore, currency expansion and Unix services | Still operating-qualification work. No synthetic workload or source publication closes these findings. |
| Old codecs/profiles and diagnostic ownership cache | Retained deliberately for historical runtimes/inspection. Serving ownership continues to rely on authenticated raw history; removing compatibility code is not part of this correction. |

The previous [323-method execution-consumer record](../../reference-execution-20261111/backend/python-consumers.json) includes the planner in its broad source bracket. That file has now changed. Reuse the record for unchanged components with its original source hashes; do not describe all 323 as a fresh run of the current tree. The new 28 methods cover the changed planner scope and overlap prior tests, so they must not be added to the older count. The four actual trace fixtures, decoder tests and recorded outer-RPC workflows remain unchanged.

## Open follow-up and release limits

1. **Initial keeper simulation work is not explicitly gas-bounded.** In `keeper/monitor.py`, the initial transaction at line 1811 omits `gas`; the `eth_call` at 1825 and estimate at 1850 therefore let the provider choose its execution envelope. The configured gas ceiling is checked at 1862, after that work. This is a provider-resource/resilience limitation, not a demonstrated signing, spending, authority or financial-guard bypass. Existing RPC/work/time limits remain; ordinary LP final simulation at 1700 is explicitly bounded. A shared submission change needs reviewed provider/legacy behavior and focused refusal/sizing tests. No keeper code was changed for this item.
2. **Default gas admission remains a blocker.** All four recorded owned-node Entry calls reject at the unchanged 12M default. Higher local policy2 simulations and their exact derived reviewed-envelope calls are diagnostics only. The synthetic $1,000 activation fixture is not the website's $100 selection, real market depth or target-chain per-transaction/block/fee qualification.
3. **Source and service qualification is not capability checking.** Individually admitted execution sources, genuinely independent fixed-ZZZ references, usable external depth excluding PoPL LP, ETH publication/liveness, actual routes and running-service behavior still require review. Runtime pins and a service source digest do not establish those facts or attest to the keeper's running behavior.
4. **Long-lived operations still need acceptance evidence.** Archive availability, raw/WAL restore, expanded-currency gas, multi-process HTTP/provider workload, Unix locking/supervision, OpenSea/VRF/wallet integration and independent approval remain open. Existing limits must not be silently raised to turn these into passes.

## Adoption and preservation

The cache correction does not change the semantic source list used by earnings checkpoints; it alone does not require rebuilding those artifacts. Earlier source-pin changes, including the shared ABI correction, retain their explicit rebuild/review/re-pin requirement. Existing artifacts, raw/WAL data and old runtimes remain preserved.

No contracts, signer, website, running service/configuration, Anvil8902, NFT/LP/balance, journal, checkpoint or user-paused heartbeat was changed. The four protected unrelated dirty files retain their original hashes. Source publication is not deployment or production approval.
