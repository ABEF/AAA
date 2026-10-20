# Browser-wallet integration: local qualification

Reviewed 2026-10-20. **Production release remains NOT APPROVED.**

The website now has an explicit EIP-1193 browser-wallet mode on the disposable
local mount. The selected wallet submits the holder transaction; the service
prepares unsigned calls and observes receipts. Public/static hosting remains a
simulation. This report does not qualify a public deployment or a wallet extension.

## Implementation and internal review

- Browser-side typed intent reconstructs mint, exact ERC20 approval, Entry
  activation/top-up and bounded LP/royalty claims. Unknown fields, targets,
  assets, excessive approvals, wrong NFT/pool/route/value, missing ownership,
  malformed minima/deadlines and overstated claim review amounts are rejected.
- Before sending, the independent provider must match chain/genesis, sender,
  target runtime, nonce, balance and gas limits, and simulate the exact call.
  Provider events invalidate unsigned reviews. The only enabled chain is local
  Anvil 31337; a same-chain-ID network with different genesis is rejected.
- Durable origin-local storage and a per-account Web Lock precede the single
  wallet submission request. Explicit rejection clears that request; ambiguous
  errors, timeout and lost hashes preserve recovery. No payment is automatically
  retried. Late wallet hashes are saved. Recovery only reads a saved or explicitly
  supplied matching hash.
- Receipt checks include exact transaction economics/nonce, gas limits, sender,
  target, canonical block, inclusion index, status and confirmation depth.
  Backend observation and final wallet acknowledgement must reconcile the same
  inclusion. A replacement or changed inclusion requires inspection.
- Browser reviews are removed from the local service signer registry and kept
  in a separate bounded persistent journal. Mock reveal is fixture-only operator
  work derived from the actual mint receipt and original ordered requests.
- Existing confirmed-state cards, exact approval followed by a separate LP review,
  target-only artwork updates and confirmed LP checks are reused.
- Review display derives gas cost from the validated gas fields, and contribution,
  exact approval units and 99% local LP floor from the typed input. Backend labels
  cannot understate these values or add unrelated claim/contribution figures.

Internal review found and corrected two receipt-boundary defects: backend reuse
of an earlier successful outcome after changed inclusion, and clearing the wallet
journal after inclusion changed between backend reconciliation and acknowledgement.
It also caught the browser-mode query URL returning 404. Focused regression cases
cover the corrections. Final display review found unbound backend gas/LP labels;
the browser now derives those values from the validated intent/transaction.
This internal review is not an independent security audit.

## Executed checks

| Evidence | Result and scope |
| --- | --- |
| [Backend evidence](backend-evidence.json) | 43 distinct affected Python cases across scoped runs, including real local HTTP origin/session/query routing. Overlapping executions are not counted twice. |
| Website focused Node run | 160 passes: browser signing, typed intent, adapter, existing local-client, contribution-flow and reward-display cases affected by integration. |
| Supplemental website cases | Three added cases pass for exact bounded pre-handler busy responses on browser manifest, preparation and receipt observation. No holder submission retry is introduced. |
| Final display hardening | Four new cases pass, then all 33 affected adapter cases pass with the final display derivation. Exact gas arithmetic, activation/top-up floors, USDC decimals and misleading labels are covered. Total across scoped runs: 167 distinct website cases; repeated cases are counted once. |
| [Five-transaction journey](browser-journey.json) | Actual isolated Anvil receipts through BrowserClient and BrowserWallet using an EIP-1193-shaped RPC test provider. See below. |
| UI inspection | New URL loads and the browser-wallet chooser displays the exact local RPC, chain ID and two fixture accounts. The in-app browser has no injected wallet; no extension approval is claimed. |
| Static website build | Build succeeds with 5,593 output files; application/view syntax and whitespace checks pass. |

The Node provider harness submits to the launcher's unlocked **disposable Anvil**
accounts. It exercises independent client-side submission and real receipts,
but is not a MetaMask/Rabby acceptance test. It uses in-memory test storage/locks;
the focused tests separately exercise durable-journal and cross-tab-lock failures.

The actual journey:

1. Wallet B mints one dormant NFT; receipt-derived mock reveal completes.
2. One native ETH Entry transaction activates it with 100 local mock dollars.
3. An exact 5 USDC approval leaves its LP unchanged.
4. A separate Entry transaction adds at least 99% of that contribution as LP.
5. Wallet A claims the seeded combined ETH balances. Selected ETH claimable
   balances become zero; all four original NFT owners, LP values and activation
   states remain unchanged.

Hashes, exact transactions and full receipts are retained in the linked evidence.
This journey preceded the final display-only derivation above; holder transaction
construction and signing did not change. The affected adapter suite covers that
last change without repeating the unchanged chain journey.
Network gas is separate. Every local asset, including ETH, uses the fixture's
$1 mock price. No real token, Uniswap/Pons route or market price was tested.

## Reuse and limits

No production Solidity source changed. Existing compiler artifacts were reused
only after the launcher's source-hash checks. No unchanged Solidity build/test,
large-scale load campaign, public transaction, public server deployment or paused
monitor restart occurred.

The earlier 8898 processes were already stopped. Their saved records were preserved.
A separate fixture was created at port 8900. Its first instance was stopped before
user activity to load the URL fix; the successful journey uses the second isolated
instance. No prior live chain was reset.

[Source hashes](source-sha256.json) identify the inspected final files. The earlier
manual six-scenario acceptance retains its [original scope](../local-wallet-concurrency/MANUAL_ACCEPTANCE.md).

Remaining gates include real extension/manual acceptance (including changed
network configuration and interrupted approvals), independently reviewed public
deployment pins, production endpoint adaptation, real routes/feeds, network fee
semantics, provider/replacement behavior, hosted services and independent audit.
The dynamic fixture manifest is not independent production authentication.
The dedicated 10/25/100-user campaign remains explicitly deferred.

Use the [browser-wallet operator procedure](../../docs/BROWSER_WALLET.md) and
[central Todo](../../TODO.md#task-wallet). Do not erase a pending journal or resend
a payment to work around an unresolved result.
