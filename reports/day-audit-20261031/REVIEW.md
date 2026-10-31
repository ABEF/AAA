# Management consolidation and current-change audit

Reviewed 2026-10-31, Europe/Paris. Local uncommitted candidate on main, based on
HEAD `37577ebf610ed7182c3d5bc481d7bb32ec5438c1`. This reviews the October30–31
optional-portfolio and residual-management changes and their current consumers.
It is an internal source audit, not a deployment, independent audit or approval
for real funds. Original earlier reports and failures are preserved.

## One operator manual

The management guide and operator guide covered the same operating responsibility.
All unique management procedures now live in the
[Operator manual](../../docs/OPERATOR_MANUAL.md#portfolio-management-controls).
The former [portfolio guide](../../docs/PORTFOLIO_OPERATIONS.md) is only a
compatibility pointer, preserving historical links without a second maintained
procedure. Current navigation and Todo links use the manual. Configuration,
enable/disable, residual-only closure, urgent single-position consolidation,
parking, idle recovery, nonce handling and restart rules remain documented.

## Findings and changes

| Finding | Correction and boundary |
| --- | --- |
| Reference-price failure hid confirmed owners and funded claims. The API reused a keeper observation that called price-dependent maintenance diagnostics. | Accounting5 physical-only observations authenticate both LPs, runtimes, owners, keys, liquidity, geometry and raw principal without maintenance-price reads. Ownership and raw funded claims remain readable; USD/NAV may be unavailable. Malformed physical evidence still fails closed. Default keeper observations retain every pricing/eligibility check. |
| Fresh activation preparation rejected otherwise valid configurations. | `ActivationConfig.verify` now passes the reviewed PositionExecutor binding required by LP-routing2. Actual verifier regressions cover the complete graph and reject missing, changed and historical helper identities; no fallback or new signing permission. |
| Ordinary single-position replacement could create an inactive main despite passing value retention. Narrow inverse-price bands plus permitted reference deviation were sufficient. | Manager exposes an executor-only ordinary-replacement context; the typed child verifies actual active stored ticks before and after mint/refund callbacks for both single and hybrid ordinary replacement. A witness with width400bps, spacing200, a permitted399bps deviation cap and approximately398.84bps actual deviation is rejected atomically. Initial activation/growth policy and explicit emergency behavior remain separate. |
| An unused private Balancer value wrapper survived math extraction. | Removed the uncalled function. All42 production ABIs and executable creation/runtime bytes match before/after this cleanup once actual compiler metadata suffixes are normalized. Metadata/codehash/CREATE2 identities are not claimed equal. |

The new read getter is not a rebalance authority or generic executor. Existing
custody, share issuance, entrant-only budgets, reserve separation, loss floors,
callbacks and atomic rollback remain. The active-main correction intentionally
tightens ordinary replacement; it is a correctness fix, not merely refactoring.

## Audit coverage

Source review followed main/residual custody, ordinary replacement and callback
boundaries, entry tracing and marginal share issuance, harvest/reserve accounting,
residual closure, parking, terminal holder return, canonical gates and the
matching keeper/API/inventory profiles. New source-bound static analysis ran
102 detectors over174 parsed contracts, then all463 findings received contextual
dispositions in [the full triage](static-triage.json). Tool severity counts are
not confirmed vulnerability counts. Manual review, including external calls,
loops, assembly, timestamps, events and suggested optimizations, is not proof
of exploit absence or exhaustive execution.

[Verification](VERIFICATION.md) separates156 distinct Python methods,19 distinct
affected EVM methods across recorded stages,42 fresh normal size gates,
778 explained callable functions, original-code negative controls, the retained
fixture failure and the metadata-only cleanup comparison. Counts must not be
added to earlier campaigns as a fresh whole-suite total.

## Remaining risks and decisions

- **Route-ranking liveness:** a narrow ordinary replacement, single or hybrid,
  may choose an own-pool candidate whose resulting target main is inactive even
  if another reviewed venue could work. The new final guard safely reverts;
  viable-alternative ranking and actual market execution still need qualification.
- **Maximum populated gas:** bounded loops are not universal gas guarantees.
  Core/provider/token behavior, full buckets/asset lists and the immutable
  governance-selected metadata URI payload require operating measurements.
  Lifetime pool aliases are exported incrementally, not assumed globally bounded.
- **External trust:** actual dual feeds/routes/VRF/authorities, upstream behavior,
  OpenSea, metadata hosting, current5 website/services and host/recovery/inclusion
  rehearsals remain unqualified. Strict sampled gaps can restart after delays;
  neither jitter nor sampling establishes manipulation immunity.
- **Privileged emergency risk:** manually selected financial bypasses can lose
  nearly all principal. They remain paused governance-only, outside daily keeper
  automation. Reviewed replacement-code trust and rejecting receivers remain
  explicit rather than being disguised as detector false positives.
- **Maintainability:** unmeasured cache/complexity suggestions were not applied
  merely to reduce detector counts. One older WETH comment is stale; it grants
  no asset admission capability and is recorded in the callback triage.
- **Release:** no independent audit, complete frozen regression/CI, target-chain
  gas/economics or production qualification is inferred from this internal pass.

The [sole Todo](../../TODO.md), feature reference, operator manual, callable
reference, release record and repository context were synchronized. No website,
service, Anvil state, transaction journal, shared signer, public signing or paused
heartbeat was changed. Work is saved locally; no commit, push or deployment was
performed for this request.
