# Compiler and dependency applicability

Current solc0.8.26/Cancun/viaIR/runs1/Yul-optimizer-off settings and77-source
production closure remain unchanged. An AST-only compile reused the exact
previous input only after comparing every content/hash to the current checkout.
It found1124function/modifier nodes, four ordinary one-argument dependency
`require` calls and no declared-internal mutual-call SCC. This is not bytecode
execution, virtual-dispatch/generated-Yul proof or compiler certification.

The official [version-to-bug list](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs_by_version.json)
and [bug predicates](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json)
were checked on2026-10-29. Applicability screening for the six listed0.8.26 bugs:

| Predicate | Current evidence / limit |
| --- | --- |
| Yul optimizer stale bookkeeping | Requires Yul optimization; current setting is false. |
| Named custom-error parameters in require | The four AST require sites each have one argument; no custom-error invocation there. |
| Memory byte-element delete | Legacy pipeline predicate; current code uses viaIR. |
| Two mutual-recursion spill bugs | No declared-internal mutual cycle found. Full generated/virtual call-graph qualification remains a release-review item; this screen alone cannot exclude every lowering case. |
| Storage-boundary array clearing | No deliberate wraparound layout found; bounded arrays/ordinary hashed storage give no demonstrated reachable trigger. Not a mathematical proof against arbitrary storage collisions. |

No compiler upgrade, optimizer/gas/size gate change or unsupported claim of
“bug-free compiler” follows. Before freezing release, retain an explicit compiler
applicability sign-off or qualify a newer compiler, rebuilding all exact artifacts
and consumers. Old test success cannot by itself answer compiler advisories.

OpenZeppelin5.4.0's relevant published [Bytes advisory](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories/GHSA-9rcw-c2f9-2j55)
lists5.4.0 as patched; the [Base64 advisory](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories/GHSA-9vx6-7xxf-x967)
is patched from5.0.2. This scoped inspection is not a complete dependency
vulnerability attestation. The exact OpenZeppelin/v4-core/periphery/Permit2
implementations, lockfile/integrities and unchanged bytecode evidence remain
separate from actual deployed token, pool, router and feed qualification.

The CI Linux compiler download is pinned to Solidity's official
[linux-amd64 manifest](https://binaries.soliditylang.org/linux-amd64/list.json):
`solc-linux-amd64-v0.8.26+commit.8a97fa7a`, SHA256
`d5f23436f443edb85d8e76906d12f0a86ce0490e7663a9e608efeb7a93f149ef`.
Checksum verification occurs before execution. The existing read-only runner
still independently checks version/profile/Forge identity. The download and
GitHub workflow were not executed during this source review.

Raw AST input/output, tool/source hashes and applicability screen are external
under `whole-project-audit-20261029/compiler`; they contain no wallet/provider
credentials. Scope limitations remain in the [review](REVIEW.md) and sole Todo.
