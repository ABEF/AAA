# Supplied-pool fork: pristine state and partial F6 setup

20 November 2026. The supplied native ETH/ZZZ pool remains the test target.
Final production selection is deferred. This campaign uses the exact recent
anchor 119107223, hash `0x13f4c5b0ff38d2e13f17b12b1af8b0894b8d642d8aa1093083441e30e2ed9335`.
**The funded LP lifecycle partition is unfinished, not passed.**

## What actually advanced

- A new owned fork authenticated the original pool key, five native dependency
  runtimes/wiring, original slot state and **zero active liquidity**. The original
  bounded native-input quote is saved before synthetic funding or LP mutation.
  Zero active liquidity is not proof that every distant tick range is empty.
- Trusted F6 production creation objects were reused with all 100 source pins
  checked; production contracts were not rebuilt or changed. New standalone
  custody/budget/admission fixtures and retained feed/trader fixtures compiled
  once. Their exact output was reused after the startup correction.
- **12 local setup transactions** were included successfully: 11 creations and
  one policy binding, including the real current Oracle, Portfolio, Confirmation,
  Strategy, Registry, Balancer and Manager objects. The control is MockAccess;
  these are not a complete production graph, authorized operator or NFT flow.
- [Independent saved-wire verification](VERIFICATION.json) checks the original
  pristine responses and [all 12 included setup receipts](SETUP_RECEIPTS.json),
  exact creation/binding inputs, nonce order and included gas equal to the
  25%-padded estimate responses. This verifies retained data without execution.

The public relay made **118 bounded read-only upstream attempts**, including
**18 HTTP429 responses and 15 retries**. Setup progressed despite recurrent rate
limits, then the agent deliberately stopped the matched owned process during
the custody-fixture simulation. This is an interrupted setup, not a proven
impossible pool, pool-price rejection or production contract defect.

The test owner received local ETH for deployment gas. **No ZZZ balance was
substituted and no persistent pool LP mint/increase/swap/harvest/close transaction
executed.** The untouched diagnostic quote executes only inside `eth_call` and
cannot persist its internal simulated swap.
Owned PID4532 is confirmed stopped with no pending submission. Existing Anvil,
NFTs, balances, journals, services and public state were not changed.

## Retained failures and evidence limits

1. Attempt1 stopped offline: the checker incorrectly expected the fixture's
   MockAccess compilation closure to include unrelated production Access. It
   was corrected to verify the fixture's exact dependency metadata against
   current source and overlapping trusted F6 pins. No node/network action.
2. Attempt2 validated the public anchor with two reads, but Anvil exited before
   binding: case-sensitive environment copying omitted Windows SystemRoot and
   caused Winsock10106. The fixture launcher now preserves that named variable.
3. Attempt3 captured pristine state and the 12 setup receipts, but the report
   transport retained mutable transaction dictionaries. Later gas/nonce edits
   overwrote earlier request metadata. Original bytes are retained, never repaired.
   Independent response and included transaction/receipt fields remain available;
   **the original full-cap/padded preflight request envelopes are unproven**.

The prepared driver now snapshots the serialized request, cleans partially entered
startup failures, and requires the intended `Slippage()` liquidity-guard error
plus non-exhausted gas for a future failed-growth case. These report-driver
corrections were reviewed; **they were not exercised by the interrupted attempt**.
The exact attempt3 runner is retained separately with its original source hash.

No old 11-method fork suite or unchanged behavioral suite was rerun. No gas,
fee, quote, size, source-call or financial guard was raised. No public transaction,
deployment, sealing, provider adoption or live rollout occurred.

## Remaining work

Complete the [planned](PLAN.md) new partition on adequate read-only archive access:
explicit local token funding, real Manager LP mint/increase, actual swap fees,
harvest/no-repeat harvest, close, cleared approvals and rollback. The report
driver deliberately refuses its already occupied evidence directory; a future
run requires a separately reviewed new path, never overwriting or resuming it.

Synthetic local depth and correlated test prices would still not qualify Entry
activation/accounting, independent valuation, external depth after withdrawal,
real conversion feasibility, target-chain gas/fees or production readiness.
