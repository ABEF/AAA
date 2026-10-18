# Frontend lifecycle verification - 2026-10-18

**Development evidence, not production approval.** Production Solidity, the
website and existing staging are unchanged. No public transactions were submitted.

| Check | Result | Scope |
| --- | --- | --- |
| [Publication snapshot](publication-tests.json), [case log](publication-tests.log) | 74 passed, zero failures/errors/skips | Exact intended published read API and tests; lifecycle, HTTP, real local sqlite/indexer replay and existing API/history regressions |
| [Existing compiler ABI bindings](abi-check.json) | 15 getters/selectors checked; 13 production source identities match | Controller, coordinator, Vault and Vault companion; no new compile or Solidity test run |
| Earlier working-tree compatibility run | 112 passed | Also included the preserved unpublished optional transaction drafts; predates the final importing-origin display refinement and is not the final publication receipt |

The published API requires eight reviewed runtime/address pins and configuration
schema 2. All lifecycle/identity reads use the same confirmed EIP-1898 block hash
as balances. Tests exercise operating, preparation, pause, settlement/export,
abort, import, retirement and cancelled states; stale abort destinations; wrong
code/controller/helper bindings; malformed or unavailable getters; missing source
or destination; unknown phases; reorgs/depth loss; sanitized HTTP failures; and
explicit unavailable successor lifetime totals despite nonzero current history.

The final snapshot run retains the existing real local indexer's ownership and
claim-history regressions. It does not connect to a live PoPL deployment, hosted
provider, browser wallet or marketplace. Pinning current code is not independent
review of a destination, and confirmation depth is not a finality proof.

Internal review found two distinctions worth preserving:

- Restored aborts retain a stale destination in the coordinator. Only a retired
  source advertises a successor; operating sources do not redirect to that address.
- An inert importer initially exposes its constructor origin, then partial
  imported state. Importing/cancelled origins are unavailable until activation,
  rather than labelled as the activated collection identity.

The initial 110-case working-tree run had one test-fixture error: its token-outage
fixture also removed immutable controller/owner getters. The fixture now removes
only financial/price reads, retaining mandatory deployment authentication. The
API was not relaxed to ignore missing bindings. Later working-tree and snapshot
checks pass. Diagnostic logs and original pre-edit drafts remain outside Git in
the task's `api-lifecycle-20261018` artifact directory.

Full predecessor-chain authentication/replay, live consumers, external operating
qualification and independent review remain in the [read API task](../../TODO.md#task-read-api).
The saved unsigned POST draft remains outside this publication. Source hashes in
the snapshot receipt identify precisely what was checked; unrelated local drafts
must not be included or represented as published by this report.
