# Native ETH V2 internal implementation review

2026-10-24. Internal source review and focused local evidence, not an independent audit.

## Findings addressed during implementation

1. **Typed native funding and zero identity:** native ETH is explicitly admitted,
   priced and funded. Zero contract targets and missing dependencies remain invalid.
   An unset `currentZZZ` cannot label raw ETH departure as ZZZ.
2. **Income versus principal:** native fees enter individual/equal-collective
   indices; converted credits are not re-earned. Principal, fee reserves, receiver
   quarantine and royalty backing retain distinct custody and captured rows.
3. **Forced ETH during callbacks:** strict post-pull manager baselines reject an
   approved-token callback forcing ETH into a typed LP budget. Vault native receipt
   counters also reject direct forced ETH during collect/close, preventing it from
   becoming fee income or principal. Ordinary prefunds remain excluded.
4. **Canonical funding and abort:** backing transfers precede zero-value
   acknowledgments. Imported prefunds cannot replace sent backing. Native receiver
   token0 protection is not counted again in a native slot2. Duplicate asset rows
   and repeated funding acknowledgments are rejected.
5. **Gas and contract size:** native semantics exposed the existing narrow Vault
   margin and a cold maximum-size canonical capture regression. The work retains
   normal EIP-170/EIP-3860 limits and the unchanged 12M per-call test budget.
   Readonly Budget extraction and skipping provably fresh zero storage writes
   address these without increasing powers or lowering supported asset counts.
   A final adversarial review found that source-companion dust prefunds could
   impose 33 extra nonzero storage writes and reopen the gas failure. Source
   capture no longer snapshots those donations. The immutable coordinator proves
   the actual returned balance increase before abort restoration forwards exactly
   that amount; destination import retains its separate prefund baseline. A
   successor later becoming a source does not reuse its old importer baseline.
   See the source-bound measurements in the verification record.
6. **Versioned services:** explicit native V2 profiles verify the Vault and
   canonical schema; predecessor configurations do not inherit successor currency
   semantics. Keeper journals are not automatically rewritten into another version.

## Preserved trust and limits

Governance remains immediately authorized and explicitly trusted for approved
external custody. Nonredeemability does not guarantee an external custodian's
return. Raw exit remains subject to usable venue/token/runtime bindings, despite
having no wrapper dependency. No sweep, reroll, payout redirect, generic executor,
timelock change or holder withdrawal was added.

The 80/10/5/5 allocation, royalty weights, exact NFT traits, current-owner rights,
1% contribution/reward-conversion and 3% ordinary maintenance limits are retained.
Historical reports remain tied to their original source. Required independent
economic/security and real-service qualification remains open.

The deleted `finalizeImport` and `confirmMigration` handlers previously always
reverted; their obsolete selectors now have no handler and still fail closed.
No retired bridge authority was restored. Explicit actual-pair guards reject
ETH/WETH atomic moves; the fixed-price loss floor is not bypassed by treating
those distinct currencies as aliases. Optional wrapped conversions retain their
own wrapper dependency; current native custody does not call that dependency.
