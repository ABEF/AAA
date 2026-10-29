# Consolidated backend scope

Six reproduced source/evidence issues are repaired: filtered transaction provenance, final inventory confirmation depth, fixed legacy/type1 receipt prices, versioned current review-bundle guidance, strict durable-state JSON, and selected-pool RPC/slot0 consistency. No financial policy, custody right or signing authority changed.

Exact test-identity union: **96 distinct methods;92 passed,4 explicit Unix-only skips;41 new methods.** The original scoped runs remain separate: backend59=59pass; state23=19pass+4skip; pool14=14pass. Iterative runs and intentional guard-removal failures are not additional passes. No unchanged test rerun was performed for this consolidation. `consolidated.json` contains every method identity/result/scope, exact skip reasons, current implementation/test hashes and original receipt hashes.

The four skipped identities are StateTests.test_atomic_state_repairs_existing_unix_permissions, test_concurrent_lock_rejected, test_lock_released, and test_predictable_temp_symlink_cannot_overwrite_another_file. Windows results do not qualify Unix filesystem permissions/fcntl/systemd or real operation.

Manual body review closed the previously partial production_observer/production_v2/function_reference/review_bundle slice, with actual cases and pins. Additional static wrapper review covered observation/validation/holder inventory/review export/reference generation/Slither review and the isolated ingress rehearsal. The selected-pool wrapper gap was reproduced and repaired; no other concrete repair was justified in that wrapper slice. Static symbols and body reads are not execution counts or independent audit approval.

Earlier backend59 remains historical to its source/test scope; strict state/main-config changes followed separately. All listed receipt file hashes currently match their recorded paths; this is not a complete transitive dependency attestation. No service, signer/action, operating journal, Anvil, website, deployment or public transaction was changed. Real providers/feeds/routes/VRF/authorities/gas/hosting and independent release approval remain open.
