# Exact verification scope

Baseline `ac98b5b`; final implementation/publication identity is recorded
separately. Production is **NOT APPROVED**. No unchanged broad regression was
repeated merely to increase counts.

| Slice | Actually verified | Evidence and limits |
| --- | --- | --- |
| Optional Pyth reader | 17 new Solidity methods pass, including one 1,000-sample confidence-boundary fuzz test and existing native Oracle integration. | [Source-bound receipt and raw results](feeds-routes/VERIFICATION.md). Fixtures do not verify Pyth proofs, real feeds, source independence or updater operation. |
| Normal production build | 43 production sources; 38 object gates pass. The 37 preceding objects are byte-identical to the prior readiness build. | [Size/input hashes](feeds-routes/source-size-gates.json). Vault remains 24,263 runtime bytes with 313 bytes of headroom. No size/gas limit was relaxed; release constructor encodings still need qualification. |
| Mint/VRF profile and CLI | 68 distinct Python methods across recorded scopes: 15 new and 53 affected existing cases. The unqualified current template returns exit 1 as expected. | [Run/source record](vrf-opensea/VERIFICATION.md). Synthetic manifests establish gate behavior, not provider/marketplace approval. Current OpenSea support is explicitly false. |
| Review exporter/verifier | 19 distinct Python methods across recorded scopes; a real baseline export/verification also passed. | [Run/source record](operations-audit/verification.json). Final fixture-admission changes reran their three affected cases; do not claim a fresh final full suite or protocol regression. |
| Callable reference | 32 contracts,698 functions,32 constructors,15 receive hooks;10 distinct generator checks pass. All top-level inputs have meaning/units notes. Exact output types, names and tuple fields are retained;142 output positions rely on function-purpose/ordered-field explanation rather than separate prose. | [Final reference checks and source bindings](function-reference/VERIFICATION.md); documentation generation does not execute functions. |
| Public runtime observation | 16 successful logical checks, 32 HTTP posts, canonical-block recheck. | [Dated observation](vrf-opensea/observation.json). One provider; code presence and empty standard proxy slots do not prove immutability, source equivalence or proof validity. |
| Fresh source/route probes | Pinax 429, one retry 429, documented endpoint 403. | [Retained failures](feeds-routes/VERIFICATION.md). No fresh route/price or provider qualification; no indefinite retry loop. |

The 68 gate/CLI and 19 review-package methods are disjoint, hence 87 distinct
Python methods plus10 separately recorded generator methods (97 distinct Python methods across these disjoint scopes, not a full fresh final-revision regression). Fuzz
samples and repeated cases are not added as extra distinct tests. No new test
counts are inferred from documentation-only price or authority clarifications.

An independent internal read-only second review found no confirmed exploit or
false-current-ready path in the inspected new Pyth and mint-gate changes. It
confirmed important residual limits: confidence is midpoint screening, a proxy
runtime pin does not pin its implementation, and the required OpenSea gross/net
payment split is not yet implemented. This is not an external audit or security
guarantee.

The external frozen archive will be regenerated from the exact implementation
commit after publication and its hash recorded separately. The archive is a
source handoff, not a final approved release or dependencies-included environment.

No website source/build/server, shared signer/client/coordinator, running local
chain, NFTs, LP, balances, transaction journals or paused monitoring changed.
Memory-only website updates are separate from a website rollout. Preserve all
historical evidence's original source scope and unrelated local drafts.
