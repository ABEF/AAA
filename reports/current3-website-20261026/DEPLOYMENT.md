# Isolated poplint publication and deployment

Website implementation [f23c559](https://github.com/ABEF/AAA-website/commit/f23c5599185997da1f36c4f64fea021b3f99b27a) is committed and pushed on main; its exact remote head was verified. The integration-only build has5,593 public files including its checksum manifest (the build reports5,592 before adding SHA256SUMS). The archive SHA256 and release identity are in BUILD.json.

https://www.poplint.0xwave.com/ now serves that release from `/var/www/popl-integration/releases/f23c5599185997da1f36c4f64fea021b3f99b27a`. HTTP and the apex integration hostname redirect to the www HTTPS origin. A separate popl-integration certificate was issued through webroot challenges. No existing demo certificate/configuration was edited. `live-observation.json` records both demo URLs, all integration HTTP/HTTPS variants and the public identity; `desktop-https.json` independently confirms desktop HTTPS200 for both www sites and integration identity with normal certificate verification.

The existing demo remains on release9be6d1 under `/var/www/aaa-website`. Before/after root, public index/app/checksum and all previously enabled-site configuration hashes match. Nginx is active and configuration testing passes. New integration files/configuration are distinct. The initial immediate deployment verifier exited without classified diagnostics after activation; the preserved follow-up read-only observation confirmed all routes and unchanged demo. No second installation or inferred failure cause is claimed. Earlier HTTPS-helper NameError attempts occurred before mutation and were corrected before successful certificate setup.

The live integration configuration is **null/unconfigured**. There is no fabricated current contract/API/price deployment. Public signing is disabled, `/api/protocol` returns503, and demo application/operator paths are denied or absent. Security headers and those boundaries passed the separate public checks in `public-boundaries.json`. A live static page is not qualified provider, API, wallet, marketplace or contract operation.

The user explicitly authorized reuse of the previously supplied server credential and installation of the deployment public key after automatic review required clarification. The credential was used only in memory, never printed or saved. The private key stays outside Git and public artifacts. No public contract transaction/deployment, Anvil reset, journal migration, keeper restart or monitor resumption occurred.

[Environment map](../../docs/SITE_ENVIRONMENTS.md), [current3 profile](../../docs/CURRENT_WEBSITE_PROFILE.md) and [verification](VERIFICATION.md) keep implementation, serving and actual deployment/service qualification separate. Production remains NOT APPROVED.

The enabled/active certbot timer now has a poplint-lineage-only executable deploy
hook. Syntax, unrelated-lineage no-op and matching-lineage Nginx test/reload pass;
demo hashes remain unchanged. See renewal-hook.json and website-final-publication.json.
Website main subsequently reached77501ce (operating docs/hook); the static
artifact remainsf23c559. The user-owned local deployment key ACL now works with
standard OpenSSH, with sandbox-account access removed and no private key printed.
