# Mint2 verification and evidence boundaries

Baseline main `15791864437ec8f35414e17d338380a484af5094`.
This is focused source verification of the [reviewed candidate](REVIEW.md), not
an independent audit, full-suite result, published CI or production approval.
Evidence stages overlap; their counts must not be added into a coverage claim.

## Production compiler, bytecode and static analysis

[Normal compiler input](contract/normal-final-05f7ac32db/compiler-input.json),
compressed output and [size gates](contract/normal-final-05f7ac32db/production-size-gates.json)
bind90 closed production/dependency sources. All47 normal object gates and both
actual royalty Factory data-child gates pass with unchanged Solidity0.8.26,
Cancun, viaIR, optimizer1 and Yul=false settings. No size limit was raised.
Solc executable SHA256:
`537fd8d8d4a0433a971bf456fc06f7b021cdcee27b252f74da49e0d8559aeb67`.

| Contract | Runtime bytes | EIP170 headroom |
| --- | --- | --- |
| Vault | 24,544 | 32 |
| NFT | 24,097 | 479 |
| CanonicalHandoff | 24,400 | 176 |
| VaultCanonical | 24,312 | 264 |
| NFTCanonical | 15,912 | 8,664 |
| NFTMetadata | 19,714 | 4,862 |
| SeaDropMint | 20,835 | 3,741 |
| Rewards | 24,218 | 358 |
| Budget | 24,018 | 558 |
| Balancer | 24,216 | 360 |

NFT creation is30,773 bytes plus at least128 ABI argument bytes. Actual dynamic
baseURI/deployment calldata and target deployment gas remain release work. The
renderer is separately predeployed; it is not an initcode-limit exception.
Retained failed intermediate size probes preceded that decomposition.

The original royalty Factory creation payload Keccak remains
`0x0b5b619ca10d338f29e7a76fd3f9069b2e034864112bbd3101bbc20a279c50aa`;
both original data parts are byte-identical. No old deployed runtime is relabelled.

[Static review](static-review.json), raw compressed analyzer output and
[coverage check](static/review-coverage.json) bind the final normal source.
Slither0.11.6/crytic-compile0.4.2 reports558 detector records:186 current contexts
were individually reassessed (32 mint/NFT and154 Vault/canonical/refactor
contexts);372 unique fingerprints are reused only with every referenced source
LF-identical to the prior fee-flow record. Existing transitive/upstream limits
remain. Strict matching rules are unchanged, and the CI default now selects this
record. Analyzer JSON reports success; its retained Windows process status is
4294967295. Disposition coverage is not proof of exploit absence.

## Actual upstream evidence

The original registry commit is
`d368f55f609a7f4b2245f89ff49c1a933fbeff83`. The independently captured RPC runtime
at block `0x68a00b2`, hash
`0xf48f34d754a1365ef4b4aa0cd9c49fc8221285dc34d8575befce6efb4bc19ef3`,
matches the verified21,081-byte SeaDrop V1 object. Original source/dependencies,
ABI, registry and RPC responses are retained; newer GitHub main is not treated
as deployed source. The exact11-selector interface ID is `0x1890fe8e`.

Source/dependency headers are preserved: the top SeaDrop source is MIT, while
some embedded Solmate dependency headers are AGPL-3.0-only. The test wrapper's
own SPDX label does not relabel that entire source closure.

## Focused EVM stages

| Stage | Successful methods | What it proves / limits |
| --- | --- | --- |
| Actual deployed SeaDrop runtime, attempt3 | 15 | Real upstream code with a deliberately minimal conforming NFT; payment/callback/proof behavior, not the whole PoPL graph |
| Actual PoPL mint graph, attempt1 | 18 | Real NFT/Vault/canonical/Budget/Policy/helper plus exact SeaDrop; explicit mock Access/VRF, no LP venue |
| Quota boundaries, attempt1 | 12, including64 fuzz inputs | Team reservation, allowlist rollover, lifetime/phase/collection boundaries; synthetic getter-verified historical counts are not1,000 real mints |
| NFT canonical domain, attempt2 | 11 | Actual staged mint/transfer/original recipient and1,006 rows including artwork; mismatches rejected; partial-domain/mock cancel, not full backing recovery |
| Whole six-domain handoff, attempt4 | 2 | Actual Access/coordinators/all six accounting domains; full commit/retire/activate and fully funded abort/return;3 real mints,2 active/1 dormant; positive LP and ETH/ZZZ royalty claims follow transferred owner while original minter allowances survive |
| Existing affected regressions, attempt1 | 68 | NFTMetadata33, RandomnessRequestSettings17, RoyaltyLaunchWindow15, SaleEndAuthority3; normal existing fuzz1000; no failures/skips in this stage |

Whole-handoff venue, token, correlated feeds and VRF are explicit fixtures.
Eight-row batches retain the12M protocol-step budget. Peak measured local step
was2,894,757 gas in each final whole-handoff case. Test-only external batch
frames reset EVM memory, and parent test gas is reset between transaction-modelled
steps; neither changes target call budgets nor qualifies actual target-chain gas.
Whole-handoff final verification SHA256:
`f188f4616ed1e20bde177f4992cfe4f546a876c0f0377b5bd5f29cec7f78776d`.
Its106 watched source/tool/fixture files are unchanged through the final run.

Retained negatives include initial actual-runtime compilation stack overflows
(the unchanged embedded code was split into test-only literal chunks), canonical
fixture setup failures and whole-handoff memory/aggregate test-gas/expected-memory
fixture failures. Final harness corrections preserve production code, assertions,
the8-row work bound and12M per-call budget. No failed/empty attempt is a pass.
Constructor call sites in existing test/script sources were adapted to the new
three-argument NFT constructor; this is not a claim to have rerun all those suites.

## Python and callable documentation

| Scope | Evidence |
| --- | --- |
| Strict offline builder | 28 final methods pass with bracketed source hashes; earlier stages overlap |
| Inventory17 validator/observer | 11 focused methods pass; post-run hashes are recorded, not a fabricated before/after bracket |
| Backend mint2/V10 reads/claims | 14 new focused methods pass;83 existing affected methods pass, with36 overlapping planner/lineage methods rechecked after final refinements; exact source stages remain separate |
| Function/static/mint qualification gates | 85 of86 initial methods passed; one obsolete current-template assertion was corrected and that one method passed separately. Initial failure is retained; unchanged85 were not rerun |
| Operator reference | 20 methods pass in the original tool observation; its derived receipt has method IDs/post-run hashes, no raw log or before/after bracket. Final read-only CLI checks confirm39 contracts,906 functions,39 constructors,13 receive hooks and958 example rows, with no input/output/explanation gaps |
| Example preservation | 890 prior example rows preserved exactly;2 intentionally changed,66 new,3 retired; original UTF8 archives retained |
| Final CLI integration | 6 additional focused methods pass with unchanged before/after source snapshots: default schema17 remains blocked, historical dispatch/UTF8/malformed JSON and sanitized observer failure/input behavior |

The backend implementation explicitly requires `mint_integration_version:2`,
pinned helper/SeaDrop roles and V10. Default1/V9 and historical lineage peers
remain explicit. Direct mint2 transaction preparation fails before RPC with
Use OpenSea. Actual OpenSea eligibility stays unknown rather than inferred from
coarse time/supply controls. Mutable mint terms do not gate earned LP/royalty claims.

Normal/static evidence is not rerun for subsequent documentation-only fixes.
Final [Todo/reference/default-static CLI checks](final-reference-gates.json)
pass. The [integrity receipt](final-integrity.json) checks59 changed/new Markdown
files and3,069 local-file link occurrences with no new broken file links;
fragment anchors/external sites are not comprehensively verified by that check.
Focused package hashes and the unchanged shared signer/protected files reconcile.
Schema17/backend candidate receipts are original tool-observed results with
post-run source hashes; they do not contain raw logs or bracketed before/after
proof. The source-scope index preserves that evidence-quality distinction.
Import-closure and exact staged/committed publication checks are separate.
The four pre-existing
protected dirty files and unrelated untracked drafts remain outside publication.

## Unverified release boundaries

No custom OpenSea collection/API onboarding, actual platform fee/payers, real
VRF funding/callback, target transaction/deployment gas, real wallets, hosting,
operating load, long-lived history/recovery or independent audit is qualified.
Source9 website/served profiles, public-null deployment configurations,
Anvil-only signer, existing Anvil8902 and journals are unchanged. The user-paused
heartbeat remains paused. See [remaining work](../../TODO.md#task-opensea-mint)
and [operator procedure](../../docs/OPENSEA_MINT.md).
