# Retired test fixtures

These are historical source archives, excluded from Solidity compilation. They are not current tests or new passing evidence. Original report scopes remain unchanged.

- `ExternalRewards.t.sol.txt`: the removed optional creator-payment inbox system. Real LP fee and separate marketplace royalty accounting remain tested in the active fee, pooled-rights, native and canonical suites.
- `mocks__RouterMocks.sol.txt`: unused integrated transport fixtures.
- `NativePoolFork.t.sol.txt`: old wrapped-native pool assumptions. It cannot qualify current native ETH accounting. A current Robinhood fork rehearsal remains a release task.
- `*.retired.txt`: only obsolete helpers or cases removed from otherwise retained mixed suites, with the reason beside each original fragment.

Mixed suites retain ownership, LP shares, funded claims, royalties, dust, principal backing, handoff/abort, scale and gas assertions. Creator-funded setup is replaced by actual venue fee collection, preserving the independent expected totals where applicable. The immutable external original files and SHA-256 retirement manifest record the source boundary.

Compilation, executed local cases, normal object limits and target-chain qualification are separate evidence. No deleted feature is replaced by a zero-return stub.
