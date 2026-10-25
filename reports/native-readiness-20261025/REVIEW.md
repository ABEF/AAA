# Native integration, Vault headroom and service readiness

Baseline contract main `8cec66c98c673c4efbcc431ea4f13bccdb8a4733`;
website main `92c090beba3155cb7f1dbfd2093018cdc1ddc92e`.
**Production NOT APPROVED.** This is an internal scoped improvement/review,
not an independent audit or a completed production rehearsal.

## Implemented improvements

| Finding | Change and practical result |
| --- | --- |
| Vault had only57 runtime bytes available | Three private refactors share the exact swap/reset path, remove an always-true private flag and cache one immutable address locally. ABI/storage and external call order stay unchanged. Runtime24,263 leaves313 bytes under the normal gate. |
| Website assumed the old wrapper, fixed1% and Entry selector | Separate explicit schema2 now reads actual native ETH and current dual-price/reviewed-Entry versions. Exact runtime/parent/policy identities, upper-input loss floor and caller-bound calldata are checked. Schema1 preserves existing deployments; incompatible current data cannot silently downgrade. |
| P2: incomplete native reward rows could appear as a complete total | Native manifests and each native LP/royalty projection must contain ETH. Omission rejects the projection/claim instead of adding whichever ledger remains. |
| P2: per-NFT earnings bypassed the existing arithmetic validator | Reuse complete currency/raw/price/period validation before attaching history. Malformed history is unavailable; current LP is preserved. No change to ledger entitlements or the today's-price product decision. |
| RPC outages could falsely prove unknown-hash support | Only explicit recognized missing-block remote errors count. Timeout, rate-limit, invalid-parameter and ambiguous failures remain failures. Sanitized typed metadata preserves the distinction. |
| Accepting withLog did not prove actual event traces | Optional preparation profile simulates exact approve(0) with no persistent state or override and checks its real log witness at the same confirmed hash, with reviewed identity pins. This is a capability test, not financial or provider approval. |

The native interface and display changes are applied to website source locally
after explicit user permission. Public DEPLOYMENT is null; the shared browser
signer, client and transaction coordinator are byte-identical. Only Anvil signing
remains available. The public server and existing local dist/chain/journals are
unchanged. [Operator procedure](../../docs/NATIVE_WEBSITE_PROFILE.md).

## Decisions and retained limits

No economic rights, royalty weights, custody authority, loss defaults2/1/3%,
hard10% maxima, immediate governance or gas separation changed. No proxy,
delegatecall, new deployed helper, arbitrary executor, sweep, bridge or holder
principal redemption was introduced.313 bytes remains limited headroom; reducing
bytecode does not establish gas-optimal execution or semantic equivalence.

Do not migrate existing local runtime/journals by changing manifest versions.
The new profile requires actual current Entry/Pricing/Oracle/Budget bindings.
It supplies no newly qualified production addresses, input/fee-conversion routes,
prices or randomness. Caller-bound loss approval does not remove trusted
governance/dependency risk.

## Actual service observations and external gates

The user separately authorized bounded read-only public RPC checks. At the saved
observation, documented Pinax passed11 basic keeper-profile checks; Robinhood's
public endpoint returned HTTP403 from this environment. This is point-in-time
compatibility, not redundant-provider approval, archive completeness, throughput,
uptime, finality or actual preparation tracing. Independent explorer identity
corroboration also returned403; the identity-pinned approval-trace profile was
therefore **not run** against a public provider. No guessed/self-approved pins.
Read [the precise public observation](../real-service-readiness-20261025/public-rpc/README.md).

[Official-source research](../real-service-readiness-20261025/RESEARCH.md)
still does not select two genuinely independent ZZZ/USD sources, compatible
proof-verifying VRF, actual authorities, real conversion/input routes or a
custom OpenSea primary-mint path. Marketplace chain support is insufficient.
Public basic reads do not qualify private API/keeper hosting or recovery.

Remaining work is actual native chain/extension and preparation-service rehearsals,
qualified feeds/routes/VRF and chain-policy inputs, authority selection, permanent
content, OpenSea, strategy economics/full target-chain gas, operating recovery,
frozen-release verification and independent audit/remediation/sign-off. Keep them
open in the [sole Todo](../../TODO.md); no duplicated task ledger is created.

## Evidence and publication

[Verification](VERIFICATION.md) distinguishes final versus earlier source scope,
meaningful negative controls, mock boundaries and deliberate reuse. The internal
cross-review found both display issues before final application. It is not an
independent external audit. Read Git and the separate publication receipt for
what is committed/pushed; local application and deployment are different facts.
