# Royalty and funded-rights preservation review

## Exact scope

The immediate comparison is `964e6b6` to the requested reference
`35007db755ad4007013c1828f83983202647857a`. Reviewed HEAD `55011c0` adds a
publication receipt; its production files are the reference files. The wider
Paris-day financial comparison starts at `3551868`, immediately before the
first 25 October commit. This daylight-saving transition day runs from
2026-10-24 22:00 UTC inclusive to 2026-10-25 23:00 UTC exclusive.

This review independently read the exact royalty helper diff and all callers,
the old/new outage fixture, and daywide LP fee, shared-share checkpoint,
membership, custody and canonical-backing boundaries. Source bindings and the
12-call map are in [the manifest](royalty-audit-bindings.json). It also followed
actual current read/history consumers, rather than treating a contract pass as
proof of working API integration.

No Solidity, deployed state, existing Anvil data, journal, signing capability,
website source or service changed in this review slice. The implemented
correction is a backend read/history fix with local tests.

## Verdict on the royalty consolidation

**Confirmed behavior-preserving within the inspected source and saved compiler
comparison.** The old private function and the existing inherited nonvirtual
function both return exactly:

```solidity
asset == address(0) ? address(this).balance : IERC20(asset).balanceOf(address(this))
```

The complete royalty source, not merely selected expressions, equals its
baseline after deleting that one private function and replacing exactly its
12 calls with the inherited name. The day-start royalty source also equals the
immediate baseline. This refactor therefore did not introduce optional currency
isolation or change custody policy; those behaviors existed earlier.

The inherited function is an internal call in the same ledger context, not an
external call to a different custodian. It reads raw balances only. Liabilities,
orphaned amounts, pending receipts, conversion debits and custody classification
remain in the original callers. It does not read the Vault's LP principal or
reinterpret ERC20 units as ETH/USD.

| Call site | Required balance and timing | Consequence preserved |
| --- | --- | --- |
| `convertBatch`, before conversion | Source ERC20 balance after selecting/debiting earned whole units | Existing source funds cannot subsidize input consumption. |
| `convertBatch`, after conversion | Fresh source balance after converter return and approval reset | Exactly the selected source units leave; received native output is checked separately. |
| `exitCustody` | Full admitted-currency balance in the approval preconditions | No partial or stale balance exit masquerades as the approved full custody transfer. |
| `returnCustody` | Fresh balance after actual exact funding and custody flag clearing | Existing obligations remain backed; a return does not become new royalty income. |
| `pending` | Guarded raw balance minus accounted amount | External custody/reentrant intermediate reads still fail; missing data is not zero. |
| `_sync` | Raw balance before updating the index | Only actual unprocessed receipts become liabilities or orphaned funds. |
| `_claim` | Fresh balance after the owner's payout callback | Returned donations may stay pending, but remaining accounted backing cannot be lost. |
| `claimable` | Guarded current raw balance | Only a verified eligible cohort can include unprocessed receipts; stored accrued credit remains separate. |
| `canonicalCapture` | Freeze-time raw balance before recording the cutoff | Frozen pending receipts and exact classified backing remain distinct. |
| `canonicalImport` | Destination balance before incoming handoff funding | Existing destination prefunds remain quarantine, not replacement source backing or holder income. |
| `canonicalActivate` | Current destination balance after imported accounting/backing validation | Extra preactivation receipts remain orphaned; activation does not invent earned revenue. |
| `forwardLate` | Actual remaining balance at the retired royalty receiver | Stale marketplace payments forward only to the fixed immediate successor, without duplicating the old paid backing. |

The saved [compiler comparison](../deep-cleanup-20261025/compiler-comparison.md)
reports unchanged royalty ABI, recursive storage and executable bytes after
only complete metadata masking; RoyaltyRewards/Factory sizes do not improve.
Raw bytecode identity and historical dependency-byte identity must not be
inferred from that statement. New deployment hashes/pins still require exact
release qualification. No unchanged compiler or full-suite run was repeated
here.

## Outage assertion replacement: what was lost and retained

The old `NFTOwnershipRightsTest` expected a separately admitted royalty token's
failed `balanceOf` to revert the whole Vault activation, leave its NFT dormant,
preserve user token balances and create neither shares nor membership. That
expectation was already obsolete at `964e6b6`: the production ledger isolated
optional token synchronization before the reference refactor.

The replacement does not make failing LP execution succeed. It establishes the
intended distinction between an LP failure and an optional royalty-currency
failure. It verifies actual mock-venue amounts and user debits, positive new
shares, unchanged incumbent shares, the shared denominator, active status,
revealed rarity's weight, native/healthy eligibility and failed-token deferral.
It preserves the old incumbent's 90 LP units, 70 healthy royalty units and 3 ETH
claim. Recovery gives all 150 unseen failed-currency units to the old cohort,
then gives the newcomer zero until the next 60-unit receipt splits 30/30.

| Removed expectation | Current intended behavior and retained protection |
| --- | --- |
| Optional currency failure must revert all activation | Intentionally replaced by successful LP activation plus deferred registration only for that currency. The final reference selection executed this real Vault/NFT integration case. |
| All user tokens must remain because of that optional failure | Replaced with exact contribution debits and physically increased LP; it no longer falsely claims rollback happened. |
| No new shares/membership/royalty weight | Replaced with positive shared-position shares, one membership and the already revealed fixed rarity weight; no prior income is awarded. |
| Recovery must retry the whole activation | Removed because the NFT is already active. Recovery synchronizes only that currency, protects old receipts and enrolls it for future receipts. |
| Actual venue/swap/transfer failures must roll back | Still required. Separate affected native and earlier Vault tests retain this coverage; the replaced optional-token test was not valid evidence for these independent failures. |

The exact original bytes and mapping are retained in the reference report's
[fixture repair](../deep-cleanup-20261025/fixture-repairs/manifest.json).
The reference's 32 selected methods do **not** include every royalty edge case
or the native-custody/deferred-ETH scenario found below. Its narrower execution
scope is preserved, rather than claiming it exercised every helper call/state.

## New confirmed issue and correction

### RR-P2-1 - valid native royalty custody broke reads and permanently rejected history

Severity **P2**, confidence **high**. This is a pre-existing integration gap,
not a regression from the royalty helper replacement. `git blame` places the
unconditional native-cohort read assumption in `83d844d5` (19 October), the
replay's native-deferral rejection in `61f2ac89` (19 October), and the explicit
native custody producer/test in `e36a581a` (23 October).

The actual source permits this sequence:

1. Existing NFT A has accrued native royalties. Paused governance moves the
   full admitted ETH royalty balance into approved external custody.
2. Governance resumes operations. NFT B successfully activates LP. Its fixed
   royalty weight exists, but ETH eligibility waits while that currency is out.
   Other healthy royalty currencies enroll normally.
3. Additional ETH receipts arrive. Exact custody return restores the previously
   accounted funds but does not itself synchronize receipts or enroll B.
4. The next sync assigns unseen receipts to A, records B's recovery baseline,
   then enrolls B only for future native distributions.

`royalty_reporting.py` previously rejected `eligibleCount(ETH) != activationCount`
for the whole NFT projection. `earnings_replay.py` rejected every native
`RoyaltyAssetDeferred` event, even after exact return and recovery. Thus valid
source behavior hid healthy holdings and poisoned later complete earnings
history. No unbacked payment or on-chain theft was demonstrated.

The implemented correction:

- Native lag requires a confirmed positive `custodyNonce`, direct ordinal/
  `eligibleFor` consistency and feasible 1..3-weight bounds for both eligible
  and waiting cohorts, including the selected NFT. A missing old custody ABI
  remains fatal. Restored-but-unsynced lag is valid; custody amount zero alone
  cannot be used to demand immediate recovery.
- During custody, a reverting native `claimable` remains **unavailable/null**.
  Full `Projection.nft` still returns healthy LP/other royalty balances; it does
  not fabricate zero ETH or mark unavailable ETH claimable.
- Replay recognizes the existing exact custody exit/return event layouts from
  the pinned royalty emitter. Native deferral requires active authenticated
  custody. Duplicate exits, wrong IDs/amounts, unknown currencies, spoofed
  emitters and sync/recovery before full return are rejected. A custody return
  is not income. Old receipts use the old cohort before subsequent recovery.
- One native ABI encoding entry was added for `custodyNonce(address)`, using
  the existing typed read path and block pin. No duplicate raw-RPC encoder,
  writer, transaction preparation or signing capability was introduced.

Three positive regression controls failed against the pre-fix backend. Final
verification covers **52 distinct methods**: 13 new cases and 39 affected
existing cases. The first focused invocation executed 67 methods because an
imported test class caused 15 duplicate passes; these are excluded. One new
second-NFT fixture lacked ordinal RPC replies. That test-only fixture was
corrected without weakening assertions; only its two API cases reran. The
remaining 50 distinct passes were reused. Raw failures, exact fixture preimage,
duplicate inventory and final source hashes are in
[the verification record](native-royalty-custody-verification.json).

The new temporary SQLite/indexer-to-API case independently checks both NFTs:
old receipts 100, unseen receipts 50, then future receipts 400 yield **250** for
A and **300** for B; collection processed royalties are **550**, not 650.
Returning the earlier 100 custody units is not counted twice.

Full per-NFT earnings reconciliation deliberately remains unavailable while
funds are external because the actual ledger's `pending`/`claimable` views then
revert. This preserves fail-closed backing verification. Collection processed
history can remain readable; after exact return/recovery, complete NFT earnings
reconcile again. No hosted API, actual chain or existing SQLite database was
changed. Any additional current Solidity execution is recorded separately by
the main verification, not silently included in the reference's 32 cases.

## Wider day functionality matrix

| Feature | Baseline before the day | Current implementation and economic consequence | Evidence and result |
| --- | --- | --- | --- |
| Mint/ownership/rarity | Separate paid dormant ERC721 mint; 1,000 cap and exact 600/300/100 eventual rarity quotas | Same ownership, request/reveal algorithm, immutable traits and no holder burn/redemption path. Only an unused `_baseURI` override was removed from NFT. | Source diff and tokenURI call trace; **preserved in inspected source**, live VRF/OpenSea still **not verified**. |
| LP holder share checkpoints | Individual fees keyed by NFT shares; checkpoint before increasing shares | Rewards source is unchanged across the day. Current `_join` still checkpoints the old share quantity before issuance and preserves accrued fractions. | Source identity; prior source-scoped Vault/atomic/native cases retain their boundaries. **Preserved in inspected paths**, no new broad simulation claimed. |
| Equal collective share | One eligible share per activated NFT, none for dormant | Same eligibility/denominator; Membership no longer inherits nonexistent asset custody. Ordinary dust entry authorization moved from removed external intake to the fixed Vault. | Direct call trace, pruning zero-asset tests and current event replay reconciliation; **preserved**, with intentional fresh-candidate layout/API removal. |
| LP-only funded 80/10/5/5 | Local branch splits 20 raw units into 16/2/1/1; actual-funded remote/creator branches also existed | Same local arithmetic/reserves and incumbent-only residual rule. Remote/creator intake is intentionally removed; arbitrary donations are not local fee receipts. | Day FeeController diff, LP-only intake rejection tests and existing indexed sums; **intentionally narrowed**, not a promise to preserve retired revenue sources. |
| Historical funded dust | Settles incumbent rights before membership changes; historical accounting called live dependencies | Current Membership uses admitted immutable currency identities, so a broken historical venue with zero/settleable dust need not veto new entry. Positive unpayable dust still blocks rather than redistributing it. | Daily-security dust tests and subsequent inactive-bucket replacement retain exact scopes; **availability improved**, deliberate residual blocking remains. |
| Separate royalties | Actual received currencies, x1/x2/x3, prefix eligibility and fractions | Same royalty contract body after the precise helper substitution. ETH/WETH/stables as royalty/conversion currencies were not confused with ETH/fixed-ZZZ contribution restrictions. | All 12 caller contexts and saved bytecode/layout comparison; **preserved**. New backend native-custody integration gap **fixed**. |
| Transfers and claims | Accrued LP/royalty rights follow NFT ID; current owner claims | ClaimRouter and Rewards source unchanged. Royalty payout remains CEI with fresh post-callback backing check. A payout callback may transfer before `Claimed`; history does not incorrectly require the emitted recipient to still be owner. | Source identity, reference owner/custody tests, affected current reporting tests; **preserved in inspected/exercised paths**. |
| Conversion to native ETH | Separate immutable-bound LP and royalty converters, exact debits/output and stronger minimums | Shared abstract code still creates separate converter instances/custody. Existing ETH is not redistributed and conversion/claims are not new earnings. | Prior actual-v4/rollback tests plus current royalty conversion cases; **preserved within recorded fixture scope**, actual cheaper routes/feeds **not verified**. |
| Compounding and market valuation | Designated 5% reserve and attributed idle included in incumbent principal NAV | Two-pass placement/idle reinvestment retain share attribution; they are not extra holder claim balances. Historical compound stays incumbent-only before new issuance. | Current join/release/fee traces and liquidity-operation/native scoped evidence; **source-reviewed**, real strategy economics/max-state gas **not verified**. |
| Local pool move/raw custody exit | Source-chain governed custody, exact funding, shares and earned ledgers survive | One fixed ZZZ identity; normal exit converts to ZZZ, raw exit preserves actual pair assets. Retired bridge/remote proof branches are removed; external custodian remains explicitly trusted. | Day diff plus scoped current custody/hand-off cases; **intentional scope change/preserved local rights**, no real custody operation performed. |
| Complete same-chain handoff | Ownership, membership, share/fee/royalty ledgers and classified backing move together | Current V4 local rows omit retired location/inbox data. Frozen/retired source, exact incoming backing, prefunds and abort remain separated. No old codec is silently imported. | Current canonical tests and strict source import comparison; **preserved within the new profile**, cross-codec/chain migration **not supported**. |
| Native royalty custody recovery | Existing core allows activation with ETH eligibility deferred | Core rights are unchanged; full return does not count as new royalties, and new entrants exclude unseen older funds. Backend now understands that valid lifecycle. | Three before failures; 52 distinct backend passes; producer EVM evidence separately scoped. **Backend integration regressed earlier and fixed here**. |
| Reproducible release/profile boundaries | Old artifacts had incomplete dependency/build content bindings | Current reference binds a closed production dependency/build closure. Raw hashes/pins change with compilation; old running Anvil and journals are not upgraded. | Main evidence checker/compiler review owns final results; **not a universal correctness or production approval claim**. |

## Remaining limits and operator consequences

- An admitted unreadable token may still block its claims, funded-dust settlement
  or complete canonical capture. Removing liabilities to make those operations
  pass would change rights. Exact conventional-token/provider admission remains
  a release responsibility.
- Expected marketplace royalty currencies should be admitted before receipt;
  previously unknown balances are quarantined rather than retroactively
  assigned. The helper consolidation does not solve marketplace payment
  enforcement or arbitrary-currency provenance.
- After a royalty custody return, use permissionless `sync(asset)` or the next
  valid claim/sync path to settle older receipts before waiting activations join.
  Do not retry NFT activation, reroll traits or treat restored funds as earnings.
- Schema/layout/runtime boundaries, original journals and the paused monitor
  remain intact. Current native Website/API/keeper hosting, qualified routes,
  independent feeds, supported randomness, production authorities, OpenSea,
  real operating rehearsals/maximal gas and independent audit remain release
  gates. No blanket exploit-absence or production-readiness conclusion follows
  from this slice.

## Final publication review: deferred native credit guard

The new rejection of a nonzero **available** native claimable balance on a
native-ineligible active NFT was independently traced again before publication.
No legitimate counterexample was found in the current pinned operating ledger:

- Activation is one-time (`ZZZRoyaltyRewards.sol:196–220`). A native-deferred
  NFT is a new activation whose ordinal exceeds the native eligible prefix;
  existing eligible NFTs never lose eligibility when another custody episode
  begins (`eligibleFor`/`_enrollWaiting`, lines 231–238). It therefore cannot
  bring previously earned native credit into a newly deferred state.
- Ordinary royalty accrual uses weight zero for an ineligible currency
  (`_checkpoint`, lines 330–339). Plain ETH receipts create pending raw funds,
  not an `accrued` balance for the newcomer. During actual custody, the native
  `claimable` view reverts; after exact return but before sync it returns the
  newcomer's zero stored accrual (lines 376–385).
- Conversion does credit ETH directly at line 166, but first calls `_sync(0)`
  at line 142. That call rejects active native custody at line 295; after return
  it allocates older pending receipts and enrolls waiting NFTs before any native
  conversion credit is assigned. Conversion also rejects never-activated NFTs
  at line 146. Thus a successful conversion cannot leave credited ETH on an NFT
  that is still outside the native prefix.
- Complete handoff cannot capture outstanding royalty custody (line 403).
  Settlement enrolls waiting currencies before export (lines 418–428), and
  destination activation sets every admitted currency's prefix/weight to all
  imported active NFTs (lines 495–501). Import may transiently hold nonzero
  accrued amounts before eligibility initialization, but that is an importing
  deployment, not a supported holdings projection: `Projection._verify_deployment`
  rejects non-operating lifecycle states at `service.py:315–317`, before
  `Projection.nft` calls royalty reporting.

This argument depends on the current pinned ledger, monotonic one-time
activation and the API's operating-lifecycle guard. It must be revisited if
another implementation adds direct native-credit writers, eligibility removal
or read access to importing states. It does not claim arbitrary replacement
code can satisfy the same invariant. The final backend diff also retains strict
custody-event layouts, admitted currencies, emitter identity, exact return IDs/
amounts, deferred-prefix checks and existing request-budget propagation. The
three conditional native-custody proof reads are bounded and use the original
typed block-pinned read helper; no retry, write or signing path is added.

No code or tests changed and no checks were rerun for this final source review.
