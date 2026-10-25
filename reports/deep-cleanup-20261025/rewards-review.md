# NFT and funded-reward cleanup review - 2026-10-25

This is an internal, source-scoped review of the undeployed candidate. It is not
an independent audit, live provider qualification or production approval. No
service, wallet, existing chain, journal, balance or public configuration was
changed. Compilation and focused execution are recorded separately by the
coordinating review; no pass is inferred from the source inspection below.

## Findings and approved changes

### R1 - duplicated royalty balance primitive (maintenance)

`ZZZRoyaltyRewards` already inherits `ZZZCanonicalLedger`, whose nonvirtual
`_canonicalBalance(address)` has exactly the same expression as the royalty
ledger's private `_balance(address)`. The private copy and its 12 calls created
two names for the same native/ERC20 observation, including in claims,
conversion, custody and canonical settlement.

The approved change removes the private copy and uses the existing inherited
helper at all 12 original call sites. The conditional expression, returned type,
`address(this)`, number and ordering of external `balanceOf` observations are
unchanged. No storage, external selector, permission, payout, rounding or event
was intentionally changed. `IERC20` is still required for admission and
approvals. The exact preimage is retained beside this review. Runtime/initcode
savings, if any, must be measured by the normal compiler; none is assumed.

`ZZZFeeController` deliberately retains its own primitive: introducing funded
canonical-ledger inheritance merely to reuse a three-line helper would add
unnecessary custody/storage coupling.

### R2 - obsolete real-Vault royalty-outage test (verification correctness)

The previous `NFTOwnershipRightsTest` method
`testUnavailableAdmittedRoyaltyAssetBlocksEntryButHealthyClaimsRemain` expected
an optional royalty currency's failed `balanceOf` to undo an entire activation.
That is the retired behavior. Current `ZZZRoyaltyRewards.activate` isolates its
bounded optional ERC20 self-call, while native and healthy currencies enroll
normally. The deliberately broken token in this test is neither LP asset.

The approved replacement,
`testUnavailableRoyaltyCurrencyDefersOnlyItsEligibilityWhileActualLPActivates`,
checks real Vault/NFT/Membership/LP/royalty interactions, with the existing
explicit mock venue, currencies, authorities, price sources and VRF. It checks:

- User token debits and physical mock-venue LP amounts, active status, newly
  issued shares, unchanged incumbent shares and the shared denominator.
- Revealed rarity's royalty weight, healthy/native eligibility and deferral of
  only the unreadable currency.
- Previously funded LP/healthy royalty rights staying with the incumbent.
- Recovery assigning all 150 unseen currency units to the old eligible cohort,
  enrolling the new NFT at zero and sharing only subsequent receipts.

The original fixture and old/new method mapping are archived in
`fixture-repairs/`; no production behavior was changed to satisfy the test.

## Preserved boundaries and rejected simplifications

| Boundary inspected | Evidence and reason to preserve it |
| --- | --- |
| Paid mint versus activation | `ZZZVault.mintDormant`, `ZZZNFT.mint`, `notifyContribution`: issuance forwards mint proceeds separately; only confirmed Vault shares create LP/royalty eligibility. |
| Fixed artwork draw | `ZZZNFT.finalizeTraits`, `_drawArtwork`, `ZZZArtwork`: authenticated stored words, mint-order finalization and draws without replacement retain exact 600/300/100 quotas. No reroll or new artwork generation is introduced. |
| NFT ownership and all accrued rights | Both ledgers key balances by NFT ID and authenticate the current ERC721 owner when claiming. Transfer does not pay a former owner or discard fractions. Approved NFT operators can transfer, but cannot claim another owner's balances. |
| LP versus royalty accounting | `ZZZRewards` uses bucket-share personal indices plus equal active collective indices. `ZZZRoyaltyRewards` uses independent rarity weights, currency cohorts and pending receipt accounting. Merging them would alter economic rules. |
| Funded revenue and dust | `ZZZFeeController.allocate` pulls declared actual receipts once, classifies 80/10/5/5 in raw-unit quanta and retains the documented incumbent-only sub-20-unit dust barrier. Existing donations never become a substitute receipt or principal. |
| Optional royalty currencies | Their synchronization can fail independently; activation keeps healthy/native eligibility. Deferred baseline records prevent new NFTs receiving older unreadable receipts. `syncAll` remains atomic; individual `sync` and claims offer currency-specific recovery. |
| WETH, stable currencies and wrapper policy | Contribution inputs remain ETH/fixed ZZZ. Marketplace receipts and reviewed conversions are a separate domain. Removing their currency/wrapper handling would remove working receipt/unwrap/conversion paths. |
| Separate converter instances | Shared immutable-bound execution code does not merge LP and royalty custody. Exact source debit, native output, pre-existing balances, wrapper sender arming/reset and route/oracle floors remain distinct per ledger. |
| Owner callbacks and batching | `ZZZClaimRouter` preflights current owners/duplicates and rechecks ownership for each leg. A transfer during an earlier payout cannot authorize later legs. All failures revert the atomic batch. |
| Claimed event after payout | A direct payout callback can transfer the NFT before `Claimed` is emitted. `frontend_api/history.py` intentionally validates the emitted payout recipient without incorrectly requiring that recipient to still own the NFT at the later event-log position. Existing ordered history fixtures cover that case. |
| Zero claims/events | Zero funded payouts can still emit `Claimed`. Removing these events changes observable history and has no demonstrated safety or size benefit. No new zero-return shortcut was added. |
| Factory authorization | The royalty factory's public creation method creates a caller-owned ledger with the fixed controller; the canonical NFT validates its own ledger/controller binding. The private `creator` field is the one-time deploying factory authority, not a retired pool-creator payment mechanism. |
| Complete same-chain handoff | NFT ownership, both ledgers, fractions, deferred baselines and classified exact backing still move together. Prefunds and post-freeze receipts retain their distinct treatment. No cross-chain transport, substitute backing or arbitrary sweep is added. |
| Broken external assets | Failure isolation is not permission to delete vested obligations. Exact canonical capture or custody can still be unavailable when an admitted asset cannot be read/transferred. Removing its ledger rows would change holder rights; admission/service qualification remains necessary. |

An unexpected currency received before its royalty admission is quarantined by
`addAsset` as pre-admission orphaned balance, even if NFTs are already active.
It is not automatically distributed on later admission. Expected marketplace
currencies should therefore be reviewed and admitted before accepting receipts;
assigning unidentified older receipts retrospectively would need an explicit
provenance/policy decision, rather than a cleanup shortcut.

## Installed dependency and callback review

The installed OpenZeppelin package is version 5.4.0. The inspected ERC721
implementation updates ownership and clears the token approval before invoking
the safe-transfer receiver hook; rejection reverts the whole call. NFT's
`_update` override preserves the canonical lifecycle guard, while same-chain
import intentionally uses inert internal minting without receiver callbacks.
That import exception still requires the existing escrow-compatibility preflight.

The inspected `ReentrancyGuard`, `SafeERC20` and project `ExactToken` distinguish
mutating reentrancy, optional ERC20 return handling and exact sender/recipient
balance deltas. These checks cannot prove that an admitted proxy/token remains
honest forever. Empty native receive hooks on the royalty/LP/fee ledgers remain
intentional for actual receipts, returns and quarantine; converters retain their
separate armed-sender rule.

[ERC-2981](https://eips.ethereum.org/EIPS/eip-2981) specifies a royalty quote, not
universal payment enforcement, and expects payment in the sale's denomination.
This supports retaining actual received-currency accounting and reviewed
conversion rather than assuming every marketplace receipt is already ETH.

## Compiler-advisory applicability triage

The pinned compiler remains 0.8.26/Cancun, via IR, optimizer runs 1, with Yul
optimization disabled. The official
[known-bug inventory](https://docs.soliditylang.org/en/latest/bugs.html)
lists two affected mutual-recursion advisories, SOL-2026-2 and SOL-2026-4.
Disabling Yul optimization alone does not exclude them. Their relevant condition
is an internal mutually recursive call graph. SOL-2026-6 concerns named custom
error arguments passed to `require`.

`rewards-callgraph.py` builds per-concrete-contract internal call graphs from
compiler ASTs, follows modifier invocations and installed library/dependency
bodies, resolves unqualified virtual calls against each root's compiler
linearization and preserves explicit base/super/library selection. External
callbacks use separate EVM frames and are not internal recursion. Manual ERC721
review checked the overloaded safe-transfer/transfer/`_update` virtual chain.

The baseline final-131-input AST analysis found 31 concrete production roots,
zero internal recursive components, zero unresolved internal calls, no
user-defined functions in 51 distinct inline-assembly scopes (149 root contexts), and no named
custom-error `require` calls. Its full external graph is retained with exact
compiler input/output hashes. This baseline predates R1; current final-source
analysis is recorded separately in `rewards-callgraph-summary.json`. The final
successful closed 265-input AST (131 project/test/script inputs and 134 dependency
inputs) retains those same counts. All compiler input contents matched the
current files, and the graph's production inputs matched the normal 75-file
build closure (44 project files plus 31 dependency files). No production state
initializer calls an internal function and no modifier in that production
closure is virtual, so these potential graph edges do not hide a current cycle.

The first attempt to inspect the then-incomplete new AST exposed a declaration
error in an unrelated test and produced no usable source roots. That raw empty
attempt is explicitly excluded. The graph reader now rejects compiler errors,
missing ASTs and missing expected production roots. A negative control against
the actual failed initial AST returned nonzero and produced no graph; the raw
failed-input evidence is preserved. The later successful final AST is the only
current-source applicability result.

The mechanical R1 call replacement leads to a nonvirtual leaf helper with the
identical body and cannot itself add an internal cycle. This is applicability
triage, not proof of compiler correctness or permission to silently upgrade the
pinned compiler/settings.

## Focused verification recommendation

After normal wire/storage and size comparisons, execute the repaired ownership
integration case plus existing representative royalty native/ERC20 funding,
fault recovery, conversion rollback/read-callback isolation, custody full
return and canonical prefund/late-receipt cases. These are affected by the shared
balance helper. Do not rerun every unchanged mint, route, keeper, website or
historical test merely to increase counts. The exact selected results and any
fixture repair must remain explicit in the coordinating verification receipt.

OpenSea integration, supported live VRF, independently qualified feeds/routes,
production authorities, operating rehearsals and independent audit remain open.
