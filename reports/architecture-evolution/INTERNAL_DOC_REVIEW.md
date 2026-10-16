# Internal documentation and enumeration review

2026-10-17. This is a scoped internal review, not an independent audit, a new
task list or production approval. The [check receipt](docs-check.json) records
the observed source/document hashes and exact selective-staging deltas. No test
suite, network query, signer or transaction was run for this review.

The observed central ledger preserves all 38 prior task IDs and titles, adds only
`custody-composition`, and keeps Contracts / Backend / Frontend first with all
seven area positions unchanged. It contains 39 unique tasks: 13 To do, 17 In
progress and nine Implemented locally. Generated `TODO.md` exactly matches the
ledger through the existing generator's render function. This is not evidence
that pending production requirements have been completed.

The final [check receipt](docs-check.json) checks local clickable links and
Markdown/HTML anchors against the intended publication tree, using the four
scoped copies and HEAD content for excluded dirty files. External URLs were not
network-checked. The
legacy destination-capacity anchor is retained. The architecture and README link
the address inventory, whose wallet/contract/helper/dependency distinction agrees
with the local deployment template. Production addresses remain unset.

The architecture correctly separates the implemented permanent four-identity
admission repair from proposed different-pair composition epochs, canonical
ownership/ledger relocation and the accepted but unimplemented aggregate 3%
migration execution budget. Activation/top-ups retain their original-source 1%
budget. Local reservations do not authenticate remote admission or provider
delivery, and permanently unused reservations can exhaust capacity.

## Selective publication boundary

The four originally dirty documentation files were reviewed against HEAD-based
copies in the external `scoped-docs` directory. `AGENTS.md` and
`PROJECT_CONTEXT.md` add exactly the same architecture handoff as the measured
pre-work-to-worktree delta; their unrelated existing work is excluded.
`CHANGE_AND_RECOVERY.md` changes only the capacity explanation and the direct
local versus approved external custody trust wording. No pre-work byte snapshot
was available for that file, so its isolation was assessed manually from its
HEAD diff rather than asserted as an exact snapshot comparison.

The initial scoped `ROADMAP.md` copy was unchanged HEAD because its transformation
matched a paragraph that existed only in the dirty worktree. It was corrected by
inserting only the final architecture/capacity paragraph before section 6. Its
unrelated operations-hardening paragraph remains outside the scoped copy. The
exact repaired diff and hash are retained in the check receipt. No pre-work byte
snapshot was available for this file either.

Intermediate scoped copies for previously clean README/ledger/release files are
not publication inputs: root explicitly stages their full current versions.
They must not be substituted for those current files. The ledger, context and
publication work remain owned by the root agent; this reviewer made no Git change.

Candidate-tree checks distinguish an existing worktree file from a published
target. Excluded unsigned frontend transaction documentation/reports are not
newly linked as if included. The historical static review archive and replacement
canonical static record are explicit publication inputs. The root will refresh
the external publication manifest after these two review files are finalized;
the check receipt identifies any pre-refresh digest differences rather than
pretending the intermediate manifest was already final.

## Reserved None-state consumers

Read-only searches found production `bucketCount` / `bucketAt` enumeration in
membership and keeper discovery. Both skip unfunded `None` entries before pool
accounting or financial reads. The existing two-case keeper receipt separately
covers real static-ABI decoding, bounded cursor progress and health; those tests
were not rerun here.

The production manifest validator checks explicit reservation identity, assets,
observed block and independent evidence without equating it to funded group
count or requiring activation. It remains an offline inventory validator, not a
live remote-capacity proof. The revenue sampler requires explicit local Active
custody before LP valuation. NFT projections discover canonical minted identity,
owner, shares and royalty eligibility rather than treating reserved buckets as
NFTs or TVL. The raw `PoolReserved` event does not create indexed ownership.
No compatibility defect from permanent unfunded admission was identified in
these paths; actual providers/services remain release qualification.

## Controlled canonical migration design

The [canonical migration design](../../docs/CANONICAL_MIGRATION_DESIGN.md) matches
the user's accepted direction: planned whole-protocol migration while the source
chain still executes. Post-halt recovery remains deferred. No verifier, attestor,
emergency committee or arbitrary successor is silently authorized, and current
sealed modules are explicitly unable to acquire the design by configuration.

The design distinguishes operational pause from protocol-wide canonical freeze.
Only a proved pre-terminal abort can restore source operation; terminal source
commitment is irreversible and finalized before destination rights activate.
It retains exact identities, immutable traits, remaining without-replacement
inventory, LP shares, both ledgers, fractions, complete-population denominators
and classified backing. It addresses contract-owner incompatibility, data
availability, late immutable marketplace/creator receivers and multi-successor
forwarding without double allocation.

The final atomic raw-balance cutoff and one-time captured-delta settlement prevent
moving receipts from entering both base export and late funding. Existing
all-pending sync interfaces are explicitly unsuitable without changes. Cutoff
gas, proof/finality mechanisms, bounded imports, actual token routes and operating
authority remain implementation/qualification requirements. The 3% principal
execution budget does not authorize a haircut of funded reward liabilities.
No blocking inconsistency was identified in this design review; this is not
implementation evidence or an independent security audit.

## Finalization limits

The stale security introduction was corrected to distinguish historical economics
from current capacity evidence. The feature reference identifies the review
branch rather than implying a merge into main. Current targeted gas/return,
provider-trust, 23-object/29-source build and 221-finding internal static records
are linked separately from historical full-suite/fork results. This documentation
review did not rerun those checks or independently reproduce their execution.
Later document or report additions require refreshed link/hash observations
before relying on this frozen snapshot for publication.

The release remains **NOT APPROVED**.
