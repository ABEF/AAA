# Production readiness reconciliation and verification plan

19 November 2026. Source baseline: `4fde8d63b54dadc0d87cb2ba4d2af0d5da8e1527`.
**Production remains undeployed and NOT APPROVED.** This is a readiness analysis
and documentation change, not a new dynamic audit, deployment rehearsal or
permission to deploy, seal, sign or open funds.

## Result

The [maintained roadmap](../../docs/ROADMAP.md) now supplies 23 concrete
acceptance packages and an ordered six-gate plan. The [coverage matrix](MATRIX.json)
maps all 83 stable Todo tasks, all 17 contract/internal and seven service
workload families, and all 21 service subfamilies containing 85 finer partitions. Existing scenario
requirements remain in the source-pinned workload plan; mapping them is not
claiming their execution. The sole Todo owns statuses; no task was marked done
or reopened by this planning review.

The order is: **launch scope and real external feasibility → missing source,
accounting and resource proof → frozen candidate and independent review →
separately authorized closed/unsealed deployment → separate seal and closed
integration acceptance → separate public opening and continuing operation.**

Deployment, sealing and launch are different decisions. Actual receipt/runtime/
immutable/binding readback cannot be obtained before deployment. Some final
marketplace/provider/wallet observations require deployed or sealed contracts;
that does not justify opening public mint or deposits before those gates pass.

## Method and scope

First built an independent checklist from the protocol's economic flows,
authority boundaries, lifecycle, moving markets, resource limits, data paths,
irreversible setup and long-term failure/recovery needs. Then reconciled that
list with current repository instructions/context/READMEs, Todo, release record,
operator procedures, workload map, consolidated finding dispositions and latest
source-scoped reports. Three parallel read-only reviews covered contracts and
accounting; services/site/history/operation; and real markets/chain/providers.

This is a targeted source/evidence reconciliation, not a new claim that every
source line or historical report was independently audited again. Historical
310-record review and the later 64+24 reconciliation retain their own individual
assessments and immutable evidence. Resolved defects, accepted choices,
structural limits, unverified inputs and actual release obligations are distinct.

Source provenance in MATRIX.json identifies the pre-edit documents at the
baseline; current documentation naturally changes in this commit. Old reports,
production code, compiler settings, profiles, defaults and unrelated drafts are
preserved. The website was inspected read-only at main
`2183e1ac676e4eb7d7ccac6dc0ce597c419aef0c`; no website source or environment changes.

## Material gaps made explicit

| Gap | Why it matters / next proof | Plan owner |
| --- | --- | --- |
| Actual market feasibility | No approved independent ETH/ZZZ source pair or complete compatible bidirectional route is established. Dated forward quotes and synthetic depth are not release markets. Review real token/admin controls and post-withdraw depth before another broad campaign. | P03–P04; existing Q01 |
| Production user submission | OpenSea covers mint, not activation/growth/claims. Source10 is read/unsigned only and never constructs the Anvil-only shared signer. Choose a separately reviewed submission approach; this review does not authorize extending that signer. | P19; existing Q06 |
| Current compiler advisories | Pinned optimized via-IR 0.8.26 must be assessed against the current official advisory registry, including disclosures later than earlier applicability reviews. A version hit is not a confirmed reachable PoPL defect. No compiler change made. | P02; dependencies / audit-release |
| One maximum-state gas refusal | Slow64-currency opening ZZZ estimates 27,142,801; full20% gives 32,571,362 against32M. At least476,135 estimated gas reduction remains. Preserve the refusal and padding; approving a smaller launch envelope does not qualify future expansion. | P06; existing Q03 |
| Cold claims, canonical and actual control graph | Previous producer uses mocked control seams; cold LP conversion/claim batching, complete latest F6 coordinator/import/abort and fresh F6 constructors require their own evidence. Passing body/companion tests does not prove the full graph. | P06/P08/P13/P22 |
| Large-wallet completeness and freshness | Backend can verify63 pages for1,000 NFTs; website adoption is missing. Qualify all pages plus summary/history against actual freshness/rate/provider bounds, or explicit partial/unavailable results. Individual-page passes do not establish usable full-wallet latency. | P17–P19 |
| Real operating composition | Inert recovery-only Linux tests do not establish normal daemon/Cast/key/provider scheduling, off-host restore/fencing, alert delivery or sustained operating acceptance. Changed checkpoint semantics require reviewed rebuild/re-pin on adoption. | P18/P20/P21 |
| Irreversible setup and platform support | Artwork, fixed ZZZ/venue graph, LP converter, SeaDrop helper/singleton and initial VRF require complete pre-seal review. Generic seal does not validate the selected launch graph. Actual OpenSea/VRF support and fee/funding terms remain inputs. | P11/P14–P16/P22 |
| Long-term operability | Currency and bucket lifetime capacity, faulty tokens, rejecting receivers, unanswered draws, upstream upgrades, lost keys, archive growth and gas funding have real limits. Specify responses without promising impossible universal payouts/recovery. | P09/P12/P13/P15/P18/P21/P23 |
| Dependency-qualified late fee netting | Preserve the unresolved callback reachability question from the [earlier contract review](../daily-reconciliation-audit-20261111/contracts/REVIEW.md). Inspect actual fixed-ZZZ/Permit2/PositionManager powers first; ordinary external swaps cannot interleave inside an atomic transaction. This is not a newly demonstrated exploit. | P04/P07/P08 |

These rows are planning gaps/qualification obligations. They do not convert every
remaining item into a code defect or imply that the current source is approved.

## Documentation corrections

- Replaced the roadmap's chronology with the dependency-ordered qualification
  plan, concrete acceptance criteria, owning Todo links and explicit launch gates.
- Extended acceptance criteria under five existing tasks: independent release,
  dependency review, wallet submission, complete portfolio reads and deployment.
  Stable task IDs, statuses and economic requirements remain unchanged.
- Corrected future RPC-capacity guidance in the operator manual to selected
  **32M/full20% contributions and24M/full25% maintenance**. Historical20M reports
  remain historical; no budget/default/configuration was raised or adopted.
- Clarified current source limits: **four LP execution venues**, four lifetime
  buckets, at most two physical positions per bucket. The original maximum-state
  report's “32 venues” phrase remains preserved; it does not override source.
- Linked the plan from README, documentation/findings/evidence/release maps,
  operator manual and repository context/handoff/instructions. One maintained
  operator guide and one central Todo remain; no operation signature changed.

## Research boundary

Official current references consulted for qualification requirements include
[Solidity known bugs](https://docs.soliditylang.org/en/latest/bugs.html),
[Robinhood Ethereum differences](https://docs.robinhood.com/chain/differences-from-ethereum/),
[fees](https://docs.robinhood.com/chain/gas-and-fees/),
[finality](https://docs.robinhood.com/chain/transaction-finality/),
[Arbitrum gas estimation](https://docs.arbitrum.io/arbitrum-essentials/how-to-estimate-gas)
and [Chainlink source selection](https://docs.chain.link/data-feeds/selecting-data-feeds).
Documentation identifies checks; it is not actual RPC/chain/provider acceptance.
No public RPC probe was run in this review. Compiler-advisory reachability was
not evaluated here; P02 explicitly schedules that work before final freeze.

## Verification and unchanged boundaries

See [the documentation verification record](VERIFICATION.json) for Todo generation,
complete task/family mapping, changed Markdown links/anchors, status preservation,
source hashes and Git scope. These are document/integrity checks, not application
tests, Solidity execution or operating acceptance. No unchanged suites were rerun.

No production Solidity/Python/browser implementation, compiler, financial guard,
authority, signer, old report, existing Anvil/DB/checkpoint/journal, hosted site,
service or user-paused heartbeat changes. No signing, public transaction,
deployment, seal or real-fund campaign was performed. Actual release status
remains in the [NOT APPROVED record](../../docs/RELEASE_CHECKLIST.md).
