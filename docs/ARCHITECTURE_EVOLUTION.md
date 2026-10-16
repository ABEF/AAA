# Architecture evolution and trust boundaries

Design reviewed 2026-10-16 against baseline `37bf0d2`. This document separates
current capabilities from proposed changes. The [central Todo](../TODO.md) owns
progress; the [review brief](../reports/architecture-evolution/REVISED_PROMPT.md)
defines execution and evidence scope. No production deployment is approved.
The [deployment address inventory](DEPLOYMENT_ADDRESSES.md) separates selected
wallets, generated contract/helper addresses and reviewed external dependencies.

## What can actually evolve

| Transition | Current boundary |
| --- | --- |
| Rebalance the shared position's range | Implemented strategy, cooldown and execution guards; one LP serves many NFTs. |
| Move to another local pool with the same ordered accounting pair | Supported within the fixed Uniswap v4 manager and admitted pools. |
| Move ZZZ/WETH principal to ZZZ/USDC | Rejected. Requires actual conversion plus accounting changes described below. |
| Reverse local currency slots | Rejected by local move; cross-chain import has its own explicit slot mapping. |
| Add a new hookless ERC20 v4 pool | Governed configuration, within existing manager/asset/price guards. |
| Add an arbitrary hook, native pool or new DEX | Unsupported by the fixed manager; the selected native/Pons exception is narrowly pinned. |
| Add a future EVM chain with equivalent assets | Append-only route/transport framework exists. Provider, remote custody, finality and capacity require qualification. |
| Treat WETH18 as USDC6 through route mapping | Unsupported; v3 transports raw amounts and requires equivalent declared decimals, not a conversion. Equal decimals alone do not prove equivalence. |
| Repeat A -> B -> C -> home -> B | Compatible-asset fixture coverage exists; no production bridge qualification. Stable home identity and historical funded obligations remain. |
| Move canonical NFT ownership and both reward ledgers | Not implemented. Moving LP does not change the canonical chain. |

Sources: [Vault](../src/ZZZVault.sol), [Migration](../src/ZZZMigration.sol),
[route registry](../src/ZZZMigrationRegistry.sol), [manager](../src/ZZZLiquidityManager.sol),
[fee controller](../src/ZZZFeeController.sol), [change matrix](CHANGE_AND_RECOVERY.md).

A future remote destination could implement another venue behind a reviewed
compatible custody/receiver interface. The source does not verify that remote
implementation's semantics. This is external custody admission, not an available
local DEX adapter. Current same-chain bridge routes are rejected, so they cannot
be used to substitute a new local Vault for the fixed canonical ledger.

## Three layers, with two distinct trust domains

| Layer | Enforced locally | Remaining trust |
| --- | --- | --- |
| Fixed rights and accounting | NFT owner checks; nonredeemable principal; stable per-NFT shares; asset-specific claims; fixed 80/10/5/5 and separate royalties; one-time module binding | Correct initial deployment, admitted token behavior and canonical-chain availability |
| Governed configuration | Timelock, exact operations, parameter bounds, asset/route admission and guardian pause limits | Multisig diligence, honest price truth, suitable strategy and safe admitted destinations |
| Custody evolution | Typed local release/import, identities, epochs, replay protection and measured token deltas | Provider backing/finality, remote implementation/admin powers, token equivalence and external venue liveness |

The local immutable rules do not prove safety of arbitrary external custodians.
A malicious approved provider can consume the exact approved principal and
return a receipt without funding a destination. Pinning its code prevents an
unreviewed replacement; it does not make initially malicious code honest.
No generic rescue, unrestricted call, proxy or owner withdrawal is proposed.

Keep **80/10/5/5 immutable**. Holders cannot redeem to reject new economics, and
variable percentages introduce policy epochs, delayed remote-fee boundaries,
dust transitions and governance extraction risk. A minimum combined owner share
would not protect the individual/equal-collective split. Separately funded future
incentives are conceptually possible without debiting existing rights, but are
not implemented or approved by this review.

## Permanent destination capacity: bounded repair

Baseline `reservePool` bound identity without reserving one of four slots. Other
arrivals could fill the destination before an earlier reserved import. The
implemented repair uses the existing bounded `buckets` array as an idempotent set:
validate pool ownership; find an existing bucket before checking capacity;
register a new identity once; then commit the pool mapping atomically.

Reservations are permanent, including after cancellation, departure or timeout.
Multiple pool aliases for the same bucket use one slot. A reservation alone has
`None` status, zero shares and no principal; consumers must skip it before price
or pool reads. All 1,000 NFTs can still share one existing active identity.
`bucketCount` therefore means admitted/historical identities, not funded pools.

This fixes local admission only. Source governance still must establish the
reviewed destination's confirmed reservation before departure; the source does
not authenticate a remote reservation proof. Arbitrary IDs reserved by malicious
governance can exhaust capacity. There is deliberately no unsafe slot recycling.

## Different-pair migration: proposed composition epochs

Do not remove the Vault's pair checks. Current `homeToken0/1` identifies remote
reward paths, canonical liabilities and the immutable creator-payment inbox.
Replacing those addresses would relabel old obligations; a new Vault alone cannot
replace the original immutable NFT/Rewards binding.

The smallest coherent extension would preserve home identity, NFT/share ledgers
and existing asset indexes while introducing an authenticated **custody composition
epoch**. Every principal proposal/message/ACK and relevant reward source must bind
that epoch. Admission history must be bounded without discarding obligations.

| Value category | Conversion rule |
| --- | --- |
| Migrating principal, attributed idle, designated compound capital | May convert through exact typed routes into fixed custody, under one budget. |
| Owner/collective allocated or claimable fees | Keep in their historical currency and ledger; do not convert or resplit. |
| Royalties | Separate funded ledger; unaffected by LP migration. |
| Buyback reserves | Separate obligation and reviewed execution path; cannot subsidize migration. |
| Donations and other buckets' balances | Excluded from migrating value and loss-floor checks. |
| Late creator receipts / unharvested or in-flight fees | Retain authenticated old intake paths and explicit processing semantics; never erase or relabel them. |

Prefer an atomic source-side same-chain conversion first: snapshot bucket,
shares, epoch, routes, custody and a fresh trusted price vector; settle old local
receipts/dust and old remote funding obligations; close the old position; convert
principal through an immutable typed helper; redeploy; verify total outcome;
otherwise revert. Fixed recipients, exact temporary approvals and measured
deltas are mandatory. The user-contribution Entry is not a principal converter.

Old creator inboxes must remain available for late receipts. Their old-currency
5% compound amounts need an explicit bounded conversion/retention policy after
the pair changes. New currencies need append-only inbox/asset admission. Remote
lifetime counters must cover all historical currencies, not merely the current
pair. Version-3 two-currency principal messages cannot represent this design
without a new authenticated message/accounting version.

The Vault/Migration currently have little runtime headroom. Typed immutable
helpers can contain route execution, but cannot solve missing ledger semantics.
Do not trade away checks or raise standard EVM limits to fit this feature.

## Accepted migration execution budget

The user chose **at most 3% aggregate execution loss per migration, gas separate**.
Activation/top-ups retain the **1%** original-input budget. The current candidate
enforces the 3% floor for atomic same-ordered-pair `movePool` and parked `resume`,
using one pre-callback price vector and exact designated compounding. The floor
covers retained LP plus attributed idle, with the existing 5% idle cap. It does
not yet cover arbitrary conversion, asynchronous bridging, rebalancing or an
earlier parking close. See [implemented scope](MIGRATION_SAFETY.md).

For an atomic move, compare attributed principal before/after using one fresh
trusted price vector. Conversion fees, slippage, bridge charges deducted from
principal if supported, and redeployment costs consume the same budget. Track
deployed and attributed idle separately; idle retained in custody is not lost,
but acceptable deployment/idle proportions require explicit guards. An operator
must never treat three separate 3% leg allowances as one 3% transaction limit.

Asynchronous delivery introduces market movement between close and arrival.
Define source valuation, nominal backing, quote expiry, conversion minima and
retry custody before claiming an end-to-end bound. An oracle-controlled USD
check is not independent protection from governance-controlled false prices.
Ten maximum-loss moves retain only about **73.74%** of starting value before
market moves. Record cumulative costs and migration frequency; an arbitrary
cumulative hard cap is not inferred from approval of a per-move limit.

<a id="canonical-chain-continuity-requires-a-separate-decision"></a>

## Controlled canonical migration

**Decision, 2026-10-17:** the user selected controlled whole-protocol migration
while the original chain still works. Post-halt recovery is deferred. The
[canonical migration design](CANONICAL_MIGRATION_DESIGN.md) specifies the proposed
transition; current contracts do not implement it. This support must be built
and qualified before sealing, not treated as a later bridge-provider setting.
The cross-chain proof/finality model remains an explicit qualification decision.

The alternatives considered were:

1. Keep the fixed home chain: least extra authority, but permanent chain loss
   leaves canonical ownership and claims inaccessible.
2. Planned canonical transfer while the source operates: requires a purpose-built
   freeze/export protocol for ownership, immutable traits, shares, both ledgers,
   fractions, backed reserves and in-flight obligations; one finalized successor
   epoch, disabled source rights and replay prevention. Not implemented.
3. Recovery after irreversible halt: needs an explicit checkpoint/finality or
   recovery authority. A snapshot cannot prove the old chain will never resume,
   and a second NFT collection does not revoke the first. Not implemented.

Do not silently select an emergency administrator or claim that a mirror NFT
solves this. The fixed VRF coordinator has a related continuity boundary: an
unfulfilled early mint blocks ordered reveal and later activation. Any fallback
must preserve randomness fairness and prevent administrator rerolls.

## Operating and release boundary

Read-only projections and Anvil keeper rehearsals do not qualify real wallet
transactions, market feeds, real routes, bridge funding, replacement-host recovery
or canonical disaster recovery. Frontend IDs must retain exact uint256 strings;
wallet preparation must pin chain/account/targets and handle stale drafts and
canonical receipts independently of an API response.

Same-pair supported flows remain distinct from the conversion and canonical
relocation designs above. Real bridging starts disabled. Independent audit,
target-chain services/gas, authority selection and operating qualification remain
required. Current release decision: **NOT APPROVED**.
