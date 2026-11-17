# Python tool impact follow-up

This follows the repaired tests into the actual tools and their wider consumers at `fdb7562bf56b11d8bade612fdaf7f9a54daf118a`. It does not treat fixture pass counts as proof of current Solidity, live RPC, signing, operating acceptance or production readiness.

## Confirmed implementation fix

The manual preparer reread its final simulation height too early. A subsequent short reorg could replace that height while preserving the older confirmed snapshot; if the latest height advanced, the old conditional comparison skipped it and returned a review whose final simulation anchor was now orphaned. The new faithful RPC regression fails before the fix while its healthy-advance control passes.

`manual_lp_review.prepare` now rereads the exact simulated height after `_finish` and the final head/header read, regardless of whether that head is newer. It preserves request count, original frozen gas/calldata/deadline, budgets, custody/control validation and no-force-fallback behavior. Multi-call reads remain non-atomic, so this does not promise immunity to changes after the last response or provider dishonesty. On-chain inclusion checks and operator revalidation remain mandatory.

New tests cover active refusal, healthy advancement with identical frozen envelopes, explicit Parked D, CLI cause/no artifact, and both protected/healthy management behavior. Production management already had the correct late recheck; no management code change is needed.

## Wider test and implementation conclusions

Three management tests had inherited the premature after-estimate fixture mutation: physical price, custody nonce and allocation-cursor/current-owner changes appeared during the first immutable anchor. They now mutate after the initial exact call, between anchors, and prove final-stage failure or admissible movement. The local-selection mutation test remains unchanged because a local input can legitimately change at any time.

The earlier standalone harvest tests mocked `submit`, proving scheduling but not the entire preflight. Two new current-accounting7 cases use real `Keeper.cycle` and `Keeper.submit` in dry-run mode with injected RPC. A slow maintenance fault crosses the hourly boundary; the harvest reaches bounded exact calldata simulation/estimation. A malformed void result stops before estimate/dry-run publication and leaves harvest clocks, pending state and spent balances unchanged. No keeper behavior is altered.

The real current normal-profile validator accepts actual pinned Forge version/config metadata under a sanitized environment. Raw configuration is not saved. This confirms that the previously repaired permission expectation also matches actual tool output; it does not build, run tests, query a chain or approve a deployment.

| Area | Actual functions / consumers | Result |
| --- | --- | --- |
| Manual active B/C/D and explicit parked D | `zzz_ops.manual_lp_review.prepare`, `simulation`, `Reader.snapshot`, `controls`, `diagnostic`, `write_exclusive`; consumers: `scripts/prepare-manual-lp.py`, `scripts/rehearse-manual-recovery.py`, `scripts/rehearse-manual-reference.py` | Confirmed final-anchor reorg race fixed. Confirmed snapshot and later simulated block are different obligations; both must survive final reads. No extra request, reprice, resimulation or force fallback added. |
| Unsigned management custody and terminal batches | `zzz_ops.management_review.prepare`, `simulate`, `_source_pins`, `management_custody.observe/call_spec`, `management_exit.observe/call_spec`; consumers: `scripts/prepare-operator-management.py`, `scripts/rehearse-manual-recovery.py` | Actual production late-anchor ordering already correct; new reproduction proves refusal and healthy advancement. Three moving-market/control test hooks were premature at the first immutable hash; moved between anchors with explicit final-stage assertions. Source pin closure includes changed manual helper, so newly prepared management reviews record its new hash; old records remain historical. |
| Independent hourly harvesting and submission | `keeper.monitor.Keeper.cycle`, `Keeper.submit`, `keeper receipt and harvest-clock authentication`; consumers: `keeper/monitor.py operating worker`, `keeper/operation_review.py diagnostics`, `scripts/run-keeper-tests.py focused runner` | No keeper production change. Prior scheduling tests mocked submit; two new current-accounting7 cases now reach actual dry-run submit, bounded simulation/estimate and reject malformed returns before estimate without pending/spent/clock publication. This proves Python scheduling-to-preflight composition, not EVM harvest or live signing. |
| Normal verification and trusted builds | `scripts/verify-normal-profile.py.inspect_profile`, `zzz_ops.deployment_plan.validate`, `Artifacts.check_sources`, `prepare`; consumers: `scripts/verify.sh`, `scripts/verify-normal-profile.py`, `scripts/prepare-deployment.py`, `zzz_ops.preseal_plan.prepare` | Actual pinned Forge version/config metadata now passes the real validator with sanitized environment, confirming the preceding permission fix beyond its injected fixture. No build/compiler/test/provider invoked in that check. Current bare-scheme URI rejection, explicit historical build admission and unknown/null readiness remain intact; no new defect reproduced here. |
| Unsigned pre-seal and function/read inventory | `zzz_ops.preseal_plan._seal_boundary_review`, `prepare`, `scripts/prepare-preseal.py completeness/publication`; consumers: `12-family conditional configuration reviews`, `seal_boundary_review constructor/read appendix`, `operator guide/function reference` | Current code reread; prior private-getter and scheme-only root mismatches are corrected at fdb7562. Preparation still performs no RPC and issues no seal calldata, authority proof or content/provider/release acceptance. No unchanged cases rerun. |

## Verification and limits

- Before fix:2 new cases,1 meaningful regression failure and1 healthy-advance control pass; no setup errors.
- After fix:11 distinct affected methods pass in two source-scoped selections:8 new methods and3 corrected management methods. No unchanged suite runs.
- Actual pinned Forge metadata-only normal-profile probe passes. No compiler/build, EVM, public RPC, signing, site/service or existing journal/chain action occurs.
- All61 production Solidity sources and all4 protected dirty files match the new-turn baseline. Source comparisons show only manual `prepare` changed among the examined production functions; other publication, financial, readiness and keeper functions remain exact at the function-body level. That comparison is not a new full-transitive audit.

Original failure, exact method IDs, source brackets, probe settings and source/pin comparisons are retained in [TOOL_IMPACT.json](TOOL_IMPACT.json) and the prefixed `tool-*.json/.log` records. The earlier30 and later29 per-method records retain their original source scopes; this follow-up does not relabel them.
