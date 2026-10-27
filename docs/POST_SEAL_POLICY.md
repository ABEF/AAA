# Post-seal configuration and public-chain rehearsals

Sealing fixes core implementations, bindings and the one ZZZ identity. Immediate
governance can change supported policy within guards, not rewrite NFT rights.
The fresh source is [accounting4/custody3/canonical V5](POSITION_V4.md), undeployed
and **NOT APPROVED**. The [sole Todo](../TODO.md#task-post-seal-configuration)
owns qualification; the [operator manual](OPERATOR_MANUAL.md) owns exact procedures.

## Configuration boundary

| Category | What remains configurable | Limit |
| --- | --- | --- |
| Governance | Direct governance wallet and proposal/acceptance handover, without delay. | No generic executor/timelock; guardian/keeper and immutable mint recipient do not rotate automatically. Lost governance has no hidden administrator rescue. |
| Routine LP operation | Roles, pause, supported range/orientation, triggers, cooldowns, approved +/-25/50% keeper selection and operating ceilings. | Applies only before `lpExitStarted`. Ordinary unpause cannot undo collective exit. |
| Inputs | Enable/disable/re-enable native ETH and the fixed ZZZ with reviewed append-only source policies. | No third input or post-seal replacement ZZZ. Source, Buyback and settlement identities must match before seal. |
| LP pools | Admit initialized pinned static hookless native ETH/fixedZZZ fee tiers; one contribution pool at a time. | No generic ERC20/WETH LP admission or arbitrary different-pair movement. Movement and deposit/route cutover are separate actions. |
| Conversion venues | Reviewed typed single-hop v3/v4 routes for contributions or already-earned LP/royalty balances. | Conversion admission does not add an LP currency or input. Explicit wrapper-dependent routes still need wrapper qualification. |
| Pricing | Reviewed two-source USD policies, source runtimes/independence, ages and0-500bps agreement setting; selected tolerance300bps. Governed sequencer-source replacement. | Both feeds must pass; no peg/spot/missing-source fallback. Captured operation prices/policy cannot be replaced mid-call. |
| Loss policy | Contribution2%, conversion1%, maintenance3% defaults, each governance ceiling10%; separate converter settings. | Stronger caller/venue minima and separate gas remain. Raw collective principal return uses raw minima, not a3% USD guarantee. |
| Randomness requests | Future confirmations3-200 and callback gas200,000-10,000,000 via `setRandomnessRequestSettings`. | Coordinator, key/lane, subscription and payment mode fixed; no reroll/repair of old requests. Actual provider bounds may be narrower. |
| Buyback | `setOperatingTradeUSD` from zero through immutable `maxTradeUSD`; zero stops buys before price/reserve reads. | Fixed ZZZ target; no administrator withdrawal of reserves or automatic keeper salary. |
| Royalties | Admit reviewed marketplace currencies and configure guarded conversion. | Actual received receipts and original per-NFT rights remain; no external royalty-custody exit/drain. |
| Services | Qualified RPC/hosting/API/keeper settings with preserved deployment and pending records. | A config edit does not change deployed code, safely migrate a journal or qualify a new source profile. |

Adding/changing a route or feed is security-sensitive despite immediate governance.
Review actual caller, bounds, events, dependency powers, pending transactions and
stop/restart behavior. Source-code configuration does not qualify live feeds,
routes, VRF, authorities or services. Historical
[post-seal-control evidence](../reports/post-seal-controls/VERIFICATION.md) retains
its own source scope.

The selected pool's observed approximately1.101% swap fee cannot qualify a
full-balance ZZZ conversion at the default1% ceiling at reference prices. Require
a cheaper reviewed route or leave balances backed and report unavailable. Do not
silently widen policy or use spot to manufacture independent valuation.

## Irreversible exit boundary

Governance can pause and start [collective holder return](HOLDER_COLLECTIVE_EXIT.md).
The permanent lock prevents new mint/principal work even after unpause. Actual
ETH/ZZZ close proceeds, attributed idle and pending compound become holder
principal by frozen shares. Existing LP rewards, royalties and buyback reserves
remain classified separately; future NFT royalties continue.

There is no chosen custody recipient, all-ZZZ exit, full-balance royalty drain,
external return/completion ingress, bridge or generic sweep. Failed recipient
payouts remain backed and can use current-owner fallback. Same-chain canonical
replacement is available only before LP exit starts; its V5 importer cannot
carry terminal holder-principal accounting or reopen an exited deployment.

## Native implementation and profile qualification

Native ETH remains the actual zero currency through LP, fees, principal and
payouts. Only explicit conversion routes may use WETH. Current services/inventory
must select accounting4, custody3, fee1, governance2, pricing2, routing2, reviewed
Entry1 and exact holder-exit V5 schema/runtime/parent pins. Position length alone
does not identify a profile. Historical accounting1/2/3 deployments and journals
keep their own meanings. The served accounting3 poplint artifact is not a
qualified accounting4 integration; public deployment stays null and browser
signing remains Anvil-only.

[Dual-source prices and actual LP](PRICE_SECURITY.md) are implemented, but actual
independent ETH/ZZZ feed pairs and routes remain unqualified. Feed failure stops
affected price-dependent work. Funded claims and raw collective closes retain
their own dependency/minimum rules; neither promises recovery through a broken
token or venue. [Native boundary](NATIVE_ETH_ARCHITECTURE.md).

## Testing with real funds on Robinhood

A future authorized rehearsal needs a separate clearly named deployment,
disposable funds, exact reviewed code/configuration and per-operation/campaign
limits. Preserve production economics when qualifying production behavior;
a local$1-minimum build does not verify the$100 production floor. Direct mint
evidence does not qualify the required OpenSea primary-mint path.

Record exact chain, contracts/runtimes, assets/venues, feed/provider policies,
authorities and signer scope before public execution. Simulate exact calldata;
retain receipts, balance changes and liability assertions. Genuine venue fees,
funded distribution tests and actual marketplace royalty receipt tests are
different evidence. No public deployment/signing/transaction is authorized here.

At the end of an authorized disposable campaign:

1. Stop new mints/contributions; reconcile pending transactions and preserve journals.
2. If appropriate, govern the irreversible collective exit, close buckets,
   apportion actual ETH/ZZZ and distribute to current test NFT owners. There is
   no custody-wallet shortcut, withdrawal reset or3% promise on raw return.
3. Claim earned rewards as current owners; account separately for pending
   principal, royalties, buyback reserve, rounding dust, mint proceeds and gas.
   Compounding belongs in returned principal, not an administrator sweep.
4. Archive manifests, receipts, remaining liabilities and final state. Removing
   rehearsal addresses from services does not erase chain or marketplace history.
5. Use a fresh reviewed deployment for the final collection. Test NFTs do not
   become final NFTs automatically, and spent gas/fees/losses are not refundable.

Do not include unrelated public holders in a disposable rehearsal. Existing NFT
and unpaid rights survive stopping services. Actual target-chain operating,
receiver-failure/recovery and gas rehearsals plus independent audit/remediation
remain [release requirements](RELEASE_CHECKLIST.md).
