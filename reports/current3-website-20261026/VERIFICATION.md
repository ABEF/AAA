# Current3 website integration verification

Campaign began 2026-10-26; review concluded 2026-10-27. This source-only integration adds an explicit website
schema3 profile matching current accounting3/direct governance2/fee1/localV4.
It preserves schema1/native2 readers, the Anvil-only signer, existing journals
and the null public demo deployment configuration. No production Solidity changed.

The one final affected Node selection records **451 passes**, zero failures or
skips, including **46 new methods**. Earlier selections overlap and are not
additional coverage. Six fixtures are exported from real Python Projection,
ActivationTransactions and Transactions code: ETH activation/growth, fixed-ZZZ
activation/growth, exact ZZZ approval and combined ETH claim. RPC, market prices,
venue, authority and state are synthetic; this is not actual provider acceptance.
The intermediate collection-fixture ordinal error is retained, with no guard
relaxation. See the adjacent machine-readable receipts and source bindings.

Checks cover current manifest/runtime/module/domain/fixed-ZZZ identity, canonical
provenance, current custody/activation/rarity/share/unavailable-state invariants,
typed calldata and contribution cap, exact approvals, claims, holdings/history
aggregation, and historical profile compatibility in the selected scope.

The separate integration shell/build is verified independently in its own
receipt; those checks must not be added to the451-method count by implication.
Public poplint has no approved current deployment/API configured and must show
unconfigured, never demo holdings. Static serving/TLS checks and publication
receipts are operating observations, not provider, wallet, marketplace or gas
qualification.

[Current profile](../../docs/CURRENT_WEBSITE_PROFILE.md) and
[environment map](../../docs/SITE_ENVIRONMENTS.md) describe setup and separation.
Actual current contracts/API, independent feeds/routes, VRF, authorities, OpenSea,
complete history, operating rehearsals and independent audit remain open.
No new public transaction or contract deployment is authorized by this report.

[ABI bindings](ABI_BINDINGS.json) independently recompute33selectors, verify
all signatures in the compiler-bound catalogue, six controller module IDs and
the canonical V4 schema label. This is separate source validation, not another
execution-test count. [Serving and rollout](DEPLOYMENT.md) record the actual site.
