# Automatic receipt confirmation follow-up

2026-10-20; scoped internal verification. Production NOT APPROVED.

The user reported another recovery screen after the earlier wait/latency fix.
The exact displayed status was generic "Transaction submitted or unresolved".
Reported mint `0xb041662ef159a8ae9778f64d8911b2a99dd24380c1702e8aa92a1ba7c6822560`
has status1 at block 274. Its canonical block was independently read.

The old loop stopped after three checks at 750ms spacing. It also required
eth_blockNumber to reach the receipt height even when a block-by-number read
already established canonical inclusion. A lagging cached head reproduced
pending behavior with this actual receipt and its original reviewed transaction.
The extension's actual cached response was not captured; this reproduction does
not prove that cache was the sole cause of the user's specific incident.

## Change and safety boundary

- One-confirmation policy checks the inclusion block's hash AND number twice.
  It no longer consults a separate head counter for that first confirmation.
  Policies requiring more confirmations still enforce their configured depth.
- Poll the same hash up to 21 times, 1500ms apart (about 30 seconds when reads are
  fast). A 45-second monotonic budget bounds the whole loop and each read uses
  the lesser of its remaining budget and the existing 15-second RPC timeout.
- The client passes the specific pending reason to the UI. Unknown submission
  hashes, provider failures and conflicting receipts retain durable recovery.
- No additional wallet send, automatic payment retry, optimistic LP update or
  relaxed transaction/economic/gas/network/genesis checks.

## Evidence

`node --test tests/browser-wallet.test.mjs`: **54 passes**, six new cases.
`node --test tests/browser-client.test.mjs`: **42 passes**, one new case.
`node build.mjs`: passed, 5,593 files; served client hashes match source.

New cases cover lagging head, receipt arrival after the old three-attempt window,
deadline and hung-read bounds, canonical number mismatch, finite configuration,
and preserving the diagnostic reason without clearing the journal.

The [read-only replay](auto-confirmation-replay.json) uses the user's actual
review/receipt: current RPC confirms; synthetic lagging head produces pending
before and confirmed after. The first probe attempt was interrupted by Git's
safe-directory check when reading historical source; a per-command exact-repo
exception allowed the read-only comparison. No global Git setting changed.
No holder/operator transaction, acknowledgement or backend observation was sent.
Source bindings are [recorded here](auto-confirmation-source-sha256.json).

No backend/contract suite was rerun because their sources are unchanged.
Actual next Chrome/MetaMask transaction remains user acceptance, not established
by these tests. No service reset, public deployment, load campaign or monitoring
change. Historical evidence retains its original scope.
