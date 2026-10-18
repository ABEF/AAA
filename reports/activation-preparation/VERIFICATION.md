# Activation preparation verification - 2026-10-18

**Development evidence, not production approval.** No production Solidity,
public website or server configuration changed. No public transaction was sent.

| Check | Result and exact scope |
| --- | --- |
| [Targeted Python checks](verification.json), [log](python-tests.log) | **38 passed, no failures/skips**, 21.331 seconds: 16 activation cases (with scenario matrices), six HTTP cases and 16 RPC boundary cases. Runs on an isolated tracked-HEAD snapshot plus only this publication's preparation/RPC/test changes. Source hashes remain unchanged through the run. |
| [ABI and runtime compatibility](runtime-verification.json) | 63 getter layouts from 14 source-matched compiler artifacts; exact Entry tuple, budget/manager signatures and source/share event indexing checked. Existing artifacts reused; no unchanged Solidity suite or full rebuild repeated. |
| Ephemeral local Anvil | Built-in callTracer logs, nested STATICCALL, canonical-hash post-block state and eth_estimateGas supported. The actual production budget helper accepts 99% and rejects one raw USD unit less. Test-only probe/transactions on loopback chain 31337; process stopped afterward. |

The typed preparation checks direct ERC20/native/converted input, six-decimal
source scaling, activation/new/existing shared buckets, top-ups, approval/reset,
unchanged economic outputs after tightening minima, incumbent idle/compound
exclusion, rounded loss floor, malformed/ambiguous/bounded traces, input policy,
code/feed/storage/binding changes, current-value availability, stale/reorg/expired
snapshots, unsupported RPC capabilities and separate gas limits/balance checks.
The HTTP checks framing, size/media/host/duplicate fields and sanitized failures.

The first test attempt exposed a **fixture codec** that could not encode signed
int24 ticks; the fixture now encodes that static word explicitly. Production ABI
and economic assertions were not relaxed. Final receipts above supersede that
incomplete attempt. Tighter Entry minima can change gas without changing economic
outputs; preparation compares economics and retains the final simulation's gas.

End-to-end preparation tests use byte-level RPC fixtures, not a live Pons route.
The local Anvil probe validates trace/API mechanics and the real budget boundary,
not complete Entry/native/Pons venue execution. Actual production manifests,
ETH/ZZZ/USDG/USDC route/feed qualification, provider tracing and full network-fee
semantics, wallet integration, hosting/operating rehearsals and independent review
remain open in [the central Todo](../../TODO.md#task-activation-quotes).
The prior contract/fork/static receipts keep their original source and workload
scope; they are not relabelled as new production qualification.

Implementation and operating requirements: [activation preparation](../../docs/ACTIVATION_PREPARATION.md).
RPC observations are not execution proofs. Release remains **NOT APPROVED**.
