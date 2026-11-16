# Metadata lifecycle: scenario inventory and current behavior

Reviewed 16 November 2026 against contract source `bb7099b54d4fe4fcbe416f8319aea6df1c64a59e`.
This is an **80-case inventory and static assessment**, not 80 newly executed tests
or proof that every possible failure is covered. Define the expected presentation
first; then verify each transition on the exact release and marketplace.
No contract, artwork, service, configuration or economic behavior changes here.
The sole status owner remains [the metadata Todo task](../TODO.md#task-metadata-ops).

## Direct answers

OpenSea documents reading ERC-721 `tokenURI` and refreshing after ERC-4906 events.
PoPL returns dynamic on-chain JSON and emits those notifications on reveal and
successful contributions. OpenSea can therefore display Activated, Enhanced and
Singularity as metadata changes, subject to actual chain/collection support,
ingestion and media caching. **Instant or already-qualified refresh is not promised.**
[OpenSea updates](https://docs.opensea.io/docs/updating-metadata),
[storage](https://docs.opensea.io/docs/metadata-storage).

After collective LP closure, an activated NFT currently becomes **LP exited**:
zero attached LP, retained royalty eligibility, old rewards and any unpaid
principal entitlement. It does **not** become Dormant. The terminal label currently
uses the existing **Activated image**; there is no fifth terminal image.
LP closed and holder paid are different facts.

## Define the state before the picture

These independent dimensions must remain separate:

| Dimension | Meaning |
| --- | --- |
| Fixed identity | Token ID/mint ordinal, revealed rarity, palette, colors and circuit pattern. Contributions, transfers and market movements do not redraw them. |
| Visual tier | Dormant, Activated, Enhanced, Singularity; thresholds use current marked attached NAV, not lifetime deposits or rewards. |
| Valuation availability | Known value versus unavailable. An outage is not zero principal or loss of activation. |
| LP lifecycle | Open, parked, exiting or closed. Main/residual geometry and contribution availability are separate from rarity. |
| Settlement | Unallocated/allocated/unpaid/paid principal; current reward balances and royalty-window/currency readiness. These are not encoded by the image alone. |
| Canonical identity | Original, preparing/importing, active successor, retired predecessor or cancelled importer. Same token number at a new contract is a different marketplace identity. |
| External display | Current contract answer, emitted notification, marketplace refetch and rendered media may occur at different times. |

Current marked NAV includes both authenticated LP legs, attributed idle and
designated compound apportioned by shares. It excludes unclaimed LP rewards,
royalties, buyback reserves, arbitrary donations and historical contribution USD.
Default Enhanced/Singularity thresholds are $1,000/$10,000 and are governed cosmetic
settings. A market loss below the activation minimum does not undo activation.
See [renderer](../src/ZZZNFTMetadata.sol) and [NFT rules](NFT_METADATA.md).

## Scenario inventory

Each row defines a situation to exercise and records what source inspection
establishes or leaves unresolved. Existing tests were read for context; none was
run in this task. “Needs qualification” is not evidence that the behavior fails.

### A. Identity, mint and reveal

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| A01 | Query an unminted, malformed or wrong-contract ID | `tokenURI` requires an existing owner; reject nonexistent tokens. Clients must keep uint256 IDs exact. |
| A02 | Mint succeeds; randomness is not fulfilled | Embedded unrevealed placeholder; no invented rarity/weight/artwork. No activation before reveal. |
| A03 | VRF words arrive but ordered finalization is pending | Words alone do not finalize traits. Earlier unfinished draws can hold up later ones; do not invent an artwork. |
| A04 | Finalize the original draw | Immutable traits become visible; NFT emits its metadata notification. No reroll or new NFT is created. |
| A05 | Transfer before reveal, then finalize | The same original draw/identity follows the NFT; current ownership does not select rarity or imagery. |
| A06 | Partial sellout, team/allowlist/public mint or sale end changes | Supply/stage eligibility changes do not alter already assigned traits. Sale timing affects royalty timing separately. |
| A07 | Mint pause/resume while old draws remain pending | New draws can stop; original fulfillment/finalization has its own controls. No Dormant-to-Activated transition is implied. |
| A08 | Unrevealed/dormant token remains after terminal exit | Never-activated token stays Dormant and cannot activate. Original valid draws can still finalize/reveal; no new royalty activation arises. JSON lacks the collection-wide permanent closure. |

### B. Activation and LP growth

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| B01 | ERC-20 approval succeeds but contribution is not sent | Approval changes no LP, shares, activation or artwork. |
| B02 | Wallet rejection, pending submission or unresolved receipt | No confirmed upgrade should be displayed. Integration holds the target's confirmed artwork; actual browser/provider qualification remains separate. |
| B03 | Swap, deployment, marginal-LP or final callback guard fails | Contribution reverts atomically; no successful activation/growth metadata event or tier change from that transaction. Gas remains separate. |
| B04 | Activation is confirmed with actual marginal LP | Share/entitlement changes precede `notifyContribution`; metadata derives from confirmed on-chain state. |
| B05 | Growth succeeds without crossing a threshold | Same visual tier; numeric NAV can change. A contribution notification still occurs. |
| B06 | Growth crosses one or several visual thresholds | Choose the final confirmed tier directly, retaining the same palette/rarity/pattern. A skipped intermediate animation is not a missing economic state. |
| B07 | Concurrent contributions to different NFTs or the same bucket | Each transaction is ordered on-chain. Do not give all cards an “Updating” badge; legitimate shared NAV changes may independently affect other tiers. |
| B08 | Transfer, fee/policy change, replacement transaction or reorg during contribution | Verify current ownership, exact transaction and canonical receipt; never infer completion from approval/submission. Marketplace cache may temporarily lag final canonical state. |

### C. Markets, NAV and cosmetic boundaries

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| C01 | ETH/ZZZ market rises without a contribution | Current NAV can upgrade the tier. Enabled watcher detects a stage change; no NFT transfer/top-up is required. |
| C02 | Market falls through one or several tiers, including below $100 | Tier can downgrade to Activated; it does not revert to Dormant or erase royalty activation. |
| C03 | Value equals a threshold or differs by one raw USD18 unit | Renderer uses `>=`; valuation/share rounding matters. Reuse exact integer values, not rounded website dollars. |
| C04 | Price repeatedly oscillates across a threshold | Renderer follows current value; watcher can repeatedly notify subject to job/budget limits. Cosmetic notification cadence/hysteresis needs a policy if churn is a problem. |
| C05 | Price changes substantially but remains in the same tier | Live JSON value changes. Watcher does not fingerprint numeric NAV; consumers caching raw JSON may retain an old number. OpenSea display of this custom field is unqualified. |
| C06 | Sources stale, disagree, revert or fail the strategy price guard | NAV becomes unavailable; renderer uses explicitly labelled Activated fallback. No fabricated zero-valued Dormant position. |
| C07 | Sources recover or disagree differently after a refresh was requested | Recompute from canonical current state; watcher detects availability/stage changes. Old notification is not proof of current value. |
| C08 | External reference manipulation, venue distortion or violent market movement | Financial/valuation guards remain; missing/failing evidence can produce unavailable metadata. This static inventory does not qualify real source honesty. |
| C09 | Donations, LP claims, royalty receipts or buyback reserve changes | Those excluded balances must not inflate attached NAV/tier. Designated compound is the distinct inclusion covered below. |

### D. LP operation, both legs and recovery

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| D01 | Main is active, outside range or earns no current swap fees | In-range status is not activation/rarity. Value the actual assets under price guards; do not make an outside-range NFT Dormant. |
| D02 | Enable optional residual mode; main-only portfolio still exists | Desired configuration alone creates no LP or new tier. Replacement may create the residual later. |
| D03 | Main plus residual, residual fills/becomes mixed, or both become outside | Value both actual legs and idle/compound. Never add raw liquidity units across different tick ranges or ignore the second leg. |
| D04 | Disable residual mode but merge has not executed | Keep both existing legs in NAV. Desired OFF is not proof of residual closure. |
| D05 | Close residual only, leaving its principal idle | Main remains; attributed idle remains backing and part of current marked NAV. Not an LP exit or Dormant transition. |
| D06 | Consolidate residual into main, replace both legs, or move to another admitted ETH/ZZZ pool | Recompute final aggregate NAV after costs; immutable traits remain. No direct per-holder metadata event is emitted by these LP paths; watcher/manual refresh covers changed states. |
| D07 | Harvest assigns the 5% compound reserve; later compound reinvests it | The designated reserve already contributes to marked NAV before reinvestment. Harvest can cross a tier. Compounding must not count the same funds twice. This is established NAV semantics, separate from awaiting actual entrant LP execution. |
| D08 | Mint-only/global/strategy/pool operations pause | Pause alone does not remove LP or royalties. Valid marks can remain available. Watcher can work during ordinary strategy pause; financial actions retain their own controls. |
| D09 | Park, resume, emergency recovery, or any failed manual/automatic operation | Parked custody marks unavailable; successful resume revalues; rollback preserves prior state. Emergency financial bypass does not make a missing USD value known. No direct metadata event on park/resume today. |

### E. Collective exit and principal delivery

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| E01 | Governance starts exit while LP buckets remain open | Future contributions/mint/replacement are blocked. Existing open-bucket metadata can still show its old tier; current JSON has no “exit in progress” flag. |
| E02 | One bucket closes while other buckets remain open | Closed bucket becomes Exited immediately; its activated NFTs return available zero/stage4. Other buckets can still hold LP. |
| E03 | All LP closes, but allocation is delayed or incomplete | LP exited is already the live answer. Explicit per-NFT exit notifications occur later during funded-NFT allocation, creating a cache-lag interval. Enabled watcher or manual refresh can notify earlier. |
| E04 | Allocation completes; payment has not occurred | Principal is an unpaid ETH/ZZZ entitlement, not attached LP or newly earned rewards. Metadata does not distinguish this state from paid. |
| E05 | Governance payout batch pays the holder | Principal paid flag/amount changes in settlement accounting. Metadata has no paid-specific field/event; old fees/future royalties persist. |
| E06 | ETH receiver or ZZZ delivery rejects; later retry succeeds | Failure/deferred delivery must not be labelled “paid” just because LP closed. Use actual principal-return accounting; metadata currently lacks that detail. |
| E07 | Owner uses exceptional authorized recovery/fallback | Final actual recipient/payment must be read from settlement; do not infer it from generic exit description. No new holder action is required in normal direct distribution. |
| E08 | NFT transfers before allocation, after allocation, before payment or after payment | Unpaid principal follows the current NFT; paid principal is not recreated for a buyer. Generic terminal wording needs this distinction. |
| E09 | One owner has mixed dormant/active tiers, several NFTs or zero actual proceeds | Each NFT's shares/paid state is separate. Dormant zero-share NFTs get no principal; zero proceeds is not a failed price read. Visual rarity never weights LP principal. |
| E10 | Everything is paid, LP cannot reopen, later royalties arrive | Activated NFTs stay LP exited and royalty-eligible. “Returned principal entitlement follows this NFT” is currently unchanged even after paid; presentation should be clarified. |

### F. Reward, royalty and ownership boundaries

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| F01 | Claim LP rewards, royalties or both; claim returns zero | Claiming is not a contribution and should not mark artwork as evolving. It does not consume attached principal or deactivate the NFT. |
| F02 | Claim is pending, rejected, reverted or reorganized | Preserve confirmed balances and original transaction recovery; no claimed amount/tier guessed from submission. |
| F03 | Mint sale/one-hour royalty activation window has not ended | Registered royalty weight is not claim readiness. No artwork/deadline badge on a dormant NFT is required by the current product decision. |
| F04 | Royalty currency is newly registered, broken, deferred or recovered | Original-currency accounting/readiness stays separate from fixed rarity weight and visual tier. `royalty_activated` is not a guarantee every currency pays now. |
| F05 | Transfer active or exited NFT with accrued unclaimed rewards | Traits/activation follow the token; current owner owns remaining rights. Cached marketplace owner/traits can update at different times. |
| F06 | NFT sent to contract escrow, inaccessible account or dead address | Ownership does not redraw or deactivate it. Metadata cannot prove a receiving address can later release the NFT or receive all payouts. |
| F07 | Royalties continue after terminal LP exit | Fixed rarity weight persists. Future royalties must not falsely imply principal is still in LP or that LP earnings continue. |

### G. Whole-collection replacement

These cases concern the retained same-chain canonical handoff before terminal
LP exit, with its original freeze/import/backing locks.

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| G01 | Source prepares/freezes and parks for canonical replacement | Keeper stops new notifications in canonical non-operating states. Current renderer may show valuation unavailable rather than an explicit migration stage. |
| G02 | Destination contains NFT ownership but incomplete reward/share imports | Importer can temporarily render Dormant/unavailable. It is not an activated release or marketplace-ready collection. |
| G03 | Atomic source retirement and successor activation | Source emits collection refresh; destination activation lacks a direct NFT metadata notification. Manual/new watcher refresh needs qualification. |
| G04 | Old source NFT remains visible/listed after retirement | Renderer lacks retired/successor JSON despite `canonicalSuccessor()` existing separately. Old metadata can misleadingly resemble a merely parked active collection. |
| G05 | Import cancelled/aborted, wrong profile or partial funding | Do not market importer metadata as live rights or resume old journals under a new identity. Current renderer has no cancelled-importer label. |
| G06 | Successor resumes LP; watcher, API and OpenSea target new contract | Rebind exact canonical deployment/runtime/profile and fresh journal/configuration. Same token number is not sufficient identity; old listings/caches do not automatically move. |

### H. Storage and OpenSea display

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| H01 | Valid on-chain JSON is fetched on the actual chain/collection | Data-URI format is documented by OpenSea; actual Robinhood collection support/onboarding and rendering remain unqualified. |
| H02 | Event mined; OpenSea queues or delays retrieval | ERC-4906 is a notification, not an acknowledgement. No current service verifies OpenSea's eventual metadata/image result. |
| H03 | New traits with old picture, new picture with stale cache, or missing SVG | Verify metadata and media independently. A successful JSON response is not proof the right evolution image rendered. |
| H04 | Root empty, prefix-only, malformed CID, wrong slash or wrong historical artwork | Constructor/`setBaseURI` checks are limited; Access sealing alone is not readiness. Preflight rejects empty/structurally invalid roots and requires reviewed 2,784 paths; actual CID/DAG/content validation remains independent review. |
| H05 | Pin lost, gateway/provider unavailable, payment/retention expires | On-chain JSON can still exist while media fails. Redundant verified retention/retrieval is required; immutable hash is not hosting. |
| H06 | Seal fixes root; later request new circuit/terminal image | A distinct terminal image needs a compatible renderer/path mapping and reviewed content revision before immutable binding/seal. Adding an SVG alone cannot change the hardwired Activated mapping; no arbitrary post-seal image setter exists. |
| H07 | Refresh whole collection or a range with sparse hashed IDs | NFT range accepts at most 50 **mint ordinals**, then emits actual token-ID events. Never pass ordinal bounds as a contiguous hashed-ID interval to a marketplace API. |

### I. Watcher, outages and long-term operation

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| I01 | Watcher disabled or not deployed | No automatic market-only tier notifications. Contribution/reveal events and permissionless manual refresh remain separate. |
| I02 | Keeper stopped for hours/days; restart with old tier checkpoints | Durable identity/cursor/pending state are validated; scan current confirmed state. Intermediate missed cosmetic tiers need not be replayed as current. Actual host rehearsal remains open. |
| I03 | Pending transaction stalls, RPC fails, rate limit or budgets exhausted | Recover pending work first; fail closed or defer new notifications. Do not mark a submission as confirmed or resend a financial action to fix metadata. |
| I04 | Refresh observation/receipt reorganizes or ages out | Canonical observation/receipt checks invalidate stale triggers. Successful notification baseline advances only after confirmation and durable save. |
| I05 | Crash before/after save, corrupt/lost journal or wrong deployment loaded | Preserve/recover original journal/backups; no guessed adoption. A metadata cursor is not a confirmed notification checkpoint. |
| I06 | 1,000 NFTs need refresh while LP work also competes | Default 50 per scan requires at least 20 scan passes, plus shared nonce/receipt/gas/priority delays. No instant collection-wide latency is established. |
| I07 | Early ordinals constantly change; remaining NFTs are stable | Rotating bounded cursor and job priority support fairness. Qualified scan cadence/gas/backlog monitoring still needed. |
| I08 | Operator manually refreshes one token or range | Permissionless event-only calls require no price read and remain callable independent of keeper lifecycle scheduling. They do not repair unavailable valuation, media or economic state. |

### J. Configuration, unusual inputs and consistency

| ID | Case to exercise | Current behavior / assessment |
| --- | --- | --- |
| J01 | Governed cosmetic thresholds change or are restored | Future current-value tiers can change collection-wide; policy emits batch refresh. Preserve fixed traits and all economic rights. |
| J02 | Source/feed/strategy settings change, causing availability or NAV changes | Revalue using current authenticated settings; no direct policy-update promise of per-NFT marketplace completion. Preserve source/profile history. |
| J03 | Invalid uint256 ID, boolean/fractional ordinal, oversized batch or duplicate request | Contract bounds and strict client parsing must remain exact. Same refresh repeated changes no balances; external refresh queues may rate-limit. |
| J04 | Metadata refresh spam or many legitimate simultaneous updates | Event caller pays gas; it cannot choose traits or transfer funds. Bound service/API workload and avoid requiring one NFT operation per historical price sample. |
| J05 | Renderer/module/royalty helper missing or malformed, or tokenURI gas unavailable | NAV errors have a fallback; every dependency failure is not universally caught. Actual release bindings and target marketplace read gas need qualification. |
| J06 | Website, OpenSea and API disagree about unavailable/artwork state | On-chain uses labelled Activated fallback; fresh integration `positionArtwork` returns no art for unavailable value. Choose a consistent explicit fallback without inventing a current tier. |
| J07 | Shared pool market change affects several NFTs during one user's operation | Update legitimately changed confirmed values; a per-operation badge/animation remains scoped to its NFT. Claiming alone is not an evolution animation. |
| J08 | Wrong chain, old source/profile, stale IPFS bundle or demo data is served | Fail unavailable/mismatch; never fill production reads with simulation data. Popldemo, served poplint and local source10 retain separate configuration/rollout status. |

## Material findings to resolve after agreeing the presentation

These are static findings/design questions, not freshly reproduced exploits or
claims that settlement accounting is broken.

| Finding | Current boundary | Recommended direction |
| --- | --- | --- |
| M1: exit notification timing | Live metadata changes at bucket close; per-NFT notification occurs in later allocation. | Notify the relevant closed bucket's NFTs promptly through bounded work; do not require an unbounded loop or successful payments to refresh. |
| M2: pending versus paid principal | JSON has zero LP and generic terminal description, no paid/remaining distinction. | Make terminal wording truthful after payment; consider a small lifecycle/settlement field only where its meaning and refresh trigger are defined. Preserve actual principal ledgers. |
| M3: never-activated token after exit | Remains Dormant with `lp_exited:false`, although activation is permanently closed. | Keep Dormant identity but expose collection lifecycle separately; never award a royalty weight to change its picture. |
| M4: predecessor/importer identity | Renderer lacks retired/successor/cancelled-importer labels; destination activation has no NFT refresh. | Publish accurate canonical lifecycle/successor identity and notify at activation/retirement using bounded or whole-collection events. Review locks and importer staging first. |
| M5: image versus numeric freshness | Watcher compares reveal/availability/tier, not every numeric NAV change; JSON has a custom numeric field. OpenSea display of that field is unqualified. | Prefer marketplace image/trait freshness and live confirmed API values. Define raw-JSON numeric freshness before adding periodic paid writes. No every-tick guarantee. |
| M6: unavailable presentation | Activated fallback on-chain, absent art in fresh integration; market outage can look like a downgrade. | Choose labelled fallback or explicitly stale last-confirmed art per surface. A renderer cannot recover an unstored last-good tier by guessing. |
| M7: terminal artwork | Current terminal uses Activated image. | Keep it with an unmistakable exited label, or review a compatible renderer mapping/content revision before immutable binding/seal. Dormant art is a visual choice, not deactivation. |
| M8: external acceptance | No current end-to-end OpenSea retrieval/cache/latency or matching-host watcher approval. | Rehearse actual supported-chain collection, content, lifecycle events, outage recovery and eventual rendered outcome; notification receipt alone is insufficient. |

Existing source rules already handle fixed identity, current-NAV tiering, downward
evolution, outage availability, whole-unit settlement and a bounded/recoverable
notification path. Reuse their unchanged source-scoped evidence. Do not rerun old
suites merely to refresh a date. Test changed behavior and missing compositions
only after selecting the next implementation scope.

## Verification contract for each scenario

For each selected case record: exact source/profile/runtime and chain/contract;
initial owner/traits/activation; main/residual/idle/compound state; pinned block;
action and expected success/revert; final principal/reward/royalty rights; decoded
`tokenURI`/image/attributes; expected notification and actual receipt; watcher
checkpoint/recovery; marketplace fetched JSON/media and observed time. Keep
**expected**, **statically inspected**, **locally executed** and **externally
observed** evidence separate. A reorg, outage or unsupported marketplace is not
an observed success. Never submit a public transaction or enable a service just
to populate this inventory.

## Source map and primary references

- [NFT](../src/ZZZNFT.sol): `tokenURI`, `notifyContribution`, `refreshMetadata`,
  `refreshMetadataRange`, `setBaseURI`, reveal notification, `canonicalRetire`.
- [Renderer](../src/ZZZNFTMetadata.sol): `currentValue`, `_markedValue`,
  `_evolutionStage`, `render`, terminal image/description and availability.
- [Vault](../src/ZZZVault.sol): actual share issuance and `exitBucketToHolders`.
  [Migration](../src/ZZZMigration.sol): `allocatePrincipal` notification and
  separate `PrincipalPaid` settlement. [Principal API](../frontend_api/principal_return.py).
- [Canonical NFT](../src/ZZZNFTCanonical.sol), [handoff](../src/ZZZCanonicalHandoff.sol):
  staged import, source retirement and destination activation.
- [Policy](../src/ZZZProtocolPolicy.sol): cosmetic threshold configuration/event.
  [Keeper](../keeper/monitor.py): `_refresh_metadata`, `_confirm_metadata`,
  `_validate_metadata_record`, cursor/pending/receipt/lifecycle scheduling.
- [API](../frontend_api/service.py), [collection](../frontend_api/collection.py):
  confirmed current value and authenticated thresholds. Website source inspected
  at `206892ab8b93d65cae3564e71feaf4435f90cdee`:
  [view](https://github.com/ABEF/AAA-website/blob/206892ab8b93d65cae3564e71feaf4435f90cdee/deployment-view.js),
  [principal reader](https://github.com/ABEF/AAA-website/blob/206892ab8b93d65cae3564e71feaf4435f90cdee/deployment-source9-data.js).
  Source behavior is not a claim those profiles are deployed to either site.
- [Preflight](../zzz_ops/production_v6.py): `_nft` content-root/manifest review;
  [current schema17 wrapper](../zzz_ops/production_v15.py).
  [Artwork publication](ARTWORK_PUBLICATION.md), [operator metadata procedure](OPERATOR_MANUAL.md#mint-and-metadata).
- [OpenSea metadata](https://docs.opensea.io/docs/metadata-standards),
  [update events](https://docs.opensea.io/docs/updating-metadata),
  [queued refresh API](https://docs.opensea.io/reference/refresh_nft_metadata),
  [ERC-4906](https://eips.ethereum.org/EIPS/eip-4906), reviewed 16 November 2026.
  The API queues retrieval and requires service access; no API request, key or
  subscription was used in this assessment.
