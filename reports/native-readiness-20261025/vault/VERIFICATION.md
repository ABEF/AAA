# Vault bytecode headroom: scoped verification

The normal build, ABI/storage comparison and selected12 Solidity cases pass.
Production is not approved.

## Change and preserved boundaries

The approved change is limited to three private refactors in `ZZZVault.sol`:

- Balancing and ZZZ handoff consolidation share one private swap implementation.
  It receives the existing storage pointer. Manager lookup, exact approval,
  reading `p.poolId`, the native/ERC20 swap, allowance reset and subsequent idle
  accounting remain in their original order. No external entry point is added.
- Both `_unwind` callers already passed `true`. Removing that private flag keeps
  phase1 checkpointing unconditional at the same point before closing the LP.
- `_put` caches the immutable Budget address locally. It retains all target,
  balance/spend, idle and deployed-position checks in the same order.

No ABI, storage slot/type, economic formula, authority, recipient, dependency,
pause/reentrancy guard, price or execution limit changed. No delegatecall, proxy,
generic executor, sweep or new deployed helper was introduced.

## Measured design selection

Before editing production source, external in-memory compiler variants measured
the alternatives under the normal profile. They are compiler experiments,
not additional EVM tests or semantic-equivalence proofs.

| Candidate | Runtime bytes | Decision |
| --- | ---: | --- |
| Published baseline | 24,519 | 57-byte margin |
| Remove always-true unwind flag | 24,511 | Retained |
| Shared swap using original storage pointer | 24,316 | Retained |
| Cache immutable Budget only in `_put` | 24,474 | Retained |
| All three selected changes | **24,263** | **313-byte margin** |
| Share collect/close observation | 24,433 | Rejected: broader boundary for86-byte gain |
| Share redeployment/event finish | 24,573 | Rejected:54 bytes larger |
| Cache Budget in `_join` | 24,526 | Rejected:7 bytes larger |

The three retained changes together save256 runtime bytes and270 creation bytes.
The measured improvement supplies additional room for reviewed fixes;313 bytes
is still limited headroom. Every later source change needs normal size checks.
There is no claim that smaller bytecode establishes gas-optimal execution.

`experiments-summary.json`, `cache-summary.json`, `selected-summary.json` and
their drivers retain source hashes and rejected alternatives. These experiments
used the published baseline source before editing the repository. The saved
`published-baseline-vault.sol` has the same SHA256 as that original compiler input.
Reproduction must preserve that baseline rather than reinterpret a future HEAD.

## Actual-source normal build and ABI/storage proof

`production-final-size-gates.json` passes all37 normal production object gates
and retains all42 production source hashes. Vault runtime is24,263; creation is
47,006 plus96 constructor-argument bytes, totalling47,102 and leaving2,050 bytes
below49,152. Registry retains its818-byte creation margin. No size/gas gate or
compiler setting was relaxed. Solidity0.8.26/Cancun, via-IR, optimizer1 and
Yul-false remain unchanged. Dynamic constructor arguments retain their separate
exact release-argument qualification requirements.

`vault-abi-storage-comparison.json` recompiles the published baseline and actual
candidate together under that same profile. The public ABI is exactly equal.
Normalized storage recursively compares slot, offset, labels, encoding, sizes,
mapping/array types and struct members while omitting AST IDs and the renamed
comparison contract label; every field matches. This is a structural proof,
not a claim of formal semantic equivalence.

The candidate Vault SHA256 is
`4d56bb0d0e2926f13bd9d78cc3a602017bb5f1cf83b396d75ec0515abae37d39`.

## Selected execution scope

All12 cases pass: three installed-v4 lifecycle/two-pass/failure cases, three ordinary
rebalance loss/donation/reentrancy controls, two local-pool-move cases, three
normal custody consolidation/return/failure cases and the existing fully indexed
maximum-capacity cold activation gate. `scoped.json`, its summary, stderr and
source/test manifest retain the actual execution. No new mirror test or unchanged
full regression was introduced.

The cold activation's named measurement is **11,510,987 gas**, leaving489,013
below the unchanged12,000,000 gate. `cold-gas.log` and `.json` retain that metric.
Only this already-cached case was repeated at verbosity2 because default JSON
omitted its named log. That logging repeat is not a thirteenth distinct case.
The suite's Unit.gas14,158,667 includes other work and must not be reported as
the measured cold operation. No controlled before/after execution-gas comparison
was performed; historical readings retain their earlier source scope.

Installed local v4 execution remains distinct from real Robinhood market/feed/
provider qualification. The existing fixtures substitute access, VRF, prices or
venues where their source explicitly says so. The cold capacity fixture is a
bounded accounting workload, not the maximal real-market transaction. Real gas,
services and independent production audit remain open.

No website source/build, running service, signer, public transaction, deployment,
existing8902/Anvil/NFT/LP/balances/journal/dist, or paused monitor was changed.

One initial PowerShell driver-construction command failed parsing before starting
a compiler. A plain Python generator replaced it. There was no Solidity/test
failure, source workaround or guard relaxation associated with that packaging
error. The final driver and actual successful receipts are retained.
