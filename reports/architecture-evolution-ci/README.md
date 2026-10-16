# Published fork-runner inventory expectation repair

2026-10-17. Ubuntu [run 38976039899](https://github.com/ABEF/AAA/actions/runs/38976039899)
on `4fbd4c0bb6e0c066a92af76213708958e4e438e8` reported two failures and one error
in the 28-test fork-runner unit module. The native Solidity source already contains
24 fork cases plus nine hookless cases; the published unit expectations still
said 20 native and 29 total. A boolean named `self.fail` also shadowed unittest's
assertion method, masking one stale expectation as a TypeError. The
[original failure excerpt](original-ci-failures.log) is preserved; this was not
a Vault accounting regression.

The [scoped patch](scoped.patch) changes only three strict inventory expectations
to 24/33 and three boolean references to `self.spawn_failure`, matching the name
in the unrelated dirty working version. No test or rejection assertion is removed.
The dirty test and runner were preserved; the larger unpublished runner changes
are outside this repair.

The isolated rerun passed **all 28 original module tests, zero failures/errors/
skips**. The [receipt](receipt.json) and [test log](tests.log) bind the fixed test,
the exact committed runner and both committed Solidity inventory inputs. The
[baseline copies](sources/baseline/tests_python/test_fork_runner.py) and
[fixed copy](sources/scoped/tests_python/test_fork_runner.py) retain their text.
The [driver](run_scoped.py) materializes a separate mirror from the recorded
commit and runs only this module with synthetic RPC/server/subprocess fixtures.
No real fork, Forge execution, network call or production transaction occurred.

This result does not claim a new complete 568-test run, a green follow-up Ubuntu
workflow, or production approval. The frozen architecture evidence bundle remains
unchanged and scoped to its recorded revision; later Todo/CI publication is a
separate change. No staging, commit or push was performed by this reviewer.
