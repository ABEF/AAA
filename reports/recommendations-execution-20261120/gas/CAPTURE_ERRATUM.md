# Scope correction: estimate-request capture

The independent final review found that the report-only `gas-presync02/run.py`
recorder stores a reference to mutable transaction parameters. The script first
requests estimates with the full24M/32M envelope, then changes that same object's
gas field to the chosen padded allowance. Earlier saved estimate-request metadata
therefore shows the later value. Original script, wire, RESULT and archive bytes
are retained unchanged; they must not be relabeled as deep-snapshot captures.

The original full-cap envelope is a source-order inference, **not independently
authenticated raw request evidence**. This limits the wire claim, not the saved
estimate response or numerical padding calculation. The final padded call/trace,
copied submission and actual receipts remain independently available with their
recorded envelopes and values. The measured optional-preparation result and
original direct-cold refusal retain the limits in [the review](../GAS_REVIEW.md).

For future runs, snapshot request parameters at serialization time and retain the
exact outgoing bytes or their bound immutable capture. Never patch old request
metadata to match an intended envelope. No unchanged case is rerun here, and no
production contract/service defect or financial change is inferred from this
report-recorder issue.
