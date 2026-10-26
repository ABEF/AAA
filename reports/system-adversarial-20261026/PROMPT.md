# Challenged and executed review prompt

## First challenge: scope and assumptions

The user's objective is appropriate, but an assurance that nothing can ever be
broken, gamed or hacked is unprovable. The current system has explicit trusted
governance/external custody, unqualified live dependencies and old local test
deployments. These are not interchangeable with defects, production acceptance
or permission to deploy. Many catalog entries are inherited getters/constants;
assigning them generic theft tests would create false coverage.

Preserve the actual requirements: fixed native ETH/ZZZ, $100/$5 minima,
2%/1%/3% defaults bounded by governance10%, independent3% source agreement,
fixed80/10/5/5, equal permanent collective membership, rarity-only royalties,
current-owner unclaimed rights, direct single-operator governance, no integrated
bridge and trusted custody exit. Do not reintroduce removed assets/roles/delays
or silently tighten allowed callbacks, out-of-range contributions or claims.

The review must include safe-but-unavailable states, refunds/reverts versus
network gas, MEV/economic costs, stale/incomplete observations and recoverability,
not merely access control or integer overflow. It must review helpers/private
paths and services as well as exported ABI functions. The website is a separate
simulation; its existing source/profile mismatch remains an explicit release
gate, not an excuse to alter public signing or the preserved Anvil deployment.

## Refined prompt

1. Pin source/configuration and preserve unrelated work. Read current
   requirements, operator procedures, architecture, task ledger, callable catalog,
   dependency implementations and source-scoped prior verification. Identify
   actual supported versus historical/local/unqualified profiles.
2. Enumerate every catalog constructor/function/receive hook, including inherited
   reads, and the relevant internal/base/library paths. Partition the source
   review by financial boundaries. For every callable, map multiple applicable
   edge/adversarial cases to a concrete property, source location and honest
   evidence status. Shared case families are acceptable; generated rows are an
   inventory, not proof that each permutation ran or passed.
3. Challenge each operation under applicable combinations of caller/authority,
   zero/extreme/malformed/duplicate input, lifecycle state, before/after another
   operation, callback, missing/changed dependency and unusual market condition.
   Include errors, partial attempts, front-running, reorg/replay, stale data,
   capacity/gas, fractional accounting, prefunds, lost keys and recovery.
4. Reconcile cross-contract and service invariants: no incumbent subsidy,
   exact backing/classification, no double allocation/claim, permanent NFT-linked
   rights, no guessed values, bounded work, safe nonce/recovery and secret-safe
   logs. Distinguish market loss/accepted trust from actual authorization or
   accounting violations. Do not assume contract-wallet callbacks are inert.
5. For a concrete finding, first construct a narrow valid counterexample against
   unchanged code. Fix the root cause without weakening guards or silently
   changing economics/ownership/custody. Verify the new property and affected
   compositions. Reuse unchanged build/static/execution evidence only at exact
   pins; do not repeat entire suites or inflate overlapping test counts.
6. Review the fixes independently; reconcile function/source coverage and record
   gaps, conditional properties and external decisions. Update the sole Todo,
   feature evidence, operator/runbooks and repository context where behavior or
   understanding changed. Preserve historical failures and evidence bytes.
7. Publish reviewed source/docs/evidence on main under the standing workflow,
   verify exact remote identity and report concrete improvements, fresh versus
   reused checks and open risks. No public transaction, deployment, signing
   extension, service/website rollout or existing local-state reset.

## Second challenge and final corrections

- **Avoid false equality guards:** same-block claim simulation can legitimately
  differ from a prior view when the owner/asset callback funds royalties or
  claims another ledger. Require a reproducible violated invariant rather than
  treating every unexpected value change as corruption.
- **Avoid false exhaustiveness:** count ABI functions separately from
  constructors/receivers, inherited instances from unique implementation paths,
  scenario mapping from manual analysis, and analysis from execution. Mechanically
  verify the inventory; explicitly record what was not qualified.
- **Test the adversarial boundary itself:** use actual reviewed RPC/HTTP/parser
  adapters with inert transports when assessing malformed responses; mocks that
  bypass decoding cannot establish that property. A malformed remote response
  must not bypass failover or leak raw provider data through exception causes.
- **Do not turn protection into accidental denial:** stop malformed identity or
  contradictory accounting; isolate genuine optional dependency outages only
  where rights/backing rules permit it. Never silently skip required evidence.
- **Keep practical limits explicit:** snapshots are observations, not signatures
  or future inclusion guarantees; per-operation caps do not bound market/IL or
  cumulative turnover, and immediate governance/external custody remain trusted.

These corrections form the final workflow executed by this campaign. Coverage
and findings must retain those distinctions instead of promising universal safety.

## Primary references used

- [Solidity0.8.26 security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html):
  cross-contract callbacks, external calls, forced ETH, loops and failure handling.
- [EIP-1474 RPC encoding](https://eips.ethereum.org/EIPS/eip-1474): typed quantities
  and canonical hash/block observations; [JSON-RPC2 response rules](https://www.jsonrpc.org/specification)
  for response identity and exclusive result/error envelopes. [EIP-695](https://eips.ethereum.org/EIPS/eip-695)
  specifies the chain-ID quantity. [Python3.11 JSON documentation](https://docs.python.org/3.11/library/json.html)
  explains parser hooks, permissive defaults and resource limits; actual tests
  explicitly distinguish transport behavior from injected platform parser limits.
- [Chainlink VRF security considerations](https://docs.chain.link/vrf/v2-5/security):
  ordered request identity, no rerolls and minimal fulfillment work. This is
  design guidance, not a claim that Chainlink is qualified on the target chain.
- Installed source-pinned OpenZeppelin and Uniswap dependencies, existing callable
  reference, current operator/economics guides and source-bound reports. Installed
  implementation bytes control source-specific conclusions; online docs are not
  substituted for the actual dependency version.
