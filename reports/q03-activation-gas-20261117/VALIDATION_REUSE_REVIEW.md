# Adjacent execution-proof reuse

This scoped optimization changes only `ZZZLiquidityManager.sol` and
`ZZZContributionPricing.sol`. It removes repeated complete source proofs where
the retained authenticated proof is adjacent and only read-only calls intervene.
There is no global cache, keeper-supplied price, new authority, financial-limit
change, public getter relaxation or default gas-budget change.

## Evidence before the change

The existing empty-ETH activation trace contains 121 wire records; record 94 is
the actual `debug_traceCall` call tree. Its compressed SHA-256 is
`9c1cf774314fcb32777bfc48d08b1591d6a7125cecf83922b0e9b74735401c35`.
Four concrete adjacent-proof sequences were identified:

| Site | Duplicate work omitted | Retained proof and boundary |
| --- | --- | --- |
| Manager initial context | Complete source validation immediately after `beginManagerExecution` | Authenticated begin captures/validates the scope; policy fingerprints still read. |
| Manager zero-token pull | Repeated source and policy context after `ExactToken.pull(...,0)` | Zero returns before any token call. Nonzero pulls retain the complete proof. |
| Manager final context | Complete source validation immediately before `endManagerExecution` | Policy/venue/spot checks remain; authenticated end performs the complete final proof after all refunds. |
| Pricing `endEntry` | Complete source validation before read-only final basis checks | Captured basis/policy checks remain; `endExecution` performs the complete final proof before clearing the context. |

The omitted calls used 1,169,830 gas in that historical trace, including the
zero-pull policy read. This attribution is **not** a measured net saving or
proof of a 20M maximum-state transaction. Warmness and changed control flow can
change the actual saving. No nested read-only duplicate beyond these concrete
sequences is claimed.

The public `Manager.balanceContext` continues to validate sources. Nonzero token
pulls, external venue execution, swap settlement/refund callbacks, factual LP
checks, Vault approval/reset checks, intermediate contribution NAV checkpoints
and final Entry approval-reset proof remain protected. Emergency masks preserve
their separate, existing semantics.

## Normal construction

The exact two-file source state was compiled with the trusted 100-source closure
and unchanged Solidity 0.8.26 settings. All 48 normal runtime/initcode gates pass;
all 48 semantic ABIs and storage layouts match the prior build. Source bytes
were stable during compilation. No Foundry configuration was changed.

| Object | Runtime bytes | Runtime headroom | Relevant change |
| --- | ---: | ---: | --- |
| LiquidityManager | 24,537 | 39 | +62 runtime/creation bytes |
| ContributionPricing | 20,643 | 3,933 | +15 runtime/creation bytes |
| Oracle | 24,573 | 3 | Runtime unchanged; embedded Pricing increases creation by 15 bytes. |

Oracle creation plus its fixed 64-byte constructor arguments is 49,088 bytes,
leaving 64 bytes below the 49,152-byte initcode limit. Manager creation plus its
192-byte arguments is 48,437 bytes. These are this exact source stage's gates,
not qualification of future code or arbitrary constructor values.

See [exact normal-gate result](validation-reuse/normal/RESULT.json),
[source edit and original identities](validation-reuse/SOURCE_EDIT.json) and
[pinned historical call tree](validation-reuse/TRACE_PROOF.json).

## New boundary checks

Five new methods exercise the changed boundaries using actual local Uniswap v4
core/position-manager execution and the current accounting graph:

- Both swap directions reconcile exact quoted output and complete own-swap
  post-state, with public full-proof reads during actual refunds.
- A nonzero token pull triggers a separately funded trader's small independent
  market movement. Exact source-scope rejection must roll back balances,
  allowances, both market states and callback state; an unchanged healthy retry
  must succeed.
- A refund disables and re-enables the same source. The revision cannot revive
  the old scope; all swap/transfer effects and the revision must roll back,
  followed by a successful healthy retry.
- Full Entry activation changes a healthy same-value ETH round during the final
  approval reset. The final proof must reject it and roll back LP ownership,
  shares, fees, membership, royalty weight, balances, allowances and market
  state. A healthy retry must establish a funded active NFT.
- Standalone Manager swap changes the healthy same-value ETH round during its
  token pull, rejects and rolls back the transfer/allowance/source/market state,
  then proves exact healthy own-swap transitions in both directions.

All five distinct methods pass, with exact source/artifact identities in the
[case-level verification registry](validation-reuse/VERIFICATION.json). No
inherited unchanged method is selected, and no successful unchanged case is
rerun. The stages remain separate:

1. `boundary01` selected zero methods because an unrelated in-progress
   experimental test had a parser error. This is a retained compiler failure.
2. `boundary02` passed two cases and exposed two fixture errors: zero ZZZ input
   has no Manager ZZZ refund, because purchased tokens go directly from core to
   recipient. A Manager-refund hook therefore did not execute. No production
   fault was inferred from the invalid callback assumption.
3. `boundary03` passes only the two corrected fixtures plus the new standalone
   caller case. The previously successful two method bodies are reused exactly,
   with their earlier actual execution results.

The normal build and boundary checks are the two-file **pre-royalty-port** source
stage. While `boundary03` was compiling, the separately authorized royalty
allocator port changed two production files and its own test harness. The broad
before/after bracket correctly records this difference instead of claiming
global source stability. Producer metadata authenticates the exact compiled
pre-port closure, reconstructed from preserved source input and unchanged
files; compiler-text Keccak and filesystem SHA identities are recorded
separately because Forge normalizes CRLF to LF. Later royalty source must retain
its own normal-build and execution acceptance; these results do not silently
qualify it.

## Limits

The small boundary fixture has controlled ETH feeds, registry/admission, Permit2,
VRF and direct-mint transport. It proves neither mint2/OpenSea integration nor
maximum cohort/currency gas. The independent source pools are locally funded
controlled markets, not qualified production price feeds or liquidity. Root's
separate near-1,000-NFT cold-RPC experiment is the relevant activation feasibility
work. No live configuration, service, signer, chain, journal or website changes.
