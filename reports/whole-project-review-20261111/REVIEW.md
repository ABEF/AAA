# Project review and corrections — 11 November 2026

This review covers the current local PoPL candidate, including the previously unpublished
9 November spot-reader work, and the separate website checkout. It distinguishes
confirmed defects, behavior-preserving cleanup, stale fixtures/docs, intentional
compatibility and decisions needing review. It is not independent production
approval or a guarantee that every possible defect has been found.

## What changed

| Finding | Confirmed problem and correction | Boundary |
| --- | --- | --- |
| Fixed-pair LP cleanup | Current Rewards admission/import permits only native ETH and fixed ZZZ, yet pricing, membership dust and metadata still scanned foreign historical LP currencies. Removed unreachable scans/calls and their unused private interfaces. Four runtime bodies shrink by3413bytes combined. | Concrete ABI/storage and legitimate pair NAV, shares, principal and reward rights are preserved. Historical-value selectors remain explicit zero compatibility reads. Royalty currencies remain separate. |
| Exact transaction encoding | The shared ABI codec could truncate floats, coerce booleans into uints or accept custom numeric conversions. It now requires exact integers/digits-only decimal strings and canonical bool/int0/1 values. | Existing valid precision/leading-zero decimal strings are retained. No externally exploitable theft was demonstrated; public parsers already validate most inputs. |
| Indexer admission | Duplicate normalized tracked addresses could create a writer database the history reader rejects. Reject malformed/non-list/empty/duplicate inventories before RPC, filesystem or SQLite work. | Valid sorted identity/reordering remains. Existing databases are neither rewritten nor migrated. |
| Keeper final budget/deadline | Generic jobs could cross UTC midnight or expire during slow pre-send reads, then publish an intent using an old day's budget/deadline. Recheck final head, known deadline and current-day caps immediately before intent. | No recalculated calldata, higher cap, charge-on-submission, new nonce or resend. Pending-first same-hash recovery remains. Inclusion may still occur later. |
| Keeper simulation ABI | Known void jobs accepted malformed/nonempty simulation output; observations accepted noncanonical bool output. Validate exact known return shapes before preparing any intent. | Principal batch counts and unknown/historical return semantics are not guessed. Source/dependency honesty is not proved by ABI shape. |
| Website module graph | Configured read profiles lacked required source10 modules in the regular build and several modules in the development allowlist. Added exact files and graph regressions. | Null-config public simulation was not broken by that missing import. Integration build already had recursive closure. No build/dist or live server was changed. |
| Demo source drift | New simulation actions still presented four inputs, old pools and99%/1% wording. New `demo_policy:2` intents use ETH/ZZZ, one ZZZ/ETH pool and97%/3%. Removed six unused app imports. | Unversioned old events retain their assets/pools/small top-ups/LP-only claim meaning. Seed and mixed legacy replay hashes are unchanged; no stored collection reset. |
| Stale current tests | Current NativeCustody expected canonicalV8; native Entry setup used an ERC20-only registry fixture; a funded ETH fee test claimed ZZZ. Corrected schema and explicitly synthetic native fixtures; funded both assets and checked actual claims. | Production registry/financial guards are not relaxed. Native NAV fixtures do not qualify actual Uniswap markets. Original failures are retained. |
| Verification/documentation drift | Four existing keeper regression modules were absent from its maintained selector. Restored them and registered new regressions. Security guidance still described removed external custody and unimplemented minting; corrected current custody/mint/profile claims. Added the missing VRF review-hash example field. | Historical evidence/codecs remain source-scoped. Current docs no longer describe foreign LP currencies as a release requirement. |

The [verification record](VERIFICATION.md) links source/compiler/test/static and
preservation evidence. The [operator manual](../../docs/OPERATOR_MANUAL.md),
[sole Todo](../../TODO.md), [feature reference](../../docs/IMPLEMENTATION_STATUS.md)
and [security model](../../docs/SECURITY.md) describe the resulting candidate.

## Invariants behind the cleanup

Rewards starts with ETH; its only additional ordinary asset must equal the fixed
`ActivationAssets.zzz()`. Canonical asset writes require the same identity and
at most two ordered assets. Current canonical capture/import authenticates the
matching V10 source/profile; old V8/V9 foreign-asset layouts cannot be relabeled.
Pool admission requires native ETH plus that same immutable ZZZ. Fee allocation
is Vault-only and accepts only the current pool currencies. Consequently an
honest current deployment cannot create foreign LP compound to scan.

Main, optional residual, attributed idle and designated **pair** compound remain
backing. Current-owner claims, exact-unit LP/royalty books, fixed80/10/5/5,
activated equal membership and rarity royalties are unchanged. Compatibility
zero getters are retained for existing readers. The canonical input/body bounds
and wire layouts are not silently redesigned. Reviewed replacement-code trust
does not establish that arbitrary malicious replacement code honors these rules.

## Decisions and release gates

| Priority | Needs review | Concrete choices / next evidence |
| --- | --- | --- |
| Before source/venue admission | **Live spot-reference coupling is broader than contributions.** Ordinary Manager balance/swap/mint/increase freezes complete Oracle fingerprints. Trading in the reference changes spot; placing LP there changes L. Rebalance, compound, pool movement and Manager buyback can reject too. | Reserve genuinely independent reference pools not modified by any configured normal destination/route, or design/review a different snapshot/context mechanism. The largest TVL market may also be the best execution venue. Do not simply remove fingerprints or duplicate one pool behind two ETH feeds. Earned-LP conversion and explicit governance emergency use separate paths. |
| Before accepting keeper risk | **Compounding's in-range/below-threshold rule is service-only.** During the hard rebalance cooldown, an authorized compromised keeper can call the contract's otherwise eligible compound path despite that service rule. | Keep the explicitly chosen service policy and its trusted-key risk, or approve a separate on-chain restriction with its liveness/emergency tradeoffs. This review does not silently overrule the earlier keeper-side decision. Financial caps remain. |
| Before additional contract features | **Vault runtime headroom remains32bytes** under the pinned normal profile. The cleanup reduces other contracts, not this custody runtime. | Keep the exact current build or move future code into narrowly typed reviewed helpers before exceeding EIP170. Do not raise size/compiler limits to hide deployment failure. |
| Before market approval | Independent ZZZ source paths/ETH publication/liveness, external two-direction depth and compatible routes are not qualified. Spot can be temporarily manipulated even in a large market. Buyback needs a genuine supported fixed-ZZZ burn and exact supply reduction. | Select actual reviewed dependencies and operating parameters, simulate whole operations at authentic depth and qualify recovery. Do not fabricate an oracle, peg, liquidity or fee-compatible route. Source availability and guard agreement are separate from safe execution. |
| Before installing source fixes | **Checkpoint1/2 pins include the ABI helper.** New source must reject an old checkpoint even though valid-call economics are unchanged. | When adopting the backend with optional checkpoint1/2 enabled, preserve old artifacts/raw logs/WAL backups and explicitly rebuild/review and re-pin a new checkpoint. Preserve pending keeper intents and reconcile nonce/receipts. Do not relabel an old artifact or deployed runtime. |
| Before production operations | Current API/RPC/archive, expanded currencies/claims, real concurrency, correct-chain gas and Unix restart/restore are not qualified by these local fixtures. Supported VRF/OpenSea onboarding, authority/key recovery and independent audit remain open. | Execute the existing release/operating gates with exact deployment/source/configuration pins. The user's deferred broad load campaign is not silently made mandatory here. Unit successes and Windows skips do not prove sustained uptime. |

The original spot/TWAP decision, two-source requirement, current3% contribution,
1% conversion,3% maintenance,1% additional execution and3% source agreement remain.
No ownership/custody/economic-rights change, new withdrawal/sweep or loss-limit
relaxation is introduced. A manual governance emergency remains its separately
accepted high-trust path; it is not an automatic failed-maintenance fallback.

## Retained intentionally

- Old accounting/API/readers/codecs and journals authenticate existing historical
  profiles. Deleting them by keyword would break evidence/recovery.
- Multi-currency royalties and optional v3/WETH earned-LP conversion are not extra
  activation inputs. Only ETH and fixed ZZZ enter current principal.
- Original-asset LP claims remain an explicit holder escape when conversion is
  unavailable; normal ETH settlement is not a promise that every raw balance has
  already been converted. See [settlement rules](../../docs/LP_ETH_SETTLEMENT.md).
- Canonical replacement preserves NFTs and both ledgers before terminal exit.
  It is different from same-pair LP movement and does not implement a bridge.
- Unsupported/unregistered/zero-cohort royalties may require reviewed allocation;
  blacklisted tokens or rejecting receivers cannot be guaranteed transferable.
- Historical reports and original failures remain immutable; old record counts
  are not promoted to a current full audit.

## Coverage and practical limits

The contract/backend task inventory records750 current code/config/docs/test
text files, including60Solidity sources, keeper, API, indexer and shared tools.
The website's module boundaries and checks are recorded separately. Inventory/hash
coverage is not the same as line-by-line manual or execution coverage.
Contract review follows all current source components and
critical lifecycle interactions; backend/frontend/keeper review records exact
workflow scope. Tests concentrate on changed behavior and affected consumers.
Generated catalogues, old evidence and pinned dependencies are inspected through
their relevant interfaces/scopes rather than claimed universally re-audited.

No fresh actual-market multi-day/1000-user/physical hybrid strategy campaign was
run. Physical two-leg custody logic is unchanged and earlier evidence remains
scoped. Explicit host skips, stale fixtures and failed attempts are preserved.
The evidence does not establish that all adversarial behavior has been exhausted.

## Adoption and publication

Source/docs changes require matching reviewed builds/configuration before use.
Sealed existing contracts cannot be patched in place. Current browser source10
remains unsigned; shared signing stays Anvil-only and both public configurations
remain null. Popldemo and served poplint remain unchanged. No service/website
rollout, public transaction, sealing, local-chain reset, journal mutation or
paused-heartbeat restart is authorized or performed by this review.

Publication and exact revision checks are recorded separately from these local
results; published CI/target operation is not implied by local verification.
