# Demo and contract-integration websites

Decision: 2026-10-26. These are separate release targets from the same website
repository, `ABEF/AAA-website`, on `main`. The operator must select the target
explicitly; a hostname change does not change a contract deployment profile.

| Boundary | Demo | Current-contract integration |
| --- | --- | --- |
| Public URL | https://www.popldemo.0xwave.com/ (existing apex alias retained) | https://www.poplint.0xwave.com/ with `poplint.0xwave.com` alias |
| Purpose | Existing product demonstration and simulated financial actions | Accounting3 reads and unsigned activation/growth/claim reviews |
| Server root | `/var/www/aaa-website/current` | `/var/www/popl-integration/current` |
| Release history | `/var/www/aaa-website/releases/` | `/var/www/popl-integration/releases/` |
| Build command | Existing `node build.mjs`; do not run it against a preserved local dist overlay | Separate `node build-integration.mjs`; isolated `dist-poplint/` output |
| Contracts and data | Clearly labeled examples; public `DEPLOYMENT = null` | Reviewed current3 manifest/API required; missing configuration is **unconfigured**, never sample holdings or guessed zero |
| Wallet authority | Existing local Anvil profile remains separate | Public read/unsigned review only; no public signing or transaction submission |

DNS records point the two integration hostnames to `46.225.185.212`. Their Nginx
site and certificate are separate from the demo. DNS, TLS and serving an HTML
page do not establish API availability, deployed current contracts, price-feed
qualification or production approval. Never point public browsers at a developer's
`127.0.0.1` RPC/API or expose disposable Anvil accounts to the internet.

## Version and data boundaries

The new website manifest is explicitly schema3: accounting3, direct governance2,
fee intake1, pricing2, routing2, Entry review2 and canonical local V4. The HTTP
API's envelope schema remains its own version; do not relabel it to match the
website manifest. Existing schema1/native2 manifests, Anvil deployments and
saved transaction journals retain their original meanings.

Current contribution inputs are native ETH and the fixed deployment ZZZ only.
The default contribution budget is 2% (98% marginal deployed LP), conversion 1%
and maintenance 3%, with governed ceilings and stronger reviewed caller/venue
minima. Use actual confirmed values and keep missing pricing/history unavailable.
OpenSea primary mint integration is still unfinished; poplint must not imply
that a production mint or real-fund wallet flow is enabled.

The integration entry fails closed when the reviewed manifest is absent or
incompatible. Do not populate it with demo contracts, unqualified addresses,
invented balances or a legacy manifest merely to remove the unconfigured label.
Supplying real runtime/configuration pins and hosting a matching API remains
separate release work under the [sole Todo](../TODO.md).

## Publish and verify a release

1. Read this table, website instructions and the integration-only deployment
   procedure. Preserve current demo and existing local Anvil/dist/journals.
2. Run affected current3 checks and the isolated integration build. Verify
   `deployment-config.js`/integration configuration, identity metadata and
   artifact checksums. Keep credentials, tests and operator scripts out of the
   public artifact. Record source commit and file hashes.
3. Use only the integration installer and `/var/www/popl-integration` target.
   **Never run the existing demo installer to publish poplint.** It hardcodes
   `/var/www/aaa-website` and would update the wrong site.
4. Before changing Nginx, record the demo's current release symlink, public
   index/app/checksum hashes and enabled-site configuration hashes. Add only
   the integration site, test Nginx configuration, and provision the separate
   poplint/www certificate. Keep existing demo configuration and certificates.
5. Verify both integration hostnames, TLS, MIME/cache/security headers and the
   environment identity. Verify the demo root/configuration/content hashes are
   unchanged. Distinguish an unconfigured integration site from actual API,
   wallet, marketplace or target-chain qualification.
   If an immediate post-reload read fails, retain the release evidence and retry
   bounded read-only status checks before considering rollback; do not blindly
   reinstall or modify the demo.
6. Roll back by switching only the integration symlink to its prior verified
   release. For a failed first-site setup, remove only the new integration
   enabled-site link after inspection, run `nginx -t`, then reload. Do not
   remove unrelated sites, certificate material or journals.

The private deployment key stays outside repositories and public artifacts.
Only its public half is authorized on the server. Keep authentication secrets
out of commands, reports, Git and frontend configuration; verify the existing
SSH host key rather than accepting a new fingerprint silently.

## Decisions and remaining qualification

The user declined the proposed extra sale-rights UI task. It is marked **Not
planned**, rather than implemented, in the ledger; underlying ownership and
unclaimed-reward rules are unchanged. No new purchase flow or marketplace was
added to the website.

Read-only mainnet forks use a separately identified RPC, chain, pinned block and
current-source fixture. Fork execution creates local state only and does not
deploy contracts or submit transactions to Robinhood. Mock feed/VRF/authority
dependencies must remain explicit; a usable archive RPC is not an approved
production provider. See [development](DEVELOPMENT.md) and the owning fork task.

[Published release and serving evidence](../reports/current3-website-20261026/DEPLOYMENT.md)
record the exact integration commit, successful HTTPS checks and preserved demo.
The live integration remains unconfigured until reviewed contracts/API exist.

Certbot renewal is enabled/active. The integration-only deploy hook at
`/etc/letsencrypt/renewal-hooks/deploy/popl-integration-nginx` validates its exact
RENEWED_LINEAGE before testing/reloading Nginx; keep it with the reviewed website
source template. Demo renewal configuration was not changed.
