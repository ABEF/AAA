# Bounded post-seal operating controls - scoped verification

2026-10-24. Undeployed development candidate; production NOT APPROVED.
Publication is recorded separately. No public transaction, website build/server,
existing Anvil/NFT/LP/balance/journal, signer or monitoring change occurred.

## Implemented boundaries

- `NFT.setRandomnessRequestSettings(uint16,uint32)` changes only future request
  confirmations (3-200) and callback gas (200,000-10,000,000), after initial
  configuration. Coordinator, lane/key, subscription and payment mode remain
  fixed. Already submitted requests retain their provider-recorded arguments;
  no request ID/epoch, stored word, trait, quota or draw order is replaced.
- `Buyback.setOperatingTradeUSD(uint256)` selects zero through immutable
  `maxTradeUSD`, with the deployment default equal to that hard maximum. Values
  use USD18 and apply per trade, not per day. Zero stops swaps and direct ZZZ
  burns before oracle reads or reserve release. It does not withdraw reserves.
- Both setters use immediate governance, allow ordinary pause, reject preparation
  and canonical lifecycle locks, prevent reentry and emit previous/new values.
  Successors review their own operating policy; canonical economic records do not
  copy these settings. Existing sealed deployments cannot gain the new code by
  changing configuration.

Current runtime/observed configuration and exact provider compatibility require
review before use. Contract bounds alone do not qualify a real VRF provider.
Raising future callback gas cannot repair an already-submitted failed callback.
The keeper still simulates fixed configured buyback amounts: resize/remove those
tasks after lowering or stopping the ceiling to avoid intentional failures/backoff.

## Backend and event compatibility

The production inventory distinguishes immutable provider configuration from
exactly two mutable future-request fields. It rejects the ambiguous old
`immutable_configuration` flag in the NFT record and still requires current
observed getters to match reviewed settings. The larger native/custody inventory
remains blocked pending its separately reviewed schema and real evidence.

Event generation exposed a pre-existing stale catalog. The additive repair keeps
all 103 previous descriptors unchanged and adds 16 current topics: 14 custody
topics and the two new controls. Seventeen retired migration topics are retained
in an explicit historical catalog with topic/signature validation and fail-closed
indexed-layout collision checks. Retaining a decoder neither admits an emitter
nor enables a retired module. The configured emitter allowlist remains unchanged.
New operational events are not new financial income.

## Evidence scope

| Boundary | Observed scope | Record |
| --- | --- | --- |
| Future VRF tuning | Nine distinct new cases and six affected existing VRF/reveal cases pass across scoped runs. The initial run had six passes and two test-expectation failures; only those repaired cases were rerun alongside the six affected existing cases. A final unsealed-importer bootstrap case passes separately. Production NFT source stayed fixed. | [Run scope](vrf/verification-final.json), [final bindings](vrf/source-bindings-final.json) |
| Buyback ceiling | Initial 34/34 passes: 12 new policy cases and 22 existing BuybackExecution cases. A later two-case run passes the strengthened 1,000-run reserve/burn fuzz case and the existing native buyback integration case. That repeated fuzz is not another distinct case: 35 distinct cases overall. Production Buyback source stayed fixed. | [Scope](buyback/evidence.json), [initial run](buyback/operating-and-existing.json), [final targeted run](buyback/native-and-strengthened-fuzz.json) |
| Production inventory | 26 affected NFT inventory cases pass, including two new policy/matching-observation cases. These are synthetic offline manifests, not deployed native inventory or VRF qualification. | [Inventory log](python/config-tests.log) |
| Event catalog | Five final focused cases pass: source/artifact consistency, two new control events, 17 retired-topic decoding and malformed/colliding historical descriptors. An earlier three-case run predates the history repair and is retained separately, not added to the final count. | [Final event cases](python/event-history-tests.log), [exact old-entry preservation](python/event-compatibility.json) |
| Compiler/size | 104 Solidity source/test/script inputs typecheck. All 34 production objects pass normal runtime/initcode gates; 32 source objects are unchanged from the native checkpoint. The normal-profile artifacts from the focused builds have 78 current production compiler bindings, zero mismatches. No extra broad build or unchanged regression suite was required. | [Typecheck](typecheck.json), [size gates](size-gates.json), [compiler bindings](compiler-bindings.json) |

The initial VRF test repairs corrected scheduling-event order and the already
existing `NotReady` selector. The archived test snapshots are retained. An empty
test-name selection ran zero cases and is not passing evidence. No production
guard was loosened to repair a fixture. Source compiler bindings and the
[111-input source/test snapshot](source-sha256.json) identify the final candidate;
earlier checks keep their recorded scope. [Evidence hashes](evidence-sha256.json)
bind the published artifacts; publication receipts are separate.

NFT runtime is **23,929 bytes** (647 bytes under EIP-170), raw initcode 43,923.
Its dynamic URI constructor arguments require actual release-size review.
Buyback runtime is **7,450 bytes**, raw initcode 8,144 (8,240 including its three
fixed constructor arguments). Vault remains 24,504 bytes with 72 bytes of margin.
Solidity remains 0.8.26/Cancun with the existing via-IR/runs-1/yul-disabled profile;
no code-size limit was raised. Actual deployment configuration and target-chain
operating gas remain unqualified.

Synthetic coordinator, venue and inventory fixtures are not actual service
qualification. No fresh full regression, fork, load campaign, real coordinator,
browser extension or independent audit is claimed.

The original 80/10/5/5 allocation, 1% contribution/reward-conversion and 3%
ordinary-maintenance limits, exact NFT inventory and current-owner rights remain.
Typed v4 conversion, explicit ETH/WETH atomic moves, native website profile,
reviewed production inventory, routes/feeds/VRF, operating qualification and
independent audit remain open. See the sole [Todo](../../TODO.md),
[operator manual](../../docs/OPERATOR_MANUAL.md) and
[policy boundary](../../docs/POST_SEAL_POLICY.md).
