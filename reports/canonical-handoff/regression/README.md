# Current offline regression - 2026-10-18

[Verification](verification.json): **582 passes, zero failures, two intentional
fork setup skips**, across 49 compiler-bound suites. The complete run took
1,764.125 seconds. Source snapshots match before and after execution.

The run includes ApprovedProviderTrust and BridgeRouterSecurity with the saved
canonicalModule fixture repair, plus all ten cases in CollectionScale,
CombinedCapacityGas and ProductionGas with final cold-helper accesses. The 12M
per-operation assertions are unchanged. Whole-test Forge gas is not the same
measurement as those bounded operation assertions.

CanonicalHandoff's 34 cases were excluded from this run and reused after checking
all 87 compiled dependencies against current bytes. There are no duplicated
passes in the 616-case combined coverage. NativePoolFork and UniswapV4Fork retain
only their two explicit opt-in setup skips; no current live-fork pass is claimed.

The complete 50 MB raw Forge JSON remains outside Git at the path recorded in
[test outcomes](test-outcomes.json), alongside its SHA-256. All case statuses and
reasons are preserved in that compact file; the verification receipt also binds
the original raw outputs and every suite artifact. This is local verification,
not independent audit, staging qualification or production approval.
