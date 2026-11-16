# Verification record

Baseline main: `502c1c8066465a7690e21ae9138b73e83d2bfc3f`.
All source stages and failures retain their original scope.

| Stage | Retained evidence name | Actual result / scope |
| --- | --- | --- |
| Baseline | `BASELINE.json` | Original tracked-file/dirty hashes and archived original current Markdown. New planner/test capability absent at baseline. No old tests. |
| ABI/source review | `ABI_REVIEW.json`, `ABI_CORE_REVIEW.json`, `CORE_REVIEW.json` | Actual signatures, tuple fields, bootstrap permissions, order/bounds/live predicates; earlier review is not relabelled final. |
| Initial representative | `core-representative-01.json/log` | One new candidate composition passes before later static-consistency corrections. Not counted as final core coverage. |
| Decimal baseline | `core-execution-decimals-baseline-01.json/log`, `core-before-execution-decimals.py` | New method fails because the old planner accepts8-decimal enabled execution source; exact candidate retained. |
| Native-pin baseline | `core-native-pins-baseline-01.json/log`, `core-before-native-pins.py` | New method fails3subcases because old validation accepts conflicting fixed pins; not3extra methods. |
| Final targeted | `core-fixed-targeted-01.json/log` |3 methods pass: changed complete representative and both corrected regressions. |
| Remaining final core | `core-remaining-01.json/log` |24 other NEW methods pass once; excludes the preceding3. Includes unknown-dependency, collision, source/pool/route/confirmation/VRF/mint/adversarial checks. |
| CLI | `preseal-cli-representative.json/log`, `preseal-cli-remaining.json/log`, `preseal-cli-case-pins.json` |1representative+17disjoint methods pass. Real local publication/argument/result handling, with preparation injected; not actual core/ABI acceptance. CLI/test sources remain exact. |
| Actual CLI composition | `cli-wire-complete-01.json/log`, `cli-wire-blocked-01.json/log`, `wire/` outputs | Current real source preparation returns expected0/2; no execution. The blocked wire input is the compact null template; published example expands nullable field names and is separately schema-checked. |
| Independent encoding | `CAST_CALLS.json`, `check_cast_calls.py` | All24actual generated calls match offlineCast under minimal environment/no RPC/key variables. NestedAllowList/string[]/UTF8 and native0 represented; no EVM simulation or transaction. |
| Final preservation/pins | `FINAL_SOURCE_PINS.json`, `PRESERVATION.json` | Exact producer/new-method AST/raw hashes, unique method union, unchanged existing Python/Solidity/builds/dirty files. Source pin checks are not rerun suites. |
| Final housekeeping/publication | `HOUSEKEEPING.json`, exact Git publication closure | Generated Todo/links/nullable example/evidence/source/whitespace/import checks only. No release approval or deployment. |

**45 unique new methods with passing scoped evidence (27core+18CLI), not a fresh
whole45 rerun.** Repeated changed/failed methods, Cast comparisons and actual
CLI outcomes are not added to that count. Final selected methods have no skips.
No unchanged test bodies or compilation/provider/browser/service campaign ran.

The evidence index binds compressed and original byte hashes/lengths. Wire
artifacts contain only explicitly synthetic public test identities and original
proof bytes; no live settings, key, RPC credential or adopted configuration.
All readiness/authority/runtime/approval flags remain false.
