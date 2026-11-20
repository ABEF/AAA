# Executed platform compatibility diagnostics

20 November 2026. PoPL baseline `c8124e6f51bbcefa86879709cae5d78036877bac`.
This adds a reproducible, source-pinned offline gate to the existing OpenSea/VRF
plans. No provider or platform path is selected, and no contract, economic right,
mint authority, service or live configuration changes.

## What advanced

[The report-scoped diagnostic](check_platform_boundaries.py) reads nine exact
repository input hashes, the trusted F6 compiler ABI, retained verified SeaDrop
V1 source/ABI and the already archived OpenVRF source. It emits bounded,
exclusive [facts and concrete witnesses](DIAGNOSTICS.json), rather than treating
a narrative recommendation as completed compatibility.

[Execution receipt](EXECUTION.json): one successful final execution in about
0.73 seconds, nine completed diagnostics, no network/EVM/provider tests or old
suite reruns. Two initial analysis-tool checks refused because of inaccurate
source-token assumptions; their exact source stages and reasons are retained in
[the tool errata](INITIAL_TOOL_FAILURE.json). They were tool defects, not PoPL
or provider defects. No failed attempt produced a compatibility artifact.

| ID | Reproducible fact | Consequence |
| --- | --- | --- |
| PF01 | Compiled PoPL request/callback selectors differ from OpenVRF; PoPL requires two words, candidate delivers one. | Direct coordinator binding cannot work. |
| PF02 | PoPL's request is nonpayable; candidate requires exactly its native request fee. | A nativePayment metadata flag does not fund the request. An external funding/adapter policy is still needed. |
| PF03 | Current PoPL callback settings permit 200k–10M; candidate permits 25k–1M. | Only 200k–1M overlaps, and actual cold callback gas remains unmeasured. |
| PF04 | Caught consumer failure differs from enclosing delivery-gas failure. | Retry the same callback after the first; replay the original fulfillment after the second. Never request a new draw. |
| PF05 | All three timestamp residues produce a 2-, 3- or 4-second beacon lead. | To guarantee a not-yet-scheduled beacon under this arithmetic for every residue, timestamp lag must be strictly below two seconds. Actual timestamp/publication behavior is unqualified. |
| PF06 | Current policy rotates only after every original mint is finalized; callback authenticates the coordinator and rejects duplicates. | A cancellation/refund or adapter restart cannot justify replacing an outstanding draw. |
| PF07 | Retained SeaDrop ABI has only a minimum signed price. Free+1wei and paid 0.05→0.1 ETH satisfy that price floor. | Enabling the standard signer alone does not preserve exact free-team and paid-price guarantees. These are predicate witnesses, not full signed mint executions. |
| PF08 | Retained SeaDrop active checks include both endpoints. Two stages sharing timestamp 200 are both active at 200. | Actual generated intervals/context must be reviewed; UI adjacency is insufficient proof. |
| PF09 | The compiled NFT callback exposes recipient and quantity only. Current mint2 rejects nonempty signer lists. | No signed price/stage/salt/signer context reaches the NFT; current refusal must remain until the integration is deliberately redesigned. |

## New recovery distinction for any future OpenVRF adapter

The earlier source research correctly described same-result retry but did not
separate the two failure domains precisely enough for an operating runbook:

1. **Consumer callback reverts while the enclosing fulfillment completes.**
   The provider stores `fulfilled=true`, `delivered=false` and its original word.
   `retryCallback` may retry that same request/result, with reviewed gas up to
   the provider maximum. No new randomness request is appropriate.
2. **The enclosing `_deliver` call reverts for insufficient parent gas.**
   Solidity transaction rollback restores the previous unfulfilled state and
   rolls back proof/result/fee writes from that fulfillment. `retryCallback`
   rejects an unfulfilled request. Retry the original `fulfill` and its bound
   proof with adequate total gas. Its original consumer/round/request remain.

These are source-order/atomicity deductions, not executed EVM acceptance.
Cryptographic correctness, actual cold callback costs, provider runtime,
delivery liveness, dedicated funding and adapter restart/duplicate mapping still
require their own implementation decision and qualification. The provider's
fee-transfer recipient can also revert, rolling back fulfillment; it must not
be diagnosed as a missing NFT request or recovered with a replacement draw.

## Decisions still open

Preserve exact free-team/paid prices and original-request permanence. Do not
enable a standard signer merely to pass Studio, or bind OpenVRF directly by
relabeling an address as a v2.5 coordinator. The operator still needs an actual
accepted OpenSea path/payload and an explicitly reviewed provider/adapter trust
and funding model. No third party was contacted, and all live-readiness gates
remain false. Independent specialist and deployed integration approval remain.

## Reproduce only when these inputs change or independent review needs it

```text
python reports/recommendations-execution-20261120/platform/check_platform_boundaries.py --output NEW.json
```

The output must be new. Changed source pins fail closed and require a reviewed
new scope. The tool does not compile, execute Solidity, send transactions or
serve production traffic. Its initial-stage `.py.txt` files are historical
analysis inputs only and are not counted as additional implementations/passes.
