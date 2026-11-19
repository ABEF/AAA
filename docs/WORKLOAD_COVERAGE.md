# Whole-project workload coverage

The [workload plan](WORKLOAD_PLAN.json) and
[whole-project function inventory](../reports/whole-workload-review-20261119/FUNCTION_INVENTORY.json)
define the scope. [The report](../reports/whole-workload-review-20261119/REVIEW.md)
records what actually ran and what remains unqualified. The [Todo](../TODO.md)
owns work status; this page is a verification map.

A finite campaign cannot prove every possible numeric state, market or malicious
contract. We require an explicit source/function inventory, reachable state
partitions, boundary and adversarial cases, independent invariants, stateful
sequences and source-bound evidence. No inventory count is a dynamic pass rate.

## Function and implementation scope

- 40 callable objects:968 functions,40 constructors and13 receive hooks.
- 1,056 implemented project Solidity definitions and29 modifiers from the
  authenticated compiler AST;511 bodyless declarations remain separately labelled.
- Eight internal-only objects are included, beyond the public ABI catalogue.
- 179 production Python files and1,976 named lexical definitions:1,796 functions
  and180 classes, including nested helpers. The anonymous-code supplement also
  records276 lambdas and2 named project Yul helpers. This is source inventory, not a claim that each body was exercised.

The [separate published website scope](../reports/whole-workload-review-20261119/WEBSITE_SOURCE_SCOPE.json)
adds29 production JavaScript modules/1,178 function nodes and39 test/helper
modules/2,139 function nodes, with HTML and17 classes inventoried. Parser/source
coverage is not browser/renderer/wallet execution; public configurations and
Anvil-only signer remain unchanged.

The inventory rejects unreviewed build/source/ABI drift and incomplete family
assignments. It reads trusted existing compiler output without compiling or
running application modules, tests, RPC or signing. Preserve the unrelated dirty
fork runner: its published HEAD blob is inventoried instead of adopting it.

```text
python scripts/build-workload-inventory.py --check reports/whole-workload-review-20261119/FUNCTION_INVENTORY.json
```

Future F6 source/reference changes require reviewed trusted-pin/plan updates and
new source-scoped evidence. Regenerate to a NEW output path, review the diff and
retain the old evidence. No automatic approval or deployment follows.

## Operation families

| Family | Principal scenario obligations |
| --- | --- |
| deployment | 8 scenario classes; exact contract/source membership and cases in the plan. |
| governed policy | 8 scenario classes; exact contract/source membership and cases in the plan. |
| mint draw | 9 scenario classes; exact contract/source membership and cases in the plan. |
| metadata | 7 scenario classes; exact contract/source membership and cases in the plan. |
| prices | 9 scenario classes; exact contract/source membership and cases in the plan. |
| contributions | 10 scenario classes; exact contract/source membership and cases in the plan. |
| physical lp | 10 scenario classes; exact contract/source membership and cases in the plan. |
| strategy | 9 scenario classes; exact contract/source membership and cases in the plan. |
| fees membership | 8 scenario classes; exact contract/source membership and cases in the plan. |
| lp claims | 9 scenario classes; exact contract/source membership and cases in the plan. |
| royalties | 10 scenario classes; exact contract/source membership and cases in the plan. |
| compound | 7 scenario classes; exact contract/source membership and cases in the plan. |
| conversion burn | 8 scenario classes; exact contract/source membership and cases in the plan. |
| manual exit | 10 scenario classes; exact contract/source membership and cases in the plan. |
| canonical | 10 scenario classes; exact contract/source membership and cases in the plan. |
| internal math | 6 scenario classes; exact contract/source membership and cases in the plan. |
| shared types interfaces | 4 scenario classes; exact contract/source membership and cases in the plan. |
| read wallet portfolio | 6 scenario classes; exact contract/source membership and cases in the plan. |
| unsigned preparation | 6 scenario classes; exact contract/source membership and cases in the plan. |
| history indexer | 6 scenario classes; exact contract/source membership and cases in the plan. |
| keeper scheduler | 7 scenario classes; exact contract/source membership and cases in the plan. |
| http workers | 6 scenario classes; exact contract/source membership and cases in the plan. |
| website wallet | 8 scenario classes; exact contract/source membership and cases in the plan. |
| release operations | 6 scenario classes; exact contract/source membership and cases in the plan. |

These187 top-level classes are expanded by21 service subfamilies with85 finer
partitions. They are not272 executed tests. Cross relevant operations with:

- All caller roles, unauthorized callers and changing authority/ownership.
- Bootstrap, sealed/paused, pool flags, active/parked, terminal and canonical phases.
- Zero, typical and boundary populations;1,000NFTs,16/64currencies, four buckets,
  both LPs, and every batch boundary supported by that operation.
- Flat/bull/bear/reversal/gap markets, tick equality, same/opposite reference sides,
  depleted post-withdrawal depth and incomplete execution.
- Just before/at/after every minimum, expiry, cutoff, observation/cooldown/jitter.
- Interleaved holder/keeper/governance actions, callbacks, restarts and partial failures.
- Malformed inputs, wrong decimals, replayed reviews, bad tokens/receivers,
  missing/stale sources, RPC/worker/storage failure and old profile identities.

Reachability matters. An honestly contained residual cannot be active while its
main is outside the enclosing range. That is a corrupt-state rejection scenario,
not a positive market case. Unsupported bridges, new tokens or public signing
are explicit negatives, not features to revive silently.

Operational shell/PowerShell/workflow entry files are also pinned in the
[operational source map](../reports/whole-workload-review-20261119/OPERATIONS_SOURCE_SCOPE.json).
That is file-level scope; no installation, deployment or live service action
is inferred or executed by the inventory.

## Controlled maximum-state results

[The expanded rehearsal](../reports/maximum-workload-20261119/REVIEW.md) executes
one new populated journey and20 cold states.11/12 ETH/ZZZ contribution states
fit32M/full20%; opening ZZZ with64 slow ERC20 royalties plus ETH needs32,571,362
padded and remains refused. Five executable maintenance paths fit24M/full25%;
three intended timing/source rejections reproduce. Both LPs,1,000 NFT rights,
all65 royalty payouts, raw LP liabilities and80/10/5/5 backing reconcile.
Only three affected growth preflights were rechecked; nine completed activation
records keep their original checker source. This finite synthetic-depth evidence
is not every listed scenario, token implementation, lifetime or real-provider approval.

## Evidence and completion rules

Use [the scenario register](../reports/whole-workload-review-20261119/SCENARIO_REGISTER.json)
for obligations and scoped evidence. A test must bind actual inputs, assertions,
source/runtime identity and outcome. A mentioned function or successful transaction
alone does not prove correct outputs, accounting, permissions or recovery.

Current new evidence covers a repaired independent exact-unit market model and
bounded ownership paging. It does not close every planned combination. Keep
new execution, exact-source reuse, historical evidence, source inspection,
unexecuted cases, external blockers and user-deferred capacity work distinct.

For every successful financial action reconcile principal, individual/equal LP
rights, royalties, compound, buyback, claimed and returned amounts. For every
refusal check full state/value/allowance rollback where atomicity applies.
Approval is its own transaction; a later reverted contribution does not undo
that earlier approval or reimburse gas.

Dedicated10/25/100-user capacity benchmarking remains user-deferred. Basic
concurrent isolation, correctness and recovery remain in scope. No test/matrix
provides production approval, a provider SLA or permission to alter live state.
