# Current-holdings earnings and production mint scope

Reviewed 2026-10-22. Internal scoped verification; production NOT APPROVED.

## Implemented

The production read API now exposes bounded, pinned wallet earnings. It replays
each epoch once for up to 16 selected NFTs, retaining independent fractional
rounding and checking ownership, shares, weights, claimable backing, past claims
and conversions. The complete wallet inventory digest and cutoff bind every
chunk. Same-chain predecessor receipt/identity checks remain. There is no signer,
new contract role, mock-address exception, or current-price fallback.

The reviewed website API profile sums all chunks before marking original earned
currencies at the current confirmed prices. It displays wallet 24h/all-time
LP + collective + royalty earnings independently of current LP and claimable ETH.
Collection holder allocations consume the existing collection earnings endpoint;
they include index dust and exclude compound, buyback, quarantine and duplicated
gross receipts. Account changes/cancellation/missing chunks cannot publish partial
totals. Missing nonzero-component prices stay unavailable.

User clarification: production minting is intended for OpenSea; the website mint
page is a demonstration. The production API client refuses mint preparation before
any network call. Its page cannot submit a mint; local rehearsal minting remains
available. OpenSea chain/product/caller/recipient integration must still be qualified
before sealing. No new OpenSea compatibility or public signing is claimed.

## Evidence

- **86 affected Python cases**: 28 existing earnings, 12 new wallet earnings,
  34 API and 12 summary cases. `python-clean-candidate.log` and
  `clean-candidate.json` bind a HEAD export plus only this change, excluding
  unrelated older drafts. SQLite history and HTTP are real; chain responses are
  explicit byte-level mocks.
- **89 distinct affected JavaScript cases**: 57 API/session, 13 wallet summary,
  19 new earnings/mint-scope. The runner reports 146 executions because two entry
  files import the same 57-case setup. This is not 146 distinct tests.
- **Six isolated headless browser scenarios** use the production profile: complete
  totals, unavailable prices, missing chunk, account change during a read,
  collection allocations and blocked production mint. Wallet/RPC/API are mocked;
  no real extension or transaction was used. Screenshot inspected at desktop width.
- **30 actual isolated Nginx checks pass**, including eight new wallet summary/earnings route, cursor and method checks. Review found the old production allowlist omitted wallet-summary; both routes are now admitted as bounded GETs. This used local HTTP and fake backend data; production Linux/TLS hosting remains open.
- Clean static build: **5,598 files**, prepared in an external directory. The
  running 8902 recovery overlay's hash is unchanged. No chain or service reset,
  browser storage change, pending-journal action, or monitor restart occurred.
- Syntax and diff checks pass. Solidity and shared signing behavior are unchanged;
  their suites and the deferred load campaign were not rerun.

## Corrections and review limits

Initial new backend tests used block 98 while their mock only served canonical
state at block 99. Corrected the fixtures; no canonical guard was relaxed. The
first JS fixture used 18-decimal USDC whereas the earnings fixture had 6 decimals;
the validator rejected it. Corrected the test manifest to the real fixture precision.
The first combined documentation patch failed atomically on a missing context line;
reapplied with the actual file heading.

Review checked independently rounded NFT units, new-member exclusion, transfer
history, source/native conversion and claim non-income, epoch import non-income,
price failure, empty holdings, cursor/identity errors, complete chunk coverage,
request limits and stale/account-change rejection. A 1,000-ID pagination test
checks a 63-request bound; it is not a 1,000-user or production capacity test.

Remaining: real deployment/provider/price/ingestion qualification, maximum-history
latency and archive availability, full collection inventory/LP aggregation,
actual extension acceptance, OpenSea mint integration and independent audit.
The user-retained signer restriction still permits only local Anvil. Public
`DEPLOYMENT` stays null; the public site is simulated. The local one-time mint
repair still awaits the user's MetaMask/browser steps and must not be deployed.

Publication is recorded separately; a passing local check does not deploy APIs
or contracts and does not imply a green published CI run.
