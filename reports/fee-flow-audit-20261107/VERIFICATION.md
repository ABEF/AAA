# Verification and evidence limits

Campaign baseline mainc055684. No full-suite/publicCI, actual target-chain
gas/uptime/provider/marketplace or independent approval is claimed. Tests and
failures below are source-scoped; do not sum overlapping stages.

| Scope | Actual result / evidence |
| --- | --- |
| Converter/native floor | [Actual converter+Oracle summary](contracts-native-floor/SUMMARY.json): baseline6pass/5new failing controls; corrected11/11pass. Divergent/missing/stale native prices, non18/drifting wrapper, caller minima, proxy drift, lying output/faulty unwrap rollback and direct1:1 unwrap covered.157-source affected ABI typecheck, no ABI/selector/state declaration change. Venue/feeds/earned ledger/proxy are controlled fixtures, not production dependencies. |
| Keeper | [Package verification](keeper/package-verification.json):338distinct passes,2explicit environment skips across corrected stages; final22focused passes. Retained original oversized-window negative, stale-deadline/UTC-day negative, incomplete mock fee setup and other attempts. No signing/public transaction; sender mocked. Cast-not-installed and Unix-permission skips are not passes. |
| Earnings reader / actual wire | [Reader manifest](readers/MANIFEST.json):11new regressions plus affected exact-tree/source-wire tests, union28distinct Python methods across overlapping stages. New actual ONE producer method succeeds against final source,77logs/four26-field snapshots/95-source closure. Six outer rows changed: old fixture bytes are archived; new data was executed, not relabeled. Final4wire+11noop pass. Retains red no-op controls, SQLite cleanup and serialization failures. |
| Backend reviewed gas2 | [Root package](root/MANIFEST.json): API run56methods,14new cases plus affected transaction/planner cases. Covers strict limits/types/config identity, legacy1 unchanged, confirmed hash/number/time/gasLimit, block clamp, full padding, fee/balance refusal, no signing, bounded prefix continuation and same-hash policy drift. Per-instance isolation checks are interleaved, not an actual concurrent-host load test. No actual provider/workload qualification. |
| Release/reference checks | [Root package](root/MANIFEST.json):156methods across strict static-record checking, generated function/operator references, fresh exact-LP inventory/profile, production preflight and frontend policy/lifecycle readers. The95reference/static methods are included, not additional. |
| Whole Solidity ABI typing | [Root package](root/MANIFEST.json):317actual source/test/script/dependency files typecheck with0errors and exact before/after hashes. This is ABI typing, not317EVMtests or a full-suite execution. |
| Normal production graph | New closed `normal-final-4de5dcc67c`:87actual sources,46normal objects+2actual immutable data-carrier gates; all pass, unchanged compiler/settings/limits. Only converter and Rewards runtime objects change; Rewards differs only in metadata. Converter runtime17,178/headroom7,398; Rewards24,218/358; Vault24,443/133; Handoff24,544/32. |
| Actual static | New strict532record:15individually reassessed contexts,517unique exact fingerprint/all-referenced-source reuse. Raw analyzer JSON succeeds; Windows process exit4294967295 remains recorded. Matching/normalization unchanged; explicit strict checker passes. [Full record](static-review.json). |
| Canonical/rights reuse | Actual canonical/NFT/Membership/royalty creation/runtime objects and semantic storage declarations remain unchanged; all ABIs/selectors match. Rewards executable body equality is proven after exact CBOR removal, not guessed from a common ABI. Original34canonical EVM methods retain prior exact source scope; they were not rerun or counted as fresh tests. |
| Factory | Actual Royalty creation bytes and both FORMAT2 data parts identical to5994. Only the F3 artifact's base-converter source pin is rebound; same payload3/FORMAT2 identity. Original artifact/module and exact proof retained. No old runtime/journal is relabeled. |

Root evidence also verifies all3,881original report files and the four protected
dirty files unchanged.21root evidence copies preserve raw/stored hashes and
gzip round trips. No unrelated art/cache/draft file is part of the campaign.
Current normal/static/source/object-equivalence records, raw snapshots and
failures are retained in the package. The full callable reference/operator
examples are rebound to the actual normal output; all38contracts/844functions/
38constructors/13receive hooks and895examples retain zero explanatory/input/
output gaps. Templates are not live snapshots or submission approval.

Earlier exact-LP cold measurements remain scoped observations:32entries used
31,085,813raw gas (above12M);8entries8,819,431in one controlled fixture. New
policy2 and sizing code do not make either count universally safe or change the
network's block/transaction limits. Actual cheap routes/feeds/VRF/authorities,
matching service/site/consumer, complete fees/max workloads/backup recovery,
OpenSea and independent audit/remediation remain open in the soleTodo.
