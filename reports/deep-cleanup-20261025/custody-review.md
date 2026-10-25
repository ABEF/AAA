# Core custody and governance review

Source baseline: `964e6b6e14dfc91670ab74b6c5d34d8fe4da39bb` (publication
checkpoint for implementation `ea2a70c`). This review reads the current local
candidate; `custody-review.json` records the actual reviewed file hashes. It is
an internal, source-scoped review, not an independent audit or production approval.

## Confirmed improvement

**P2 - Guardian authority could change without an observable role event.**
`ZZZAccessController.setGuardian` previously wrote its mapping without emitting
a log; constructor keeper/guardian grants also lacked logs. The production
gate requires `role_history_complete` (`zzz_ops/production_v2.py`, governance
validation). A role observer could not reconstruct all authority grants and
revocations from deployment history, particularly unknown guardian addresses.

The candidate adds `GuardianChanged(address indexed account,bool enabled)` and
emits it after the guardian mapping update. Constructor grants now emit the
existing `KeeperChanged` and new `GuardianChanged` after each corresponding
write, in the original keeper-then-guardian order. No grants, access checks,
storage, financial rights or lifecycle transitions change. The additional event
and constructor logs are an intentional observable behavior change, not an
ABI-identical refactor. Existing deployed history cannot be repaired by adding
events to a fresh candidate; old deployments require their original evidence.

Four new `DirectGovernanceTest` methods check exact topics, emitter and boolean
payload, initial reconstruction, bootstrap and sealed-governance grant/revoke,
zero/unauthorized attempts, mapping preservation and no logs on rejection.
These tests were **written but not executed by this reviewer**. The parent
coordinates the single final compiler/size/test campaign and generated event
catalogue. Do not infer a test pass from this review.

## Custody paths and invariants inspected

| Path | Required properties read in the current source |
| --- | --- |
| Contribution and shared LP accounting | Vault owner checks and incumbent checkpoints precede share issuance; `MigrationBudget` delegates read-only owner/contribution checks to the fixed canonical companion. Only ETH/fixed ZZZ are user sources. Pool accounting and actual physical LP validation remain separate from quoted USD inputs. |
| Maintenance and same-pair pool moves | `MigrationBudget.checkpoint` freezes the starting price vector and loss policy before external operations, includes released classified compound exactly once and checks actual deployed plus attributed idle afterwards. Pool moves retain exact ordered currency identity and permanent bucket reservation; NFT shares do not change. |
| Parking | `CustodyValidation.validateParking` binds pool, LP token ID, shares, deposit record, custody epoch, nonce, actual currencies, raw minima and review. `Vault.park` harvests venue fees separately and closes only into Vault custody. The operator can park with stale source USD feeds, but cannot bypass a broken token/venue or changed immutable runtime binding. |
| Normal external custody exit | `Migration.approve/exit` bind the exact source snapshot, recipient code hash, captured retained-value floor and output minima. Exit marks Sent/increments epoch before external callbacks; principal is released only after closing/consolidating attributed idle. Exact deltas prevent raw donations from substituting for principal. A failure rolls back the exit transaction. |
| Raw external custody exit | Explicit approval selects raw mode and actual raw minima; it is not an automatic fallback from a failed normal exit. It does not fabricate a USD floor while pricing/swap markets fail. Raw mode still requires usable source custody, exact identity and transfer behavior. |
| Funded return/completion | `Migration.recover` requires every actually sent source currency, exact native call value and ERC20 ingress; it can restore parking while paused using a fresh bounded deadline. No timeout, partial return or proof-only recovery cancels sent liability. `completeLocal` requires actual LP, original shares and the approved budget/minima; approvals reset afterwards. |
| Whole-collection handoff | Fixed six-domain coordinator freezes economic/ownership work before capture; settlement/export/import/funding have distinct ordered phases. Rows must match the frozen source byte-for-byte; prefunds cannot satisfy funding flags. Retirement and replacement activation are atomic. Abort returns only transferred backing and restores source only after all such backing is returned. |
| Configuration and sealing | Direct governance remains trusted for reviewed custody recipients and replacement code. Two-step wallet handover changes governance only. Module/source identities are fixed at seal; bootstrap disappears. Preparation/frozen/terminal states independently block unauthorized new economic work. No generic executor or holder principal withdrawal is introduced. |

The review also read `ZZZFeesCanonical`, `ZZZNFTCanonical`,
`base/ZZZCanonicalLedger`, `ZZZFeeController`, `ExactAsset` and `ExactToken` for
classification, funding and callback boundaries. The royalty system's separate
currency policy is not an activation-source allowance.

## Code retained deliberately

These are not removal candidates merely because a current CLI or launch flow
has few callers:

- Pool aliases and `homePoolId` preserve original pool/bucket provenance and
  prevent previously occupied identities being reassigned across moves and
  repeated canonical replacements. Removing them changes current V4 wire records.
- Source snapshots, custody epochs, nonces and recipient code hashes bind exact
  approvals and reject stale execution or replay. They are not redundant caches.
- Normal and raw exit are distinct failure boundaries. Combining them with an
  implicit fallback would silently weaken an approved operation's guarantees.
- Canonical prefund baselines, quarantine, delivery flags and imported-share
  totals prevent fabricated backing, redistribution and repeated release/restore.
- Destination record/ledger validation remains useful even after exact source-row
  comparison: it checks the admitted destination's own configuration and backing.
- Fee reserves and royalty liabilities are separate from LP principal. External
  principal exit intentionally does not sweep claimable fees, compound/buyback
  reserves, royalty funds or donations to the operator. Full collection handoff
  exports those classified domains separately; separate royalty custody preserves
  the corresponding liabilities.
- Historical profile readers/events/journals retain actual evidence boundaries;
  they must not be relabelled as current accounting3 or deleted to reduce counts.

Naming the Budget checkpoint values 0..3 could improve local readability, but
does not correct a demonstrated defect. It is deferred rather than creating
additional source/compiler/test churn in this pass.

## Pinned dependency checks

The actual installed dependency sources were read, rather than assuming a newer
API: OpenZeppelin 5.4.0 and Uniswap v4-core 1.0.2/v4-periphery 1.0.3.

- `ReentrancyGuard.nonReentrant` rejects nested protected entry and restores its
  state after the body. Cross-contract before/after lifecycle checks remain
  necessary; one contract's guard does not guard another contract.
- `PoolManager.unlock` authorizes its callback to the unlock caller and requires
  all currency deltas settled before re-locking. The current hookless pool still
  needs its exact reviewed manager/position/state identities.
- `PositionManager` supports fee collection with zero-liquidity decrease; burn
  removes the position and applies slippage to principal excluding accrued fees.
  TAKE_PAIR sends actual available credit, not a caller-supplied balance sweep.
- `ExactToken` validates sender and recipient deltas for conventional tokens;
  native `ExactAsset.push` validates exact sender spend. These checks cannot prove
  an admitted token or upgradeable dependency stays honest forever.

No dependency versions, compiler settings, bytecode limits or public routes were
changed. The review does not qualify the real deployed dependencies, gas,
providers, feeds, routes, VRF, OpenSea or operations.

## Existing test intent inspected, without rerunning it

`CustodyHandoff.t.sol` asserts normal output identity, rollback after failed
conversion, explicit stale-price raw exit, destination reservation, unchanged
shares, exact full recovery, lifetime fee rights during custody, no post-send
timeout cancellation and original-budget preservation. `CustodyParking.t.sol`
asserts that old idle, fees, compound and donations cannot subsidize close
minima, and that failed resume preserves parked custody. `CanonicalHandoff.t.sol`
asserts actual owners/traits/shares and both ledgers, source retirement,
prefund/donation exclusion, partial funding rejection, exact abort return and
callback rollback. These source assertions were examined; their historical
execution evidence remains in its original report scope.

No additional core custody/accounting exploit was confirmed in these inspected
paths. This is not proof of absence. Accepted immediate-governance/external-
custodian trust, failed dependency recoverability, exact release initcode/gas,
real service qualification and independent audit remain open.
