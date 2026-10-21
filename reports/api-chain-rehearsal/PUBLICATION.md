# API rehearsal and wallet totals publication - 2026-10-22

Backend/read-only totals and local rehearsal code are on main at `f068f9f`;
website code is `777fd05`. Later documentation-only commits do not change the
served source revision. [Deployment receipt](publication-receipt.json) and
[public verification](public-verification.json) identify the exact release.

- All 5,598 static build files matched committed Git blobs before
  packaging and passed full server-side SHA-256 verification before switching.
- Only `deployment-api.js`, `deployment-view.js` and `local-view.css` changed in
  the public package. Artwork bytes and public null configuration are unchanged.
- 42 public asset checks, 4
  HTTPS/redirect checks and 4 private-path denials
  passed. The previous `d786286` release remains available for rollback.
- The local fixture at port 8902 remains separate. No public contracts, API
  services, real-wallet signer, monitor restart or load campaign was deployed.
- Scoped source hashes still match [verification](VERIFICATION.md). No unchanged
  signer or Solidity suite was rerun for publication. CI for a published revision
  must be checked separately; local results do not imply a green remote workflow.

Todo, features, operator procedure, handoff and both repository memories were
updated together. Older unrelated local drafts remain uncommitted. Production
remains NOT APPROVED; public actions are still simulated. Actual extension
acceptance and reviewed services/routes/feeds/VRF plus independent audit remain open.
