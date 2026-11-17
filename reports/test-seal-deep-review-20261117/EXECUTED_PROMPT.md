# Test validity and irreversible configuration — improved audit request

## Objective and actual scope

Improve the current PoPL candidate through two coordinated workstreams:
critically validate the focused-test claims and systematically examine every
irreversible construction/configuration/lifecycle boundary. The purpose is to
fix confirmed defects and weak verification, not accumulate passing-test counts
or produce another generic report. Baseline is main `003c8d8`.

Production primary mint is intended for OpenSea through the pinned SeaDrop
integration, not the demo website. The ERC-721 still owns issuance/accounting,
random draw, `tokenURI`, lifecycle traits and royalty receiver behavior. Trace
both the primary-payment/callback path and OpenSea metadata retrieval; neither
marketplace listing nor a compatible ABI proves product onboarding or content
availability.

## 1. Establish evidence before changing anything

Read current repository instructions, both project READMEs where relevant,
central Todo, operator procedures, current architecture, constructors and
dependencies. Preserve the four unrelated dirty tracked files, old reports,
existing Anvil state, journals, websites/services, signing restrictions and
paused monitoring. Main only; no public transaction, deployment, sealing or
service adoption is authorized.

Reconcile the earlier **30** operator-input methods and the later **29**
behavior-follow-up methods from exact records. Identify any overlap rather than
adding totals blindly. A fuzz input, loop iteration, inventory entry, compiler
gate and static detector disposition is not another test method. Retain source
stages, failed attempts, skipped/zero-selected checks and fixture limitations.

## 2. Critically examine every claimed method

For each distinct method record its exact name, intended property, production
path and current profile, fixture/dependency seam, assertions actually made,
nonzero preconditions, what a plausible faulty implementation could do while
still passing, and whether it establishes behavior or only structure/text.

Compare assertions with production source and economic requirements. Examine
authentication, amount/recipient deltas, liabilities/reserves, prior rights,
repeat calls, rollback of every relevant state object, emitted receipts and
timestamps. Check exact errors when they define the intended rejection. Avoid
tautologies, overly broad reverts, self-generated expectations, impossible RPC
states at one pinned block, mocked success mistaken for EVM execution, and
fixtures that fail before reaching the intended scenario.

Classify each method as current/relevant, current but narrow, needing
strengthening, historical compatibility only, redundant or obsolete. Do not
delete an adversarial case just because it uses a deliberate historical wire.
Improve confirmed weaknesses, keep useful independent oracles and assertions,
and run only new/changed or materially affected selections. Use meaningful
boundary and state-transition cases rather than mirroring implementation logic.
Explain fixture/runtime limits and avoid universal completeness claims.

## 3. Inventory all irreversible boundaries

Inspect every current Solidity source and its constructor, immutable field,
constant, one-time assignment, bootstrap-only setter, seal-sensitive operation,
terminal flag and frozen/canonical state. Account for factory-created helpers,
typed children and externally pinned dependencies, not just top-level modules.

For each boundary identify the exact source/check, input provenance and units,
who can commit it, prerequisites and binding order, what becomes unavailable,
how to verify it before commitment, the earliest unrecoverable state, and the
real post-commit remedy. Distinguish an ordinary governance edit, temporary
external outage, reviewed replacement, terminal holder exit/redeployment and
absence of any in-place repair.

Cover at least:

- Controller/module/helper reciprocal identity, uniqueness, parent/controller,
  policy/renderer/budget/canonical bindings and deployment chain identity.
- Fixed ETH/ZZZ identity shared by contributions, Rewards, buyback, native pool
  admission and holder return; constructor decimal/native dependency constraints.
- Exact native core/periphery/Permit2/state bindings versus compatible-looking
  but permanently unusable alternatives; proxy/upstream mutability limitations.
- SeaDrop helper and LP converter binding before seal, selected release versus
  explicit local/direct-mint profiles, external SeaDrop runtime rotation limits,
  gross/net fees, payers, proof terms, inclusive windows and lifetime counts.
- One-time artwork root and renderer; blank setup, malformed/empty identifiers,
  wrong-but-nonempty content, all evolution paths and marketplace refresh. Do not
  represent a nonempty string check as content or availability verification.
- Initial VRF configuration, funding/consumer admission, pending requests,
  rotation only after finalized draws, immutable original callback authority,
  unavailable providers and absence of reroll/admin-selected artwork.
- Mint end, inability to reopen after closure, first mint/allowlist terms,
  one-hour royalty opening/cutoff, zero-cohort funds, irreversible allocations,
  admitted-currency capacity and existing entitlement/outage behavior.
- LP pool history/capacity, fixed position ownership, residual mode transitions,
  parking versus terminal return, final principal allocation, deferred payouts,
  claims and future royalty rights after exit.
- Preparation, importer selection before sealing, freeze/funding/abort/retirement,
  exact same-chain schemas and whether replacement is actually available when
  dependencies fail. Do not call replacement a universal recovery mechanism.
- Governance/keeper/guardian key loss or compromise; one human may manage
  separate capabilities. Preserve the explicit software-only compound waiting
  decision; do not silently add a contract policy.

Evaluate omitted, swapped, wrong-chain, zero, stale and internally coherent
wrong dependencies; partial setup, repeated calls, restored settings, callbacks,
market changes, first mint, supply underfill, outages and delayed inclusion.
Identify interacting irreversible prerequisites rather than auditing each setter
in isolation.

## 4. Correct and verify

Implement independently justified source/tool/test corrections while preserving
ownership, custody, fixed economic rights, authorization, limits and atomic
rollback. Distinguish behavior fixes from test/fixture repair and documentation.
Do not impose a new universal mint/operating policy merely to simplify tests.
If a consequential choice remains unresolved, give concrete alternatives and
continue independent work.

For changed Solidity, retain normal compiler/settings and size limits, exact
source/runtime/build admission, current generated function reference and strict
static-analysis evidence. Reuse unchanged evidence with exact scope; no whole
suite rerun solely for a new count. Source publication does not upgrade old
deployments or adopt operating settings.

Turn the inventory into an operator-readable before-seal checklist with exact
reads, expected values, fixed versus editable settings and honest recovery
limits. Keep unknown live state unverified/blocked; no seal calldata, automatic
force, signing or approval. Update the Todo, operator guide, feature reference,
current technical guidance and repository memory together.

## 5. Review the work twice and report

First challenge the plan against actual source, selected architecture and
OpenSea requirements. Then independently review final changes, inventories,
claims, method counts and remaining uncertainty. Report material fixes,
per-method assessments, all irreversible categories, actual verification,
unresolved decisions/release blockers and exact local/GitHub publication state.
Never promise exhaustive security, successful delivery for arbitrary broken
tokens or permanent external service availability.
