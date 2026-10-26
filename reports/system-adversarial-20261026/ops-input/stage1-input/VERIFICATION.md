# Holder inventory input verification

The original CLI called `Path.read_bytes()` and only then checked the2MiB limit;
large local operator inputs could therefore exhaust memory before rejection.
Default JSON parsing also accepted duplicate fields, NaN/Infinity and finite-text
exponents overflowing to infinity. These are local tool/data integrity and
availability defects, not an on-chain authorization bypass.

The narrow correction in `scripts/inventory-nft-holders.py` bounds the read
itself to2MiB+1, rejects duplicates at all object depths and all nonfinite numbers,
and normalizes a JSON decoder `RecursionError` to the existing sanitized validation
failure. Valid finite floats/exact-limit input remain accepted. Exclusive output
creation and the existing no-migration-approval semantics are unchanged.

Eight new tests were written before the code change. The final exact
[negative control](before.json) runs those unchanged tests against the original
CLI: eight assertion failure records and one expected parser-recursion error;
three control methods already pass. [Original log](before.log).

The [affected runner](run-affected.py) selects only TestCase classes defined in
the two affected modules and deduplicates IDs. [Final receipt](after.json):
**20 distinct methods passed**, eight new plus12existing holder-preflight methods,
zero skips/failures/errors or source drift. Final new-test SHA256 is unchanged
since the bound negative control. Existing source/fixture inputs are pinned before
and after. No other unchanged production/keeper/contract suite was rerun.

One preliminary harness assumption—that valid2000-level JSON necessarily fails
parsing on every Python runtime—was incorrect. Its initial test bytes and receipt
remain in `exploratory-depth-assumption/`. The corrected final test injects an
actual parser-limit exception and adds no arbitrary schema-depth restriction.
Preliminary and final selections overlap and are not added as coverage.

All files are temporary local fixtures; RPC objects are inert mocks. No endpoint,
wallet, private key, running Anvil, service, original journal or deployed contract
is accessed or changed. No valid input is turned into production approval.
