# Upstream and compiler applicability - 2026-10-25

Installed versions are OpenZeppelin 5.4.0, v4-core 1.0.2, v4-periphery 1.0.3 and
forge-std commit 77041d2ce690e692d6e03cc812b57d1ddaa4d505. See
[baseline](BASELINE.json), the three component reviews and the final closed
compiler-input hashes. No dependency or compiler upgrade was performed.

## Guidance applied to actual paths

- [Solidity 0.8.26 security](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html):
  native and token calls can transfer control. Callback authentication, exact
  deltas, accounting checkpoints and lifecycle guards remain; repeated reads
  across external interactions were not deleted merely for brevity.
- [Solidity storage layout](https://docs.soliditylang.org/en/v0.8.26/internals/layout_in_storage.html):
  compare recursive inheritance/struct slots and offsets rather than infer
  compatibility from unchanged field names or contract counts.
- [PositionManager](https://developers.uniswap.org/docs/protocols/v4/guides/position-manager)
  and [unlock/deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas):
  verify typed action encoding, payer/recipient and complete settlement against
  installed core/periphery. The new native fixture uses actual core/PosM/StateView;
  its Permit2 allowance seam and mocked admission/prices are explicit limitations.
- Core is not proxy-upgraded and the selected pool is hookless. Upgradeable-core
  initialization and custom hook implementation guidance are not incidental
  cleanup requirements. External dependency proxy/admin reviews remain relevant.

## Current compiler notices

The [official current bug catalogue](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json)
was consulted in addition to versioned documentation. Applicability is conditional:

| Notices | Actual candidate condition and treatment |
| --- | --- |
| SOL-2026-7 | Requires Yul optimization; this build explicitly disables it. |
| SOL-2026-6 | Named custom-error arguments in `require`; none found in the reached source closure. |
| SOL-2026-2, SOL-2026-4 | Mutual internal recursion; final context-aware graph finds no internal cycle. Disabling Yul optimization alone would not exclude them. |
| SOL-2026-1, SOL-2026-3 | Introduced after pinned 0.8.26. |
| SOL-2026-5 | Applies to legacy code generation; this candidate uses viaIR. |
| SOL-2025-1 | Storage-end wrapping conditions remain part of frozen compiler/source review; no custom near-end layout is introduced by this cleanup. |

[Final graph evidence](rewards-callgraph-summary.json) binds 265 explicit inputs,
31 concrete roots, resolved internal dispatch/modifiers and reached dependency
bodies. It records zero internal cycles, unresolved internal calls and named-error
`require` triggers; 51 distinct assembly scopes have no user-defined Yul functions.
Source initialization and virtual-modifier scope are recorded. Invalid compiler
output is rejected, with the actual failed AST used as a negative control.
This is source-level applicability triage, not a proof about every compiler-
generated helper, optimized opcode, EVM behavior or future compiler release.
External callbacks require their separate economic/reentrancy review.

The [core](https://github.com/Uniswap/v4-core/security/advisories) and
[periphery](https://github.com/Uniswap/v4-periphery/security/advisories) advisory
pages exposed no published entries during this read. This does not establish
absence of upstream vulnerabilities. [OpenZeppelin advisories](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories)
are checked against actual imported files rather than treated as instructions
to upgrade unrelated modules automatically.
The [Bytes.lastIndexOf advisory](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories/GHSA-9rcw-c2f9-2j55)
lists 5.4.0 as patched; this candidate already pins 5.4.0. That one check does not
replace review of every imported dependency or later advisory.

The final release still needs independent compiler/dependency review, exact
artifact/constructor qualification, current service and venue qualification,
operating/gas rehearsals and independent audit/remediation. Production NOT APPROVED.
