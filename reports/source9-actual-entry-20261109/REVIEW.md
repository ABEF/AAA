# Source9 actual Entry3 rehearsal

Production is **not approved**. This campaign fixes production backend/unsigned
consumer defects and exercises the current contracts on a new disposable fork.
It does not change deployed public contracts, either running website, the shared
wallet signer, the existing Anvil lab, its journals, or the paused heartbeat.

## Improvements

1. Fresh accounting7 reads used `PoolRegistry.ZZZ()`, which has no public
   selector. They now authenticate the existing pinned
   `Migration.currentZZZ()` binding. Wrong, missing or malformed identity fails
   closed; there is no fallback or new contract dependency.
2. The activation trace parser rejected a real first-deposit epoch0 witness.
   Fresh7 now verifies the actual one-phase initial / two-phase funded epoch
   sequence, exact bucket, equal bounded epochs and historical marks. It rejects
   missing, extra, changed or misplaced observations. Historical profiles keep
   their original decoder. The published literal trace regression binds its
   original production sources; it is not a synthetic success trace.
3. Optional activation gas policy2 captures the reviewed operator ceiling and
   the same confirmed block's gas limit, enforces full20% estimate headroom and
   a total network-fee ceiling, and uses that cap for both traces and the final
   estimate. The source9 consumer independently checks the matching envelope.
   Defaults remain policy1/12M. Choosing policy2 changes neither contract loss
   caps nor signing permissions. Claims retain their separately selected policy.
4. Rehearsal rejection expectations are typed. A timeout, HTTP503, unrelated
   exception or changed source cannot count as the requested negative result.
   Deployment/funding helpers retain exclusive durable intents and submitted
   hashes before recovery, preventing a read failure from becoming a resend.

## Actual environment and market limitation

The fork is Robinhood chain4663 at block109612376,
`0x3099ccb56cf1070b94260c5db3f12bca7ef053d01b9bcd3ae3664b80d16e225f`.
All five fixed core/periphery/ZZZ dependency hashes match the source inventory.
The production graph uses the unchanged normal compiler objects, admitted only
after all87 raw-source hashes and compiler input contents/settings match.
58 deployment/configuration transactions completed with actual Access bindings
and sealing, on this disposable fork only.

The first $100 ETH test at the captured **unmodified market depth** safely
reverted. About$46.89 was deployed and$52.82 remained idle, exceeding the5%
idle guard; the later$98 marginal-LP requirement would also be unsatisfied.
Caught quote-result reverts are not operation failures. No financial guard,
pool range or input minimum was weakened to obtain a pass.

Successful-flow tests use an explicitly separate synthetic external-depth
fixture in that same real pool. It added `10^22` active liquidity over aligned
ticks[-887200,887200], using locally funded ETH/ZZZ, and proved unchanged pool
spot/tick/fees, exact active-liquidity increase and complete unused-budget
refunds. Its position is owned by the test helper, never PoPL or an NFT.
This is **not qualification of current public liquidity or swap routes**.

Four controlled, correlated feed fixtures and a mock VRF are explicit substitutes.
Random disposable empty-code EOAs avoid existing delegated-code accounts. The
public provider was read-only and rate-limited behind a bounded exact-anchor
cache. An older archive attempt failed and is retained. None of this establishes
independent feeds, VRF proofs, provider availability or target transaction costs.

## Executed user flows

The ordinary website source9 consumer used real HTTP, real canonical RPC reads
and the production API handlers. It produced unsigned reviews only. A separate
owned-fork controller executed their exact calldata using disposable local EOAs.

| Flow | Observed result |
| --- | --- |
| ETH activation | One contribution transaction; about$99.53 actual associated LP. Only its NFT became active. |
| ZZZ activation | Exact selected-token approval, then fresh full preparation and contribution; about$99.35 associated LP. |
| ETH growth | $60 input increased the existing main; its NFT reached about$159.28 and the enhanced metadata variant. |
| ZZZ growth | Exact9,000ZZZ approval, then fresh contribution; its NFT reached about$162.11 and the enhanced variant. |

Every contribution proves entrant-only marginal deployment, actual share
issuance, source spending, the fixed Entry destination and actual successful
receipt. Later entries preserve the main position ID, ticks, centre and
rebalance clock; other NFTs' share quantities remain unchanged. No residual is
created. Exact allowances are consumed without unlimited approvals.

The isolated cosmetic thresholds are150/500USD so the small campaign can show
confirmed evolution; production defaults and user economics are unchanged.
Metadata uses an explicit disposable URI prefix, not a qualified IPFS bundle.

Wrong-owner and wrong-state reviews, and ETH/ZZZ growth one raw input unit below
the effective minimum, are rejected. A saved expired review fails on-chain with
`Expired()`. An intentionally stronger impossible liquidity floor was simulated
and submitted only on the owned fork: it reverted with `Slippage()`. The actual
failed receipt proves native input returned, no logs or LP/share/allowance/
metadata changes, unchanged pool spot and only network gas paid.

## Evidence and remaining work

See [verification](VERIFICATION.md), the machine-readable campaign records and
the linked source-bound test fixture. Original failed attempts and full local
artifacts are retained; historical reports are not relabelled as new passes.
The contract normal/static suites were not rerun because production Solidity
and runtime objects are unchanged. New test fixtures were compiled separately.

The current public pool's execution depth remains a release blocker. Qualify
actual reviewed venues, independent feeds, supported VRF/OpenSea minting,
authority addresses, complete target fee/gas accounting, archive/hosting/recovery
and independent audit/remediation. This campaign does not test a public wallet
signature, production deployment, residual/rebalance lifecycle, fee harvesting,
claims or long-lived load. Their existing evidence keeps its original scope.
