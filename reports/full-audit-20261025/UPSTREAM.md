# Upstream applicability follow-up

Fresh primary-source reads consulted the [current Solidity bug catalogue](https://raw.githubusercontent.com/ethereum/solidity/develop/docs/bugs.json),
[OpenZeppelin advisories](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories),
[v4-core security](https://github.com/Uniswap/v4-core/security) and
[v4-periphery security](https://github.com/Uniswap/v4-periphery/security).
The versioned0.8.26 bug page alone omits later disclosures; the current catalogue
is required for review. Its listed2026families match the earlier same-day triage.

Pinned0.8.26/Yul-disabled excludes the2026-7optimizer condition; viaIR excludes
2026-5legacy generation;2026-1/3start after this compiler.2026-2/4need mutual
recursion and2026-6needs named custom-error require arguments. The unchanged
production/dependency closure retains [source-bound graph evidence](../deep-cleanup-20261025/UPSTREAM.md)
excluding those source patterns. This is conditional source triage, not proof
about all generated compiler helpers. Storage-boundary and final compiler review
remain open. No compiler/dependency upgrade was performed.

The official [Bytes advisory](https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories/GHSA-9rcw-c2f9-2j55)
lists5.4.0as patched; that version is pinned. The checked v4security pages show
no published advisories; absence of published entries is not proof of safety.
Actual deployed dependency runtimes, compiler versions, proxy/admin controls and
selected venue remain separately unqualified. Source package versions do not
identify the code running on Robinhood. Production NOT APPROVED.
