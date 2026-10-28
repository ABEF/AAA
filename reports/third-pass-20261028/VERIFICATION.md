# Third-pass verification

Baseline `cb0aadfe61b0bdcebab1838adbcf1b5835215510`, main. Calendar source window:
October26-28 Paris, completedOctober29. [Review](REVIEW.md),
[35-commit/71-path inventory](three-day-inventory.json),
[exact machine summary](verification-summary.json) and
[external receipt hashes](external-artifacts-sha256.json) retain the source scope.

## Fresh affected checks

**152 distinct Python methods:151 passes, one explicit Unix permissions skip.**
21 new regression methods are included once. This is a source-scoped union:

| Selection | Result |
| --- | --- |
| Checkpoint/reset and affected recovery | 75methods:74pass/one unsupported Unix-runtime-permissions skip, including seven new methods. This run precedes the subsequent royalty-worker repair; only that loaded file later changed. |
| Final LP/royalty conversion admission | 40methods pass, including12new methods across native v4 and both wrapper profiles, both ledgers, malformed/future headers, depth retreat, exact300/301age, unchanged floors, actual malformed-worker/due-harvest scheduling and the final post-quote checks/deadline. Healthy quote-eligible scans now use six header calls (one deliberate extra final head); disabled paths retain two and low-amount paths four. Earlier37methods overlap and are not added again. |
| Final indexer/log ingestion | 37methods pass, including two new methods covering malformed head quantities and legitimate zero/confirmed-only ingestion. Existing reorg/log safety cases remain in this affected scope. |

All recorded runs use inert synthetic transports with outbound sockets and
subprocess signing disabled. Before/after loaded-file hashes have zero in-run
drift. They do not qualify real providers, browser extensions, Linux operating
processes or target-chain economics.

## Negative controls and fixture correction

- The initial seven checkpoint methods fail three methods against the original
  handler, without errors; actual prior receipt anchor and no-pending state are
  required to reproduce the missed boundary.
- Original conversion observations reproduce uncaught missing/null/bool timestamp
  errors and a future cutoff reaching unsigned submit review. The first new suite
  also wrongly expected four existing header calls; it was corrected to the
  actual five. That fixture error is retained, not called a product regression.
- Independent review then reproduced two distinct tail failures after the quote:
  lost depth/age/order reached review, or an advancing head kept the old deadline.
  A third low-amount control passed. The corrected source deliberately adds the
  final head check; its six-call expectation records that safety/cost tradeoff,
  rather than changing the old count to manufacture a pass.
- The original indexer admits four tested noncanonical representations; other
  malformed inputs already raised generic parse exceptions. The final gate
  consistently supplies `invalid_header`. Subtest failures are not extra methods.

## Exact unchanged evidence reused

No Solidity source/test, dependency or normal build input changed. The142execution
pins,46normal production source pins,31dependency pins and four build-input pins
match [the earlier evidence](../practical-improvements-20261028/VERIFICATION.md).
Its217affected Solidity passes and39normal size gates are reused, not rerun or
added to the fresh Python count. Bytecode headroom and ABI/storage/economics are
unchanged. Exact release constructor/target/maximal-catalog gas remains unqualified.

Static contract/admission/parent review notes contain source hashes and explicit
no-finding/limited-hypothesis conclusions. Inspected file/commit rows are not
execution coverage of all665functions. No global no-bugs, attack-profit immunity
or production approval is asserted.

## Preservation

External receipts, negative controls,473committed baseline files and the combined
three-day patch remain under the local `third-pass-20261028` evidence directory.
The machine summary verifies four original dirty files and2,224historical report
files unchanged. Historical failures/counts retain their original revisions.
No service, website, Anvil, journal, public signer or paused monitor was changed.
Actual publication head/bytes are verified separately from saved local evidence.
