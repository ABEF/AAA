# Audit coverage and behavior preservation

The candidate at initial main e32e966 is reviewed across all project layers.
Scope means source/call-path inspection plus explicitly stated execution,
not exhaustive state-space proof or a new complete suite. Detailed traces:
[principal](PRINCIPAL.md), [rights](RIGHTS.md), [services](SERVICES.md).

| Capability | Current intended behavior | Audit / new evidence | Result |
| --- | --- | --- | --- |
| Mint/reveal/traits | 1,000 ERC721,0.05ETH direct mint; random prepared design,600/300/100rarity quotas; dormant mint adds no LP | Actual NFT/VRF/metadata call path and analyzer; prior source-matched checks reused | Preserved source; real VRF/OpenSea NOT VERIFIED |
| Activation | ETH/fixed ZZZ contribution≥$100, captured2%default/≤10%caller ceiling, actual marginal LP | New current3 composition regressions fix dormant and native policy-call rejection | Regressed backend integration fixed; financial contract unchanged |
| Growth | Current owner, active NFT,≥$5input, exact approval and LP-attribution/price bounds | Composed native growth and fixed-ZZZ approval negatives; principal call trace | Preserved, valid preparation restored |
| LP custody/shares | Shared physical LP and independently accounted nonredeemable NFT shares, old fees/compound excluded from entrant allocation | Vault/Budget/Manager/Entry and callback traces; new full-capacity fault case | No new dilution bypass confirmed; real venue/gas assumptions open |
| Revenue | Funded80/10/5/5, one collective share per activated NFT; separate1/2/3rarity royalties | Fee/membership/ledger/converter traces and analyzer; earlier exact-source tests reused | Preserved; rounding/dust exceptions and source funding remain explicit |
| Transfer and claims | All unclaimed NFT rights follow current owner; owner rechecked across batch callbacks | Ledger/router/ERC721 and canonical transition traces | No new stale-owner/double claim confirmed; secondary seller may claim before sale |
| Royalty outages | Failed optional currency defers its new cohort without old receipt theft | New16simultaneous-gas-fault case checks success, deferred eligibility and recovery | Local composed pass; actual token/venue assumptions open |
| Earnings/history | Claims/conversions/returns are not new income, complete pinned history required | Real Rpc transport/SQLite regression restores independent chain-ID audit; prior native custody replay unchanged | Adapter integration fixed; live independent provider coverage unqualified |
| Compounding/rebalancing/ranges | Preset policy/keeper/cooldown, captured3%maintenance, attributed idle and actual LP checks | Principal/Strategy/Oracle and analyzer review | Source behavior preserved; repeated turnover/market/MEV/gas risks remain |
| Pool movement/custody exit | Same actual pair atomically, or trusted approved normal all-ZZZ/raw custody; exact return/backing | Migration/helpers/canonical trace and analyzer | Preserved; custodian may withhold, different-pair external handling is trusted |
| Complete same-chain handoff | Exact ownership/ledgers/backing, one canonical successor, funded abort | All six domains and codecs/cursors/roots/funding/terminal state traced | Preserved source; live provider/token/VRF/contract-holder liveness unqualified |
| Governance/pause/sealing | Direct trusted wallet, guardian pause, bounded keeper; fixed code/bindings at seal | Authority/module/canonical call traces and all47current static bindings | Preserved; no timelock/executor/hidden new authority introduced |
| Keeper/HTTP/indexer recovery | Bounded isolated work, verified log provenance, saved intent/receipt, no blind resend |31critical service files reviewed, no original state changed | No new additional bypass confirmed; hosting/outage/monitoring qualification open |
| Website/wallet | Simulation/publicnull, signing Anvil-only; matching source profile required | Six critical files read-only, actual native reader still2only | Current3 integration remains open/fails closed; no production signing enabled |
| Evidence/build/release | Exact source/dependency/compiler pins, normal limits, reviewed actual flags | Fresh399flag manual triage; fresh37size lengths match;265AST new test;11Python/1EVM | Current internal static gate passes; independent/full release approval remains open |
| Future unknown royalty currency at retired receiver | Admitted-only forwarding, no arbitrary rescue | Actual forwardLate and terminal canConfigure traced | Explicit unsupported case retained, not silently represented as solved |

No normal function ABI, storage slot, permission, economic split, custody right,
price policy or loss default changes. Three backend modules are corrected and
one new test-only fault mode is added. Fixed call/reference and old source
profiles/journals remain distinct. Broad testing of unchanged code is reused
only with its recorded hashes/conditions, not automatically promoted by this matrix.
