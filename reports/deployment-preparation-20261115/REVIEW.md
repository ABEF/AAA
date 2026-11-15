# Offline deployment preparation review

Scope: add a bounded, unsigned construction planner for the fresh
schema17/mint2/canonicalV10/execution-price1/LP-routing3 candidate. Baseline:
`ecb9dce6902c70c167e9d7e2ac11c7c52c7cb843`. This is a Python tooling/documentation
change, not a contract, deployment or release approval.

## Changes and review boundaries

The planner reuses the exact accepted
[normal build](../manual-reference-swap-fix-20261115/build/ARTIFACTS.json).
It distinguishes25 explicit constructions,12 internally created contracts and
2 inert carriers, rather than treating every ABI constructor as an independent
deployment. Exact resolvable arguments are appended to creation code; unresolved
values stay explicit. Both original byte limits remain in force. Royalty code
carriers are checked using their actual returned data runtime.

Planned public addresses are unverified assignments, not CREATE predictions.
Permissionless factories can have interleaved calls, so royalty ledger and
ActivationAssets addresses remain getter-discovered. Runtime template hashes
are not immutable-specific deployed pins. The binding checklist accounts for
Policy-before-consumers, bound-Vault-before-VaultCanonical, all16 Access module
IDs, the fixed ZZZ identity and separate current-release mint/converter setup.

The tool has no RPC, key handling, signer, broadcast, nonce reservation or seal
call. Every plan remains not ready for submission and not production approved.
No source label or evidence reference can approve its own actual deployment.

## Verification

**21 new unit methods pass; one additional method is skipped** because this
Windows account cannot create symlinks. Existing-output preservation, exclusive
publication and uncertain-publication checks pass separately. The22 unique
methods run across three non-overlapping successful stages; only the new sample
drift method runs after adding it. [The AST delta](TEST_SAMPLE_DELTA.json) proves
the preceding21 methods/helpers are unchanged. No old suite is rerun.

The [initial setup failure](checks/focused-first/RESULT.json) and log are retained:
the first loader incorrectly applied strict user-number parsing to a trusted
compiler size report's elapsed-time float. The correction permits that pinned
metadata only; constructor input numbers remain strict. The corrected first
method,20 remaining methods and sample-only method retain exact source stages
under [checks](checks). Results are summarized in [VERIFICATION.json](VERIFICATION.json).

The [independent encoding review](INDEPENDENT_ENCODING_REVIEW.json) checks all39
instance constructor shapes/arguments/sizes,15 getter ABIs and16 module binding
dependencies. Seven offline Cast encodings, including UTF-8 NFT metadata, match.
Two actual script-entry CLI cases return0 for complete offline input and2 for a
blocked preview; neither authorizes submission. These checks overlap the unit
workflows and are not additional product features. The original local-path
[review helper](independent_encoding_review.py.txt) is retained as source evidence,
not an operational deployment script. Its source/cast/CLI hashes are recorded.

The review retains the existing24,576 runtime /49,152 full-initcode limits.
Oracle is24,573 runtime and49,073 full initcode (3/79 bytes remaining).
Vault32 and Manager101 runtime-byte margins are unchanged. Actual inert carrier
runtimes are24,576/952 bytes; their full initcodes are25,095/1,479. Incomplete
address discovery prevents exact Entry/ClaimRouter argument bytes, while their
fixed96-byte argument lengths and size gates remain provable. None of these
offline checks executes a constructor or establishes a deployed runtime hash.

[Build reuse](REUSED_BUILD.json) authenticates100 exact current source pins and
the original48 normal gates. All61 Solidity sources and the four unrelated dirty
files remain unchanged. Compiler, Solidity/browser/old Python suites, static
analyzer and public RPC were not rerun. The tool adds no runtime bytecode,
financial-policy change, signer or service capability. Sites, existing Anvil,
journals and the user-paused heartbeat remain unchanged; no deployment or sealing
occurred. [Current tool hashes](SOURCE_SHA256.json) identify the published source.

## Documentation and task status

The [operator procedure](../../docs/DEPLOYMENT_PREPARATION.md) explains typed
inputs, CLI exit codes, hashes, missing data, bootstrap authority, all binding
stages and the pre-seal boundary. The central ledger/generated Todo, feature
reference, address inventory, read-only preflight, roadmap, release record and
repository context are aligned. The local tooling milestone is complete; actual
release qualification is not. Existing reports and deployed profiles retain
their original scope.

A separate initial isolated test-discovery command loaded/executed zero tests;
[the runner note](TEST_RUNNER_NOTE.json) explains its explicit-path correction.
It is not a test pass or rerun.

## Still required

Actual public role/bootstrap addresses, metadata content, live dependency code
and controls, independently qualified prices/routes, SeaDrop onboarding/settings,
VRF subscription/consumers/funding, creation address/nonce/receipt reconciliation,
constructor execution, target deployment gas/complete fees, deployed runtime and
reciprocal bindings, hosting/recovery and independent audit remain open.
The parent deployment qualification task therefore stays in progress.

See the [tool procedure](../../docs/DEPLOYMENT_PREPARATION.md),
[operator guide](../../docs/OPERATOR_MANUAL.md#offline-deployment-preparation) and
[sole Todo](../../TODO.md#task-deployment-initcode). Production is **NOT APPROVED**.
