# Local API wallet publication

Website code **d786286** and contract documentation/evidence **59739ea** were
committed and pushed to main. The Ubuntu static site serves d786286. The previous
757a8de release remains available for rollback.

- All **5,598** server file checksums passed; local source/build bytes matched
  committed Git blobs before packaging.
- Only deployment-session.js, deployment-transactions.js and deployment-view.js
  changed publicly. Artwork, shared signer and configuration remained unchanged.
- **42** scoped public-file hashes, **4** HTTPS/host/redirect checks and **4** private
  path exclusions passed. Nginx configuration validated and the service is active.
- Public DEPLOYMENT is null: the website remains simulated. No public API, RPC,
  contract transaction or production signing was enabled. Existing Anvil/8900,
  NFT/wallet state and paused monitoring were untouched.

The following publication-note commit changes documentation/memories only; the
served code remains d786286. See [receipt](publication-receipt.json),
[scoped verification](VERIFICATION.md) and [operator guide](../../docs/DEPLOYMENT_WEBSITE.md#local-api-wallet-rehearsal).
Actual extension/service qualification and independent release approval remain open.
