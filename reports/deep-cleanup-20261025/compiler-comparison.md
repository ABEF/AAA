# Saved compiler and source comparison

No compiler or execution tests were repeated by this comparison.

Comparison checks pass: **True**. **108** total project objects are compared; **37** have normal creation/runtime gates and **31** are concrete callable targets.
- All object wire ABI/layout checks pass after only the explicit exceptions: **True**.
- Access adds the explicit `GuardianChanged` event. Existing keeper and new guardian constructor grant logs are observable behavior changes; economic permissions are unchanged.
- Three concrete ABI lists lose an identical `InvalidConfiguration()` duplicate; the abstract converter base loses a fourth duplicate. The internal-only validator's sole error descriptor is separately retired in favor of the same existing Module declaration, with unchanged error selector. No other sole error removal is normalized.
- No parameter/tuple label, constructor argument, output or mutability change is hidden. Only Access, RoyaltyRewards and the internal v3 validator source hashes differ; the other 41 production files match the prior build.
- All **37** normal runtime/initcode object gates pass. Exact dynamic NFT URI argument encoding remains a release gate.

## Compiler and dependencies

The actual existing Foundry profile has seven remappings; the older bespoke production driver supplied five. The two added aliases (`v4-core/` and `permit2/`) are unused by production imports. Every resolved production import and all 75 source-unit paths remain identical. Core compiler/optimizer/settings are unchanged; raw settings are explicitly not byte-identical.

Current 31 dependency source bytes are explicitly captured and match the new build. The older production input omitted those dependency contents, so historical dependency-byte identity is **not proven**. Partial earlier local-review pins are compared only where they exist.

## Royalty balance helper

The removed private balance expression exactly matches the already inherited `_canonicalBalance` expression. Every remaining RoyaltyRewards body preserves its token/call order after only that helper-name replacement. Actual executable comparisons are recorded below; this source comparison does not replace changed-path execution checks.

| Object with a size change | Runtime delta | Creation delta | Runtime / margin |
| --- | ---: | ---: | ---: |
| ZZZAccessController | +45 | +175 | 9252 / 15324 |

## Executable comparison

- `ZZZCanonicalHandoff` creation/runtime equal after only known complete metadata masking: **True / True**.
- `ZZZMigration` creation/runtime equal after only known complete metadata masking: **True / True**.
- `ZZZRoyaltyRewards` creation/runtime equal after only known complete metadata masking: **True / True**.
- `ZZZVault` creation/runtime equal after only known complete metadata masking: **True / True**.

The first strict saved-output comparison surfaced the abstract-base and internal-library metadata exceptions. Its exact report/script preimage and reason are retained as `initial-*`; only this read-only comparison was repeated after explicitly admitting those exact exceptions.

See `compiler-comparison.json` for all object ABIs/layouts/bytecode, 37 size rows, 75 source units, import resolutions and hashes. Initial ABI/AST test-import failure and test-only repair remain separately recorded. Production remains NOT APPROVED.
