# NFT, royalty, canonical and terminal-rights behavior follow-up

## Confirmed implementation defect: empty artwork root could be sealed forever

**Severity: medium; irreversible operator setup error, not an outsider privilege escalation.** `ZZZNFT` deliberately accepts an empty constructor base so bootstrap can populate it later. `setBaseURI` is one-time and permanently unavailable after seal. The earlier actual `Access.seal` checked the module graph, fixed token/exit identity, recipient and canonical randomness, but did not reject an empty artwork root. A mistaken raw seal could therefore erase bootstrap while revealed token metadata constructed relative artwork paths with no immutable content root.

The new regression uses actual current AccessController, ProtocolPolicy, NFT, metadata renderer and controller-created factories. Unused modules and VRF are explicit typed binding fixtures; this is not a complete market or operating rehearsal. The baseline EVM call actually emitted `SystemSealed` with `artworkBaseURI()==""`; the expected rejection was missing. Two companion positive/unauthorized cases passed at that source.

The correction adds a typed **nonempty artwork root check before irreversible sealing**. Empty-constructor setup remains possible. The negative case now proves the rejection preserves bootstrap, then fills the root, seals successfully and verifies the root cannot subsequently be replaced. Constructor-populated roots still seal; an unauthorized keeper can neither populate the empty root nor seal.

This does not validate CID syntax, content completeness, availability, marketplace retrieval or actual immutable publication. Those remain separate reviewed release inputs. No ownership, balance, reward, principal, runtime capability version, ABI or storage field changes.

## Confirmed verification weakness: recovery fuzz allowed an unexplained remainder

`OriginalCurrencyRoyaltyTest.testFuzzRecoveredSourceClaimsNeverExceedFundedUnits` exercised fresh exact-unit **governance recovery** but asserted only `paid<=received` and retained backing equal to the unpaid liability. A permanently unclaimable positive remainder would satisfy those assertions. This was a test-quality defect; no production remainder was reproduced.

The one adapted method now requires:

- A nonzero receipt and meaningful three-NFT cohort with weights 1/2/3.
- The entire receipt is explicitly unallocated before reviewed recovery, then becomes a funded liability.
- Independent six-ticket quotient/remainder arithmetic matches each NFT's payout.
- Actual recipient balance deltas equal those payouts.
- Total payout equals every received unit.
- Ledger token balance, accounted value, liability and unallocated balance all drain to zero.
- Repeated claims pay zero.

Exactly this changed method passes its configured **1,000 fuzz inputs**. That is one adapted method, not 1,000 different features. The unrelated recovery/royalty suites were not rerun.

## Confirmed stale fixture: canonical preparation did not reach its test bodies

The first selected positive `CanonicalPreparation` case failed in `setUp`, before its test body. Source reconciliation exposed an obsolete two-ERC20 fixture: it used the old accounting transport, called fresh `Rewards.addAsset` twice and attempted admission before declaring the fixed ZZZ. Fresh Rewards correctly rejects that setup. Merely filling its empty artwork root was therefore insufficient; this failure is not attributed to the new root guard.

The fixture now uses the actual native Vault, ETH plus one 18-decimal ZZZ, fixed identity before the sole ERC20 reward admission, matching buyback target, exact native call value and explicit balances. Dollar-valued share expectations remain meaningful. A deterministic native venue and a small explicit read-only execution-identity adapter preserve the existing geometry seam; Oracle/ContributionPricing, custody, royalty, fee/reward, lifecycle and callback bodies remain real. No production source or safeguard is weakened. Strategy geometry/spot checks, venue behavior, feed values and VRF remain controlled fixtures: these cases do not establish actual Uniswap execution, independent markets or provider qualification.

All **seven affected intended cases now pass**:

- Exact governance notice/hash and cancellation authority.
- Canonical-chain and nonempty-notice rejection.
- Nonzero activation, LP fee claims, royalty claims, NFT transfers and pending reveal during preparation.
- Configuration stop with separate guardian/governance pause behavior.
- NFT receiver callback preparation rolls the entire mint/request/ownership back.
- Final treasury callback preparation also rolls the whole mint back.
- Nonzero final harvest and raw governance parking still work with stale fixture prices, preserving exact principal and shares.

`OperatorControls` also now declares a nonempty fixture artwork root; its one selected affected stop/re-enable case passes with failing price/token/venue dependencies. Other empty-root tests using deliberately permissive `MockAccess` were not silently relabelled as real-controller sealing evidence.

## Actual behavior and interference cases reviewed

| Operation / source | Relevant case | Source-grounded outcome / limitation |
| --- | --- | --- |
| NFT `setMintEnd` → royalty `setMintEnd` | Old sale ended, opening finalized, zero/past end, shorter/longer future end | Rejects after the previous sale closes or opening finalizes; only a future end is accepted. The one-hour opening is relative to the governed official end, distinct from full-day reporting. No silent extension after closing. |
| NFT `increaseRoyaltyAssetCapacity` | Repeated/decreased capacity, over64, gas growth | Only increasing reviewed capacity up to64; currencies never disappear. A permitted engineering limit is not gas feasibility, and a malicious admitted token can still break its own reads/transfers. |
| NFT `addRoyaltyAsset` → royalty `addAsset` | Unsupported currency prefund, before/after opening, read failure | Admission reads actual balance; existing prefunds become reviewed unallocated, not earned current-cohort income. Post-opening admission does not rewrite the original cutoff. A failed token read reverts its admission atomically. |
| Royalty activation/sync | Optional currency unreadable while another NFT activates | Isolated currency synchronization may defer that NFT; the earlier eligible cohort retains unseen receipts until recovery, then newcomers join future receipts. No new royalty currency can assign older earned balances to a newcomer. Currency-specific continuation is bounded by actual gas. |
| Royalty opening | No eligible NFT, first transaction late, failed currency across cutoff | Opening finalizes before a late activation joins. Zero-cohort receipts remain unallocated for a later governance decision. Faulted currency initial allocation uses captured opening cohort, not the first late activator. |
| `allocateUnallocated` / `allocateAllUnallocated` | Admission needed, paused/preparing controller, zero active weight, concurrent activation | Only current governance, current canonical NFT, open royalty window and stable operation context can recover original-currency unallocated value. Already earned/deferred liabilities are excluded. **Beneficiaries are the active weighted cohort at inclusion, not a cohort frozen by reviewHash.** |
| Royalty `claim`, router and current owner | Transfer before claim, selected bad currency, callback, repeat claim | Owner authorization is explicit; claim debits precede transfer. Selected batch faults roll the batch back; a separate healthy-currency claim remains possible. Original currencies and NFT rights remain separate from LP conversion. Supported exact-transfer token behavior is an admission assumption. |
| Canonical freeze/capture | One admitted currency becomes unreadable, live residual, unfinished opening/draw | Capture failure rolls freeze back atomically. An unavailable admitted token can prevent complete canonical migration until dependency recovery; emergency economic bypasses do not create missing token transfer capability. No write-off or unauthorized recipient was added. |
| Public canonical export/import/progress | Another caller advances a cursor between operator read and inclusion | Valid public progress can stale an operator plan, but exact row bytes/order/roots and peer identity remain authenticated. Reread progress; do not make every progress function governance-only. |
| Canonical funding | Partial transfer, destination prefund, callback attempts phase change | Exact source/destination asset/amount matching, balance deltas, per-index flags and nonreentrancy protect funding. Prefunds do not substitute for required source backing. A failed transfer rolls its flags back. |
| Canonical abort/restore | No funding, some indices funded, all funded, late receipts at cancelled importer | Restoration requires exactly those transferred assets back before reopening source. Separate reviewed cancelled-royalty recovery follows authenticated current target/governance; imported rights remain inert. Token failure can delay restoration; no generic sweep or alternate custody recipient exists. |
| Terminal principal close/allocation | Final fees/compound, multiple NFTs per owner, dormant NFT, tiny units | Actual close proceeds and designated compound enter principal; fee/buyback liabilities remain separate. Shares, not rarity or wallet count, determine principal. Cumulative allocation conserves raw units and transfers retain unpaid rights. Existing exact-state tests have explicit nonzero share/payout assertions; not rerun here. |
| Terminal distribution/fallback | Receiver rejects ETH/token, transfers during callbacks, duplicate batches | Self-call isolation defers one payout while retaining backing; current-owner selection has an explicit payout linearization point. An owner fallback cannot be exercised by governance/ERC721 approvals on somebody else's behalf. A contract owner unable to receive, transfer or call fallback remains an incompatible-escrow risk; no universal delivery guarantee. |
| Royalties after terminal exit | Principal distributed, new ETH/ERC20 royalties, retained NFT transfer | Principal terminal lock does not remove existing/future royalty entitlement or reward claims. Exited metadata remains distinct from Dormant; financial rights are not inferred from image tier. |

## Recovery-allocation game theory and an existing optional operating procedure

The approved rule allocates reviewed unsupported/zero-cohort receipts among NFTs active **when recovery executes**. A trader can observe a pending recovery and activate an NFT first if its prospective weighted share justifies the locked principal and costs. This is an accepted economic exposure, not evidence that reviewHash freezes beneficiaries; no new cohort guard or retroactive exclusion is implemented.

Terminal principal delivery is a separate atomic ETH+ZZZ payment: `_pay` sends ZZZ first, then ETH, and a failure rolls both back for that NFT. A globally frozen/unsupported ZZZ transfer can therefore defer healthy ETH too. The existing API has no ETH-only partial principal payout. This is a dependency/recovery limit, not permission to change liabilities or send somebody else's funds elsewhere.

For an operator who wants a stable activation cohort during review, existing controls can temporarily stop contributions without globally pausing royalty recovery:

1. Read the exact current contribution pool and its full current configuration.
2. Submit governance `PoolRegistry.disablePool(pool,true,false)` and confirm the stop before capturing the cohort. An activation ordered before that transaction can still succeed.
3. Read current royalty activation count/weight, review the exact currency/classification and allocate. Leave global pause false because reviewed recovery requires an unpaused controller.
4. Deliberately re-enable the reviewed destination through full `configureNative` validation; do not assume a boolean-only enable or a successful future validation.

Source trace for direct-call coverage: **Vault.activate/increase → _join → MigrationBudget.validateContribution → VaultCanonical.validateContribution rejects !depositsEnabled**. The Entry checks the flag separately. NFT.notifyContribution is fixed-Vault-only and requires nonzero committed shares; the royalty ledger's activation writer is NFT-only. Production Registry permits at most one deposits-enabled pool. Thus direct Vault activation is not a bypass of the contribution stop. Existing earned claims/transfers and royalty recovery remain separate. If healthy feed/venue validation is unavailable afterward, re-enabling can legitimately wait; do not remove guards to promise immediate restoration.

## Evidence boundaries

Fresh dynamic evidence consists of **12 distinct methods: three new seal cases, one strengthened royalty recovery fuzz method, seven affected canonical-preparation cases and one affected operator-controls case**. The original seal failure, zero-selection attempt, initial stale-fixture setup failure and final source-stage outputs are preserved separately in `RIGHTS_VERIFICATION.json` and companion logs/results. Baseline/final overlap and the diagnostic repeat are not added to the unique count.

The source review above is not a fresh execution of all royalty/canonical/terminal cases. Existing source-scoped tests were inspected for meaningful nonzero quantities and assertions; their previous execution evidence is not relabelled. No public RPC, transaction, wallet, deployment, sealing of an existing environment, service, site, journal or heartbeat action occurs.
