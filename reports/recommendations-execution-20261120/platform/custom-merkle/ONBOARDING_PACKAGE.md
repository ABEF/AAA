# Custom OpenSea Merkle path — qualification package

## Decision and preserved contract model

The operator selected qualifying a **custom OpenSea path** for the existing
mint2 Merkle design. Standard Studio's documented Merkle-stage rejection is not
evidence that a custom path is supported. No authenticated custom onboarding
response or actual mint/configuration payload is available yet. This package is
prepared for review; it sends no message or request to OpenSea.

The intended integration uses the unchanged, pinned SeaDrop and PoPL contract
interfaces. It does not introduce a new minter/signer, an arbitrary executor,
platform ownership of the NFT, a custom payment custody address or a fee bypass.

| Preserve | Current requirement |
| --- | --- |
| Collection and rarity | At most 1,000 nonsequential ERC-721 IDs; original asynchronous draw, eventual fixed artwork/rarity and dynamic LP lifecycle metadata. |
| Free TEAM | Initial quota 20; exact free entitlements; unused team slots reserved. Actual addresses/quantities still required. |
| Paid ALLOWLIST | Initial quota 500; one original mint per listed address; exact governed price, currently 0.05 ETH gross. |
| Public FCFS | Initial base 480; unused allowlist supply rolls into public. Governed price matches ALLOWLIST. |
| Platform fee | Buyer pays the governed gross price; creator receives the remainder after actual accepted fees. No extra surcharge is inferred. |
| Eligibility proof | Exact current `keccak256(abi.encode(address,MintParams))` leaves and bounded proofs; no double-hashed StandardMerkleTree substitution. |
| Configuration | Current typed governance calls and reviewed Merkle/public/payer/fee/payout fingerprints; no assumed `owner()` or `multiConfigure`. |
| Time and royalties | Strictly disjoint inclusive stages; official final sale end matches royalty accounting; one-hour activation window follows even without sellout. |
| NFT economic rights | Mint creates dormant ownership; activation/LP shares, 80/10/5/5, original-currency royalties and current-owner unpaid rights remain unchanged. |

These quota/price defaults are governed under existing constraints, not frozen
by this package. Actual changed terms require new source-bound manifests and
fresh transaction review; old proofs and successful illustrative examples are
not relabeled as matching new configuration.

## Required platform evidence

Separate feasibility from actual deployed acceptance. Before authorizing any
public deployment, obtain confirmation that the chain, source/ABI, Merkle flow,
configuration ownership and sale terms are supportable through a custom path.
Actual collection/runtime/counter/payload and end-to-end receipt checks require
the separately authorized deployment and later integration gates. Missing
undeployed addresses are not filled with the illustrative examples, and this
package does not authorize deploying merely to answer those questions.

| Evidence to obtain | Acceptance rule | Status |
| --- | --- | --- |
| Custom drop onboarding for Robinhood chain 4663 | Platform explicitly accepts this deployed custom collection and its supported exact SeaDrop/Merkle path. Generic SeaDrop availability is insufficient. | Unknown |
| Actual collection identifier and address | Exact chain/NFT/runtime agrees with the reviewed deployment; no dummy addresses. | Unknown |
| Custom configuration procedure | Each target, selector and caller preserves PoPL governance and current typed setters. A standard Studio payload requiring unsupported selectors is rejected. | Unknown |
| Actual unsigned TEAM mint payload | `mintAllowList` recipient/proof/terms/quantity match the free phase; native value exactly zero. | Unknown |
| Actual unsigned ALLOWLIST mint payload | Same Merkle path; exact approved leaf; one-per-address counters and gross payment respected. | Unknown |
| Actual unsigned PUBLIC mint payload | Supported `mintPublic` recipient, quantity, governed gross value and public/reserved supply rules. | Unknown |
| Proof delivery and account changes | Wallet/account, NFT/chain, phase terms, current root and source/configuration identity stay bound; stale proofs/counters re-review rather than resend. | Unknown |
| Payer/relayer details | Direct payer works; any delegated platform payer must be explicitly admitted and reviewed. No invented allowance. | Unknown |
| Actual fee and payout terms | Exact fee bps/recipient, creator recipient and inclusive buyer price match current governed configuration and atomic SeaDrop settlement. | Unknown |
| Stage schedule translation | Actual generated intervals are strictly disjoint and inclusive; shared-boundary collisions and late inclusion do not misclassify a mint. | Unknown |
| Current counters and official final end | Actual original-mint counts, phase quotas, eligibility and one-hour royalty opening remain coherent after edits/transfers and partial sale. | Unknown |
| Platform metadata/read behavior | Nonsequential IDs, exact mint stats, reveal and later ERC-4906/lifecycle updates are accepted and tested independently. | Unknown |
| Exact end-to-end simulation and receipts | Current contracts/settings, real balances, gas/full fees and atomic payment/issuance all verified before any separate broadcast authorization. | Unknown |

## Actual inputs still needed

Keep these unresolved; the illustrative examples do not fill them:

- Deployed NFT, Access/governance and exact SeaDrop/runtime/block identities.
- Actual custom collection/onboarding reference and supported transaction source.
- Complete reviewed TEAM addresses/quantities and ALLOWLIST address inventory.
- Actual final phase schedules and official final sale end.
- Actual platform fee bps, allowed fee recipient, creator payout and delegated
  payer list; any required signature flow must be explained rather than enabled.
- Current governed price/quota/batch/wallet limits and actual mint counters.
- Live randomness provider/subscription/lane/funding and delivery qualification.
- Exact user transaction, full fee envelope, current simulation and actual
  platform/marketplace acceptance evidence.

The current examples at [TEAM input](examples/team-input.json) and
[ALLOWLIST input](examples/allowlist-input.json) are reviewer input-format
examples. Their [review outputs](examples/EXECUTION.json) never approve a wallet
signature or establish a live sale.

## Stop conditions and completion

Stop this path if the actual platform requires signed stages, unsupported owner
or configuration selectors, arbitrary executable calls, extra payment, changed
free-team/price/eligibility rules, incompatible timestamps or new custody. Record
the precise incompatibility and return the design decision to the operator.
Do not rewrite a platform payload or silently weaken PoPL checks to make it fit.

Qualification completes only with actual accepted custom onboarding, exact
reviewed configuration/unsigned payloads, current contract/authority/simulation
proof and independently reconciled sale settlement. Later public submission,
deployment, sealing and opening retain their separate authorization gates.
