# Platform and provider readiness — Gate A

Reviewed 20 November 2026 against local main
`519ff4f075022f789f46facbab56f0a944705b11` and trusted F6 source.
**Production NOT APPROVED.** This is a current primary-document/source
compatibility review. No RPC probes, tests, compiler runs, accounts, contacted
providers, credentials, signing, transactions or environment changes.

[Evidence](EVIDENCE.json) records exact local source/build hashes, the existing
compiled NFT ABI's84 function entries/83 distinct names, observed official-page headings/excerpts and
retrieval limitations. Official text is not frozen upstream runtime evidence.

## Result

Three practical gates remain: an actual RPC plan accepted for complete PoPL
workloads, a supported original-request randomness service, and confirmation
that OpenSea accepts this custom mint/configuration path. No service is selected
or adopted by this review. The observations below narrow the work and identify
one concrete OpenSea product mismatch to resolve before sealing.

## OpenSea: protocol deployed, custom Studio path unproved

The [official SeaDrop deployment registry](https://github.com/ProjectOpenSea/seadrop/blob/main/docs/Deployments.md)
still lists Robinhood4663 as a standard V1 drop network. The existing
[9 November on-chain evidence](../opensea-integration-20261109/REVIEW.md) supplies
the original runtime witness; it was not repeated here:

- SeaDrop: `0x00005EA00Ac477B1030CE78506496e8C2dE24bf5`.
- Historical runtime:21,081 bytes, Keccak
  `0x53e4b9339cf624803c9a7d0195576cca5b917920813508d86b3eb93dcbabeb5c`.
- This address is not a new current RPC observation, accepted collection,
  configured fee recipient or approved payer/router.

Current [SeaDrop documentation](https://docs.opensea.io/docs/seadrop) describes
Studio's public and server-signed allowlist stages. Its
[custom-contract guidance](https://docs.opensea.io/docs/customize-a-seadrop-contract)
describes publishing configuration through `multiConfigure`.

PoPL intentionally supports a different, narrower path:

| Current local code | Consequence for actual platform acceptance |
| --- | --- |
| NFT forwards typed individual setters through `ZZZSeaDropToken` and `ZZZSeaDropMint.prepareUpdate` | These can configure the pinned singleton on-chain, but do not implement Studio's documented batch-publish function. |
| No `multiConfigure` selector in the NFT's compiled ABI | Do not assume Studio's ordinary Publish operation works. |
| `updateSignedMintValidationParams` unconditionally reverts | Server-signed allowlist setup is deliberately unsupported. Merkle team/allowlist configuration is implemented instead. |
| No `owner()` selector in the NFT's compiled ABI; governance uses Access | Actual custom-collection ownership verification must accept the real authority model. Do not assume an Ownable getter exists. |
| `updateAllowedSeaDrop` rejects rotation, max supply is fixed and canonical peers retain the same singleton | A later default-contract/adapter migration is not an in-place repair of this PoPL binding. |

This is **a documented-product compatibility gap, not a demonstrated mint exploit
or a failed live Studio test**. A public V1 deployment and successful local
`mintAllowList` do not establish custom Studio/API acceptance. Preserve the
existing narrow contract until the real product requirement is established.

The useful next step is to obtain exact acceptance for the custom NFT/helper:
the Merkle team/allowlist flow, individual configuration route, authority proof,
actual mint transaction builder and payer/fee rules. If OpenSea requires signed
stages or `multiConfigure`, produce a narrowly scoped design and source/profile
review before implementation; do not silently expand mint authority or replace
PoPL with a generic template.

The [new existing-contract adapter guidance](https://docs.opensea.io/docs/drop-from-an-existing-contract)
requires platform linking and identifies its adapters as unaudited. It is not an
already-approved substitute. PoPL already exposes its own NFT callback; an extra
adapter would also require proof that original recipient/canonical counts,
governed price, reserved supply and randomness remain correct.

### Fee responsibility

The [current general fee guide](https://support.opensea.io/en/articles/8867091-what-fees-do-i-pay-on-opensea)
advertises a typical10% primary-drop fee and says fees can change. This is a
budget lead, not this collection's approved BPS/recipient. At the chosen gross
0.05ETH price, **if**10% applies, platform share is0.005ETH and recipient net
0.045ETH, with network gas separate. Keep actual fee/payer fields null until
confirmed. SeaDrop handles primary-sale proceeds; these are not LP fees or NFT
secondary royalties.

## Randomness: no qualified provider found

The current [Chainlink v2.5 supported-network catalog](https://docs.chain.link/vrf/v2-5/supported-networks)
contains no Robinhood entry. Another chain's coordinator cannot be reused merely
because Robinhood is Arbitrum-based or its chain guide mentions VRF generally.

Current PoPL source requires the original subscription-v2.5 request tuple,
nonzero lane and subscription, two words, authenticated asynchronous original
coordinator callback, and no reroll. A pending original result must remain
deliverable under the recorded recovery policy. Provider rotation requires all
old draws finalized.

| Candidate | Current primary-document evidence and qualification consequence |
| --- | --- |
| RH-VRF | [Integration](https://rh-vrf.com/docs) documents a Chainlink-shaped tuple, native funding, a zero-lane example, and same-signature callback retry. Its [FAQ](https://rh-vrf.com/) says an unserved request may be refunded after7,200 L1 blocks and cannot subsequently be fulfilled. This conflicts with PoPL's required still-valid original request. The zero-lane example alone does not prove nonzero lanes are rejected; exact verified code/key behavior still needs review. |
| D20DAO | The [security model](https://d20dao.org/docs/security) documents a distinct request/proof architecture, owner-controlled UUPS coordinator, and an unserved-fee refund after60seconds. Current v2.5 direct compatibility and original-request behavior are not established. Public deployments and replay claims do not substitute for independent code/proof/admin review. |

Published RH-VRF chain4663 candidates are coordinator
`0x1637195a674630E475ACD18B3D27b13C0EefDac1`, subscription
`0x3fbFE73935B729C6A30AE6060D5708215b3633f5` and verifier
`0x035299fe87211f35f5F36FBBa67919f9545dDd16`. They are **documentation leads**,
not fresh runtime/source/authenticity or cryptographic acceptance. The browser
research tool could not retrieve the coordinator's explorer contract page.

A request adapter can translate ABI and authenticate results; it cannot recover
entropy a provider permanently refuses after expiry/refund. Do not remove the
nonzero-lane guard or add a reroll to pass a candidate. First establish actual
provider code, keys/proof verification, native-payment decoding, two-word delivery,
callback gas/duplicates/retry and permanent-unserved-request behavior. If no
provider can satisfy the current rule, that requires a separate explicit design
decision before first mint, not a fabricated qualification pass.

## RPC and complete fees: actionable candidates, no selected tier

The [official connection guide](https://docs.robinhood.com/chain/connecting/)
recommends a provider-backed endpoint and archive access; it labels its public
endpoints rate-limited and unsuitable for production. It names Alchemy, Pinax,
QuickNode and other providers. No new account or credential was created here.

| Lead | What the current official material establishes | What it does not establish |
| --- | --- | --- |
| Existing public Pinax witness | Earlier report proves finite canonical-hash trace/interface observations at its exact source/time | A current plan/SLA, full32M/24M work, archive retention or complete PoPL fees |
| [QuickNode Robinhood](https://www.quicknode.com/chains/robinhood) and [Robinhood `debug_traceCall`](https://www.quicknode.com/docs/robinhood/debug_traceCall) | Chain-specific archive/debug product and call-trace method documentation | Exact `callTracer/withLog`, canonical-hash behavior, numeric gas/body/deadline bounds, chosen tier/cost and PoPL acceptance |
| [Alchemy Robinhood API](https://www.alchemy.com/docs/chains/robinhood-chain/robinhood-chain-api-endpoints/eth-estimate-gas) | Actual chain-specific estimate/read documentation and account-backed endpoint | Robinhood-specific debug-trace capability and32M numerical acceptance; its [550M generic gas-limit table](https://www.alchemy.com/docs/reference/gas-limits-for-eth_call-and-eth_estimategas) names other chains, so do not borrow that bound |

For a selected tier, collect explicit method/trace, canonical-hash, execution
gas, timeout, request/response, archive/log range, rate/concurrency and cost
terms, then run bounded exact current operations using the existing reviewed
probe/preparation path. This review makes no new RPC call and does not adopt a
provider. Public docs-demo endpoints are not a production service plan.

The [chain fee guide](https://docs.robinhood.com/chain/gas-and-fees/)
describes inclusive execution/posting estimates. Preserve complete-fee accounting
without adding posting twice. Retain selected32M/full20% contributions and
24M/full25% maintenance plus separate ETH/price/day/funding bounds. Numerical gas
admission is not the same as complete fees, actual sequence inclusion or an
approved operating budget.

## Required decisions and next concrete work

1. **OpenSea:** verify the exact custom Merkle/configuration/authority path before
   deciding whether any contract extension is necessary. Actual onboarding and
   collection-specific fee/payer terms remain external inputs.
2. **Randomness:** select only after original-request recovery and cryptographic/
   authority review. Existing documented candidates do not close that gate.
3. **RPC:** choose an account-backed compatible plan, or a separately reviewed
   self-hosted service; exact tier acceptance still needs bounded live evidence.
4. **Operating costs:** confirm provider, publication, VRF and keeper budgets with
   the chosen products. Generic prices/fee guides are not approved quotes.

Owning tasks remain `opensea-mint`, `fair-draw`, `host-services`,
`native-production-preflight`, `operation-review` and `security-dependencies`.
Root owns central Todo/operator/current-guide updates. This report adds source/
document evidence only; it does not close those tasks or alter current rights.
