# Knowledge and method selection

Reviewed2026-10-29. Primary references were read to answer specific project
questions. They inform review criteria; they do not qualify this deployment,
prove provider honesty or authorize changing project decisions. Installed package
implementations/pins take precedence over a newer online example.

| Knowledge / primary reference | Application and limits in PoPL |
| --- | --- |
| [Solidity0.8.26 security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html) | Review external/native callbacks, state ordering, arithmetic and bounded loops. Keep the pinned compiler/Cancun/profile; do not infer that latest documentation requires an unreviewed compiler upgrade. General callback guidance does not justify removing isolated bounded payouts or their reentrancy guards. |
| [Official compiler bug predicates](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json), [version applicability](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs_by_version.json) and [binary manifest](https://binaries.soliditylang.org/linux-amd64/list.json) | The [compiler screen](COMPILER_DEPENDENCIES.md) checks current settings and77-source AST, records unresolved lowering proof and checksum-pins CI. It neither upgrades the compiler nor replaces release applicability review. |
| [OpenZeppelin maintainer advisories](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories) | Compare imported code/version with actual predicates, including Base64; a newer upstream release or known patched advisory is not complete downstream security certification. |
| [OWASP SCSVS](https://scs.owasp.org/SCSVS/) | Map architecture, economic logic, authorization, communication, arithmetic, availability and operations to actual components. A checklist row is not an execution result or certification. SCSVS's data-state category does not require reintroducing an integrated bridge. |
| [Uniswap v4 unlock and deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas) | Check actual callback identity, negative/positive currency obligations and complete settlement against installed v4-core1.0.2/periphery1.0.3. Route quotes, native sync, refunds, PoolKey/ticks and directional fees require implementation review, not a generic50/50 swap assumption. |
| [ERC-721](https://eips.ethereum.org/EIPS/eip-721) | Ownership, approvals, safe-transfer receiver callbacks and event semantics. Transfer approval does not grant PoPL reward-claim rights. A receiving address may execute code; no EOA-only safety assumption. |
| [ERC-2981](https://eips.ethereum.org/EIPS/eip-2981) | Royalty recipient/amount is information; actual eligible receipts fund PoPL's separate ledger. It does not make every transfer a sale or universally enforce marketplace payments. |
| [ERC-4906](https://eips.ethereum.org/EIPS/eip-4906) | Check metadata notification interface and hashed-ID/ordinal batches. Notifications aid marketplace refresh; actual cache behavior still needs marketplace qualification. |
| [VRF2.5 security guidance](https://docs.chain.link/vrf/v2-5/security) | Review original request matching, confirmation choices, callback work and absence of reroll/cancellation. An ABI-shaped mock or these docs do not establish a supported Robinhood coordinator, billing/subscription policy or real recovery service. |
| [EIP-1193](https://eips.ethereum.org/EIPS/eip-1193), [EIP-6963](https://eips.ethereum.org/EIPS/eip-6963) | Treat provider/account/network events and multi-wallet discovery as untrusted inputs. UI-selected accounts and accounts exposed to a dapp are distinct. Do not invent permissions, evaluate provider icons as code, or silently switch signers. Public signing remains deliberately disabled. |
| [EIP-1474](https://eips.ethereum.org/EIPS/eip-1474), [EIP-1898](https://eips.ethereum.org/EIPS/eip-1898) | Use canonical wire values, checked response envelopes and block-hash selectors with canonicality. Provider conformity/support must be tested; canonical syntax and node assertions are not consensus or log-completeness proof. Historical wallet responses need explicitly reviewed compatibility, not arbitrary coercion. |
| [Python3.11 sqlite3](https://docs.python.org/3.11/library/sqlite3.html), [SQLite backup API](https://www.sqlite.org/backup.html) | Review transaction boundaries, one-writer/reorg guards and consistent backups. A lone live DB file copy does not establish a consistent WAL snapshot; current filesystem/host/fencing behavior still needs rehearsal. |
| [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html) | Check installed-version-compatible watchdog ownership, restart and failure semantics. Latest online262 documentation is not proof of the required actual host version, loaded unit or process-group cleanup. No source review installs a service. |
| [WCAG2.2 quick reference](https://www.w3.org/WAI/WCAG22/quickref/) | Review keyboard/focus, dialog meaning, status announcements, responsive text, color-only cues and motion/audio controls in financial flows. Static code/tests do not certify visual accessibility or real browser-extension acceptance. |

## Available skills and tools

The available skills cover image generation, computer use, documents, pages,
slides/sheets, sites, plugin management and related artifact work. None is a
repository-specific security-audit skill. This source audit uses native Git,
source/ABI/dependency inspection, bounded local Python/Node fixtures and existing
source-bound compiler/EVM evidence. No new plugin, paid service or image
generation is needed to preserve the current artwork or audit the source.

If a later verified need calls for interactive browser/native inspection, read
and announce the computer-use skill before using it. Such a skill does not
override wallet, environment, deployment or signing boundaries. Do not claim a
browser exercise when only synthetic DOM/provider fixtures ran.

## Critical application rule

For every borrowed recommendation, record its actual component, version,
threat/precondition, expected benefit, regression/cost tradeoff and evidence.
Keep unknown external facts unknown. Do not turn general best practice into a
mandatory new role, timelock, custody path, economic policy or unavailable service.
