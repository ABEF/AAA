# Fixed historical evidence admission

## Concrete improvement

The historical physical/rights packaging helpers checked successful counts3/2, but did not independently require the exact expected test identities before summarizing. The original records contain the correct expected identities; **no historical substitution was found**. A count-only gate could nevertheless admit unrelated successful rows if reused or combined with recomputed caller-controlled evidence. The historical reports/helpers remain unchanged.

New `zzz_ops/focused_evidence.py` and `scripts/check-focused-evidence.py` check a closed reviewed baseline, with the exact raw manifest checksum pinned in code. A caller cannot approve altered evidence by rewriting its report, manifest and hashes together. No arbitrary manifest, report root, RPC, execution option, compiler, signing, state adoption or archive extraction is exposed by the CLI.

From repository root run:

```text
python scripts/check-focused-evidence.py
```

A pass prints `integrity_admitted:true`, original-stage limits and `production_approved:false`. Refusal exits2 with a sanitized reason. No file is modified. Changing the baseline intentionally requires separate source/manifest review, not a new command-line override.

## Exactly what is admitted

| Group | Historical method records | Evidence tier |
| --- | ---: | --- |
| Latest actual-v4 physical checks |3|Exact raw results plus actual compiled artifact/method selectors/metadata source identity|
| Latest rights sequences |2|Exact raw results plus actual compiled artifact/method selectors/metadata source identity|
| Seal-review OpenSea artwork case |1|Exact raw result and compiled artifact/source identity; its recorded intermediate Budget stage stays explicit|
| Earlier behavior seal cases |3|Exact raw results and recorded historical source metadata; standalone compiled artifact is not extracted from its archive|
| Operator-input tools |24|Only the retained source-hashed reported method list; absent independent raw terminal logs are not manufactured|
| Original pre-seal core |27|Exact successful unittest rows/log digests/commands and recorded source-stage pins|
| Original pre-seal CLI |18|Exact successful unittest rows/log digests/stage/source records|

The78historical records are **not78newly executed or uniformly raw-verified cases**. The output gives each tier explicitly and never compares historical compiler inputs against current source or relabels old stages. It authenticates only these seven groups, not every observation or claimed outcome across the five families. Original metadata/runtime/source scopes and declared fixture limitations still apply.

## Checks and bounds

- Exact contract-qualified/fully qualified method identities; missing, extra, duplicate, skipped, failed or substituted selections refuse.
- Original raw, proof and compressed-artifact hashes pinned to the maintained trusted baseline; decoded artifact selectors, compilation targets, compiler settings and source-map identities cross-check where those artifacts are available.
- Python result rows, method names, command selections, summary counts, successful statuses and log digests cross-check. A failed extra row cannot hide behind an unrelated final `OK`.
- Stored files<=4MiB, expanded gzip<=8MiB, bounded JSON depth/integer/float parsing, duplicate-key/nonfinite-number rejection, contained paths and sanitized gzip/DEFLATE errors. No new dependency or archive extraction.

Integrity is not proof that original tests executed, that assertions covered every branch, that the provider/token/marketplace will behave honestly, or that production is approved. Missing raw artifacts remain missing; a strong checksum cannot restore them.

## New focused verification

[Machine evidence](EVIDENCE_CHECKS.json) records15distinct new admission methods observed passing across their actual source stages. The initial13new methods passed in the tool response; a raw terminal file was not captured and is not fabricated. A new malformed-log negative first exposed the draft parser ignoring an extra failed row; after correction only that case, its affected existing log case and the affected genuine-baseline case reran. Independent review then reproduced a valid-header/corrupt-DEFLATE `zlib.error`; only that new case reran after normalizing it to `EvidenceError`. Baseline/final logs and source brackets for both draft-checker corrections are retained here. Those failures belong to the new checker development, not to PoPL contracts or previously published evidence.

No old Solidity/Python/browser suite, EVM, compiler, static analyzer, public RPC, existing chain, service, signer or journal was run. The root may invoke the default CLI as a metadata/integrity check; that is not another test execution.
