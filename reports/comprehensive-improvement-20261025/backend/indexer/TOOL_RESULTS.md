# Scoped tool results

- Original 80d330e indexer was loaded in isolation without reverting the working tree. The two new outage/malformed methods reproduce 12 expected failed subcases; raw output is baseline-negative-control.log.
- Final monitor: affected indexer file, 25 methods passed in 0.845 seconds. Original verification stdout is retained in the conversation; this is a transcription summary, not a raw stdout file.
- Added depth/genesis boundaries plus API projection integration: 3 methods passed in 0.147 seconds.
- 28 distinct methods pass across these scopes; no existing unaffected suite was rerun.
- git diff --check passed for owned files.

See receipt.json for exact sources, baseline and limitations.
