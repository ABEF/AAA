# Operations-hardening static analysis - 2026-10-16

Slither 0.11.6 analyzed the current 29-source production candidate, with exact typed AST, compiler input and bytecode bindings. Three build/configuration files are also bound. It consumed the completed normal-profile build without recompiling. The production Solidity change in this workstream is the Vault's four-bucket cap and two explanatory comments.

All **220 findings** were individually reviewed internally: 40 High, 73 Medium, 69 Low, 33 Informational and five Optimization. Dispositions: **130 false positives, 46 accepted risks, 44 informational, zero unresolved detector entries**. No historical approvals were automatically imported. This is **not an independent audit or production approval**.

The separate, reproduced destination-capacity reservation race remains unresolved and is a blocker before enabling a real bridge. Zero unresolved detector entries does not mean zero known limitations. Combined mock-venue gas evidence does not qualify actual Entry/Pons execution.

[slither-review.json](slither-review.json) is also the [canonical review](../../production/slither-review.json). The previous 220-finding review is byte-for-byte preserved in [history](../../history/slither-review-pre-operations-hardening.json); previous source-bound reports retain their original scope.

[coverage.json](coverage.json) binds current source/report/review hashes and complete coverage. [run-summary.json](run-summary.json) binds compiler input, artifacts and tools; the large raw analyzer report and build information stay in the referenced external evidence directory. The unchanged matcher passes all 43 tests; [nine fresh mutations](mutation-tests.json) are rejected, including source/finding/decision drift. Detector settings and acceptance rules were not weakened.

Remaining production gates include actual routes, feeds, wrapper authority, VRF, creator-payment terms, real provider backing/recovery, operations staging, final-release Ubuntu CI and external audit/remediation.
