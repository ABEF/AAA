# Focused-test validity and irreversible setup review

**The review found real test-quality and setup defects.** It individually
assesses both cited lists—the earlier30 methods and the later29—and examines
irreversible configuration across all61 Solidity sources. It also surveys the
wider test corpus for affected fixtures. A method count, source inventory or
successful generic seal is not production approval.

Baseline: `003c8d8dc88b60cbfbcc8caf61fa864c6487b40f`, main.
The [adapted execution prompt](EXECUTED_PROMPT.md) distinguishes real behavior
from text/mock checks, current requirements from deliberate compatibility tests,
and actual irreversibility from merely configurable settings. It was challenged
against the source and OpenSea path before implementation and again against the
resulting source/evidence/remaining limitations.

## OpenSea clarification

**Production primary mint is intended for OpenSea through SeaDrop.** The
website mint page remains demonstrative. SeaDrop validates the payment/proof path;
our ERC-721 still issues the NFT and supplies `tokenURI`, traits and artwork.
OpenSea reads that contract metadata. An empty or wrong immutable artwork root
therefore remains a collection defect when minting on OpenSea.
[OpenSea metadata documentation](https://docs.opensea.io/docs/metadata-standards),
[custom-contract guidance](https://docs.opensea.io/docs/deploying-a-seadrop-compatible-contract).

One new focused case runs the pinned official SeaDrop V1 runtime with actual
NFT/Vault/renderer/lifecycle code and controlled VRF. It verifies gross/fee/net
payment, dormant ownership, pending reveal, then revealed metadata using the
collection root without premature royalty eligibility. MockAccess and controlled
sale/provider settings are explicit; this is not hosted OpenSea onboarding,
actual fee approval, public minting or content-availability qualification.
[Result](OPENSEA_ARTWORK.json), [execution scope](OPENSEA_ARTWORK_EXECUTION.json),
[actual compiled-source proof](OPENSEA_ARTWORK_SOURCE_PROOF.json). That case's
Budget source is the explicitly retained intermediate reservation implementation,
not final Budget bytecode acceptance; it does not exercise reservation behavior.

## Task 1 — what the tests actually prove

All59 original methods have individual assessments of intent, assertions,
fixtures, current relevance and missing proof:

- [Earlier30 matrix](EARLIER30_METHOD_MATRIX.md) / [machine record](EARLIER30_METHOD_MATRIX.json).
- [Latest29 matrix](LATEST29_METHOD_MATRIX.md) / [machine record](LATEST29_METHOD_MATRIX.json).

The lists are distinct. Historical passes retain their original source stages;
they are not all rerun or relabelled as current full-system execution. Several
methods remain useful but deliberately narrow. Legacy readers and toy fixtures
are not obsolete merely because they mention older profiles or assets.

Confirmed improvements include:

| Weakness | Correction |
| --- | --- |
| Market mutation occurred within the same pinned block's simulated reads | Move it after the first exact call, between the two canonical anchors, and assert the final stage/envelope. |
| “Accepts only exact source” tested a valid import without tampering | Exercise actual rejection of a changed temporary source copy. |
| “Identical legacy record” checked two fields | Compare the complete independent legacy record. |
| Shared-struct guidance checks searched globally for phrases | Follow each operation's actual linked section and verify its own semantics. |
| Enabled harvest timing could pass without a fresh read or due submission | Assert exact enabled/disabled head-read differences and the due operation itself. |
| Broad seal rejection and incomplete callback rollback checks | Require intended errors, unchanged root/bootstrap, recipient refunds, NFT/helper/VRF request rollback and repeat behavior. |
| Claims asserted return amounts without complete economic changes | Assert recipient deltas, liabilities and designated reserve separation. |
| Tiny royalty cases lacked repeated recovery/transfer ordering | Add deterministic1–6unit rotations, reverse claims and transferred ownership. |
| Current LP test venue lacked the required execution interface | Repair explicit test-only execution/identity seams while forwarding real production math checks; keep independent native-v4 movement proof. |
| Current artifact tests retained an old trusted family | Explicitly admit `seal-boundaries-20261117`, preserve every old family and reject source drift without fallback. |

The wider corpus review also found positive setup roots containing bare schemes,
invariant plan replacements missing the new validator binding, and a normal
verification tool that rejected the narrowly approved public-fixture read
permission while its mocked positive fixture concealed that mismatch. Corrected
checks remain separately counted and source-scoped. Corpus inventories are
navigation/maintenance evidence, **not execution or a manual audit of every
method in the repository**.

The final independent read also caught an instruction mistake introduced in
this review: the new pre-seal checklist requested private `openingFinalized`
storage as if it had a public getter. The checklist now uses actual public
sale-time reads and authenticated finalization history, explicitly distinguishing
time eligibility from finalization. One new check validates **every emitted
critical read** against its actual target's trusted compiler ABI; no production
getter or signing capability was added.

The [current execution-fixture repairs](CURRENT_EXECUTION_FIXTURES.md) address
another concrete source of false confidence: missing current execution readers
and native balance cheatcodes inside operations under rollback test. The venues
now forward actual production math checks, pre-fund synthetic cash during setup
and use reversible EVM transfers during operations. Selected exit, both-leg
accounting, mixed-decimal loss boundaries, handoff and rollback cases execute;
the broader gas/fork/fuzz campaigns retain their unverified scope. The four
selected commit/abort checks have [exact source-closure evidence](HANDOFF_EXECUTION.md),
including unrelated concurrent test edits rather than a false global-stability
claim.

The approach follows the official distinction between stateful handler actions
and invariant assertions in [Foundry's guidance](https://www.getfoundry.sh/guides/invariant-testing),
and the [Solidity security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html).
That is why setup reachability, nonzero economic state, exact rollback and
independent expectations matter more than a large passing total.

One optional historical fork suite still has wrapped-Pons setup assumptions
incompatible with fresh native-only Manager paths. Its disabled-by-default
skips are not qualification; its useful pinned identity observations remain
historical. Do not weaken native guards to resurrect that adapter. Fresh native
fork qualification uses the separate maintained current-pool harness and remains
an actual dependency/market/provider release task.

Exact selected executions, new/adapted distinctions, failures and corrections
are in [verification](VERIFICATION.md). No unchanged full suite, old1000-input
fuzz or long invariant campaign was rerun merely to increase a count.

## Task 2 — systematic irreversible boundaries

[SEAL_INVENTORY.json](SEAL_INVENTORY.json) covers all61 sources:40 concrete
components, five abstract bases, eight libraries and eight interfaces. It combines
curated per-component decisions with exact constructor/immutable/one-time/terminal
source locations. Lexical locators are not a claim that every branch was proved.
[SEAL_REVIEW.md](SEAL_REVIEW.md) records ordering, mutable alternatives and actual
recovery limits; the [operator guide](../../docs/SEAL_READINESS.md) provides the
before-seal procedure.

Three production behaviors are corrected:

1. **Wrong immutable home chain.** Vault construction now rejects a nonzero
   home-chain ID different from the executing chain. Current architecture has
   no cross-chain home ledger. It fails before creating an unusable Vault;
   ordinary same-chain construction/import remains supported.
2. **Bare artwork scheme.** The renderer rejects `ipfs://` and `ar://` without
   any suffix, including constructor and one-time setter paths. Empty draft
   construction remains possible, but the existing controller guard prevents
   sealing an empty root. The unsigned constructor planner rejects the same
   known-invalid inputs before loading artifacts or preparing calldata, while
   preserving empty drafts and suffixed Unicode URIs. This is not
   CID/content/length/availability validation.
3. **Wrong new reservation ID.** Following the operator's explicit decision,
   new bucket reservations must use the canonical companion's origin-derived
   ID. Wrong fresh IDs reject before capacity/alias writes. Existing registered
   aliases, immutable mappings, idempotence and the four-bucket limit remain.

Portable authenticated historical creation bytecode demonstrates the earlier
bad chain/root acceptance; current code rejects those inputs. Native-v4 tests
verify typo rejection followed by successful physical activation and an actual
alias/pool move/return with shares and funded backing retained.

### Size-safe placement of the new check

The first Budget implementation exceeded the normal runtime ceiling by103bytes;
an attempted placement in VaultCanonical exceeded that module by79bytes. Neither
was admitted. The final read-only predicate lives in the **existing**
CustodyValidation child. Budget preserves admission/authority/old-alias checks
and calls the bound Migration validator. No new deployed helper, storage,
custody recipient, writer permission or financial bypass is introduced.

`CustodyValidation.validReservationIdentity(pool,bucket)` is a public **identity
read only**. True does not prove pool admission, authority, remaining capacity or
activation readiness. An empty registered alias remains possible but is not a
new contribution domain. First reservation requires complete Migration/validator
binding. [Reservation behavior and source stages](RESERVATION_REVIEW.md).

## What remains irreversible or unqualified

These are explicit limits, not silently declared fixed:

- **SeaDrop helper and LP converter must bind before seal for the selected
  release.** Generic `Access.seal` still supports explicit local direct-mint
  configurations and does not require both integrations. Omitting them cannot
  be repaired by a later setter. The release review must reject those omissions.
- **An expired nonzero mint end cannot be extended**, even if bootstrap has not
  sealed or minted. An initially unset end can be configured after seal; delay
  the first deadline write until the schedule is viable. No royalty cutoff
  semantics were silently changed.
- **Wrong-but-nonempty content, fixed native venue graph and token identity**
  cannot be repaired by changing an ordinary policy. Reconstruct before funds;
  qualify the actual root length, all artwork paths, code and actual read cost.
- **Unanswered VRF requests can prevent provider rotation/replacement.** No
  reroll or administrator-selected traits were introduced. Actual coordinator,
  consumer/funding/callback acceptance remains necessary.
- **Capacity and lifecycle commitments remain real.** Valid reservations are
  permanent; terminal principal exit and final canonical retirement do not
  reopen through unpause. Canonical abort needs exact transferred backing back.
- **Failed tokens/receivers are external limits.** Exact entitlements and
  retained backing cannot guarantee transfer of an arbitrary broken asset.

The unsigned pre-seal planner now emits all39 constructor boundaries and critical
reads as **unverified**, with no seal calldata or RPC. Inert code parts use
length/hash commitments instead of duplicated payloads. Complete offline inputs
never become live seal readiness or approval.

## Verification and publication boundary

The final closed normal build passes all48 runtime/initcode gates. Concrete
storage layouts are unchanged; the only ABI addition is the public identity
read. Current headroom is Oracle3/Vault32/Budget69runtime bytes; renderer457 and
CustodyValidation5708. The pinned compiler/settings/limits and financial defaults
are unchanged. Foundry gains only a read permission for pinned public historical
test fixtures; the effective normal-profile CLI verifies that exact scope.

Actual final static analysis reuses accepted compiler output without another
compile: **573 records =22 individually current assessments +551 unique exact
referenced-source reuses**. The strict default checks raw and full projected
input. Intermediate analyses/build failures remain historical; independent audit
is still false.

Todo acceptance, operator procedures/tables, feature/reference, current artifact
guidance and repository memory are reconciled. Existing reports and the four
protected dirty files remain preserved. No public transaction/deployment/seal,
existing Anvil reset, site/service rollout, signer extension, journal rewrite or
paused-monitoring restart occurred. Actual markets/providers/VRF/OpenSea/content,
complete fees/gas, operating acceptance and independent audit remain open.
