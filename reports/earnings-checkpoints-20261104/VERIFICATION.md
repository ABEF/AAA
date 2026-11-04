# Verification scope and retained stages

Baseline096fd2b; work began November4and continued November5,2026. The directory
name records the start, not a claim that publication/qualification happened then.

| Exclusive stage | Recorded result |
| --- | --- |
| initial-checkpoints |13methods:3pass/10fixture errors. Mock ABI rejected native zero in setup; no completed checkpoint journey established. |
| native-fixture-corrected |13methods:3pass/10fixture errors. The older mock RPC rejected every historical EIP1898 block; fixed the synthetic archive transcript, not a production hash check. |
| archive-transcript-corrected |13methods:12pass/1fixture error. A duplicate-transaction test reused the same primary key before reaching reader validation; a distinct log index exercises the intended cross-prefix rejection. |
| strict-checkpoints |18methods pass after explicit state/type/supply/cohort/provenance validation and added concurrent/WAL/failure cases. |
| accounting-edges |23methods:22pass/1fixture error. Appending an unadmitted descriptor correctly failed the existing allowlist; the corrected case proves actual royalty admission, runtime/decimals and constructor-prefund exclusion. |
| affected-history-final |147distinct affected Python methods pass with no failures/errors/skips. Includes24new methods and existing history/storage/chronology/transaction/API/earnings/wallet/lineage/current-profile regressions. |
| reviewed-checkpoints-final |24new methods pass after the final strict integer/identity checks and builder self-validation. Earlier123default/historical-reader methods retain the immediately preceding recorded source stage, not a fabricated rerun. |
| checkpoints-published-candidate |24new methods pass with before/after semantic-source stability during construction. No prior source record is silently relabelled. |
| publication-checkpoints-final |24new methods pass after fixture-import cleanup. Module discovery now selects exactly the24owned tests rather than also discovering imported fixture test classes. Production Python is unchanged from the previous stage. |
| roundtrip-checkpoints-final |24new methods pass after applying the exact reader decoder/resource limits to candidate construction; a reader-bound failure rejects before publication. This is the final source/test stage. |

No stage totals are added. Failure artifacts, source snapshots, exact selected
IDs and before/after source hashes are preserved externally. Four protected
dirty files remain byte-identical/unstaged. Existing imported helper bodies from
test_frontend_history equal committed HEAD; its two unrelated new methods were
excluded from the affected selection. See the fixture AST comparison.

The improvement is verified with the actual production Python classes and real
temporary SQLite files. The current6/5RPC fixture authenticates canonical block
tags and supplies byte-level module/ledger responses for each scenario; it is
synthetic evidence, not Robinhood state, runtime qualification or a market model.
The1000-account case is a replay/fraction bound, not1000holder gas or live load.
No operating data, wallet/private key or public transaction was used.

All production Solidity/dependency/build inputs remain equal to the latest
manual-safeguard normal43gate pins. No normal compilation, Slither, Foundry or
existing fork suite was repeated. Callable reference/Todo/document links and
exact staged/committed Python import publication closure are separate checks.
Neither publication closure nor these tests establish live provider behavior,
production performance, independent audit or an approved source/site rollout.

OpenSea research used official documentation/repository sources only. The
inspected mutable upstream references and research date are retained separately;
no verified Robinhood SeaDrop product/address/codehash or fee acceptance was
invented. The production mint gate remains blocked.
