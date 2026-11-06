# Main/residual verification and limits

6 November 2026. Baseline main `5d70b4b5a3ade066ec46a6dd81ed172cf50bc16e`.
Production NOT APPROVED. [Review](REVIEW.md), [lifecycle matrix](LIFECYCLE.md)
and [evidence index](evidence.json) describe the scope and file hashes.

## New verification

| Evidence | Actual result and scope |
| --- | --- |
| [Services result](services/focused-final.json) | **66 distinct module-owned Python methods passed, zero skips**, including 13 new methods. Imported fixture test classes were excluded and exact test IDs deduplicated. The result records imported source hashes before/after execution. |
| [Pre-fix negatives](services/integrity-before.log) | Three rejection assertions failed because the old reader accepted contradictory physical principal, a wrong nonzero stable identity, or a non-contained residual. These are retained failures, not passing checks. |
| [Fixture transition](services/affected-first.log) | Initial affected run included imported duplicates and five subtest failures in two stale arbitrary-value fixture methods. Fixtures were corrected to actual geometry/amounts; guards were not weakened. Do not add that run's count to 66. |
| [Actual-core lifecycle stage](accounting/evm-first/status.json) | **Three new selected EVM cases passed**: mode-ON destination movement; parked resume followed by activation/main-only growth and OFF merge; infeasible destination rollback preserving both source legs, shares, liabilities and reservations. |
| [Separate producer stage](accounting/evm-producer-corrected/status.json) | **One additional selected EVM case passed**, producing raw actual PositionManager/Manager outputs for an unfilled residual and the same residual after a real v4 trade makes it mixed. The earlier three test bodies were unchanged and were not rerun. |
| [Actual vectors](actual-physical-vectors.json) and [consumer result](producer-consumer.log) | **One new independent Python method passed**. It decodes both 25-word ABI tuples, recomputes pool identity, principal for each leg and both fingerprints, and agrees with the actual EVM outputs. The producer/exporter did not calculate Python expected amounts or hashes. |

The three lifecycle cases ran at their explicitly captured test source stage;
the later producer adds a new method without changing their bodies. The
[accounting review](accounting/FINAL_ACCOUNTING_REVIEW.json) and
[producer review](accounting/FINAL_PRODUCER_REVIEW.json) retain their separate
test hashes. Final `test/OptionalPortfolioCore.t.sol` raw SHA256 is
`aed5e0511e3abb0dee655d90f27bd20d8920e15e5453bc8a5dedfe37d2c609c2`.

A final independent implementation review found no additional material defect
within this scope. Its only follow-up corrects the neutral helper's module
docstring to say it needs no RPC or USD feeds: physical sqrt price is an input.
The [comment-only record](services/comment-only-follow-up.json) proves identical
executable AST and preserves both source hashes; unchanged tests were not rerun.

Retained setup failures are not concealed or counted: the initial lifecycle
ABI check attempted a private/unavailable getter; the initial producer ABI check
needed `PositionInfo.unwrap`. Corrected closed-source typechecks cover 188 sources.
An end-anchored producer selector exited zero with **zero selected tests**; only
the corrected selector establishes the one producer success. See the original
stage records under [accounting](accounting/FINAL_PRODUCER_REVIEW.json).

## Exact unchanged evidence reuse

Production Solidity was not modified. The [reuse record](solidity-reuse.json)
checks all **53 production and 31 dependency source hashes** plus the recorded
build inputs. The existing factory campaign's **44 normal compiler-object gates
and two actual carrier runtime/initcode gates**, and **489 strict static records**,
are reused only within their original scope. No compiler-size or analyzer rerun
is claimed. Historical reports retain their original bytes and source identity.

The new isolated Forge source-behavior tests use royalty creation artifact
`0xee61b40298c3a075124538647c141c5d4a92a761fabc17b61960f883d42eb3ee`.
They are not relabelled as the separately recorded normal artifact family.
The prior factory report explains the source-equivalent compiler-family
distinction; this campaign does not replace normal deployability evidence.

## What these checks do not establish

- The actual-v4 fixture uses real local core/periphery but mock authority,
  correlated USD feeds, Registry admission, test tokens, VRF and Permit2. Its
  fixture code-size override is 1,000,000; it is not a normal deployment gate.
- Selected scenarios and deterministic reader cases are finite evidence, not
  exhaustive proof of every market path or all possible inputs. No full suite,
  independent security audit, public CI result, target-chain gas benchmark,
  actual provider qualification or operating uptime is asserted.
- Source inspection found no ordinary two-leg custody/accounting defect in the
  reviewed conventional-token/hookless model. Late collect-to-burn fee generation
  under malicious/upgraded token or compromised periphery callbacks remains a
  dependency/accounting boundary, described in the [review](REVIEW.md).
- Same-block consistency checks can reject conflicting views; they cannot prove
  an entirely fabricated RPC state honest. USD/reference outages remain separate
  from physical custody and raw reward claims.
- No website JavaScript/configuration, signer, service, existing Anvil state,
  journal, wallet funds, deployment, public transaction or paused heartbeat was
  changed. Website documentation changes do not upgrade the served current3
  integration. Checkpoint semantic sources are unchanged; no checkpoint rebuild
  or adoption was performed or required by this physical-read-only correction.

The [preservation record](preservation.json) binds the protected dirty files,
unchanged production sources, historical reports and website source boundary.
The [documentation checks](documentation-checks.json) cover the maintained Todo,
function reference, all 869 operator example rows and local Markdown targets.
The [exact staged Python closure](publication-index.json) excludes untracked and
unstaged code. Used helpers in the protected dirty frontend fixture are
[AST-identical to their published versions](protected-fixture-compatibility.json);
its unrelated additional methods were not selected or staged.
Final committed/remote heads and the repeated committed-blob publication check
are recorded externally at publication; source publication is not operating approval.
