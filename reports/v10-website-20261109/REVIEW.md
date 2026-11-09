# Current mint2/V10 website integration

Local source now supports the current contract mint profile explicitly. Website
schema5/source10 selects mint2/canonicalV10 over accounting7; it does not relabel
source9/schema4/V9 or any installed runtime. Source publication is not deployment.
Production remains **not approved**.

## Implemented

- Added a separate33-role browser proof for the current graph, including the mint
  helper, exact SeaDrop runtime commitment, predeployed renderer and NFT codec.
  All checks use one canonical hash. Bounded proof work coalesces per exact hash;
  caller mutation cannot change a captured manifest or block selector mid-proof.
- Connected the existing exact-LP data and unsigned-review validators through a
  closed V9/V10 discriminator. Financial arithmetic, ownership, custody, fixed
  80/10/5/5 economics and contract ABIs/runtimes are unchanged.
- Current holdings, both physical LP legs, governed minima/cosmetic policy,
  original royalty currencies, pending fixedZZZ LP conversion, earnings and
  terminal principal remain distinct. Invalid or unavailable data is rejected
  or displayed unavailable rather than guessed zero.
- ETH/fixedZZZ Entry3 reviews verify exact approvals, marginal LP, caller/policy
  floors, expiry and independent simulation. Fresh300bps contribution review
  permits97% marginal deployed LP; old reviewed200 ceilings stay stricter. Gas1
  and optional independently selected activation/transaction gas2 remain bounded.
- Mint2 direct mint/readiness paths reject before transport. The protocol reports
  OpenSea as the channel, direct preparation=false, available=null and unverified
  stage eligibility. It does not infer allowlist/proof/payer eligibility or
  publish an invented mint URL.
- Replaced a negative signer-schema test with an explicit legacy1–3 allowlist.
  Schema4/5 and future schemas cannot inherit a signer on Anvil. The shared
  browser-wallet bytes remain unchanged; both public configuration exports stay
  null. There is no new nonce queue, resend, transaction submission or recovery
  journal format.
- Added exact source10 build identity and a66-descriptor ceiling matching current
  LP/royalty inventory. Unconfigured artifacts identify no selected contract
  profile. Source9 retains its historical97 descriptor acceptance.

## Evidence and corrections

[Verification](VERIFICATION.md) separates focused browser checks, actual backend
handler output under synthetic state, clean publication checks and unchanged
historical evidence. The new exporter executes current Projection,
Transactions/ClaimPlanner, ActivationTransactions and trace parsing. Its traces,
prices, runtime bytes, graph-only replies and market state are injected; they do
not establish actual EVM execution or provider/market acceptance.

Review strengthened the test transport so a historical getter cannot be relabeled
as a current-block proof. Python mock quantities are serialized into standard
JSON-RPC hexadecimal wire quantities only in test transport. Production quantity
validation is not relaxed. Same-block number/hash gas headers and the producer's
100bps caller-slippage request now match the existing website review. Exact
calldata and nonzero earned balances are checked, including approvals that add
no LP and require a fresh complete Entry review after confirmation.

No production Solidity/backend implementation changed. The existing Solidity,
size and static-analysis evidence retains its own exact source scope; it was not
rerun for browser/Python fixture work.

## Operator and release boundary

Use [the source10 procedure](../../docs/SOURCE10_WEBSITE_PROFILE.md), [environment
map](../../docs/SITE_ENVIRONMENTS.md) and [operator manual](../../docs/OPERATOR_MANUAL.md).
The central Todo, feature reference, roadmap and repository context record local
implementation separately from qualification. No contract callable/input/permission
changed, so ABI/operator call tables require no regeneration.

Popldemo, served current3 poplint, services, existing Anvil8902, NFTs, LP, balances,
journals, preserved dist overlay and the user-paused heartbeat remain unchanged.
Actual current mint2 deployment/configuration, target-chain Entry3 execution,
market depth/routes, independent USD feeds, VRF, OpenSea onboarding/fees/payers,
wallet extension/hosting/operating acceptance and independent audit remain open.
The synthetic consumer fixture does not close those release gates.
