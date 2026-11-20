# OpenSea standard-drop adaptation — reviewable plan only

20 November 2026. Current contract source is the trusted F6/mint2 candidate.
**No contract change, new mint authority, implementation choice, signing,
deployment, sealing or platform approval is made by this plan.** Production is
undeployed and NOT APPROVED. Final LP-pool selection remains operator-deferred.

The recommendation is to prepare and review a narrow standard-drop adaptation,
then decide whether its platform dependencies and trust changes are acceptable.
It is not a claim that adding three selectors makes PoPL compatible with Studio.

## 1. What the current project actually implements

| Component | Current responsibility and limitation |
| --- | --- |
| `ZZZNFT.mintSeaDrop(minter,quantity)` | Accepts only the pinned SeaDrop through its helper, receives zero ETH, reserves/records the whole batch before callbacks, creates dormant NFTs and original asynchronous randomness requests. |
| `src/base/ZZZSeaDropToken.sol` | Forwards six fixed typed configuration families to the helper. Signed-stage and token-gated setters revert. `setMaxSupply` and SeaDrop rotation revert. There is no `owner()` or `multiConfigure`. |
| `ZZZSeaDropMint.configure` | Reviews strictly disjoint inclusive TEAM/ALLOWLIST/PUBLIC windows, quotas, gross price, exact fee recipient, payer commitment and a nonzero Merkle root when restricted supply exists. It does not configure SeaDrop itself. |
| `ZZZSeaDropMint._validatedFingerprint` | Rechecks the exact public drop, payout recipient, Merkle root, fee recipient and payer set; requires **zero signers and zero token-gated collections**. It also binds price and official final sale-end revision. |
| Pinned SeaDrop V1 | Owns proof/signature validation, exact buyer payment, payer permission and atomic fee/creator settlement. Its NFT callback exposes only recipient and quantity, not upstream mint family, signed parameters, salt or signer. |
| Offline tools/readers | Produce/review the current Merkle profile and preserve its exact source identity. Their refusal of `mintSigned` is correct for mint2, not a defect to bypass. |

The retained verified V1 source is in
`reports/opensea-integration-20261109/official-seadrop/verified-sources/src/`.
Its historical runtime witness is not a fresh observation of upstream state.
Do not substitute the latest GitHub source or a generic ERC721SeaDrop template
for that exact dependency or for PoPL's nonsequential token IDs and dynamic
metadata/LP/royalty rights.

## 2. Platform boundary and alternatives

The current [Studio edit API](https://docs.opensea.io/reference/save_drop_edits)
accepts public and signed presale stages and explicitly rejects Merkle presales.
It replaces the complete stage list, places public first in array order, requires
contiguous presale times and describes per-stage wallet additions. A draft save
does not change live on-chain state. These API conventions need verified
translation into SeaDrop parameters; they are not four independent runtime bugs.

The [publish API](https://docs.opensea.io/reference/build_drop_publish_transaction)
returns platform-computed configuration, including signer/fee/payer values, for
the actual on-chain owner. It also describes base-URI publication. Its generated
calldata must be inspected unchanged, not edited to make a review pass.

| Route | When it is viable | Required decision/evidence |
| --- | --- | --- |
| Keep the current Merkle integration | OpenSea explicitly supports a custom route outside the standard edit/publish path for this collection. | Obtain actual custom onboarding, owner/configuration proof, transaction builder, sale and fee terms. Merkle support in the SeaDrop protocol does not establish Studio/API support. |
| Narrow standard signed-stage adaptation | The actual generated payload and signed mint flow can preserve the accepted sale model, and the operator accepts any additional signer dependence explicitly. | Review the proposed changes below and resolve the price/stage-context limitations before implementation. A new source/profile and affected qualification will be needed. |

No OpenSea account, API credential, collection slug, actual configuration payload,
signature or buyer transaction has been accepted here. No third party has been
contacted. The operator has not selected either implementation route.

## 3. Economic and ownership requirements to preserve

- Fixed collection maximum **1,000**; default phase allocations TEAM20,
  ALLOWLIST500 and PUBLIC480 may change only under the existing issued-count and
  reserved-supply constraints. Counters never reset after transfers or edits.
- TEAM is free, with network gas separate. Unused TEAM slots remain reserved.
  ALLOWLIST costs the same governed price as PUBLIC, defaults to **0.05 ETH gross**,
  and permits one NFT per listed address. Unused ALLOWLIST supply may roll into
  public FCFS. Team/allowlist membership and any permitted overlap must be explicit.
- The buyer's paid mint total remains the governed gross price; the creator
  receives the remainder after the **actual accepted** platform fee. No assumed
  10% fee, extra surcharge, proceeds custody, LP funding or royalty credit is added.
- Preserve original recipient, phase and lifetime mint books, maximum batch10,
  receiver reentrancy defenses and exact all-or-revert payment/issuance behavior.
- Preserve the original asynchronous randomness request, no reroll, immutable
  eventual artwork/rarity and normal reveal recovery. This plan qualifies no VRF.
- Official final sale end must still match the royalty ledger. The **one-hour**
  activation window follows that end, even when fewer than1,000 NFTs sell.
  Scheduling changes must not reopen a closed final sale or move old rights.
- Existing NFTs, activation/LP shares, fixed80/10/5/5 LP economics, original-
  currency royalties, transfers and current-owner unpaid rights remain unchanged.

## 4. Important limitations to resolve before coding

### Signed eligibility introduces another authorizer

An approved Merkle root commits the reviewed restricted-sale leaves. Standard
signed presales delegate issuance of mint authorizations to an allowed signer.
Bounded signer parameters constrain that authority but do not recreate the
same immutable commitment. A signer outage can prevent restricted mints; a
compromise can authorize addresses not intended by the operator unless there is
an independent on-chain eligibility constraint. Quantity, per-wallet, phase and
global caps must still protect supply. Do not call that delegation governance-only.

The retained SeaDrop V1 `SignedMintValidationParams` has **minimum mint price,
not a maximum or exact mint price**. It bounds wallet/stage/time values and a fee
range, but `mintSeaDrop(minter,quantity)` cannot see the signed price or stage.
Consequently, enabling a signer and removing the empty-signer check alone cannot
prove free TEAM tickets or exact paid prices against a bad signer. Setting the
paid minimum to the governed price prevents discounts, not overcharging.

The buyer sees and chooses the actual payment, but wallet review is not an
on-chain exact-price guarantee. The operator must decide whether platform-signed
terms plus exact client review are acceptable, or require an authenticated
mint-context/custom path that can enforce those terms. Do not weaken the
requirements silently. The same issue affects stale higher-price tickets after
a governed price reduction. Require a verified invalidation procedure; a local
revision hash absent from the signed payload cannot invalidate it by assertion.

### Shared stage boundaries need explicit handling

PoPL currently requires inclusive, strictly disjoint stage windows. Studio's
contiguous API representation shares boundary timestamps. At equality, upstream
active checks and PoPL's phase classification must not turn an ALLOWLIST mint
into a TEAM issuance or change which reserve it consumes. A half-open local
`currentPhase` or arbitrary one-second offset is not sufficient proof when the
callback carries no upstream stage identity.

Review the actual generated parameter intervals and choose a provable policy.
Possibilities include an accepted custom context path, verified platform
translation, or deliberately refusing shared-boundary mints with corresponding
UI/retry behavior. Any liveness/trust change needs an explicit decision. Test
timestamps on both sides and exactly at each boundary, including delayed mining.

### API wallet additions are not SeaDrop running totals

SeaDrop checks the recipient's lifetime original mints against each supplied
cap. Studio describes additions across stages, including unused allocations
carrying forward. Prove its actual generated signed/public limits against PoPL's
one-ALLOWLIST-NFT rule and explicitly selected public lifetime limit. Cover TEAM,
ALLOWLIST, both/neither memberships, unused entitlements, transfers and duplicate
addresses. Do not approve an API number merely because it equals a contract cap.

### Platform lifecycle may restrict contract configurability

Studio can reject or disable supply/price increases during a live sale. Contract
governance's future-price capabilities do not guarantee product acceptance.
Plan mint pause, exact saved-stage replacement, publish, signed-ticket
invalidation, confirmed readback and reopen. Keep the official final sale end
and royalty cutoff synchronized. Do not promise arbitrary live edits or bypass
platform refusal by writing mismatched contract state.

## 5. Conditional implementation target

Only after the unresolved choices and platform payload are reviewed:

1. **Use a new explicit integration/profile identity.** Preserve current mint2
   source, old deployments, manifests, results and journals unchanged. Define
   new signed settings and semantic commitments; do not reinterpret a nonzero
   Merkle field as signed-stage authorization or reuse the current codec label.
2. **Keep the NFT wrapper small.** Prefer bounded typed preparation/validation in
   the existing fixed NFT-specific helper. No generic executor, arbitrary target,
   delegatecall, proceeds recipient, external minter or mutable SeaDrop singleton.
3. **Add only required compatibility views/entry points.** `owner()` may expose
   the actual existing configuration authority; it must not create a second
   owner, independent transfer/renounce authority or bypass Access. Define how
   bootstrap-before-seal and governance-after-seal ownership proof works with
   platform caching. A read alias does not make unauthorized configuration valid.
4. **Review `multiConfigure` against the actual generated ABI and values.** Use
   exact selector/tuple decoding, zero value, one pinned SeaDrop/runtime and
   bounded arrays/strings. Authenticate the original caller, not a newly trusted
   `this` caller. Preserve operating/preparation/canonical/terminal checks before
   and after external calls. A failed member must revert the complete batch.
5. **Implement signed configuration narrowly, if approved.** Replace the current
   unconditional signed-setter rejection and empty-signer assumption with a
   reviewed bounded signer set and exact policy commitments. Enforce maximum
   wallet/supply/time bounds, intended price protection, exact accepted fee
   range and allowed payer/fee recipient sets. Keep token-gated families disabled.
   Re-read all relevant signer parameters, not just signer-list length.
6. **Keep mint issuance atomic.** Reserve complete lifetime/phase counts before
   VRF/ERC721 callbacks, retain official SeaDrop payer/payment/signature checks,
   and revalidate the full approved configuration after those NFT callbacks.
   Failures in any item or later payout must roll back all issued NFTs, requests,
   counts and digest consumption in the containing transaction.

The existing helper lock ends when the NFT callback returns. SeaDrop then makes
fee/creator payout callbacks using its cached terms. Do not claim the NFT can
revalidate configuration after those later calls or that its lock spans the
whole upstream transaction. Retain that documented boundary and review malicious
payee/governance callback behavior separately; changing it requires a supported,
explicitly reviewed upstream/context design, not an extra local hash assertion.

### Batch fields that must not silently succeed

| Supplied field/family | Proposed admission rule, subject to actual payload review |
| --- | --- |
| `seaDropImpl` | Exact pre-bound singleton/runtime only. No address rotation. |
| `maxSupply` | Zero/no change, or an explicitly supported idempotent1000 assertion. Reject any actual change; do not recreate a mutable supply setter. |
| Public drop | Exact governed price, reviewed window/cumulative wallet cap, accepted fee and restricted recipients. |
| Signers / signed parameters | Matching lengths, bounded canonical sets, no duplicates, exact approved policies and no contradictory add/remove. |
| Fee recipients / payers | Exact reviewed identities, bounds and add/remove semantics. No arbitrary platform-returned permission is automatically trusted. |
| Merkle data | Empty/disabled for a signed-only profile, unless an explicitly designed dual path is separately approved. |
| Token-gated fields | Unsupported; reject nonempty values rather than ignoring them. |
| Base URI / reveal upload | Never replace PoPL's dynamic metadata/artwork root automatically. Existing URI can be set once before seal under current rules; incompatible publication must refuse. |
| `contractURI` / provenance fields | Unsupported nonempty/nonzero changes fail closed unless independently specified and approved. A generic template's setter is not required PoPL behavior. |
| Unknown/trailing data or unreviewed callable | Reject. Do not strip/rewrite platform-generated calldata or silently drop unsupported fields. |

OpenSea's generic metadata upload/reveal flow must be confirmed compatible with
PoPL's original random assignment, huge hashed token IDs and LP-dependent
artwork. Do not switch to sequential IDs, fixed token images, ERC721A or a
different renderer merely to satisfy a template.

### Signed buyer transaction review

Validate the pinned V1 behavior and exact EIP-712 domain: SeaDrop name/version,
chain ID and verifying singleton, plus NFT, effective minter, fee recipient,
all `MintParams` fields and salt. Preserve single-use digest checks and actual
supported ECDSA forms; do not assume contract-signature support. Quantity is not
itself in the retained signed struct, so exact payment, lifetime/stage/global
caps and batch rules remain essential. Test wrong NFT/chain/signer/payer/recipient,
expired/future terms, malformed/high-s signatures, altered fee/price/caps,
signature reuse and rollback after a failed later receiver or payout.

Changing allowed signers/payers, refunding fees or re-signing a ticket must not
reset the NFT's lifetime mint count or change past payment/ownership/royalty
records. No contract or user transaction is prepared for signing by this plan.

## 6. Resource, construction and canonical impact

Reuse only the recorded [F6 normal size evidence](../activation-final-six-20261118/build/final/normal-size-evidence.json)
as a baseline, not as proof of a new implementation:

| Object | Existing runtime / headroom | Existing construction boundary |
| --- | --- | --- |
| NFT | 24,234 /342 bytes | Creation30,924bytes plus exact dynamic constructor arguments. |
| SeaDropMint helper | 20,835 /3,741 bytes | Creation22,236bytes plus128 fixed argument bytes. |
| Access | 10,854 /13,722 bytes | Recorded full initcode48,580/49,152bytes: only572bytes headroom. |
| Royalty / Vault | 24,562 /14;24,544 /32 bytes | Do not add unrelated sale logic to these hosts or assume their transitive constructor graph is unaffected. |

Prefer the existing helper split, but do not assume `multiConfigure` decoding,
signer policy or owner forwarding fits. A new helper, if truly necessary, changes
construction count/order/nonce prediction, binding inventory, runtime pins and
possibly initcode/gas. Reject an oversized design; do not lift the24,576/49,152
gates, padding or operating budgets. No build or measurement is run by this plan.

Review canonical NFT/helper semantic hashes and original phase/lifetime books
for the new signed configuration. Preserve original recipient, ordinal, quotas,
sale-end revision, request identity and royalty eligibility across an allowed
same-chain handoff. Old signatures bind the old NFT and cannot be reinterpreted
for a successor. New peers/profiles must authenticate the actual accepted mint
settings; do not relabel V10 or old checkpoints/journals to avoid a codec review.

## 7. Execution and acceptance sequence

1. Obtain an actual custom-collection ownership/configuration requirement and
   representative **unchanged unsigned** publish and signed-mint payloads. The
   existing offline mint2 reviewer should keep refusing incompatible ones.
2. Present a decision note covering added signer trust, exact-price/free-TEAM
   enforcement, equality-boundary behavior, wallet-cap translation and authority
   view. Obtain explicit implementation authorization; do not infer it from
   approving preparation of this plan.
3. If authorized and feasible, implement the narrow new source/profile and
   offline decoder/configuration changes with a reviewed dependency graph. Keep
   public signing disabled and use a new isolated local fixture only.
4. Verify affected cases: saved-stage replacement/removal, wrong owner or
   signer, prior configuration revival, all boundary seconds, mixed membership,
   partial sellout, reserved team supply, AL rollover, exact fee/net proceeds,
   rejecting receivers/payees, later batch failure, mint pause/restart, pending
   randomness, canonical counts, metadata and final-end/one-hour royalty cutoff.
5. Rebuild only affected artifacts and refresh required size, static, profile,
   canonical, constructor/binding, gas and consumer evidence. Reuse unchanged
   proofs explicitly; no broad unchanged-suite rerun or invented gas result.
6. Actual platform onboarding, provider/VRF qualification, real fee/payer terms,
   target-chain owner transaction, deployed readback and sealing/opening remain
   separate acceptance/authorization gates. Platform draft acceptance is not
   on-chain publication; mined publication is not production approval.

**Stop condition:** if exact accepted sale/ownership/metadata rules cannot be
preserved through the confirmed standard product, retain the current source and
return to the custom-support alternative or an explicitly reviewed requirement
decision. Do not implement a misleading compatibility shim or claim a pass.
