# Work handoff

Reviewed5November2026. Pre-settlement2 task baseline main
`bce897c480cd7df67e4936d278d51908d3d7885f`; verify actual local/remote Git heads.
Read [instructions](../AGENTS.md), [context](../PROJECT_CONTEXT.md),
[README](../README.md), [sole Todo](../TODO.md),
[Operator manual](OPERATOR_MANUAL.md) and [profile](POSITION_V6.md).
**Production NOT APPROVED.** Publication is not deployment or rollout.

## Current task result

User selected original-currency royalties. Fresh settlement2/recovery2 removes
the royalty converter and ledger swap/binding/approval entrypoints. Governance
allocateUnallocated(asset,amount,reviewHash) changes only admitted orphaned units
to liabilities in the SAME currency at active weights. No earned/deferred/fraction
backing, LP conversion, principal, weight or current-owner right is changed.

Fresh schema11 has18helpers; reporting3/converter:null and explicit keeper
royalty_settlement_version2/no royalty conversion authenticate the new boundary.
Legacy schemas/events/conversion tests stay separate. This is a new royalty
runtime/storage layout, never an upgrade or relabeled journal. Source website
claims/displays raw royalty currencies; public signing and actual sites unchanged.

Current short tables cover797functions/36constructors/12receivers with845rows.
[Verification](../reports/royalties-in-kind-20261105/VERIFICATION.md) records
normal42gates, static466contexts and focused EVM/Python/website checks. Initial
fixture failures remain archived; no security guard was relaxed.

## Verify documentation without repeating contract suites

```text
python scripts/generate-function-reference.py --check
python scripts/generate-operator-reference.py --check
python scripts/sync-project-todo.py --check
```

For ABI/behavior changes first regenerate the source-bound ABI/notes, review all
changed examples/roles/tuple/value semantics, then regenerate the tables. Never
re-pin automatically just to pass. The source-bound [full reference](CONTRACT_FUNCTIONS.md)
owns exact outputs/permissions; the manual owns procedures/recovery/reversal.
Inspect actual IDs: NFT_ID is not BUCKET_ID, and portfolioFingerprint takes the
main LP_TOKEN_ID. Contribution policy, mint policy and offline reviewHash differ.

## Exact source evidence and remaining work

[Royalty verification](../reports/royalties-in-kind-20261105/VERIFICATION.md) owns the
current42normal gates/466strict static contexts and58selected EVM methods;
Python stages overlap. Current source is accounting6/custody5/portfolio2/direct
Entry3 plus royalty settlement2/recovery2; compatible parked canonicalV6 wire is not runtime identity.
Earlier [reports](../reports/README.md) retain their original pins/failures/scope.
Documentation work does not rerun unchanged Solidity suites or establish CI/live
provider/gas/hosting/marketplace or independent approval.

Real feeds/routes/VRF/authorities, OpenSea primary integration, source8 matching
site/services, metadata, history longevity/restore, operating economics and
independent audit/remediation remain open under the [roadmap](ROADMAP.md) and sole
Todo. Do not revive retired bridges/creator inboxes/third contribution inputs or
external custody-address exits. Existing earned/deferred royalties remain distinct
from current-weight unallocated recovery. Review actual admitted royalty currencies before seal; no royalty converter is bound. LP conversion is separate. Source publication changes no worker.

## Preserve actual environments and unrelated work

Anvil8902, minted NFTs/LP/balances/journals and website overlays remain unchanged.
Popldemo is simulation; separately served poplint remains current3/unconfigured,
not the new source8/accounting6consumer. Public DEPLOYMENT null; signing Anvil-only;
heartbeat remains user-paused. No public transaction, deployment/seal, reset,
service/site restart or journal conversion was authorized.

External evidence root:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9`.
`operator-docs-20261105/BASELINE.json` archives109original maintained files, full
source/report pins and the four protected dirty files below. Earlier royalty and
manual/authority evidence remains in its original linked directories. Preserve
unrelated untracked drafts; stage only owned changes and verify index/HEAD Python
publication closure before claiming published.

| Protected tracked file | Original SHA256 |
| --- | --- |
| `reports/source-checks.json` | `049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4` |
| `scripts/run-fork-checks.py` | `875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b` |
| `tests_python/test_fork_runner.py` | `6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9` |
| `tests_python/test_frontend_history.py` | `361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb` |
