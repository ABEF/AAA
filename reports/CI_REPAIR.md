# Development-verification repair — 2026-10-14

The [initial failed run](https://github.com/ABEF/AAA/actions/runs/38511008220) stopped before tests because npm does not publish `@uniswap/v4-periphery@1.0.4`. The dependency is now pinned to published version 1.0.3, with a real npm lockfile and integrity hashes. OpenZeppelin 5.4.0, v4-core 1.0.2, and forge-std v1.9.7 remain unchanged.

The [next run](https://github.com/ABEF/AAA/actions/runs/38523050113) installed dependencies and passed all 84 Python tests, then exposed Solidity 0.8.26's internal bytecode-assembly error. Isolated compilation identified the vault's default Yul-optimized build as the failing case. The recorded workaround disables only the Yul optimizer; via-IR compilation, the EVM optimizer, 200 runs, and standard size gates remain enabled. No contract logic or permission checks were changed.

Foundry 1.4.4 rejected `testFailedMintRollsBackWholeDeposit` because its name starts with the removed `testFail` prefix. Renaming it to `testMintFailureRollsBackWholeDeposit` enables the existing rollback assertions without removing or weakening them.

Local verification used official Foundry 1.4.4 (`05794498bf47257b144e2e2789a1d5bf8566be0e`) and Solidity 0.8.26 / Cancun on native Windows:

- Every contract, test, and deployment script compiled.
- All 16 module runtime artifacts are below 24,576 bytes and initcode below 49,152 bytes. The vault runtime is 23,451 bytes, with 1,125 bytes of remaining runtime capacity. See [module sizes](ci-repair/module-sizes.json).
- All 70 supplied Solidity tests passed, zero failed or skipped. Each of the two fuzz tests ran 1,000 cases. See [test output](ci-repair/forge-tests-windows.log).
- Complete Unix Python verification is evidenced by the Ubuntu run above; native Windows still lacks the Unix permission/`fcntl` assumptions.

The latest [workflow run](https://github.com/ABEF/AAA/actions/workflows/verify.yml) determines the complete CI result for each pushed commit. These checks do not close the independent audit, gas benchmarking, stateful invariants, real Uniswap fork, or production bridge integration gates. Original delivery evidence has been retained.
