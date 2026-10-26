# Keeper/LP audit verification

## Final Python scope

[Maintained runner](../../scripts/run-keeper-tests.py) selects21modules and only
their defined TestCase classes, deduplicates method IDs and pins local Python
inputs before/after, including lazy fixture imports. Input inventory is not a
claim that every branch/module was exercised. The workflow now uses this runner
and includes native/conversion/example/new regressions omitted from its old list.
An edited workflow is not an executed/passing GitHub Actions run.

[Final result](affected-suite.json):359executed,354passed,5Unix-only skips,
zero failures/errors; 23.688s; 145input pins unchanged.
The5skips concern supported Unix ownership/symlink/permission/locking behavior;
Windows does not qualify production keeper operation. Thirteen new portable
methods pass (6health/5conversion/2rehearsal), plus one new Unix-only permissions
method not executed here. Fresh full-repository or real-service approval is not
inferred. Existing loopback HTTP and synthetic RPC/SQLite fixtures are not public
provider tests. Actual cast --help inspection does not sign.

## Negative controls and harness repairs

- Health6-method before scope: matching control passes,10mismatch assertions fail
  across5methods. After6new+13existingOps methods pass. The final aggregate includes
  them; do not sum those overlapping counts. [Operations evidence](operations/operations-evidence.json).
- Conversion5-method before scope:18malformed flag assertion failures across2methods,
  three positive methods already pass. Same methods after5pass across three profiles
  and both ledgers. [Reward review](rewards/REVIEW.md).
- Range existing negative control panics on obsolete enum conversion. Final9methods
  pass, one with1,000fuzz runs; fresh265-input AST typecheck changes only that test.
  [Core results](core/after-summary.json), [original](core/before-summary.json).
- Real disposable Lab builder originally lacks current version fields and retains
  a retired job option:2methods fail before and pass after. [Before](rehearsal/profile-before.log),
  [after](rehearsal/profile-after.log).
- Old/new test-only KeeperVenue separately compiles with actual solc0.8.26, deploys
  only on fresh owned loopback Anvil and verifies deployed runtime equals compiled
  runtime. Before4current checks fail; after version3/fee1/8words/native-zero and
  real Keeper reader pass. [Before](rehearsal/venue-before.json), [after](rehearsal/venue-after.json).
  No existing chain, real LP, external key or production contracts are involved.

The first358-method aggregate is preserved under [attempt1](regression-attempt1/affected-suite.json).
It has two failures, five error records and two skips: one preparation fixture
mutated config after Keeper construction, three unsupported Unix methods and a
redirect test's unread POST caused three Windows connection-abort subcase errors.
The source-inventory also mistakenly treated a later lazy import as file mutation;
actual earnings.py was unchanged. The repaired maintained runner captures those
paths before execution. No production health check was weakened; fixture setup
now finishes before construction. The redirect server drains/witnesses each request
and retains exact failure/no-target assertions. Portable atomic roundtrip remains;
the actual0600 assertion is stronger on Unix and explicitly skipped on Windows.
The rerun is justified by these changed fixtures/runner, not a repeated clean suite.

## Reuse and unavailable checks

Production44Solidity,31normal dependencies and four build inputs match the prior
normal/static source pins; unchanged contract size/static suites were not rerun.
No ABI/function reference change; its consistency is checked separately.
Fee, nonce, ownership, LP, authority and allocation rules remain unchanged.

This Windows host reports WSL unavailable. The Unix process-crash/systemd/private
file campaign is prepared but **not executed here**; the workflow owns its next
supported-host run. Historical operating reports do not verify the changed fixture.
No actual provider, new operating service, realistic strategy/load/gas or independent
audit qualification is claimed. Production remains NOT APPROVED.
