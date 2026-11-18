# Constant-cost royalty accounting and bounded reads

Baseline main `06956fb22c55ad83d8d65186d6ab8988246995f0`.
Production is undeployed and NOT APPROVED. No existing environment is a target.

## Invariants and chosen design

Replace only the permanent royalty-ticket tree with cumulative complete rounds,
the existing rotating remainder cursor, exact enrollment snapshots and NFT-paid
coordinates. Keep imported accrued separate. Liabilities, backing and aggregate
payout arithmetic stay checked; only lifetime coordinates wrap. This design is
specific to append-only royalty tickets and does not apply to mutable LP shares.
There is no receipt queue or new worker, payout recipient or authority.

Prove actual old-cohort credit before new eligibility; the opening cohort is the
explicit exception enrolled before initial credit. Handle homogeneous unit2/3 to
unit1 transitions, inherited RAW cursor offsets, fault catchup groups, canonical
empty-engine import and funded abort. Same scalar claimable values and allocation
events are required. Never reinterpret another runtime's private storage.

Preserve the1M full optional sync allowance and original GasPolicy tuple. A new
separately governed read-only balance allowance defaults50,000gas; standard
STATICCALL data is bounded. Setter changes invalidate old gas revisions and
commit the new value, without changing the historical gas-fingerprint format.
Future cap/currency changes require requalification; no20M blanket promise.

## Verification order and scope

1. New independent integer-oracle/counter prototypes, including UINTMAX wrap,
   sparse enrollment/zero counters, changing prefixes and phase transitions.
2. Port only a proven implementation; early normal100-source/48-object size
   probe under unchanged0.8.26/Cancun/viaIR/optimizer settings.
3. New targeted actual-ledger cases and affected existing integration cases,
   with exact pre/post source and artifact identities. Historical tree tests
   stay explicitly frozen to V4; unchanged bodies are not executed as current.
4. Complete Entry flow with1,000 minted/999 activated, actual stock600/300/100,
   admitted currencies across population growth, ETH/ZZZ entry/growth, opening,
   rotated receipts and faulty reads—including all16 exhausting read limits.
5. Cold owned account-free loopback calls:20M cap, actual estimates/full20%
   padding and exact padded-call success, verified financial traces.32M remains
   diagnostic only; normal source size/default/financial limits never widen.
6. Fresh payload5 with old3/4 identities preserved. Update unsigned preparation,
   observer/validator, complete function/operator references, sole Todo and memory.

No unchanged suite, public RPC qualification, site/service rollout, deployment,
seal, signer change, existing Anvil/DB/journal mutation or heartbeat restart.
Preserve the four unrelated dirty tracked files and all old reports as recorded.

Primary references: [checked arithmetic](https://docs.soliditylang.org/en/v0.8.26/control-structures.html#checked-or-unchecked-arithmetic),
[gas-bounded work](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html#gas-limit-and-loops),
[ERC20 balance/transfer semantics](https://eips.ethereum.org/EIPS/eip-20).
