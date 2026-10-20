# Independent local wallet execution - 2026-10-20

## Defect and implementation

The earlier fixes handled stale cached preparation and the service lock. A third
boundary still rejected a valid second-wallet review when the first wallet's
operation advanced the global revision. The UI's Review required message therefore
remained reproducible after those fixes.

Server-held wallet drafts now pin the sender's pending nonce in the exact reviewed
transaction. A typed execute envelope must match its server draft's original
revision and account; only that path may span unrelated global revisions. Missing,
consumed, future, wrong-account or expired drafts still reject. Legacy operator
actions retain the global revision rule. The ledger remains serialized and durable,
with identical-ID replay checked before consumption and no eviction.

Execution rechecks the sender nonce, uncertainty, every reviewed NFT's ownership
(including batch claims), activation state and contribution lifecycle. The local
20-NFT cap is rechecked at execution. The existing send path freshly simulates
unchanged calldata, rejects higher gas requirements/prices than reviewed, and
broadcasts only after durable intent. A transaction from the same wallet invalidates
its other reviewed nonce; another wallet does not. Contract slippage/loss, custody,
owner and pause guards are unchanged. Claims may reflect newly funded balances as
allowed by their existing contract semantics; review values are simulated estimates.
No production Solidity or production unsigned-preparation service changed.

## Verification

- 68 distinct affected Python cases passed across wallet, wallet concurrency,
  named inputs, local stack and stack-edge modules. Eleven concurrency cases then
  passed after adding two new cases: 70 distinct cases in total, not 79 distinct
  tests. An initial discovery also ran 12 imported wallet tests twice (80 passes);
  the import was corrected and the clean 68-case run is the main receipt.
- Tests cover two senders reviewed at one revision, exact replay, same-sender nonce
  conflicts, consumed/missing/future/mismatched/expired drafts, supply cap, owner
  changes, malformed nonce, operator revision restrictions, approval lifecycle and
  activation revalidation, and two independent approvals across global revisions.
- One stale boundary fixture still allowed activation above $100. It was corrected
  to the already-published fixed local activation rule; no production floor changed.
- [Actual local mint journey](nonce-mint-observation.json): both clients reviewed
  at revision 34, with sender nonces 0x28 and 0x4. Concurrent confirmation requests
  both succeeded, producing revisions 35 and 36 and dormant NFTs #15/#16 for the
  two respective owners. Their user mint transactions were followed by the local
  fixture's mock reveal/finalization transactions, not extra user approvals.
- All 14 pre-existing NFTs retained identical owner and position records. No LP,
  rewards or allowances were changed by this mint rehearsal. Native mint gas and
  0.05 test ETH per wallet were paid on disposable chain 31337.
- [Sanitized receipts](nonce-mint-receipts.json) and [source bindings](nonce-source-sha256.json)
  record scope. The unchanged 64 website cases are reused only with matching hashes
  from the previous client follow-up; no unchanged Solidity suites were rerun.

## Running service and limitations

The existing lock-protected local stop endpoint drained the web service without
allowing a racing transaction. Its external recovery launcher closes only the
indexer on shutdown; Anvil PID 35896 was preserved. The verified web-only recovery
started PID 20672 on port 8898; exact contracts, revision 34 and all 14 positions
matched before the two test mints. Unsigned old drafts were intentionally invalidated.
The 8896 service was not restarted or updated.

This is disposable local account execution, not production browser-wallet hosting
or a public-chain performance qualification. The shared service still serializes
execution and can request fresh review for expiry, same-wallet activity, changed
ownership, invalid execution or increased gas. Public deployment/server and paused
monitor remain unchanged. Production release remains NOT APPROVED.
