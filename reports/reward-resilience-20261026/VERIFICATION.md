# Reward resilience verification

## Final affected Python scope

[Runner](run-affected.py) combines the maintained23-module keeper selection with
three claim-preparation modules. It selects only each module's defined TestCase
classes, deduplicates method IDs and pins local Python inputs before/after,
including lazy fixture dependencies. Inventory pins are not whole-module coverage.

[Final report](affected-suite.json): **443 distinct methods, 437 passes,6 explicit
skips, zero failures/errors**, with no source drift. Thirty new methods are
included once:16keeper isolation/pending cases and14claim activation-integrity
cases. Prior subset runs overlap and are not added to this count. Five skips
require Unix permission/locking behavior; the cast CLI smoke test is not executed
because cast is not on PATH in this invocation. No live Linux/service/target-chain
qualification is inferred. All signing/submission is inert or dry-run test work;
loopback HTTP tests use their own fixtures, not the installed website/service.

The original [443-method attempt](regression-attempt1/affected-suite.json) has one
failure, zero errors and six skips. It caught the candidate's changed handling of
missing currency thresholds. The existing fail-closed assertion was not relaxed;
only the exception boundary was narrowed before the final rerun. Both source
identities/results are retained rather than relabeled as the same candidate.

## Source-bound negative controls

Against the original `da7ec983` sources, the final new tests reproduce:

- Keeper: 13 failure records across10methods (including four conversion subcases),
  six control methods already passing and zero fixture errors. Final 16 pass after
  the correction. [Before](keeper/before.json), [after](keeper/after.json).
- Claim preparation: 14 failure records across six methods, eight controls already
  passing and zero errors. Final 14 pass. [Before](backend-claim/before.json),
  [after](backend-claim/after.json), [bindings](backend-claim/source-bindings.json).

Keeper's earlier overbroad candidate pair is retained in
`keeper/attempt1-price-and-config-errors/`. Preliminary fixture/driver exploration
omitted a current-profile response and initially expected12rather than13records;
these were harness mistakes corrected before the valid bound receipts above,
not production failures or extra coverage.

## New actual Uniswap v4 integration check

[One new method](solidity-summary.json) passes with actual installed local v4
PoolManager, PositionManager and StateView plus production Vault/fee/reward
accounting. It generates real swap fees for two NFTs, expires both fixture price
sources, confirms rebalancing rejects stale prices, then collects actual fees and
claims both holders' funded balances. Physical LP liquidity/token ID/Vault owner,
NFT shares, unrelated entitlements and compound/buyback reserves remain intact.
Donations and protocol fees remain separate. [Results](solidity-results.json).

The admitted venue, governance/VRF/provider/feed independence and Permit2 inputs
are explicit local substitutes; this is not actual Robinhood qualification.
The reported 13,721,830 gas covers a composed test containing multiple user/trade/
harvest/claim actions, not one proposed production transaction or a replacement
for the existing per-operation gas gates.

[Typecheck](typecheck.json) and [bindings](bindings.json) pin 265 Solidity inputs.
Only the new method in `test/IntegratedEconomicConservation.t.sol` changes from
the preceding AST; normal 0.8.26/Cancun/viaIR/runs1/Yul-disabled settings are retained.
The selected driver preserves test/helpers byte-exact and removes only unrelated
test methods. Production 44 Solidity/31normal dependencies/four build pins remain
unchanged. Existing37object/static and1,000claim-order evidence are reused at
their exact source scope; no unchanged full Solidity/static suite was rerun.

## Publication and operating limits

No new permissions, schema, calldata, rate, minimum, token, custody or governance
model is introduced. All corrections are off-chain safety/liveness checks plus
tests/docs. Existing Anvil/NFT/LP/balances/journals, website/server, paused monitor
and actual keeper services remain untouched. No public RPC/signing/deployment
or public transaction was used. Source publication does not update an installed
service or qualify real dependencies. Production remains **NOT APPROVED**.
