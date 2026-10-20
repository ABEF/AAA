## Canonical dynamic-fee receipt recovery - 2026-10-20

The user's mint 0xa7f91e…ac3891 succeeded at block 351. Anvil's derived fee fields
reported 1,000,000,014 wei/gas although signed cap and actual balance charge were
1,000,000,007. Shared signing and independent observation now derive EIP-1559
execution price from signed caps and canonical block base fee; original gas/unit/
paid-cost limits remain. Raw reported fee is retained separately. Deterministic
verification failures surface immediately with their specific reason.
[Evidence](../reports/browser-wallet/DYNAMIC_FEE_RECEIPTS.md): 142 signer/client and
40 observer tests, actual read-only mint receipt/balance replay, syntax/build pass.
Only local web worker restarted; session, 12 NFTs/LP and Anvil preserved. No new
holder/operator transaction or public deployment. Actual extension recovery retest
and production fee/profile qualification remain open.

## Mint loading presentation - 2026-10-20

Mint button loading now follows the actual activity instead of a generic busy
flag. Initial/refresh reads, connection, mint preparation, wallet confirmation,
receipt waiting and confirmed-state reconciliation have separate labels. Claims,
approvals and LP actions cannot label the button as a mint in progress. Existing
readiness/pending guards remain. See [evidence](../reports/browser-wallet/MINT_LOADING.md):
44 affected UI/lifecycle/contribution cases, syntax/build and served-source checks
pass. No signer, contract, backend, transaction, service or public deployment change.

## Numeric wallet nonce compatibility - 2026-10-20

The user supplied the exact failure: eth_getTransactionCount returned a number.
The shared website signer now accepts only exactly representable nonnegative JS
integers at its RPC response boundary, converting directly to BigInt. Hex responses
remain supported; prepared transactions/journals remain canonical hex. This has
no local-chain/address exception and keeps exact nonce, gas and receipt guards.
139 affected signer/client cases pass after reproducing the original failure.
See [evidence](../reports/browser-wallet/NUMERIC_NONCE.md). Actual MetaMask retest is
pending; public signing/Robinhood manifest qualification remains open. No backend,
contract, chain reset, public transaction, deployment or monitor change.

## Wallet lifecycle review - 2026-10-20

The browser connection/signing flow now separates provider discovery, account
selection, deployment verification, submission, receipt and balance refresh.
EIP-6963 providers take precedence over the legacy slot. Cancelled account choices
cannot poison later connections; network addition is followed by a verified switch;
account events and late provider restoration revalidate without transaction prompts.
The review identifies the extension/full sender and distinguishes unsent failures,
rejections, pending recovery and confirmed receipts. Existing exact approval,
calldata/gas, journal and confirmed-artwork safeguards remain.

[Scoped lifecycle review](../reports/browser-wallet/LIFECYCLE_REVIEW.md): 203 affected
website cases, syntax/build and served-source checks pass. The saved mint preflight
passes through direct local RPC without sending. Actual MetaMask acceptance and
its reported pre-prompt failure remain unresolved; Chrome inspection hit an app
approval timeout. No transaction, chain/service reset, backend/contract change,
public deployment or load campaign. Release remains NOT APPROVED.

## Review-dialog diagnostics follow-up - 2026-10-20

The transaction dialog now shows the escaped underlying failure instead of only
Review required. At observed local block 333 no new Wallet A mint was mined;
next nonce remained 0x23. Direct node balance/nonce/gas/estimate reads returned
canonical quantities. Actual browser-provider error is still needed; no confirmed
root cause or successful mint is claimed. Syntax and build pass; unchanged
signer/client tests were not rerun. No transaction/service/contract change.

## Wallet numeric-response failure - 2026-10-20

Reload updated frontend files. A failed preflight identifies the RPC field and
states that this operation was not submitted; refresh balances before another
review. If a saved submission exists, recover its original hash instead. Never
delete the journal or repeat a potentially confirmed approval/mint. Collect the
exact field diagnostic and wallet transaction hash when investigating; no keys
or full session data. Bounded hex padding is accepted only for provider reads.
[Evidence](../reports/browser-wallet/RPC_QUANTITIES.md): 123 focused passes.
The user's actual MetaMask response/root cause remains unconfirmed.

## MetaMask explicit reconnect follow-up - 2026-10-20


### Fresh MetaMask selection (2026-10-20)

This supersedes the earlier statement that explicit reconnect retains a chosen
sender. Refresh can retain a completed authorized selection, but clicking the
MetaMask button starts a fresh permission choice. Select the intended account in
MetaMask; if multiple accounts are shared, use its exact address in the website
picker. An unfinished choice cannot restore the previous sender. Pending
transactions must still recover under their original sender before switching.
No network or service configuration change is required; reload the updated app.
[Scoped evidence](../reports/browser-wallet/FRESH_SELECTION.md): 90 affected
passes; actual Chrome extension acceptance remains open.

## Authorized wallet account selection and clean picker - 2026-10-20

Fresh wallet picker sessions hide previous-attempt diagnostics and old provider
controls; actual pending-recovery notices and internal connection guards remain.
After choosing a provider, its authorized fixture accounts are selectable in the
website. Never infer the intended account solely from eth_accounts[0] or silently
choose a different allowed account. Wallet A may be selected even if an older
address is returned first; selection survives reload while still authorized.
The extension's private popup selection is not readable by the website.

Signer checks now require the explicitly reviewed sender to remain a valid member
of eth_accounts, plus unchanged account-event revision, network/genesis and all
existing economic/receipt checks. Revocation, wrong chain/genesis and pending
journals still block operations. Missing account permission requires one explicit
wallet authorization; no permission request on refresh and no silent substitution.

180 affected tests pass across 171 existing and nine new focused cases; syntax
and 5,593-file build pass. Read reports/browser-wallet/AUTHORIZED_ACCOUNTS.md.
No holder transaction, backend/contract change, chain/service restart, public
deployment or monitoring change. Actual MetaMask UI acceptance remains open.
Use main, preserve unrelated drafts, maintain the central Todo, feature evidence,
operator notes and both memories. Production remains NOT APPROVED.

## Main wallet button account retry - 2026-10-20

The user clarified that refresh restored the rejected MetaMask address and
clicking the main MetaMask button appeared to do nothing. The previous separate
chooser did not fix that normal button's read-only retry path. Main provider
click now rereads a previously rejected/restored account and invokes its selected
extension's chooser if that address is still inadmissible. If external wallet
selection already corrected it, normal verified reconnect avoids another prompt.
Refresh itself never opens permissions. Pending journals and exact deployment
checks remain; no silent account substitution or transaction send.

53 client tests pass, including four new rejected/restored/cancelled/corrected
retry cases. See reports/browser-wallet/ACCOUNT_CHOOSER.md (follow-up) and
docs/BROWSER_WALLET.md. Actual MetaMask acceptance still needs the user's click.
No backend/contract change, service/chain reset, public deployment or monitoring
change. Use main and maintain Todo/features/operator notes and both memories;
preserve unrelated drafts. Production remains NOT APPROVED.

## In-page wallet account selection - 2026-10-20

The user reports Rabby works but MetaMask exposes a previous site-authorized
address while another account is visible in the extension. Do not assume the
website can silently change wallet permissions. The local connection dialog now
offers Choose a different account in the selected extension. Its explicit click
requests only eth_accounts permissions, then reads current accounts/network and
verifies the admitted fixture account and exact deployment. Ordinary reconnect
remains read-only when already authorized; no automatic permission prompts.

Expected account-change events during the chooser do not invalidate the final
fresh verification. Cancellation, unsupported methods, busy prompts, empty/wrong
accounts and wrong networks stay unverified. Pending transactions block account
selection and retain their journals. No signing/transaction/approval occurs.
49 client checks pass including seven new cases; JS syntax and 5,593-file build
pass. See reports/browser-wallet/ACCOUNT_CHOOSER.md and docs/BROWSER_WALLET.md.
Actual MetaMask chooser acceptance remains user verification. No backend,
contract, Anvil/service/public deployment or monitoring changes. Use main;
keep Todo/features/operator procedures and both memories consistent, preserve
unrelated drafts. Production remains NOT APPROVED.

## Automatic receipt confirmation follow-up - 2026-10-20

The user still saw manual recovery after mint. The reported b041662e...6822560
receipt succeeded at block274. Read-only replay with its original review
reproduced old pending behavior under a synthetic lagging eth_blockNumber;
this cache condition was not directly observed in the extension.

One-confirmation inclusion now requires two canonical block hash/number reads,
without a separate cached head veto. Additional confirmations still require
the configured depth. Automatic polling is 21 attempts/1500ms, bounded by a
45-second monotonic read budget (each RPC also has its existing 15-second cap).
This supersedes the previous three-attempt/750ms note. The separate 90-second
wallet response wait remains. Same hash only; no automatic resubmission.
Persistent faults retain recovery, and the client displays the specific pending
reason. Economic, original gas, identity, genesis and reorg checks remain.

54 wallet and 42 client checks pass, with seven new cases. Read-only replay
confirms the actual mint without signing, acknowledgement or backend writes.
See reports/browser-wallet/AUTO_CONFIRMATION.md and docs/BROWSER_WALLET.md.
Refresh Chrome to load the changed client; actual extension acceptance remains
open. No service/Anvil restart, contract change, public deployment or monitor
restart. Keep main, preserve unrelated drafts, maintain Todo/features/operator
procedures and both memories. Production remains NOT APPROVED.

## Mint confirmation and local read latency - 2026-10-20

The user confirmed the minted NFT appears after Recover status. The successful
mint was inspected on-chain; the original UI failure cause is not established.
Wallet submission now has a separate 90-second response wait (read RPCs retain
15 seconds), and receipt faults retry the same hash up to three times. Never
resubmit a payment automatically or erase unresolved recovery records.
Same-account/session refresh preserves labeled confirmed cards with actions
disabled; failed reads and account changes do not present cached values as current.
Confirmed LP execution still controls artwork and sound.

The local serialized portfolio read now reuses its literal-loopback HTTP
connection, closing it at the end or on failure. Chain, canonical hash, response
identity, size and work-budget checks remain. Default production RPC transport
is unchanged. Eight-NFT state reads measured 6.057s before, 3.723s cold and 1.904s
warm after. This is not production capacity qualification.

48 signer, 8 contribution-flow and 35 Python cases pass; website build passed.
Read reports/browser-wallet/MINT_WAIT_PERFORMANCE.md and docs/BROWSER_WALLET.md.
Only the web process changed to 21472; original Anvil10988/RPC61752, session,
revision22 and eight NFT owner/LP/reward/trait records were preserved. Always
read running.json before process control. No holder/operator test transactions,
public deployment, unchanged Solidity rerun or paused-monitor restart.
Use main, preserve unrelated drafts, keep the single Todo ledger/features/operator
procedures and both memories consistent. Release remains NOT APPROVED.

## Browser-wallet local integration - 2026-10-20

Read [the browser-wallet procedure](BROWSER_WALLET.md) and
[scoped evidence](../reports/browser-wallet/VERIFICATION.md). The explicit local
/app/?wallet=browser profile uses injected EIP-1193 signing, independently checked
typed calldata, exact approvals, chain/genesis/runtime/nonce/gas checks and durable
per-account recovery. Browser drafts cannot use the service holder signer. Never
automatically retry a payment or erase an unresolved journal. Confirmed receipts
and actual LP reads still govern artwork/sound; approval alone changes no LP.

43 affected Python and 167 distinct JS cases pass across scoped runs. A five-user-
transaction Anvil journey covers mint, native activation, exact USDC approval and
top-up, and ETH combined claim, preserving the original four positions. The probe
uses an EIP-1193-shaped RPC test provider, not an actual extension. Chrome/MetaMask
acceptance remains open. Production deployment pins, live endpoint adaptation,
routes/services and independent release approval remain open; public signing is
disabled and release remains NOT APPROVED. The large load campaign stays deferred.

The previous 8898 processes were already gone. Separate 8900 fixture data is in
EXT/browser-wallet-lab/run-20261020-180024-5688c6; read running.json before process
control. No old live chain reset, public deployment or monitor restart. Use main,
preserve unrelated drafts, and verify Git for publication. Keep central Todo,
feature evidence, operator procedures and both repository memories consistent.

## Manual acceptance and next priority - 2026-10-20

The user reports all six proposed local 8898 two-wallet scenarios passed; read
[manual acceptance](../reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md). This is
user-reported evidence, not new automated tests or independently captured receipts.
The user deferred the proposed 10/25/100-user load campaign; do not run or schedule
it without a later request. Production capacity remains UNVERIFIED. Next focus is
real browser-wallet integration with unsigned preparation and independent signing.
Basic bounded service concurrency, safe transaction recovery and dependency/release
qualification remain required before real funds. The shared local signer/lock is
test-only. Release remains NOT APPROVED. Use main; preserve unrelated drafts.
No code/test/service/deployment/monitor change is included in this documentation
update. Keep Todo, feature evidence, operator procedures and both repo memories
consistent; docs/project-todo.json is the sole task-status ledger.

## Independent sender nonce checkpoint - 2026-10-20

Current 8898 web PID20672 uses per-sender nonce-bound wallet drafts, resolving the
remaining cross-wallet global revision rejection. Anvil PID35896 was preserved.
Both real local mints reviewed at revision34 confirmed at35/36, adding dormant
#15 and #16 (one per owner); 14 existing owner/LP records unchanged. Read
[verification](../reports/local-wallet-concurrency/NONCE_VERIFICATION.md).
70 distinct affected Python cases pass. Reload browser pages; old unsigned reviews
were invalidated by the guarded web-only restart. Preserve saved pending intents
for identical-ID recovery. Legacy operator actions retain global revision checks.
No production Solidity/public server/monitor change. Port8896 not upgraded.
Main only; preserve unrelated drafts and verify Git for publication.

## Second-wallet submission lock follow-up - 2026-10-20

The browser error was the exact pre-handler /action busy response. Client now
waits with the identical durable envelope only for that response. Ambiguous
responses keep recovery; stale reviews are not automatically submitted. 64 cases
and real local lock/rejection probe pass; see reports/local-wallet-concurrency.
Reload pages, preserve pending intents and Anvil; no service restart needed.
No public deployment or production contract/backend change. Main only.

## Cross-browser local wallet continuation - 2026-10-20

Chrome/Codex stale-cache confirmation mismatch fixed in website local-client.js;
read [evidence](../reports/local-wallet-concurrency/VERIFICATION.md). Reload both
8898 pages to load it; do not restart or reset either Anvil chain. Newer unsigned
drafts reconcile actual confirmed state with bounded retries. Post-review changes
still require fresh review; backend global revision protection remains. Ambiguous
submissions keep the identical pending ID. Only confirmed pre-handler rejections
clear saved intent. No production contract/server/monitor changes. Main only,
preserve unrelated drafts and verify Git publication.

## Latest local continuation - 2026-10-20

Local read-clock bottleneck and contribution flow corrected; see
[verification](../reports/local-contribution-flow/VERIFICATION.md). Existing
8896 Anvil/NFTs/LP were preserved through a web-only recovery. A separate native
fixture is available at http://127.0.0.1:8898/app/#my-nfts with mock native venue
admission. ETH is one atomic Entry call; supported ERC20 needs at most exact
approval plus Entry. The current processes use external session recovery launchers;
consult the external run directory/running.json before process control. Do not
reset either chain or assume normal launcher restart resumes its persisted state.
Only the web processes were replaced; old unsigned drafts are invalidated.
No public deployment/server/paused-monitor change. Main only; preserve unrelated
drafts and verify Git publication. Production still requires live route/service
qualification and fixed-$100 pricing policy alignment.

## Local activation busy-response fix - 2026-10-20

The current local website adapter retries only pre-handler busy unsigned
preparation, with bounded waits, account/state cancellation and unchanged expiry.
Never auto-retry submission. Reload the page; preserve the running 8896 Anvil
state. No contract/backend restart or public server change is needed. Read
[scoped evidence](../reports/local-preparation-busy/VERIFICATION.md). Production
wallet integration remains open; check Git for publication.

## LP holder ETH settlement checkpoint - 2026-10-20

The user approved a 1% maximum LP reward conversion loss, gas separate. Read
[the operator procedure](LP_ETH_SETTLEMENT.md) and
[scoped verification](../reports/lp-eth-settlement/VERIFICATION.md). A dedicated
pre-seal-bound converter checkpoints earned 80% individual/10% collective
balances and credits ETH to the same NFTs. Principal, compound/buyback, dust
and rarity economics are unchanged. Source claims remain an explicit fallback.
Native payouts, exact backing/abort and same-chain handoff, bounded keeper
priority, history/earnings reconciliation and ETH-default local UI are implemented.
Vault/Fees handoff helpers skip the Rewards-only native slot. Do not reintroduce
ERC20 reads at asset zero or count conversion as new earnings/claimed income.

142 distinct affected Solidity cases pass across scoped runs, with 32 normal
object gates/41 production bindings and a 33-assertion fresh local Anvil journey.
Backend/UI results, initial failures and corrected fixtures are recorded in the
report. This is not a full fresh regression or independent audit. Actual routes,
feeds, wrapper policy, operator pins, Linux/gas/settlement-latency qualification
and release approval remain open. Core sealing alone does not certify converter
setup; require the binding before sealing. Production remains NOT APPROVED.

Use main; check Git and deployment receipts for publication. The separate new
local fixture uses port 8896; prior user fixtures were not reset. No public
contract transaction/deployment or paused-monitor restart. Preserve unrelated
drafts; keep Todo, feature evidence and operator procedures together.

# Client admission continuation - 2026-10-20

The current change closes the local per-client admission implementation gap in
host services: bounded IP concurrency/state, separate read/preparation rate
budgets, explicit local-proxy identity and exact-origin validation, and restricted
Nginx includes. Read [the operator procedure](API_INGRESS.md) and
[scoped verification](../reports/api-admission/VERIFICATION.md): 47+3 distinct
Python passes, 22 actual local Nginx assertions, sanitized logs and matching hashes.
The first Nginx harness attempt lacked a temporary directory; the corrected
isolated run passes without a policy change. No unchanged contract tests rerun.

Linux/TLS/default-host/CDN policy, real RPC/provider load, multi-host quotas and
off-host alerts remain open under the central service task. The test uses local
HTTP and fake projections, not real transactions. No public website/server,
contract deployment, Anvil user-state reset or paused-monitor restart. Use main;
check Git HEAD/origin for publication. Older unrelated drafts remain separate.


## Contribution floor and NFT earnings checkpoint - 2026-10-19

The user requires $5 minimum LP increases; initial activation remains $100.
Entry and the fixed Vault budget helper enforce both, including direct Vault
calls and higher pool minima. The original-source 99% new-LP requirement and
separate gas remain. Backend preparation and new website actions agree; legacy
v7 preview events are preserved rather than resetting saved holdings.

Read [minimums](CONTRIBUTION_MINIMUMS.md), [scoped verification](../reports/topup-and-reward-review/VERIFICATION.md)
and [internal review](../reports/topup-and-reward-review/REVIEW.md). Fresh evidence:
91 Solidity passes, 32 normal compiler-object gates (Vault 19 runtime bytes spare),
74 distinct Python and 102 distinct JS cases across documented scoped runs.
No full fresh regression, independent audit or public-chain qualification.

Cards/details use NFT net earned individual+collective+royalty totals. The fee
labels and regular-weight values share one compact line below centered LP attached;
Rewards to claim is separately centered. No gross fees on NFT cards. Original
demo 24h net history is unavailable; local totals require exact snapshot identity
and all price components. Optional local history failures retain core balances;
terminal budgets/core errors remain fatal, dormant reads skip history.

Main only, preserve unrelated drafts and establish publication through Git. No
public server update, public transaction or monitor restart. Existing local
8892 contracts were not replaced: start a separate source-matched disposable
fixture to test the new binary without deleting the current session. Central
Todo, feature/evidence and operator procedures are updated together.

## Local website integration checkpoint - 2026-10-19

Read [the website local-mode guide](LOCAL_WEBSITE.md) and
[scoped verification](../reports/local-website/VERIFICATION.md). The existing website
can run at the local launcher's /app/ mount with confirmed contract ownership,
current LP, earnings, royalties and lifetime claims. Explicit confirmations cover
mint, exact approval, Entry/top-up, transfer and bounded combined claims. Failure
clears projections; identical operation IDs recover lost responses. Source assets,
public demo behavior and v7 storage remain separate.

The user accepted local integration before public deployment. Only disposable
launcher-owned Anvil accounts are used; production EIP1193 signing is still open.
No production Solidity, public transaction, server deployment or paused-monitor
restart occurred. The four frontend tasks are in progress, not production complete.
Keep main only, preserve unrelated drafts, update Todo/features/operator procedures,
and verify Git publication. Repository context is durable local memory only.

## Local browser stack continuation - 2026-10-19

The user requested that we set up and run the local test environment. Read
[the local runbook](LOCAL_TEST_STACK.md) and
[scoped verification](../reports/local-stack/VERIFICATION.md). The separate local
panel at port 8890 uses real sealed core contracts, Entry, Strategy, budgets,
funded LP/royalty ledgers, ClaimRouter and confirmed indexed API projections.
LocalDemoVenue replaces LiquidityManager/Uniswap, LocalFeed is an always-fresh
$1 mock and MockVRF has no proof. It is not a public-chain/provider qualification.
The completed journey verifies mint, activation/no retroactive income, top-up,
funding, rebalance, ownership transfer and repeated combined claims/lifetime totals.
The expanded 39-assertion Anvil journey passes, including adversarial input/replay checks;
35 focused launcher/HTTP/recovery cases pass. Strict action schemas, revision
checks, durable operation IDs, bounded workers/timeouts and atomic evidence writes
protect the local panel. Refresh recovers a lost response with the same ID;
uncertain submissions block new operations. Production sources are unchanged
and their suites were not rerun. The public website/server and paused
monitor are unchanged. Production website wallet integration remains open.
Local state and full receipts are external, disposable and not recoverable as a
chain after shutdown; restarting creates a fresh deployment. Source and metadata
are verified against reused artifacts. No private key or public funds are used.
Use main; preserve unrelated drafts and check Git for publication. Update the
central Todo, feature/evidence reference and operator manual with future changes.

## Earnings ingestion audit continuation - 2026-10-19

The earnings backend and unsigned mint/claim preparation are already published;
do not reimplement the older quoted plan. This follow-up adds a read-only
[history audit](HISTORY_AUDIT.md) comparing one configured current/predecessor
epoch window with a separately reviewed RPC. It requires all seven emitters,
exact cursor/header/log identity, confirmed ancestry and bounded work. Missing,
conflicting or unavailable data never yields a matched window. The indexer adds
one ordered block/log SQLite index; no economic replay or contract code changes.

[Scoped evidence](../reports/history-audit/VERIFICATION.md) covers 41 distinct affected
cases across new execution and exact-body reuse, including 10,000 logs/128 blocks
and protected CLI output paths. No unchanged Solidity or earnings suites rerun.
Actual independent providers, full backfills, reviewed prices, large-history/load
qualification and website integration remain open. Provider agreement and a
partial window report are not completeness/finality proofs. Follow the linked
operator procedure; no server, website, public-chain or paused-monitor change.
Use main, preserve unrelated drafts and check Git for publication. Keep creator
questions in their central section; release remains NOT APPROVED.

## Unsigned wallet preparation continuation - 2026-10-19

The saved mint/claim draft is now hardened for the current lifecycle and promoted
with [operator instructions](FRONTEND_TRANSACTIONS.md) and
[scoped evidence](../reports/wallet-preparation/VERIFICATION.md). Typed 0.05 ETH mint
and 1-32 mixed LP/royalty claims simulate at a confirmed canonical hash. Mint-only
pause and preparation block mint; eligible claims remain available. Unselected
currency faults can be isolated, while selected assets, inventory/core mismatches,
canonical locks, expiry and work budgets fail closed. A required reviewed policy
binds the read configuration and separately bounds/estimates gas; no signer or
broadcast exists. Default GET-only; explicit transaction config enables POST in
a supervised serial worker. Browser integration and live fee/RPC qualification
remain open. The 149-test affected inventory has passing evidence across two
scoped runs; the initial reorg fixture correction is recorded. All 40 Solidity
source bindings and six compiled ABIs match reusable artifacts; no contract rerun.

Use main and Git to establish publication. Preserve unrelated route/process-runner,
history-test and artwork drafts. No website/server/deployment/public transaction
or paused-monitor change. Update central Todo, features and operator manual with
future changes; release remains NOT APPROVED.

# Resume handoff - 2026-10-19

This is a continuation record, not another task list. Remaining work and acceptance
criteria live in the [central Todo](../TODO.md#task-security-chain-recovery).

## Current checkpoint

Implemented [processed earnings and today-price USD](EARNINGS_HISTORY.md).
The user chose current prices for both all-time and 24h earned source amounts.
Read [the 186-test scoped evidence](../reports/earnings-history/VERIFICATION.md)
for exact reuse/corrections; no Solidity rebuild/tests repeated. Per-NFT payouts,
conversions, fractions, deferred royalty cohorts and same-chain imports reconcile.
The current profile requires all seven emitters from creation; preserve old
indexes when backfilling. Missing prices are null, not assumed stablecoin pegs.
Next qualify actual providers/feed pins, complete ingestion/load/reorg operation
and the live frontend consumer. Keep this reporting separate from claimable and
previously-claimed fields. Main publication is established by Git; unrelated drafts
remain local. Website/server/paused monitor and public-chain state are unchanged.


The [royalty reporting profile](ROYALTY_REPORTING.md) now exposes confirmed
ETH/source balances, per-currency deferred eligibility and pinned converter enable
control. Exact conversion replay and same-chain predecessors preserve conversion
credits separately from actual lifetime LP/royalty claims. Current ETH claimable
already includes unclaimed converted amounts. Read [scoped evidence](../reports/royalty-reporting/VERIFICATION.md):
138 affected Python passes followed by 20 supplemental passes, 40 unchanged
Solidity bindings reused, ten getter ABIs and 26 added schema events verified.
The test trees exclude unrelated unpublished wallet/server/route/history-test drafts.

That reporting milestone is now followed by the processed earnings profile above.
Remaining integration work is actual price/ingestion qualification, live frontend
wallet/data behavior and actual service/route qualification.
Use the central Todo and keep operator procedures in sync. No website/server,
paused monitor, deployment or public transaction changed. Use main; Git establishes
publication. Preserve unrelated drafts and reuse unchanged contract evidence.

The read-only [replacement holder preflight](HOLDER_PREFLIGHT.md) now inventories
confirmed ownership/code, flags unresolved escrows/delegated accounts and detects
incomplete/mixed pages. Actual release/claim rehearsals remain open. See
[scoped evidence](../reports/holder-preflight/VERIFICATION.md); no Solidity changed
in this follow-up, so the royalty verification was reused without rerunning it.

The royalty conversion continuation implements guarded batches, per-currency
outage recovery and optional keeper automation. Read [the runbook](ROYALTY_SETTLEMENT.md)
and [source-bound verification](../reports/royalty-conversion/VERIFICATION.md).
The approved 1% cap excludes gas; older unapproved/not-implemented statements
below describe the earlier checkpoint. Live qualification remains open, release
NOT APPROVED, website/server/paused monitor unchanged. Use main and preserve drafts.

Historical October 19 royalty clarification (superseded by the implemented checkpoint above): [the accepted direction](ROYALTY_SETTLEMENT.md)
is ETH pricing and verified ETH/WETH royalty receipts first. If USDC/USDG royalty
settlement cannot be excluded, implement guarded automatic ETH conversion. OpenSea
documents Robinhood ETH/USDG pricing selection; it does not establish a universal
currency ban or qualify actual collection settlement. Buyer checkout assets may
differ from receiver settlement. No royalty conversion or failure-isolation code
has changed. Delayed per-currency eligibility was discussed, not approved. The
central Todo, operator procedure and feature boundary distinguish this planned work
from current direct per-currency claims. Documentation-only verification does not
require repeating unchanged contract tests. No marketplace/service action occurred.

The October 19 operator-controls continuation adds dependency-independent,
disable-only `PoolRegistry.disablePool` and governed `NFT.setMintPaused`.
Pending original reveals and existing economic rights retain their own guards;
mint callbacks cannot commit after setting the mint pause. Reopen pools through
full validation. The confirmed API reports mint-only pause separately.
Read [current evidence](../reports/operator-controls/VERIFICATION.md) and the
[updated operator manual](OPERATOR_MANUAL.md). Prior full/static evidence retains
its original scope; no website/server/deployment/monitor action is included.
Unrelated unpublished drafts remain preserved. Use main and Git for publication.


The October 19 continuation adds [the operator manual](OPERATOR_MANUAL.md) with
mandatory same-change maintenance in repository instructions/Todo workflow, API
request-wide work limits and supervised workers, plus confirmed mint readiness.
Read [scoped verification](../reports/api-work-limits/VERIFICATION.md) for results
and source bindings. Solidity is unchanged; do not repeat unchanged suites.
Randomness policy is qualified/funded service plus draining original requests
before replacement; no reroll/carry. Keep the 3% cap per operation only. Production,
provider/escrow/hosting qualification remain open; main publication is established
by Git. Website/server/paused monitor and unrelated drafts remain unchanged.


The [review of October 18 changes](../reports/daily-security-20261018/REVIEW.md)
was completed October 19 against 13 commits through `485a089`. No production
code changed. Existing build/source hashes matched; unchanged suites were not
rerun. A new synthetic expiry check reproduced continued API work before safe
rejection. Request-wide deadlines and RPC-work limits belong to host-services;
the unfulfilled-VRF/handoff dependency belongs to fair-draw and canonical recovery.
Successor escrow compatibility, immediate governance trust and cumulative
maintenance costs remain recorded risks. The central Todo contains acceptance
criteria. Release stays NOT APPROVED; preserved local drafts remain unpublished.

Governance now has **no mandatory waiting period**, including the additional LP
migration delay. The user explicitly superseded the earlier delayed policy and
proposed route-only exception. Read [authority semantics](GOVERNANCE.md) and
[scoped evidence](../reports/immediate-governance/VERIFICATION.md). Target safety
checks, sealing and finality remain; there is no advance warning window. Update
production authority/runtime records and operating procedures before approval.
No deployment or website/server change occurred; monitor stays paused. The
randomness provider decision remains open and unchanged. Use Git for publication.


The [read-only route campaign](INTEGRATION_CAMPAIGN.md) now records a successful
paced USDG/ETH feed and four-route conversion observation. This is not complete
activation, a public transaction or a new fork/test pass. See [its scope](../reports/activation-route-observation/VERIFICATION.md).
Actual PoPL deployment, qualified services and operator-run transactions remain
open; the private key was not accessed. Earlier HTTP failures remain preserved.

The [local $1 rehearsal](ONE_DOLLAR_REHEARSAL.md) is separately implemented and
verified (10 Solidity / four Python). Production $100 activation / 0.05 ETH mint rules
are unchanged; no public transaction or website/API deployment was made. Read
[its evidence](../reports/one-dollar-rehearsal/VERIFICATION.md) for the original
fixture failure and successful corrected run. Real defects found in later tests
must be fixed in production with targeted evidence; the $1 override stays isolated.

The latest [range-policy path](RANGE_POLICY_UPDATES.md) is implemented. After a
governance-approved range update, ordinary keeper rebalance becomes eligible once cooldown
passes even at a flat price. It compares current LP ticks at the recorded center,
preserves existing Vault guards and clears the mismatch on success. No forced
execution role/state was added. Backend context now reports the pending range
cause and checks both triggers. Read [current evidence](../reports/range-policy/VERIFICATION.md).
Only Strategy production Solidity changed; broad unchanged suites were not
repeated. Vault still has 19 runtime bytes of headroom. Runtime manifests, real
range/MEV/gas qualification, services and independent review remain open. The
website/server and paused monitoring are unchanged. Check Git for publication.

The [dynamic-liquidity review](DYNAMIC_LIQUIDITY.md) adds the user-approved
out-of-range warning with honest eligibility timing, the 3% aggregate ordinary
rebalance budget, guarded current NFT valuation and current-LP API context.
[Verification](../reports/dynamic-liquidity/VERIFICATION.md) binds affected
checks to these changes; the earlier full handoff regression below is historical
for its source snapshot and must not be presented as a new full regression.
Vault has 19 runtime bytes of headroom. Use the central Todo for live range/
strategy qualification, next-check telemetry, wallet integration and audit.
No website/server or monitoring service changes are included.

Complete activation/top-up preparation is implemented separately from the old
mint/claim and conversion-only drafts. Read [the integration contract](ACTIVATION_PREPARATION.md)
and [scoped evidence](../reports/activation-preparation/VERIFICATION.md): 38 focused
checks passed on the exact publication snapshot; 63 ABI getter layouts and local
Anvil trace/gas/budget mechanics were verified using source-matched artifacts.
The backend returns the current NFT on-chain marked value separately from the
new marginal LP contribution, an exact unsigned Entry call and separate gas.
Insufficient approval returns only an approval/reset step and requires re-quoting
after confirmation. Production manifests/routes/feeds/RPC fee semantics and the
wallet/hosted-service integration remain open; no website/server changes occurred.
Source/evidence/docs are published together on main; use Git for exact identity.


The latest [claim-lineage checkpoint](FRONTEND_LINEAGE.md) extends the schema-2
lifecycle API with complete explicitly configured same-chain predecessor replay.
It verifies both handoff directions, canonical retirement/activation receipts and
terminal source commitments, then includes all prior LP/royalty claims and owners.
Old indexes may stop at retirement; historical-only assets remain visible.
Missing configuration stays unavailable; invalid lineage fails closed.
[Scoped verification](../reports/frontend-lineage/VERIFICATION.md): 91 passing
API/lifecycle/history cases on the exact publication snapshot, plus two getter and
two event layouts checked against source-matching existing compiler artifacts.
Production Solidity is unchanged and its tests were not repeated. Live archive
services, independent peer review and website integration remain open.
The optional wallet POST drafts remain outside this scoped publication.

The earlier handoff's saved bridge-fixture fixes and final cold-gas checks were
verified. That regression passed **582 cases with zero failures and two intentional fork setup
skips** across 49 suites. The unchanged 34-case focused handoff run is reused after
checking all compiled dependencies, giving 616 successful cases in combined scope.
These are separate source-matched runs, not one new 616-case execution.

This checkpoint accompanies the scoped canonical-handoff publication on **main**.
Use Git HEAD/origin/main to verify the exact publication; the earlier
`79f205a7933107f61f26892109f14ee52821700e` checkpoint and its uncommitted wording
are historical. Unrelated wallet/API, quote/process-runner and artwork drafts
remain outside this publication. Do not use `git add .` to include them later.
No contract has been deployed and no website/server service was changed.
Release remains **NOT APPROVED**.

## Implementation and accepted trust

Read [the implemented handoff boundary](CANONICAL_HANDOFF.md). It supports only
same-chain replacement: all mints revealed, buckets Parked/None, no active plans
or historic legacy bridge activity. Freeze captures all six receipt cutoffs
atomically; phase 8 settles domains once in strict order before export. Complete
state/import and exact classified backing precede atomic source retirement and
single-successor activation. Restored abort and one-hop late forwarding exist.

The user accepts different reviewed replacement code approved through timelocked
governance, including the risk of a malicious approved successor diverting LP.
Do not impose identical-code admission. Future-chain activation still requires
verified source finality with no multisig/timeout override. Authenticated channel
closure, new lineage/message semantics and exact cross-chain transport/backing
remain pre-seal work. Sealed code cannot acquire absent capabilities later;
post-halt recovery is deferred.

## Evidence to reuse

The [verification record](../reports/canonical-handoff/VERIFICATION.md) separates:

- The new 582-case regression, including repaired bridge suites and ten cold-gas
  cases, with unchanged sources and explicit fork skips.
- The reused 34 focused passes, 30 normal object gates/39 production bindings,
  141 configuration checks and 88 keeper lifecycle checks.
- The current-source internal review of 374 Slither findings, coverage and ten
  mutation rejections. Internal review does not replace an independent audit.
- 123 additional successful keeper cases; one Unix permissions case awaits
  Ubuntu. The venue fixture and local deployment script compile/type-check,
  without implying deployment or operating rehearsal.

[Reuse verification](../reports/canonical-handoff/reuse-verification.json) binds
prior evidence to unchanged source dependencies. Do not repeat checks solely to
increase counts. Vault has 33 runtime bytes of headroom and Migration 58;
constructor arguments still need deployment allowance.

## Next work boundaries

Follow the owning tasks in the central Todo for exact-commit Ubuntu CI, keeper
operating qualification, live API/indexer and same-chain history integration,
marketplace/contract-owner cutover, qualified live services and independent audit.
The cross-chain requirements remain implementation work, not completed by the
same-chain tests. The initial release still requires migration disabled.

The chat health monitor was **paused at the user's request on 2026-10-17**.
Do not restart it without authorization. That action did not stop the isolated
server service; the period after pause has no chat-monitor observation coverage.

## Artifact and publication discipline

External artifacts and runner scripts remain under:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/handoff-20261017`.

Current broad receipt: `regression/attempt2/receipt.json`; reused focused receipt:
`focused/attempt5/receipt.json`; normal production build: fresh attempt9 and
successful cached attempt10. Fresh static analysis is in
`static-analysis-settlement/`. Continuation tooling is in `resume-20261018/`.
Original failed/stale diagnostic attempts remain preserved and are not merged
into passing results. Raw large logs stay external with hashes and full compact
case outcomes in the repository. Do not overwrite existing attempt directories.

Do not rerun `publish_local_evidence.py` blindly: its historical review assumption
is obsolete. Preserve strict reentrancy write-bundle comparison metadata when
updating the review. Keep compiler/profile and tested source unchanged during a
verification run. Current CI allows 60 minutes for local checks and includes
canonical/preparation keeper tests; that timeout does not relax gas assertions.

For every change, update `docs/project-todo.json`, regenerate `TODO.md`, run the
sync tool with `--check`, and reconcile affected evidence/release references.
This is durable repository context, not a claim of global personal memory.

Latest user clarification: holder LP rewards must also settle in ETH. The
[audit](../reports/topup-and-reward-review/ETH_PAYOUT_AUDIT.md) finds LP conversion
and unwrap absent; royalty-only conversion is not sufficient. The local read-only
claim trace confirms source ERC20 plus native royalties and leaves claims intact.
Track implementation before sealing; no new LP conversion-loss policy is assumed.
The current local input balance was replenished without restarting the chain.
Palette names now use their own text colors in both website modes, without pills.

Contribution UI follow-up: four visible input choices (ZZZ/USDG/USDC/ETH), WETH internal only, dedicated contribution dialog and confirmed per-NFT evolution refresh. See [named local rehearsal](LOCAL_TEST_STACK.md#named-input-local-rehearsal). No production authority/procedure change; public routes, ETH-only LP settlement and hosting remain open.
