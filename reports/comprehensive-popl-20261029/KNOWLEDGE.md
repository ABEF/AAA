# Applied knowledge and dependency review

Research informs specific inspected boundaries; no framework certification or
blanket state-of-the-art/security claim follows. Local implementation/locked
versions take precedence over examples for a newer library.

| Primary material | Applied here | Limitation |
| --- | --- | --- |
| [Solidity0.8.26 security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html) | External calls, bounded loops, checks/effects, atomic rollback and ownership/custody separation. | General guidance does not validate economic correctness or this compiler's every transform. |
| [Official compiler bug database](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json) | Match introduction/fix/settings/necessary patterns to pinned0.8.26/Cancun/viaIR/Yul-optimizer-disabled build. | Retrieved advisory scope, not immunity to unknown/later bugs. |
| [Uniswap v4 flash accounting](https://developers.uniswap.org/docs/protocols/v4/concepts/flash-accounting) and installed source | Unlock/callback deltas, exact native settlement, directional fees, physical position identity and quote execution. | Mocked runtime admission is not actual Robinhood qualification. |
| [Python3.11 SQLite](https://docs.python.org/3.11/library/sqlite3.html) | Stored integer chronology and actual temporary DB reader reproduction. | Schema/host backups and live provider authenticity need separate acceptance. |
| [Python3.11 OS files](https://docs.python.org/3.11/library/os.html) and [I/O](https://docs.python.org/3.11/library/io.html) | Exclusive create, owned handles, fsync before/after evidence, failure retention. | Windows skipped pathname/symlink cases; arbitrary filesystem/power-loss durability is not proven. |
| [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html) | Existing source watchdog/recovery and controlled rollout boundaries. | Host version, process-group behavior and supervisor installation not exercised here. |
| [EIP1898](https://eips.ethereum.org/EIPS/eip-1898) | Canonical block-bound state reading and finality/receipt chronology. | RPC conformance/authenticity and actual provider latency remain unqualified. |
| [OWASP ASVS5.0](https://asvs.owasp.org/) | Input/data integrity, operation authorization, dependency/configuration and failure diagnostics. | Relevant service controls adapted; nonexistent password/session/AI subsystems not invented. |
| [NIST SSDF1.1](https://csrc.nist.gov/pubs/sp/800/218/final) | Source/evidence provenance, dependency inventory, reproducible review and release separation. | Not independent audit or formal SSDF certification. |

## Compiler applicability and fresh generated artifacts

The [source advisory screen](contracts-compiler-advisories.json) records actual
settings, requires, internal-call inventory and source pins. Named optimizer,
legacy-only or later-introduced conditions are not blindly treated as applicable.
For SOL-2026-2/-4, a separate outputSelection-only compile preserves all78sources,
settings and39creation/runtime bytecode objects exactly, then inspects original
and optimized structured Yul object graphs. The [final follow-up](contracts-compiler-generated-followup-FINAL.json),
[independent graph review](compiler-analyser-independent-review.json) and
[fixture-scope correction](compiler-analyser-fixture-scope.json) record no
mutual-recursion witness in those exact artifacts. The failed initial zero-count
parser is preserved and excluded; independent raw counts cross-check traversal.

Eight synthetic analyzer probes are helper checks, not contract passes. Some
stress shapes are not compiler-accepted Yul programs; do not present them as
language-valid examples. The AST is produced by the compiler under review and
later backend correctness is not independently proven. No silent toolchain
upgrade or compiler-safety PASS is claimed. A frozen release still needs reviewed
compiler/dependency sign-off and refreshed actual static analysis/triage.

Full primary-source links, source locators and limitations are retained in
[contracts research](contracts-research.json), [operations research](operations-research.json)
and [backend research](backend-review.json). Direct web-tool reads of public
sites were unavailable; that is not evidence the sites are down. Source/readme
inspection is not a browser/extension/host/provider operating rehearsal.
