# Typed v4 conversion and governed limits: verification

Recorded 2026-10-24. Undeployed development candidate; production NOT APPROVED.
Publication is recorded in a separate receipt. No public funds or live services
were used, and no full fresh regression is claimed.

## Scope and outcomes

| Scope | Distinct passing cases / checks | Evidence |
| --- | --- | --- |
| Parent-only typed executor | 12 Solidity cases, including actual installed v4 PoolManager/StateView swaps and hostile callbacks/credits | [Executor record](executor/verification-final.json), [raw run](executor/helper-tests-final.log), [86 compiler bindings](executor/helper-source-bindings-final.json) |
| Entry through actual Vault | 3 final Solidity cases: ERC20-to-ETH activation, ERC20-to-ZZZ growth, native-to-ZZZ activation, downstream LP/minimum rollback | [Final raw run](executor/entry-tests-final.log), [135 matching inputs](executor/entry-source-bindings-final.json) |
| LP/royalty conversion | 50 Solidity cases across scoped runs: 13 new actual-core/governed-policy cases plus 37 affected existing cases | [Run accounting](rewards/evidence.json), [initial48](rewards/solidity-current.json), [changed13](rewards/solidity-callback-current.json) |
| Governed contribution/maintenance/custody | 18 final Solidity cases: 12 new policy cases and six affected existing flows | [Final 18](policy/tests-final.json), [final bindings](policy/VERIFICATION.json), [normal sizes](policy/source-and-size.json) |
| Activation preparation | 48 Python cases: 14 new typed/profile/cap cases and 34 affected legacy/native cases | [Scoped run accounting](backend/evidence.json) |
| Conversion keeper/reporting | 48 Python cases: explicit current/historical profiles, cap boundaries, pins, state identity and reporting | [Source-scoped record](rewards/evidence.json) |
| Event decoding | 16 existing checks pass; 119 earlier descriptors retained exactly, six added | [Compatibility](event-compatibility.json) |
| Compiler and source | 35 normal production object gates, 79 matching production compiler inputs, 109 Solidity ABI/typecheck inputs, 131 final source/test hashes | [Sizes](size-gates.json), [bindings](compiler-bindings.json), [typecheck](typecheck.json), [source hashes](source-sha256.json) |

Totals are **83 distinct Solidity and 112 Python passes**, across the documented
source scopes. The two existing converter fuzz cases retain their recorded
1,000/1,001 runs; repeated cases are not counted twice. Local installed-core
execution is not a Robinhood mainnet fork or qualification of live markets.

## Changed behavior verified

- Typed hookless static single-hop v4 routes, immutable parent/executor identity,
  fixed recipient, exact native/ERC20 funding, full input settlement and positive
  output, strict runtime/key/view pins, preserved prefunds and callback context.
- Owner-authenticated exact Entry contribution, original-source valuation and
  per-NFT shares, marginal deployed LP, actual confirmed event/LP result. A failed
  swap, minimum, forwarding or LP deployment reverts atomically; gas is separate.
- Already-earned LP/royalty balances only, exact native output and unchanged
  historical NFT entitlement, with explicit wrapper-free v4 and preserved v3.
- Immediate governance settings default 100/100/300 bps, hard 1,000 bps; zero and
  boundary rejection, authorization/lifecycle guards, callback defenses, rounded
  floors, captured contribution/maintenance limits and immutable custody plan floor.
- Budget read-only validation extraction authenticates its existing fixed
  VaultCanonical to the actual Vault Budget. No canonical codecs, writes or
  funding authority changed. Final actual activation/growth and custody/rebalance
  cases exercise this source.
- Explicit routing version2/current worker/reporting schemas read current on-chain
  policy. Legacy fixed-cap/v3 profiles are not silently reinterpreted. Exact
  approval, fresh review, gas and caller minima remain additional guards.

## Size and diagnostic scope

Solc 0.8.26, Cancun, viaIR, optimizer runs1, EVM optimizer on/Yul optimizer off.
No compiler/code-size limit was relaxed. Final Vault runtime is 24,508 bytes
(68 margin); creation including 96 constructor bytes is 48,444 (708 margin).
Registry creation including 32 argument bytes is 47,369 (1,783 margin).
Migration runtime 24,360 and VaultCanonical runtime 19,990 also pass.
Converters runtime 16,952; helper 11,164. Dynamic constructor arguments still need
actual release-specific size review.

The first controls draft exceeded Vault creation limits and was rejected. The
compact shared setter and guarded read-only extraction restored normal gates.
An earlier policy run passed 8/12 and exposed four fixture sequencing errors;
[initial diagnostic](policy/tests.json) is retained, and final 18 passes cover
repaired cases under final source. One new Python fixture argument error was
repaired before its final focused run. A later signed-bound rejection was tested
separately; earlier valid fixture inputs remain below that new guard.

The standalone size command emits a valid size table and then exits on the known
host global signature-cache permission error. This is recorded in raw size logs;
acceptance uses actual compiler artifacts, ordinary limits and matching metadata,
not an invented successful command exit. The external ABI typecheck initially
needed the installed solmate remapping; the repository already auto-resolves it.
No dependency or compiler profile was relaxed. Unchanged helper, converter and
legacy checks were reused with their explicit source bindings.

## Remaining gates and preservation

Actual routes/tokens, independent prices, RPC traces/network fees, VRF,
keeper/hosting operation, native website/inventory, atomic ETH/WETH principal
moves, OpenSea mint, remote canonical handoff and independent audit remain open.
Governance may authorize up to 10% loss immediately; no cumulative breaker or
protection against future market loss is implied. Stronger venue/caller minima
remain, and normal custody floor changes require a separately reviewed new plan.

No website source/build/server, public deployment/transaction, private-key use,
existing 8902/Anvil/NFT/LP/balance/journal/dist overlay, signer or monitor changed.
Public DEPLOYMENT remains null; signer Anvil-only; monitor paused. Main only.
See [internal review](REVIEW.md), [operator controls](../../docs/EXECUTION_LOSS_POLICY.md),
[typed routes](../../docs/TYPED_V4_ROUTES.md) and the [single Todo](../../TODO.md).
