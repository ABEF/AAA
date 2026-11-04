# Whole-project audit and improvement supplement

November4,2026. Starting source: main e237aa72ec7fa09382d857ffab1a3fd96b286299.
**Production NOT APPROVED.** [Scope](AUDIT_PROMPT.md), [plan critiques](PROMPT_REVIEW.md),
[coverage/limits](COVERAGE.md), [verification](VERIFICATION.md).

This pass made two indexer improvements and corrected current cross-repository
guidance. Production Solidity, economic rights, configuration/runtime profiles,
services, websites, signer and journals remain unchanged. No public transaction,
deployment, sealing, local-chain reset or operating rehearsal occurred.

## Findings corrected

| ID | Finding and impact | Correction / evidence |
| --- | --- | --- |
| N04-01 | Low, history integrity: Indexer retained its caller's mutable configuration. Editing start_parent_hash after construction could change the first ingestion boundary or the full-history reorg anchor without changing the persisted configuration identity. An originally unanchored instance could also acquire an anchor this way. This is an in-process configuration-alias defect, not a demonstrated remote attacker exploit. | Snapshot the anchor once; validate nonnull hashes before opening/creating SQLite. Ingestion and reconciliation use that snapshot. Existing stored identity spelling/schema are unchanged. Negative controls reproduced bypasses; corrected actual-SQLite regressions verify rejection leaves the database/cursor/owner unchanged. |
| N04-02 | Performance/longevity: nft_owners materialized every historical Transfer with fetchall, although only current owners are needed. Memory grew with transfers and exceptional processing could retain a cursor. | Stream the SQLite cursor and close it in finally. Actual2001-row replay verifies current ownership, later transfer, burn and collection separation while forbidding full-result materialization. CPU remains proportional to scanned history; SQLite may sort. No maximum-history benchmark is claimed. |
| N04-03 | Operational documentation: current-looking website prose conflicted with fresh source: old accounting/custody/canonical labels,99% entry, removed input/bridge/creator architecture, dormant royalty trait0, old payout gap and old pattern name. Contract README navigation still called custody4 Entry3 evidence current. | Align both READMEs and maintained website/context instructions to accounting6/custody5/schema10/direct Entry3,2% contribution and ETH/ZZZ only, while retaining correctly named historical fixtures and current3 served site. Trait weight is distinct from eligibility; reward settlement source exists but actual services are unqualified. Existing catalogue name was checked against palette-system.js. |

**No new confirmed Solidity defect was established by this scoped pass.** Do not
interpret that as a clean independent audit or proof that every source path is
safe. Exact unchanged source permits reuse of earlier build/static/selected-EVM
evidence; it does not upgrade that evidence into new full coverage.

## A proposed fix deliberately rejected

Initial investigation considered resetting confirmation on a route-capability
metadata failure. The existing incident test and coordination policy deliberately
isolate unrelated routing telemetry from sampled price evidence. Resetting every
such failure would add liveness/gas cost without proving a bad price observation.
No keeper change was made. Genuine condition/clock/identity faults retain their
existing reset and pending-first recovery rules.

## Preserved policy and remaining decisions

- Governance/keeper/holder permissions, exact80/10/5/5 and separate received
  royalties remain. No contribution asset, economic parameter or emergency power
  changed. Collective exit stays perNFT/current owner, with governance-only
  direct batches and owner reward/fallback claims.
- Tight bytecode remains an engineering risk: unchanged Migration39-byte runtime
  margin, Budget237, Balancer360 and Vault635. No speculative extraction or build
  relaxation was introduced to claim extra headroom.
- Actual dual independent feeds, deep cheap routes, supported VRF/subscription,
  authority addresses, OpenSea primary-drop compatibility, permanent hosting,
  fresh-profile services/site, target gas and strategy economics remain open.
- Source-modeled sampled confirmation is not continuous price evidence or MEV
  immunity.60/40 is a selected tradeoff, not an optimized profitability result.
  Immediate governance/emergency trust, mutable external dependencies, rejecting
  recipients and complete chain disappearance remain explicit limitations.
- Streaming fixes Python materialization, not long-lived history architecture:
  authentic complete ingestion, replay CPU/storage, backups/restoration and
  operating qualification still belong to the existing Todo tasks.

## Actual verification and delivery boundaries

33distinct affected Python methods pass:27existing indexer regressions and6new
methods. The first negative-control campaign is preserved, including failure
subcases and a Windows cursor-cleanup error in the test wrapper. The wrapper was
corrected; no production safeguard was weakened. See the exact [record](VERIFICATION.md).

Both project READMEs/current guidance, the sole Todo, feature/evidence reference,
operator restart/recovery steps and repository memory are updated. Historical
report bytes, the four unrelated tracked dirty files and unrelated untracked
drafts are preserved. Source publication does not change running environments.

## Research basis

The [Solidity advisory list](https://docs.soliditylang.org/en/latest/bugs.html)
and [versioned security guidance](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html)
were consulted against the pinned build. Prior AST/settings applicability remains
source-scoped, not compiler correctness proof. [OWASP SCSVS](https://scs.owasp.org/SCSVS/)
supplies broad coverage categories; it does not certify this project.

[Uniswap flash accounting](https://developers.uniswap.org/docs/protocols/v4/guides/flash-accounting)
and [fee collection](https://developers.uniswap.org/docs/protocols/v4/guides/managing-liquidity/collect-fees)
support the settlement/collection review. [Chainlink VRF security](https://docs.chain.link/vrf/v2-5/security)
supports request identity/order/no-reroll and funding considerations; it does not
prove provider support here. [OpenSea SeaDrop](https://docs.opensea.io/docs/seadrop)
requires its own compatible primary-drop integration; ERC721/direct mint alone
is not that integration. No provider addresses or operating readiness are inferred.
