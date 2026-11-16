# Unsigned pre-seal configuration planner

Implemented the authorized fresh-configuration planner on baseline main
`502c1c8066465a7690e21ae9138b73e83d2bfc3f`. Twelve fixed setup families now
produce ordered, conditional current-ABI calls instead of only unprepared
checklist entries. Unknown own inputs and required earlier families retain
blocked status/null calldata. All live-state, authority, runtime, readiness and
production-approval flags remain false.

**No RPC, signing, submission, deployment, nonce reservation, adoption or seal.**
No existing Python/Solidity source, compiler/build, financial/default/size limit,
signer, chain, DB, journal, site, service or paused heartbeat is changed.

New source: [planner](../../zzz_ops/preseal_plan.py),
[CLI](../../scripts/prepare-preseal.py), [nullable example](../../config/preseal-preparation.example.json),
two focused test modules and one synthetic-input helper. The existing constructor
and address/nonce planners stay byte-identical.

## Implemented behavior

| Area | Concrete behavior |
| --- | --- |
| Current build | Exact trusted metadata2-20261116 source/ABI/normal-size checks are reused. Historical/unknown builds do not silently fall back or become current. No compiler or size gate is rerun. |
| Typed scope | Twelve closed setup families: feeds, fixed ZZZ, Rewards asset, Migration token, execution references, native pools/orientation, execution/conversion routes, confirmation, initial VRF, reviewed SeaDrop terms, NFT-forwarded upstream settings and official mint end. No arbitrary selector, target or calldata input. |
| Caller/address | Explicit bootstrap is the conditional pre-seal caller. Governance is not inferred as bootstrap. Child addresses are operator-supplied actual-getter assignments, never factory predictions. Known graph/dependency/authority collisions reject. |
| Blocking | Null objects/scalars/lists stay unknown. Missing own/prior inputs suppress calldata, while independent complete families can still be reviewed. Extra fields, coercions, invalid hashes, duplicate identities and out-of-bound values reject. |
| Asset/source consistency | Fixed ETH/ZZZ only; Assets/Rewards/Migration/Buyback identities and declared native pins agree. Two-source address/ID, freshness/precision/disagreement bounds stay. Enabled execution-source pins must match admitted ZZZ policies with18decimals; no independence proof is inferred from IDs. |
| LP setup | Valid hookless native keys, bounded configuration, one contribution destination and selected initial pool identity. Explicit `Strategy.setRangeOrientation(poolId,1)` follows each admission; admission alone leaves the raw-ratio default. Venue IDs must be admitted and operations-enabled. |
| Routes/confirmation | Bounded native-v4 converter and Balancer lists, exact source/native/core/state pins, no wrapper/v3 restoration. Reference corroboration stays required. Deliberate stopped settings are displayed, not treated as missing or automatically bypassed. |
| Mint/VRF | Full8-argument initial randomness call. Existing source-bound OpenSea artifact is digest-pinned/rebuilt and matched to NFT/SeaDrop/payee/current initial0.05ETH price. Upstream calls target NFT, with exact SeaDrop first argument. Fresh empty external lists are explicit; no partial-state clearing/resume. Official end matches publicEnd and remains inclusion-time-unverified. |
| Publication | Existing64KiB input/16MiB output bounds, safe argument errors and exclusive flushed publication. Existing/racing/dangling outputs are preserved; late failures expose possible complete unapproved output. No execution switch, gas or nonce envelope. |

Local array/URI bounds are review-work limits, not reduced on-chain lifetime
capacities. `explicit_operating_stops` names deliberately empty execution venues,
converterOFF, maximumGap0 or no contribution destination. Static completeness can
describe a stopped system; it is never a readiness or release decision.

Shared native pin constants are reused from `production_v2` and checked against
the trusted current Registry source. Only constants are reused: no historical
observer/validator, ABI/profile, custody codec or deployment is adopted.

## New-planner defects caught and fixed

1. Source review found complete upstream input could dereference unknown
   SeaDrop terms. It now returns a blocked preview; a new regression passes.
2. The first implementation accepted an enabled execution-source policy with
   declared8decimals, although current execution requires18. A new regression
   reproduced that acceptance; the planner now rejects the contradiction.
3. Mutually matching but wrong native code pins could pass even though the
   Registry requires specific fixed ZZZ/core/state hashes. A new regression
   reproduced all3 cases; declared pins now agree with the actual source guards.
4. Known same-graph protocol implementations cannot be declared as price feeds
   or VRF coordinators. Unknown external contracts remain unqualified rather than
   being assumed safe. No extra restriction is inferred merely from wallet roles.

These are new planner validation corrections, not claimed production-contract
defects or weakened on-chain rules. The original candidate/failure evidence is
retained, without reinterpreting old runtime or test scopes.

## Verification actually performed

**45 distinct new methods pass:27 core and18 CLI/publication.** The final core
runs as3 targeted methods plus24 previously unrun methods. Earlier failed/newly
affected selections are not extra coverage. CLI preparation is injected; exact
CLI/test logic remains unchanged across its recorded source-scoped selections.

Two actual CLI paths additionally compose current real preparation and exclusive
publication: a synthetic complete input returns0 with24 conditional calls, and
the compact all-null input returns2 with a blocked preview. They do not qualify
their invented authorities, feeds, VRF, markets or platform terms.

All24 encoded calls across21 contract-qualified ABI functions match independent offline
Foundry Cast1.4.4 encoding, including nested structs, string arrays, UTF-8,
zero-address native values and dynamic offsets. These are byte-encoding
witnesses, not24 extra test methods, transactions or successful EVM simulations.
Encoding follows the [Solidity0.8.26 ABI specification](https://docs.soliditylang.org/en/v0.8.26/abi-spec.html).

Existing suites, Solidity/compiler/static-analysis/browser/provider campaigns
were not rerun. Final mechanical checks cover Todo generation, links, exact
source preservation, evidence integrity, whitespace and staged/committed Python
import closure. They are not additional tests or a published-CI-green claim.

## Remaining before deployment

The [deployment](../../TODO.md#task-deployment-initcode) and
[inventory/preflight](../../TODO.md#task-native-production-preflight) tasks remain
In progress. Real addresses/caller/code/getters/bindings, fresh unsealed zero-mint
state, current sale price/payee/root/payers/empty upstream lists, future inclusion
timing and exact operation simulations/complete fees still need verification.
Two independent qualified valuation paths, usable venues, supported funded VRF,
OpenSea acceptance, content/services/operations and independent release approval
remain open. A supplied review hash or complete plan proves none of those facts.

See the [operator procedure](../../docs/OPERATOR_MANUAL.md#prepare-unsigned-pre-seal-configuration),
[input guide](../../docs/PRESEAL_CONFIGURATION.md), [verification stages](VERIFICATION.md)
and [lossless evidence inventory](EVIDENCE.json).
