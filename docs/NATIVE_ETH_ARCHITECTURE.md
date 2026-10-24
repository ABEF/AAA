**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Native ETH architecture: V2 contract candidate

2026-10-24. The user requires robustness and efficiency over preserving existing
code. The selected venue is native ETH/ZZZ. The local native V2 contract candidate
now preserves ETH through contributions, LP settlement, fee/reward accounting,
maintenance, custody recovery and versioned same-chain canonical handoff. Keep
wrapping only for an operation that actually uses WETH. This candidate is
**undeployed and not approved for production**; scoped verification and remaining
boundaries are recorded in the [native-port report](../reports/native-eth-port/VERIFICATION.md).

Atomic native ETH/WETH pool conversion is not implemented and the same-pair guard
rejects it. Legacy V1 canonical import is rejected. Typed v4 fee/input conversion,
the native website manifest, actual backend/inventory/history qualification,
routes/feeds/providers and
native target-chain operating/fork qualification remain open. Do not treat the
old WETH checkpoint or its backend profiles as evidence for this new candidate.
The API/keeper candidate now binds explicit accounting versions, including
predecessor profiles; that code does not qualify actual deployed services.

## Asset identity and backing

- Native currency is `address(0)`, with 18 decimals and its own reviewed USD feed.
  It is not relabeled WETH. Future WETH is a distinct ERC20, with a separately
  reviewed proxy policy whenever wrapping/unwrapping is actually required.
- Vault principal/idle, FeeController compound/buyback/dust, Rewards liabilities
  and royalty liabilities are separate native balances in separate custody domains.
  An ETH balance alone is never sufficient evidence of a new contribution/income.
- Payable ingress must match the exact declared native amount once per operation.
  ERC20 ingress requires zero unrelated ETH. Forced ETH, prefunds and receipts from
  unrelated operations must not subsidize principal, execution loss or liabilities.
- Native sends use checks/effects/interactions, existing reentrancy/lifecycle guards
  and exact source deltas. Rejecting recipient/callback failures revert the complete
  operation. No arbitrary sweep, automatic resend or relaxed loss budget.

## Required end-to-end flows

| Flow | Native requirement |
| --- | --- |
| ETH activation/growth | Entry forwards exact ETH to Vault; Vault funds typed v4 settlement directly. No WETH allowance, deposit or withdraw. |
| ZZZ activation/growth | Exact ZZZ approval; typed ZZZ/native-ETH swap; actual LP and99% marginal contribution guard. |
| Other input currencies | Reviewed typed routes only. A route that requires WETH may wrap/unwrap at its boundary; its failure cannot block native LP recovery or unrelated inputs. |
| Fee collection | Real ETH credits enter FeeController directly and receive80/10/5/5 classification. No keeper conversion is needed for already-native holder fees. |
| Rewards | Native owner/collective indices preserve old-weight accrual, fractions and transfers; direct native receipts coexist with previously converted native credits. |
| ZZZ fee conversion | User reconfirmed the1% limit on2026-10-24; gas stays separate. The selected approximately1.101% venue needs a cheaper route at reference prices; do not invent one or loosen the cap. |
| Compound/buyback | Spend only the classified5% reserve through typed native settlement. Keeper gas is external. |
| Fee-tier move | Atomic same-native-pair close/redeploy, actual destination depth and one captured starting-price maintenance budget (3% default). |
| ETH/WETH pool move | Not implemented atomically: the actual-currency pair guard rejects ETH/WETH substitution. A future boundary needs explicit exact1:1 reviewed wrapping, distinct asset/idle accounting and historical reserve rights; no implicit normalization. |
| Normal custody exit | Close actual LP, preserve accrued fees, enforce stricter swap and aggregate floors, consolidate to ZZZ and send only approved principal. |
| Raw custody exit | Close and send native ETH plus ZZZ without calling WETH, swapping or reading USD prices. Exact reviewed raw minima; no USD guarantee. |
| Recovery/local completion | Actual ETH/token funding, declared units and actual LP backing; no synthetic return receipt. |
| Whole-collection handoff | Carry native principal, fees, indices/fractions, reserves and quarantines exactly once. Native asset zero must not be confused with missing data. |

## Review and qualification

Inventory all payable ABI/call-value changes, constructor casts, zero-address
sentinels, receives/callbacks, canonical funding/protection slots, historical
currencies and original-source contribution contexts. Update API/indexer/keeper
configuration and unsigned preparation without widening the Anvil-only signer.
Never silently interpret the old WETH-accounting profile as this new profile.

Required focused tests include exact/extra/missing ETH, reverted LP/swap/claim,
forced ETH and prefunds, recipient rejection/reentrancy, fee/compound separation,
membership timing, transfer/unclaimed rights, native/wrapped pool changes, wrapper
failure with successful raw native exit, canonical abort/backing and code sizes.
Old evidence remains source-bound; changing these paths justifies fresh affected
coverage. Do not repeat unchanged suites merely to inflate counts.

Current candidate: [native-port evidence](../reports/native-eth-port/VERIFICATION.md).
The earlier [hookless-pool evidence](../reports/hookless-pool/VERIFICATION.md)
retains its WETH source/block scope. No old result silently qualifies native V2.

## Adversarial design review - 2026-10-24

The earlier [design audit](../reports/daily-security-20261024/REVIEW.md) identified
the boundaries below before native implementation. Its historical claims are
unchanged. The current code addresses the contract boundaries; fresh affected
evidence is recorded separately. Website profile integration, actual backend/services, target-chain
qualification and independent review remain release gates. Never combine
incompatible old and new modules.

| Boundary | Required design and implementation | Native V2 implementation or remaining boundary |
| --- | --- | --- |
| Native versus missing identity | Zero is an explicitly admitted currency, never an owner, contract target or configured ZZZ. Raw ETH cannot be reported as `sentZZZ` when ZZZ is unset. | Native Oracle/ActivationAssets admission, exact pool identities, Entry and custody checks; API codec/profile qualification remains open. |
| Native fee accrual | Publish both individual-share and equal-collective indices; preserve fractions and converted credits without re-earning them. Checkpoint old weights before new eligibility/shares. | Rewards native checkpoints, funded payable credits, claimable views and canonical records now follow the token accounting rules. |
| Historical reserves and NAV | Include native compound/dust and all 33 currencies; do not hide missing backing as zero. | MigrationBudget historical valuation and Membership dust settlement include native. An atomic ETH/WETH move is still rejected, rather than silently normalized. |
| Typed funding | Validate exact native value once per ingress, exclude incoming value from starting baselines, reject ETH on ERC20 operations and preserve prefunds. | Entry, Vault, LiquidityManager, Fees/Rewards credits and Migration funding use actual native budgets. The API/keeper candidate binds native V2 semantics; the website manifest and actual services remain unqualified. |
| Two-stage canonical funding | Transfer backing first, then acknowledge with zero value; restore through the reverse protocol. | Vault/Fees companions forward already-received ETH, protect prefunds and reject duplicate acceptance. Handoff checks actual transfer deltas. |
| Separate backing domains | Keep native Vault principal, Fees reserves/quarantine, Rewards and royalties independently backed, exactly once. | Native is included in finite Vault/Fees inventories; Rewards retains indexed and converted native liabilities in its own domain. |
| Receiver cutoff/protection | Native slot0 cannot also be protected/exported as native slot2. | Native inboxes require wrapper zero, use slot0 and reject a positive duplicate slot2 protection. Explicit legacy ERC20 wrapper inboxes retain separate native quarantine. |
| Transitive wrapper independence | Native close, harvest, parking, raw exit and recovery must not call WETH or its policy. | Native Registry bindings omit WETH; manager returns ETH; Vault/Fees/Migration preserve ETH. Actual target-chain behavior and operating failure rehearsals remain open. |
| Versioned state and history | Bind schema/accounting semantics and keep historical WETH epochs distinct. | Native V2 handoffs require matching `SCHEMA`; legacy V1 import is rejected. The separate API/keeper profile candidate identifies deployment/predecessor versions; actual lineage history and service qualification remain open. |
| Backend and wallet boundary | Accept native asset zero but reject zero targets; use native pricing and exact typed call values; keep gas separate and approvals ERC20-only. | Explicit native API/keeper profiles exist as a candidate. The website manifest, actual inventory/history/services and independent qualification remain open. Public deployment is null; signer remains Anvil-only. |
| Claims and callbacks | Effects precede ETH payment; each batch leg rechecks owner; recipient rejection reverts atomically. | Rewards preserves its lifecycle/reentrancy/current-owner guards and unclaimed NFT rights. Existing ClaimRouter and royalty custody remain separate. |

Source companion donations are not a new captured backing domain. Capture does
not write a prefund baseline for every currency: anyone could otherwise inflate
freeze gas by sending one raw unit of each admitted asset. On abort, the immutable
handoff verifies the exact returned balance increase before restoration forwards
exactly that amount, preserving unrelated companion funds. Destination import
still records its independent prefund baseline and rejects unfunded acceptance.
An imported successor later acting as a source uses the same source-return rule.

### Donations and actual receipts

Typed LP operations can isolate the expected native amount from prefunds and
unexpected/forced ETH; unexpected funds cannot subsidize principal or execution
loss. A plain balance-based royalty or external-revenue inbox cannot distinguish
forced ETH from a donation. Keep its documented prefund/quarantine/cohort rules:
actual eligible receipts are allocated by those rules, not by an invented proof
of sender or marketplace origin. The ETH balance alone never proves a specific
trade, royalty agreement or typed LP execution occurred.

### Focused native acceptance boundaries

Require actual source-bound evidence for: missing/extra value and existing
prefunds; partial settlement and rollback; receipt classification; native owner
and collective fractions across activation/transfer/top-up; historical compound
after ETH/WETH moves; partial canonical funding and abort; zero-asset identity
and unconfigured ZZZ; duplicate receiver protection; old/new schema rejection;
recipient callbacks; and successful raw native exit/recovery with a deliberately
failed wrapper. Test current native prices and metadata from actual attributed LP.
Mocked API traces do not replace the typed on-chain cases. Prior WETH-checkpoint
passes do not close these native implementation requirements.
