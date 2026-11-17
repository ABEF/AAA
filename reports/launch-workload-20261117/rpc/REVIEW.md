# Local launch16 RPC verification and optional pre-sync workflow

**The16-currency workload does not universally fit the existing20M contribution profile.** Nine distinct exported states were replayed read-only on new owned loopback Anvil nodes. Five satisfy a capped estimate, full20% headroom and the exact padded call; four do not. These are controlled chain31337 EVM results, not Robinhood network/provider/complete-fee or production qualification.

The fixtures use two minted NFTs, one incumbent/shared main, real v4 core/periphery and PoPL financial code, a bound mint2 helper and pinned SeaDrop runtime, with controlled authority/admission/feeds/VRF/Permit2. The actual ledger has17 assets: native ETH plus16 optional ERC20s, capacity16 and royaltySyncGas1M. This is **not** the maximum1000NFT/four-bucket/two-leg workload.

## Original profile results remain unchanged

| Captured state | Capped estimate | Full20% padded |20M result |
| --- | ---: | ---: | --- |
| ETH activation, no pending royalties |15,121,045 |18,145,254 |Fits |
| ETH activation, healthy pending receipts |16,520,408 |19,824,490 |Fits |
| ZZZ activation, healthy pending receipts |16,930,567 |20,316,681 |Insufficient margin |
| ETH activation, first opening allocation |17,058,665 |20,470,398 |Insufficient margin |
| ETH activation, one gas-consuming optional fault |17,446,142 |20,935,371 |Insufficient margin |
| ETH activation,16 gas-consuming optional faults |Refused |Unavailable |Call fails |
| ETH growth, healthy pending receipts |13,649,230 |16,379,076 |Fits |
| ZZZ growth, healthy pending receipts |14,017,751 |16,821,302 |Fits |
| ETH growth,16 optional faults |13,649,230 |16,379,076 |Fits |

32M diagnostic calls were used only where the20M profile failed. In the16-fault activation case the successful diagnostic trace used29,419,722 gas. That is neither20M admission nor a new service limit. No faulted-currency condition is declared fixed.

All actual traces authenticate the empty-code outer sender and exclude calls to the omitted compiled harness. The original parser retains method-scoped materialization events emitted before each unsigned call, including the16currencies/helper/SeaDrop; identical duplicate exports are deduplicated and conflicts rejected. Baseline/delta hashes, zero storage overrides, runtime pins, exact calls and full wire responses are retained. The source pre_state fingerprint is not presented as a commitment to the whole VM.

## Measurement-adapter correction, separate from contract behavior

The historical adapter fetched the old LP through the dormant entrant's nftBucket0. Here the pool already has an incumbent main, so it needed that shared position. This caused six activation helper rejections; the actual RPC/cap results were unaffected. The six measurements are corrected **offline**, using the retained early typed STATICCALL Vault.group(sharedBucket) output before balancing/placement. All six then pass production trace measurement. Three already-correct growth measures were not replayed. Original errors/records remain, with separate correction provenance; this was a verifier-input defect, not a reproduced contract defect.

## Two NEW optional public pre-sync workflows

| Existing optional syncAll before the SAME activation | Sync estimate/padded within12M | Entry estimate/padded within20M |
| --- | ---: | ---: |
| Healthy pending ZZZ activation |1,813,210 /2,175,852 |15,531,204 /18,637,445 |
| First-opening healthy ETH activation |2,355,311 /2,826,374 |15,121,045 /18,145,254 |

Each sync uses actual call/estimate/full20% padded call and callTracer. Its actual prestateTracer diff initializes a second new node at the identical exported timestamp, preserving the exact entry calldata/value/deadline. Every provided pre-value is validated; slot clears are represented exactly. Only royalty storage changes51/71slots; LP position/shares/owners/reserves, token/native balances and code remain unchanged. All17 incumbent claim views stay1601units and newcomer views stay0 before/after sync. The post-sync entry also passes production trace measurement.

The first strict diff-admission stage rejected the client's simulated sync-sender nonce0→1. That failure is retained. The corrected adapter faithfully retains exactly that observed empty-code sender increment; other nonce/code/balance changes reject. It does not strip nonce state or adopt any real wallet nonce. Its successful sync calls are reused offline; they were not repeated. The second workflow was then evaluated independently.

[Documented prestateTracer semantics](https://geth.ethereum.org/docs/developers/evm-tracing/built-in-tracers#prestatetracer) explain pre/post differences and cleared slots. The full actual tracer replies, exact state changes, source/genesis hashes and protected economic views remain inspectable.

Pre-sync moves work into a separate optional transaction; **no aggregate gas saving is claimed**. It adds no automatic worker, mandatory holder step, approval, permission, gas/default increase or transaction submission. New receipts/activation/state or market movements before actual inclusion can change costs again. Faulted syncAll was deliberately not attempted. Real operator-wallet fees, intervening blocks, maximum state and operating qualification remain open.

## Evidence and preserved boundaries

[Verification inventory](VERIFICATION.json), [original9 outcomes](INITIAL_SUMMARY.json), [offline6 corrections](MEASUREMENT_REPLAY_SUMMARY.json), [two pre-sync outcomes](PRESYNC_SUMMARY.json), and [source/state stages](SOURCE_STAGES.json) keep the stages distinct. Full actual wire/trace archives are compressed in the case directories; the205MB raw producer file and duplicated genesis bodies are not republished here. Their exact hashes/paths are retained. The absence of an initial verifier self-hash is explicit; the final source is a reproducer, not retroactively authenticated initial source. The refused pre-sync source reconstruction matches its recorded hash.

All owned nodes are stopped. No signed/sent transaction, impersonation, old node, public RPC, service/site, existing DB/journal or heartbeat was used. All61 production Solidity sources, protected four files, financial rights, gas/defaults and public-null/Anvil-only boundaries remain unchanged. Source preparation and these finite controlled workflows do not approve production.
