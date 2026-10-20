# Browser-wallet signing on the disposable local chain

## Choose another wallet account from the website

When the extension exposes a different account from the one visible in its
popup, open the website connection dialog and click **Choose a different account
in MetaMask** (or the named extension). Select the intended disposable fixture
account in its permission prompt. The site rereads permissions and verifies the
network/deployment before enabling actions. No transaction is sent.

Complete or reject an already-open wallet prompt before trying again. If the
extension does not support permission requests, use its connected-site settings.
Pending transactions must be recovered before switching accounts; never erase
the journal to bypass that guard. No operator contract call/configuration is
required. [Evidence](../reports/browser-wallet/ACCOUNT_CHOOSER.md).


The existing website has an opt-in EIP-1193 browser-wallet flow for minting,
activation, LP increases and ETH reward claims. The website prepares and checks
an exact transaction; the selected wallet signs and submits it. The local service
does not submit holder transactions in this mode.

**Scope: local Anvil, chain 31337 only.** The public website remains a simulation.
This is a reusable signing implementation exercised against disposable contracts,
not an approved production deployment. [Scoped evidence](../reports/browser-wallet/VERIFICATION.md)
distinguishes automated provider tests, actual local receipts and browser-extension
acceptance. The [central wallet task](../TODO.md#task-wallet) remains in progress.
Connection diagnostics and receipt recovery follow-up are recorded separately in
[connection and recovery evidence](../reports/browser-wallet/CONNECTION_RECOVERY.md).

## Start and connect

1. Start the [local launcher](LOCAL_TEST_STACK.md) with the existing website checkout,
   authenticated production artifacts, the native input fixture artifacts,
   `--named-assets --native-input`, and an unused `--port`. This creates a new
   disposable deployment; it does not resume an old Anvil chain.
2. Open `http://127.0.0.1:<port>/app/?wallet=browser#my-nfts` in a browser with an
   EIP-1193 extension. The exact `?wallet=browser` query opts in. The ordinary
   `/app/` page retains the launcher-owned test wallets; ordinary static/public
   hosting retains the separate simulation.
3. Connect one of the displayed fixture accounts through the wallet. Only the
   two funded disposable accounts from `/session` and `/browser/manifest` are
   admitted. Another address, even on chain 31337, cannot prepare holder actions.
   Import/select a disposable Anvil test account through the wallet's own UI;
   never use a production key or store a key in the website, repository or API.
4. Use the displayed local RPC URL and chain ID 31337. The RPC port belongs to
   that run and can change on a new run. An existing wallet network named Anvil
   may point to an older port: verify the URL and genesis, not just its name.
   Network switching/adding is an explicit wallet action; adding a network does
   not by itself prove the wallet switched to it.
5. Refresh confirmed state. Check ownership, LP and claimable balances before
   reviewing a transaction. Connection survives soft refresh through account
   reads; no transaction is sent while restoring a connection.

The dialog distinguishes the address the wallet exposes to this website from the
account merely selected in the extension. If the exposed address is not one of
the two fixture accounts, change the site's connected-account permissions in the
wallet and reconnect. The error displays that public address; importing an
account alone does not grant the website access to it.

A switch-network button is shown only for a different chain ID. Chain 31337 with
the wrong genesis is a different local deployment: correct the RPC URL to the
one displayed for this run. A failed connection stays in the dialog with its
error and cannot trigger a successful-state refresh. Reconnecting the same
provider reads its current authorized accounts and chain before verifying the
genesis again; it does not reuse a stale account or open overlapping permission
prompts. A refresh also revalidates the connection before enabling actions.

The local named inputs are ZZZ, USDG, USDC and ETH. **All have a $1 mock input
price, including ETH.** Local activation is exactly 100 input units at that mock
price; increases start at 5 input units. This does not qualify actual token prices
or conversion routes. Production Entry still enforces a $100 minimum, not an
exact-$100 maximum; production quote/rounding alignment remains open.

## What is checked before signing

The frontend reconstructs the allowed mint, exact approval, Entry or bounded claim
calldata from the user's typed intent and the configured local deployment. It
does not accept arbitrary backend calldata merely because the response succeeded.

The signing module verifies:

- The selected account, chain 31337, exact genesis and target runtime code.
- Exact destination, calldata, native value, sender nonce and reviewed gas fields.
- A fresh, unexpired review; account/network changes invalidate unsent reviews.
- Pending nonce and balance, current gas price/estimate and a fresh simulation
  of the exact transaction, with bounded gas and native-value policies.
- Separate network gas display. An approval spends no LP and does not activate
  the NFT.

An ERC20 contribution requires at most an **exact amount approval, then Entry**.
If sufficient allowance already exists, the approval is omitted. Reset-only
tokens are unsupported by this two-transaction local flow. Native ETH goes to
Entry in one holder transaction in the native fixture. A confirmed approval does
not automatically send Entry; it proceeds to a separate review of the LP action.

The local policy caps a transaction at 30 million gas, 100 gwei gas price and
1 test ETH maximum network cost; actual reviewed gas fields can be tighter.
The maximum native input is 99,999 mock ETH. These are fixture limits, not a
production fee policy. Before offering public transactions, replace the dynamic
local manifest with an independently reviewed production deployment inventory,
qualified fee semantics, supported RPCs, token routes and prices.

**Production network requirement:** the production UI must request Robinhood
Chain using an independently verified production manifest containing its exact
chain ID, approved RPCs and deployed contract identities. It must not substitute
a testnet or fall back to Anvil. These production values remain unqualified here;
the currently enabled browser signer still accepts only the explicit local
chain-31337 profile. This requirement does not enable public signing.

## Submission, confirmation and artwork

Before the single wallet send request, the browser saves a recovery record in
`localStorage`, keyed by chain, genesis and account. Same-origin Web Locks serialize
that account's submission across tabs. Different accounts have separate records
and nonces. Missing locks, unreadable storage or a failed durable write block a
new send. These browser locks are not a distributed authorization system.

The wallet request has a 15-second UI wait bound. A slow extension prompt can
remain open afterward; timeout does not cancel a wallet request. A later returned
hash is still saved while the page remains alive. There is exactly one send:
timeout, missing response and receipt recovery never automatically repeat it.
Definitive wallet rejection clears only that request's unsent record.

The signer makes bounded receipt checks, then leaves pending work for Refresh.
It checks transaction identity, sender, calldata, nonce, value, gas, receipt status,
inclusion and canonical block identity. The local observer independently checks
the receipt against its saved draft. A previously observed receipt changing
inclusion or status requires operator review; an old successful result is not
reused for a different canonical receipt.

Wallets can increase the submitted gas limit after the website's review. Recovery
can accept that adjustment only after canonical execution is verified. Sender,
destination, calldata, value, nonce and chain must still match exactly. The
submitted gas limit and gas price must remain within the local policy's hard
limits and total fee envelope; its gas price cannot exceed the reviewed price.
The receipt must use no more gas than either the submitted or reviewed gas limit,
pay no higher unit price than either submitted or reviewed price, and charge no
more than the original reviewed maximum network cost.

The original reviewed transaction remains unchanged in both recovery records;
observed transaction/receipt fields establish what actually happened. This is a
bounded receipt-reconciliation rule, not permission to raise the reviewed cost,
accept changed calldata or sign again. Pre-send checks remain unchanged. Without
a canonical receipt, the transaction remains pending or unresolved. If any paid
bound is exceeded, preserve the record for operator review. The website cannot
prevent a user or extension from editing the wallet's own confirmation.

Only a reconciled terminal receipt can be acknowledged and removed from browser
recovery storage. Confirmed state is then read again. LP and artwork do not change
on approval, submission or a guessed input value; the existing view waits for
confirmed on-chain position data. A failed history/API read does not manufacture
zero rewards or a successful contribution.

After a confirmed local mint, the fixture may fulfill its original MockVRF request
and finalize traits in mint order using the local operator account. The NFT ID is
read from the mint receipt, not the latest collection ordinal. These fixture
transactions are separate from the holder's one mint transaction and do not prove
production randomness. A failed mock reveal leaves the mint confirmed and reports
operator work pending; do not mint again to repair it.

## Local endpoints and records

| Boundary | Behavior |
| --- | --- |
| `GET /browser/manifest` | Read-only fixture chain/genesis, runtime pins, allowed accounts, assets, routes and bounded fee policy. No key or caller-selected RPC target. |
| `POST /browser/prepare` | Strict typed holder input; creates an unsigned browser review. Removes it from the launcher's `/action` signer registry. |
| `POST /browser/confirm` | Accepts only saved draft ID, account and transaction hash; observes exact canonical execution. Does not submit a holder transaction. |
| Existing `/action` | Separate launcher-owned test-wallet/operator flow. It cannot execute a browser-only draft. |
| `browser-drafts.json` | External per-run journal: reviewed transaction, original typed request, observed hash/receipt and outcome. Preserve for recovery. |
| `operations.json`, `receipts.json`, `submissions.json`, `errors.log` | Existing operation outcomes, mined receipt evidence, fixture operator submissions and errors. Inspect together with the browser record. |

POST requires the exact local Host, Origin, session header and JSON content type;
requests are limited to 2,048 bytes. There is no generic RPC relay. Shared local
work uses the fixture's existing lock, with explicit busy responses. Browser
observation can be retried for the same saved hash; it cannot replay the holder
payment. The underlying production read/unsigned APIs have their own
[bounded admission](CONCURRENT_SERVICES.md), separate from this fixture.

Browser reviews expire after 60 seconds. Receipt observation can occur later:
a signed transaction may be mined after the UI review expires. The server-side
browser review journal has a 256-record and 16 MiB limit. Records are not evicted merely because
a review expired; it might have been sent. At capacity, preserve and inspect
evidence before starting another disposable fixture.

## Failure and recovery procedure

| Symptom | Required action |
| --- | --- |
| Wallet exposes an ordinary account instead of fixture A/B | Use the displayed public address to inspect the wallet's site permissions. Authorize the intended disposable account, then reconnect. Do not mint or transfer funds to solve a connection error. |
| Wallet reports chain 31337 but the connection is not verified | Check the exact RPC URL and genesis for this run. A chain-ID-only switch is insufficient; another Anvil deployment can use the same ID. |
| Wallet rejection | Inspect whether the wallet reports a definitive rejection. A confirmed approval remains on-chain; reprepare and reuse its sufficient allowance. |
| Wallet prompt exceeds the 90-second response wait | Inspect the existing prompt/activity. Keep the original request; do not submit it again. Refresh to recover a later returned hash. |
| Browser refresh while a transaction is pending | Reconnect to the same account, exact RPC/genesis and origin. Refresh reads the saved hash and verifies its receipt; it does not send again. |
| Wallet sent, but the page never received a hash | Keep the recovery record. Copy the exact hash from wallet activity into recovery; identity and reviewed nonce/calldata must match. If no hash can be established, stop that account's new actions and inspect wallet/RPC records. |
| Account or chain changed | Unsent reviews are discarded. A sent transaction remains associated with its original account/genesis; switch back and recover it. |
| Wallet increased the gas limit | Recover the existing hash. Canonical execution may be accepted only within the submitted-policy and original reviewed paid bounds described above. Preserve the original review; never repeat a confirmed approval or contribution. |
| Wallet replaced/cancelled a transaction, changed economic fields or exceeded reviewed paid bounds | Do not clear storage or assume success. Inspect the original/replacement receipts and account nonce. Automatic replacement searching or accepting different calldata is not implemented. |
| Receipt disappeared or changed after observation | Preserve old/new hashes, inclusion and outcome records. Do not acknowledge or replay a payment. Reconcile canonical execution before continuing. |
| API/indexer read failed after receipt success | Retry confirmed reads. Preserve the successful transaction; a projection failure is not a reason to pay again. |
| Mock reveal failed | Inspect the original request and the operator's submissions; complete only the original request in order. Never reroll or mint a replacement. |
| Storage/Web Locks unavailable or journal full | Stop new sends. Restore supported browser storage/locks or inspect and archive the disposable session; never disable recovery checks to bypass the error. |

No wallet private keys or session tokens belong in reports or Git. Preserve public
transaction hashes, receipts, source bindings and sanitized outcomes.

Wallet response and RPC-read waits are separate: 90 seconds for the extension,
15 seconds per read. Confirmation polls the same hash up to 21 times at 1500ms spacing,
within a 45-second monotonic read budget; no retry sends a transaction.
One confirmation requires two matching canonical block hash/number reads;
additional confirmations still require the configured depth. This avoids a
separate cached head vetoing checked inclusion. See
[automatic confirmation evidence](../reports/browser-wallet/AUTO_CONFIRMATION.md). If still unresolved,
inspect the wallet and recover the saved hash. Keep the original request and
review. Ordinary refresh shows labeled last-confirmed cards with actions disabled;
read failures or account/session changes must not present those values as current.

Local portfolio reads reuse one literal-loopback HTTP connection only within the
serialized read and close it on completion/failure. This changes no operator
permissions or production RPC configuration. A web-only update must authenticate
the original chain/session/journals; never restart Anvil to clear a slow read.
See [latency and mint follow-up](../reports/browser-wallet/MINT_WAIT_PERFORMANCE.md).

## Stop, restart and rollback

The local operator may close an unsigned review at any time. A wallet request
already sent to the extension must be inspected there; closing the website does
not cancel it.

Do not restart Anvil to fix a page error. The ordinary launcher owns its Anvil
child; stopping it shuts down that disposable chain. A fresh start creates a new
genesis/deployment and cannot recover old chain state. Keep each run directory and
all pending records. A deliberately prepared web-only recovery must authenticate
the original running chain, contracts, submission ledger and session before reuse;
the normal launcher is not a persistence or migration tool.

For a frontend rollback, preserve pending browser records and keep receipt
observation available until they are reconciled. Returning to ordinary `/app/`
does not cancel extension transactions or authorize the local signer to resend
them. Do not roll back transaction/recovery checks or delete the journal to clear
an error. This change introduces no contract authority, sealing operation,
production service command or public deployment.

## Evidence and remaining qualification

The scoped candidate has 43 affected Python checks and 167 website checks, plus
five actual holder transactions through an EIP-1193-shaped local RPC adapter:
mint, native ETH activation, exact USDC approval, USDC increase and ETH claim.
The four original fixture NFT ownership/LP/activation records remained unchanged.
The adapter exercise is **not** browser-extension acceptance or public signing.
See the [verification record](../reports/browser-wallet/VERIFICATION.md) for exact
source scope, receipts, corrections and limitations. The later
[connection and recovery record](../reports/browser-wallet/CONNECTION_RECOVERY.md)
separates the actual extension observation from its focused fixes; the initial
test counts above are not new evidence for those changes.

Actual Chrome/extension behavior, production manifests, provider semantics, live
routes/feeds, hosting and independent review remain open. The user-deferred
10/25/100-user campaign remains deferred; no production capacity claim follows
from this work. Release remains **NOT APPROVED**.
