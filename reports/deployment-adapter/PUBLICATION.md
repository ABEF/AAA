# Publication checkpoint - 2026-10-21

Website code **`757a8dea37a593c9c78e7cfb0213c4a0f5d5973a`** is committed and pushed
on `main`, then deployed to the existing static Ubuntu site. Contract-side
Todo/evidence/operator documentation was pushed as **`1dc05d3`**. This publication
record and repository-memory follow-up contain documentation only; they do not
change the deployed public bytes.

[Sanitized receipt](publication-receipt.json) records UTC observation times,
source/package hashes, remote installation and public checks.

- All **5,597** public files matched their server manifest; source/build bytes
  matched committed Git blobs before packaging.
- Only five public files changed: `app.js` and the four new deployment modules.
  Artwork and the existing signer/client code were unchanged.
- **41** selected public assets/catalogues/artwork samples, **4** HTTPS/redirect
  cases and **4** private-path denial cases passed. Private memory, `.git` and
  `.env` are not served.
- Nginx configuration passed and the service is active. The previous release
  `f060d66` remains available for rollback.
- The served configuration is **`DEPLOYMENT = null`**. The public website remains
  a simulation; no production API, RPC, contract or signing service was enabled.

[Scoped verification](VERIFICATION.md) records the new read/unsigned-review
integration and its limits. All thirteen previous chain-reader bindings remain
unchanged. Local port 8900, Anvil and the user's saved wallet/NFT state were not
reset or transacted against by this work. Paused monitoring was not resumed.
Production signer adaptation, extension acceptance, qualified configuration and
services, collection aggregation and independent release approval remain open.

Automatic approval review rejected the proposed shared-signer expansion; it was
not applied. This release is the safe read/unsigned-preparation alternative and
**does not close the public transaction task**.
