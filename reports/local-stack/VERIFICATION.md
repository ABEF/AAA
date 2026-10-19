# Local browser stack: scoped verification

2026-10-19. **Internal local integration evidence; release NOT APPROVED.**

The user requested a working local setup using disposable wallets. The launcher
deploys the unchanged core candidate to its own Anvil chain 31337, binds and seals
the modules, configures a test pool, and connects real raw-event ingestion and the
confirmed API to a separate local browser panel. No private key, public-chain
transaction, website source change, server update or monitor restart occurred.

## Executed evidence

- **20 journey assertions passed**: four initial NFT evolution states; funded
  fees; missing-session/origin/unsupported-action rejection; prepared mint;
  $100 activation with no retroactive fees; top-up into the same shared LP;
  funding both streams; a governed range change and rebalance; preservation of
  old fees across rebalance/transfer; rejection of the former owner; combined
  claims; cumulative lifetime claims; no duplicate earnings; missing ETH USD mark.
- **Seven launcher boundary checks passed** in `tests_python.test_local_stack`:
  exact block-hash read deduplication and request separation, changed/missing
  runtime detection, owned-process guard, external-account rejection and local
  value cap. These do not test public-wallet signing.
- Browser inspection confirmed on-chain trait artwork, four holder cards, actual
  fee balances and receipts. The local confirmation dialog opens and cancellation
  returns to the unchanged panel. JavaScript syntax check passed.
- Local fixture compilation completed with Solidity 0.8.26 and the repository's
  existing settings. Initial sandbox invocations returned a post-compilation
  Foundry signature-cache error. A permitted cache completion returned exit 0,
  reusing the same compilation; only naming-style lint notes remained.
- **40 production Solidity bindings match** the prior royalty-conversion build.
  The launcher independently checks every used artifact's metadata source hash,
  including dependencies. No unchanged production Solidity tests or full build
  were rerun. Production source is unchanged.

[Journey assertions and transaction summary](journey.json) retain transaction
hashes, statuses, gas and native balance changes. Their complete receipts and
full API snapshot are kept in the external session directory, with SHA-256
bindings in that record. [Source bindings](source-bindings.json) identify this
local implementation and reused production source. The original journey predates
the edge-case hardening below; it is not represented as current-source full coverage.
None of this is a full production regression or independent audit.

## Corrections during setup

The first read configuration incorrectly anchored history at the controller's
deployment, before the NFT existed. The API rejected the missing historical NFT
runtime; the launcher now starts at the exact NFT creation block and parent hash,
including child royalty-admission events. No projection guard was weakened.

A first journey attempted a $50 top-up against a test pool configured with a
$100 per-contribution minimum. Its Entry simulation rejected it after the exact
approval, leaving principal unchanged. The journey and UI now use that pool's
$100 floor. This was a fixture/driver mismatch, not a production defect.

The original single-thread HTTP server could stall behind browser preconnections.
The final server serves assets concurrently and serializes all state/transaction/
indexer work. Pure exact-runtime-byte hashes are bounded and memoized; only exact
hash-bound RPC reads within one aggregate response are deduplicated. The final
canonical header checks and all independent requests remain fresh.

## Internal review and remaining boundaries

- Loopback only, launcher-owned Anvil child, fixed chain/client/genesis checks,
  local-account allowlist, typed actions, exact approvals, fresh simulation,
  gas/balance/value limits and recorded successful receipts.
- Host/origin/session checks and bounded JSON prevent an arbitrary website from
  using the local action endpoint. There is no public RPC argument, arbitrary
  calldata relay, private key read or unrestricted recipient. This convenience
  server must never be used as a production signer or exposed to the Internet.
- LocalDemoVenue replaces the actual LiquidityManager and Uniswap, with a
  deterministic funded ERC20 venue. LocalFeed and MockVRF are explicit mocks.
  This cannot qualify real swaps, concentrated-liquidity math, Pons funding,
  feeds, real VRF, MEV, production gas or keeper reliability.
- Clock advancement and mocked fresh prices are local testing conveniences.
  Production API freshness remains unchanged. The lab deliberately starts fresh
  after shutdown; it is not a chain-state recovery service.
- Production website integration, actual supported input routes, hosted services,
  target-chain rehearsals, pre-seal migration gaps and independent audit remain
  open in the central Todo. No production approval follows from this test panel.

## Edge-case hardening follow-up

The user explicitly requested strange inputs and failure recovery. Internal review
found local-panel gaps: requests were not idempotent, invalid small contributions
could send an approval before failing, duplicate JSON/header fields were accepted,
and a lost post-transaction refresh could obscure an already successful action.
These affected the new local test service, not production Solidity.

Changes: exact schemas, canonical ID/amount strings, owner/lifecycle/balance checks
before approval, session-scoped operation IDs, stale-revision rejection, nonqueued
concurrent mutations, 256 retained operation records, 12 HTTP worker slots,
five-second socket timeout and 2,048-byte bodies. The confirmation dialog resets
its cancel state and suppresses repeated clicks. Missing USD marks remain unavailable.

Transaction intent/hash/receipt and operation outcomes are saved separately using
atomic file replacement. Lost HTTP responses recover the existing outcome.
Uncertain broadcast/receipt or operation-persistence failures stop new actions.
Refreshing after a session restart does not replay an old operation. This is a
fresh disposable-chain recovery policy, not a production wallet/nonce service.

- **35 focused tests pass**, zero failures/skips; see [results](edge-unit.json)
  and [raw log](edge-unit.log). Includes malformed and nonfinite JSON, duplicate
  headers, short/oversized bodies, canonical number bounds, wrong ownership,
  wrong activation state, insufficient balances, gas/chain/client/genesis guards,
  failed simulation, concurrent calls, stale revisions, changed payload replay,
  lost response recovery, partial approvals, full replay-ledger capacity, disk
  persistence failures and preserving a receipt when a later balance read fails.
- Initial development runs of 29 and seven selected checks also passed. The final
  35-case run was justified by the subsequent atomic-persistence changes; these
  are not 71 distinct tests or additional Solidity coverage.
- The expanded Anvil journey exercises the same core economic path through the
  new request envelope, then checks duplicate mint replay, stale/changed requests,
  malformed amounts, wrong modes/owner, unknown IDs, empty claims and insufficient
  balances. **39 assertions passed**, zero failures; [transaction/evidence summary](edge-journey.json).
- That journey server was started before the final atomic-file/persistence-failure
  hardening. The 35-case run covers those final changes, and the browser server at
  8890 was freshly started from the final launcher. No unchanged contract build,
  fork or broad Solidity suites were rerun.

A local response timeout is not a failed financial action. Use Refresh to recover
with the same operation ID. After an uncertain RPC submission, preserve the logs
and restart the disposable chain. The production integration and live-service
release gates remain open.

Browser checks on the final restarted launcher reject a 99-unit activation before
opening a transaction dialog; a valid 100-unit input opens it and Escape cancels
without changing the four NFTs or receipt list. The final panel also confirmed a combined claim: both claimable streams became
zero and lifetime LP/royalty claims increased. Escape cancelled a later mint
without reusing the previous confirmation. See [final browser smoke](browser-smoke.json).
