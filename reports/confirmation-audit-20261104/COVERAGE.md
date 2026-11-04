# Confirmation audit matrix

November4,2026. [Review and findings](REVIEW.md), [verification](VERIFICATION.md).
S=source inspection; N=fresh selected Python execution; R=prior source-scoped
execution referenced without rerun; Q=real qualification remains open.

| Boundary | Reviewed behavior and evidence |
| --- | --- |
| Threshold versus range |85%actual centre-to-boundary ZZZ-in-ETH distance, not85%absolute price change or actual range exit. Physical/reference corroborate the same side. S; N current-policy reader tests; R actual-core sampled journey. |
|600-second window | Same identity/side, first/last ordering, recent final observation and elapsed duration. Gap0 stopped,300inclusive,301stale. S contract/helper/unit bodies; R latest actual-core600-second sequence. No new contract mutation. |
| Re-entry/reversal/identity/policy | Negative observed condition must clear, not renew after recovery. Monotonic revisions prevent change-and-restore reviving evidence; entry preserves geometry. S/N; R actual-core entry-during-samples. Hidden moves between checks remain Q/limitation. |
| Feed/reference failures | Missing/disagreeing/invalid data fail closed; caught on-chain observe failure deletes within a successful reset result. Off-chain incident flags require confirmed clear. N worker fault/reset/acknowledgement tests; S contract try/catch and read projection. Live source independence Q. |
| Timing and enrollment | Hard12hours separate from600/240/300 and60–300jitter. Raw cooldown reads and near-eligibility paid enrollment; earlier maturity/cooldown deadlines. N existing/current-policy tests plus new actual-daemon deadline regressions. Actual inclusion Q. |
| Outer loop and overhead | New deadline-aware polling and monotonic sleep prevent the full interval/watchdog overhead from overriding saved wakes. N positive/negative controls, simulated90seconds of work and two-second pulse overhead. No live latency measurement. |
| Multiple buckets | Earliest saved deadline first; one serial sender. N multi-bucket priority/next-wake tests. Several due windows may still exceed one sender's real capacity; no SLA. |
| Pending, retry and global faults | Pending-first same-hash recovery, existing exponential global-error backoff and paid retry truth preserved. New timer never submits work or skips receipt verification. N recovery/nonce/global-error tests. Real crash/off-host restoration Q. |
| Restart/storage/clock | Saved jitter/nonce/spend records retained; local monotonic anchor is never persisted. Invalid new head cannot replace it; stale/retreating clock falls back. Failed save cannot authorize signing. N new/current incident tests; real Unix disk/watchdog qualification Q. |
| Clear-only router independence | Existing incident reset gets priority without swap-router metadata; blocked reset remains queued and is not renewed. Two negative controls fail before correction, pass after. N; normal route and price checks unchanged. |
| Authority and writes | Global sealed/authorized/canonical checks remain before priority. observe/reset require keeper; configure is governance-only. Normal Vault/Budget and exact financial/fingerprint checks remain. S; N existing revocation/submission tests; prior authority R. |
| Manual/emergency exceptions | Deliberate geometry applies after hard cooldown without ordinary window; emergency financial/timing bypass is paused governance-only and never automated. S, existing current-policy N. Accepted governance trust is not removed by this audit. |
| Jitter limits | OS-random60–300, excludes previous chosen delay, saved before use, no redraw for same candidate/restart. On-chain guards constrain a keeper key; local jitter cannot prove which software it runs. N current-policy schedule tests. |
| Watchdog/stop | Monotonic wait still pulses the main thread and checks shutdown between bounded sleeps; once/initialize/resolve dispatch unchanged. N affected main-loop tests; actual systemd/socket/Unix host unchanged and Q. |
| Economics and principal | No fee split, shares, contribution floors, compounding/burn behavior, custody or permission change. All52production Solidity/31dependency/4build-input pins unchanged; reuse43normal gates at those pins. No new financial-accounting campaign or market-profit test. |
| Current evidence versus deployments | New helper tests use source6 inert RPC; old profile fixtures retain explicit versions. Existing Anvil, journals, servers, sites and heartbeat remain unchanged. Matching release rollout and independent audit Q. |

Current files inspected include Confirmation, Strategy, PortfolioPolicy,
Vault/Budget readiness and fingerprint boundaries; the shared observation codec,
keeper condition/priority/submit/receipt/state/health/loop and operator procedures.
An inventory/source read is not behavioral execution of every called function.
