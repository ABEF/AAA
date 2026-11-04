# Whole-project coverage and limits

Scope: user-approved [brief](AUDIT_PROMPT.md), twice [challenged](PROMPT_REVIEW.md).
Baseline main e237aa72; unchanged Solidity source/evidence e26fc74. This matrix
distinguishes focused current inspection from previously scoped evidence reuse.
It is not a claim that every function received a new independent line-by-line
audit or that every historical test ran again. No public chain/service was used.

| Area | Current inspection / evidence | Disposition and remaining limit |
| --- | --- | --- |
| Architecture and authority | Both READMEs, current instructions/context, components, callable reference, Module/Access and Vault/Migration entry guards; [authority audit](../authority-audit-20261103/VERIFICATION.md) | Direct governance, keeper separation, custody5 and holder claims retained. Immediate governance/emergency trust remains. |
| Solidity/toolchain | Exact52production/31dependency and4build-input pins checked against current normal evidence; current official compiler disclosures consulted | Existing43normal gates/static471 records and compiler applicability reused, not freshly executed. Migration39-byte margin remains tight; no speculative refactor or compiler change. |
| Contributions/shares/NAV | Entry→Pricing→Vault join/balance/put/result, fee checkpoints, old/new NAV, main-only growth, owner and policy binding | No reproduced new accounting defect. Prior scoped [LP audit](../smart-contract-lp-audit-20261103/COVERAGE.md) and [Entry3](../direct-entry-v3-20261103/VERIFICATION.md) retain their exact scopes. Actual independent feeds/depth remain open. |
| Both physical LPs | Manager/typed Executor, collect/decrease0, both-leg burn, residual-only close, exact native/token receipts, portfolio amount and tick helpers | Main/residual remain one logical share account. No third-leg or dropped-backing change. [Multi-day scenarios](../portfolio-long-horizon-20261102/CASE_MATRIX.md) are reused local evidence, not live economics. |
| Routing, fee floors, price | Oracle dual bounds/sequencer, Pyth shape, captured pricing, Balancer/Math sizing and ordinary-active checks | Gross, additional-loss-after-fees, idle and caller floors kept distinct. No global best-price or manipulation immunity claim. Real routes, proxy behavior and independence unqualified. |
| Normal timing and keeper | Strategy/Confirmation, keeper priority/status/recovery/submit paths, compound and raw-range policy |85%/600/300/240 plus12h and60–300jitter remain. The suspected route-only outage reset issue was rejected as intentional; no keeper code/settings changed. Existing incident tests distinguish price faults from unrelated telemetry. |
| Harvest/rewards/compound/burn | Vault receive/allocation, Fees dust, Membership checkpoints, Rewards indices/claims/conversion, Compounder/Buyback | Actual receipts only;80/10/5/5 preserved. Harvest independent, claim not compounding. Existing per-asset rounding and unharvested receipt-time policy are not silently changed. Burn ABI/real gas remain qualification. |
| Royalties and failures | Royalty activation/deferred cohorts, per-NFT conversion/claim and neutral converter admission | Known rarity1/2/3 distinct from currency eligibility; no historical-fee dilution or arbitrary sweep introduced. Actual marketplace payments/currencies and live conversion remain open. |
| Terminal holder return | Exit lifecycle, allocator/distributor/current-owner data, API principal report, [1000/mixed-wallet assurance](../holder-exit-assurance-20261103/REVIEW.md) | Governance-only batches, actual ETH+ZZZ and old claims retained. Source and assurance tests unchanged. Rejecting receivers/broken tokens/maximum target gas remain limits. |
| Parking/emergency/canonical | Distinct manual procedures, Budget source/destination controls, canonical freeze/domain/backing semantics and retained findings | No integrated bridge/custody address/reopening. Emergency may bypass financial checks; pre-exit same-chain replacement and complete chain loss are different boundaries. No new migration policy. |
| NFT/VRF/metadata/OpenSea | NFT mint/request/finalize/transfer and metadata paths, prepared artwork/royalty traits, policy identity and official VRF/SeaDrop guidance | No new images/random traits. Direct mint is not SeaDrop; live VRF/chain/drop/funding/hosting unqualified. Unsupported OpenSea integration remains an actual release blocker. |
| API and unsigned actions | Projection/custody/portfolio/current LP and reward data, activation config/trace, Transactions, budgets, HTTP/workers/admission | Pinned reads, exact drafts, no signing expansion. Fresh-profile wallet/site integration remains open; current3 runtime is not source8. Missing data never becomes demo/zero. |
| Indexer/reorg/configuration | Actual SQLite rollback proof and ingestion; caller config alias reproduced; fixed start-anchor snapshot and validation | N04-01 corrected. Malformed anchor rejected before creating DB; same DB identity/schema.33affected fresh Python methods pass, no existing database touched. |
| History/performance | Earnings replay/pricing/audit paths, indexer SQL ownership replay | N04-02 streams instead of Python fetchall and closes cursor.2001synthetic transfer rows checked. Replay CPU, SQLite sorting/storage and years of authentic history are still unqualified. |
| Website, UX/concurrency | Complete website README/AGENTS/context; adapter/manifests, default configuration and preserved signer inspected; historical published UI evidence retained | N04-03 current guidance corrected. No JS/CSS/assets/config/build changes; no fresh browser/load/extension claim. Existing per-NFT artwork/audio and confirmation rules retained. |
| Operations/data/observability | Operator/operations/recovery, health/journal/nonce evidence, startup identity and storage boundaries | Exact new anchor/restart/reverse procedure documented. No service, heartbeat, journal or host changed. Unix sustained operating/restore/off-host qualification remains. |
| Historical reconciliation | [Current findings](../../docs/AUDIT_FINDINGS.md), [report map](../README.md), prior finding dispositions and exact source pins | Immutable historical reports retained. The existing400-report baseline catalogue is reused, not reread/recounted as new audit coverage. Current report index and maintained guides updated. |
| Release and management | Single Todo, features/roadmap/release/current memory and source/site distinction | No gate falsely closed. Actual providers, authorities, OpenSea, storage/operations, strategy economics and independent audit/remediation remain open. |

## Cross-feature cases considered

The review follows activation/growth while harvesting and while a residual is
filled/mixed; transfer/claim before and after contribution and terminal allocation;
independent reserve use and both-leg close; policy/range/mode changes during
confirmation; RPC faults/price outages versus healthy funded claims; nonce/pending
recovery before unrelated work; configuration changes across restart; reorg and
restored history;1000NFTs with mixed owners/rarities/tiers and dormant entries;
1→2→1 portfolio transitions and trend/reversal/thin-depth execution.

Those paths are a combined source/historical-evidence review, not new live market
simulations. Fresh execution in this supplement is limited to the changed indexer
and its regressions plus publication/document consistency. Do not sum old
portfolio, authority, exit, Python and website counts into a full current suite.
