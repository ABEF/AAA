# Historical test sources

`ActivationEntry.t.sol.txt` preserves the original 31-method, mock-only Entry
suite byte-for-byte. Its source hash and exact method list are recorded in
`ActivationEntry-retirement.json`.

It targets the retired unreviewed `execute(Request)` selector, a mock without
the current ContributionPricing helper, generic third-token inputs and native
wrapping. Those semantics do not describe the current reviewed native-ETH,
ETH/ZZZ-only contribution candidate. The file is not compiled or counted as
current passing coverage. Its history is retained rather than changing the
assertions mechanically to make obsolete behavior pass.

The reusable typed-v3 route identity fixtures moved to
`../helpers/ActivationRouteFixture.sol`. Current real Entry/Vault/Pricing tests
are in `../EntryReviewPolicy.t.sol`, `../AtomicActivationIntegration.t.sol`,
`../TypedV4Entry.t.sol` and `../ContributionSourcePolicy.t.sol`; each run still
needs its own exact source scope and evidence. This archive does not claim that
every historical case has been rerun or replaced one-for-one.
