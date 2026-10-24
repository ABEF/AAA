# Pre-production internal audit plan - 2026-10-25

Baseline: contract main `214d9a104643df0643a21ceec6970329f3525d3f`; website main
`3a6a69cc86031762485fe0cf52c6d172a6762fe8`. Existing unrelated drafts are excluded.
This is a source-scoped internal review, not independent audit or production approval.

## Method and decision rules

1. Trace custody, liabilities and authority through complete operations, including
   external calls and intermediate/recovery states. Do not infer safety from a
   function's name, a UI label, mocked integrations or a prior pass count.
2. Distinguish an exploitable defect, an operational/documentation defect, an
   accepted governance trust and an unqualified external dependency. Record concrete
   triggers and consequences; absence of a discovered exploit is not a proof.
3. For a code defect, improve a focused harness first, reproduce failure, fix the
   implementation and rerun affected cases. For missing composition coverage, add
   independent conservation assertions and demonstrate meaningful executed paths.
   Reuse unchanged source-bound evidence; do not claim a fresh full regression.
4. Correct actionable operator instructions in place. Historical reports retain
   their original scope. Maintain one task ledger, feature/evidence reference,
   sequencing roadmap, release record and operator manual.
5. Publish intended work on main only, recording local/published/operated states
   separately. Preserve unrelated drafts, existing Anvil/NFT/LP/journals, local
   dist overlay, Anvil-only signer, null public deployment and paused monitoring.

## Coverage and adversarial scenarios

| Boundary | Review paths | Required evidence or open qualification |
| --- | --- | --- |
| Governance and lifecycle | Bootstrap/seal, immediate configuration, callbacks during changes, pause scope, canonical preparation/freeze/import/funding/abort/retirement, repeated successors | Exact authority/state transitions; preserve original approvals and backing; no multisig finality override |
| Shared principal | Activation/growth, fresh and incumbent NAV, same-pool atomic placement, out-of-range joins, harvest/dust/compound, rounding, native prefunds, failed callbacks | Actual manager/PoolKey/owner/ticks/liquidity and balance deltas, captured price/policy and marginal floors; composed real-v4 harness |
| Economic rights | LP 80/10/5/5, equal activated collective share, rarity-only royalties, transfers, fractions, converted credits, claims, late and unreadable currencies | Separate ingress/claims/reserves; no new income from claims/conversion; no old-income entitlement for newcomers |
| Strategy and external custody | Trigger/cooldown/range, actual directional fees, MEV/oracle bounds, move/park/normal exit/raw exit/recovery | Per-operation limits (not lifetime loss guarantee); exact approved snapshot/raw minima; external recipient trust explicit |
| Oracle and dependencies | Two sources, freshness/decimals/sequencer, rounds/spot changes, proxy/common-mode failure, token callbacks/blacklists/rebasing, venue outage | Source independence is a provider-review gate; no stale/single-source/spot/peg fallback; failed dependencies can block movement |
| Keeper and backend | Durable intent before signing, nonce/reorg recovery, spend limits, canonical fees, chain/version preflight, indexer completeness, API bounded concurrency and same-block reads | Improved failing-first receipt transcript harness; no automatic resend/journal deletion; actual Linux/RPC/finality operations still required |
| Website and marketplace | Read-only profile/Anvil-only signer boundaries, exact approvals, submitted-hash recovery, confirmed LP before artwork, transfer and marketplace escrow | Current public simulation unchanged; actual extension/OpenSea/services qualification cannot be inferred |
| Release/tooling | Source-bound evidence, size/gas headroom, CI/static/fork scope, inventory versions, documentation contradictions | Preserve normal compiler/EVM gates; no silent test skips, stale review approvals or guessed deployment configuration |

## Verification limits

No public transaction, deployment, service control or secret access is part of
this audit. Real price sources/routes, VRF, production authorities, OpenSea,
permanent content, Linux operating campaigns, destination/finality transports
and independent audit remain explicit release gates. New tests will identify
their substitutes and inputs. Review results and exact commands are recorded in
the accompanying review/verification documents when complete.
