# Payload5 consumer and unsigned-tool boundary

Baseline `06956fb22c55ad83d8d65186d6ab8988246995f0`; prepared18November2026.
This section owns offline consumers/tools only, not the royalty implementation,
gas qualification, normal build, operating configuration or release approval.

- Schema17/source10/canonicalV10 and code-storage FORMAT2 remain explicit.
  Omission/exact3 selects immutable payload3; exact4 selects immutable payload4;
  only exact5 selects the new source-owned payload5. Booleans, strings, unknown
  versions, missing new policy sections and mixed creation/data-part pins fail.
- The prior fresh payload4 template is archived byte-for-byte in
  `config/production.schema17.payload4.example.json`, SHA256
  `cc1061255416857aab34b6ccfe4c44b0281f6745fc142cda2440ea08a011692b`.
  Historical payload3/4 helpers, manifests and templates are never rewritten.
- Payload5 alone requires `royalty_read_policy`: version, policy address, raw
  balance-call gas, gas revision, computed fingerprint/scope, actual observation
  and review evidence. Unknowns remain null/blocked, never replaced by50000.
  Inventory gas/revision values are exact JSON integers; unsigned pre-seal ABI
  inputs remain canonical decimal strings, for example `"balanceGas":"50000"`.
- The new Policy getter is `royaltyBalanceGas() -> uint32`; reviewed bounds are
 10000..1000000. It isolates ERC20 balance reads during activation enrollment;
  ordinary sync, claims and canonical balance reads retain their existing paths.
  It is separate from the unchanged full royalty-sync allowance.
  The inherited `gasPolicy()` four-word ABI and `gasFingerprint()` computation
  remain intact. The setter increments that tuple's gas revision.
- The new read-policy fingerprint is explicitly OFFLINE:
  `keccak256(abi.encode(keccak256("ZZZ_ROYALTY_BALANCE_READ_POLICY_V1"), policy,
  balanceGas, gasRevision))`. No nonexistent on-chain getter is requested.
  Observation first authenticates the old tuple/fingerprint and reciprocal
  controller binding, then reads the cap at the same canonical anchor/budget.
  Failure clears stale positive observations; declarations are never adopted.
- Original twelve pre-seal setup families/order remain intact. An explicit
  optional top-level `royalty_balance_policy` request prepares a separate typed
  `setRoyaltyBalanceGas(uint32,bytes32)` call. Omission requests nothing; partial
  inputs block completion and keep calldata null. Complete inputs still provide
  no authority, live-state, submission, simulation, seal or operating approval.
  The actual current ABI must expose the getter/setter before this path is usable.
- Final payload5 pins may be produced only from the accepted actual current
  full normal build, with all100 current source bytes and all48 size gates
  authenticated through the unchanged strict deployment artifact reader.
  Proposed/experimental builds never populate final manifests.

Eleven new focused Python methods cover exact accepted creation/data parts,
historical identities, selector isolation, declared/observed cap and revision,
independent fingerprint encoding, real bounded same-anchor observer reads,
failed-read clearing, null/unapproved templates, exact optional calldata,
input rejection before artifact access, and actual required-read ABIs.
They were prepared but not executed at this initial source stage; the later
[consumer review](CONSUMER_REVIEW.md) records their actual source-scoped results.
The old
payload4 test helpers now select their explicit archived configuration/build;
the changed unknown-selector control uses6 because5 is newly supported.
No unchanged module is selected for execution.

Accounting changes must preserve exact scalar claim views, original-currency
claims, allocation events, opening/fault cohorts and per-NFT canonical rows.
`ROYALTY_SETTLEMENT_VERSION` remains4. Only fresh payload5 requires the separate
read-only `ROYALTY_ALLOCATION_VERSION=2` identity; old3/4 lack that getter.
The contribution20M envelope/full20% margin, defaults and one-million-gas sync
allowance are not changed by these consumers. A gas cap, currency capacity or
source-owned hash is not whole-workload or production qualification.
