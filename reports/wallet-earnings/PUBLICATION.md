# Production earnings publication - 2026-10-22

Backend code and scoped evidence `31e5ac4` and website `35c7843` are pushed on
main. The static website serves `35c7843`; subsequent documentation commits do
not change this served code revision.

- All 5,598 public files match committed source blobs and passed server-side
  SHA-256 checks before the atomic release switch. Only deployment-api.js and
  deployment-view.js changed in the static package.
- 42 public asset checks, four HTTPS/redirect checks and four private-path
  denials passed: 50 scoped checks. Previous release 9aaedec remains for rollback.
- The release came from a separate clean build. Local dist/deployment-view.js
  retains the exact temporary mint-repair overlay hash. Existing local chain,
  NFTs, LP, pending browser journals and paused monitoring were not modified.
  Actual user MetaMask reset and browser archival still require user action.
- Public DEPLOYMENT remains null. No public API, contracts, financial transaction
  capability or keeper was deployed. Shared signer/coordinator remain unchanged
  and Anvil-only. New earnings are implemented for the opt-in reviewed profile;
  the public website still displays simulated data.
- Production minting is intended for OpenSea. Marketplace compatibility is an
  open pre-seal qualification task, not established by this publication.

See [verification](VERIFICATION.md), [package](static-package.json),
[server receipt](publication-receipt.json) and [public checks](public-verification.json).
Unit/contract suites were not rerun for publication. JSON fixture/report line
endings were normalized without changing parsed evidence or application behavior.
Published CI status is separate; production remains NOT APPROVED.
