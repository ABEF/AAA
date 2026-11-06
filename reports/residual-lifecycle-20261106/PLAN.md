# Main/residual lifecycle audit and improvement

6November2026; baseline main `5d70b4b5a3ade066ec46a6dd81ed172cf50bc16e`.
Production NOT APPROVED. The user requested execution of the complete lifecycle,
market, accounting, operator, reader and recovery audit—not a new strategy.

## Scope and challenged assumptions

- Two physical positions share one native ETH/fixed-ZZZ pool and logical bucket.
  The residual is not another pool or a per-holder LP NFT.
- Desired hybrid policy, applied geometry and actual residual existence are
  distinct. ON need not create a residual; OFF need not mean an old one is closed.
- Replacement includes governed same-pair movement and parked resume, not just
  Vault.rebalance. Trace the Budget context rather than inferring by call name.
- Default60/40 is a captured replacement allocation constraint, not a continuously
  maintained ratio or token50/50 rule. Price/entry can change later composition.
- Containment makes some requested state combinations normally unreachable.
  Prove that invariant instead of fabricating impossible normal scenarios.
- Existing exact-scoped real-core cases cover many modes, reversals, callbacks,
  fees, entries, parking and terminal return. Reuse only their unchanged scope;
  add missing composition/integrity checks rather than repeat every suite.
- No software can guarantee transferability through permanently broken tokens,
  core contracts or chains. Separate temporary blocking, intentional idle,
  actual stranded accounting and dependency failure.

## Work streams

1. Independently trace physical registration, geometry, custody, quotes, mint/
   increase/refund, collection, burn and state rollback against pinned sources.
2. Reconcile both-leg principal, idle/compound, entrant shares,80/10/5/5 fees,
   owner rewards and terminal/canonical boundaries.
3. Audit same-block keeper/API physical proof, policy coordination and recovery.
   Reproduce contradictory physical data before correcting reader admission.
4. Add actual-core destination-hybrid move/resume/rollback scenarios missing from
   the earlier single-destination campaigns. Keep production source/test freeze.
5. Publish the lifecycle/recovery matrix, source-bound results, retained failures,
   relevant operator/Todo/features/context and exact preservation evidence.

Current compiler/dependency/normal/static evidence can be reused only after
checking exact unchanged production source and settings. A new Python validation
rule is not a Solidity/runtime upgrade, service rollout or independent audit.
No deployment, public transaction, site/service change, signer extension, chain
reset, journal adoption or heartbeat restart is authorized.

## Knowledge and primary references

The actual pinned PositionManager, Pool and SqrtPriceMath source is authoritative
for this build. Uniswap's [liquidity lifecycle guide](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/overview)
describes encoded PositionManager operations. Its [fee collection guide](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees)
explains zero-liquidity decrease followed by taking the two currency credits.
Those operations alone do not prove PoPL's fee/principal classification.

[Solidity0.8.26 security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
motivate reviewing control handed to external contracts and complete rollback;
they do not imply that a compromised token/core can be made trustworthy by
reentrancy guards. Classify those trust boundaries separately.
