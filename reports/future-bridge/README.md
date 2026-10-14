# Fixed future-bridge router verification

Date: 2026-10-15. Baseline: `4924d0f6db30a734dad4617f9b1f174cc5f8b4e1`. Scope: the undeployed AAA contract candidate. The user authorized secure onboarding for future unknown EVM chains, pools and bridge providers. Actual provider selection, SDK implementation and funded use remain pending. No public-chain deployment, transaction or website change occurred. This is internal engineering/security evidence, not an independent audit.

## Result

The new fixed `ZZZBridgeRouter` permits append-only timelocked provider policies after sealing without replacing the vault or adapter. Policies capture both physical router/wrapper identities, runtime/configuration hashes, channel and review digest. Each route permanently binds its policy; changing providers creates a new route ID. Existing plans cannot be redirected by selecting a new provider.

Policies start outbound-disabled. Migration validates readiness at proposal, before closing LP, and at router dispatch. Typed principal/reward/ACK vectors, exact sender/recipient funding, donation-preserving balances, temporary approvals, callback guards, origin validation and a provider-independent economic nonce domain constrain the custody handoff. Local wrapper pins are checked before and after funding/handoff. Failed operations atomically roll back principal, nonce and replay markers. Authenticated pending inbound settlement remains available after route/outbound disable and pause.

The local-only deployment template creates an empty router; sealing validates the adapter endpoint against the fixed router. Local paid dormant mint, owner activation and permanent top-ups do not require a bridge policy. The schema-2 offline manifest supports that explicit migration-disabled launch scope without waiving economics, valuation, authorities, staging or independent-review gates. Full onboarding and trust assumptions are in [BRIDGE_ONBOARDING.md](../../docs/BRIDGE_ONBOARDING.md).

Compatibility: `Route` and economic `BridgeMessage` version 2 retain their layouts. Registry registration changes to `add(Route,bytes32 policyId)` and route identity changes to `keccak256(abi.encode(route,policyId))`; regenerate operator route IDs. A version-1 physical transport envelope wraps the version-2 payload. Indexer schemas include provider-policy bindings and transport receipts; decoding regressions pass.

## Executed local checks

| Check | Result / evidence |
| --- | --- |
| Full Solidity compilation and size gates | All contracts/tests/local script compile with unchanged Solc 0.8.26/Cancun, via IR, optimizer runs 1, Yul disabled. All 17 modules fit EIP-170/EIP-3860. Router runtime/initcode 14,964/15,476 bytes; vault unchanged 23,662/24,688. [Build](final-build.log), [sizes](module-sizes.json). |
| Complete offline Solidity suite | **183 passed, zero failed, one expected opt-in fork setup skip**, 15 suites. Five fuzz tests each run 1,000 cases. Existing stateful model: 32 runs / 4,096 calls / zero unexpected reverts; it covers local accounting, not arbitrary cross-chain/provider sequences. [Full test/gas output](final-tests-gas.log). |
| New router adversaries | **38 passed**, including one 1,000-case funding/replay fuzz. Wrong provider/origin/route policy, code/config drift, reentry, partial consumption, zero receipts, taxed/extra-tax tokens, donations and underfunding, rollback/retry, old-policy settlement and global replay. [Targeted log](router-security-tests.log). |
| Multi-chain state machine | **7 passed** with real routers/core custody/controllers and explicit mock LP venue plus unbacked burn/mint SDK queue. Empty-router local launch, A→B→C→A→B, reversed/one-sided asset order, pre-release disable, pending old-provider rotation and historical rewards. No live bridge backing/finality proof is implied. Included in full test log. |
| Static analysis | Pinned Slither 0.11.6, 86 contracts / 102 detectors, **136 individually reviewed findings**: 73 conditional false positives, 49 accepted risks/design assumptions, 14 informational. Source-identity/review gate passes. [Raw normalized output](slither-final.json), [review](slither-review.json), [log](slither-final.log). |
| Secondary internal review | All 15 changed High/Medium findings and router custody boundaries reviewed by a collaborating agent, with exact source/test hashes. No confirmed new exploit within the bounded documented trust model. [Review](secondary-security-review.json). |
| Retained Foundry lints | 41 unsafe casts and six unchecked transfers: 33 production / 14 test warnings, individually reviewed. Conventional timestamp narrowing remains an assumption. Additional style/gas notes are retained; no warnings suppressed. [Review](forge-lint-review.json). |
| Source and event consistency | 22 Solidity source files / 17 modules, zero textual consistency errors; 45 generated event schemas. These checks are not compilation or security proof. [Source record](source-checks.json). |

The full Python inventory and Windows subset are recorded in [python-windows-portable.json](python-windows-portable.json) and [log](python-windows-portable.log). Four unchanged Unix state/locking/link tests require Ubuntu and remain mandatory in CI. The exact published revision must pass all three Ubuntu jobs, including the separate six-test actual Robinhood dependency fork; the offline skip is not a substitute. Fork tests exercise the existing Uniswap adapter against deployed dependencies and a different local hookless test pool, not this new router against a live bridge.

Historical production/readiness/analyzer reports remain in their own directories. The previous analyzer review is preserved as [slither-review-4924d0f.json](../history/slither-review-4924d0f.json). The current CI review gate uses `reports/production/slither-review.json`, identical to this directory's review; its source hashes bind the current Solidity/toolchain snapshot. The root manifest binds the published files.

## Remaining release gates

Implement and independently review each actual SDK wrapper, asset backing, source authentication/finality and exact atomic delivery/retry semantics; rehearse every chain and onward/return/revisit path. Runtime pins cannot detect hidden proxy upgrades or prove that a configuration getter is honest, and local code cannot prove declared remote hashes. Wrapper/channel mutation can deliberately halt pending settlement. Governance still chooses future custody and can approve unsafe destinations; a timelock provides notice, not a permanence guarantee.

The user-deferred Pons revenue share versus new-pool decision, native/hook integration where required, authentic ZZZ valuation/outage policy, production authorities, staged operations and independent audit/deployment review remain open. NFTs and Power stay canonical; no arbitrary asset conversion, satellite user top-ups, admin withdrawal or timeout refund was added. No claim of production readiness or guaranteed capital value follows from passing these checks.
