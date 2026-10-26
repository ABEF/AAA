# Qualify randomness and OpenSea primary mint


Current source issues paid NFTs through `Vault.mintDormant()`. It does not yet
implement an OpenSea primary-drop mint path. Marketplaces may recognize the
ERC-721 collection for secondary sales without supporting its primary mint.
Keep these two acceptance criteria separate before sealing.

## Versioned production inventory

The current blocked [production template](../config/production.example.json)
declares `mint_integration_version: 1`. The existing production inventory checker
then verifies the current code-owned `vault_direct_v1` capability and explicitly
reports `mint.opensea_unsupported`. Inventing a `mintSeaDrop` flag, successful
secondary sale or generic supported-chain proof cannot make this source support
a new mint caller or payment path.

An omitted/zero version preserves historical schema-5 consistency checks.
The module labels their output `legacy_manifest_consistency_only`, with
`production_qualification_supported: false`. The CLI defaults to the current
release gate and fails closed on omitted/zero/boolean mint profiles or old
schemas. Historical inspection requires explicit `--historical-consistency`;
that output is labeled `historical_manifest_consistency_only` and
`current_release_gate: false`, never current production qualification. Current
qualification requires explicit version 1, supported qualification scope,
`ready: true` and genuine independent evidence. No checker authorizes deployment,
signing, sealing or spending.

From the repository root, inspect the existing checker output:

```sh
python3 scripts/validate-production-config.py --config config/production.example.json
```

The checked-in template must remain blocked. Do not invent service addresses,
evidence hashes, fees, source-code matches or a successful marketplace mint to
silence the checks. A future reviewed implementation needs an explicit capability
profile update; manifest metadata alone cannot add it.

## Qualify the original randomness request

Production minting is intended for OpenSea; website minting is demonstrative. This decision is not marketplace acceptance. Current PoPL needs the subscription-v2.5 tuple request selector `0x9b1c385e`,
exactly two words, its configured nonzero immutable lane/subscription/payment
mode and authenticated asynchronous callback. The version-1 randomness record
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

An unanswered draw can block later reveals, activation of unrevealed NFTs and
whole-collection replacement. It does not block ordinary LP pool movement merely
because randomness is pending. No promise of post-provider-failure recovery is
made without a genuine still-valid original result.

## Design and qualify the OpenSea path

The user's decision is **0.05 ETH total mint price paid by the buyer**, with
network gas separate. The mint-proceeds recipient receives that gross payment
minus the actual OpenSea platform fee. The actual fee is not yet verified; do
not assume a fee percentage or invent a platform recipient. Confirm the supported
ERC-721 drop product and exact reviewed SeaDrop deployment on Robinhood. Current
Vault direct mint forwards all 0.05 ETH and does not implement this future split;
do not charge the mint twice or claim marketplace compatibility is complete.

A compatible implementation must retain canonical hashed NFT IDs, Vault issuance
records, max supply 1,000, the exact 600/300/100 draw, immutable royalties and
transferable economic rights. It needs an explicit reviewed caller/buyer path,
exact payment conservation, bounded quantity and worst-case request gas, pause
and lifecycle checks, receiver-callback protection, complete failure rollback
and exactly one original randomness request per minted NFT. Copying a template
that adds a public burn, sequential identity or unrelated mint authority is not
an authorized integration.

Before approval, retain the exact OpenSea collection/drop URL, network, verified
runtime and product configuration; generated unsigned mint transaction; actual
buyer receipt and canonical NFT record; mint price/platform fee/creator payment;
request/fulfillment/reveal; ERC-2981 receiver; and failed/duplicate/last-supply/
receiver-rejection cases. Source review and local simulations should precede
the separately authorized real rehearsal. No public transaction is authorized
by this runbook. The website Mint page remains a demonstration.
