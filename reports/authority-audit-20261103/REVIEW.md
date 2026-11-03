# Authority review and governance-only terminal batches

3November2026, source base main db8033ec5f193e472ff70ac82197d8ad1570461a.
Fresh candidate **accounting6/custody5/schema10/Entry3**; undeployed and production
NOT APPROVED. This is an internal access-control/change review, not an independent
whole-protocol audit or proof that no exploit exists.

## Result and intentional public actions

No additional unauthorized discretionary-management path was established in the
reviewed scope. Configuration/custody administration remains governance-only
(after sealing), while owners claim their own rewards, the authorized keeper
performs bounded maintenance, and pinned dependencies retain their callbacks.

The compiler/reference inventory covers37 concrete contracts/818 functions:
241 mutable endpoints and577 view/pure entries, plus37 constructors and13 native
receivers. Mutable entries resolve effective inherited implementations, not just
local visibility. Source review traces inline/transitive guards, authentication
through fixed modules, callback contexts, lifecycle and post-call checks.
[Inventory](AUTHORITY_INVENTORY.json), [permission guide](../../docs/ACCESS_PERMISSIONS.md),
[complete callable reference](../../docs/CONTRACT_FUNCTIONS.md).

Intentional non-governance paths include owner claims/contributions/standard
ERC721 transfers, keeper maintenance, permissionless fixed-allocation harvest,
actual royalty funding/synchronization, event-only metadata refresh and finalizing
already fulfilled ordered draws. Canonical public progress relays are phase-bound
and each imported row matches authenticated source output; they cannot authorize
a plan or choose another recipient. Factories create caller-bound children at
caller cost and cannot seize existing modules. Pool callbacks require the pinned
manager and one-time pending payload; VRF callbacks require the original request
coordinator. Public review/state hashes confer no authority.

## Authorized behavior change

A-01: Previously anyone could allocate or push already-authorized terminal
principal, without redirecting it. The user chose governance-only batches. Added
the existing onlyGovernance pre/post checks to allocatePrincipal and
distributePrincipal. This tightens authority; the old public path was not shown
to steal funds. Governance pays/submits each bounded batch; keep the limited keeper
payout job disabled. Each payout remains current-owner-only, isolated and backed.

**Reward claims were not restricted.** Current owners retain accrued LP rewards,
royalties and owner fallback principal. Previously earned rights follow the NFT;
terminal principal is not earned income. The fixed80/10/5/5 and royalty weights,
LP strategy, withdrawal guarantees and absence of external custody recipient remain.

A-02: Explicit custody5/schema10 prevents new permission semantics from being
silently attached to old runtime/config/journal profiles. Fresh API/keeper reads
check declared custody5; omission keeps historical4 and rejects actual5. Every
fresh lineage peer declares its own custody version. New validator/observer8
use20helpers/Entry3; historical9 stays behind historical-consistency. Keeper
rejects enabled principal_distribution on5 without blocking pending-first recovery.

A-03: First normal build exceeded runtime size by20bytes. Reused the current
owner authenticated immediately in each of two private payout callers, with no
intervening external call, instead of querying ownerOf again inside _pay.
This private refactor preserves recipient/error/paid/backing/reentrancy semantics
and the payout-start owner event. No public signature/storage layout changed.
Final Migration runtime24537, margin39; Vault635/Budget237/Balancer360 unchanged.
These margins are exact-source object gates, not target gas or future capacity.

## Review boundaries and residual risks

Existing ZZZModule governance checks use canConfigure before/after callbacks;
Access erases bootstrap at seal, two-step no-delay governance change authenticates
the pending wallet, guardian only pauses, fixed module handoff transitions cannot
be invoked by an arbitrary payer. Operator and keeper keys may technically be
identical; that intentionally merges compromise risks. Do not store governance
credentials on a keeper host. Production addresses remain unselected.

Immediate governance, optional paused financial bypass, approved replacement code,
upstream proxy behavior and key custody remain accepted trust risks. A lost
operator can delay principal allocation/delivery; rejecting receivers, broken
assets/venues and inclusion/gas failures remain liveness risks. No force can make
an incompatible receiver accept native ETH. Owner fallback remains separate.

Real feeds/routes/VRF/authorities/OpenSea, fresh services/site, target gas/market
conditions, maximum1000-holder delivery, recovery and independent audit/remediation
remain release gates. No deployment, sealing, public transaction, service/site,
Anvil/journal/signer or paused-heartbeat change occurred.

Primary reference basis: [OpenZeppelin access control](https://docs.openzeppelin.com/contracts/5.x/access-control)
and [ERC721 owner/approval semantics](https://eips.ethereum.org/EIPS/eip-721).
Standards do not prove this implementation; source/behavior evidence below does
not eliminate the stated risks. [Verification](VERIFICATION.md).
