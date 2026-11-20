# Readiness reconciliation and offline mint-review implementation

20 November 2026. Baseline main `9d1033a60029fb5b4112c28b6c8bd9015ebd0321`.
**Production remains undeployed and NOT APPROVED.** Pool selection stays deferred.

## Outcome

The sole Todo, current findings and roadmap now distinguish all23 acceptance
packages and83 stable tasks from whole-package approval. Counts remain35done,
40in progress,7todo and1excluded; no task or release percentage is invented.
[STATE.json](STATE.json) maps every package to its existing owning tasks and
retains unresolved scopes. Completed compiler/construction/settlement/backend
subchecks do not close actual market/provider/platform/operating acceptance.

The unblocked advance adds **saved unsigned mint intent review** to the EXISTING
OpenSea preparation tool. It implements no new mint authority, contract, wallet
submission, generic executor or platform adapter. A separate standard-OpenSea
adaptation **PLAN** and pinned OpenVRF source investigation expose actual remaining
decisions rather than making unqualified integration changes.

## New functional behavior

Run `python scripts/prepare-opensea-drop.py review-mint INPUT.json --output NEW.json`.
The exact normalized input contains a checked source-bound manifest, explicit
caller/minter/phase/quantity/review-time intent and the saved transaction's
chain/from/to/value/data fields. It is not an assumed authenticated REST response.

The reviewer:

- Checks the current manifest/source graph and exact chain4663/SeaDrop/NFT,
  intended payer/recipient, quantity and gross wei payment.
- Accepts only canonical current-profile `mintPublic` or Merkle `mintAllowList`.
  Enforces static ABI widths, high address bits, bool, exact13-word head,
  proof offset416, length0–10 and no extra/trailing data.
- Checks the selected phase's exact terms/proof and supplied inclusive review
  window, admitted delegated payer, batch/wallet and maximum static public supply.
  Zero possible public supply refuses; unused allowlist rollover remains valid.
- Rejects signed/configuration/unknown calls and unsupported object fields.
  Retains the supplied transaction/calldata without constructing or rewriting it.
- Publishes an exclusive output with domain-bound audit hashes. **Every actual
  readiness flag remainsfalse.** No network, signer, send or automatic queue.

Current on-chain configuration, remaining original-mint counters, authority,
chain time, runtime, balances, simulation, nonce/gas/fees and OpenSea acceptance
remain unverified. Static intent matching cannot replace those checks or approve
a signature. The [operator guide](../../docs/OPERATOR_MANUAL.md#review-a-saved-mint-transaction-offline)
documents every input and the source/rebuild/review procedure.

## What actually passed

| Evidence | Actual scope |
| --- | --- |
| First focused run |11 NEW methods,4.222s unittest; independent ABI assembly and synthetic source fixtures. Payment/recipient/quantity/phase/proof/ABI/payer/capacity/source/JSON/CLI/exclusive-output cases pass. |
| Additional boundary run |Only3 NEW methods,5.533s; singleton empty proof452bytes,10-sibling proof at772byte maximum with1000 eligibility leaves, and positive multi-NFT free-team/paid-public values. Prior11 methods are not rerun. |
| Current-source CLI example |One new CLI invocation uses105 actual source/dependency/tool pins with illustrative NFT/participants/time. Quantity2 at nominal0.05ETH has exact0.1ETH payload; transaction unchanged and all readiness flagsfalse. No actual API response or mint occurs. |
| Independent read-only review |Cross-checks code and tests against retained SeaDrop V1 ABI/payer/leaf/payment semantics. No material defect found; suggested boundary cases are the separate3-method run above. This is not independent production audit. |
| Source inventory |179 production Python files/1,979named definitions, up by two functions. All61 Solidity/39dependency/4build-control pins and1,021 ABI rows remain unchanged.276lambdas/2Yul helpers retain source-only classification. |

Exact receipts, stdout/stderr and stage-one test bytes are retained in
[evidence.zip](evidence.zip), bound by [the manifest](EVIDENCE_MANIFEST.json).
The first11 test-file hash is not relabeled as the later14-method source.
Production module SHA256 remains
`01f86be5db2a2d8102b51e1d7fe3a4aae451d53cce7726dfbf3f32e064047480`
across both test stages. The actual-source CLI example is not another unit test
or proof of real mint eligibility. No unchanged suite, compiler, Solidity,
browser, historical population or real-market/provider campaign is rerun.

## Source-bound artifact maintenance

`opensea_drop.py` was already part of each manifest's self-source identity. Its
changed bytes intentionally invalidate an old artifact under the new checker.
Keep original requests/artifacts and explicitly rebuild/review current ones;
never edit an old hash or claim the new checker authenticated an old source.
No deployed profile, journal or checkpoint is migrated. `service.py` and its
checkpoint semantic identity are unchanged.

Only that production Python module changes. The normal verifier now selects
[the new inventory](FUNCTION_INVENTORY.json); old inventories/reports remain.
New test discovery is automatic through the maintained test runner. No gas,
fee, RPC/work, financial, authority or privacy restriction is relaxed.

## Concrete platform finding and plan

OpenSea's [standard edit API](https://docs.opensea.io/reference/save_drop_edits)
explicitly rejects Merkle presales. Its public-first stage array, adjacent UI
stage times and additive wallet-limit descriptions need exact payload translation;
they are not automatically four proven on-chain defects. Its
[publish API](https://docs.opensea.io/reference/build_drop_publish_transaction)
computes signer/fee/payer/configuration calldata for the on-chain owner.

PoPL intentionally uses Merkle presales, direct Access governance and typed
setters. The [standard adaptation plan](OPENSEA_ADAPTATION_PLAN.md) identifies the
needed boundaries and preserves business rules as acceptance requirements, not
promises that a thin interface patch can enforce them. Notably, SeaDrop V1's
signed validator has a minimum price without an exact maximum; the NFT callback
does not reveal the signed mint context. Exact free-team/paid-price, signer trust,
stage boundaries and authority/payload behavior need explicit resolution.
Preparing the plan is not approval to implement contract or economic changes.
The new current-profile reviewer deliberately rejects `mintSigned`.

## Additional VRF progress, not provider admission

[Pinned OpenVRF research](VRF_RESEARCH.md) authenticates source revision9fb960c
and its Git tree. Its no-expiry/same-result-retry structure is a new lead for
original-request permanence. It is payable, one-word and self-hosted; PoPL's
subscription/two-word interface, funding separation, derivation and authentication
need separate design. Its2–4second beacon lead depends on sequencer timestamps;
crypto/dependencies, liveness and operations remain unqualified. Organization
names are not endorsement. Seven source fetches succeeded; an eighth failed and
was retained without retry. No chain RPC, adapter or provider is adopted.

## Remaining work and preservation

Pool selection/actual independent feeds/routes/depth,32M/24M provider/complete
fees, full-normal1000-NFT workloads,476135 estimated-gas reduction, actual
OpenSea/VRF/authority/content/submission/host recovery and independent approval
remain open. The gas target is not claimed fixed by a speculative codec edit.

Original changed documents/source were archived before edits. Preserve the four
unrelated tracked dirty files, existing Anvil/NFTs/LP, journals/checkpoints/dist,
popldemo/poplint and services. Browser signing stays Anvil-only and public
configuration remains null. No public transaction, deployment, sealing, service
change or paused-heartbeat restart occurred.

[Preservation checks](PRESERVATION.json) verify the18 original archives, four
protected dirty-file hashes, unchanged contract/dependency/build inputs, all23
package/83task mappings,22 archived evidence members and38 new local document
links. They inspect bytes and saved receipts; they rerun no behavioral tests.
The [staged Python publication check](PUBLICATION.json) records static import
closure against staged Git blobs, independent of unrelated local drafts. It is
not a runtime test or production approval.
