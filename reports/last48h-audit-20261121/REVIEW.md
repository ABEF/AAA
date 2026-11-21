# Audit of the last 48 hours

21 November 2026. Reviewed HEAD:
`83a721a0ae48561819fddb366ab0958230dc7ae5`.
Window: **19 November16:48:43 to21 November16:48:43 Europe/Paris**
(CET; the exact UTC endpoints are in [SCOPE.json](SCOPE.json)).

## Result

Reviewed all15 commits in the window and the surrounding code used by their
five changed production Python modules. **No additional confirmed production
code defect was found in those changes.** This is a source/evidence audit, not
independent release approval or proof that every possible state works.

Three documentation/evidence-maintenance issues were corrected. No contract,
Python behavior, financial limit, permission, journal, checkpoint, website or
running service was changed by this audit. Earlier runtime results keep their
original source and workload boundaries.

## Changed-code review

| Area | What was checked | Conclusion |
| --- | --- | --- |
| Claim planner | Request-local copied verifier; exact target/pin/canonical-block cache keys; successful-proof-only insertion; deadline/global-error handling;512-entry bound; first-success prefix; full final preparation; fresh owner/balance/lifecycle/fee/funding/canonicality reads | Both optimizations retain safeguards and exact remaining selections. No cache proof survives another plan. Nonmonotonic refusals and work-budget exhaustion remain explicit limits, not a guarantee of optimal packing. |
| Offline OpenSea mint review | Current contract and preserved upstream ABI/payer/proof semantics; canonical addresses/offsets/bool/tail; phase/cumulative-wallet/static supply limits; exact free-team/paid values; original calldata and source-bound manifest; false readiness flags | Consistent with its offline scope. It cannot establish deployed counters, actual custom OpenSea support, simulation or VRF. Standard signed adaptation remains unselected. |
| Keeper submission | Nonzero hash validation before journal mutation; fatal malformed-output behavior; exact durable intent; no resend; nonce/spend/receipt and shutdown boundaries | The previous zero-hash fix is sound. Existing uncertain intent remains for exact reconciliation. |
| Manual diagnostics | Identical profile2 simulation/estimate/cost envelope and one positive quote; original profile1 behavior; pure pinned compound-observation authentication; no reset/acknowledgement/journal write | Matches the maintained worker's reviewed policy. Confirmation3 reference/threshold-return and malformed proof stay blocked/unavailable. Independent harvest remains separate. |
| Shared process lock | Both keeper/indexer callers; pinned protected direct parent; no-follow/nonblocking/CLOEXEC; owner/type/permissions; inode identity; descriptor cleanup; legacy0644; process-death exclusion | Consistent with the stated trusted-host model. Same-UID attackers, untrusted ancestor directories and multi-host fencing are outside that model and remain documented responsibilities. |
| Verification entry points | New modules registered without inheriting old tests; current generated inventory exists and matches; verifier retains contract/reference/size checks | No weakened test selection or production build gate found. |

Independent parallel source reviews covered claims, minting and keeper/locks.
Findings were checked against actual code/callers and current requirements;
the absence of a new confirmed defect was not converted into an all-safe claim.

No Solidity source, dependency, compiler/profile, ABI, economic split or browser
behavior changed in the window. The website's one corresponding commit is
documentation-only. The four unrelated tracked dirty files and untracked
drafts are excluded and preserved.

## Corrected findings

| ID | Finding | Correction |
| --- | --- | --- |
| A48-01 · Low | Two phrases in the Ubuntu preparation report could imply that keeper authorization and a live harvest recovery receipt were established, despite its correctly stated incomplete outcome | State explicitly that authorization was not established and the receipt proof is a future requirement. Preserve original attempts, archives, source hashes and cleanup; add [dated clarification](../ubuntu-keeper-20261121/ERRATA-20261121.md). |
| A48-02 · Low | Current function-count/reference labels still pointed to older1,977/1,979-definition snapshots while the current checked inventory contains1,980 | Correct current coverage to179 files/1,800 functions/180 classes; explicitly label earlier inventories as historical in instructions/context/handoff. No old inventory is rewritten. |
| A48-03 · Low | The latest named inventory was current, but the anonymous-code supplement still represented276 lambdas at its earlier source | Add a separately pinned [current supplement](ANONYMOUS_CODE_INVENTORY.json):278 lambdas. Reuse its two Yul rows only after exact equality of the trusted F6 source maps. Older276-row evidence remains intact. Inventory is not dynamic coverage. |

## Verification actually performed

- Offline integrity validation of **11 published evidence archives and940
  recorded payload hashes**, including constructor, market, Entry, LP-fee,
  readiness, recommendation and Ubuntu preparation records. Original archive
  bytes are unchanged. Additional embedded manifest files are explicitly listed
  and covered by each outer archive hash. [Exact results](ARCHIVE_INTEGRITY.json).
- AST inventory of the authenticated179 production Python source files. The
  unrelated dirty fork runner uses its preserved published Git blob, not its
  working copy. Current named counts are1,980 and anonymous count278; F6
  Solidity/dependency/build-control maps remain identical to the prior inventory.
- Current inventory, generated Todo, contract/operator references, targeted
  links and protected-file preservation are checked before publication.

**No new dynamic tests, model replays, compiler/size builds, RPC probes, fork
transactions, browser suites or operating rehearsals were run.** The previous
18 focused keeper methods and earlier source-specific claim/mint proofs are
reused, not recounted as fresh passes. A valid hash proves artifact integrity,
not the truth/completeness of every assertion or a new production acceptance.

## Still open

- Cast30/90-second subprocess capture still lacks a byte ceiling. This is a
  known resource-hardening item; no new exploitable fund-loss path was shown.
  Any future cap must retain ambiguous intent and forbid automatic resend.
- The stock normal-daemon/real-Cast Ubuntu signing/recovery journey did not
  run. Eight Unix lock methods are helper evidence, not that missing journey.
  Previous owned units are stopped; this audit performs no remote operation or
  new host-health observation.
- Real independent spot feeds, compatible execution depth/routes, complete
  provider fees, actual custom OpenSea/VRF/authority choices, current consumer
  adoption, operating recovery and independent approval remain qualification.
- Maximum-state direct activation retains its476,135-estimate shortfall.
  Separately paid synchronization is an optional preparation path, not a
  reduction of that direct cold estimate.32M/full20% and24M/full25% limits stay.

The sole Todo retains all83 stable tasks and unchanged statuses. No acceptance
package, release gate, deployment, sealing or public opening is approved.
