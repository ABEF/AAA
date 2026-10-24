# Internal review: typed conversion and governed loss limits

2026-10-24. This is an internal source review and scoped local verification,
not independent audit or permission to use public funds. Publication is recorded
separately. Earlier reports retain their original source scope.

## Reviewed changes

- Parent-bound hookless static single-hop v4 execution, exact settlement,
  authentication, source/native prefunds, forced ETH, partial fills and callbacks.
- Entry owner/context/original-source-to-LP accounting, exact user approval and
  native value, preserving distinct v3 descriptors and route identities.
- Already-earned LP/royalty source-to-ETH conversion without changing ledger
  entitlement, funding, allocation or current-owner claim rules.
- Immediate governance limits with 1% / 1% / 3% defaults and hard 10% maxima,
  rounded floors, captured operation policies and frozen custody approval floors.
- Explicit preparation/keeper/reporting version boundaries and failure behavior.
- Normal creation/runtime limits and size-driven read-only validation extraction.

The executor/Entry/converter and final backend were independently read by another
project agent. The final Budget/VaultCanonical/Migration policy delta received a
separate read-only review by an agent who did not implement it. No concrete
blocking issue remained in those reviews. Review is not a guarantee of no bugs.

## Findings and resolutions

| Concern | Resolution and retained boundary |
| --- | --- |
| v3 router calls cannot execute native v4 settlement | Separate immutable typed executor with parent-only authority and fixed output recipient; no arbitrary router/call/recipient/hook surface. |
| Native payment can inherit stale ERC20 sync state or forced balances | Explicit core sync even for native; exact debt/settle/take and authenticated receive counters; all prefunds preserved. Short/extra/forced output and partial input revert. |
| Conversion pools could accidentally become principal/reward pools | Policy lives only in the parent executor, independent from LP Registry admission and one-contribution-pool control. |
| Old route IDs/configs could be reinterpreted | Explicit route kind, chain/executor/parent/full-policy domain, routing version 2, worker profiles and reporting schema 2. Historical fixed-v3/fixed-cap profiles remain strict. |
| A cap change could weaken work already in progress | Packed early contribution cap, cached maintenance policy/price vector and absolute normal custody approval floor. Caller minimums and separate venue checks remain stronger guards. |
| Governance cap setters increased Vault embedded creation beyond the ordinary limit | Compact shared Budget setter plus extraction of existing read-only owner/contribution validation into the already-bound VaultCanonical. New views accept only the fixed Vault's actual Budget; no codec, custody funding, write or transfer authority changed. Normal limits were retained. |
| Backend could prepare approval for an unsupported signed settlement amount | New v4 amount bound rejects before approval or trace. Exact approval and mandatory fresh LP review remain. |
| Worker instructions used the wrong helper key | Documentation corrected to LP/royalty-specific contract/code-hash pins; generic v4_executor belongs only to activation configuration. |
| New events might erase historical decoding | Existing 119 descriptors retained exactly; six appended. Historical descriptors do not authorize retired modules. |

Initial policy tests exposed fixture sequencing errors, which are recorded with
their repaired scope. The first size candidate was rejected before publication.
No full unchanged regression was repeated for presentation; final evidence
distinguishes focused reruns and reused cases.

## Material trust and remaining work

Governance can immediately authorize a ceiling as high as 10%; this permits more
economic loss and gives users no advance-warning delay. Keep conservative defaults
unless an explicitly reviewed change is justified. No cumulative loss breaker is
added. Venue deviation/slippage, caller minima, five-percent idle and actual
funding remain independent restrictions; increasing a ceiling does not guarantee
execution or protect against impermanent loss.

Pins prove identities, not safety. Actual manager/StateView/token runtimes,
liquidity, independent feed quality, current directional fees, RPC/trace support,
complete gas costs, monitoring and keeper behavior require target-chain
qualification. At default 1%, the selected approximately 1.101%-fee pool remains
unsuitable for full-balance reward conversion at reference prices. No route or
automatic cap increase is invented.

Native website/release inventory, atomic ETH/WETH principal transitions, OpenSea
primary mint, real service operation, future-chain handoff and independent audit
remain open. The controlled raw custody path still trusts its recipient and may
be blocked by unavailable venues or nontransferable assets.

No public transaction/deployment, private-key use, website source/build/server,
existing Anvil/NFT/LP/journal, signer-policy or monitor change occurred. Public
DEPLOYMENT remains null; shared signer remains Anvil-only; production NOT APPROVED.
