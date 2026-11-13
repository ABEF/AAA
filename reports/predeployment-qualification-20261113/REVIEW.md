# Predeployment RPC, market and fee qualification

13 November 2026. Source baseline: `11e74883787e32e816b5c01b1213189400fe01fe`.
**Independent genesis identity and all 13 existing RPC compatibility checks now pass. Complete PoPL fees and production adoption remain unqualified.** This campaign advances the missing external evidence, without changing code, safeguards, defaults or live environments.

## Completed work

| Work | New evidence | What it establishes |
| --- | --- | --- |
| Independent network identity | Official Robinhood rollup metadata plus its initial Ethereum assertion through a separate L1 RPC; exact event layout and assertion commitment independently recomputed | Expected chain4663 genesis, without taking the expected hash from the candidate endpoint |
| Complete existing RPC profile | All13 `activation_api_v1` checks;48 actual Robinhood HTTP posts with configured1.5-second monotonic pacing | Point-in-time canonical reads, exact runtime, actual Approval(0) trace/log, missing-hash rejection and bounded receipt/header checks |
| History and temporary simulation |19 further bounded reads; genuine historical event, exact9November state/runtime, tiny code-only call/estimate/trace override and nonpersistence | These methods and specific history are available at the observed endpoint; not a full-work capacity guarantee |
| Current market/feed evidence |58 attempts across a retained partial phase and separate canonical closure;95 known pool states and four new bounded quotes | Current source/route blockers and concrete launch actions, without pretending incomplete data passed |

See the separate [identity and full-profile report](rpc/REVIEW.md), [capacity/history report](capacity/REVIEW.md) and [market/feed report](markets/REVIEW.md). Their anchors, source hashes, request bounds, failures and integrity manifests remain separate. The earlier [controlled20M/24M campaign](../gas-profiles-20261113/REVIEW.md) and [fee-component campaign](../rpc-fees-20261113/REVIEW.md) retain their original scope; none of their suites, financial operations or compiler work was repeated.

## Identity and provider boundaries

The independently derived expected genesis is:

`0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c`

The derivation binds the officially listed Ethereum rollup and deployment block to the initial assertion's L2 block hash. Its state/assertion hashes and chain initialization are reconciled. The independent Ethereum provider returned a null deployment receipt; no receipt-trie proof, locally verified L1 consensus, complete ArbOS rebuild or deployed-source binary attestation is claimed. Two other initial L1 provider handshakes returned403 and were stopped. These limitations remain in the proof and second review.

The successful full profile used unchanged `keeper.probe.probe()` with an evidence-recording, paced transport. The exact [runner](rpc/profile-runner.py.txt) is inert text with local paths, not a portable recipe. The stock CLI has no pacing option; its default cadence/parser was not the successful execution. A command template is not evidence that an anonymous public tier can sustain that cadence.

Primary Pinax method and Help pages conflict about logs/submission, and tracing examples are not endpoint-specific capacity promises. The actual log witness resolves only that observed read. Submission was not tested or authorized. No reviewed numerical full-work gas/body/response/deadline/rate/concurrency caps, plan/SLA, independent upstream or lifetime archive guarantee exists yet. A specific older state being available does not close archive completeness. The endpoint is not adopted automatically.

## Actual launch blockers

At block113296579,13November10:48:31UTC, the selected `501122…` pool has **zero active liquidity**. Distant ticks still contain liquidity: its new ETH quote succeeds across a gap. This is neither proof of zero total liquidity nor a reason to reseed or switch the selected pool automatically.

The two Chainlink ETH proxies still share one aggregator. Pyth's stored ETH price is541758seconds old and disagrees by1483.837986bps; API3 ETH remains inactive and lacks the required round-compatible observation. Two independent fixed-ZZZ valuation paths are also missing. No valid two-source USD vector is approved.

Known native candidates with larger activeL materially disagree with the selected price. Only the tiny `07ee2b…` active candidate has a possible common500bps reference band in this bounded inventory. Largest activeL is not highest TVL, independent price truth or usable depth excluding PoPL. The95 known pools are not an exhaustive new pool-discovery scan.

The four new200k official-quoter diagnostics retain exact semantics. A nominal$50 ETH input, conditionally sized from one Chainlink round, loses14.211291% against selected initial spot and84.654786% against the compatible candidate's initial spot. Selected1000ZZZ reverse fails full input; the other reverse returns empty wrapped error and remains unavailable. These are concrete poor-execution diagnostics, not qualified USD floors, optimal strategy sizing, final spot, universal activation rejection or full operation gas. No safeguard was weakened to accommodate them.

## Remaining work, in order

1. **Creator/operator and pricing providers:** establish genuinely independent ETH and ZZZ valuation paths, fresh authenticated publication, round compatibility, reviewed ages/depth and outage/liveness controls. If using Pyth/API3, actually qualify updates/activation and any adapter before admission.
2. **Creator/operator:** resolve target/reference price compatibility and meaningful external bidirectional liquidity. Keep the selected destination unchanged unless the user explicitly selects a replacement. Record actual control/upstream risks and reviewed route/source fingerprints.
3. **Operator/provider:** obtain an appropriate service plan and explicit numerical capacities, trace weight, history, rate/concurrency, submission role, outage/support and change terms. The [acceptance worksheet](capacity/PROVIDER_ACCEPTANCE.json) is incomplete, not a configured service or approval hash. No paid subscription or external message was created.
4. **Engineering:** prepare exact current launch-state operations on a suitable isolated fork/target-compatible simulation, then reconcile complete Nitro execution/posting estimates, actual traces/accounting and full20% contribution/25% maintenance padding under20M/24M. Include current mint2 bindings and real qualified financial inputs; manual Migration C/D and maximum state remain separately unqualified.
5. **Operator:** approve gas-price/per-transaction/day/native-funding ceilings and complete policy/evidence hashes. A ceiling is not expected cost; component-only quotes cannot substitute for a complete operation. Matching consumer/configuration adoption and real hosting/operating/recovery rehearsals require separate authorization.

The old authenticated full-graph override footprints are about1.44–1.48MB, but use chain31337/source9-mint1 and old controlled clocks. They were sized offline, not sent or relabeled current mint2/4663 state. Rebuilding a large artificial graph now would not qualify the missing live markets or complete launch fees. The [fresh-state worksheet](capacity/REVIEW.md) records prerequisites instead of inventing backing, source independence, current timestamps or a green fee result.

## Preservation and verification

No production or test source changed. All61 production Solidity files, the100-source normal closure, fee/profile helpers and protected dirty files must match their baselines in the [final verification record](VERIFICATION.md). No unchanged suite, EVM operation, fork campaign, compiler or static analysis was rerun. New offline verifiers recompute evidence integrity and analytical conclusions only.

API/unsigned-review default stays12M; keeper limits are separately configured and optional20M/24M remain unchanged. Two-source300bps agreement, spot selection,3% contribution/97% marginal deployed LP,1% conversion/additional loss,3% maintenance, caller floors, exact accounting and all authority/callback/custody safeguards remain. No contract deployment, public transaction, signing, service/site change, existing Anvil/journal reset or paused-heartbeat restart occurred. Source publication is not provider adoption or production approval.
