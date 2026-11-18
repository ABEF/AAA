# Actual placement-boundary regressions

All five NEW methods in `ManagerPlacementProofReuse20261118Test` passed against
the frozen C07 source, before the later C08 canonical-prefund correction. The
existing inherited methods were not selected. C08 does not change their Manager,
Pricing, admission or ordinary activation paths; no result is relabelled as a new
C08 execution. The current full-flow qualification is recorded separately.
Actual installed v4 core, StateViews and PositionManager are used; MockAccess,
local admission/ETH publications, Permit2 and VRF remain controlled seams.

| Method purpose | Non-vacuous result |
| --- | --- |
| Mint proof | Nonzero funded position, exact owner/bounds/refund and one explicit full Oracle validation. Source order independently places that proof before mutable Portfolio recording; call count alone does not prove ordering. |
| Public callback proof | Actual nonzero token refund changes a healthy same-value ETH round; public Manager getter rejects it, then the callback restores the round and the funded increase succeeds. |
| Source-fault rollback | Persistent round mutation during refund rejects the increase, restores LP/core/balances/allowance/prefund/source state, and permits a healthy retry. |
| Physical-L rollback | A separately funded, explicitly owner-approved actor actually increases the same physical position by1 during refund. Exact-L checks reject it and restore both parties' funding; a healthy retry succeeds. This does not assert that unapproved outsiders can mutate a Vault-owned LP NFT. |
| Entry/admission/phase | Zero-amount value skips an unknown asset; disabled admission, mismatched decimal policy, changed token runtime and subminimum value reject before funding. Unauthorized/out-of-phase Pricing finish calls reject. A source fault during actual child approval reset rolls back NFT/share/reward state; healthy activation then succeeds. |

RESULT binds all compiled dependency hashes to pinned-tool metadata and the
before/after source bracket. Configuration and the four protected files remain
unchanged. Five outcomes took373.625seconds including compilation. No default,
gas budget or production size gate was raised. These are funded behavior checks,
not the launch-scale20M profile qualification or new emergency-mask execution.
The original raw JSON remains outside Git, bound by EVIDENCE.json; compact exact
outcomes are in FORGE_COMPACT.json.
