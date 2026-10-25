# Service capability, release qualification and operator reference

Reviewed 25 October 2026 against baseline `ac98b5b`. This is an internal,
source-scoped improvement pass. **Production is NOT APPROVED.** The
[verification record](VERIFICATION.md) separates new behavior, reused evidence,
actual public observations and still-unqualified services.

## Implemented improvements

| Area | Change | Practical boundary |
| --- | --- | --- |
| Optional second-source capability | A small immutable [Pyth Core reader](../../src/ZZZPythPriceFeed.sol) exposes the existing Oracle's required source interface. It validates exact return shape, signed precision, positive price, original publish time, confidence and runtime using a bounded static read. | No source deployment, updater, admission, live price or provider independence is established. Confidence screens the midpoint; it does not expand Oracle USD bounds or prove market truth. |
| Honest mint qualification | Current release validation requires explicit schema 5 / mint profile 1. It cannot accept proof flags as an implementation of OpenSea minting. Historical inspection is an explicit separate CLI mode. | Current direct mint is incompatible with SeaDrop and remains blocked. No new mint authority or paid path is added. |
| Randomness recovery evidence | The current profile requires the exact request ABI, two words, nonzero fixed lane, original-request validity, same-result recovery and separately funded subscription. | Neither inspected Robinhood candidate is qualified. No proof adapter, provider swap, cancellation or reroll is implemented. |
| Auditable source handoff | An offline exporter packages exact committed blobs, dependency pins, required fixtures and an exclusion inventory; a strict verifier uses an independently trusted archive hash. | It does not bundle dependencies, run tests, perform an independent audit or approve a release. Regenerate for the eventual frozen release. |
| Operator documentation | Authority/custody distinctions, current contribution defaults, current versus historical profiles, optional reader setup and callable inputs/outputs are documented. | Procedures and ABI visibility do not grant authorization or prove an external dependency safe. |

## Material findings and decisions

1. **A generic service-evidence record could conceal a missing primary-mint
   implementation.** The code-owned current mint profile now rejects this. Old
   schema/profile results are labeled historical consistency and the CLI refuses
   them by default. Library compatibility is retained for historical consumers.
2. **Pyth was not consumable directly through the Oracle's source ABI.** The
   optional reader supplies that shape with immutable policy, exact original
   timestamps and bounded failures. It adds no ownership, fund custody or updater.
   The separate source/operator guide explains proxy and uncertainty limits.
3. **Original VRF request expiry is consequential.** A provider can share the
   callback shape yet irreversibly cancel the original request, leaving ordered
   reveal blocked. Qualification now requires actual same-request/result recovery;
   a refund or a new request is insufficient. Existing proof guards were retained.
4. **Current component/operator prose contained stale defaults and scope.** The
   current map now uses 2% contribution / 98% deployed LP and distinguishes
   implemented tooling from actual service acceptance. Retired bridges are not
   reinstated as launch dependencies. Governance authorizes exits; an approved
   recipient holds only the transferred assets and gains no configuration role.
5. **OpenSea price decision is explicit.** Buyer pays 0.05 ETH gross; its actual
   platform fee comes out of recipient proceeds. Gas is separate. No platform
   percentage is assumed. Existing direct mint still forwards the whole 0.05 ETH;
   a compatible buyer/payment path remains a pre-seal implementation requirement.

## Actual external investigation

Official catalogs identify candidate Chainlink/Pyth products for ETH, USDG and
USDC. No ZZZ source pair was established. Different proxies or Pyth products do
not establish independent upstreams. Pyth requires funded, monitored update
operations; deployment on Robinhood does not imply sponsored fresh data.

The VRF/OpenSea observation obtained 16 logical hash-pinned runtime/storage
checks through 32 HTTP posts from one public provider. Later feed/route probes
received two Pinax HTTP 429 responses and the official endpoint HTTP 403 before
a usable snapshot. These are distinct dated observations, not contradictory
proofs of uptime or market absence. No fresh route price, liquidity depth,
cheaper ZZZ conversion or actual source round is qualified by this pass.

## Remaining release decisions

- Two defensible independent ZZZ sources, actual ETH/stablecoin source policies,
  proxy/upstream review, freshness/confidence and update funding/operations.
- Funded activation routes and a cheaper ZZZ-to-ETH reward route at the default
  1% conversion limit; actual RPC preparation traces and redundant service policy.
- A compatible proof-verifying VRF with original-request recovery and funded
  operation; no currently inspected candidate has passed that qualification.
- Actual OpenSea product/chain support, a reviewed canonical buyer/payment
  implementation, platform terms and end-to-end primary-mint/royalty acceptance.
- Production multisig, guardian, keeper, mint-recipient and provider-specific
  funding addresses. The user explicitly deferred these; no addresses are invented.
- A coherent separate current-native operating stack, target-chain/fork and Linux
  outage/recovery rehearsals, economic and worst-case gas review, independent
  audit/remediation and exact-release sign-off.

No existing Anvil state, NFT, LP, balance, journal, dist overlay, service or
monitoring configuration changed. Shared signing remains Anvil-only; public
DEPLOYMENT remains null. No public transaction, deployment or sealing occurred.
The website server is unchanged. Unrelated local drafts are excluded from publication.
