# OpenVRF: pinned source lead, not a qualified provider

20 November 2026. PoPL baseline `9d1033a60029fb5b4112c28b6c8bd9015ebd0321`.
Read-only research; production remains NOT APPROVED. The repository name
`Robinhood-OSS` is not evidence of official Robinhood endorsement.

## What is pinned

Public source revision **`9fb960cfc4d41e38f9d3057bf547e0d9cdcd4cc2`**, committed
18 September 2026. [Source manifest](VRF_SOURCES.json) binds five retrieved files,
the commit response, both dependency gitlinks and exact SHA256/Git blob hashes.
All 12 nested trees and root `dba5f85c18cf1b9106b4bfaf166418a018b59b17` were
independently reconstructed from the recursive entries. The API's top-level
`sha` repeated the query commit rather than the commit's tree; it was not trusted
as the tree identity. The commit is reported unsigned.

Eight bounded public HTTP requests produced seven successful responses. The
last request, for the upstream registry at a requested `/demos/` path, returned
`HTTPError` and was not retried. The source remapping points into `src/`; no
claim is made that this failed URL was the correct dependency path. Raw originals
and the complete capture remain in the external `vrf-source-review` archive.
No provider/chain RPC, key, funding, installation, build, test or transaction ran.

## Relevant source properties

At this pinned [OpenVRF source](https://github.com/Robinhood-OSS/OpenVRF/blob/9fb960cfc4d41e38f9d3057bf547e0d9cdcd4cc2/src/OpenVRF.sol),
requests retain one consumer, round, fee and result. The inspected router declares
no expiry or cancellation entry point. Removing a consumer blocks new requests without
invalidating old ones. Fulfillment verifies the bound beacon round before
recording the word; retry preserves that result and recipient. Callback gas may
increase only up to 1M. Reserved request fees cannot be withdrawn by the owner.

These properties address original-result permanence structurally. They do not
force delivery: the owner can authorize/revoke consumers and relayers, set future
fees, and act as an emergency relayer. A halted authorized relay fleet or unavailable
beacon can still leave a valid request unanswered.

## PoPL compatibility gaps

PoPL's unchanged NFT calls the six-field subscription-v2.5 request without ETH,
requires a nonzero reviewed lane/subscription and exactly two callback words,
and authenticates its original coordinator. Rotation waits for all draws to
finalize; no pending reroll is available.

The candidate instead takes a payable `requestRandomness(uint32)` and returns
one word through `rawFulfillRandomness`. It has no subscription abstraction.
A reviewed bridge of those interfaces would require all of the following:

- An external prepaid reserve/account model; never fund service from LP principal,
  holder rewards or silently diverted mint proceeds.
- One permanent PoPL-request-to-provider-request association and authenticated,
  duplicate-safe same-result delivery, including retry after partial failures.
- An explicitly reviewed deterministic two-word derivation and domain separation;
  expansion does not create 512 bits of independent entropy.
- Genuine lane/subscription meaning and native-payment handling; no dummy policies,
  zero-lane exception or fabricated current request-profile qualification.

No adapter or funding policy is implemented or approved here. The candidate's
callback range overlaps PoPL at 200k–1M, but actual cold callback gas is unmeasured.
Its pinned compiler is 0.8.28/Paris; this is a separately compiled external-dependency
question, not authorization to change PoPL's 0.8.26/Cancun build.

## Security and operating limits

The pinned [security review](https://github.com/Robinhood-OSS/OpenVRF/blob/9fb960cfc4d41e38f9d3057bf547e0d9cdcd4cc2/docs/security-status.md)
requires sufficiently fresh sequencer timestamps: the current beacon is scheduled
only 2–4 seconds beyond the request's block timestamp. A delayed timestamp can
undermine the intended commitment-before-publication ordering. Waiting later to
fulfill cannot make an already-public beacon unpredictable again. Generic
Arbitrum timestamp bounds are not target-chain acceptance.

Public chain smoke evidence applies to earlier round-policy runtimes, not the
exact current source. The router and BLS dependency lack independent specialist
cryptographic approval. The pinned dependency revision is
`randa-mu/bls-solidity@11af179a8287d978659aae07adb66aa60f64b8a6`; its registry source
was not retrieved in this bounded pass. OpenZeppelin's gitlink is
`cab19933c33c2ad1d4c7a84864a3601dddfd16f3`. Gitlinks alone are not dependency audit.

The pinned [README](https://github.com/Robinhood-OSS/OpenVRF/blob/9fb960cfc4d41e38f9d3057bf547e0d9cdcd4cc2/README.md)
offers self-hosted router/relayer software, not a shared funded service. Production
would need reviewed deployment identity, trusted role control, dedicated gas
funding, source/finality policy, durable request/nonce recovery, beacon-proof
retention, monitoring and independent review. Local upstream test counts are
not PoPL passes or a hosted-service SLA.

## Other candidates and next decision

The [Chainlink v2.5 catalog](https://docs.chain.link/vrf/v2-5/supported-networks)
still lists no Robinhood deployment. [RH-VRF's FAQ](https://rh-vrf.com/) explicitly
makes refunded unserved requests permanently unfulfillable. [D20DAO's published
security rules](https://d20dao.org/docs/security) use a 60-second refundable deadline
and a different proof/callback architecture. None is newly qualified by this pass.

OpenVRF is a useful new source-design lead because it avoids request cancellation.
It is not a drop-in coordinator. Before any adapter coding or funding, decide
whether its self-hosted beacon/timestamp trust model is acceptable, then complete
exact dependency review and the request/funding/two-word design. Keep provider,
source hashes and integration acceptance blocked until genuine reviewed evidence
exists. No PoPL safeguard, economic right, authority or environment changes.
