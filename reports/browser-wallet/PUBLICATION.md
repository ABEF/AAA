# Wallet code and static demo publication - 2026-10-20

The verified wallet/backend candidate is on `main` at `df8a98a`; the corresponding
website code is `f060d66`. Documentation-only commits may follow those source
revisions. [Receipt](publication-receipt.json) identifies the deployed code exactly.

## What was verified

- The website worktree was clean and HEAD matched origin/main before packaging.
  All 5,593 public build files match their committed Git blobs. Only changed
  public files were uploaded; artwork bytes were unchanged.
- The prior release `d1a6959` and its full manifest were verified before copying
  into a separate release directory. All 5,593 resulting public files passed
  server-side checksums before the atomic symlink switch. Nginx configuration
  and reload passed; the previous release remains available for rollback.
- HTTPS on both public hostnames, HTTP redirects, 37 public asset checks
  and four private-path denials passed. Public checks include all non-artwork
  assets, both catalogues and 12 sampled artwork states; they are not a repeat
  download of the full artwork library.
- [Thirteen source bindings](publication-bindings.json) still match the
  [focused wallet verification](CHAIN_READER.md). Existing 232 website and 43
  backend cases are reused at those exact source hashes, not reported as new runs.
- Todo generation and changed document links were checked. README, roadmap,
  feature reference, handoff and both repository memories describe the same
  boundaries. No operator behavior changed; existing wallet recovery and static
  release procedures remain applicable.

## Preserved boundaries

Local port 8900 responded with its existing genesis and the corrected signer.
Anvil and the local web process were not restarted; wallet journals, NFTs and LP
were not reset or edited. The previous 13-NFT preservation check retains its
original scope; this publication did not re-enumerate or transact on those NFTs.

The public website remains a development simulation. No public contracts, APIs,
routes or signing profile were deployed; no public transaction or paused-monitor
restart occurred. Actual MetaMask UI acceptance of the latest fix remains open.
The user-deferred load campaign was not run. Production remains **NOT APPROVED**.

Older unrelated local contract/source/test/documentation/artwork drafts remain
outside this publication. They must be reviewed separately; publishing this
checkpoint does not certify or publish them. Repository memory is durable local
project context, not global personal memory.

Full deployment/public verification receipts remain outside Git in the matching
`website-server-release-f060d66` local release directory. The committed receipt
contains only sanitized provenance and check counts, never credentials or sessions.
