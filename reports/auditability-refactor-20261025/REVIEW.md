# Auditability refactor - 2026-10-25

The user authorized four previously proposed refactors. This review compares
against `ba91651805051a974070b8a07543fa18d20d3551`; it does not redesign economic
rights, governance, custody or deployment profiles. This is an internal review,
not independent audit or production approval. See [verification](VERIFICATION.md)
for the final compiled and executed scope.

## Changes and protected boundaries

| Change | Implementation | Boundary checked |
| --- | --- | --- |
| Collect/close settlement | [LiquidityManager](../../src/ZZZLiquidityManager.sol) uses private `_settleTakePair`; each caller still constructs its own fixed DECREASE/BURN arguments. | Same checks, native-credit arming/disarming, TAKE_PAIR recipient, token delta, prefund isolation and callback order. No new selector, arbitrary caller action or recipient. |
| Shared v3 validation | [Internal library](../../src/libraries/ZZZV3VenueValidation.sol) and [neutral interfaces](../../src/interfaces/IZZZV3Route.sol), used by Entry and the converter base. | Each caller retains its own source/output policy, runtime pins and fee limits before the shared read-only check. Router/factory/pool/token/fee reads preserve short-circuit order and the existing error selector. |
| Separate converters, neutral implementation | [Abstract base](../../src/base/ZZZRewardConverter.sol), [LP wrapper](../../src/ZZZLPRewardConverter.sol), [royalty wrapper](../../src/ZZZRoyaltyConverter.sol). | Distinct deployed addresses, immutable ledgers, policies and storage. Shared code grants neither ledger rights over the other, and adds no rescue, arbitrary call or custody authority. |
| Financial readability | [Vault](../../src/ZZZVault.sol), [Migration](../../src/ZZZMigration.sol), [CanonicalHandoff](../../src/ZZZCanonicalHandoff.sol). | Private/local NFT and bucket identifiers are explicit; financial branches are expanded. Named private phase, lifecycle and domain constants retain existing numeric values. Public argument names, wire types and ordering remain. |

## Review decisions

- Do not cache the Vault binding across callbacks: the original code rereads it
  after native settlement, and the refactor retains that behavior. New adversarial
  callback tests distinguish those reads, disarmed credits and actual payouts.
  Their mutable binding helper is a controlled test dependency, not a new real
  AccessController rebinding feature.
- Do not combine LP and royalty balances. The neutral abstract implementation is
  inherited independently by each concrete wrapper; the shared library has no
  storage, approvals or fund-moving entry point.
- Do not reorder policy validation around an external read for apparent savings.
  Six poisoned-later-dependency controls exercise each v3 mismatch boundary.
- Do not use an enum that changes public phase encoding. All nine handoff phase
  values, five Access lifecycle values and six domain indices remain unchanged.
- No broad inheritance/dispatcher rewrite, new external library linking, public
  executor or generic financial hook was introduced. Source brevity alone is not
  evidence of lower gas, smaller deployed code or stronger security.

## Corrections during development

Independent review caught an intermediate private identifier collision in
`Vault._join`: its NFT argument and bucket argument were both renamed `bucketId`.
Before compilation/execution, the original source was restored and compiler-AST
declaration references were used to replay explicit NFT/bucket renames, with
parameter-uniqueness checks. The corrected NFT argument controls owner checkpoints,
NFT shares, contribution and membership; the bucket argument controls physical LP
and aggregate shares. The intermediate source and transform hashes are retained
externally. No deployed or persistent-chain state used that intermediate source.

Moving inherited structs requires Solidity source callers to use
`ZZZRewardConverter.RoutePolicy` / `WrapperPolicy`. Existing wire tuple types and
fields remain; `internalType` provenance now names the neutral base. A preliminary
royalty constructor parameter rename was restored to the existing `receiver`
label before compilation. The final compiler comparison distinguishes these
source-level metadata changes from ABI encoding and storage compatibility.
The compiler also lists an identical `InvalidConfiguration()` ABI error twice
for Entry and both converter wrappers because the library declares the same
selector. The comparison explicitly deduplicates only byte-identical error
entries; it does not hide new selectors, different errors or changed function
entries. Raw ABI JSON is therefore not claimed to be byte-identical.

The event generator previously inspected only top-level source files. Two new
nested-base controls reproduced missing events and an undetected indexed-layout
conflict before the fix. The first recursive attempt exposed a field-alias
precedence change on Windows. Discovery now uses deterministic depth/POSIX-name
ordering, preserving existing top-level names while checking nested sources.
All 135 stored descriptors remain byte-for-byte unchanged; 20 affected methods
pass. The negative controls and first failed attempt are retained separately.

Under the unchanged compiler profile, the settlement helper saves 344 runtime
bytes, Entry saves 29 and each converter saves 122. Named typed constants change
Handoff code generation and add 139 runtime bytes; its 3,542-byte runtime margin
passes the normal gate. This is an explicit clarity/size tradeoff, not a claim
that all refactors shrink bytecode. Vault and Migration executable runtimes
remain identical after removing only the compiler metadata trailer. Creation
bytes are not claimed equal, including metadata embedded in child objects.

## Remaining boundaries

Existing Anvil deployments, historical profiles and journals retain their own
runtime identities. A new build's runtime hashes must be captured for its actual
reviewed deployment; ABI compatibility does not approve or silently substitute it.
No existing service, website source/build/server, signer policy, public deployment,
transaction, seal or paused monitor changed.

Actual native website3 acceptance, independent feeds and conversion routes,
VRF, authorities, OpenSea, strategy/gas and operating rehearsals, and independent
audit/remediation remain open in the [sole Todo](../../TODO.md). No internal
refactor closes those external gates. Production NOT APPROVED.
