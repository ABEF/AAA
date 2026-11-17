# Operator-tool reconciliation and one additional stop diagnostic

Baseline main `1c18379b03b067de722d250cee1cc173acc4d635`.

The machine [finding map](TOOL_FINDINGS.json) follows the tool/backend-relevant groups in the five report families into current source. Earlier gas, output preservation, due-clock, private-read, source-binding and late-anchor fixes remain present. The original planner's build family is superseded by explicit `seal-boundaries-20261117`; old receipts and tests remain historical. Service-only compounding and direct-EOA envelopes are accepted boundaries, while real dependencies, gas/fees, operators and independent approval remain qualification work. These classifications do not manufacture new passes for unchanged code.

## Confirmed improvement

A complete pre-seal input may deliberately set the selected contribution pool's `operationsEnabled` to false. That configuration was accepted as a conditional unsigned plan, but `explicit_operating_stops` was empty when its other settings were healthy. Thus the declared diagnostics omitted a known stop even though readiness and approval correctly stayed false.

The new actual-planner reproduction demonstrates the omission, with an enabled-pool positive control. The planner now names each fully known disabled pool and states that **ordinary contributions, compounding and rebalancing stop for that pool**. It still preserves the supplied false setting and its exact ABI call. It does not re-enable anything, choose a route, change defaults/limits or change completeness into readiness. Producer/manifest hashes naturally change for new outputs; do not rewrite old artifacts to match them.

Source trace: normal placement/balancing uses operations-enabled native configuration/price validation; `Strategy.compoundPlan` and ordinary rebalance eligibility retain the flag. Harvest uses `LPPositionExecutor.collect` with `executionConfig(pool,false)`, and reward claims follow their own ownership/accounting/lifecycle controls. Raw custody and explicit emergency operations also retain separate permissions and selected checks. Therefore the warning is pool-specific ordinary LP management, **not a global pause or a statement that harvesting/claims stop**. Their independent token/provider/custody/lifecycle constraints still apply.

## Verification and preservation

- Before fix:2new methods,1meaningful diagnostic failure and1healthy control pass; no setup errors.
- After fix:the2affected methods pass using actual pre-seal preparation/current trusted ABI with synthetic inputs. Exact operation argument stays false, calldata remains present and every readiness/approval flag stays false.
- Source brackets, IDs, failures and raw logs are in `TOOL_STOPS_BEFORE/AFTER.json/.log`.
- All61 production Solidity sources and four protected dirty files match the prior preserved baseline. Existing reports, default limits, ownership/custody/economics, signer/public-null configs, chains, journals, websites/services and paused heartbeat remain unchanged.
- No unchanged suite, compiler, static analysis, EVM/RPC/provider campaign or live operation was rerun. These2local planner methods do not qualify an actual stopped/restarted deployment or prove all possible operation behavior.
