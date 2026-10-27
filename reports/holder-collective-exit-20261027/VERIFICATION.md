# Collective holder return: verification

Reviewed 2026-10-27. Fresh undeployed accounting4/custody3 candidate; production
NOT APPROVED. [Internal review](REVIEW.md) describes the changed rights and
residual risks. [Operator procedure](../../docs/HOLDER_COLLECTIVE_EXIT.md) owns
the shutdown, batching and recovery instructions.

## Implemented behavior

- Governance alone starts the irreversible exit while paused and closes each
  native ETH/fixedZZZ bucket. Ordinary holder withdrawals remain unavailable.
- Final fees retain80/10/5/5; actual LP proceeds, attributed idle and pending
  compound form principal. Earned LP/royalties and buyback reserves stay separate.
- Deterministic bounded allocation conserves every raw unit. Direct payments
  resolve the current owner and isolate rejected/gas-consuming recipients.
  Successful normal delivery requires no holder action or holder gas.
- Optional keeper automation processes allocation and delivery only after all
  governance closes. It reuses the existing simulation, signer, journal, nonce,
  gas/day limits and receipt recovery. It never starts exit or closes LP.
- Failed recipients remain backed; the operator retries, with owner-authenticated
  fallback for incompatible receivers. Arbitrary ERC721 approval cannot redirect.
- NFTs retain transfers, prior unclaimed rights and future rarity royalties.
  Exited5 reports verified zero LP with terminal metadata/ERC4906 notification.
- External principal/royalty custody drains, all-ZZZ conversion exit and external
  recovery/completion are removed. Native-only LP admission prevents new pools
  incompatible with ETH+ZZZ return. Same-pair moves/parking remain before exit.
- Access blocks new principal work and canonical replacement permanently after
  exit starts, including after unpause. New canonical domain is
  `ZZZ_CANONICAL_SAME_CHAIN_HOLDER_EXIT_V5`.

## Solidity execution and compiler evidence

**133 distinct final affected Solidity methods pass** across two disjoint
selections:116 holder/royalty/metadata/native/budget/Vault cases and17 controller/
native-canonical cases. These are not a full repository regression. Commands and
individual results are in [metadata](verification-metadata.json).

The holder suite contains16 methods: real Vault/NFT/fee/reward/Membership/Migration
composition with explicit fake native venue/correlated prices, plus a supplemental
1,000-entry/four-bucket inventory model. Its fuzz method runs1,000 cases. Method,
fuzz-run and model-entry counts are different units and are not added together.
The scale test is not1,000 real target-chain mints or gas qualification.

Covered cases include proportional rather than equal principal; exact rounding;
final fees and pending compound; current-owner transfer and paid markers;
post-payout future royalty receipt/claim; duplicate pushes and reentry; rejected
and gas-burning receivers; prefund isolation; stopped-pool/stale-price raw close;
raw minima rollback; in-flight contribution callback rejection; all-bucket
validation; partial close/transfer; missing share inventory; dormant NFTs;
actual typed native Manager close; real controller terminal authorization;
and pre-exit same-chain handoff/abort backing.

The first execution had109 passes and5 failures. Three stale fixture expectations
used the old profile/schema/contribution floor; two new fixture failures came
from a getter consuming vm.prank/vm.expectRevert. Fixtures were corrected without
weakening production guards. Final affected selections pass. A duplicate compiler
attempt was stopped before execution to avoid shared-cache writes; it contributes
zero passes. Earlier diagnostics remain in the external campaign evidence.

Final solc0.8.26/Cancun uses the committed via-IR/optimizer1/Yul-disabled profile,
with75 explicit inputs:44 project sources and31 dependency sources, no implicit
or missing sources and stable input/compiler hashes. **37 normal EIP-170/EIP-3860
object gates pass**. [Size evidence](production-size-gates.json) records exact pins.

| Contract | Runtime bytes | Remaining runtime bytes |
| --- | ---: | ---: |
| Vault | 23,523 | 1,053 |
| NFT | 24,400 | 176 |
| Migration / holder settlement | 18,358 | 6,218 |
| AccessController | 9,693 | 14,883 |

The initial normal build caught NFT runtime24,799,223 bytes over the limit.
Sharing stage computation/removing duplicate checks reduced it without changing
compiler or size limits. NFT headroom remains tight; exact release constructor
URI/arguments and target gas still require acceptance.

[Execution binding](execution-source-binding.json) checks all65 project/test
source names referenced by the final EVM artifacts against current exact compiler
metadata hashes. Three files were normalized to Forge's already-tested LF bytes
before the final normal production compile. No Solidity tests were repeated for
subsequent Python/docs changes.

## Backend, keeper and documentation

- 16 new profile4 tests pass in [the final log](backend-profile-final.log).
  An affected historical batch had122 methods:119 initially passed; three stale
  fixtures were corrected and rerun successfully. This is not a fresh whole
 138-method pass. [Earlier result](backend-profile-results.log).
- 11 new automatic-delivery tests pass in [their final log](principal-automation-final-tests.log).
  A separate common keeper selection has85 passes/1 existing platform skip;
  [receipt](principal-automation-existing-keeper.log). These scopes can overlap
  other historical checks and are not added into one global total.
- 19 event/release-gate cases pass in [the final log](event-release-final.log).
  Old custody topics remain historical; PrincipalPaid decodes separately and
  does not enter income replay. New source cannot be approved with old inventory.
- New API/keeper profiles pin accounting4/custody3/V5 and the principal-exit/NFT
  modules. They stop new principal work but preserve old claims, royalty rights,
  exact principal allocation and unknown/null handling. Source profile1/2/3 and
  historical event/journal semantics remain separate.
- Generated callable reference binds the new compiler artifacts:31 contracts,
 606 functions,31 constructors and13 receive hooks. There are no purpose gaps
  or unannotated inputs;122 existing unnamed/public-getter output explanations
  remain counted by the generator. New holder-exit arguments/results are documented.
- Todo, feature reference, roadmap, security/economics/metadata, operator guide,
  repository instructions/context and handoff are reconciled. Current guides do
  not inherit historical external-custodian procedures. Local file links resolve.

## Limits and remaining work

No contract was deployed, sealed or called publicly. Existing Anvil services,
NFTs/LP/balances/journals, websites/server and paused heartbeat are unchanged.
The automatic keeper job is disabled by default; no actual service was enabled.
Its polling/confirmation/gas budgets affect multi-batch completion time.

All buckets must close before Ready. Lost governance or a permanently broken
venue/token can block completion. A receiving contract can reject ETH or lack a
way to release assets; current ERC721 ownership is authoritative, not an inferred
beneficial owner. Ordinary recipient rejection does not block other Ready payouts.
Immediate price/configuration authority and reviewed replacement code remain
separate governance trust boundaries.

Actual independent feeds/routes/VRF, authority/service addresses, OpenSea,
metadata hosting, accounting4 website/inventory, target-chain closing/payout gas,
operating rehearsals, authentic history/provider acceptance and independent
audit/remediation remain open. Historical accounting3 fork and website evidence
keeps its original source scope and does not qualify these changed contracts.
