# Project and composed operating model

Contract baseline93ceee1b78ad1e8532932961b934177b558f13c3; website baseline
997f8c3524ea75d613dbb752f67b33a69fe7992f. These identify source, not running services.
Fresh accounting4/custody3/confirmation2/local-canonicalV5 retains old explicit
profiles; no reset or automatic historical state migration is introduced.

## Economic and authority boundaries

1,000 ERC721s have exact600/300/100 rarity quotas and a fixed artwork inventory.
VRF assigns remaining inventory; evolution reflects current LP value and may
fall. Rarity1/2/3 determines only received royalties, not LP fee weight.
One human operator controls direct governance and services; a limited keeper key
executes allowed automation. There is no timelock or independent committee.
Sealing fixes implementation/token/native bindings, not all operating settings.
Guardian pause, keeper authority and governance configuration have different jobs.

Many NFTs independently own shares of a shared physical native ETH/fixed-ZZZ LP.
One contribution pool is selected at a time; old custody buckets remain bounded.
Activation$100/growth$5 floors and stronger pool minimums use two qualified USD
sources;3% source disagreement differs from2% contribution/1% conversion/3%
maintenance defaults and10% governed ceilings. Gas is separate. Financial
emergency bypass remains an explicitly trusted paused-governance capability.

## Complete principal and income journeys

| Journey | Actual sequence and invariant |
| --- | --- |
| Mint/reveal | Exact payment/cap, request provenance, ordered random draw, immutable revealed traits. OpenSea primary drop compatibility remains unfinished. |
| Activate/grow | Checkpoint incumbent fee/compound ownership; route only entrant funds; use actual current target-range ratio; verify marginal deployed LP; issue net-NAV shares. No recenter or rebalance-clock reset. Failure atomically rolls back. |
| Harvest | Collect actual physical fees once per shared bucket, allocate80/10/5/5 with carried fractions/dust rules. Hourly automation is independent of claims and swaps. |
| Holder income | Individual LP share plus equal activated collective; separate royalty rarity/cohorts. Current owner inherits prior unclaimed rights. Claims/conversions/imports are not new earnings. |
| Compound | Reinvest attributed idle/designated reserve into current range; may swap. Separate governed interval; normal service waits while outside or width pending and yields to due replacement. |
| Rebalance | Close shared LP, size against actual remaining execution depth, bounded reviewed swap and redeploy under captured fresh financial/identity guards. Initial12h hard minimum; physical/reference same-side sampled900/300 window,240-second source checks, durable60-600second jitter. No uninterrupted-history guarantee. |
| Move/park | Same-native-pair governed relocation or paused raw parking, distinct from ordinary upkeep and terminal return. No bridge/custody-address executor. |
| Collective exit | Irreversibly stop principal/mint operations; close all buckets; principal plus designated pending compound allocated by NFT shares; bounded current-owner payouts/fallback. Old rewards, transfers/future royalties survive; LP earnings end. |
| Post-exit reserve | At Ready, governance can validate deposits-disabled ETH/ZZZ swap venue. Buyback reserve only, ordinary execution rules. Principal remains separately backed and cannot reopen LP. |
| Canonical replacement | Compatible same-chain freeze/export/backing/import/retire/activate before terminal exit; historical lineage retained. Not post-halt rescue or future-chain proof machinery. |

[19-feature machine map](feature-operation-coverage.json), [contract flow review](contracts-review.json),
[operations map](operations-understanding-and-coverage.json) and
[backend/website boundary review](backend-review.json) bind concrete source paths.

## Data, UX and operating boundaries

RPC/indexer observations are a trust model, not independently proven consensus.
Canonical hashes, full lineage, strict JSON/ABI, chronology, budgets and explicit
unavailable states prevent contradictory data being silently replaced by zero.
Earnings/current claimable/previous claims/principal remain separate projections.
Complete raw replay cannot grow forever without a reviewed archival evolution.

Keeper pending recovery precedes new signing, confirmation deadlines outrank
optional nonce users, independent harvest continues through unrelated faults,
and exact persisted state/receipts preserve nonce/spend truth. Relevant identity
faults invalidate sampled readiness. Logs/health/artifacts are diagnostics, not
remote attestation or proof a host runs a particular release.

Public popldemo is the existing simulation. Served poplint remains current3,
null-configured read/unsigned. Current4 source wallet/service integration is not
qualified by those releases or old Anvil flows. Browser signing stays Anvil-only;
no site/build/server/installed-service/journal changed in this campaign.
