# 20M contribution / 24M maintenance software qualification

This partition changes no production implementation, default, deployment,
installed configuration, service, site, signer or journal. It qualifies existing
software budget gates with new inputs. Production fees, providers and execution
are separate evidence; no unqualified fee fields are attested true.

## New checks, without unchanged test reruns

All **13 new Python methods** pass in one run. [Receipt](PYTHON.json),
[log](python.log), [test source](../../../tests_python/test_reviewed_gas_profiles_20_24.py).
The activation cases use the current accounting7 / Entry3 / execution-price1 /
LP-routing3 verifier fixture, then the real gas-review/configuration helpers.
This is a verifier/gas-helper boundary, not complete market/API inventory admission.

The 24M manual cases invoke the actual manual simulation/estimation function.
Keeper cases invoke actual submission coordination with injected transport,
readiness/authority seams and an inert mock signer. They cover both LP action
selectors, exact initial 24M simulation, smaller 25%-padded mock signing,
fee/day/price/padding refusal, provider refusal and original pending-record priority.
They do not establish real signer/host/authority/recovery qualification.

The normal Python runner discovers the new module. The dedicated keeper runner
adds that same mixed-profile module through one inventory-only line. Its
[AST proof](KEEPER_INVENTORY.json) verifies no other runner behavior changes;
the [full inventory](KEEPER_FULL_INVENTORY.json) selects951methods, including the
13new methods, while executing **zero** tests. That count is not951passes.

All **12 new Node checks** pass against unchanged website production modules.
[Results](BROWSER.json), [runner](browser-check.mjs), [direct inputs](browser-inputs.json),
[static local-import closure](browser-import-closure.json). Source10/execution1
checks ETH/ZZZ activation, growth and exact approval, backend/manifest cap mismatch,
padding, fees, provider refusal and unchanged claim-policy1. Historical source9
keeps its own LP2/profile identity while accepting its explicit 20M policy.

The runner extracts only fixture factories before the old programs' first test
registration; no unchanged Node test body is imported or run. Literal imports
still load the actual reviewed production modules. An initial pre-execution
guard incorrectly identified `RegExp.test(...)` as test registration. It stopped
before any case; the corrected guard then ran the 12 cases once. The
[precheck failure](BROWSER_PRECHECK_FAILURE.json) remains explicit. No EVM/compiler
or network request occurs in this partition's tests.

## Recorded actual contribution integration

[Four actual owner captures](ACTUAL_CONTRIBUTIONS.json) from the separate new
owned-Anvil campaign also pass the unchanged production `activation_trace.measure`,
`ActivationTransactions._gas_review` and `_gas` helpers. The
[offline reader](reconcile-recorded.py) accepts only exact recorded RPC replies;
it reruns no EVM operation and makes no network request.

| Controlled operation | Actual RPC estimate | Full20% review limit | Margin below20M |
| --- | ---: | ---: | ---: |
| ETH activation, local$100 |14,748,028|17,697,634|2,302,366|
| ETH growth, local$5 |13,616,039|16,339,247|3,660,753|
| ZZZ activation, local$100 |15,082,371|18,098,846|1,901,154|
| ZZZ growth, local$5 |13,929,079|16,714,895|3,285,105|

Each marginal deployed-LP/share result equals the captured producer result;
all four use accounting7/Entry3/execution-price1/LP-routing3 and the actual
recorded32M canonical block. These are controlled feed/market/owner cases, not
qualified real Robinhood asset prices, liquidity, max-state workload or complete
network fees. The isolated gas-helper settings use each original capture's
calculated local execution cost as a diagnostic bound; they grant no production
fee approval. Full `Projection`/configuration-inventory admission and hosted
worker operation are outside this replay. No claims or rights are inferred from
a gas-only success.

The six actual maintenance cases are recorded by the separate EVM campaign;
they are not relabeled as actual manual-service admission here. Their producer
did not capture the numbered-header request required by the manual helper, so
this partition preserves its separate injected manual gate checks rather than
fabricating a provider response. The offline reader's initial source-list typo
stopped before any case; [precheck record](REPLAY_PRECHECK_FAILURE.json). After
that correction, each contribution capture was reconciled once.

## Exact budget rules

| Path | Selected ceiling | Required padding | Largest estimate fitting ceiling |
| --- | ---: | ---: | ---: |
| Activation/growth schema2 |20,000,000|20%, rounded up|16,666,666|
| Keeper |24,000,000|25%, rounded up|19,200,000|
| Manual LP review |24,000,000|25%, rounded up|19,200,000|

The next estimated unit fails rather than clipping padding or increasing the
budget. The confirmed-block bound and all price/transaction/day/funding checks
remain. An observed synthetic `2^50` header does not raise the configured ceiling
and does not prove the actual network execution limit. Actual transaction and
provider parameters require their own current review.

The browser requires the backend's **configured 20M to equal
`manifest.limits.gas` exactly**. The effective block bound can be lower; that is
not permission to configure a different browser ceiling. Backend cap declarations
of 19M or 21M against a 20M manifest reject. `activation_policy_schema:2`,
`activation_sha256`, fee-review hash and existing runtime/read identities must
match. The gas-only change does not promote a source9 deployment into source10.

Claim transaction policy remains unchanged: policy1 still caps claims at12M
even when the manifest permits20M activation. Selecting claim-policy2 needs its
own matching backend/consumer review. Fresh source9/source10 stay unsigned and
never construct the unchanged shared signer.

Keeper `max_gas_limit` applies to **all enabled jobs in that loaded keeper
configuration**, not only rebalance/compound. Per-job economics, per-transaction
and daily spending guards remain. Manual LP uses its separately reviewed fee
policy. Source/quote/payout/optional-royalty-sync subcall budgets are not raised.
No gas setting grants authority or bypasses financial/on-chain safeguards.
The existing request-work limits also remain: default25-second request budget,
30-second worker lifetime, 1MiB worker result and an8,192-frame/depth64 activation
trace limit. A20M/24M gas review does not qualify throughput, raise these limits
or guarantee that a remote provider completes full preparation within them.

## Non-live candidate profiles

[profiles.template.json](profiles.template.json) gives exact gas/schema fields
and required matching overlay paths. It is **not a complete runnable service
configuration**. Fee caps/review hashes, identities and provider acceptance are
unresolved rather than invented. `estimate_includes_all_fees:false`, null fee
ceilings and `receipt_fee_policy:unverified` intentionally prevent live adoption.

Merge only explicit fields into a separately reviewed full configuration; never
replace a whole `limits` or `fee_policy` object while dropping other controls.
The activation JSON is the complete `ActivationConfig` supplied through
`--activation-config`; its root `schema:2` and fee fields are not a claim-policy
file. Mint/claim `TransactionConfig` is a separate `--transaction-config` with
its own chain/projection identity and stays unchanged. Production worker clients
require separate activation and mint/claim listeners; do not combine their
configurations. The read/deployment inventory is a third, separately pinned
input. Manual LP policy and keeper configuration also have distinct loaders.
Retain price, fee, value, loss, timing, ownership, callback, balance, route, NAV,
idle, work-budget and pending-recovery checks. No global 12M default changes.
These are operator software settings after sealing, not governance-contract calls.

A later rollout requires pending-first reconciliation, original journals, new
configuration hashes, matching consumers, complete fee review and controlled
restart/dry-run. Do not edit a saved pending operation to make it fit a new policy.
Current public null configurations, live sites, Anvil8902 and the paused heartbeat
remain unchanged.

Reproduce only these new checks from the contract root:

```text
python -m unittest -v tests_python.test_reviewed_gas_profiles_20_24
node reports/gas-profiles-20261113/backend/browser-check.mjs WEBSITE_CHECKOUT NEW_OWNED_SCRATCH_DIRECTORY
python reports/gas-profiles-20261113/backend/reconcile-recorded.py --output NEW_OUTPUT ACTUAL_CAPTURE_DIRECTORY...
```

The Node runner requires byte-matching pinned inputs and an unused scratch path.
It accepts an optional fourth argument naming a JSON array of exact new case
names, allowing a failed changed case to be rechecked without rerunning passes.
No full unchanged browser/backend/Solidity suite is requested here.
