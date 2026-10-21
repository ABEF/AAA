## Real local API rehearsal and wallet totals - 2026-10-22

Publication: backend `f068f9f` and website `777fd05` are pushed on main. The
static server serves `777fd05`; all 5,598 checksums and 50 scoped public checks
passed. Public DEPLOYMENT remains null. See [receipt](reports/api-chain-rehearsal/PUBLICATION.md).

The reviewed API coordinator now has actual local-chain evidence: mint, native
activation, exact USDC approval, $5 growth and a combined ETH claim. A deliberately
interrupted post-claim API read recovered the same confirmed hash with one send.
Wallet-wide LP and funded ETH totals use bounded 16-NFT chunks at one confirmed
block and complete inventory; missing/partial/mismatched data never becomes zero
or a partial total. Historical earnings remain per NFT; collection-wide aggregation
and portfolio-wide historical earnings are still separate open work.

Read [runbook](docs/LOCAL_API_REHEARSAL.md) and
[scoped evidence](reports/api-chain-rehearsal/VERIFICATION.md). APIs, core contracts,
receipts and transfers are real on isolated Anvil; venue math, token markets,
feeds and VRF are explicit local substitutes. The signing test uses an EIP-1193
RPC shim, not actual MetaMask/Rabby acceptance. Shared BrowserWallet/BrowserClient
remain byte-identical and local-only; public DEPLOYMENT remains null.

Separate fixture: port8902, external api-chain-rehearsal/runs; read running.json
before process control. Prior8900 processes were already absent; its saved files
were untouched. Monitor remains paused; the deferred load campaign was not run.
No production Solidity change or public transaction. Main only; preserve unrelated
drafts and keep the sole Todo, feature evidence, operator guidance and memories aligned.
Publication is recorded separately; inspect Git and the publication receipt.

## Local API wallet coordinator - 2026-10-21

Publication: website code `d786286` and contract evidence `59739ea` are on main;
the static server serves `d786286`. All 5,598 server checksums and 50 scoped public,
host/redirect/privacy checks passed. Public DEPLOYMENT remains null. See
[publication evidence](reports/deployment-local-wallet/PUBLICATION.md).

The user explicitly chose **Keep the signer restricted to local Anvil** after
automatic approval review rejected the broader signer proposal. That proposal
was not executed. Shared BrowserWallet/BrowserClient remain byte-identical;
never generalize public signing from this work or treat it as release approval.

The reviewed API profile now has a local-only coordinator for mint, exact approval,
activation/growth and ETH claims. It requires environment rehearsal, chain 31337,
HTTP literal-loopback page and RPC. Nonlocal profiles remain unsigned. Approval
continues to a fresh complete LP review, never an automatic send or second approval.
Recovery retains the original journal/hash. Confirmed receipts with a lagging API
are labeled confirmed, with balances catching up. LP/artwork require the matching
Entry event and a confirmed active NFT position; claims do not mark artwork pending.

Read [operator procedure](docs/DEPLOYMENT_WEBSITE.md#local-api-wallet-rehearsal)
and [scoped evidence](reports/deployment-local-wallet/VERIFICATION.md): 84 affected
cases (57 API/session plus 27 coordinator) and nine headless browser scenarios.
The wallet/RPC are mocked; no actual extension or chain transaction was performed.
All 13 prior shared signer/backend bindings remain unchanged. Existing Anvil/8900,
wallet state, paused monitoring and the deferred load campaign remain untouched.
Public DEPLOYMENT is null. Production integration/qualification and independent
audit remain open. Use main; preserve unrelated drafts; maintain the one Todo,
features, operator guidance and both memories. Check Git/publication receipts.

## Reviewed website API profile - 2026-10-21

Publication: website code `757a8de` and contract docs `1dc05d3` are pushed on
main; the static server serves `757a8de`. All 5,597 server checksums and 41 public
assets, four host/redirect and four private-path checks passed. The public
configuration is null and financial actions remain simulated. See
[publication receipt](reports/deployment-adapter/PUBLICATION.md).

The separate website now has a build-configured, default-disabled read and unsigned-
review profile for the existing APIs. Ordinary authorized accounts, eight-card
holdings pages, confirmed LP/ETH rewards, matching-block earnings and typed
mint/approval/Entry/claim reviews are implemented. Token-unit quotes target $100
activation (minimal raw-unit round-up) and at least $5 growth, with a 99% marginal
LP floor and separate gas. No signing or broadcast method exists in this profile.

Read [operator setup](docs/DEPLOYMENT_WEBSITE.md) and
[scoped evidence](reports/deployment-adapter/VERIFICATION.md): 57 focused cases,
eleven actual Python API response fixtures and eight headless browser scenarios.
Dependencies/wallets are mocked; this is not live provider/extension acceptance.
All thirteen earlier chain-reader bindings still match; unchanged signer/contract
suites and the deferred load campaign were not rerun. Build: 5,597 static files.

Automatic approval review rejected expanding the shared signer beyond local mode;
that proposal was not executed. Preserve its chain-31337 restriction and pending
journals. Public signing/qualified deployment config, routes, feeds, hosting,
full collection aggregation and independent release approval remain open. The
shipped DEPLOYMENT is null, so the public website stays simulated. Existing
Anvil/8900/session/NFT state and paused monitoring were not changed. Use main,
keep the single Todo/evidence/operator procedures aligned, preserve unrelated
drafts, and check Git/publication receipts rather than inferring publication.

## Publication checkpoint - 2026-10-20

The verified wallet implementation is published on main: contract/backend
df8a98a and website f060d66. The static Ubuntu site now serves website f060d66;
full server checksums and scoped public HTTPS/redirect/privacy checks passed.
See [publication evidence](reports/browser-wallet/PUBLICATION.md).
The public site remains simulated; this is not a public contract/API deployment
or release approval. Local port 8900, Anvil and saved wallet/NFT state were not
reset. Thirteen source bindings still match the prior focused test evidence;
unchanged suites and the deferred load campaign were not rerun.

Actual MetaMask acceptance of the latest confirmation fix, production pins,
routes, feeds, services and independent audit remain open. Keep the single Todo
ledger and operator procedures authoritative. Preserve older unrelated local
drafts; they were not included in this publication. Monitoring remains paused.

## Independent chain confirmation - 2026-10-20

Shared wallet flows now read balances, simulation and confirmation through the
reviewed deployment RPC instead of extension-formatted transaction responses.
Wallet permissions/signing stay in the selected extension. Node and wallet chain/
genesis checks, exact approvals/calldata/fees and saved-hash recovery remain.
Legacy missing chainId resolves only through replay-protected EIP-155 v; typed
missing IDs fail closed. Approval never changes LP or artwork; Entry receipt plus
confirmed on-chain position remains required for activation/growth presentation.

[Evidence](reports/browser-wallet/CHAIN_READER.md): 232 distinct website and 43 backend cases;
read-only recovery of the actual successful nonce-36 mint, exact-node CSP/CORS,
syntax/build and preservation of all 13 NFTs/LP/session after web-only restart.
Anvil 10988 was not reset. No signing/public transaction/server deployment or
paused-monitor change. Actual extension acceptance and production pins/routes/
RPC/fee qualification remain open; public signing is not enabled. Use main,
preserve unrelated drafts and check Git for publication. Keep Todo, feature
reference, operator guidance and both repo memories aligned.

## Canonical dynamic-fee receipt recovery - 2026-10-20

The user's mint 0xa7f91e…ac3891 succeeded at block 351. Anvil's derived fee fields
reported 1,000,000,014 wei/gas although signed cap and actual balance charge were
1,000,000,007. Shared signing and independent observation now derive EIP-1559
execution price from signed caps and canonical block base fee; original gas/unit/
paid-cost limits remain. Raw reported fee is retained separately. Deterministic
verification failures surface immediately with their specific reason.
[Evidence](reports/browser-wallet/DYNAMIC_FEE_RECEIPTS.md): 142 signer/client and
40 observer tests, actual read-only mint receipt/balance replay, syntax/build pass.
Only local web worker restarted; session, 12 NFTs/LP and Anvil preserved. No new
holder/operator transaction or public deployment. Actual extension recovery retest
and production fee/profile qualification remain open.

## Mint loading presentation - 2026-10-20

Mint button loading now follows the actual activity instead of a generic busy
flag. Initial/refresh reads, connection, mint preparation, wallet confirmation,
receipt waiting and confirmed-state reconciliation have separate labels. Claims,
approvals and LP actions cannot label the button as a mint in progress. Existing
readiness/pending guards remain. See [evidence](reports/browser-wallet/MINT_LOADING.md):
44 affected UI/lifecycle/contribution cases, syntax/build and served-source checks
pass. No signer, contract, backend, transaction, service or public deployment change.

## Numeric wallet nonce compatibility - 2026-10-20

The user supplied the exact failure: eth_getTransactionCount returned a number.
The shared website signer now accepts only exactly representable nonnegative JS
integers at its RPC response boundary, converting directly to BigInt. Hex responses
remain supported; prepared transactions/journals remain canonical hex. This has
no local-chain/address exception and keeps exact nonce, gas and receipt guards.
139 affected signer/client cases pass after reproducing the original failure.
See [evidence](reports/browser-wallet/NUMERIC_NONCE.md). Actual MetaMask retest is
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

[Scoped lifecycle review](reports/browser-wallet/LIFECYCLE_REVIEW.md): 203 affected
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

## Wallet RPC quantity diagnostics - 2026-10-20

The user reported Invalid transaction quantity after the mint review. At the
observed local block 319, Wallet A's next nonce was 0x23, both latest mint drafts
used that nonce with no observed hash, and no pending transaction was present.
The supplied text was the app review, not a receipt. Actual MetaMask failure
cause remains unconfirmed; do not claim a successful mint or a proven root cause.

Wallet-returned numeric fields accept bounded unsigned hexadecimal padding;
unsigned prepared transactions and journals remain strictly canonical. Invalid
responses identify their field without logging raw provider data. Preflight
failure says nothing was submitted by this operation; uncertain submissions
retain recovery. No automatic retry sends. 123 affected signer/client tests and
5,593-file build pass; see reports/browser-wallet/RPC_QUANTITIES.md.
No backend/contract, public transaction, service reset or deployment change.
Keep main, Todo/evidence/operator notes and both memories consistent.

## Fresh MetaMask button selection - 2026-10-20

The user still reproduced the previous-account issue. Explicit reconnect no
longer prefers a remembered sender over fresh provider accounts. The MetaMask
picker button always requests fresh eth_accounts permission on that user gesture;
refresh never prompts. If several accounts are returned, the user must select
one in the website instead of guessing which popup account was intended.
Unfinished selection blocks account restoration and clears only remembered
connection selection, not pending transaction journals. Exact chain/genesis,
sender authorization and pending recovery remain enforced.

90 affected client/UI-state cases and the 5,593-file build pass. See
reports/browser-wallet/FRESH_SELECTION.md. Actual Chrome/MetaMask acceptance is
still open: mock-provider tests do not verify the extension popup. No backend,
contract, transaction, chain reset, service restart or public deployment.
Use main; preserve unrelated drafts and keep operator/Todo/evidence consistent.

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

## MetaMask connection and approval recovery - 2026-10-20

Connection diagnostics now distinguish site-authorized account, network ID and
exact local RPC/genesis. Reconnecting uses fresh public reads; importing/selecting
Test A in MetaMask alone does not authorize it for the site. Failed verification
never marks the connection ready. Gas-limit padding is tolerated only within hard
policy and canonical paid-gas/price/cost limits from the unchanged original review.
Economic fields, nonce and submitted gas-price ceiling remain exact. Never clear
an unresolved journal or repeat a confirmed approval.

31 Python, 41 connection-adapter and 44 signer cases pass in scoped runs.
The user's existing MetaMask approval fbcd791c...a0c86e7 was independently verified
and recorded without resubmission; this is not complete extension-flow acceptance.
Only web process 10672 was replaced by 25784; Anvil10988/RPC61752, session and all
six NFT owners/LP/activation/claimable balances were preserved. Port8900 remains
the local fixture. Read running.json before process control; never reset Anvil
to resolve a page error. The external fixed-fixture recovery helper never owns
or terminates that chain. See the contract report
reports/browser-wallet/CONNECTION_RECOVERY.md and docs/BROWSER_WALLET.md.

Production must request Robinhood Chain using independently reviewed deployment
configuration; current signing remains local31337 only. Public server/signing,
unchanged Solidity and paused monitoring are untouched. Main only, preserve
unrelated drafts; central Todo, features, operator procedures and both memories
are maintained. Production remains NOT APPROVED.

## Browser-wallet local integration - 2026-10-20

Read [the browser-wallet procedure](docs/BROWSER_WALLET.md) and
[scoped evidence](reports/browser-wallet/VERIFICATION.md). The explicit local
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
[manual acceptance](reports/local-wallet-concurrency/MANUAL_ACCEPTANCE.md). This is
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

## LP holder ETH settlement checkpoint - 2026-10-20

The user approved a 1% maximum LP reward conversion loss, gas separate. Read
[the operator procedure](docs/LP_ETH_SETTLEMENT.md) and
[scoped verification](reports/lp-eth-settlement/VERIFICATION.md). A dedicated
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

## API client admission checkpoint - 2026-10-20

Both read/unsigned-preparation CLI services now install bounded per-client
concurrency, separate read/preparation budgets and a finite identity table.
Explicit proxy mode requires a local peer, overwritten validated client IP and
exact HTTPS Origin for POST; arbitrary forwarding headers never choose a budget.
Read [operator procedures](docs/API_INGRESS.md) and [scoped evidence](reports/api-admission/VERIFICATION.md).
Fifty distinct affected Python cases pass across 47+3 runs; 22 actual local Nginx
assertions and sanitized-log verification pass. No unchanged contract suites rerun.
The proxy rehearsal used fake data and HTTP on Windows; Linux/TLS/provider/NAT/
distributed quotas and alerts remain hosting gates. No website/server, public
transaction or paused-monitor change. Use main, preserve unrelated drafts and
check Git for publication. Keep Todo/features/operator procedures consistent.

## Approved Twin circuit routes artwork - 2026-10-20

The user explicitly chose Vertical ribs (not Orbital rings) for replacement by
two static groups of four continuous circuit traces. Display name: Twin circuit
routes. Preserve stable ID ribs / numeric slot 3, image paths, the fixed 1,000
inventory entries, rarity/palette assignments and economics. All 696 matching
SVGs/reference JSONs are regenerated; the original embedded textures and 2,088
other pattern states are byte-identical. The on-chain metadata candidate changes
only its display label, not its URI path or economic logic. Read
[scoped evidence](reports/twin-circuits/VERIFICATION.md). Refresh the artwork upload
bundle before initial immutable publication; older bundles are historical.
Use main, preserve unrelated drafts, and check Git/server receipts for publication.
No public contract transaction or paused-monitor restart is part of this change.

## Local website integration checkpoint - 2026-10-19

Read [the website local-mode guide](docs/LOCAL_WEBSITE.md) and
[scoped verification](reports/local-website/VERIFICATION.md). The existing website
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
[the local runbook](docs/LOCAL_TEST_STACK.md) and
[scoped verification](reports/local-stack/VERIFICATION.md). The separate local
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
[history audit](docs/HISTORY_AUDIT.md) comparing one configured current/predecessor
epoch window with a separately reviewed RPC. It requires all seven emitters,
exact cursor/header/log identity, confirmed ancestry and bounded work. Missing,
conflicting or unavailable data never yields a matched window. The indexer adds
one ordered block/log SQLite index; no economic replay or contract code changes.

[Scoped evidence](reports/history-audit/VERIFICATION.md) covers 41 distinct affected
cases across new execution and exact-body reuse, including 10,000 logs/128 blocks
and protected CLI output paths. No unchanged Solidity or earnings suites rerun.
Actual independent providers, full backfills, reviewed prices, large-history/load
qualification and website integration remain open. Provider agreement and a
partial window report are not completeness/finality proofs. Follow the linked
operator procedure; no server, website, public-chain or paused-monitor change.
Use main, preserve unrelated drafts and check Git for publication. Keep creator
questions in their central section; release remains NOT APPROVED.

## Creator coordination continuation - 2026-10-19

The user requested a dedicated **Creator tasks / ZZZ team** section in the
[central Todo](TODO.md#creator-tasks--zzz-team). Keep every question requiring
the token/pool team's answer there: fee basis/percentage, active-liquidity
measurement, payment delivery/reconciliation, independent ZZZ pricing,
token/pool controls, input liquidity and future-market/incident continuity.
The existing `creator-terms` task ID is preserved; technical qualification stays
under its linked Contracts/Backend tasks. Record dated answers and evidence,
never infer a payment agreement, provider choice or permission from silence.

The ZZZ-feed question is deferred to that section, not answered. No production
price source or complete ETH-to-LP qualification is established. Current selected
pool adapter support is distinguished from historical market observations.
This is documentation/coordination only: no contract, API, website, server,
public transaction or paused-monitor change; release remains NOT APPROVED.
Use main, preserve unrelated drafts and verify Git for publication. Update this
creator section whenever later development raises a team-dependent decision.

## Unsigned wallet preparation continuation - 2026-10-19

The saved mint/claim draft is now hardened for the current lifecycle and promoted
with [operator instructions](docs/FRONTEND_TRANSACTIONS.md) and
[scoped evidence](reports/wallet-preparation/VERIFICATION.md). Typed 0.05 ETH mint
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

## Confirmed earnings continuation - 2026-10-19

The user selected **current (today's) prices** for all-time and 24-hour earnings.
Read [the earnings guide](docs/EARNINGS_HISTORY.md) and
[scoped verification](reports/earnings-history/VERIFICATION.md). Optional read-only
collection/NFT endpoints replay actual processed allocations and royalty receipts,
including complete configured same-chain predecessors. Shares, equal collective
membership, rarity cohorts and carried fractions are separate. Transfers, claims,
conversion credits and imported balances are not new earnings. Unprocessed funds
are excluded. Missing prices produce null USD, never an assumed stablecoin peg.

The 186-test affected inventory has passing current-body evidence across three
scoped runs, with fixture/runner corrections explicitly recorded. Forty unchanged
Solidity source/build bindings and compiled ABIs were reused; no contract rerun.
Live feeds, complete ingestion/load rehearsals and frontend integration remain
open. Release NOT APPROVED. Use main; check Git for publication. Preserve unrelated
drafts. No website/server, paused monitor or public-chain changes. Update the
central Todo, feature/evidence reference and operator manual with future changes.

## Royalty reporting continuation - 2026-10-19

The optional current-ledger API profile reports per-currency royalty eligibility,
ETH/source balances and converter enable control. Currency view/runtime failures
are null/unavailable, never zero; strict core/lifecycle/history/snapshot and work
limits remain. Complete raw history separates conversion credits from actual
claims, including pinned same-chain predecessors and historical assets. Read
[the profile/runbook](docs/ROYALTY_REPORTING.md) and
[scoped evidence](reports/royalty-reporting/VERIFICATION.md).

Evidence: 138 affected Python cases, then 20 supplemental cases (three new edge
cases plus 17 request-limit cases), no failures/skips. The 17 initial new test
bodies and production backend code were unchanged in the supplemental run.
All 40 Solidity source bindings match the prior royalty build; ten new getter
ABIs and 26 added event schemas match reusable compiler artifacts. No unchanged
Solidity suites/build were rerun. This is internal scoped verification only.

Keep gross earned 24h/all-time USD history, website wallet/data integration and
production service qualification open. No website/server/monitor, deployment or
public-transaction change occurred. Use main and exact Git publication state;
preserve the unrelated wallet/server/history-test/route/artwork drafts. Maintain
the central Todo, feature reference and operator manual together.

## Replacement NFT holder preflight - 2026-10-19

Read [the holder inventory and cutover procedure](docs/HOLDER_PREFLIGHT.md) and
[scoped evidence](reports/holder-preflight/VERIFICATION.md). The read-only tool
inventories up to 1,000 NFT owners at an explicit confirmed canonical block,
flags contract/delegated owners, rejects mixed/duplicate/incomplete coverage and
never authorizes migration. Resolve exact replacement release/claim compatibility
before freeze; rescan after freeze and recheck before commit. Incompatible escrow
after freeze requires the supported fully funded abort before holder withdrawal;
no owner rewrite or retirement override. Actual marketplace/escrow qualification
remains open. Royalty conversion/outage work is published in 74c5f3e; no Solidity
changed in this inventory follow-up. Main only, preserve drafts; website/server,
public transactions and paused monitoring remain unchanged. Check Git for publication.

## Royalty batch conversion and outage recovery - 2026-10-19

The user approved automated batch ETH conversion, a maximum 1% execution loss
with gas separate, and optional-currency failure isolation. This supersedes earlier
notes saying these decisions were unapproved. Read [the runbook](docs/ROYALTY_SETTLEMENT.md)
and [scoped evidence](reports/royalty-conversion/VERIFICATION.md).

RoyaltyRewards checkpoints earned source balances for 1-32 sorted NFT IDs, converts
once through a separately deployed pre-seal-bound RoyaltyConverter, and credits the
same NFTs in ETH. Native receipt indices never redistribute conversion output.
Original source fractions, dust, quarantines and direct-currency claims persist;
conversion is not a payout or lifetime claim. Fixed helper, reviewed mutable route/
wrapper policies, exact deltas, 99% oracle floor, stronger caller minimum and deadline.
Keeper conversion is opt-in, shares serial nonce/pending/gas recovery, and uses
confirmed hash reads with fair bounded scanning. It is not deployed on the server.

Unreachable optional assets retain their older eligible cohort while activation
and healthy-currency royalties continue. On recovery, unseen receipts (including
during the outage) go to incumbents before waiting NFTs join future receipts.
No retroactive catch-up. Canonical export flattens join-index baselines; exact
unreadable backing can still block handoff. Immediate governance and all existing
LP economics remain unchanged. No website, server, public transaction or monitor
restart. Main only; preserve unrelated drafts and check Git for publication.

## ETH-first marketplace royalties - 2026-10-19

Read [royalty settlement](docs/ROYALTY_SETTLEMENT.md) and its
[central task](TODO.md#task-royalty-eth-settlement). The user accepted ETH pricing
with native ETH/verified Robinhood WETH as the initial royalty scope. If USDC/USDG
royalty settlement cannot be excluded on supported marketplace flows, implement
guarded automatic conversion to ETH. Activation input choices are separate.
Rarity/multiplier is fixed at reveal; activation enables eligibility without an
additional royalty payment or user registration. OpenSea documents an ETH/USDG
pricing choice, not a proven universal currency ban. Inspect actual settlement,
including offers and cross-chain checkout, rather than buyer input currency.

This is a documented direction, not implemented conversion or outage isolation.
The current ledger claims each admitted currency and synchronizes all admitted
assets during activation. Native ETH has no external token balance read; WETH
still has wrapper risks. Preserve pre-activation receipts and funded liabilities.
Per-currency delayed eligibility was discussed but NOT approved. Do not silently
adopt it or distribute older receipts using membership at later conversion time.
No source, marketplace, website/server, monitor or public transaction change is
included. Main only; preserve unrelated drafts and use Git for publication status.

## Operator procedures and maintenance - 2026-10-19

## Independent operator controls - 2026-10-19

The current candidate adds governed `PoolRegistry.disablePool(poolId,stopDeposits,
stopOperations)` (only clears existing flags, no token/price/venue reads) and
`NFT.setMintPaused(bool)` (new mints only; trailing callback guard). Full
configure/configureNative validation is still required to reopen pools. Pending
original reveal, existing activation, transfers, claims and LP work retain their
independent guards. Same immediate governance and preparation/canonical locks;
no new keeper/guardian authority, delay, reroll or provider substitution.
The read API exposes the mint switch separately. Successor mint-pause state is
reviewed operational configuration, not imported economic rights.

Read [current verification](reports/operator-controls/VERIFICATION.md) and the
[updated manual](docs/OPERATOR_MANUAL.md). Central Todo/features/release records
are reconciled; release remains NOT APPROVED. Use Git to establish publication.
No website/server/public transaction/deployment or monitor restart is included.
Preserve unrelated local drafts; main only. Historical source-bound evidence is
not a fresh full regression of these changes.


Read [the operator manual](docs/OPERATOR_MANUAL.md) before changing management
behavior. The user requires it to stay complete: every operator-facing function,
permission, parameter/default, lifecycle, service command, failure or recovery
change must update its applicable procedure in the same change, or explicitly
record why no operator procedure changes. Include authority, exact call/config,
preconditions, verification, stop/restart, rollback and irreversible limits.
Reconcile central Todo and feature/evidence documentation; never create a parallel
status checklist in the manual. Validate links and exact selectors/semantics.

The user selected reliable qualified/funded randomness plus stopping new minting
and draining original requests before whole-collection replacement. Retain the
fully-revealed handoff gate; no pending-request carry, reroll or admin-selected
traits. Unfulfilled VRF can still block replacement, not ordinary LP pool moves.
Keep only the existing 3% per-operation maintenance cap; no cumulative breaker.
Immediate governance remains accepted. Service/provider qualification and escrow
compatibility remain open. The manual distinguishes configure/pause/park/resume
from immutable implementations and unsupported future-chain recovery.

Request-wide API budgets, supervised read-only HTTP workers and a confirmed
mint-readiness endpoint are added in this workstream. See current scoped evidence
in reports/api-work-limits/VERIFICATION.md; these are not live hosting/VRF approval.
No Solidity, website, server, signer or paused-monitor change. Preserve unrelated
local drafts; use main and verify Git for publication.

## Review of October 18 changes - completed 2026-10-19

Read [the daily security review](reports/daily-security-20261018/REVIEW.md).
Reviewed 13 published commits from 79f205a through 485a089 plus a separate local
draft inspection. No new unauthorized principal withdrawal, hidden recipient or
reproducible double claim was identified; this is not a no-vulnerability guarantee.
Production remains NOT APPROVED. Immediate governance trust is accepted and must
not be silently replaced with a timelock. An unfulfilled ordered VRF request also
blocks whole-collection handoff; the fully-revealed-only requirement remains.
A new synthetic-clock reproduction observed 134 RPC calls including two traces
after expiry before safe rejection; no unsigned draft was returned. Request-wide
monotonic deadline/cancellation and work budgets are required before hosting.
Escrow/successor compatibility and cumulative maintenance losses remain risks.
All findings are linked to owning central Todo tasks. Existing 78 build/source
bindings, including 39 production sources, matched; unchanged test suites/static
analysis were not rerun. No production code, service, website, key, transaction
or monitor change occurred. Preserve unpublished drafts; check Git for publication.

## Immediate governance decision - 2026-10-18

Verification: 228 distinct affected Solidity passes (177 retained exact-bound
passes plus 51 corrected-fixture passes), 142 configuration passes, 30 normal
size gates / 39 production bindings, and 378 internally reviewed Slither findings.
See [current evidence](reports/immediate-governance/VERIFICATION.md). Not a full
new regression, live qualification or independent audit; release NOT APPROVED.

The user explicitly requested NO governance timelock at any point, superseding
both the old two-day template and the briefly proposed narrow fast-route role.
Read [immediate governance](docs/GOVERNANCE.md). AccessController now requires zero
constructor and single/batch scheduling delay and rejects delay updates; approved
Migration plans have MIGRATION_DELAY=0. Existing proposer/executor/canceller roles,
exact-operation hashes, replay/predecessor checks, sealing, canonical locks,
keeper cooldowns, oracle safety/finality, 1% contribution and 3% supported local
execution limits remain. No route-manager role or generic upgrade was added.
Governance can approve harmful dependencies or successor code immediately;
there is no advance warning window. Production addresses and independent approval
remain open. No deployment, public transaction, website/server update or restart
of the user-paused monitor occurred. Read scoped evidence and Git for verification
and publication; do not reuse older delayed-operation receipts as current proof.
Randomness-service qualification is still open; no provider was selected and no
randomness or artwork behavior changed in this workstream. Preserve other drafts.

## Read-only route campaign checkpoint - 2026-10-18

Read [the campaign brief](docs/INTEGRATION_CAMPAIGN.md) and
[observations](reports/activation-route-observation/VERIFICATION.md). A subsequent
paced probe succeeded for USDG/ETH feeds and four USDG-to-WETH quotes at block
92,079,017. Three conversion-only quotes were within 1% at observed oracle marks;
the 1% fee tier already exceeded it. Complete source-to-Pons LP execution remains
unqualified; gas and later LP costs are not included. No production code changed
and unchanged tests were not rerun. The earlier HTTP failure cause is unconfirmed.
The user requested a real-wallet campaign; no key was accessed, public transaction
submitted or contract deployed. The assistant cannot execute real-asset signing/
broadcasting; this is independent of wallet access. No signing script was supplied.
PoPL remains undeployed; the $1 variant remains local only and production mint is
0.05 ETH. Todo and feature references retain the open live qualification gates.
Preserve unrelated drafts, use main, and verify Git for publication. Website,
server and paused monitoring are unchanged.

## Local $1 rehearsal checkpoint - 2026-10-18

The user authorized $1 activation for testing and requested that any real bugs
found be fixed in production. Read [the isolated build guide](docs/ONE_DOLLAR_REHEARSAL.md)
and [scoped evidence](reports/one-dollar-rehearsal/VERIFICATION.md). The generator
copies sources outside the repository, changes the copied Entry/budget floors and
adds local-chain constructor guards. Ten Solidity and four Python cases pass;
the initial fixture's zero minimum-output mistake was corrected and preserved in
the evidence. No production defect was found. All production source remains
unchanged: $100 activation, 0.05 ETH mint and 1% execution loss with gas separate.
The website and production API still use $100; no live $1 integration is supplied.
Fix future production defects with focused regressions, without copying the test
override into production. Central Todo and feature/evidence references are updated.
README now separates Contracts / Backend / Frontend into component responsibility
tables with source links and an activation flow. It distinguishes live integration
targets from the current simulated website; no website source was changed.
Read-only public-wallet balance/token checks ran; price/route probing failed on
RPC HTTP errors, so no complete quote is claimed. No private key was used/saved,
no public transaction/deployment occurred, services and paused monitor are unchanged.
Use main and Git HEAD/origin to verify publication; preserve unrelated drafts.

## Range-policy application checkpoint - 2026-10-18

Read [range policy](docs/RANGE_POLICY_UPDATES.md) and [current evidence](reports/range-policy/VERIFICATION.md).
Timelocked width changes now trigger ordinary rebalance at flat prices after
cooldown. The stateless comparison uses current physical ticks and stored center;
successful replacement clears it. No new force role/request/Vault state exists.
Fresh prices, pause/lifecycle, minima, 3% aggregate and 5% idle guards persist.
Backend reports range_update_pending and price/range eligibility reason at the
confirmed hash; next keeper timing remains unknown without qualified telemetry.
Execution uses current approved configuration, not a signed historical config
hash. Scope: 37 Solidity / 38 isolated Python checks, fresh normal sizes and
internal review; refer to the evidence for the selected-pool fork result. This is
not a full regression, independent audit or production approval. Only Strategy
production source changed; Vault headroom stays 19 bytes. Preserve unrelated
drafts. Use main; verify Git publication. No website/server change, public
transaction or restart of the paused monitor is authorized.

## Dynamic liquidity checkpoint - 2026-10-18

Read [dynamic liquidity](docs/DYNAMIC_LIQUIDITY.md) and its
[scoped verification](reports/dynamic-liquidity/VERIFICATION.md) before continuing.
The user explicitly approved out-of-range activation/top-ups with a warning,
including cooldown end/current eligibility; a 600-second polling example is not
a guaranteed next rebalance. Without fresh authenticated keeper telemetry, next
check/execution time stays unavailable. The same original-source 99% marginal
deployed-LP rule and separate network gas remain enforced.

The user also explicitly approved a 3% aggregate execution-loss cap on ordinary
rebalance. Vault now reuses the immutable budget checkpoints before harvest,
after exact compound release and after redeployment. Fixed initial prices,
97% LP-plus-idle retention and 5% idle remain; existing per-step guards are kept.
This is not a 97%-deployed guarantee, an IL hedge, a cumulative erosion cap or a
cross-chain guarantee. Metadata now applies the real strategy's exit-price
deviation/freshness guard and reports unavailable on failure without losing rights.
The API resolves current LP identity/total shares separately from historical
gross contributions, and prepared transactions include confirmed range/timing.

Current size gates leave Vault 19 runtime bytes and Migration 58. Read the scoped
receipts instead of relabelling old full regressions/fork/static evidence. Main
is the only branch; use Git HEAD/origin for exact publication. Keep unrelated
wallet/process-runner/artwork drafts intact. Release is NOT APPROVED; website and
server remain unchanged, monitor remains paused, no public transaction authorized.
Repository context is durable local project memory, not global personal memory.

## Activation preparation checkpoint - 2026-10-18

Complete typed activation/top-up preparation is now in `frontend_api/activation.py`,
with strict operator pins, bounded built-in call traces and an opt-in loopback
endpoint. Read [the integration guide](docs/ACTIVATION_PREPARATION.md) and
[scoped verification](reports/activation-preparation/VERIFICATION.md). There are
38 passing focused backend tests on the exact publication snapshot, 63 verified
ABI getter layouts and a local Anvil trace/gas probe with the actual budget helper.
No production Solidity changed; unchanged broad contract checks were not repeated.

Per-NFT displayed value must come from confirmed `NFT.currentLPValue`: marked
deployed LP plus attributed idle/compound, separately from rewards and the new
contribution's marginal LP. The user pays network gas separately; one Entry call
covers conversion/balancing/LP addition, with ERC20 approval/reset transactions
separate when required. Conversion/slippage/undeployed input share the 1% limit.
Missing allowance produces only an exact approval step, never a fake ready LP
quote. Full preparation checks original-source value, actual budget/share/LP
results and resimulates exact final calldata with bounded minima/deadline.

This milestone is published on main with Todo/features/evidence; verify Git for
the exact commit. Actual route/feed manifests, provider callTracer/hash/gas support,
complete network-fee accounting, browser wallet/hosting and independent production
qualification remain open. Release NOT APPROVED; website/server unchanged. Preserve
the separate unpublished mint/claim, conversion-only quote, process-runner and
artwork drafts. The user-paused staging monitor remains paused.

# AAA / ZZZ PoPL project instructions

## Claim-history continuity checkpoint - 2026-10-18

Read [the predecessor history reference](docs/FRONTEND_LINEAGE.md) and its
[verification](reports/frontend-lineage/VERIFICATION.md). The schema-2 API now
combines lifetime LP and royalty claims across the complete explicitly pinned
same-chain predecessor lineage, including past owners and historical-only assets.
Each source must be retired with matching origin, bidirectional peer links,
canonical activation/retirement receipt and terminal root. Replays end at each
source retirement; current claimable balances are unchanged. Missing lineage
configuration stays unavailable; invalid configured history fails closed.
Bounds are eight predecessors and one million configured replay events in total.
These checks rely on reviewed RPC/indexer ingestion, not consensus finality proofs.

The exact publication snapshot passed 91 API/lifecycle/history tests, including
17 new lineage cases. Existing compiler artifacts authenticate two getters and
two event layouts; production Solidity is unchanged and was not retested.
The central read-API task is implemented locally. Hosted archive qualification,
independent peer-code review, live frontend integration and cross-chain history
remain separate open tasks. Keep release NOT APPROVED. Do not mistake these
same-chain receipt checks for the missing cross-chain finality mechanism.

Use main and verify publication with Git HEAD/origin/main. Preserve unrelated
optional wallet POST, quote/process-runner and artwork drafts. No website/server
change, monitor restart, deployment or public transaction was authorized.
Older dated checkpoints below retain their original scope; this entry supersedes
the earlier statement that same-chain predecessor replay was unimplemented.

## Frontend lifecycle checkpoint - 2026-10-18

Read [the schema-2 API boundary](docs/FRONTEND_LIFECYCLE.md) and its
[verification](reports/frontend-lifecycle/VERIFICATION.md). The pinned read API
now checks canonical phase/state, pause/preparation and original identity using
eight runtime pins. Locked NFT/wallet projections fail closed; `/v1/protocol`
reports status without reward/price reads. Peer addresses are source commitments,
not independently verified destinations. Importing/cancelled origins and imported
successor lifetime-claim totals are unavailable; complete predecessor replay and
website integration remain open in the central Todo.

This scope promotes the saved final snapshot freshness/depth checks, with the
matching tests, but keeps optional POST/unsigned wallet, quote/process-runner and
artwork drafts separate. Verify publication using Git HEAD/origin/main. Production
Solidity is unchanged; do not rerun its unchanged tests for this Python work.
No website/server update, monitor restart or public transaction is authorized.

## Verified handoff checkpoint - 2026-10-18

The saved bridge fixtures and cold-helper gas changes are verified: 582 offline
regression passes, zero failures, two expected opt-in fork setup skips, across
49 compiler-bound suites. Reuse the unchanged 34 focused handoff passes only with
[the dependency check](reports/canonical-handoff/reuse-verification.json): together
these cover 616 successful cases, not one newly executed 616-case run. The 30
normal object gates/39 production source bindings, 141 configuration checks,
88 focused keeper checks and 374-finding internal review remain source-matched.
123 additional keeper cases pass; one Unix permissions case awaits Ubuntu.
Current runtime margins remain Vault 33 bytes and Migration 58 bytes.

This checkpoint accompanies scoped publication on main. Verify Git HEAD and
origin/main before naming the published commit or reporting CI; older uncommitted
statements below describe historical saves. Preserve unrelated unpublished
wallet/API, quote/process-runner and artwork drafts. Follow
[the resume handoff](docs/WORK_HANDOFF.md) and [verification](reports/canonical-handoff/VERIFICATION.md).
No production source changed during the resumed regression. Release is NOT
APPROVED; cross-chain finality/closure/lineage/transport remain pre-seal work.
No website/server update or public deployment/transaction is authorized.

The user paused the chat staging-health monitor on 2026-10-17. Do not resume it
without authorization. The isolated server service was not stopped by that pause;
subsequent intervals have no chat-monitor coverage. Existing staging has not been
upgraded to this keeper/controller lifecycle. Exact-commit CI and new operating
rehearsals remain separate from local evidence.

## Saved continuation checkpoint - 2026-10-17

Historical snapshot, superseded by the verified 2026-10-18 checkpoint above.

The user requested a durable save before credits run out. Read
[the resume handoff](docs/WORK_HANDOFF.md) and the
[current evidence](reports/canonical-handoff/VERIFICATION.md) before continuing.
The same-chain candidate and these notes are LOCAL, UNCOMMITTED and UNPUSHED
at this checkpoint; baseline main is `79f205a7933107f61f26892109f14ee52821700e`.
Do not confuse saved files with GitHub publication or production approval.

Completed scoped evidence: 34 focused handoff tests, 30 normal object size gates,
39 production source bindings, 141 configuration tests and 88 keeper tests.
Internal Slither review covers 374 findings (153 false positives, 75 accepted
risks, 146 informational), with coverage and 10 mutation rejections passing.
The broader diagnostic run returned 576 passes, six failures and two intentional
fork skips; its compiled snapshot also predates the final coordinator changes.
Six bridge failures exposed mocks lacking the lineage interface. Mock fixes are
saved but NOT rerun. Gas diagnostic attempt1 returned ten successes, but source
binding rejected its stale fixtures; the final cold-helper fixture changes also
need a fresh run. Do not report a complete current-source regression pass.

Preserve unrelated wallet/quote/process-runner/artwork drafts. Do not repeat
unchanged focused/static checks without a source-binding reason. Keep release
NOT APPROVED, future-chain requirements open, and website/server unchanged.

## Canonical handoff candidate - 2026-10-17

Read [the same-chain handoff reference](docs/CANONICAL_HANDOFF.md) and
[current verification](reports/canonical-handoff/VERIFICATION.md). Continue using
`main`. Preserve unrelated unpublished wallet/quote/process-runner/artwork work.

The new local candidate adds six-domain complete export/import, immutable receipt
cutoffs, ownership/accounting freeze, ordered per-domain settlement, exact classified backing transfers, restored
abort, atomic source retirement/single-successor activation and one-hop late
creator/royalty forwarding. Four separately deployed modules are sealed:
CanonicalHandoff, NFTCanonical, VaultCanonical and FeesCanonical; owner bindings
are verified. Royalty and creator receiver factories are immutable automatic
children. Inventory is controller plus 20 modules and eight fixed helpers/factories.

This executable path is SAME-CHAIN ONLY: all mints revealed, local buckets
Parked/None, no active plans and no historical legacy bridge sends/receipts.
The original identity/inventory and exact reward fractions persist; source
approvals are not imported. Imported successors cannot initiate v3 principal
bridging because its lineage/current-home model is incompatible. Cross-chain
finality, authenticated channel closure, a new lineage/message version and exact
transport/backing remain pre-seal work. Do not say full future-chain migration is
complete or that sealed code can acquire it later. No post-halt recovery is supplied.

The user explicitly chose reviewed replacement code through timelocked governance
on 2026-10-17, accepting that a malicious approved replacement could divert LP.
Do not add an identical-code requirement or describe governance as unable to alter
successor economics. Independent code/admission review remains mandatory; this
decision does not waive verified finality, exact backing or single-successor
retirement, and adds no multisig/timeout activation override.

Keeper requires strict canonicalState plus preparationActive; locked states stop
all new submissions while pending receipt recovery continues. Existing isolated
staging is unchanged. API/website lifecycle, predecessor claim-history continuity,
marketplace collection cutover and contract-owner/escrow compatibility remain
tracked in the central Todo. Keep the current feature/evidence and release scope
distinct from historical receipts. No website/server change, public transaction
or contract deployment is authorized.

## Architecture evolution and migration preparation - 2026-10-17

**Use `main` for this project**, as explicitly requested by the user. The earlier
review branch was integrated into main; check Git for exact publication. Preserve
unrelated unpublished wallet/quote/process-runner/artwork changes.

Read [migration safety](docs/MIGRATION_SAFETY.md), the
[canonical migration design](docs/CANONICAL_MIGRATION_DESIGN.md),
[current verification](reports/migration-safety/VERIFICATION.md) and the earlier
[architecture review](reports/architecture-evolution/REVIEW.md).
The user-approved **3% aggregate execution limit, gas separate**, is now enforced
for atomic same-ordered-pair local `movePool` and parked `resume`. The immutable
Vault-created helper snapshots prices/principal before harvest, adds released
compound to the denominator and requires at least 97% retained LP plus attributed
idle, with the existing 5% idle ceiling. It is not a 97% deployed-LP promise, a
cross-chain budget or protection against repeated cumulative losses. Activation
and top-ups keep their **1% marginal deployed-LP** rule. Keep 80/10/5/5 fixed.
Do not remove ordered-pair guards: different pairs need composition epochs,
historical reward/intake handling and typed conversion.

The user selected **controlled whole-protocol migration while the home chain
still works**, deferring post-halt recovery, and **verified source finality with
no multisig-only override** for future replacement activation. No proof provider
is inferred. Reversible timelocked preparation now stops new economic work and
protocol configuration while claims, transfers and authenticated settlement/drain
remain available. It does not freeze/export ledgers, retire the source, activate
a successor or authenticate satellite shutdown. Complete funded freeze/export/
import and single-successor accounting remain pre-seal requirements; sealed
contracts cannot gain these missing capabilities later.

Keeper preparation checks fail closed if the controller getter is unavailable.
Receipt recovery and permitted drains continue; new rebalance/compound/buyback
submissions stop. Existing isolated staging was not upgraded. Qualify keeper and
controller/fixture interfaces together before deployment. See the
[keeper evidence](reports/canonical-preparation/keeper/README.md).

Destination capacity has permanent idempotent registration; `bucketCount`
includes unfunded reserved None identities. Source code does not authenticate
remote reservation proof. The [address inventory](docs/DEPLOYMENT_ADDRESSES.md)
now includes the fixed migration-budget helper; production selections remain
open. Current normal-build headroom is only 17 runtime bytes in Vault and 30 in
Migration, requiring modular design for subsequent handoff work.

Use current source-bound receipts, not older Vault/static/fork results, for these
changes. Internal review is not an independent audit or production approval.
No website/server change, public transaction or contract deployment is authorized.

## Current documentation rules - 2026-10-16

- [Project Todo](TODO.md), generated from [the ledger](docs/project-todo.json), is the only task-status list. Preserve Contracts / Backend / Frontend ordering, stable task IDs and clickable titles; detailed acceptance criteria expand under their owning tasks.
- [Feature and evidence reference](docs/IMPLEMENTATION_STATUS.md) describes capabilities and scoped verification. [Release approval record](docs/RELEASE_CHECKLIST.md) records the exact-release go/no-go; it remains NOT APPROVED. Neither is another Todo.
- Follow [the maintenance procedure](docs/TODO_WORKFLOW.md). Runbooks and the roadmap describe procedures, scenarios and sequencing; update progress in the central ledger, not in parallel checkbox lists.
- Older dated entries below preserve historical evidence. Their old bucket limits, missing batch claims, test counts and publication statements do not override the current README/reference or a later scoped handoff. Check Git HEAD, origin and the working tree before reporting what is published.
- Unpublished wallet/quote/process-runner and artwork work must remain distinct from published source and historical verification. Repository context is durable project memory; it is not a claim that global ChatGPT personal memory is enabled.

- This directory is the smart contract project: https://github.com/ABEF/AAA.
- The separate website is https://github.com/ABEF/AAA-website, locally at `C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website`.
- The user requires website modifications to follow this order: edit locally, verify, commit and push the website repository, then update and verify the Ubuntu server. This does not authorize deploying smart contracts or real transactions; the website is a simulation.
- Check which repository a requested change belongs to before editing or publishing. A website simulation is not evidence of implemented or deployed contract behavior.
- Current accepted decisions (2026-10-16; production gates open) supersede older dated context: dormant mint costs exactly 0.05 ETH; activation starts with at least $100 original gross source value and must deploy at least 99% as marginal LP, with gas separate. Later contributions use the same 1% execution/undeployed limit. The immutable Registry-created Entry now binds original-source value through typed conversion into the Vault; actual route/feed qualification remains open. Target inputs are USDC, USDG, ETH and ZZZ with reviewed addresses/routes, not ticker-based admission. Minting alone increases supply, not LP.
- Collection cap is 1,000 NFTs, with exact eventual quotas of 600 Commun / 300 Rare / 100 Legendary. A fixed coordinator supplies VRF words; ordered draws consume remaining rarity quotas. No owner-selected rarity/color or reroll is authorized. Actual production VRF support/configuration is still unverified.
- LP revenue allocation is 80% individual / 10% collective / 5% compounding / 5% buyback and burn. Individual rewards follow LP shares; the collective pool is shared equally among activated NFTs. Power is removed from the current economics. Unharvested or delayed remote fees use receipt/processing-time collective membership; already indexed rewards and settled local inbox funds exclude later entrants.
- Marketplace royalties request 5% via ERC2981. A separate immutable NFT-controlled ledger distributes 100% of actual admitted royalty receipts among activated NFTs at Commun x1 / Rare x2 / Legendary x3. Rarity never changes LP fee weights. Prefunds and receipts before asset admission or while no NFTs are eligible stay quarantined.
- Artwork evolution uses current marked attached LP value, not lifetime contributions or a high-water mark: Dormant / Activated / Enhanced ($1,000) / Singularity ($10,000). Market declines can reduce the artwork stage without revoking activation, royalty eligibility or fee rights. Remote/outage valuation is explicitly unavailable; principal remains nonredeemable.
- The current source caps total historical local buckets at 16, including imported custody; returns reuse their slot. The earlier 32-bucket workload used 16,311,524 gas and exceeded the unchanged 12M local regression budget. The revised 16-bucket workload passed at 8,909,042 gas, and all four bucket-cap/import/return tests passed. This shared-pair/mock-venue result does not establish gas safety for every production asset/inbox/venue combination.
- Artwork now uses eight fixed colors: Cyan, Blue, Violet, Emerald, Amber (yellow), Crimson (red), Ivory (white) and Onyx (black). Bicolor pairs contain Ivory, Amber, Crimson or Onyx; tricolor adds a distinct Amber, Crimson or Onyx to an allowed pair. This yields 8 monochrome / 22 bicolor / 28 tricolor palettes. Color style, palette and circuit pattern are immutable visual traits with no effect on any rewards. Final approved patterns are Flowing arcs, Segmented panels, Orbital rings and Vertical ribs. Hexagonal mesh is removed, Vertical ribs replaces Branching circuits, and Helix was rejected. The approved egg texture/material and original 72 PNGs are preserved. The renderer covers 2,784 palette/pattern/rarity/evolution states, separate from the 1,000 NFT supply.
- A fixed finite artwork inventory is drawn without replacement within each VRF-selected rarity. It has 200 monochrome / 500 bicolor / 300 tricolor slots, each with the same 60/30/10 rarity mix; at most four identical palette/pattern/rarity finishes, with all 100 Legendary looks unique. The website uses the same inventory in a deterministic simulation. Public GitHub/source/economics/security links are removed; the footer links to https://zzz.protocol.link/ and has clickable X/Telegram icon placeholders until the user supplies URLs. See docs/NFT_METADATA.md and design/nft-metadata/palette-system-v1/README.md.
- The user accepted Flowing arcs for Overview PoPL #444 with no additional circuit overlay. The website banner places DEVELOPMENT PREVIEW on the right, with bold PROOF OF PERMANENT LIQUIDITY and the exact disclaimer “(Minting and claims are simulated; no real assets move)” on the left. Mint pattern lines are readable in Dormant state and become brighter through evolution; the original metallic texture is retained.
- The contract candidate remains undeployed. Actual selected native-ETH/Pons market integration, revenue terms, supported production VRF, production bridge, authority/configuration review and an independent audit remain gates. Website wallet actions are simulations. Website artwork/UI commit 9eaa9e67917240112dd402d27fc8b2980c7b79fa is locally verified, pushed and deployed. All 5,581 public files match the committed build over verified HTTPS; five host/redirect/IP checks and four private-path checks pass. Website checks passed 40 tests, 83 HTML IDs, five routes and 2,784 artwork/metadata pairs. External receipt: website-server-release-9eaa9e6/public-verification.json. Earlier 4cf1c81 and f8e1916 release receipts preserve their historical 155-file checks. Website publication is not contract deployment.
- Final four-pattern implementation and current scoped source verification are complete: full offline Solidity passed 336 tests with zero failures and one expected opt-in fork-setup skip (337 total, 24 suites); 327 portable Python tests passed from a 331-test inventory with zero failures/errors/runtime skips and four unchanged Unix-only cases excluded; all 20 module/helper runtime/initcode-object size gates passed and the normal offline build/size command exited zero. NFT runtime/initcode object is 18,519/42,004 bytes, renderer 12,191/12,508, and Vault runtime remains 24,407 bytes with 169 bytes available. Constructor arguments still need deployment-time allowance. Compiler metadata binds all 26 current Solidity sources. Fresh source-bound Slither covers 26 sources and three build/configuration files: 179 findings individually reviewed internally as 110 false positives / 42 accepted risks / 27 informational / zero unresolved, with coverage/matcher/mutation checks passing. This is not an independent audit. See reports/artwork-palettes/verification-summary.json and reports/artwork-palette/README.md. Check Ubuntu CI separately for the published revision.
- Dynamic tokenURI reads select the current artwork stage; reveal and contributions emit ERC-4906 events. The release-hardening candidate adds permissionless inclusive ordinal-range notifications (maximum 50), resolving actual hashed token IDs without price reads. An optional disabled-by-default keeper watcher observes confirmed evolution/availability/reveal state through the existing budgeted serial transaction path, with receipt-state checkpoints and fair bounded scans. It does not refresh every within-stage USD fluctuation. Actual feeds/runtime pins, operating staging and external marketplace caches remain release work; Uniswap does not update this NFT's metadata.
- Historical metadata snapshot (superseded by the current handoff): the then-current feature checklist was docs/IMPLEMENTATION_STATUS.md; docs/COMPONENT_STATUS.md provides source boundaries, while docs/RELEASE_CHECKLIST.md remains NOT APPROVED. Current metadata-source tests, sizes, Python and static-analysis receipts are in reports/release-hardening/; full offline Solidity passed 342 tests with one expected fork setup skip, all 20 object gates passed, and fresh internal Slither reviewed 179 findings. NFT runtime/initcode is now 18,822/42,307 bytes. Earlier all-green Ubuntu CI for 5febe7065856749345010ecca23dcd368b472c9e (run 38793910449) remains scoped to that revision; check the new published commit separately. Native/Pons custody, arbitrary USDC routing, live financial projections/wallet claims and actual watcher staging remain pending. Claims take one NFT and asset per call; the demo bulk button is not an implemented contract batch function.
- Production governance, guardian, keeper and mint-recipient public addresses are not selected; the user explicitly requested keeping those release gates open. No deployment or real transaction is authorized. Rewards use actual receipt/processing events, not a fixed minute clock. The keeper example polls every 600 seconds and makes conventional harvest eligible every 14,400 seconds; rebalance additionally requires configured price movement, cooldown and execution guards. Production strategy parameters and creator payment frequency/percentage remain undecided. Royalties synchronize pending admitted receipts on claim; LP claims use already allocated funds. The website still simulates LP claims and lacks real royalty claim integration.
- Historical pre-art evidence in reports/website-alignment/ records 334 offline Solidity passes, 321 portable Python passes and 177 reviewed Slither findings for its earlier source snapshot. Its nine pinned-block fork tests (zero failures/skips), four bucket-cap cases including the 8,909,042-gas workload, and 256 x 256 accounting stress run (65,536 calls, zero reverts) are preserved as historical 16-bucket verification. The fork uses a separate hookless local pool and mock VRF, not actual Pons custody or real randomness service. The live-dependency fork and extended stress profile were not rerun for the final four-pattern artwork source; unchanged LP/economic source hashes do not turn those earlier complete snapshots into fresh current-source evidence.
- Preserve existing source and historical review evidence unless the user requests a change. Distinguish original review reports from checks actually run in this environment.
- Do not save credentials or access tokens in source files, documentation, Git remotes, or commits.

## New release-integration work - 2026-10-15

The current working candidate adds strictly pinned selected native/Pons settlement with real venue keys separate from WETH accounting, fee-aware balancing, a bounded 32-operation NFT-owned LP/royalty claim router, confirmed single-NFT read API, active-liquidity revenue measurement proposals and a verified IPFS upload archive. Older 342-test/20-object/179-finding receipts above retain their original source scope; they do not verify these changes. Follow the fresh evidence and pending gates in docs/IMPLEMENTATION_STATUS.md and docs/RELEASE_CHECKLIST.md.

Creator terms stay unset while accounting uses actual receipts. The user reports the creator accepted proportional liquidity sharing, requested implemented measurement proposals and a Todo to confirm them: fee-weighted sampled active liquidity is proposed, time-weighted active liquidity is an alternative. Epoch/sampling/complete event data, payout asset/frequency, percentage basis and authorized payer/receiver still require agreement. The calculator cannot debit the creator or fabricate claimable revenue. IPFS provider selection and publication remain deferred; preparing the 5,571-file archive is not pinning a CID.

Native wrapper implementation/admin upgrades remain a trust and operating-review issue. Production native inventory admission, actual stable-input route qualification, live VRF/oracles/authorities, hosted financial projections and wallet transactions, testnet operation and independent audit/remediation remain open. No smart contracts were deployed or public transactions authorized. The separate website release is now 8c0b93523d914644d440129d74745c9e12f8e08a, still simulated; current contract work has not changed/published the website.

Previous local integration/recovery verification: 430 Solidity passes (two expected opt-in fork setup skips), 478 portable Python passes (four Unix-only cases for Ubuntu), 22 normal module/helper size gates, all 28 compiler/source bindings and 17 actual selected-pool fork passes. Internal Slither: 210 findings individually reviewed, 121 false positives / 56 accepted risks / 33 informational / zero unresolved; not an independent audit. Those receipts predate the Entry/parking changes below. Governed activation-source add/disable/re-enable, wrapper policy maintenance including renunciation, and nonzero sequencer-source replacement are implemented; sealed custody code remains fixed. Read docs/CHANGE_AND_RECOVERY.md and reports/release-progress/README.md.

## Atomic entry and custody parking - 2026-10-16

The immutable Registry-created ZZZActivationEntry authenticates current owner, exact source ingress, Oracle-based gross value and the typed Vault calldata. Direct/native/single-hop V3 inputs share one original-source 1% loss budget. Arm context only after the exact Vault approval and owner recheck; delete it before allowance cleanup. Active context mismatches must revert rather than falling back to post-conversion pair value. No arbitrary executor/recipient, NFT custody, user USD claim, permit or rescue is authorized. Actual routes/feeds and combined real Pons execution remain qualification gates; USDC is unavailable without a reviewed funded route.

PositionStatus.Parked is appended as 6, preserving 0..5. Global pause plus sealed timelocked Migration.park authorizes an exact share/LP/pool/location/epoch/nonce snapshot, review hash, narrow deadline and raw close minimums. Close-only proceeds exclude old idle, donations and compound reserves. Parking retains principal in Vault and skips source prices and creator inboxes; actual venue/wrapper/token checks remain. Parked membership/reward/royalty claims and transfers persist, upkeep/new contributions stop and current LP valuation is unavailable. Fresh guarded resume or separately approved migration retains ordinary destination and remote-funded-liability protections. No generic proxy upgrade, principal withdrawal or universal external-failure recovery exists. See docs/ACTIVATION_ENTRY.md and docs/CUSTODY_PARKING.md.

Current work remains local, uncommitted and undeployed; the website/server are unchanged. Historical review evidence must not be relabelled for this source snapshot.

These are repository-local instructions, not a claim that global ChatGPT personal memory is enabled. Later explicit user instructions take precedence.


Latest gap-hardening verification supersedes the old 430/478/22/28/210 snapshot: 488 offline Solidity passes (two intentional fork setup skips), 488 portable Python passes (four unchanged Unix-only cases for Ubuntu), 23 normal object gates and 29 production source bindings. Actual single-run fork result: 20 selected native/Pons plus nine secondary hookless tests passed, none failed/skipped. Fresh internal Slither: 220 reviewed findings, 128 false positives / 53 accepted risks / 39 informational/zero unresolved; 43 matcher cases and nine mutation rejections pass. Exact-source receipts and fixtures are in reports/gap-hardening/. This is not independent audit or production approval. Current source is saved locally and remains uncommitted/unpushed/undeployed.


## Git publication handoff - 2026-10-16

The user explicitly requested committing and pushing the verified contract work, including project notes and todo/release checklists, to ABEF/AAA. Earlier uncommitted/local wording records the verification-time state before this publication. The source-bound receipts remain unchanged; current publication status and commit identity are established by Git HEAD and origin/main. No smart-contract deployment, signing, real asset movement or website/server change is authorized by this request. Exact-commit Ubuntu CI must be checked independently; local evidence is not a claim of a green published workflow or production approval.

## Central Todo maintenance - 2026-10-16

The user wants the central task list in this contract repository on GitHub, **not in the website frontend**. For every new task, fix, decision or completed milestone, update `docs/project-todo.json`, regenerate `TODO.md` with `python scripts/sync-project-todo.py`, run it again with `--check`, and reconcile affected implementation/release details. Commit/push the intended checklist changes and verify publication; report any unpublished work explicitly. See `docs/TODO_WORKFLOW.md`. Todo-only changes do not require a website deployment.

## Keeper recovery hardening - 2026-10-16

Read `docs/KEEPER_RECOVERY.md` and `reports/keeper-recovery/REVIEW.md` for keeper changes. Live startup requires restored/explicitly initialized state, nonce continuity, a canonical receipt anchor for used signers and a reviewed network fee accounting policy. Never delete ambiguous intent or reset budgets to recover. Use only one signer host; state loss, failed backup, role/key rotation and real Linux/RPC/fee operation require rehearsals. Local tests and internal review do not establish production readiness. Keep the central Todo/release gates current.

## Published keeper verification - 2026-10-16

Keeper/Todo commit `3db782b087d5add2327f519030055d288d9d6512` is pushed. Exact-commit Ubuntu keeper verification (run 38956992156) passed 183 tests with zero failures/skips and systemd unit validation; Todo consistency run 38956992065 passed. The local broader workspace passed 602 Python tests with five Unix cases separately covered by Ubuntu. The keeper changes are published; other pre-existing Solidity/frontend development remains uncommitted and must not be silently discarded or included. The website is clean at its previous deployed revision, with no Todo page. Read `reports/keeper-recovery/REVIEW.md`; production operating gates remain open.


## Isolated keeper staging and operating evidence - 2026-10-16

The user authorized the existing website server for an isolated staging account. Current keeper operating source is published at 089d391c1689c2036db518c7a9705989896a14d8. Ubuntu run 38961988650 passed 209 tests without failures/skips plus all 14 real-process Anvil rehearsals. The website host now runs zzz-stage-anvil / zzz-stage-keeper as unprivileged zzz-stage, chain 31337 on loopback port 18545, with resource/filesystem/network restrictions. No public signing or real assets were used. Systemd crash/restart and controlled off-host snapshot round-trip restore passed; website HTML remains unchanged over HTTPS.

Read docs/KEEPER_REHEARSALS.md and reports/keeper-rehearsal/ for exact source scopes. A forced-command zzz-stage-monitor SSH account exports only test health/recovery snapshots; no shell/forwarding/signing authority. zzz-stage-observer.timer refreshes every five minutes. Chat heartbeat popl-staging-health reads it every 30 minutes, stores off-host snapshots outside Git and reports meaningful changes; it depends on desktop availability. Never print private keys or treat a missing monitoring interval as uptime. The sustained soak is not yet a multi-day pass. Actual Robinhood Testnet, redundant production RPCs/fee qualification, live services/authorities, physically distinct host loss/key rotation and independent review remain gates. Preserve unrelated unpublished contract/frontend work.

## NFT economic-rights audit handoff - 2026-10-16

Read reports/nft-rights-audit/REVISED_PROMPT.md, REVIEW.md and VERIFICATION.md for
the executed comprehensive review. Economic owner indexes are per bucket/asset,
collective indexes per asset, and paid checkpoints/accruals/fractions per NFT;
all unclaimed rights follow current ownership. Transfer approval alone cannot
claim. Buyers receive then-unclaimed balances, not guaranteed listing snapshots.
An escrow that becomes ownerOf is the holder. Already correct economics were
preserved; new tests strengthen 1,000-NFT payouts, buyback and dual-ledger coverage.

The current historical bucket cap is FOUR, not the old sixteen; all 1,000 NFTs
can use one shared LP. The older combined16 workload exceeded the unchanged12M
gas budget. Getter ordering in gas fixtures was corrected before final evidence.
Production token/venue/Entry costs still need qualification. Real bridge capacity
admission, token liveness/dust policy, live services, creator terms, authorities,
operating rehearsals and independent audit remain open. No deployment is authorized.
Current receipts are source-bound; unchanged-source old Slither/fork runs are
explicitly reused, not rerun or renamed. Do not silently include remaining
unpublished frontend/quote/process-runner/artwork changes in an audit publication.


## Security audit workstreams - 2026-10-16

The central Todo now tracks seven security workstreams with acceptance criteria
in docs/SECURITY_AUDIT_PLAN.md: governance/sealing, shared accounting, ownership
and allocations, oracle/keeper economics, dependencies/backing, whole-protocol
recovery and cross-contract/infrastructure security. These are release work,
not an assertion that independent audit is complete. The split is currently
fixed; configurable percentages are only a risk/benefit question, not an approved
change. Permanent home-chain loss has no canonical NFT/reward-ledger recovery;
LP migration alone does not solve it. Decide this architecture before sealing.
