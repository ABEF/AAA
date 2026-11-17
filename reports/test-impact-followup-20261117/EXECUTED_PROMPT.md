# Follow the repaired tests into the behavior they were meant to verify

Start from main `fdb7562`. The previous review repaired obsolete fixtures and
assertions, but its finite selected passes did not establish every dependent
workflow. Trace the repaired test infrastructure into its consumers and the
actual production code. Recheck intended properties, not just test names or
whether setup now succeeds.

1. Build an exact dependency and inheritance map for the changed test roots.
   Distinguish imported code, intended assertions, branches actually exercised,
   inherited cases, historical compatibility and unverified workloads. Existing
   source-scoped successes remain historical; never reinterpret them as a full
   current-suite pass.
2. Review each affected behavior against the implementation and requirements:
   contributions and marginal shares; one/two-position maintenance and recovery;
   actual fees, exact allocation and reserves; current-owner claims, royalties,
   buyback, terminal return and canonical handoff; transaction preparation,
   canonical block evidence, gas/calldata and failure handling. Follow callbacks,
   state transitions and interactions across those boundaries.
3. Identify what a faulty implementation could do while the old or repaired
   test still passes. Fix confirmed code defects, obsolete expectations and weak
   verification. Use independent expected amounts, nonzero economic state,
   intended errors/stages, physical custody and complete rollback assertions.
   Corroborate controlled accounting models with focused actual-v4 checks.
4. Run new or genuinely affected cases only. Do not repeat the prior80 methods,
   unchanged full suites or long fuzz/invariant campaigns to increase counts.
   Keep discoveries, failures, selected-zero runs, corrections and source stages
   explicit. A dependency inventory is not runtime coverage or production proof.
5. Preserve all rights, permissions, operating limits, unrelated work and the
   four protected dirty files. No public transactions, deployment, sealing,
   existing-chain reset, service/site/signer/journal change or monitoring restart.
   Ask only for unresolved consequential product choices; routine corrections
   within established requirements should proceed.
6. Publish a behavior-oriented impact matrix, actual findings/fixes, finite
   verification and remaining coverage limits. Update the sole Todo, relevant
   operator/feature guidance and repository memory. Main only; verify exact
   staged/committed imports and local/remote revision before claiming published.
