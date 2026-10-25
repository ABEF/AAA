# Ownership, economic rights, authority and handoff review

## Scope and assurance boundary

This is a fresh manual call-path review of the current committed candidate
`e32e9669d79bc3c576175f51f72d8277f6fa48f9`, whose production Solidity remains
the `35007db` source. It is not a claim that every compiler path or adversarial
schedule is proven safe. Source hashes for this slice are in
[the binding manifest](rights-source-bindings.json). No code, deployed state,
Anvil journal, website or service was changed by this slice. No unchanged suite
was rerun, and historical tests are not counted as fresh results.

The review read AccessController, NFT/metadata identity, Rewards, Membership,
FeeController, RoyaltyRewards, ClaimRouter, Buyback, Migration/CustodyValidation,
CanonicalHandoff and all four domain codecs, the shared canonical/module bases,
converter implementation/subclasses, exact-asset helpers and fixed artwork
catalogue. It traced actual cross-contract callers, not just function signatures.
Principal execution, live dependencies, services and fresh static analysis are
separate slices owned by the parent review.

## Economic and ownership traces

| Boundary | Actual code path and reviewed protection | Disposition |
| --- | --- | --- |
| Ownership and old-owner claims | NFT inherits the pinned ERC-721 implementation. Both reward ledgers authenticate `ownerOf(id)` at payout; ERC-721 approval alone is not claim authority. Accrued balances/fractions use NFT ID rather than wallet address. | No new former-owner claim or approval-based theft path confirmed. |
| Batch claim callbacks | ClaimRouter prevalidates owner/duplicates, then checks owner again before each operation. Each ledger repeats ownership verification and debits before payout. A previous callback that transfers a selected NFT causes a later old-owner operation to revert the whole batch. | No double claim confirmed; transfer and any callback actions roll back with a failed atomic batch. |
| Single-claim transfer callback | A current owner can receive one debited claim, transfer the NFT in its callback, and permit the new owner to exercise remaining rights. The old claimed amount is already zeroed; fractions and the other ledger remain attached to the same NFT. | Intentional current-ownership ordering, not a duplicate payout. Secondary buyers must inspect execution-time rights; a seller can claim before sale. |
| Individual LP rewards | Vault checkpoints old owner shares before increases. Rewards uses bucket owner indexes, NFT share quantities and carried 1e36 fractions. Bucket migration does not replace the canonical NFT share ledger. | Source path preserves existing earned units and excludes earlier indexed receipts from newly issued shares. Principal/share issuance is audited separately. |
| Collective LP rewards | Membership checkpoints the inactive NFT before setting its one permanent eligible share. Rarity, top-ups and later transfers do not add collective weight. Funded residual settlement precedes joining. | Dormant NFTs do not dilute the collective denominator. No holder burn/deactivation path exists. |
| 80/10/5/5 | FeeController pulls the declared actual local fee, then allocates whole groups of 20 raw units as 16/2/1/1. At membership/movement barriers up to 19 carried raw units go to incumbent individual rewards. | Preserved documented rounding exception; do not claim an exact split at every tiny receipt. Donations do not become harvested LP fees. |
| Royalty eligibility | Immutable revealed rarity determines1/2/3. Activation assigns weight once. Healthy currencies checkpoint before joining; failed/custodied currency keeps its earlier eligibility prefix and recovery baseline. `_sync` allocates old unseen receipts before enrolling waiting NFTs. | No retroactive royalty entitlement or rarity-driven LP weighting confirmed. Current API custody fix does not change these on-chain entitlements. |
| Royalty claims/backing | `_sync` requires actual balance at least accounted; claim checkpoints, clears amount and debits liability/accounted before payout. Exact ERC-20 transfer checks and post-callback backing validation remain. | No unbacked or repeated claim confirmed within reviewed conventional-token assumptions. Failed currency/recipient may block that currency. |
| LP/royalty conversion | Separate instances bind separate immutable ledgers. Sorted IDs prevent duplicate selection. Only earned whole units are debited; exact input/output balances and reset allowances are checked. Cumulative rounding credits every output wei back to the same selected NFTs/components. | Conversion is denomination change, not new revenue or collective redistribution. Native royalty sync runs before direct conversion credit, preventing deferred-native retroactive credit. |
| Buyback | Reserve release is module-authenticated. Spend uses upper USD bound rounded upward and operating/immutable limits. Target is the fixed ZZZ. Actual ZZZ balance increase, `burn(acquired)` and matching total-supply decrease are required. | No arbitrary reserve recipient or retargeting path. Real ZZZ burn ABI/semantics and actual route economics remain unqualified. |

## Governance and custody

AccessController's direct governance wallet has accepted configuration power;
there is no timelock queue or generic execution contract. `canConfigure` allows
only bootstrap before sealing and selected governance in operating state after
sealing. The module list is fixed, distinct and bound to this controller at seal;
fixed source/exit ZZZ identities must match. Governance handover is two-step;
proposal alone does not replace the current wallet. Role events do not add power.

Guardians may pause; only governance/bootstrap can unpause. Claims/transfers can
continue during ordinary pause, but importing/frozen/retired canonical states
have separate guards. Preparation blocks new operating work/configuration while
permitted original drains/claims remain distinct. The shared `economic`,
`canonicalAccounting` and `operating` modifiers also check state after callbacks,
preventing a financial operation from silently finishing in a different canonical
lifecycle. `setPaused` itself can still emit changes on retired controllers;
that does not override terminal lifecycle or revive module authorization.

Normal custody exit requires an exact source snapshot, paused governance,
recipient code commitment, review hash, deadline and captured loss floor. It
converts attributed principal to fixed ZZZ and verifies exact transfer deltas.
Raw exit deliberately avoids conversion/oracle floor and uses approved raw minima.
Both paths preserve NFT shares but put actual funds under a trusted recipient.
Neither the source nor a review hash can force that recipient to preserve or
return assets. This accepted authority is a genuine withdrawal path for governance,
not proof of immutable capital custody.

`completeLocal` only closes a sent plan after actual caller funding and physical
destination LP with unchanged NFT shares; its original floor cannot be weakened
by later policy changes. `recover` requires every originally sent source asset,
not a fabricated remote valuation or timeout. A sent plan cannot be cancelled to
erase the obligation. Other parties may fully fund a recovery; this donates
backing rather than authorizing a payout to the caller. Same-chain direct pool
moves reject differing actual currencies; externally converting ETH to WETH or
issuer tokens remains a separately reviewed custody operation.

## Complete same-chain handoff

| Stage | Cross-contract trace and safety boundary |
| --- | --- |
| Prepare | An unused destination imports only after binding a sealed source and matching local schema. Source notices bind a sealed inert importer and deployment commitment. These are trusted reviewed implementations, not proof that new code is safe. |
| Freeze | Source state becomes frozen before external balance observations. NFT records must all be revealed; Vault buckets must be parked without custody plans; royalty custody must be resolved. All six domains capture before settlement. |
| Settle/export | Fixed domain order preserves captured cutoffs. No funding/import can precede complete source snapshot. Source-derived rows, row indexes and rolling roots are authoritative; governance cannot supply arbitrary accounting rows. |
| Import | Each supplied row must equal the frozen source's actual export. Per-domain cursors, IDs, inventory bounds, shares/fractions and exact layouts are checked. Dependency order mistakes revert rather than partially advance a cursor. |
| Fund | Source/destination backing asset and amount must match. Source and destination exact balance delta, per-row funding flags and companion forwarding prevent old destination prefunds replacing source funding. Distinct custody domains stay classified. |
| Commit | Governance retires source and activates destination atomically. Destination validates all imported domains and actual backing. A failed activation reverts retirement. Source states3/4 cannot return to operation. |
| Abort | Source cancels the unused destination, then returns only rows actually funded, once. Exact return deltas and canonicalRestore re-forwarding restore source-domain backing. Source resumes only after every sent row returns and all domains validate. Cancelled destination remains inert. |
| Late royalties | Retired source forwards remaining admitted ETH/ERC-20 receipts to its fixed immediate successor. Old snapshot backing was already sent, so it is not forwarded twice. Forwarding through successive retired deployments preserves the single successor chain. |

Importing NFT ownership deliberately omits receiver callbacks. A smart-contract
owner may therefore own the replacement NFT without supporting that address or
release. This is an existing explicit holder/escrow-preflight release gate, not
proof that every migrated contract holder can use its replacement. Historical
accounting2/remote layouts are not implicitly accepted as current localV4 rows.

## Open cases and operational findings

No new unprivileged theft, duplicate-claim, share/royalty override or terminal-state
replay exploit was confirmed in these inspected paths. This does not close the
independent audit, live-service or final frozen release suite.

1. **Real fixed-ZZZ burn compatibility:** `ZZZBuyback.execute` requires callable
   `burn(uint256)` that reduces both its balance and total supply exactly. An
   ERC-20 or pool address alone does not establish that. Qualify actual code and
   authority/upgradability before promising automatic burns; a failure leaves
   classified buyback reserves rather than paying the operator.
2. **Unadmitted late royalty currencies:** `forwardLate` requires source
   `isAsset(asset)`. Retired governance cannot admit a new currency because
   `canConfigure` is false. An arbitrary previously unadmitted ERC-20 sent to an
   old receiver is therefore outside recovery support. Existing admitted ETH/
   token late receipts work. Do not promise universal recovery; future policy
   requires explicit review rather than a generic administrator sweep.
3. **Freeze liveness:** an outstanding VRF result blocks ordered reveal and
   whole-collection capture. One unreadable admitted royalty token, unresolved
   custody or broken parked-pool binding can also block capture/validation.
   These protect truthful export/backing but require provider/token/custody
   recovery; no administrator-selected traits or liability write-off exists.
4. **Worst-state gas:** up to16 optional royalty currencies receive bounded
   250,000-gas synchronization calls on activation; other loops span at most33 LP
   assets/four historical buckets. A smaller cold-activation benchmark does not
   qualify this composed maximum or target-chain affordability. Avoid treating
   each bounded loop as proof that all simultaneous maxima fit.
5. **Current Todo wording:** task `activation-quotes` still described1% default
   contribution twice; current policy is2%. Task `authorities-prices` retained
   “template executor is open” despite direct governance2 removing the executor.
   Parent was notified for the central documentation correction; historical
   dated evidence must not be silently rewritten.

The root review owns severity/prioritization, current source-bound static analysis,
any resulting fixes, central Todo/operator changes and publication. No public
transaction, deployment, service operation or new economic decision is implied.
