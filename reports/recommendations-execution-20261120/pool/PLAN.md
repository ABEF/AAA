# Current F6 native-pool partition

Use the supplied pool at the exact recently captured block 119107223/hash
13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335.
Public transport is the maintained read-only cached Pinax relay; all state changes
are restricted to one PID-owned loopback Anvil process on a fresh ephemeral port.

Reuse trusted F6 production objects after checking their source/build pins. Compile
only new tiny local custody/budget/asset-allowlist fixtures and the existing
standalone feed/trader test substitutes; no production build or old test rerun.
The controls are explicitly MockAccess and correlated fixture USD prices. They
cannot qualify governance, independent sources, NFT accounting or an Entry flow.

1. Capture the untouched pool key/price/active liquidity, exact five native
   dependency runtimes/wiring and a bounded diagnostic quote/refusal.
2. Deploy current real Registry/Oracle/Strategy/Portfolio/Confirmation/Balancer/
   Manager objects, with explicit controlled Access/Policy/custody seams.
3. Assign ETH/ZZZ test balances locally, seed a main LP through the real F6
   Manager, then increase, trade, harvest actual fees, repeat harvest and close.
4. Verify LP ownership, actual liquidity, fixed ticks, cleared approvals,
   physical balances, no duplicate fees, empty manager/child residual balances,
   and preservation of seeded external core/token/periphery identities.
5. Stop the owned process and retain raw wire, receipts, failed attempts and
   compile/source identities. Do not touch existing Anvil/services or public
   state. Synthetic local depth is not external-depth or production approval.
