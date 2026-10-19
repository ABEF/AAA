# Unsigned mint/claim preparation: scoped verification

Reviewed 2026-10-19 against base `61f2ac89fa58b605ee2fba04b82019ed7e23210c`.
The saved optional preparer is promoted with current lifecycle gates, request
limits, selected-currency failure isolation, fee policy and supervised HTTP.
Publication is established by Git, not by the existence of this report.
**Release remains NOT APPROVED.** No Solidity, website/server, public-chain
transaction, deployment, signer or paused-monitor change occurred.

## Current checks

| Evidence | Result / exact scope |
| --- | --- |
| First affected Python run | 143 executed: 142 passed, one fixture failure, no skips/errors. Source remained unchanged during execution. |
| Corrected affected preparation/HTTP run | 60 passed, zero failures/errors/skips. Includes six additional activation-HTTP compatibility cases. |
| Current inventory | **149 distinct tests have passing evidence** across the two runs. Changed transaction fixtures and their consumers were rerun; unaffected API/lifecycle/activation/budget results were retained. This is not a single fresh full regression. |
| Contract evidence reuse | 40 unchanged Solidity source bindings and compiler configuration match the prior royalty build. Six relevant functions, including tuple-array claim ABI, match compiler artifacts whose production inputs were checked. No build/Solidity suite was repeated. |
| Exact claim encoding | Three historical Solidity `abi.encodeCall` vectors (one uint256-max claim, mixed native/LP/royalty claims, maximum 32 operations) match the current encoder, frozen vectors and unchanged router source/current compiler ABI. These are ABI evidence only, not reuse of an entire older contract test suite. |

The [source and inventory receipt](source-and-abi.json) contains exact hashes,
test-to-run coverage and ABI checks. Raw runs:
[initial receipt](attempt1/receipt.json), [initial test output](attempt1/stderr.log),
[corrected receipt](confirmed/receipt.json), [corrected output](confirmed/stderr.log).
The isolated test trees used published HEAD plus only the selected code/test
manifest. Unrelated dirty history-test, route, process-runner and artwork files
were not incorporated. Historical vector proof is retained as
[fixture](abi-reuse/WalletCalldata.fixture.sol), [compiler run](abi-reuse/forge-abi.log)
and [original binding](abi-reuse/source-sha256.json). Its older interface bindings
are historical; current ABI/source verification is the separate receipt above.
The JSON vector fixture uses LF in publication; only CRLF line endings changed
after execution. Exact normalized-byte equality and identical parsed vectors are
verified; the receipt retains both the original execution and publication hashes.

The initial reorg test expected rejection during the final projection check.
With gas estimation added, the mocked node instead encountered the invalidated
hash sooner and raised a fixture assertion. The fixture now models the actual
RPC rejection, and the test accepts that fail-closed RPC error. No production
code changed between runs. The 60-case rerun covers the modified fixture's
preparation/HTTP consumers, rather than repeating unrelated passing suites.

## Internal review and behavior

- **Intent and authority:** strict typed actions, fixed targets/value, exact
  ownership and ordinal/ledger checks; no supplied arbitrary call, recipient,
  chain, approval, nonce or state override. No signer/broadcast API. Simulation
  from a public address does not authenticate its holder; the wallet must sign.
- **Mint controls:** canonical operating state, preparation/global/mint pauses,
  exact supply and price. Full simulation remains required for VRF/recipient
  callbacks; unrelated reward currencies no longer block mint preparation.
- **Claim isolation:** full core and inventory checks remain mandatory. Only
  unselected asset runtime/decimal failures may be isolated. Selected failures,
  malformed inventories, unavailable entitlement or exact-call reverts reject
  the whole draft. WorkLimit is terminal. Claims remain independent of pauses
  while operating; canonical locks cannot be bypassed.
- **Gas and funds:** required policy binds deployment/read configuration and
  reviewed complete fee semantics. Bounds apply to estimate, gas price and
  suggested-limit cost; native payment and gas are separate. Expected claim
  proceeds cannot fund upfront gas. Missing hash-estimation support has no
  latest-state fallback. Gas is a quote, not a guarantee of inclusion cost.
- **Availability:** direct/nested work budgets and stricter snapshot expiry;
  serial supervised HTTP with bounded cleanup. Inputs/results are bounded,
  errors sanitized, read-only default preserved. Reorg/expiry after simulation
  or estimation cannot produce a successful draft.
- **Integration:** actual loopback HTTP request parsing, direct preparer and
  process boundary tests cover their respective layers. These are offline RPC
  fixtures, not a hosted production or browser-wallet rehearsal. Approval,
  signing, account/chain changes and receipt handling remain browser work.

No unauthorized principal path or hidden recipient was added in this scoped
review. This is internal review, not an independent audit or a no-vulnerability
guarantee. Reviewed RPCs may still misreport state; code pins are not consensus
finality proofs. The operator attests fee completeness, and public ingress can
still suffer resource exhaustion without qualified proxy/rate/monitoring controls.
Short expiry is a client rule, not a contract deadline. Frontend revalidation and
receipt/replacement/reorg recovery are required before real wallet use.

## Operational impact and remaining work

The [operator procedure](../../docs/OPERATOR_MANUAL.md#unsigned-mint-and-claim-service)
and [API guide](../../docs/FRONTEND_TRANSACTIONS.md) define the new required policy,
enable/disable commands, validation, separate gas and recovery boundaries.
The [central task](../../TODO.md#task-unsigned-actions) and
[feature reference](../../docs/IMPLEMENTATION_STATUS.md) are reconciled.

Actual deployment/runtime manifest, VRF, complete network-fee/hash-provider
qualification, hosting/load/ingress, live wallet integration and independent audit
remain open. No production address or fee policy was inferred. Existing activation
preparation is separate; this change does not qualify real activation routes.
