# Consumer/build test impact: current versus historical scope

This source inspection does not run old suites. Only the eleven new payload4
methods and the six specifically changed methods below are planned for final
Python execution after the accepted new default is registered.

| Area | Source-backed finding | Correction/scope |
| --- | --- | --- |
| Current deployment default | Two methods hardcoded `seal-boundaries-20261117` as today's default. | Use `D.DEFAULT_BUILD_PROFILE` for current preparation. Keep the old seal family explicitly registered and hash-checked. |
| Access constructor size | Current-graph method fixed full initcode at48,377 bytes. Royalty creation bytes are embedded transitively. | Verify actual current creation length plus an independent96-byte ABI encoding of exactly three address inputs, retaining normal49,152 limit. Preserve48,377 only in explicit historical seal evidence. |
| Schema16/payload3 fixture | `test_exact_lp_inventory.config()` read the moving current example while the module expected schema16, V9 and fixed payload3. This was already stale before payload4. | Read `production.schema16.example.json` and use its historical module gate. Do not change payload3 hashes/source counts to new values. |
| Historical CLI dispatch | The same module still expected default CLI schema16 and automatic schema16 observation, although current CLI already requires17. | Assert current17 rejects old15 and require `--historical-consistency` for both schema16 and15 observer paths. No automatic legacy fallback. |
| Schema14/payload2 | `test_factory_code_profile` already reads its explicit schema14 archive. | No change; its old fixed counts/bytes are deliberate historical assertions. |
| Pre-seal and deployment sequence | Current preparations use `D.DEFAULT_BUILD_PROFILE` dynamically and verify actual trusted ABIs. | No historical relabel or mass rerun needed just for a new family name. The new final checks cover current payload/default composition. |
| Original construction evidence | `deployment_legacy_fixture` constructs an exact old-source temporary checkout and explicitly selects the manual-reference family. | Keep old receipts, compiler bytes and constructor expectations exact; current source must still reject an old build without a matching checkout. |
| Website/source10 | Public getter/event/economic/canonical semantics are unchanged by the internal royalty algorithm. | Fresh actual runtime pins remain mandatory; no old runtime/configuration/evidence is rewritten or automatically adopted. |

The three affected build methods are:

- `test_default_planner_accepts_current_metadata_build_and_tags_identity`
- `test_seal_fix_keeps_previous_objects_historical_without_automatic_fallback`
- `test_current_complete_graph_has_exact_objects_and_original_size_limits`

The three changed historical-body methods are:

- `test_current_template_explicit7_v9_has_no_observations_or_approval`
- `test_old15_cannot_enter_current_gate_or_observer`
- `test_cli_requires_explicit_historical_selector_for_schema16_and15`

The historical fixture correction also restores intended inputs for other
schema16 methods; those unchanged bodies are NOT claimed freshly executed.
No schema14/F2 source is changed, and no previous raw report is relabelled.

The old positive-node differential test is also deliberately retained: it uses
only positive `addRange`, so exact raw-node equivalence can still hold there.
It does not establish raw-node equivalence for the new complementary credit
representation. New per-ticket/canonical integration tests cover that behavior
without replacing a useful older assertion with a weaker one.
