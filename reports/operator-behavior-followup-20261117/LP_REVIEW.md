# New LP behavior and authorized-keeper recovery evidence

Starting source: `6945eeeba24304b8ddf27ac4c08fe55dc553554e`.
This follow-up adds actual execution evidence for a previously source-described
boundary; it does not claim a new LP accounting exploit or change the accepted
on-chain economics. The user explicitly selected **keeper-software-only**
in-range/below-threshold compounding coordination.

## Newly executed behavior

`OptionalPortfolioCoreTest.testKeeperSoftwareBoundaryActualCompoundAndRevokeRotatePauseRecovery`
executes actual local v4 PoolManager/PositionManager/StateView and production
Vault, Manager, Compounder, Budget, FeeController, Rewards, Membership and NFT:

1. Activate an NFT and create nonzero ETH **and** ZZZ compound reserves from
   actual funded core donation fee growth while the main is active.
2. Move the market outside the main at one hour, before the twelve-hour ordinary
   rebalance minimum. Independently assert stored tick/boundary, raw price side,
   no manual geometry exception and contract compound readiness.
3. Prove an unapproved address cannot compound and leaves physical L unchanged.
4. Using the authorized key, execute compound and prove a nonzero actual
   balancing swap plus increased existing-main L. The maintained keeper would
   wait here; another program with that same authorized key can use this contract-
   permitted operation. This is not an unapproved outsider acquiring authority.
5. Preserve NFT shares, aggregate shares, main ID, centre, rebalance clock and
   no-residual identity; maintain funded reward/reserve backing.
6. Model a confirmed operator revoke/grant: the old key's exact prepared calldata
   rejects as Unauthorized, despite an unexpired deadline. The replacement key
   cannot bypass the existing compound interval.
7. Global pause blocks replacement-key compound **and public harvest**. Funded
   holder claims continue, with exact recipient balance/liability checks.
8. After unpause, real trading and elapsed normal compound interval restore
   eligibility. The replacement key compounds normally, the old grant stays
   revoked, ownership/shares remain and backing stays solvent.

This actual-core test uses explicitly mock authority state, native admission,
Permit2/VRF and controlled correlated price feeds. It does not qualify a real
market or provider. The authority seam is not falsely presented as production
governance authentication.

## Separate production-authority check

`AccessControllerTest.testKeeperRecoveryGovernanceRevokesAndReplacesWhilePausedWithoutRestoringOldGrant`
uses the actual sealed AccessController. It verifies that:

- The old keeper cannot grant replacement/self authority.
- Guardian pause remains separate from governance configuration.
- Current governance can revoke the old keeper and grant the replacement while
  paused.
- The replacement keeper cannot unpause; governance can.
- Unpause does not restore the old grant, change governance or revive bootstrap.

The authority-only graph uses BoundDummy for unused economic roles. Its newly
required `artworkBaseURI()` getter now explicitly returns nonempty test content;
no production seal guard is bypassed. Exactly one affected existing method,
`testSealErasesBootstrap`, verifies the updated valid fixture against the new
artwork-root guard being implemented separately in AccessController.

These two source scopes complement each other; they are not a full actual-
controller-plus-live-market integration campaign.

## Verification and preservation

- **Two new methods and one affected existing method pass**, with no skips or
  failures in their selected executions.
- Three earlier filter attempts selected zero tests. Logs are retained and count
  as zero verification. Selecting the exact new method substring corrected the
  Forge signature filter; no existing portfolio suite was rerun.
- Solidity0.8.26/Cancun, viaIR, optimizer1/Yulfalse are retained; exclusive output
  and cache directories keep historical build artifacts intact.
- No production LP source, loss cap, rights, keeper capability, clock or default
  changes were made by this LP portion. The separate Access artwork seal fix is
  identified separately and source-pinned in the authority build.
- Test-method gas includes many sequential operations/setup and must not be
  described as a single production operation's gas requirement.
- Existing Anvil state, sites, services, signer, databases, pending journals and
  user-paused monitoring are unchanged.

Exact compiler metadata/source hashes, method lists and log digests are in
[LP-evidence.json](LP-evidence.json). Existing broader portfolio campaigns were
inspected for gaps but not rerun or relabelled as fresh checks.

## Recovery limits

Keep the stricter policy in the maintained keeper. Restrict the authorized key,
monitor actual execution and use governance revoke/replace or guardian/global
pause when needed. A program hash is not an on-chain restriction on the key.

Revocation/pause affects contract execution after the relevant governance state
change is included. A valid old-key transaction ordered first can execute; later
revocation does not undo it or cancel its wallet nonce. Preserve its hash and
reconcile actual receipts, spend and pending nonce state. Do not erase journals,
resend automatically or describe key rotation as atomic cancellation of mempool
transactions. Global pause also stops normal harvest; claims remain separate.
