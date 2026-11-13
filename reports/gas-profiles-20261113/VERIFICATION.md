# Verification and reuse boundary

Baseline `fbe47c3`; new profile inputs, unchanged production implementations.

| Evidence | Fresh scope | Reuse / limitation |
| --- | --- | --- |
| Python |13 new methods pass| Real configuration/gas/manual helpers and keeper coordinator with injected transport/inert signer; no full unchanged suite |
| Browser |12 new checks pass| Actual unchanged website modules and extracted fixture factories; no old test registration or execution |
| Solidity |5 new methods pass| Only the new inheriting host;35 prior methods remain byte-identical and are not rerun |
| Actual owned RPC |4 contribution +6 keeper cases pass| New isolated32M nodes; exact canonical calls, traces, estimates and padded calls; same workflows as the five methods, not ten extra features |
| Actual reader replay |4 captures pass| Exact recorded responses through production trace/gas helpers; zero new EVM/RPC execution |
| Keeper inventory |951 selected, zero executed| One module-inventory addition; list count is not pass count |
| Public provider |33 attempts:24 results/8 RPC errors/1 transport failure| Cheap views/estimates only; required complete tracing remains unavailable |

The Solidity test-only parent field `exportSetupHash` changes private→internal
to retain strong setup/delta authentication in the new inheritor. No production
ABI/storage/runtime/profile changes result. The new cases assert exact minimum
rejection,97% actual marginal LP, share/geometry/clock preservation, funded
reserves and both-leg replacement. Old test bodies and fixture baselines remain.

Actual RPC sources preserve setup and per-slot delta hashes, explicit zero
storage writes, exact runtime identities, actor EOAs and keeper permission. Each
call uses the declared20M/24M cap and full20%/25% estimate padding. The exact
padded call succeeds too; trace gas, cold call gas and estimates remain distinct.
An authenticated production-state restoration is not a claim of whole-VM hash
equality with an omitted test harness. No old runtime or capture is relabeled.

The original owned-node launcher inherited its parent environment. All executed
nodes used explicit local arguments, `--accounts0` and `--silent`; no environment
names/values are inspected or published, no signing/submission occurs and no
credential-isolation claim is made for those executions. A hardened reproducer
must remain distinguished from the source that actually produced the captures.
All ten owned nodes were stopped. Existing8902, journals and services are untouched.

All61 production Solidity sources retain exact baseline bytes. Reuse the
accepted100-source normal build and strict567-record static evidence from
[11 November](../gas-feasibility-20261111/VERIFICATION.md); no normal/static build
or unchanged regression suite reruns. Oracle remains24,573bytes/3bytes headroom;
Vault24,544/32 unchanged. This profile task does not solve the size constraint.

[EVM scope](evm/VERIFICATION.json), [backend](backend/README.md),
[public provider](network/REVIEW.md), [candidate overlays](backend/profiles.template.json).
Final source/document/preservation checks are recorded in the
[completion receipt](COMPLETION.json).
Production provider, full fees, actual markets/configuration/maximum state,
OpenSea/VRF, operating and independent audit approval remain open.
