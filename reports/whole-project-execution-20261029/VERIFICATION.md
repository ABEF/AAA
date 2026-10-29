# Verification and evidence scope

Reviewed2026-10-29. [Summary and exact method/source identities](verification-summary.json).
**Production NOT APPROVED.** No public transactions, deployment, installed
service/site change, journal reset, Anvil restart or signer modification occurred.

| Verification | Actual result and scope |
| --- | --- |
| Backend |96distinct methods:92pass/4explicit Windows skips for Unix permissions/locking/symlink cases. Separate59/state23/pool14receipts retain their exact source scopes. [Backend evidence](backend-evidence.json). |
| Keeper |64distinct methods pass:21new/43affected existing. Pending-first, guards, clocks,240-second polling, optional queues and historical compatibility exercised with controlled fixtures. Earlier123-method/intermediate runs are retained externally and not added. [Keeper evidence](keeper-evidence.json). |
| Artwork/catalogue tooling |14IPFS/resource/archive methods pass;7generator/catalogue methods pass, including normal versus optimized Python and exact existing1000inventory. No artwork/library regenerated. [Tooling](TOOLING.md), [IPFS log](ipfs-tests.log). |
| Deduplicated Python union |**180distinct methods:176pass/4explicit skips.** One identity overlaps the separate scopes above. This is a selected campaign, not a freshly run complete suite. The original unpublished history-test draft used by affected backend checks stays unstaged and source-pinned; no published CI pass is inferred. |
| New composed EVM checks |**2methods pass**,225.19seconds, no source drift: emergency mask composition includes successful no-price bypass controls; retained confirmation-policy callback mutation reverts all composed state, while the identical manifest succeeds without mutation.32mask cases are subcases of one method, not32tests. [Receipt](solidity-evidence.json). |
| Website metadata |3focused methods pass in an isolated exact source copy over all2784current references; future generator output matches every stored reference without rendering, fixed rarity is independent of dormant eligibility, preview wording agrees. Applied bytes are verified exact and actual app/generator syntax checks pass. [Changes](website-changes.json), [local application](website-application.json). No full website suite, new extension flow or fresh4 integration claimed. |
| Existing assets |Every2784approvedSVG passes stricter resource validation and its exact manifest hash.72historical metadata files, effective example ledger, manifest, signer/null configs and all other tracked website files outside the reviewed allowlist are unchanged. [Compatibility](asset-compatibility.json). No rendered visual QA/upload/pin/CID qualification. |
| Callable reference |122missing output notes merged while preserving all existing notes. Source-bound regeneration/check passes with zero purpose/input/output gaps.33contracts/696functions/33constructors/13receivers, exact ABI and source unchanged. [Merge evidence](reference-merge-verification.json). |

## Exact reuse and failures

The closed78-source production compiler input matches every current source and
dependency byte, with unchanged0.8.26/Cancun/viaIR/runs1/Yul-optimizer-off settings.
The prior final build-attempt011output and all39normal runtime/initcode gates
are reused at exact hashes, without recompilation or relaxed thresholds.
Vault runtime margin59bytes/initcode105; Manager initcode margin37; Strategy
runtime162; Migration runtime201. Exact dynamic constructor URI and target cold/
maximum gas remain unqualified.

Earlier131affected EVM results remain in the [feature report](../independent-rebalance-20261029/VERIFICATION.md)
with their original fixture/test/source pins. This campaign adds a test-only
callback seam in NativeVaultFlows; those older fixture hashes therefore differ.
They are historical evidence for unchanged production instructions, not131fresh
current-fixture passes and are not added to the2new methods above.

Negative controls preserve confirmed pre-fix acceptance of contradictory logs,
head-depth retreat, legacy receipt-price mismatch, ambiguous JSON/pool state,
optimized-away catalogue checks and alternate SVG resource channels. Keeper
baseline12selected methods produced11failing assertions/subcases across7methods;
this is not11distinct failing tests. Additional clock/config negatives are
retained. Initial fixture/import/Unicode-decoding/quoting failures and corrected
attempts are recorded externally; zero-test/import failures are not passes.
The report logs distinguish assertions/subcases from distinct method identities.
Final staged whitespace checking removed one extra EOF blank line in the earlier
unpublished reference-confirmation test; its executable content is unchanged.
That formatting correction does not refresh its earlier test receipt.

Original raw evidence, exact drafts/compiler/test inputs, before source, output
and failure logs remain under the external `whole-project-execution-20261029`
directory recorded in the handoff.2247previously tracked report files and the
four original unrelated dirty files remain byte-identical. Current report files
summarize evidence rather than overwrite prior runs.

## Remaining qualification

See [coverage](COVERAGE.md), [compiler applicability](COMPILER_DEPENDENCIES.md)
and the [sole Todo](../../TODO.md). Coherent dishonest providers, actual service
rollout/finality/load, economically profitable manipulation, live prices/routes/
VRF/OpenSea/authorities, immutable hosting, exact deployment arguments and
independent audit/remediation cannot be closed by these mocks/static reads.
No signing/payment/deployment permission follows from the audit or publication.

Publication and final documentation checks are recorded in [the publication record](PUBLICATION.md).
