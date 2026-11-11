# Two authority-description corrections

The earlier [current-context review](../../reference-execution-20261111/static/current-162.json)
used `Fees` where the actual Manager authority is `Buyback`. The source and
function reference already authorize the sealed fixed **Vault or Buyback** for
`LiquidityManager.swap` (`src/ZZZLiquidityManager.sol:220–223`). Typed custody
operations remain Vault-only, with the fixed position-executor parent callbacks
separately authenticated.

| Original current-context index | Correction |
| --- | --- |
| 98 | `typed Vault/Fees operation` becomes `typed Vault/Buyback operation`. |
| 142 | Replace nonexistent `onlyFees` authorization with the actual Vault/Buyback swap and Vault/position-executor custody gates. |

[AUTHORITY_ERRATA.json](AUTHORITY_ERRATA.json) records the exact detector
fingerprints, descriptions, old/new rationale and current Manager source hash.
The complete [corrected strict record](../static-review.json) preserves all567
finding identities/dispositions and original162current/405reuse review scopes.
Only these two rationale fields change, plus explicit top-level provenance and
reviewer labels. The remaining565records were not freshly re-audited here.
Inherited evidence paths resolve against the original reference-execution report.

The previous record is preserved byte-for-byte. The checker default selects the
corrected complete record; strict coverage against the existing actual analyzer
output and44checker regressions pass. No analyzer rerun, source compilation,
contract edit, authority change or production approval is implied.
