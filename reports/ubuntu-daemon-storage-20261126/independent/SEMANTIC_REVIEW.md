# Independent c811 semantic review — 26 November 2026

Status: independent source/design review complete for the exact candidate below; actual execution results require separate saved-vector review. No tests, network calls, server actions or production modifications performed by this reviewer.

## Final pre-execution candidate review

The independent static review approved model `a02747cd750363b04280d0f01438338bfbbc4df73065d1d5a74b6825a1924eb4`, native control `04943410dbb51c5f019ba6f8bd3c4d752653d7987631f02ec9865e90ee83f1bb`, capsule extension `1a7bf7d6299a2283017aea79981c70b07d5aae6629f9838f8d85dc7bdbb39a54`, packager `c70ddd1b497d7428bbe3d8fc23260bf58e95ab9bc96c3890e859addae1077c82`, and parent `cc590a414d4344edf5fd6b9af8ae7315bbaf3641da6837d02bc7bddb7b189b40`. No remaining blocking static issue was identified in that candidate. Actual run results remain a separate obligation.

Preparation defects were corrected before execution: final-evidence failure cannot skip child cleanup; the unprivileged model can read only the exact root-owned public resolution marker; archive/public-output lists include the new recovery vectors; the parent waits for the actual natural EACCES exit before fencing; log reads wait for an empty writer group; the hash-only resolver does not use the old settled-resolver postcondition; and semantic health-configuration digests remain distinct from raw configuration-file digests. Post-resolution one-second local block mining preserves fresh head reads during the unchanged 240-second service wait, after recording exactly twelve confirmation blocks. These are harness preparation corrections, not production behavior changes or repeated failed financial campaigns.

## Actual outcome and separate reconciliation scope

The original c811 model and orchestration remain **NONPASS**. The final harness incorrectly required at least 239 seconds between receipt-recovery health and the next healthy cycle. The actual keeper preserves an earlier known confirmation-check deadline: its `poll_delay` intentionally prioritizes that deadline before the refresh-only outer interval. The saved recovery schedule has `last_checked_at=1795697384`, `next_check_at=1795697624`; the final schedule records the next sample at `1795697626`. The actual stock log records confirmed receipt accounting, a degraded recovery cycle, then a healthy normal cycle 228.258214 seconds later. Configuration remains 240 seconds. This is expected deadline prioritization, not a shortened configuration or a production defect.

A separate bounded, read-only capture of the already stopped lab preserves its final healthy record and exact settled journal. The separate reconciliation tool checks only supported recovery/health/accounting evidence and explicitly keeps the original timing assertion false. No financial scenario or old test body is replayed. Because the model refused before its planned `FINANCIAL_AFTER` read, this new campaign has no independent post-harvest physical/rights/backing vector; earlier proofs retain their original source scopes. The full originally planned scenario must not be relabelled as passed.

## Source facts

- `submit` durably saves a hashless exact intent before launching bounded real Cast. A validated returned hash is put into memory before the second atomic save. A pre-replacement EACCES therefore leaves the older complete hashless intent on disk even when the in-memory object contains a hash.
- `run_cycle` logs sanitized `cycle_failed` before attempting the error-health write. A second EACCES while writing health escapes to the CLI handler, which logs `keeper_halted` and exits 1. A stale/running health file is not a success signal.
- `poll_pending` returns a recovery block for a hashless intent without signing. Current receipt recovery checks original identity, captured fees, canonical inclusion, twelve confirmations, final header and previous anchor before copy-on-write accounting publication; a failed save restores the prior in-memory receipt state.
- `resolve_pending` checks the human-supplied candidate against the actual transaction before publishing its hash. It can exit successfully while that transaction remains unmined: CLI success is not itself receipt completion. No `--live` is permitted for the explicit resolver in this rehearsal.
- `atomic_json` creates, fsyncs and atomically replaces a private temporary file, then fsyncs its parent. This case targets EACCES before temporary creation; it must not claim directory-fsync or physical power-loss durability.
- Local process locks do not establish cross-host fencing. Whole owned cgroup emptiness and exact old process generation death are required before the resolver/replacement writer.

## Required composed proof

1. Current HEAD production snapshot and frozen helper/tool/input pins; real stock daemon and real Cast under UID/GID 65534 in a private network.
2. Exactly one original raw submission; strict nonzero accepted hash captured from the private node and independently matched to the durable original nonce, sender, target, calldata, value, gas and fee review.
3. Change only the new lab actor directory to mode 0500 after acceptance and before returning the original hash to Cast. Preserve exact previous journal bytes; no mocked storage exception or altered production writer.
4. Native first main exits due to genuine journal-write EACCES, with original sanitized diagnostic followed by the failing health write; original service group is empty.
5. Repair only that directory to 0700, retain exact configuration/journal/lock inode, restart the actual stock service, and observe a fresh `recovery_required` health record with the same hashless intent and no second send.
6. Fence that group before the explicit no-live resolver. If resolution is deliberately while unmined, require pending except hash to remain exact and then genuinely mine twelve-confirmation depth before live daemon receipt recovery.
7. Authenticate original transaction/receipt/header/head, canonical execution price, gas and actual charge, inclusion-day spend, nonce 0→1, receipt anchor and harvest clock. No lost intent, resend, duplicated cost or fabricated replacement.
8. Complete a fresh actual healthy normal cycle after recovery while retaining the configured 240-second interval and hourly harvest. No shortening for a fast pass.
9. Compare all captured owners/shares/membership/weights, LP custody/identity/ticks/liquidity and money/reserve/backing vectors, not only totals.
10. Stop owned keeper/resolver/model groups and preserve exact final journal bytes plus all original host service states. Keep original failures and distinguish this finite two-NFT, single-main, zero-fee case from all-feature or target-provider qualification.

## Harness pitfalls already identified

- Old c806 native resolver helpers require the pending transaction to be settled immediately; do not reuse those postconditions for a new unmined hash-adoption phase.
- `B.save` is exclusive: do not reuse it for mutable cumulative phase files/configuration. Mutable evidence needs a fixed-path, bounded atomic writer; original production journal semantics stay unchanged.
- Transient units may disappear after clean stop. Capture synchronous resolver completion and exact reviewed launch definition before collection; do not infer success from absent properties.
- A failed evidence write must not prevent nested keeper-first/model-second cleanup. Parent deadline and cleanup reserve remain bounded.
- Export no keystore/password, raw signed transaction, signature components, credentialed endpoint or complete process argv.
