# Total activation/growth default:3%

Baseline main `793c8e026b1d3fc307256fde2f6d4e82c4efec37`.
The user explicitly selected **TOTAL activation/growth loss only:3%**.
This is a future execution-policy change, not a refactor or deployment.
**Production NOT APPROVED.**

## Approved change and unchanged controls

`ZZZMigrationBudget`'s fresh constructor initializer changes
`contributionLossBps=200` to `300`. This is the only production Solidity edit.
The fresh schema17 template records the same intended300 value in its Budget
bindings and execution-loss policy. Actual addresses/observations, per-pool
spot/slippage choices and approval flags remain unset/unqualified.

| Control | Result |
| --- | --- |
| Total activation/growth contribution allowance | Default300bps; at least97% of conservative upper input becomes actual marginal deployed LP |
| Exact100USD /5USD upper-valued input | At least97USD /4.85USD added LP respectively; exact integer rounding retained |
| Idle, incumbent LP/compound, rewards or donations | Cannot satisfy that added-LP floor |
| Pool per-swap output and retained-value floors | Unchanged; can require stronger execution than the new total cap |
| Pool/reference deviation | Unchanged; production value remains unselected, not copied from the1% rehearsal |
| Additional loss after directional trading fees | Default1%, unchanged |
| LP reward conversion | Default1%, unchanged |
| Ordinary maintenance/migration | Default3%, unchanged |
| Two-source price agreement | Intended3%, unchanged and economically distinct from contribution loss |
| Governance hard ceilings, caller minima and gas |10%, stronger signed/reviewed limits and separate gas remain |

For upper-input USD18 integer `U` and cap `C`, required marginal LP is
`U - floor(U*C/10000)`, equivalent to rounding the retained fraction upward.
A wide source-price spread, stronger pool NET floor, actual input/output limits
or unavailable depth can still reject an operation. A3% total allowance does
not make every request executable or authorize a partial successful activation.

## Existing state, reviews and ownership

Source publication does not change any existing Budget's stored cap. On an
existing matching deployment, an authorized governance change would need the
actual `setLossLimits(300,CURRENT_MAINTENANCE_BPS)` call; no call was submitted.
Read and preserve maintenance, verify events/getters and prepare new reviews.

A saved caller maximum200 remains200. Entry rejects a governed300 cap before
pulling input rather than widening that review. Current preparation already
reads the on-chain getter dynamically; no consumer implementation fallback,
signer, running config, website, journal or existing Anvil was changed.

NFT ownership/shares, funded earned rights, allocation splits, principal custody,
callback authentication, rollback and terminal holder-return rules are unchanged.
Canonical peers must still match their actual policy VALUES before a handoff;
the new default does not rewrite predecessor configuration or import old source
state under a new label. ABI/storage/capability versions remain the same, while
exact raw source/runtime/artifact pins must be rebound for a fresh release.

## Verification and maintenance

The [verification record](VERIFICATION.md) separates focused current300 tests
from intentionally governed100/200 scenarios and old actual-trace evidence.
Normal90-source compilation,47 normal gates and both Factory-data gates pass.
ABI/storage remain equal; all64 deployed object bodies match after removing only
their exact compiler CBOR tails. The approved state initializer differs, and
Budget creation grows one byte. Metadata/raw runtime hashes change; existing
runtime pins are not re-labelled. Royalty creation payload/data parts are exact
unchanged. Vault runtime headroom remains32 bytes.

Actual static analysis retains558 detector records:11 contexts individually
reassessed and547 unique exact referenced-source reuses. The strict CI default
points to this source-bound record; matching rules were not changed.

Current guides, constructor template, operator examples, feature/release
references, Todo and repository memory now use3%/97%. Explicit caller200 examples
and immutable historical reports retain their original narrower scope. Operator
guidance describes the exact existing setter and how to preserve other limits;
no new function, role, withdrawal path, source currency or migration mode is added.

The earlier [actual-market campaign](../market-qualification-20261109/REVIEW.md)
used a recorded2% total allowance plus1% spot and2% swap guards. Those original
receipts/traces remain unchanged. This default-only change does not remove the
spot/swap/reverse-fill blockers, qualify independent ETH/ZZZ feeds or establish
successful market execution. No unchanged market fork or broad contract suite
was repeated to imply otherwise. Actual providers/routes, operating settings,
wallets, target gas and independent audit/remediation remain open in the
[sole Todo](../../TODO.md).
