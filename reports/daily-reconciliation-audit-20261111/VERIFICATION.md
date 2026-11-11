# Verification and evidence boundary

## Fresh checks

- [Claim planner](backend/claim-cache-final.json):28distinct focused planner,
  worker and HTTP methods pass,0failures/errors/skips. Three new methods cover
  the two immutable selectors, request isolation, exact-block/pinned-target
  restrictions and mutable-read exclusions. Same18-unit payout; measured
  capability/binding reads18→6. Injected RPC, not live provider acceptance.
  Final cleanup removes one extra blank test-file line at EOF; [complete AST
  equivalence](backend/test-format-equivalence.json) preserves the original run's
  source hashes without repeating unchanged tests.
- [Strict-review errata](contracts/ERRATA_VERIFICATION.json): corrected full
  567-record review passes against existing actual analyzer output;44checker
  regressions pass. Two rationale fields plus provenance change; remaining565
  are not newly re-audited. No analyzer/compiler rerun.
- Both reference generators pass:40contracts,956functions,40constructors,
 13receive hooks,0explanation/input/output gaps;1009operator rows with
  `ready_for_submission:false`. Templates remain unresolved examples.
- Sole Todo generation/check, current-document local links, history provenance,
  preservation and exact staged/committed Python publication checks are recorded
  in [completion checks](COMPLETION.json). Counts are not added across scopes.
- History verification retains310original pointers/hashes, prior main-history
  inventory and5,517old-report bytes; current task links resolve. Bulk extraction
  hash/count checks use the explicit external directory; no missing external
  archive is silently described as verified by the standalone public verifier.

## Reused, not rerun

All61production Solidity files remain equal to the exact normal a846 source
record used by the [reference-execution campaign](../reference-execution-20261111/VERIFICATION.md).
Its compiler/runtime/initcode, actual-core, funded Entry, ABI and static analysis
retain their original fixtures/source/economic/gas limits. Four immutable actual
trace cases/replays and all browser executable source remain unchanged. Website
changes here are documentation/comments only; no redundant browser suite ran.

The prior323-method backend record includes the now-changed planner in its broad
hash bracket. It is reused only for unchanged components with original hashes;
it is not323fresh passes of this tree. The new28overlap earlier methods and are
not added to that total. The two-selector change is outside checkpoint1/2
semantic source closures; it alone does not require checkpoint regeneration.
The earlier ABI-helper adoption still requires explicit checkpoint rebuild/re-pin.

No test demonstrates all future markets, arbitrary tokens, target chain fees,
continuous uptime or absence of exploitable defects. Actual feeds/routes/VRF,
OpenSea, authority/provider/hosting/recovery/gas and independent acceptance
remain open. No financial limit, signer, service/site, existing chain/journal or
heartbeat changed.
