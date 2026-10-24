# Engineering roadmap

Reviewed 2026-10-25. **Production NOT APPROVED.** The [sole Todo](../TODO.md)
owns task status and acceptance criteria; the [feature/evidence reference](IMPLEMENTATION_STATUS.md)
describes implemented candidates, and the [release record](RELEASE_CHECKLIST.md)
owns approval. This roadmap sets dependencies and order, not another checklist.

## 1. Close required immutable capability and safety boundaries

The current candidate implements native ETH accounting/routing V2, pricing V2,
typed v3/v4 conversions, governed bounded loss limits, one contribution pool,
same-pair moves, explicit external custody and same-chain canonical handoff.
Read [architecture](ARCHITECTURE.md) and [the internal audit](../reports/preproduction-audit-20261025/REVIEW.md).
Do not redo completed behavior or unchanged tests merely to increase a pass count.

First add [caller-bound contribution policy](EXECUTION_LOSS_POLICY.md#review-time-policy-binding-remains-open) to the versioned approved activation/growth flow. The current Request does not preserve the maximum cap shown during review. Update Entry/API/trace/inventory and wallet profile coherently before public signing; retain old local deployments under their original profile. The bounded two-pass planner and safe idle reinvestment now have scoped local evidence; qualify actual thin-market quotes/depth without relaxing the captured deployed-LP floor. Explicit inverse orientation and approved two-width keeper policy need real threshold/turnover/MEV and operating qualification.

The current release uses guarded same-chain pool movement and explicit source-chain
custody exit to an operator-controlled address. That custodian performs external
token migration or bridging; integrated bridges and future-chain canonical NFT/
reward transport are deferred optional scope, not launch gates. Atomic ETH/WETH
or other different-pair conversion remains unsupported; external custody is a
distinct trusted workflow, not that algorithm. Retain and qualify same-chain whole-
collection handoff. It does not solve future-chain or post-halt ownership recovery.

Keep normal runtime/initcode and gas limits. Vault remains close to EIP-170; use the latest exact-source size receipt.
Any bytecode change needs fresh normal runtime and initcode gates. Review
complete custody/liability invariants, callbacks and abort/return paths before
accepting further changes. Immediate governance/external recipients remain trusted.

## 2. Qualify real dependencies in parallel with integration

The selected Robinhood pool is static hookless native ETH/ZZZ
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
Qualify its actual directional fees, liquidity, native execution and gas. At the
default 1% conversion limit its observed approximately 1.101% combined fee does
not qualify full ZZZ-to-ETH conversion at reference prices: require a cheaper
reviewed route, not an automatic policy increase.

Prioritize two genuinely independent USD sources per economic asset. Review
shared upstreams/proxies, ages, depegs, outage/recovery and cost; neither a pool
spot estimate nor two proxies for the same provider establishes independence.
Qualify actual ETH/ZZZ/USDG/USDC routes and complete execution/trace/fee evidence.
Creator-team pricing/token/market answers remain relevant; Pons creator funding
is optional historical scope for the current hookless pool.

Select supported funded proof-verifying VRF and production authorities, publish
verified permanent artwork, and qualify OpenSea primary mint/royalty recipients
and contract-owner compatibility. Local direct mint and local substitutes cannot
close these external gates. Keep schema-5 inventory genuinely blocked until its
actual identities, observations and independent reviews exist.

## 3. Integrate the exact native deployment and rehearse operation

Use reviewed versioned API/indexer/website profiles, complete confirmed history,
current-price USD and explicit unavailable states. Confirm owner rights, exact
approvals and original-hash recovery. Public website stays simulated and signing
Anvil-only until separately authorized and qualified. Existing local fixtures,
journals and dist repair overlay must not be reset or deployed as production.

Rehearse on supported Linux and the target chain: durable fee-review recovery,
included/separate L1 semantics, outages, reorgs, lost/stale backups, old-host
fencing, signer rotation and off-host alerts. Use [operator procedures](OPERATOR_MANUAL.md)
and [keeper recovery](KEEPER_RECOVERY.md). A pause is not a custody freeze; an
already approved paused exit can still move assets. Ten-minute polling is not
an execution guarantee or protection against all out-of-range time.

Qualify maximum actual assets/inboxes, strategy economics/MEV and service capacity.
The dedicated 10/25/100-user campaign remains user-deferred, not passed. Keep
monitoring paused as requested; historical chat observations do not establish uptime.

## 4. Approve an exact release, then a separate public rehearsal

Use local tests, the Robinhood mainnet fork and Robinhood Testnet for their
different purposes. Improve focused harnesses and prove their meaningful paths
before rerunning affected tests; keep reuse and limitations source-bound.
Complete independent security/economic review, remediation and exact-release
CI/static/fork/size/gas/configuration and operator sign-off.

A real-funds rehearsal needs separate named contracts, explicit budget and
execution authorization. Final collection identity is fresh. No burn/reset,
arbitrary sweep, public deployment or sealing follows from this roadmap.
Record publication and operations separately; keep [Todo maintenance](TODO_WORKFLOW.md),
operator guidance and both repository memories synchronized.
