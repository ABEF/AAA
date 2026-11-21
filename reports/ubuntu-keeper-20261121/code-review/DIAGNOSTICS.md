# Direct keeper diagnostic review

Two confirmed differences between the read-only operation report and the normal
worker were corrected in `keeper/operation_review.py`. No contract, signing,
scheduler, journal or service behavior was changed by these corrections.

| Finding | Correction |
| --- | --- |
| Submission fee profile2 was simulated without its live type-2/zero-tip fee envelope, with the gas quote obtained afterward. | Capture one positive quote before simulation and reuse the exact type, fee cap and zero tip for simulation, estimation and bounded cost. Profile1 retains its existing envelope and quote policy. |
| An in-range position could be reported compound-eligible despite a tracked nonempty or malformed confirmation record that makes the actual worker wait for a reset. | Reuse the existing pure confirmation-record authenticator at the report's pinned block. Report the reset requirement or unavailable evidence without mutating the journal. Independent harvesting remains reportable. |

Four new cases reproduce the original errors against the archived HEAD module:
four assertion failures, no setup errors. The corrected module passes all four
new cases plus three directly affected existing methods: **7 passes, no skips**.
No unchanged suite, public RPC, wallet signing or running service was used.

The runner is `check_diagnostic_fixes.py`. Exact before/after logs, method names
and source hashes are retained externally under
`ubuntu-keeper-20261121/code-review/diagnostics-before` and `diagnostics-after`.
The new tests reuse the existing deterministic transcript fixtures without
inheriting or duplicating their test classes.

The report still does not predict worker jitter, scheduling or future inclusion.
Those limits are explicit and unchanged. These diagnostic checks do not qualify
the unfinished normal-daemon Ubuntu rehearsal.

One additional NEW confirmation3 threshold-return method passed separately.
[Its preserved original console result](CONFIRMATION3_TOOL_RESULT.json) retains
the exact invocation and combined output; separate stdout/stderr files were not
captured. This uses an accounting5 transcript, not F6 runtime qualification.
The original seven-method record keeps its original test-source hash. Distinct
diagnostic total: five new plus three affected existing methods, eight passes.
