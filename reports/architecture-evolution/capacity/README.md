# Permanent capacity and local switching verification

Fresh focused verification, completed 2026-10-17. All **91 tests passed**,
zero failures and zero skips. The two raw executions are separate; no historical
outcomes were merged. The exact commands, selected files, pinned tool hashes,
source hashes, raw Forge JSON and stderr are preserved in `targeted/attempt1/`
and `affected/attempt1/`. `compiled-bindings.json` checks the current byte content
of every dependency against compiler metadata for each executed suite, accepting
only explicitly recorded CRLF-to-LF normalization where required.

The only production change is the bounded idempotent bucket registration in
Vault and registration before committing a pool reservation. Reservations and
historical custody now share four permanent slots. Pool aliases and returns
reuse an existing slot. No principal, NFT shares or active status are created by
a reservation. Ordered accounting-pair restrictions remain intact.

The first run covers reservation admission, both local-activation/reservation
orderings, successful reserved arrival at a full destination, malformed and
late-token-failure atomicity, None-state membership settlement, full-cap aliases,
and actual Vault/Migration local same-pair moves. The switches preserve shares,
home identity, prior funded claims, designated compounding and excluded donations;
different pairs, reverse order, occupied pools, venue failures and ordinary
authorization/deadline/pause failures remain rejected. Governance cancellation
does not recycle an earlier reservation.

The second run covers combined maximum-asset/inbox/royalty workloads under the
unchanged 12M gas assertion, custody parking, repeated compatible-asset future
chain moves/returns, delayed accounting and route/authentication restrictions.
These exercise actual protocol and some real timelock paths with synthetic
venue, feed/VRF and transport fixtures. They do not qualify production authority
choices, actual selected-Pons gas or a production bridge.

The targeted standalone Vault artifact is **24,122 runtime / 24,875
initcode-object bytes**, with **454 runtime bytes** remaining under
EIP-170. Constructor arguments are excluded. A complete normal all-object build
and fresh source-bound static review are separate evidence and must not be
inferred from this focused compilation.

Source code still does not authenticate remote capacity proofs. Provider backing,
destination correctness, finality, market truth, real execution costs, different-
pair conversion, canonical-chain continuity, authorities and independent audit
remain boundaries. No public deployment or real asset movement occurred.
