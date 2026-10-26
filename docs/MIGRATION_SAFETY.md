# Local LP maintenance and collection preparation safety

This guide describes current local safeguards, not the removed bridge executor.
Use [exact custody operations](GOVERNED_CUSTODY_HANDOFF.md), [loss policy](EXECUTION_LOSS_POLICY.md)
and [same-chain collection handoff](CANONICAL_HANDOFF.md) for callable procedures.

## Aggregate maintenance budget

For guarded same-actual-pair moves, resumption and ordinary rebalancing, capture
starting LP+attributed idle at fixed initial prices, include exact released
compound in the denominator, then compare actual final LP+attributed idle using
those same prices. Default3% means at least97% retained, not97%deployed. The5%idle
ceiling, nonzeroLP, close/swap/deployment guards and stronger minima remain.
Governance may change future maintenance policy up to10%; captured operation/
custody floors are not retroactively weakened. Gas is separate.

Other buckets, donations, accrued claims, royalties and buyback reserves cannot
subsidize maintenance. Failure rolls back the atomic action. A per-operation cap
does not bound cumulative repeated loss or impermanent loss. Contribution uses
its different default2% marginal deployed-LP budget, with the caller maximum,
upper-source/lower-LP marks and$100/$5original-value thresholds.

Same-pair pool movement does not convert ETH to WETH or implement another pair.
External conversion/issuer exchanges use approved trusted custody. Explicit raw
exit skips swaps/USD loss checks under its reviewed raw minima; it is never an
automatic fallback. Broken tokens/venues can still block collection/close/send.

## Preparation and canonical replacement

Governance announces an exact `PreparationNotice` through the direct controller;
there is no timelock schedule/executor. Preparation stops new economic work and
ordinary protocol configuration while permitted existing claims/transfers,
original reveal, harvest and exact funded local draining remain governed by
their own guards. Cancel only the exact current notice. Consult the callable
reference and [handoff procedure](CANONICAL_HANDOFF.md) for the full ordered steps.

Preparation alone does not retire the source or authorize a successor. The
same-chain coordinator separately freezes ownership/accounting, exports/imports
bounded complete domains, verifies actual classified backing and atomically
retires/activates one deployment. Fully funded abort restores original rights.
Pending VRF draws must finish; outstanding custody must return before capture.

The keeper observes `preparationActive()` before new maintenance/signing and
preserves original receipt recovery. Missing/malformed controller state rejects;
an old controller is not upgraded by changing configuration. Existing running
staging/services remain separate from source publication.

Integrated bridges, remote reward/ACK draining, satellite shutdown and cross-chain
canonical finality are not current procedures or launch/sealing prerequisites.
External custody leaves canonical NFT/reward rights on the source chain. A future
whole-protocol cross-chain design and post-halt recovery would need separately
reviewed code; they are not configuration promises of sealed contracts.
