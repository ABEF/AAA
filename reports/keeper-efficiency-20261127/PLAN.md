# Keeper output, storage bounds and current-code review

Baseline: `1605dac2b2fd30e3b23e0adfc2c09ab8a913e2b7`, 27 November 2026.

Review current keeper logging, health output, exact recovery, scheduled selection
and staging backup/export paths against their readers. Distinguish today's inert
rehearsal helpers from the unchanged production source; retain historical report
bytes rather than editing successful/failed evidence to fit later improvements.

Implement justified changes only: compact log/health JSON without suppressing
events or fields; exact encoded-output bounds before replacing a scheduler
selection or staging export; bounded desktop snapshot reads and archive count;
bounded health-ID previews with honest full counts/digests and the complete
inventories retained in the original transaction journal.
Preserve journal formatting, schemas, pending hashes, nonce/spend/fee accounting,
backup originals, alert queues, signing and financial/resource safeguards.
No automatic deletion, pruning, changed clock, live rollout or monitor restart.

Review each changed branch and its callers before verification. New focused tests
must cover the refusal boundary, preservation of previous bytes, logical output
equivalence, critical event retention and safe failure behavior. Use fixture setup
only, without executing existing test bodies. Distinguish new tests from saved-data
review and static inventory/publication checks. No unchanged suite or server
campaign is needed for these local output/publication changes.

Refresh the source-bound inventory and its current pointer; frozen F6 Solidity,
dependency/control maps, ABI and historical inventories remain unchanged. Update
the single Todo, current findings, feature reference, concise operating guidance,
roadmap/release boundaries and repository handoff. Keep source adoption separate
from installed services and old pinned packages/policies. Preserve four unrelated
dirty files and every existing environment, journal and paused heartbeat.
