# Release integration and recovery progress - 2026-10-15

This is an **undeployed working candidate**, internally verified and **not
approved for production funds**. Changes remain local. Earlier release-hardening,
artwork and alignment evidence retains its original source scope.

## Implemented in this candidate

- Strict selected native-ETH/Pons custody, with real PoolKey identity separated
  from canonical WETH accounting and fee-aware input balancing.
- $100 gross pair-input activation and at least 99% marginal deployed LP; the
  same execution limit applies to additions. Network gas is separate.
- Immutable activation-source policy helper: governed add/disable/re-enable,
  append-only history and dependency-independent disabling. Pool reconfiguration
  cannot silently re-enable a disabled input.
- Reviewed wrapper implementation/administrator/owner maintenance, including
  renounced ownership; governed sequencer-feed replacement with mandatory uptime
  and grace checks. Disabled strategy admission alone does not block source exit.
- Immutable batching of up to 32 LP/royalty claim operations, with repeated
  current-owner authentication and direct payouts.
- Unhosted confirmed API with optional creation-anchored wallet and cumulative
  LP-plus-royalty claim history; receipt-based revenue measurement proposals.
- Verified artwork upload archive, plus read-only stablecoin provenance/quote
  groundwork. No IPFS upload, live website integration or production quote is
  implied.

See [change and recovery boundaries](../../docs/CHANGE_AND_RECOVERY.md),
[service decisions](../../docs/PRODUCTION_SERVICES.md) and the
[Implemented / Todo checklist](../../docs/IMPLEMENTATION_STATUS.md).

## Current verification

| Check | Result and scope |
| --- | --- |
| Full local Solidity | **430 passed, zero failed**, 31 suites; two opt-in fork setup skips recorded separately |
| Portable Python | **478 passed** from 482 tests; four unchanged Unix-only cases reserved for Ubuntu, no runtime skips/errors |
| Actual selected pool | **17 passed, zero failed/skipped**, at Robinhood block 88,544,093 and the pinned block hash |
| Original alternative pool | **9 passed, zero failed/skipped** in a separate final-source hookless-pool/dependency regression; the CI inventory gate accepts both real result sets, 26 tests total |
| Compiler binding | All **28 current production sources** match compiled metadata; production/test bytecode objects match |
| Normal size gates | All **22 modules/helpers** pass; Vault runtime 24,434 bytes, margin **142 bytes**; NFT initcode object 46,294 bytes before constructor arguments |
| Fresh internal Slither | **210 individually reviewed findings:** 121 false positives, 56 accepted risks, 33 informational; zero unresolved review entries |
| Review replay | Two analyzer runs, unchanged coverage checker, 43 matcher tests and nine rejected adversarial mutations |

[verification-summary.json](verification-summary.json) binds the current sources
and evidence. [solidity-verification.json](solidity-verification.json) records
individual mock-call gas measurements; whole test-scenario gas includes setup and
is not a production transaction estimate. The full logs and detailed
[static review](static-analysis/README.md) retain their scope. The 46 MB analyzer
JSON, compiler outputs and artwork archive remain in the external evidence
directory recorded by the receipts.

The selected-pool fork uses real venue dependencies with mock authority/VRF and
synthetic USD calibration. It proves custody/accounting scenarios under that
fixture; it does not prove real randomness, a valid production ZZZ/USD feed,
creator agreement, production strategy economics or a functioning live bridge.

## Gates still open

The [release checklist](../../docs/RELEASE_CHECKLIST.md) remains NOT APPROVED.
Atomic original-source stable entry, supported VRF/recovery, independent ZZZ
pricing/outage policy, production authorities, creator measurement/payment terms,
public artwork hosting, live frontend and gross-fee/USD projections, target-chain
operating rehearsals and independent audit/remediation remain open. Actual bridge
provider wrappers/backing/finality/recovery must be qualified before migration is
enabled. The example production inventory is intentionally blocked.

No public-chain deployment, signature, real asset transfer, website modification
or server publication occurred in this work. Controlled configuration is not a
general proxy upgrade mechanism or a guarantee against external custody failures.
