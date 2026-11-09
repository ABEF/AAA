# Qualify randomness and OpenSea primary mint


Fresh [SeaDrop mint2/helper1](OPENSEA_MINT.md) implements the canonical NFT
callback, shared supply/quota bookkeeping, authenticated buyer issuance and
atomic SeaDrop fee/creator settlement. Initial sale:20free team,500paid
allowlist(one per distinct address),480public FCFS; unsold AL rolls public,
unused team remains reserved. Paid price defaults0.05ETH total, gas separate.
Actual OpenSea onboarding/fee/payer/provider and operating acceptance remain
unqualified. Website minting remains demonstrative.

## Versioned production inventory

The blocked [schema17 production template](../config/production.example.json)
requires mint integration2, `seadrop_sequential_v1`, the fixed helper and
canonicalV10. The checker/observer authenticate source-matching configuration,
original-recipient lifetime books and actual admitted drop state separately
from proof review, actual onboarding, fees, VRF and operating evidence. A
manifest cannot approve its own deployment or make opaque root contents safe.

The exact prior [schema16 template](../config/production.schema16.example.json)
and direct `vault_direct_v1` checker remain explicitly historical; that path
does not gain SeaDrop functionality by relabeling. Existing reader/source9,
site/runtime/journal/signer profiles remain unchanged. No checker signs or
authorizes deployment, sealing or public spending.

```text
python scripts/validate-production-config.py --config config/production.example.json
```

The checked-in template stays blocked. Exact addresses, platform fee/payer,
wallet limits, sale windows, source hashes and independent evidence must
come from actual qualification; do not fabricate them to silence blockers.

## Qualify the original randomness request

Production minting is intended for OpenSea; website minting is demonstrative. This decision is not marketplace acceptance. Current PoPL needs the subscription-v2.5 tuple request selector `0x9b1c385e`,
exactly two words, the reviewed provider/lane/subscription/payment mode fixed
for that request, and authenticated asynchronous callback. Future provider changes
require the fully drained ProtocolPolicy rotation procedure; no pending reroll or retargeting. The version-1 randomness record
contains:

| Field | Required reviewed meaning |
| --- | --- |
| `request_profile` | `subscription_v25_two_words_v1`, matching actual request and callback behavior. |
| `request_selector`, `num_words` | `0x9b1c385e` and integer 2. |
| `recovery_policy.unserved_request` | `original_request_remains_valid`. |
| `recovery_policy.refund_or_expiry` | `cannot_invalidate_original_fulfillment`. A provider's irreversible refund/expiry is incompatible with this policy. |
| `recovery_policy.failed_callback` | `same_request_same_result`. |
| `recovery_policy.reroll` | `none`. |
| `funding.source`, `funding.owner` | `external_subscription_reserve` and its actual public owner address. LP principal and accrued holder rewards do not fund the service. |

The independent coordinator review and actual staged integration still bind
chain, coordinator, NFT, key, subscription, payment mode, runtime and release.
In the staged integration, `recovery_request_id` must equal the original
`fulfilled_request_id`. `original_result_sha256` and `recovered_result_sha256`
are the identical SHA-256 digest of the original two words encoded as two ABI
uint256 words. `request_selector` and `callback_words_count` must also match.
Retain hashed negative-case evidence in `invalid_proof_rejection_sha256` and
`unauthenticated_callback_rejection_sha256`. These fields index actual reviewed
evidence; their existence is not cryptographic verification of a provider.

Before funding or sealing, obtain the exact provider source, code/configuration
and upgrade/key authority history. Review fees, supported confirmation/gas
bounds, callback authorization, duplicate behavior, compromised/wrong proofs,
subscription consumer authorization and original-request recovery. Exercise
those paths on the exact test network and then the separate approved rehearsal
deployment. A mock coordinator, runtime presence or ABI match does not pass.

The [dated candidate review](../reports/release-services-20261025/vrf-opensea/RESEARCH.md)
finds no selected compatible provider. Do not copy a zero key into PoPL or remove
the nonzero guard merely to fit another service. An adapter is new reviewed code,
not a configuration substitute. If a provider can permanently cancel an unanswered
request, resolving that requires an explicit design decision before integration;
a fee refund supplies no randomness and does not refund the NFT mint price.

## Operate reveal recovery

1. Observe `/v1/mint-readiness` at its confirmed block: unfinished draws include
   fulfilled requests still awaiting ordered finalization. It does not prove
   subscription funding or provider liveness.
2. If fulfillment or funding is unhealthy, governance can call
   `NFT.setMintPaused(true)` to stop new mints independently. This does not cancel
   pending draws or stop existing claims and LP operations by itself.
3. Inspect the exact oldest request at its original coordinator. Follow only the
   reviewed original-result recovery path; never create another request, change
   traits or pretend a refund is a fulfilled result.
4. Anyone may call `NFT.finalizeTraits(id)` when that original result exists and
   its ordinal is next. Drain existing requests in order; do not skip one.
5. Resume with `NFT.setMintPaused(false)` only after actual provider/funding
   checks and applicable global/lifecycle controls. Future callback tuning does
   not repair a request already submitted with insufficient gas.

Planned provider rotation requires all old draws finalized and cannot bypass a
stuck original request. An unanswered draw can block later reveals, activation of unrevealed NFTs and
whole-collection replacement. It does not block ordinary LP pool movement merely
because randomness is pending. No promise of post-provider-failure recovery is
made without a genuine still-valid original result.

## Current OpenSea investigation and remaining acceptance

The [November9 source/runtime investigation](../reports/opensea-integration-20261109/REVIEW.md)
supersedes the historical missing-chain conclusion: the pinned official
registry lists Robinhood4663 and an independent RPC read matches verified
SeaDrop V1. The canonical callback is implemented against that exact runtime.
Protocol compatibility is still not custom collection onboarding/API
acceptance; generic marketplace support or a generic fee guide is insufficient.

Use the [complete plan, inputs and stop/restart procedure](OPENSEA_MINT.md).
Before production approval retain the actual OpenSea collection/drop URL and
accepted configuration; generated unsigned platform mint; buyer receipt and
canonical ownership; gross/platform/net balance changes; original request,
fulfillment and ordered reveal; royalty receiver; negative/duplicate/last-slot/
receiver/payer cases and actual maximum-batch gas. Source-local tests and
mock VRF do not qualify that campaign. Public transaction authorization is
separate. No deployment, website mint or signer rollout is implied.
