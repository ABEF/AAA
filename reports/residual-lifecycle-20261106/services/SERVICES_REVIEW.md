# Main/residual services review

Scope: current main5d70b4b and its shared fresh accounting6 physical reader,
keeper coordination, API/read-only contribution context and source-bound test
fixtures. No runtime/site/service/chain/journal/signer changed.

## Concrete finding and correction

The shared `keeper.compound_policy.observe` used by fresh API portfolio reads,
unsigned contribution context and keeper diagnostics accepted a self-consistent
but physically wrong pair of `Manager.amounts` and `portfolioAmounts` replies.
Its stable portfolio fingerprint was checked only for nonzero. It also accepted
valid individual residual ticks outside the actual main despite fresh creation
always containing the residual inside that main.

Three new pre-fix negative methods demonstrate actual acceptance (all three fail
their rejection assertion in integrity-before.log). This is a read-integrity gap,
not evidence that a holder or keeper can drain funds. Pinned code and successful
on-chain checks remain separate. A Byzantine provider can fabricate an entire
coherent state; local consistency checks are not consensus proofs.

Fresh6 now independently computes each leg's floor principal from already-read
slot0 sqrt price, complete stored ticks and actual PosM liquidity; compares each
Manager view and their aggregate; requires the residual's actual range to be
contained in the main; and recomputes stable/full-info and liquidity-sensitive
fingerprints in the source wire order. Full packed positionInfo is retained.
The child stable getter already checks its main/residual reverse association,
so another reverse-mapping RPC is unnecessary.

One bounded same-block execution-fingerprint getter is added per fresh bucket.
No USD feed/reference/price-policy call is added. Pure physical math is extracted
unchanged into zzz_ops.physical_portfolio; the existing current preflight function
keeps its API through a delegate wrapper. Historical5 math/reader semantics stay
explicitly unchanged. The source/API profile is not a deployment upgrade.

A private accounting6 bucket-proof pair lets contribution_context reuse the
already-verified execution hash instead of repeating its existing getter. The
public read_bucket payload remains unchanged. No cross-request cache, deadline,
control recheck, runtime pin or transaction simulation is removed.

## Case coverage and retained boundaries

- Single main; modeON without a useful residual; modeOFF with an actual residual
  awaiting merge; partial/mixed/fully converted/outside residuals.
- Main growth changes the execution hash while stable geometry stays unchanged.
- Per-leg errors cannot cancel in the aggregate; wrong nonzero stable/execution
  hashes and non-contained physical ranges are rejected.
- Current6 raw claims/ownership remain available during unrelated USD/reference
  outage when physical custody is sound. Existing fee-only harvest diagnostics
  remain spot/oracle independent and are not routed through this value proof.
- Current1-to2-to1 synthetic reader snapshots now use actual ticks/liquidity,
  monotonic geometry/applied revisions, and explicit one-view stale-total faults.
  They do not claim to execute an LP-ID allocation or market transaction history.
- Keeper in-range/below-trigger compound waits, pending mode/range exceptions,
  hourly harvest independence, pending-first recovery, hash-pinned observations
  and legacy profile boundaries retain their existing source behavior.

The served website is current3/unconfigured and does not become fresh6-capable
by this source change. Its README still mentions schema13; matching website
source/config and rollout remain release work. No website file was edited.

## Verification discipline

The new integrity methods include deterministic integer-boundary comparisons
against retained historical/preflight math and direct integer vectors. Fixtures
derive physical replies; negative tests independently corrupt one or several
views. They do not stub production checks or introduce guessed zero values.

Initial affected logs preserve former arbitrary-principal fixture failures.
Their synthetic values were corrected, not economic checks relaxed. The final
runner selects only module-owned TestCases, deduplicates exact IDs and captures
imported Python source hashes before/after. Its focused-final.json/log owns final
counts. No full suite, public/provider acceptance, EVM audit or live load test is
claimed. Raw custody/principal/reward recovery still depends on working core,
tokens, authority and the separately reviewed contract recovery paths.
