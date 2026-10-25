# Publication receipt - 2026-10-25

The completed source/evidence refactor is committed and pushed on **main**:

- Contract implementation: [`ea2a70c`](https://github.com/ABEF/AAA/commit/ea2a70c443eb40845e87f08cf0dbeeb1a25fe8b5).
- Website **memory only**: [`2461e6e`](https://github.com/ABEF/AAA-website/commit/2461e6eb5d4166cd9f89a7eca0e440daae4f21e9).
- Exact remote heads, 44 production blobs, owned candidate blobs, artifact hashes,
  website source hashes and preserved unrelated drafts were verified at
  `2026-10-25T20:37:51.373894+00:00`. [Machine receipt](PUBLICATION.json).

The later receipt/memory checkpoint contains documentation only and does not
replace the implementation identity above. [Final scope](FINAL_SCOPE.json) and
[artifact manifest](artifact-sha256.json) distinguish owned changes from older
local drafts; only owned memory prefixes were staged from dirty memory files.

[Review](REVIEW.md), [verification](VERIFICATION.md) and
[compiler comparison](compiler-comparison.md) retain their exact limits:
26 distinct selected Solidity behaviors across recorded fixture scopes, 20
event-schema methods, 131-input typechecking and 37 normal object gates. Two
inherited repeats are not additional distinct coverage; the one-byte test
version repair and reused bodies are explicit. This is not a full regression,
real provider approval, formal equivalence proof or independent audit.

No contract deployment, public financial transaction, seal, website source/build/
server/service update, existing 8902/Anvil/NFT/LP/balance/journal/dist-overlay or
paused-monitor change. Public DEPLOYMENT stays null; signing stays Anvil-only.
Actual website3, independent feeds/routes/VRF, authorities, OpenSea, strategy/gas
and operating qualification plus independent audit/remediation remain open.
Production NOT APPROVED.
