# Five failed fixture cases: repair and exact rerun

The initial focused49-method selection executed44 passes and5 failures. This
follow-up changes only two current test fixtures; all41 production Solidity
source hashes remain unchanged against `manifest.json`.

- FixedZZZPool three negative cases expected one `zzz()` call but also read the
  getter in their own final assertion. The correct total is two: one real Registry
  read plus one test postcondition read. The poison oracle/reward controls remain;
  omitting or duplicating the Registry read still fails the exact count.
- NativeCanonicalIntegration kept a parking deadline one day ahead after its
  scheduling-time warp was removed. The unchanged ten-minute guard correctly
  returned `Expired()`. A fresh100-second deadline fixes the fixture; production
  guards, backing, assertions and direct governance remain unchanged.

Exact root/profile pre-repair bytes match and are archived here. The manifest
records their hashes and replaced byte ranges, source Git HEAD, unchanged41-source
hashes and initial failure-summary identity. No production patch was needed.

The five failed methods were then executed once and all five passed in1.484s
using the existing AST-focused profile. The earlier44 passes were not rerun or
counted again. See `results.json` and `raw-results.json`. The native cases include
full setup/deployment work; their test gas is not a production transaction quote.

Two preceding runner invocations executed zero tests: the first compiled the
repaired fixture files but matched no full signatures (263.094s); a CLI correction
then targeted the wrong argument and was rejected before execution. Both are
recorded with exact stderr/hash evidence, never counted as passes. The final
selector explicitly matches the five full `()` signatures. No -vvvv diagnostic
run was needed because source/count/deadline evidence identified both causes.

This is selected local execution under the existing reduced profile, not a full
fresh regression, normal size/gas release qualification, live-provider rehearsal,
public deployment or independent audit.
