# Last24hours: audit and exact-unit royalty correction

Fixed audit interval2026-11-04T19:04:18Z through2026-11-05T19:04:18Z
(Europe/Paris local20:04:18 at both endpoints). Contract baseline before the
11in-scope commits is e237aa7; candidate967370f. Website baseline997f8c3,
three commits through5674487. Current source is not a deployed release.

The user executed the14-part audit prompt and subsequently selected deterministic
exact-unit allocation instead of accepting permanently reserved rounding units.
That is an authorized accounting-policy change, distinguished from the backend,
website and documentation bug fixes below. Old runtimes/readers remain explicit.

## Scope and method

| Area | Investigation / evidence |
| --- | --- |
| Scope/preservation | Exact Git interval/heads, tracked-file hashes and original current-doc archive outside Git; protect four dirty files, old reports, Anvil, journals, signer and services. |
| Economics/accounting | Independent raw-unit conservation, finite-ending nondivisible receipts, all claims, rarity/ticket fairness, one-hour cutoff, zero cohort, prefunds and unsupported receipts. |
| Contracts | Royalty/NFT/router/current-owner calls, callback rollback, optional-currency failure, opening/recovery/capacity, V8 backing/import/abort and terminal LP independence. |
| Allocation correction | Compare old failure reproductions to whole-unit rotating tickets; bounded outstanding tree, overflow cycles, claim ordering, cohort changes, gas and normal deployment sizes. |
| Backend | Reporting/opening status against the same confirmed timestamp; full replay/checkpoint/suffix equivalence, exact event credits, ownership/cohorts/cursors and explicit lineage profiles. |
| Operations | Indexer identity/WAL/rollback/reorg source matches; keeper deadline and pending-recovery context, no current royalty swaps, independent LP conversion, manual safeguard composition. |
| Website | Same-snapshot opening validation, locked-royalty separation, original-unit selection, dormant deadline preference, historical profiles and unchanged Anvil-only signer. |
| Evidence/docs | Strict source-bound static analysis, normal runtime/initcode gates, generated function/operator references, ledger/Todo/profile/release/context/guide consistency. |

No blanket whole-project or independent approval follows. Run useful affected
checks and independent regressions, retaining failed stages and fixture corrections;
reuse unchanged checks only with exact source applicability. Broader external
qualification remains separate. No deployment/public transactions/service/site
rollout, live data changes, Anvil reset or heartbeat restart is authorized.

## Test-maintenance follow-up

The user's subsequent question about obsolete tests extends the review to current
test consumers of the changed window/profile/rounding rules. Classify current
contracts versus explicitly historical imports; preserve legacy reader coverage.
Update confirmed stale schemas, expected rounding losses, unopened-window claim
fixtures, vacuous claim invariants and false aggregate gas claims. Re-run only
changed/affected scenarios and bounded stateful checks. These are test/fixture
changes, not another production implementation or normal/static rebuild.
