"""Materialize this reviewer's function-to-scenario assignments, not execute tests.

Coverage of catalogue rows is mechanical. Scenario/property assessment is static
reasoning with explicitly reused source-bound evidence; neither is a safety proof.
"""
from pathlib import Path
import hashlib, json, re

ROOT = Path(__file__).resolve().parents[2]
TARGET = Path(__file__).parent
CONTRACTS = {'ZZZNFT', 'ZZZNFTCanonical', 'ZZZNFTMetadata', 'ZZZMembership',
    'ZZZRewards', 'ZZZRoyaltyRewards', 'ZZZRoyaltyFactory', 'ZZZClaimRouter',
    'ZZZLPRewardConverter', 'ZZZRoyaltyConverter'}
FAMILIES = {}


def family(key, property, *cases):
    assert len(cases) >= 3
    FAMILIES[key] = {'reviewed_property': property, 'scenarios': list(cases),
                     'assessment': 'Static reasoning; not newly executed tests.'}


family('constructor', 'Bind immutable identities without preexisting funds becoming holder income.',
    'Zero/no-code/wrong-controller dependencies: inspect constructor validation and transitive bindings; pure renderer accepts a controller without validation and is not itself custody authority.',
    'Predicted-address prefunding before construction: royalty receiver quarantines native balance; factories create distinct isolated ledgers; converter prefunds remain excluded from measured input/output.',
    'Malicious constructor or receiver callback: construction-time NFT address is intentional, factory caller binding is authenticated, failed deployment rolls back all companion creations.')
family('constant-read', 'Read ABI/profile limits; reading a constant grants no authority or existence proof.',
    'Read while unsealed, operating, frozen or retired: literal constants remain the same for this exact runtime.',
    'Unsupported selector/malformed calldata must not be accepted as this typed getter by the consumer.',
    'A matching numeric constant on another contract is not implementation authentication; check runtime and module/ledger binding.')
family('identity-read', 'Expose configured or immutable identity; consumers retain lifecycle and binding checks.',
    'Before bootstrap/configuration, distinguish intentionally unset zero from a qualified dependency.',
    'Wrong contract/chain with matching ABI: verify runtime/controller and canonical module rather than trusting an address label.',
    'After canonical replacement, old identity getters remain historical; use canonical state/successor rather than treating old approval/ledger addresses as current.')
family('mapping-read', 'Raw mapping views expose stored values without proving NFT existence, eligibility or current claimability.',
    'Unknown ID/address, including zero and maximum uint256: default mapping values are not proof of a minted NFT or supported asset.',
    'Read after transfer, claim, conversion and canonical import: NFT-indexed facts differ from wallet ownership and previously paid totals.',
    'Counterfeit or mixed-block reads: reconcile typed values with canonical owner, indices/share denominator and runtime at one confirmed block.')
family('array-read', 'Bounded ordinal/asset arrays distinguish indices, token IDs and unavailable state.',
    'Zero/last valid index and index equal to length: fixed/dynamic array bounds revert where appropriate; mapping ordinal access can instead return zero.',
    'An ordinal is not a random uint256 NFT ID; use tokenAtOrdinal and mintedCount before resolving owner.',
    'After import, admitted history and declared counts must match canonical capture; do not infer support or population from one returned element.')
family('state-read', 'Counters and policy getters describe confirmed state, not guarantees about future execution.',
    'Initial zero state and collection maxima: zero minted/activated/asset counts mean different things; native assets exist from construction.',
    'At pause/preparation/freeze/import/retire boundaries: getter availability does not authorize an economic action.',
    'Read during mutation via a callback: use guarded derived views where required; raw storage getters may expose interim values and are not a transaction safety oracle.')
family('erc721-read', 'Use installed OpenZeppelin ERC721 existence and approval semantics.',
    'ownerOf/getApproved of a nonexistent token revert; balanceOf zero owner reverts; ordinary unowned accounts have zero balance.',
    'Approval and operator rights permit transfer, not holder fee/royalty claims; transfer clears per-token approval.',
    'Read at source retirement or successor import: historical ownership is not active canonical authority; imported approvals are deliberately not preserved.')
family('erc721-approve', 'Standard owner/operator approvals never grant ledger claims or bypass canonical transfer guards.',
    'Unauthorized caller, missing ID or zero operator: installed ERC721 validation rejects forbidden approval cases.',
    'Approval set/revoked immediately before a transfer or claim: only current owner receives claims, and transfer clears token approval.',
    'Approval changes while ownership is frozen: standard approvals may change, but transfer/update remains lifecycle-locked and successor approvals start empty.')
family('erc721-transfer', 'Economic rights remain indexed to the NFT; only current ERC721 authority can transfer.',
    'Wrong from/to, zero receiver, missing token and unauthorized operator reject without moving shares or balances.',
    'Safe receiver reverts/returns wrong selector/transfers onward or reenters: standard callback rollback plus canonical pre/post guards preserve final ownership semantics.',
    'Transfer before or after claim/conversion: unclaimed whole balances/fractions follow NFT, previously paid money does not; approved operators cannot claim.',
    'Unsafe transfer to an incompatible escrow/dead address can strand ownership and rewards; no hidden rescue or burn path is promised.')
family('mint', 'Vault-authenticated safe mint atomically binds one request/ordinal before callbacks, without LP eligibility.',
    'Supply1000, reused ID, zero/incompatible receiver and paused mint: reject and roll back ordinal/request/payment state.',
    'Coordinator zero/duplicate request ID, provider revert or synchronous callback before registration: reject; no minted token or replacement random draw survives.',
    'ERC721 receiver callback transfers NFT, requests another mint, starts preparation or pauses mint: reentrancy/phase/end checks prevent partial new work; valid onward ownership is not a reroll.')
family('random-config', 'Provider/subscription/lane/payment mode bind once before sealing.',
    'Unauthorized, sealed, duplicate configuration or no-code coordinator rejects.',
    'Zero lane/subscription; confirmations outside3..200 or gas outside200000..10000000 reject.',
    'An ABI-compatible coordinator is not evidence of verified randomness or Robinhood support; source-level configuration does not qualify/fund the actual service.')
family('random-settings', 'Only future request gas/confirmations change; pending request words/identities do not.',
    'Unauthorized, preparation/frozen lifecycle or unconfigured randomness rejects.',
    'Boundary settings3/200 confirmations and200000/10000000 gas are bounded; out-of-range changes revert.',
    'Tuning settings during pause cannot cancel/reroll/rebind a submitted request; an old failed callback cannot be retried through this setter.')
family('mint-pause', 'Independent mint pause does not remove existing LP/reward/transfer rights.',
    'Non-governance and canonical/preparation-locked configuration rejects through canConfigure.',
    'Repeated pause/resume is idempotent policy; global pause and lifecycle can still prevent mint.',
    'Callback attempts to change policy during a mint cause the outer guarded operation to revert where its end-state requirement changes.')
family('fulfill', 'Only fixed coordinator can store exactly two original words once for a known epoch-scoped request.',
    'Unknown request, duplicate fulfill, zero/one/three words or unauthorized caller rejects.',
    'Out-of-order authentic fulfillments do not change ordered finalization or consume rarity/artwork quotas.',
    'Epoch change during canonical import distinguishes old request IDs; source capture requires all earlier draws finished, so no legitimate pending source request can rewrite frozen exported traits.')
family('finalize', 'Permissionless ordered draw without replacement preserves exact quotas and fixed artwork identities.',
    'Missing/unfulfilled/already revealed ID or a later mint ordinal rejects without consuming randomness or quotas.',
    'Zero/max random words, quota boundaries and last remaining item map into fixed rarity/artwork inventory; no owner/admin-selectable alternative is accepted.',
    'Transfer between request, fulfillment and finalization does not reroll; one missing earlier fulfillment blocks later reveal and whole-collection handoff by explicit design.')
family('notify', 'Successful Vault share issuance activates existing rarity weight once and emits metadata notification.',
    'Forged caller, nonexistent/unrevealed NFT or zero shares rejects.',
    'Repeated growth cannot multiply royalty/collective eligibility or change rarity/artwork.',
    'Optional royalty-token read failure is isolated by the royalty ledger; ETH/healthy currencies and actual LP commit retain their own checks.')
family('metadata-value', 'Derived LP valuation is marked backing, not gross contributed dollars or redeemable principal.',
    'Missing NFT rejects at NFT entry; dormant revealed NFT reports zero and remains ineligible rather than unavailable.',
    'Active LP with stale/disagreeing price, invalid custody/status/share denominator or failed venue reports unavailable through NFT wrapper; direct renderer currentValue may revert.',
    'Current-value threshold crossing at1000/10000 changes visual stage, never rarity, historical contributions, eligibility or earned rights; zero value of an active NFT is Activated.')
family('metadata-render', 'Rendering is read-only; immutable labels/art paths and escaped JSON cannot alter rights.',
    'Pending traits use unrevealed art/attributes; activated unavailable value uses labelled fallback rather than fabricated dormant state.',
    'Invalid standalone stage/palette/pattern can revert array access; arbitrary standalone inputs do not change canonical NFT state or authorize a claim.',
    'Base strings with quotes/control characters are escaped in JSON image fields; catalogue colors/patterns and stage are fixed bounded values on the canonical tokenURI path.')
family('metadata-refresh', 'Permissionless notification has no valuation cache, trait mutation or financial action.',
    'Missing NFT rejects; valid dormant/active/unavailable-valued IDs only emit notification.',
    'Repeated events or spam cannot mint shares or rewards; callers pay gas.',
    'Notification while paused does not guarantee external marketplace refresh or a new LP value; consumers reread confirmed canonical state.')
family('metadata-batch', 'Refresh uses bounded inclusive mint ordinals, not sequential NFT IDs.',
    'First ordinal zero, reversed bounds or last beyond mintedCount rejects before events.',
    'One and50entries succeed within bound;51entries rejects without partial notification.',
    'Sparse uint256 IDs, transfers and unavailable prices do not change ordinal mapping; events trigger rereads rather than financial writes.')
family('base-config', 'Artwork base is filled once before seal; runtime cannot silently replace existing permanent artwork root.',
    'Unauthorized caller, sealed state, second configuration or empty setter value rejects.',
    'HTTP/javascript/non-permanent scheme rejects; ipfs:// and ar:// prefix validation is not proof of pinned, available, reviewed content.',
    'Malformed-but-prefixed URI is an admission/hosting qualification failure, not a hidden post-seal setter; exact root is checked by canonical import.')
family('royalty-info', 'ERC2981 requests5% in the sale currency, paid to fixed royalty contract; it does not enforce a sale payment.',
    'Zero sale price returns zero amount; maximum uint256 uses full-precision mulDiv without multiplication overflow.',
    'Queried token ID is intentionally unused, including unminted IDs; the receiver remains fixed and not an operator wallet.',
    'Off-platform transfer or ignored royalty request provides no automatic income; only admitted actual receipts back distributions.')
family('lp-admit', 'Append bounded LP reward asset history; admission is not activation-input permission or receipt allocation.',
    'No-code, duplicate or33rdERC20 admission rejects; native zero is already admitted.',
    'Governance adding an asset cannot turn preexisting raw balances into indices/claims or expand contribution inputs.',
    'A newly admitted mutable/taxed/rebasing token remains unsafe despite code existence; future failure can block its checkpoints/payouts and requires admission review.')
family('royalty-admit', 'NFT-authenticated admission quarantines unsupported prefunds and records existing eligible cohort.',
    'Unauthorized caller, zero/no-code/duplicate currency or17thERC20 rejects.',
    'Preexisting donated token balance is accounted/orphaned, not a windfall to newly eligible holders.',
    'A token whose balanceOf reverts fails admission; later blacklist/rebase/upgrade risk is not eliminated by initial balance observation or optional activation isolation.')
family('membership-activate', 'One eligible membership per successfully activated NFT; checkpoints old collective index first.',
    'Non-Vault caller, already eligible or nonexistent NFT rejects.',
    'Current published LP indices are checkpointed at weight zero so dormant entrants cannot claim past allocation.',
    'Growth, transfer, market downgrade, parked/outbound custody or later claims do not add/remove another equal share.')
family('membership-dust', 'Bounded historical funded dust settles for incumbents before membership changes.',
    'Non-Vault caller or wrong canonical phase rejects.',
    'Four historical buckets and33assets remain bounded; immutable admitted currency identities avoid needless broken-venue price calls.',
    'Actual unharvested fees in a different historical venue retain receipt-time policy; this method cannot fabricate external funding or sweep claim liabilities.')
family('checkpoint', 'Authenticated index checkpoint preserves fractions and uses one pre-mutation membership/share snapshot.',
    'Wrong Membership/Vault caller or frozen canonical state rejects.',
    'Zero shares/inactive membership updates paid baseline without granting prior indexed rewards.',
    'All33assets, tiny distributions, repeated checkpoints and later share growth preserve fractions without changing global liabilities or transferring funds.')
family('credit', 'Only actual bound Fees intake advances fixed individual/collective indices with measured backing.',
    'Wrong caller, unsupported asset, zero credited total or zero bucket share supply rejects.',
    'Native exact msg.value and ERC20 exact transfer are mandatory; prefunds cannot substitute for the specific fresh credit.',
    'No collective members quarantines shared amount; fractional global dust remains backed and cannot be claimed twice or swept.')
family('cutoff-credit', 'Frozen cutoff intake is restricted to actual captured canonical settlement.',
    'Wrong Fees module, non-frozen lifecycle, missing capture or canonicalSettling false rejects.',
    'Post-callback phase recheck prevents cutoff work escaping its settlement window.',
    'Captured backing amount grows by exact received credit; ordinary operating intake and historical event replay do not authorize another allocation.')
family('lp-claim', 'Only current owner, directly or authenticated NFT router, receives NFT-indexed funded LP balances.',
    'Prior owner, approved transfer operator, forged router/owner or unsupported asset rejects.',
    'Repeated/zero claims preserve fractions; one claimant cannot change another NFT entitlement, equal denominator or5%reserves.',
    'Rejecting ETH receiver, taxed ERC20 or reentrant same-ledger callback rolls back consumed balances/liabilities; paused strategies/prices do not themselves block funded claims.',
    'Owner may transfer another NFT or add fresh money in a callback; batch current-owner checks and atomic rollback decide later entries, not a frozen initial-wallet assumption.')
family('royalty-claim', 'Only current owner receives actual royalty balances, including pending receipts for the eligible currency cohort.',
    'Wrong current owner/router or unsupported/in-transit currency rejects.',
    'Before/after sync, repeated claims and tiny fractions produce backed amounts without awarding pre-activation/deferred-cohort income.',
    'Rejecting native payout, taxed/rebasing token or same-ledger reentry reverts atomically; healthy currencies can be claimed separately.',
    'Recipient callback can return ETH into the inbox, legitimately leaving new pending income for a later entry; a universal pre-view/output equality requirement would reject this supported behavior.')
family('claimable-lp', 'Derived claimable includes only this NFT individual/equal-collective credits and fractions.',
    'Unactivated/unknown NFT normally has defaultzero; raw getter is not a substitute for owner/existence checks.',
    'Reentrant callback during credit/conversion/payout rejects the derived view rather than exposing a partial settlement balance.',
    'Transfer, top-up and repeated claims retain NFT fractions while paid amounts leave liability; unsupported asset support is separately checked before an executable claim.')
family('claimable-royalty', 'Derived royalty view previews current pending receipts only for the eligible cohort.',
    'Unsupported asset, in-transit custody or backing below accounted rejects; no guessed zero substitutes for a broken dependency.',
    'Deferred newcomer excludes old receipts; recovery baseline prevents historical redistribution when joining future income.',
    'Reentrant callback rejects intermediate conversion/payout reads; frozen source view excludes post-cutoff pending receipts rather than representing them as active earnings.')
family('pending-read', 'Only admitted, locally backed unprocessed royalty money is pending.',
    'Unsupported currency, external custody or negative rebase/backing deficit rejects.',
    'Zero receipts and constructor/admission prefunds differ: quarantined funds are accounted/orphaned, not pending.',
    'Read during payout/conversion callback rejects intermediate balance; later callback refund is legitimately pending after transaction completion.')
family('eligibility-read', 'Currency eligibility is distinct from fixed rarity weight and total activation count.',
    'Unactivated or unknown NFT has ordinalzero and is ineligible even if its default rarity is Commun.',
    'A newly activated NFT deferred for a broken currency remains active for healthy assets and waits for a recorded recovery baseline.',
    'Admission after earlier activations enrolls that existing cohort but quarantines prefunded unsupported receipts; transfer changes owner, not ordinal/weight.')
family('batch-claim', 'At most32unique selected NFT/asset/ledger claims pay the current owner directly and atomically.',
    'Empty/33entry batch, duplicate same-ledger tuple, unsupported asset or unauthorized NFT rejects; same NFT/currency across LP and royalties is intentionally distinct.',
    'Callback transfer before a later selected claim causes current-owner recheck and whole-batch rollback; approved operators cannot receive payouts.',
    'One failing payout/token reverts the batch; user may omit that currency and claim others directly/in a new selected batch.',
    'Native refund or cross-ledger claim from a contract-owner callback can change a later output at the same initial block; returned amounts are raw units, not dollar sums.')
family('lp-convert-batch', 'Convert selected checkpointed whole holder LP credits; do not reallocate or count conversion as new income.',
    'Wrong keeper, paused/preparing/frozen state, native input, unsupported source, empty/33entry/unsorted/duplicate IDs rejects.',
    'Partial batches exclude other NFTs and source fractions; cumulative rounding assigns every output wei to the same individual/collective components.',
    'Concurrent raw claim before conversion reduces selected balances; zero total or stronger minimum can fail without a double claim.',
    'Lying router, taxed input, failed reset/unwrap/payout or callback role/pause change reverts source debits/output credits together.')
family('royalty-convert-batch', 'Convert only selected earned royalties after sync; preserve original cohort and all output attribution.',
    'Wrong keeper/module, preparation/pause/freeze, unsupported/native source or invalid sorted32NFT bound rejects.',
    'Pending receipts settle before selection, while orphaned funds/fractions/unselected NFT balances remain in source currency.',
    'Output is cumulatively assigned to the same NFT balances without a new rarity denominator or another royalty/LP split.',
    'Source/ETH balance mismatch, minimum loss failure, taxed token, reentrancy or callback pause rolls back liabilities, approvals and credits.')
family('sync', 'Permissionless admitted royalty synchronization allocates actual received money to the old eligible cohort before deferred enrollment.',
    'Unsupported token, in-transit custody or balance below accounted rejects; syncAll is intentionally atomic, so isolate healthy currencies with sync(asset).',
    'Empty eligible cohort sends receipts to orphaned; zero receipt recovery can still enroll waiting activations at the current index.',
    'Repeated sync, sender refund and historical cohort recovery cannot reindex the same balance difference or give waiting NFTs older income.')
family('activation-sync', 'Only internal bounded self-call may isolate optional token synchronization.',
    'Direct external caller rejects; no public bypass to ordinary sync/economic phase exists.',
    'Optional balance read revert/OOG/oversized revert is isolated by the caller self-call with no return-data copy.',
    'Caller underfunding cannot selectively defer a healthy asset: minimum remaining gas guards rollback the entire activation instead.')
family('royalty-activate', 'NFT-only permanent weight1/2/3 activates once while failed optional currencies retain prior eligible cohorts.',
    'Wrong NFT caller, missing owner, weight0/>3, duplicate weight or activation1001 rejects.',
    'Pending healthy receipts settle before the new ordinal/weight joins; failed optional currency or native external custody records deferral rather than awarding old money.',
    'Multiple outages/recoveries create ordered nonoverlapping join baselines; binary lookup and preserved fractions exclude every pre-registration receipt.',
    'Full17currency tail-gas bounds remain a real operating qualification requirement; insufficient total transaction gas reverts rather than fabricating successful registration.')
family('royalty-fund', 'Optional funding accepts only exact received admitted ERC20 money and separates preexisting pending receipts.',
    'Native/unknown currency and amountzero rejects; plain ETH transfer uses receive instead.',
    'Taxed/rebasing/lying transfer reverts exact pull and both synchronization changes.',
    'Receipt before new eligibility is settled to the existing cohort; funding does not create NFT activation/LP shares or a manager share.')
family('bind-controller', 'Factory creator binds the royalty controller once atomically; arbitrary users gain no migration authority.',
    'Wrong caller, duplicate controller or no-code controller rejects.',
    'Factory-created ledgers for unrelated callers are separate receivers and are not the canonical NFT royaltyInfo target.',
    'Controller address alone does not make an arbitrary ledger canonical; handoff validates module/nft identity and current release profile.')
family('bind-converter', 'Before seal bind a one-time compatible converter to this exact ledger/controller.',
    'Unauthorized, sealed, second binding or no-code converter rejects.',
    'Wrong immutable ledger/controller rejects; matching ABI alone does not qualify routes or wrapper behavior.',
    'A successor requires its own reviewed converter; predecessor-held source balances and old converter addresses must not be relabelled current.')
family('custody-exit', 'Explicit paused governance exit transfers one entire admitted royalty currency while preserving its old liabilities/cohort.',
    'Wrong governance/pause/preparation, unsupported asset, existing custody, stale nonce/balance or mismatched recipient code/review rejects.',
    'Recipient revert or exact-token transfer failure rolls back custody markers/nonce/funds; a trusted recipient can later refuse return by accepted design.',
    'New NFT activations defer only this currency; funds are not rewritten as claimed or converted and unrelated healthy claims remain separate.')
family('custody-return', 'Exact full currency restoration clears matching custody ID without creating royalty income.',
    'No active custody, stale/wrong ID, partial/excess native value or unexpected ETH on ERC20 return rejects.',
    'Taxed token or insufficient final backing rejects atomically; any donor may restore the exact lost backing, not a redirected manager payout.',
    'Receipts arriving while away remain pending; on recovery they go to the prior eligible cohort before newcomers enroll for future income.')
family('forward-late', 'Retired receiver forwards admitted post-cutoff actual receipts only to its one immediate successor royalty receiver.',
    'Operating/frozen source, unsupported token or invalid/self destination rejects.',
    'Repeated forwarding sends only remaining actual funds; source claims/imported backing are not revived or double credited.',
    'A retired successor may forward onward in another operation; unsupported new currencies and broken tokens remain stranded/blocked rather than swept to an arbitrary address.')
family('canonical-write', 'Only fixed sealed NFT canonical module may write inert importing ownership/traits/header/inventory.',
    'Wrong caller, non-importing phase or unsealed controller rejects.',
    'Typed codec validates header quotas/count/base and record ranges/owner/request epochs; duplicate randomness key or duplicate ERC721 ID rejects.',
    'Import mint deliberately skips receiver callbacks; contract-holder compatibility must be preflighted, and source data authenticity comes from authenticated handoff, not only local field bounds.')
family('canonical-capture', 'Capture bounded immutable source ownership/ledger state only through authenticated freeze/handoff.',
    'Wrong handoff/phase, pending NFT draws, unreturned royalty custody or backing deficit rejects where required.',
    'Source ownership/claims stay frozen while exports proceed; paid indices/fractions and pending royalty cutoff remain distinct.',
    'Raw prefunds are captured/quarantined separately from holder liabilities; all source assets must remain usable for complete movement/abort.')
family('canonical-settle', 'Canonical cutoff synchronization occurs only inside the fixed handoff process; module-specific no-op hooks do not grant authority.',
    'Wrong caller/phase/repeated royalty settlement rejects through module or orchestrator guards.',
    'Cutoff receipts use captured eligible cohorts and backing, not later raw post-freeze deposits.',
    'Interrupted settle/export cannot activate a partially funded destination; no-op NFT/membership/rewards settle functions are inert and must be interpreted with controller orchestration.')
family('canonical-export', 'Rows export a typed bounded frozen snapshot, not live mutable ownership or an arbitrary remote proof.',
    'Wrong source phase, row beyond count or missing reveal/cutoff readiness rejects.',
    'Header, NFT ordinal, asset order, bucket index and fraction rows have distinct shapes; readers must not reuse historical profile codecs.',
    'Deferred royalty baselines are flattened with _paid, preserving old entitlement while not recreating historical outage interval storage.')
family('canonical-import', 'Authenticated monotonic row imports preserve source identity and current codec bounds; semantic authenticity is handoff responsibility.',
    'Wrong handoff/phase, duplicate/out-of-order/out-of-range row or malformed ABI record rejects atomically, including cursor increment rollback.',
    'Invalid quotas/weights/asset order/NFT IDs/share-index fractions/baseURI or backing bounds rejects before successor activation.',
    'Destination prefunds cannot substitute for exact source backing; mutable/broken tokens can prevent import and require a funded abort rather than balance editing.')
family('canonical-validate', 'Validate complete rows, aggregate membership/weights and actual backing before cutover.',
    'Incomplete cursor or imported aggregate count/weight mismatch rejects.',
    'Backing below captured principal/liability plus destination prefund rejects; future callbacks cannot supply a bookkeeping-only substitute.',
    'Standalone validation/read success is not authority to activate or evidence of contract-owner receiver compatibility; fixed orchestrator makes one atomic retirement/activation.')
family('canonical-activate', 'Only fixed handoff activates importing state after final validation; pending prefunds remain quarantined.',
    'Wrong caller/phase rejects; an inherited no-op activation does not bypass controller lifecycle checks.',
    'Royalty receiver extra balance before activation is orphaned and added to prefund bookkeeping, not distributed to imported holders.',
    'Repeated cutover, aborted source or wrong successor cannot reactivate old ledgers or duplicate NFT/claim rights; source approvals are not copied.')
family('canonical-transfer', 'Canonical asset movement is fixed-handoff-only with exact classified backing and one delivery/accept/restore marker.',
    'Wrong caller/phase, zero destination, repeated marker or nonzero value on acknowledgment rejects.',
    'Taxed/reverting asset or rejecting native receiver rolls back marker and balance movement; real tokens are sent before acknowledgment.',
    'Abort releases only accepted exact backing and restores source delivery markers; unrelated destination prefunds remain separate.')
family('canonical-read', 'Canonical counts/backing/records are typed snapshot data, not proof of completion or active ownership.',
    'Before capture, zero snapshot counters are normal and must not be treated as a completed migration.',
    'Out-of-range backing index reverts; nominal count does not prove matching import cursor or actual backing.',
    'After retirement, export/history remains inspectable but cannot authorize operating claims/transfers; use canonical controller state and exact schema.')
family('canonical-retire', 'Retirement notification is handoff-authenticated and does not burn or redeem holder principal.',
    'Wrong caller or lifecycle other than retired rejects.',
    'BatchMetadataUpdate announces re-read; old tokenURI/ownership can remain historical rather than representing current active rights.',
    'No hidden burn/sweep or alternate successor is introduced by the notification; source economic guards remain closed.')
family('route-config', 'Only immediate governance admits typed append-only runtime-pinned conversion routes.',
    'Unauthorized/preparing/frozen caller, missing code/review or mismatched router/factory/pool/currency/fee rejects.',
    'Duplicate route identity rejects; V3/V4 route IDs cannot silently collide or overwrite old policy.',
    'Only ERC20source-to-ETH v4 conversion is accepted here; wrapper-dependent v3 checks are separate. Proxy controls and real depth still require external qualification.')
family('wrapper-config', 'Reviewed immutable-wrapper policy cannot silently admit a changed proxy/admin/implementation.',
    'Wrong governance/phase, zero/wrong runtime or missing review rejects.',
    'Inconsistent direct-code vs proxy tuple, wrong admin owner/getProxyAdmin/getProxyImplementation rejects.',
    'Unused broken/zero wrapper does not block a native v4 conversion; wrapper-compatible ABI and a pin alone do not prove future immutability.')
family('converter-stop', 'Dependency-independent governance stop is reversible without mutating earned balances.',
    'Wrong governance or canonical/preparation phase rejects.',
    'Disabling does not query broken venue/wrapper/token; it does not seize or claim balances.',
    'Re-enable permits attempts only; each operation still validates route, runtime, exact balance, price and loss floor.')
family('route-stop', 'Unknown route rejects; disable is narrow and reopening revalidates dependencies.',
    'Unauthorized/preparing/frozen caller or nonexistent route rejects.',
    'Disable remains possible without reading a failed runtime; no raw arbitrary route becomes admitted.',
    'Re-enable checks current source/router/factory/pool identity and pins; it does not rewrite historical ID or bypass global enabled flag.')
family('loss-policy', 'Governance may set conversion0..1000bps; stronger caller minimum always remains.',
    'Unauthorized/preparing/frozen caller or1001bps rejects.',
    'Zero cap requires full rounded-up oracle output;1%default is not rounding down to a lower output guarantee.',
    'Governance callback cannot reenter the active converter to widen its captured local floor; external governance/feed trust remains, and repeated conversions can still incur cumulative loss.')
family('converter-execute', 'Only immutable bound ledger supplies exact source; exact measured ETH returns to the same ledger.',
    'Wrong caller, disabled route/converter, native/zero source, zero amount/minimum or expired/>10min deadline rejects.',
    'Direct unwrap is exact1:1 with wrapper policy and routezero; native v4 path needs no wrapper, and typed v3 cannot silently fall back.',
    'Lower output, lying return, changed dependency, approval-reset failure, extra/missing source or rejecting ledger payout reverts fully; source/native prefunds stay unchanged.',
    'Price/source/runtime qualification still matters: a fabricated agreeing oracle or malicious approved dependency is not made safe by a numerical minimum.')
family('converter-receive', 'Only currently armed wrapper/v4executor can send conversion ETH through receive.',
    'Unsolicited EOA/direct native transfer rejects while disarmed.',
    'Wrong sender during conversion rejects; armed sender is reset before external ledger payout.',
    'Force-sent ETH can bypass receive but remains in beforeBalance and cannot inflate measured output or become a manager rescue balance.')
family('ledger-receive', 'Plain ETH transfers are cheap and do not execute accounting or external calls.',
    'A2300gas marketplace transfer succeeds without storage writes in the receive function.',
    'Royalty ETH becomes pending until synchronization; LP Rewards raw ETH donation does not advance fee indices.',
    'Forced prefund/callback refund cannot clear liabilities, change weights or trigger compound/buyback; preserve the ledger-specific accounted/prefund rules.')
family('factory-create', 'Any caller may create an isolated NFT-bound royalty receiver; only actual canonical NFT receiver holds protocol rights.',
    'Creator binding/controller assignment are atomic; another caller cannot take over a just-created receiver.',
    'Repeated factory calls create separate ledgers; no canonical module registry is modified by arbitrary creation.',
    'A counterfeit caller contract may create its own receiver/weights, but cannot make it royaltyInfo receiver or acquire another ledger funding/claim authority.')
family('route-query', 'Typed route queries describe append-only policy and enablement, not a usable current execution quote.',
    'Unknown ID: route/v4Route can revert, routeKind/routeExists report absence and enabled is false; consumers must preserve these distinct semantics.',
    'Disabled or changed-runtime route: a recorded policy remains historical but execution separately revalidates pins and enablement.',
    'V3 and V4 use separate typed route records; never decode a known ID with the wrong route kind or infer output currency from a route label.')
family('string-read', 'Collection strings and immutable artwork-root reads are metadata, not financial state or runtime identity.',
    'Initial empty artwork base is an unconfigured draft; name/symbol are initialized literals, and neither proves published artwork availability.',
    'The source can retire while historical names/root remain readable; successor and exact content root must be independently identified.',
    'Arbitrary malformed/misencoded RPC string output must not be accepted as authenticated metadata; no view mutates ownership or reward weights.')
family('interface-read', 'Interface advertisement identifies supported selectors, not implementation quality or financial authority.',
    'ERC721/ERC165/metadata/ERC2981/ERC4906 IDs return installed supported behavior; an arbitrary unknown interface ID is false.',
    '0xffffffff remains unsupported as required by ERC165; claiming an interface at a counterfeit runtime is not a source/runtime check.',
    'Interface support remains historical after retirement and cannot authorize active canonical transfer, royalty payment enforcement or wallet signing.')


def select(c, f):
    name, kind = f['name'], f['kind']
    if kind == 'constructor': return 'constructor'
    if kind == 'receive': return 'converter-receive' if 'Converter' in c else 'ledger-receive'
    if name.startswith('canonicalWrite'): return 'canonical-write'
    canonical = {'canonicalCapture':'canonical-capture', 'canonicalSettle':'canonical-settle',
        'canonicalExport':'canonical-export','canonicalImport':'canonical-import',
        'canonicalValidate':'canonical-validate','canonicalActivate':'canonical-activate',
        'canonicalRelease':'canonical-transfer','canonicalAccept':'canonical-transfer',
        'canonicalRestore':'canonical-transfer','canonicalRetire':'canonical-retire'}
    if name in canonical:return canonical[name]
    if name in ('canonicalCount','canonicalAssetCount','canonicalBacking','canonicalRandomness','canonicalArtwork'):
        return 'canonical-read'
    direct = {'approve':'erc721-approve','setApprovalForAll':'erc721-approve',
        'transferFrom':'erc721-transfer','safeTransferFrom':'erc721-transfer',
        'mint':'mint','configureRandomness':'random-config', 'setRandomnessRequestSettings':'random-settings',
        'setMintPaused':'mint-pause','rawFulfillRandomWords':'fulfill','finalizeTraits':'finalize',
        'notifyContribution':'notify','currentLPValue':'metadata-value','currentValue':'metadata-value',
        'evolution':'metadata-value','tokenURI':'metadata-render','render':'metadata-render',
        'refreshMetadata':'metadata-refresh','refreshMetadataRange':'metadata-batch','setBaseURI':'base-config',
        'royaltyInfo':'royalty-info','addRoyaltyAsset':'royalty-admit','settleDust':'membership-dust',
        'checkpointAll':'checkpoint','checkpointOwner':'checkpoint','creditPool':'credit',
        'creditCanonicalCutoff':'cutoff-credit','claimBatch':'batch-claim','bindCanonicalController':'bind-controller',
        'bindConverter':'bind-converter','sync':'sync','syncAll':'sync','syncForActivation':'activation-sync',
        'fund':'royalty-fund','pending':'pending-read','eligibleFor':'eligibility-read',
        'exitCustody':'custody-exit','returnCustody':'custody-return','forwardLate':'forward-late',
        'addRoute':'route-config','addV4Route':'route-config','configureWrapper':'wrapper-config',
        'setEnabled':'converter-stop','setRouteEnabled':'route-stop','setConversionLossBps':'loss-policy',
        'convert':'converter-execute','create':'factory-create'}
    if name in direct:return direct[name]
    if name=='activate':return 'royalty-activate' if c=='ZZZRoyaltyRewards' else 'membership-activate'
    if name=='addAsset':return 'royalty-admit' if c=='ZZZRoyaltyRewards' else 'lp-admit'
    if name in ('claim','claimFor'):return 'royalty-claim' if c=='ZZZRoyaltyRewards' else 'lp-claim'
    if name=='claimable':return 'claimable-royalty' if c=='ZZZRoyaltyRewards' else 'claimable-lp'
    if name=='convertBatch':return 'royalty-convert-batch' if c=='ZZZRoyaltyRewards' else 'lp-convert-batch'
    if name in ('ownerOf','balanceOf','getApproved','isApprovedForAll'):return 'erc721-read'
    if name in ('route','v4Route','routeKind','routeExists','routeEnabled'):return 'route-query'
    if name in ('name','symbol','artworkBaseURI'):return 'string-read'
    if name=='supportsInterface':return 'interface-read'
    if name in ('assets','rarityRemaining','tokenAtOrdinal'):return 'array-read'
    if name.isupper():return 'constant-read'
    if name in ('access','nft','royalties','royaltyRewards','claimRouter','metadataRenderer', 'canonicalModule',
        'canonicalSuccessor','controller','canonicalController','converter','ledger','wrapper','v4Executor'):
        return 'identity-read'
    if f['inputs']:return 'mapping-read'
    assert f['state_mutability'] in ('view','pure'), (c,f['signature'])
    return 'state-read'


HELPERS = ['src/base/ZZZModule.sol','src/base/ZZZCanonicalLedger.sol',
    'src/base/ZZZRewardConverter.sol','src/libraries/ExactToken.sol','src/libraries/ExactAsset.sol',
    'src/libraries/ZZZArtwork.sol','src/libraries/ZZZV3VenueValidation.sol',
    'node_modules/@openzeppelin/contracts/token/ERC721/ERC721.sol',
    'node_modules/@openzeppelin/contracts/token/ERC721/utils/ERC721Utils.sol',
    'node_modules/@openzeppelin/contracts/utils/ReentrancyGuard.sol',
    'node_modules/@openzeppelin/contracts/utils/math/Math.sol']


def locations(contract, f):
    paths = [contract['source']]
    if 'Converter' in contract['name']: paths.append('src/base/ZZZRewardConverter.sol')
    if f['name'].startswith('canonical'):paths.append('src/base/ZZZCanonicalLedger.sol')
    if contract['name']=='ZZZNFT':paths.append('node_modules/@openzeppelin/contracts/token/ERC721/ERC721.sol')
    paths.append('src/base/ZZZModule.sol')
    name=f['name'];result=[]
    for namepath in paths:
        for line,text in enumerate((ROOT/namepath).read_text().splitlines(),1):
            if (re.search(r'\bfunction\s+'+re.escape(name)+r'\s*\(',text) or
                (f['kind']=='constructor' and re.search(r'\bconstructor\s*\(',text)) or
                (f['kind']=='receive' and re.search(r'\breceive\s*\(',text)) or
                (re.search(r'\bpublic\b',text) and re.search(r'\b'+re.escape(name)+r'\b',text))):
                result.append({'path':namepath,'line':line})
    assert result,(contract['name'],f['signature'])
    return result


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    reference=json.loads((ROOT/'docs/function-reference.json').read_text())
    rows=[];owned=[c for c in reference['contracts'] if c['name'] in CONTRACTS]
    for c in owned:
        for f in c['functions']:
            key=select(c['name'],f)
            rows.append({'contract':c['name'],'signature':f['signature'],'kind':f['kind'],
                'state_mutability':f['state_mutability'],'source_locations':locations(c,f),
                'purpose':f['purpose'],'authority':f['access'],'scenario_family':key,
                'scenarios':FAMILIES[key]['scenarios'],'reviewed_property':FAMILIES[key]['reviewed_property'],
                'assessment':'static-reviewed; no new execution claimed',
                'evidence':['reports/market-adversarial-20261026/bindings.json',
                    'reports/reward-allocation-20261026/VERIFICATION.md',
                    'reports/market-adversarial-20261026/VERIFICATION.md']})
    source_names={c['source'] for c in owned}|set(HELPERS)
    # Source pins are independently checked; a report pointer alone is not reuse.
    existing=json.loads((ROOT/'reports/market-adversarial-20261026/bindings.json').read_text())
    pins=existing['source_sha256']
    reused={n:sha(ROOT/n)==pins.get(n) for n in source_names}
    assert all(reused.values()),[n for n,ok in reused.items() if not ok]
    result={'schema':1,'baseline_commit':'c3289a844f304803495597298688b1d6d89862be',
        'scope':'Static adversarial assessment of the ten assigned concrete rights contracts and transitive helpers; catalogue coverage is not execution completeness or a security proof.',
        'catalog_sha256':sha(ROOT/'docs/function-reference.json'),'contracts':sorted(CONTRACTS),
        'row_count':len(rows),'function_count':sum(r['kind']=='function' for r in rows),
        'constructor_count':sum(r['kind']=='constructor' for r in rows),'receive_count':sum(r['kind']=='receive' for r in rows),
        'families':FAMILIES,'rows':rows,'source_sha256':{n:sha(ROOT/n) for n in sorted(source_names)},
        'unchanged_against_prior_closed_ast':reused,
        'helper_review':{
            'ZZZModule':'Pre/post governance, phase and canonical guards; fixed caller authentication; live vs economic/claim separation.',
            'ZZZCanonicalLedger':'Monotonic import cursor, classified backing vs prefunds, exact delivery/accept/restore and funded abort markers.',
            'ZZZRewardConverter':'Fixed ledger, source/native before balances, typed routes/runtime pins, exact approvals/reset, unwrap, min/max deadline and minimum output.',
            'ExactToken/ExactAsset':'Sender and receiver deltas reject taxes/rebases; native exact-balance loss checks; callbacks remain explicit interaction boundaries.',
            'ZZZArtwork':'Packed finite inventory, sparse without-replacement draw indices, bounded palette/pattern paths and rarity-independent color masks.',
            'ERC721/ERC721Utils':'Inherited approval/existence/receiver callback, cleared token approval after transfer, unsafe transfer limitations.',
            'ReentrancyGuard/Math':'Ledger mutation locks and derived-view guard; mulDiv/mulmod fractions and cumulative floor conservation.'},
        'new_tests_executed':0,'production_source_changed':False,'confirmed_new_exploits':[],
        'cross_layer_observations':[{
            'id':'R-OBS-1','topic':'Exact claim preview equality is conditional',
            'assessment':'Existing supported contract-recipient callback behavior, not an exploitable defect.',
            'details':'At an unchanged block with an inert EOA recipient, royalty claimable preview and claim sync use the same pending index/cohort, and LP checkpoints use the same indices. A contract recipient can legitimately donate ETH to the royalty receiver or claim another ledger before later router entries. Universal equality of each pre-read claimable and batch return would reject valid flows. Callback transfer can instead correctly revert the whole batch.',
            'source':['src/ZZZClaimRouter.sol','src/ZZZRoyaltyRewards.sol','test/ClaimRouter.t.sol'],
            'suggested_action':'Do not add unconditional equality checks without an explicit callback-free policy; keep source/profile/runtime checks and exact simulation results separate from pre-read advisory balances.'}],
        'unresolved_or_accepted_risks':[
            'No qualified live VRF provider/subscription; permanent coordinator outage can block ordered reveal and whole-collection handoff. Existing mint-only pause/settings cannot reroll or retry old requests.',
            'ERC2981 royalties remain voluntary; admitted unsupported, blacklisted, rebasing, mutable or unreadable tokens can block their own payouts and full canonical migration.',
            'Unsafe ERC721 transfer/dead keys/incompatible imported escrow can strand an NFT; immutable principal nonredemption means there is no secret rescue or burn to remove its share.',
            'Immediate governance and approved dependencies/custodian remain trusted; source review cannot prevent malicious future policy/dependency choices.',
            'Actual conversion route depth/fees, gas at maximum asset/holder state, marketplace settlement and independent audit/rehearsals remain unqualified.',
            'Per-operation loss limits do not cap cumulative conversion/maintenance losses, market loss or impermanent loss; no cumulative cap was authorized.'],
        'primary_sources':[
            {'url':'https://eips.ethereum.org/EIPS/eip-721','use':'Standard existence/approval/receiver semantics; local installed OpenZeppelin implementation remains authoritative for this candidate.'},
            {'url':'https://eips.ethereum.org/EIPS/eip-2981','use':'Royalty request and sale-price currency; voluntary marketplace transfer, not universal enforcement.'},
            {'url':'https://docs.chain.link/vrf/v2-5/security','use':'Match request IDs, confirmations appropriate to value at risk, no cancellation/reroll, bounded callback and provider/subscription funding; not proof of Robinhood support.'}]}
    (TARGET/'rights-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:result[k] for k in ('row_count','function_count','constructor_count','receive_count','new_tests_executed')}))


if __name__=='__main__':main()
