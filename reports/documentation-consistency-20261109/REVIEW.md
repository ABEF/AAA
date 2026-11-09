# Documentation and review-artifact consistency

Starting contract revision:`c56e260b25895842d8d2ed458bfd7abfe910a5c3`.
Starting website revision:`a41dbf8c901a5ecf573d68494eaf6052d40713e8`.
This maintenance updates current guidance and review-export instructions; it is
not another contract/security audit or production qualification.

## Reconciled current guidance

- Current release inventory17/mint2/V10 and its20 callable helpers+2 inert data
  children are separated from original source9/schema16/V9 and historical
  consumer/runtime records. The existing whole-unit LP domain is preserved
  inside the newer outer handoff; old evidence is not relabeled.
- Total contribution defaults3%/97% deployed LP; conversion1%, maintenance3%,
  additional-loss1%, two-source agreement3%, idle and caller/venue guards remain
  separate. Explicit historical200-bps client ceilings are preserved.
- The feature reference, roadmap, operator procedures, deployment/preflight,
  metadata, security, reward/history and compatibility guides now use the
  correct current or explicitly historical scope. Ten source-bound callable
  descriptions were corrected; no ABI, permission, argument or example changed.
- The central ledger retains all77 task IDs, statuses and order. Current LP
  whole-unit accounting, implemented cooldown observations/Entry3 and LP-only
  conversion replace stale unfinished/index/royalty-conversion wording.
  Original-currency royalties and unresolved release gates remain explicit.
- Six website documentation files are aligned with these boundaries. Website
  source9 stays V9 and unsigned, public configuration remains null, and older
  demo/review settings retain their original meaning. No site build or rollout
  is implied by publishing those documents.

Original documents were archived externally before edits. Historical reports,
dated changelog entries, deployed runtime profiles and recorded failures remain
unchanged. Repository context is current project memory, not a background
deployment/synchronization service.

## Versioned frozen review instructions

The exporter still generated old inventory6/confirmation2/direct-mint guidance.
Editing the existing instruction strings would invalidate authentic old bundles
because verification checks their exact text. New exports therefore use
**archive instruction schema3**. Original schema1/2 instruction and ZIP bytes
remain exact and verifiable. Archive schema is independent of contract/API/
inventory/journal versions; no protocol implementation or financial rule changes.

Schema3 directs reviewers to the frozen commit's actual profile, keeps approval
false, explains current mint2/V10/3% reference boundaries and prohibits implied
signing/deployment/rollout. Source exclusions, dependency records, size bounds,
safe paths, deterministic publication and old archive identity remain protected.
[Procedure](../../docs/FROZEN_REVIEW_BUNDLE.md).

## Verification and publication boundary

[Bundle verification](bundle/final.json) records26 distinct final stable passes
(7 profile+19 integrity methods), with original schema1/2 handoff/archive hashes,
cross-version relabel/mixed-handoff rejection and unchanged protected function
ASTs. Original red, overlapping and formatting attempts remain in the
[bundle evidence](bundle/artifact-sha256.json). No old/full contract suite,
market fork, browser test or static analyzer was rerun for this maintenance.

Generated Todo/callable/operator references, local Markdown file links and
heading fragments, example preservation, protected hashes, exact staged import
closure and local/remote publication identities are checked before completion.
Heading-fragment checking is heuristic; external web pages are not comprehensively
revalidated. All958 operator examples remain unresolved documentation templates,
not executable approval.

[Final integrity](final-integrity.json) records77 unchanged task IDs/statuses,
958 unchanged examples, unchanged callable source/ABI snapshots and financial
code/configuration, plus3,749 checked local links and1,466 heuristic fragment
checks with no unresolved targets. The website documentation publication is
`0236210e357d1c1dfaacedd54aa6d9b1205267ee`; its code and signer are unchanged.
Exact artifact hashes are in [the manifest](artifact-sha256.json).

No production Solidity, financial backend, frontend code/configuration,
existing Anvil/NFT/LP/balance/journal, signer, service, website deployment or paused
heartbeat changes. Only current documentation, the Todo generator's explanatory
prose and versioned review-export instructions/associated tests change.
Actual providers/routes/VRF/authorities/OpenSea, matching services/site, gas and
operating recovery, and independent audit/remediation stay open in the
[sole Todo](../../TODO.md).
