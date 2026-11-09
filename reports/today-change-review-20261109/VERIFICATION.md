# Verification and reuse boundaries

Baseline:`d81185684d768b0afccfed4801a443ed4ccca60d`. No production Solidity
or website implementation changes in this review. This is not a new full-suite,
real-provider, target-gas, public-CI or independent-audit result.

## New preflight regressions

The consumer [red/green records](consumers/regression-01) retain5 new methods
against the original validator, producing16 failing subcases. After the narrow
phase/type corrections, the affected`MintInventoryTests`class runs13 methods
successfully:5 new and8 existing. Same before/after source hashes bracket each
run. These component fixtures exercise inclusive starts/ends, stage gaps,
wrong-but-in-range phases, malformed timestamps and boolean count aliases.
They do not establish a fully qualified deployment or an open sale.

## New funded Entry3 coverage

[Funded verification](funded-trace/verification.json) records8 distinct passing
methods across two explicit stages: the first run has7 passes and1 test-message
capitalization mismatch; after correcting only that expectation, that one method
passes. The unchanged other7 method bodies are compared by AST hash and are not
rerun or double-counted. Original failure/source/logs are retained.

The test pins the saved campaign ZIP plus three original entry hashes. Its
actual ETH growth witness has nonzero incumbent shares, two stable epoch0 reads,
60USD original input,58.8USD floor and about59.7524USD marginal LP. It retains the
original200-bps/source87/synthetic-depth/controlled-feed context. Equal epoch1
and malformed/misordered observations are explicitly synthetic mutations.
No raw trace is duplicated, no actual new300-bps EVM result is claimed, and
historical producer/profile pins are not relabeled.

## Exact unchanged evidence

All59 production Solidity sources remain byte-identical to the starting
revision, as listed in [scope.json](scope.json). The existing
[3% record](../contribution-loss3-20261109/VERIFICATION.md) therefore retains its
normal90-source build,47 size gates+2 data gates,13 distinct selected Solidity
successes+1 offline fork skip and558 strict static records(11 reassessed/547
exact referenced-source reuse). These are reused records, not new executions.

Prior [mint/V10](../opensea-integration-20261109/VERIFICATION.md),
[manual management](../operator-management-20261109/VERIFICATION.md),
[actual source9](../source9-actual-entry-20261109/VERIFICATION.md) and
[market findings](../market-qualification-20261109/REVIEW.md) retain their exact
source/fixture/environment limits. No counts from overlapping stages are added.

Current reference checks cover39 contracts,906 functions,39 constructors,
13 receive hooks and958 operator rows without explanation/input/output gaps.
Examples remain unresolved templates with readiness false. Generated Todo,
local documentation links, immutable evidence hashes and exact staged/committed
Python import closure are checked separately before publication. Document checks
are not transaction simulations, provider admission or evidence of deployed state.

[Final gate records](final-gates/verification.json) retain reference/operator/Todo
checks and strict coverage against the saved analyzer output, without rerunning
the analyzer. The unconfigured production example still returns`ready:false`
and`deployment_authorized:false`; its issues are missing/unqualified inventory,
not a count of newly discovered bugs. The first driver omitted the CLI's required
`--config` flag, then tried to parse empty argparse stdout. That failed attempt
is retained; only the corrected final command ran again. The four earlier
successful gates were not repeated.

[Final integrity](final-integrity.json) verifies the59 unchanged Solidity files,
all958 unchanged example rows,77 preserved task IDs/order/statuses, local file
links, nested evidence manifests and the protected files/signer boundary.
[Artifact hashes](artifact-sha256.json) bind this report and its retained evidence.
External pages and fragment anchors are not comprehensively revalidated here.
