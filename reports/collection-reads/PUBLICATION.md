# Confirmed collection publication - 2026-10-23

Contract-repository backend/evidence `d1b11eb` and website `9be6d11` are pushed
on main. The static website serves `9be6d11`; later documentation commits do not
change the served code revision.

- All 5,598 public files match committed source blobs and passed complete
  server-side SHA-256 verification before the atomic release switch. Only
  deployment-api.js and deployment-view.js changed in the static package.
- 42 public asset checks, four host/HTTPS/redirect checks and four private-path
  denials passed: 50 scoped checks. Previous release 35c7843 remains for rollback.
- The separate clean build excludes the temporary local mint-repair overlay.
  That overlay's exact hash is unchanged. Existing local Anvil, NFTs, LP, user
  journals and paused monitoring were not changed. User MetaMask reset/browser
  archival still requires user action.
- Public DEPLOYMENT stays null. The implemented explorer belongs to the opt-in
  reviewed API profile; public collection data/actions remain simulated. No public
  API, contract, signer extension or financial transaction was deployed or sent.
  Shared browser signer/coordinator remain unchanged and Anvil-only.
- Actual RPC/history/pricing/latency qualification, different-pair/future-chain
  migration, OpenSea primary mint integration and independent approval remain open.

See [verification](VERIFICATION.md), [static package](static-package.json),
[server receipt](publication-receipt.json) and [public checks](public-verification.json).
Scoped tests were not rerun for publication. Remote CI is separate from local and
static-release evidence. Production remains NOT APPROVED.
