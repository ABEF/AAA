# Keeper operating/read-only partition review

Static review ledger: 120 named functions. This records source inspection, not dynamic coverage. No server, chain, signer or paused heartbeat was invoked.

## Confirmed improvements

- OPS-01: staging initialization now uses the existing bounded Cast helper for its two wallet commands; deadlines remain60/30 seconds.
- OPS-02: forced-command SSH monitor now bounds total captured bytes during reading;1MiB combined stdout/stderr,30-second work and2-second cleanup, complete result only.

## Scope and unresolved items

- Source identities are local-file observations, not running-code attestation.
- Legacy accounting3 rehearsal and fixed staging observer have remaining capture/retention boundaries; no automatic rollout or broad qualification claim.
- HistoricalNov21 failed-daemon wording needs contextual correction in current recovery guidance.
- Full provider fees, off-host restore/fencing/alerts, restart storms, physical storage durability and sustained operation remain release work.

## Function ledger

| File | Function | Lines | Review status |
|---|---|---|---|
| keeper/ops.py | _read_required_json | 24–31 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | _review_bucket | 34–38 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | digest | 41–42 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | timestamp | 45–50 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | health_check | 53–98 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | preflight | 101–164 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | create_snapshot | 167–191 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | verify_snapshot | 194–208 | Static inspected; no dynamic pass claimed |
| keeper/ops.py | main | 211–237 | Static inspected; no dynamic pass claimed |
| keeper/health.py | source_hashes | 20–23 | Static inspected; no dynamic pass claimed |
| keeper/health.py | digest | 26–28 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _uint | 31–32 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _hash | 35–37 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _health_profile_valid | 40–58 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _confirmation_bindings | 61–73 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _confirmation_roles | 76–78 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _confirmation_capabilities | 81–87 | Static inspected; no dynamic pass claimed |
| keeper/health.py | _maintenance_policy_valid | 90–104 | Static inspected; no dynamic pass claimed |
| keeper/health.py | observe_confirmation_health | 107–149 | Static inspected; no dynamic pass claimed |
| keeper/health.py | confirmation_reasons | 152–248 | Static inspected; no dynamic pass claimed |
| keeper/health.py | execution_reasons | 251–346 | Static inspected; no dynamic pass claimed |
| keeper/health.py | summary | 349–371 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | ReadOnlyKeeper.save | 28–28 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | ReadOnlyKeeper.submit | 29–29 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | ReadOnlyKeeper._validate_signer | 30–30 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | ReadOnlyKeeper.poll_pending | 31–31 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | ReadOnlyKeeper.initialize_state | 32–32 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | PinnedReads.__init__ | 36–38 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | PinnedReads.call | 40–53 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | PinnedReads.eth_call | 55–56 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | _header | 59–63 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | _attempt | 66–70 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | _row | 73–77 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | _set | 80–82 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.__init__ | 86–92 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.read | 94–98 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.uint | 100–101 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.flag | 103–106 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.pin | 108–117 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.bucket | 119–136 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.market | 138–143 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review._harvest_ticks | 145–155 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.harvest_custody | 157–201 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.execution | 203–208 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.budget | 210–216 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.financial | 218–248 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.financial.maintenance | 219–224 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.financial.current_idle | 236–239 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.schedule | 250–260 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.compound_confirmation | 262–283 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.simulate_action | 285–366 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.simulate_action.gas | 322–330 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.operations | 368–549 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.operations.complete | 387–395 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | Review.operations.clock | 511–518 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | review | 552–606 | Static inspected; no dynamic pass claimed |
| keeper/operation_review.py | review.controls | 588–598 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _remote_error | 23–30 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _EndpointBudget.__init__ | 34–42 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _EndpointBudget.check | 44–46 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _EndpointBudget.transport | 48–71 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _EndpointBudget.call | 73–84 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _approval_trace | 86–119 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe | 121–253 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.observe | 149–162 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.genesis | 164–168 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.head | 170–174 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.same_block | 188–193 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.hex_result | 196–204 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.reject_unknown_hash | 208–214 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.approval_trace | 217–219 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.tagged | 223–225 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | probe.receipts | 227–248 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _Parser.error | 257–257 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _read_config | 259–271 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _read_config.pairs | 262–267 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | _read_config.constant | 268–268 | Static inspected; no dynamic pass claimed |
| keeper/probe.py | main | 273–295 | Static inspected; no dynamic pass claimed |
| keeper/staging.py | main | 22–64 | Static inspected; no dynamic pass claimed |
| keeper/staging.py | main.send | 33–37 | Static inspected; no dynamic pass claimed |
| keeper/staging_observer.py | main | 21–46 | Static inspected; no dynamic pass claimed |
| scripts/check-staging-monitor.py | validate_export | 21–37 | Static inspected; no dynamic pass claimed |
| scripts/check-staging-monitor.py | main | 40–63 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | check | 34–35 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | wait_until | 38–46 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | rpc | 49–56 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | FaultProxy.__init__ | 60–62 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | FaultProxy.__enter__ | 63–86 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | FaultProxy.__enter__.Handler.log_message | 66–66 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | FaultProxy.__enter__.Handler.do_POST | 67–82 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | FaultProxy.__exit__ | 87–88 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | FaultProxy.fault | 89–90 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.__init__ | 94–95 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.__enter__ | 96–99 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.start | 100–135 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.__exit__ | 136–138 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.spawn | 139–142 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.kill | 143–147 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.write_config | 148–148 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.cli | 149–156 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.worker | 157–157 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.state | 158–158 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.health | 159–159 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.nonce | 160–160 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.tx | 161–164 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.admin_call | 165–165 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.count | 166–166 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | Lab.settle | 167–167 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | run | 170–267 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | main | 270–304 | Static inspected; no dynamic pass claimed |
| scripts/rehearse-keeper.py | main.record | 285–286 | Static inspected; no dynamic pass claimed |
| scripts/run-keeper-tests.py | select_tests | 56–73 | Static inspected; no dynamic pass claimed |
| scripts/run-keeper-tests.py | sha | 74–74 | Static inspected; no dynamic pass claimed |
| scripts/run-keeper-tests.py | inputs | 75–85 | Static inspected; no dynamic pass claimed |
| scripts/run-keeper-tests.py | Results.__init__ | 87–87 | Static inspected; no dynamic pass claimed |
| scripts/run-keeper-tests.py | Results.startTest | 88–88 | Static inspected; no dynamic pass claimed |
| scripts/run-keeper-tests.py | main | 89–111 | Static inspected; no dynamic pass claimed |
| zzz_ops/read_process.py | _windows_available | 23–40 | Static inspected; no dynamic pass claimed |
| zzz_ops/read_process.py | _cleanup | 43–59 | Static inspected; no dynamic pass claimed |
| zzz_ops/read_process.py | run_read_process | 62–142 | Static inspected; no dynamic pass claimed |

## New verification

Windows stage1 retained10 named passing log records:6 real disposable-child capture boundary methods and4 structural/inert-monitor integration methods. The original result is interrupted/nonpass; its source-before/after maps were lost and are not admitted. See [original marker](../verification/utility-original/RESULT.json), [log](../verification/utility-original/RESULT.log) and [log reconciliation](../verification/utility-original/LOG_FOLLOWTHROUGH.json). Linux-specific inherited-pipe execution belongs to the separate Ubuntu partition. No SSH, staging initialization, network, key, service, journal or heartbeat action occurred in this Windows partition.

## Evidence interruption correction

The original stage1 producer is NONPASS/interrupted: SystemExit(0) was raised inside the Evidence context after finish(), so __exit__ replaced the report with its conservative interrupted marker. Preserve RESULT.json and RESULT.log unchanged. LOG_FOLLOWTHROUGH.json independently verifies10 distinct named ok records and Ran10/OK in that log; it does not restore the lost durable source-before/after maps or admit the original producer. No method was rerun. Earlier statements of a completed source-bound stage are superseded by this correction.
