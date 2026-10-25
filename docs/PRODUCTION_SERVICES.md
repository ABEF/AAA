## Current feed candidates, costs and dated readings - 2026-10-25

## Service compatibility and mint-price decision - 2026-10-25

The optional [Pyth Core reader](PYTH_PRICE_SOURCE.md) is implemented and locally
verified; no source is deployed or admitted. It preserves original publish times,
checks precision/confidence/age/runtime with bounded reads, and adds no updater
or authority. Confidence is a screening limit, not a widening of Oracle USD bounds
or proof of market truth. Core proxy implementations and common upstreams still
need independent review. Chainlink/Pyth catalogs provide candidate ETH/USD,
USDG/USD and USDC/USD products; no ZZZ pair was established. Pyth updates require
a separately funded, monitored service. [Research and scoped evidence](../reports/release-services-20261025/REVIEW.md).

Current release validation requires schema5 with explicit mint_integration_version1.
The existing Vault direct mint is not an OpenSea drop integration; the gate blocks
it regardless of supplied proof flags. Legacy inspection requires the explicit
CLI --historical-consistency option and is never current release qualification.
[Mint and randomness qualification](MINT_INTEGRATION_QUALIFICATION.md) requires the
actual request ABI, original-request/same-result recovery and separate funding.
No supported VRF provider is selected. Authority wallets remain unset by decision.

OpenSea primary mint must charge the buyer **0.05 ETH gross**, pay its actual
platform fee from that amount and send the remainder to the mint recipient;
network gas is separate. The actual platform fee is unverified. Current direct
mint still forwards the entire0.05ETH and is not that integration. Keep the
OpenSea implementation/acceptance gate open before sealing.

Use the [frozen review package](FROZEN_REVIEW_BUNDLE.md) to hand an exact committed
source tree and dependency pins to reviewers. Export/verification is not an audit,
test run, self-contained dependency bundle, operating rehearsal or release approval.
Production remains NOT APPROVED; public signing, services and existing local
state are unchanged.

## Service capability and marketplace boundaries - 2026-10-25

Use [RPC preparation qualification](RPC_PREPARATION_QUALIFICATION.md) before
real deployment-specific rehearsals. The stricter missing-hash classifier and
actual discarded Approval(0) trace test are implemented; no fixture qualifies
a provider. [Dated research and observations](../reports/real-service-readiness-20261025/VERIFICATION.md)
keep network support, ABI compatibility, operating evidence and approval separate.

Current official documentation does not establish a qualified independent ZZZ
source pair or a supported compatible VRF for this collection. OpenSea Robinhood
network support alone does not qualify the custom primary mint/SeaDrop path.
Do not substitute two shared-upstream proxies, remove proof/request guards or
assume a marketplace product supports this mint. Authorities remain unset at
the user's request. Continue those external decisions in the sole Todo.

The [saved read-only observation](../reports/price-reference-20261025/OBSERVATION.md)
records candidate Chainlink ETH/USD and a separately labeled pool-derived ZZZ
estimate. Neither is configured PoPL two-source consensus. The catalog's Shared
SVR secondary proxy is not an independent second provider. Actual pairs, ages,
administration/product policy and operating gas/cost agreements remain open.

Standard public push-feed getter reads require no separate LINK payment; gas
inside transactions and potential RPC/custom-provider charges are separate.
No production oracle cost estimate or provider contract is selected. For an
already sealed compatible deployment, governance uses setDualFeed, not retired
setFeed, and must refresh approved downstream policies after admission.

## Independent dual USD sources - 2026-10-24

Current pricing2 requires two independently qualified sources for each of ETH,
ZZZ and USDG (and USDC if admitted). The user selected3% disagreement tolerance;
addresses, freshness ages and actual proxy/upstream policies remain unset.
[Price security](PRICE_SECURITY.md) distinguishes market truth from actual LP
facts, common-mode risks and the separate execution-loss floor. The schema5
inventory observes full policies and source rounds; no mocked review qualifies
live services. Selected hookless LP income does not require Pons creator funding.

## Native V2 inventory and preflight - 2026-10-24

[Current schema-5 preflight](PRODUCTION_PREFLIGHT.md) validates native/V4 bindings,
actual versus approved runtime pins and current governed limits. A separate
bounded read-only observer captures a canonical snapshot without upgrading review
status. Legacy schema 4 stays historical; missing actual public addresses,
prices/routes/VRF/services and audit evidence remain release blockers. No signer,
Solidity, website/service, existing Anvil/journal or monitor change follows.

**Current policy, 2026-10-24:** [Typed v4 conversions](TYPED_V4_ROUTES.md) and
[governed execution-loss limits](EXECUTION_LOSS_POLICY.md) are implemented in the
undeployed candidate. Current defaults are 2% contribution, 1% conversion and 3% maintenance;
immediate governance may set each category up to a hard 10%. Existing stricter
venue/caller minima remain. Pending normal custody approvals retain their original
absolute floor. Earlier fixed-cap or v3-only descriptions below retain their
historical/default scope. Actual routes, services and independent audit remain open.

# Production service decisions still open

**Current service scope (2026-10-24):** [Selected hookless ETH/ZZZ](POOL_SELECTION.md) earns conventional LP fees; Pons creator-payment terms are historical/optional rather than launch prerequisites. Independent feeds, supported VRF, real routes and operating qualification remain open. [Post-seal policy](POST_SEAL_POLICY.md) records current fixed settings and required extensions; native accounting V2 is implemented; actual services remain unqualified.

These are development research results from 2026-10-15. None selects a provider,
approves deployment or establishes that a service will remain available.

## Randomness

The NFT currently requires a once-configured VRF-v2.5-style coordinator, two
authenticated words and mint-order finalization. MockVRF proves local request and
accounting behavior, not real proof verification or service liveness. A stalled
earlier request can block later reveals and activation.

Two public Robinhood candidates were found and inspected; neither is approved:

| Candidate | Observed mainnet endpoint | Review still required |
| --- | --- | --- |
| [D20DAO](https://d20dao.org/docs/deployments) | `0xEc8b95B168c87294c45727Bd2ac903d09316D132` | Different API, proof/security model, single-operator liveness, owner-controlled UUPS implementation and request-timeout behavior. A published testnet endpoint does not establish a safe replacement for the current NFT coordinator. |
| [RH-VRF](https://rh-vrf.com/docs) | `0x1637195a674630E475ACD18B3D27b13C0EefDac1` | Source/proof/key/operator/administrator verification, fees, native-payment rules, retries/refunds and supported testnet. Its documented zero key hash conflicts with current NFT configuration; do not simply remove that guard to make the ABI fit. |

The D20DAO testnet endpoint was observed at
`0x2f26513DE4Ed388947f5d22FD395D5E06f472f05`. The research includes code and
implementation/admin observations, retained externally in the release workspace.
Published deployments and runtime matches are evidence of deployed code, not an
independent audit or approval of that code. Review the candidate's
[security model](https://d20dao.org/docs/security) and actual proof verification.

Before choosing a coordinator, independently verify the complete request,
fulfillment and recovery path on the target chain. Define how a permanent
provider failure is handled without an administrator selecting traits, cancelling
an unfavorable outcome or rerolling an already requested NFT. Any required NFT
integration/recovery change needs fresh source review before sealing.

## USD prices and sequencer status

ETH/USD, USDG/USD and USDC/USD observations and exact feed addresses are recorded
in [activation routing](ACTIVATION_ROUTING.md). A stablecoin ticker is not a
dollar-value oracle. The feeds require denomination, round, heartbeat, proxy and
administrator review for the actual deployment.

**An independent ZZZ/USD source has not been selected.** The selected Uniswap v4
pool does not itself provide a built-in TWAP, and the reviewed Pons hook does not
record the required oracle observations. A production price policy needs real
historical observations, manipulation/liquidity bounds, reference sources and
outage behavior. Do not use the same instantaneous pool price as an independent
USD guard. See the [Uniswap v4 whitepaper](https://app.uniswap.org/whitepaper-v4.pdf).

The Oracle candidate now supports governance-approved replacement of a reviewed nonzero
sequencer-status source, retaining status and recovery-grace checks. It does not
create a supported feed on Robinhood. Select a genuine supported source or
independently justify the initial no-feed policy for that chain. Runtime hashes
alone do not pin proxy implementations. See
[Chainlink's uptime-feed model](https://docs.chain.link/data-feeds/l2-sequencer-feeds).

## Remaining operational decisions

- Public governance multisig, guardian, keeper and mint-recipient addresses remain
  unset at the user's request.
- Creator receipt terms and the liquidity-measurement/payment policy are
  historical/optional for the selected hookless pool; the calculator has no
  payout authority. Any optional external revenue arrangement still needs review.
- The artwork upload bundle is prepared; IPFS provider, CID, publication,
  independent retrieval and marketplace rehearsals remain open.
- Production RPC, indexer/API hosting, confirmations, rate limits, monitoring,
  signer recovery and target-chain keeper rehearsals remain unqualified.

The [central Todo](../TODO.md#launch--operations) tracks these decisions and rehearsals. The [change/recovery matrix](CHANGE_AND_RECOVERY.md) explains the boundaries; the [release record](RELEASE_CHECKLIST.md) records final approval.
