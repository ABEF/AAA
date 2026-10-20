# Independent chain reads for wallet confirmation - 2026-10-20

## Incident and evidence

The user reported a successful MetaMask signing followed by a missing
`transaction.chainId` error. The app incorrectly depended on the extension's
transaction lookup representation for confirmation. The actual extension response
was not captured independently; its missing field is user-reported evidence.

Read-only inspection found the latest mint
`0x3d770ea9c6fe7c3e7892097c4149db0e1e481e87731885db1fac325943958805`
succeeded at block 362, nonce 36, on the existing chain. Direct node lookup includes
type 2 and chain ID 31337. No mint was resent to investigate or recover it.

## Documentation reviewed and correction

- [Ethereum Execution API transaction schemas](https://github.com/ethereum/execution-apis/blob/main/src/schemas/transaction.yaml)
  distinguish optional legacy chainId from required typed transaction chainId.
- [EIP-155](https://eips.ethereum.org/EIPS/eip-155) defines the legacy signed chain
  identity in v. Typed y-parity is not a substitute for a missing chain ID.
- [Viem client separation](https://viem.sh/docs/clients/intro) distinguishes public
  blockchain reads from account/signing requests.
- [Receipt waiting implementation](https://github.com/wevm/viem/blob/main/src/actions/public/waitForTransactionReceipt.ts)
  distinguishes submission, inclusion, confirmations and replacement handling.
  This patch does not claim automatic replacement/cancellation tracking.

The website now uses a read-only HTTP client pinned to its reviewed deployment
RPC for simulation, balances, nonce, gas, transaction and receipt reads. The
selected EIP-6963 wallet still handles permissions, accounts, network selection
and the one signing/submission request. Its account, chain and genesis are
checked before signing; the node chain and genesis are checked independently
before signing and before/after receipt verification. A previously sent operation
can recover on its original reader even if the extension changes networks.

The generic transport supports HTTPS and explicit loopback HTTP, finite response
size/time, abortable reads, exact JSON-RPC response IDs, no cookies, redirects,
signing methods or automatic fallback to another provider. An RPC URL change in
the current client session invalidates the deployment rather than silently moving
recovery. This is provider pinning and consistency checking, not a cryptographic
proof that the provider's history is honest. Production RPC qualification remains.

Legacy responses may resolve chain ID from EIP-155 v. Unprotected v, conflicting
explicit chain ID, missing typed chain ID and wrong-chain transactions fail closed.
The independent Python observer uses the same rule. Exact sender, target, nonce,
calldata, value, gas/fee bounds, receipt inclusion and status checks remain.
Missing transaction details while a receipt becomes visible are bounded pending
reads. No recovery path signs or resubmits the user's transaction.

## Activation and LP growth

The same shared verifier serves mint, exact ERC20 approval, activation, increases
and claims. Confirmed approval only enables a fresh Entry review. It does not
activate an NFT, change its LP amount/artwork or automatically submit Entry.
Native ETH needs no token approval; adequate existing allowance skips approval.
Entry confirmation and refreshed on-chain position data remain necessary for LP
and artwork changes. Failed/reverted transactions cannot be labeled successful.
These changes do not alter contract atomicity, slippage limits or fees.

The local HTTP security policy permits only its configured loopback RPC in
connect-src for /app/ pages. Other pages keep self-only connections. It does not
add a general RPC proxy, new signing API, wildcard source or query-selected host.

## Scoped verification

- 161 signer/client/transport cases pass on the final sources.
- 71 intent/UI/contribution/lifecycle cases pass; their code/test bodies were
  unchanged by the final RPC diagnostic and end-of-confirmation chain check.
- 43 Python observer/HTTP cases pass, including legacy signature identity and
  exact-node CSP restrictions. Total: 232 distinct website cases and 43 backend.
- [Actual mint replay](chain-reader-replay.json) recovers and acknowledges the
  existing mint with a memory-only browser journal and a deliberately unusable
  extension transaction reader. No extension reads/signing are needed for recovery.
  Node CORS and the served exact-origin CSP were checked.
- Web-only recovery 18456 -> 35448 preserves Anvil PID 10988, the session, deployment,
  all 13 NFT owners/traits/shares/LP/claimable balances and recovery journals.
  /state reads mine empty local confirmation blocks; no holder/operator transaction
  was sent. Session snapshots stay external and are excluded from evidence/Git.
- Syntax, static build, links and Todo consistency checks pass. Source bindings
  are in [chain-reader-sha256.json](chain-reader-sha256.json).

Initial edit matching stopped on a duplicate line before completing the client
patch. Two old mock-signer fixtures needed the new reader identity, and one newly
inserted Python test initially captured assertions belonging to the prior test;
these were corrected before passing runs. An initial snapshot comparison also
included deliberately advancing block/time provenance; recovery validation now
compares the economic/ownership fields explicitly. These are recorded fixture/
verification corrections, not hidden successful first attempts.

See [final signer run](chain-reader-signing-tests.log),
[earlier combined scoped run](chain-reader-combined-tests.log), and
[backend run](chain-reader-backend-tests.log). No unchanged Solidity/artwork suites,
public transaction, public server deployment or deferred load campaign was run.

## Remaining boundaries

Reload the page and recover the existing hash. Do not mint/approve again to repair
the previous operation. Actual MetaMask UI acceptance of this fix remains to be
confirmed by the user. The public website remains a simulation. The enabled
browser profile is still the explicit local deployment; the shared read transport
and identity/receipt rules are reusable production code, not a local exception.
Robinhood deployment pins, supported RPC/fee semantics, real prices/routes,
confirmation policy, operational qualification and release approval remain open.
