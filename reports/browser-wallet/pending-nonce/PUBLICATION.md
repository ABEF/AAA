# Pending nonce diagnostic publication - 2026-10-22

Website code `9aaedec` and scoped contract documentation/evidence `1bb8668` are
pushed on main. The static website serves `9aaedec`; later documentation commits
do not alter the served code revision.

- All 5,598 files matched committed source blobs and passed complete
  server-side SHA-256 verification before the atomic release switch.
- Only browser-wallet.js and deployment-view.js changed in the static package.
- 42 public asset checks, 4 host/redirect checks and
  4 private-path denials passed; 50 scoped checks total.
- Previous release 777fd05 remains available for rollback. Public DEPLOYMENT is
  still null; no public contract, API, signer capability or monitoring change.
- Local 8902 serves the rebuilt files without a chain/service restart. No queued
  transaction was dropped, altered or resent. The user's nonce 35 mint remains
  unmined and requires separate reconciliation; publication does not resolve it.

See [verification](../PENDING_NONCE.md), [server receipt](publication-receipt.json),
[public checks](public-verification.json) and [package](static-package.json).
Source bindings still match. Scoped tests were not rerun for publication; no
unchanged Solidity/backend suites or deferred load campaign were run. Remote CI
status is separate from this local/static evidence. Production NOT APPROVED.
