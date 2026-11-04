# Verification and preserved evidence

November4,2026. Baseline main e237aa72ec7fa09382d857ffab1a3fd96b286299;
production Solidity still matches e26fc74. [Review](REVIEW.md), [coverage](COVERAGE.md).

## Fresh affected execution

Python: the bundled runtime, `-B -X utf8`, Windows host. Tests use temporary
SQLite databases and synthetic RPC data; no network, keys, running database,
Anvil, services or transaction sender is involved.

| Stage | Actual outcome | Scope |
| --- | --- | --- |
| [Negative control](indexer-negative-control-results.json), [selection/pins](indexer-negative-control-selection.json), [raw log](indexer-negative-control-execution.log) |6methods ran;10failure/subcase results and2errors, not a passing campaign | New regressions against the original indexer reproduced anchor aliasing, acceptance of malformed anchors and full transfer materialization. One error was Windows cleanup caused by the deliberately failing cursor wrapper; that wrapper was corrected. An ingestion error also exposed changed-anchor behavior. Original attempt is retained. |
| [Corrected campaign](indexer-corrected-results.json), [selection/pins](indexer-corrected-selection.json), [raw log](indexer-corrected-execution.log) |33distinct methods selected/executed,0failures,0errors,0skips; source unchanged through execution |27existing indexer regressions plus6new anchor/streaming methods. Actual2001-row SQLite ownership replay includes burn, transfer and collection isolation. No broad unrelated suite rerun. |

The explicit runner inventories canonical method IDs and rejects empty/duplicate
selection. The failed stage and corrected stage overlap: the result is33distinct
successful methods, not39. This does not establish Unix operating acceptance,
live RPC correctness, complete financial history, maximum gas or production capacity.

## Unchanged contract evidence reused

[Exact comparison](reuse.json):52production Solidity files,31dependencies and
4build inputs match the current authority build byte-for-byte. All previous
report files match baseline except the deliberately maintained report index.
The four unrelated dirty files also match their baseline bytes and stay excluded.

Therefore the existing [43normal gates](../authority-audit-20261103/production-size-gates.json),
[static review](../authority-audit-20261103/VERIFICATION.md) and source-matched
[exit assurance](../holder-exit-assurance-20261103/REVIEW.md) retain their prior
scopes. No new compiler, analyzer, Solidity suite, fork or public CI run is claimed.
Current compiler disclosures were consulted; the [previous source/settings
assessment](../smart-contract-lp-audit-20261103/compiler-assessment.json) remains
limited to unchanged source and its stated AST/compiler-lowering limitations.

Migration24537bytes/runtime margin39; Vault23941/margin635;
Budget24339/margin237; Balancer24216/margin360. These are reused measurements,
not new optimization/gas results. Tight margins remain a release engineering risk.

## Documentation and publication checks

The sole Todo was generated and `--check` passed. The source-bound callable
reference `--check` returned37contracts/818functions/37constructors/13receivers,
0explanation/input/output gaps; it is inventory consistency, not behavior testing.
Document links, exact staged/committed Python closure, protected-file hashes and
publication identities are recorded separately in the final consistency record.

Website changes are only README/AGENTS/context documentation. There is no JS/CSS,
asset, manifest, configuration, signer, build or served-site change. No JS/browser
test rerun is justified by those documentation edits. The served current3 and
preserved Anvil profiles remain separate from fresh accounting6 source8.

External originals, baseline tracked hashes, full runner/campaign files and
documentation drafts are retained under the local evidence root's
`whole-project-audit-20261104/`. That archive is not a public service or monitor.
No credential contents were accessed or included. Independent review and all
actual provider/route/VRF/authority/OpenSea/operating release gates remain open.
