# Historical creation bytes for seal-input regressions

These are **test-only baseline counterexamples**, not current deployment artifacts.
The JSON files contain the exact creation bytes from the authenticated pre-fix
Vault and metadata artifacts, together with source, original artifact and
creation-byte hashes, compiler and settings, tied to baseline
`003c8d8dc88b60cbfbcc8caf61fa864c6487b40f`.

`SealCriticalInputs20261117Test` checks each creation SHA-256 before actually
deploying the old bytes with controlled constructor arguments. It demonstrates
the old acceptance of a foreign home chain and a scheme-only artwork root, then
checks the exact rejection by current source. The sole added filesystem
permission is read-only for this directory of public test fixtures. No absolute
local artifact path, environment variable, skipped control or compiler
relaxation is required. These bytes are excluded from normal `src` compilation.

The synthetic content roots and authority/policy fixtures do not establish
market, venue, OpenSea, VRF, content availability or production readiness.
