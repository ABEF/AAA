# AAA / ZZZ PoPL project instructions

Read [README](README.md), the [current review](reports/CURRENT_REVIEW.md),
[findings](docs/AUDIT_FINDINGS.md), [sole Todo](TODO.md), [roadmap](docs/ROADMAP.md)
and the relevant [operator procedure](docs/OPERATOR_MANUAL.md) before changing behavior.
This is an undeployed production candidate; production is **NOT APPROVED**.

## Workspace, authorization and preservation

- ABEF/AAA is this checkout. ABEF/AAA-website is `../../aaa-website`.
  Use **main only**. Inspect Git status before edits/staging; preserve unrelated work.
  Verify local and remote heads before claiming publication.
- Source/documentation publication does not authorize public transactions,
  deployment, sealing, website rollout, service adoption, local-chain reset or
  signer/configuration changes. Obtain separate explicit authorization for those actions.
- Preserve Anvil8902, NFT/LP/balances, pending/nonce/receipt/spend journals, locks,
  dist overlay, existing services and sites. Never relabel old profiles/runtimes
  or rewrite a journal, checkpoint or old evidence to satisfy new source pins.
- Popldemo is simulation; recorded served poplint/current3 is a separate older
  read/unsigned build. Fresh source9/V9 and source10/mint2/V10 are separate
  consumers. Use [the environment map](docs/SITE_ENVIRONMENTS.md). Missing actual
  configuration is unavailable data, never demo fallback. Public DEPLOYMENT stays
  null and browser signing **Anvil-only**, as explicitly selected by the user.
- The desktop staging heartbeat is **user-paused**. Do not resume it implicitly.
- Never print/log/commit keys, passwords, keystores, credentialed endpoints or raw
  operational configuration/recovery packages. Keep signer recovery separate.
- Archive relevant dirty documentation before consolidation. Do not stage unrelated
  untracked drafts or modify these four unrelated tracked dirty files:

| File | Preserved SHA-256 |
| --- | --- |
| `reports/source-checks.json` | `049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4` |
| `scripts/run-fork-checks.py` | `875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b` |
| `tests_python/test_fork_runner.py` | `6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9` |
| `tests_python/test_frontend_history.py` | `361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb` |

## Current implementation and required rights

- Fresh normal Solidity is the reviewed `activation-final-six-20261118` build:
  factory payload6/allocation2, accounting7/LP-allocation1, custody5, portfolio2,
  maintenance3, confirmation3, compound4, emergency2, direct Entry3/review2,
  pricing2/ProtocolPolicy1, immediate governance2 and fee-intake1. Mint2/schema17
  uses canonicalV10; explicit execution-price1 uses LP-routing3. Equal wire
  length is not compatibility. [Exact profiles](docs/POSITION_V7.md).
- Principal accepts native ETH and **one fixed ZZZ**. No USDG/USDC/WETH principal
  input, creator inbox, Power, timelock/executor, bridge or external custody exit.
  Wrapper support for a reviewed earned-fee conversion is a distinct purpose.
- Contributions checkpoint incumbents, use only entrant funds for actual added
  main LP, then issue NAV-priced shares. They do not recenter or reset rebalance
  clocks. Current default activation/growth minima are $100/$5; future governed
  minima and captured stronger caller/pool limits remain. [Entry](docs/ACTIVATION_ENTRY.md).
- Actual LP revenue is fixed80/10/5/5: individual shares/equal activated collective/
  compound/fixed-ZZZ buyback-burn. Exact whole-unit LP books support ETH and fixed
  ZZZ only. Engine phase is not a fractional monetary claim. Rarity affects only
  separately received royalties; dormant NFTs do not dilute activated membership.
- Royalties stay in their admitted original currencies, without royalty swaps.
  Preserve exact entitlement/outage cohorts, Commun1/Rare2/Legendary3 weights,
  one-hour sale-end activation window and explicit unallocated/zero-cohort rules.
  Reviewed capacity16→64 ERC20s plus ETH is not unlimited safe-token support.
- Default total contribution/conversion/maintenance losses are3%/1%/3%, each
  governed up to10%; additional loss after actual known fees defaults1%, agreement
  tolerance3%, gas separate. Preserve independent idle/caller/venue/funding floors.
- The user selected **spot** for both placement and independent valuation. Do not
  introduce TWAP automatically. Two ETH feeds through one ZZZ pool are not two
  independent ZZZ exposures. Qualify external depth excluding our LP and actual
  routes/fees. Final production-pool selection is operator-deferred. The recorded
  `0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`
  remains an isolated integration-test target, including explicitly synthetic depth.
- One contribution pool at a time, at most four historical/reserved logical
  buckets. A bucket owns one main and optionally ONE same-pool residual, both
  Vault-owned. Include both actual ranges in value/harvest/close; never sum raw L.
  Main≥60%/residual≤40% applies at replacement, not continuously. Residual width
  defaults to half the corresponding main side with a positive tick-spacing gap.
- Ordinary adjustment uses85% centre-to-boundary ZZZ-in-ETH distance and same-side
  independent corroboration, a600s sampled window/maxgap300s,240s source checks,
  hard initial12h and durable freshly drawn60–300s jitter. Faults/identity changes
  reset evidence. Operator geometry changes are a separate guarded exception.
- Extra compounding waiting remains **keeper software policy**, per user decision.
  Keep its independent interval, rebalance priority and hourly independent harvest.
  Only authenticated successful receipts coalesce collection clocks. No swap,
  canonical, conversion or operator action may silently borrow another's authority.
- One human operator controls governance. Keep the limited keeper gas key separate;
  governance can revoke/replace it. Explicit paused governance emergency bypasses
  may waive economic guards and risk severe loss; never make them automatic.
- Terminal collective exit is irreversible: governance closes all LP and pays
  actual ETH+ZZZ by NFT shares to current owners in bounded batches. Preserve
  transfers, old funded rewards and future royalties. No principal reopening or
  arbitrary custody beneficiary. Pre-exit same-chain canonical replacement remains
  separate, with exact logical full-width phase/backing and funded abort handling.

## Evidence, verification and source adoption

- Use the [workload plan](docs/WORKLOAD_COVERAGE.md), not only activation gas.
  Frozen F6 maps are61 project/39 dependency/four controls and1,021 ABI rows.
  Inventory counts and finite scenarios are obligations/evidence, not universal coverage.
- The selected contribution candidate is32M/full20% padding; maintenance24M/full25%,
  claims12M/full20%, unchanged legacy defaults. Never replace estimates with traces,
  reduce padding or widen limits merely to pass a test. Actual providers/fees and
  maximum workloads remain qualification work. [Gas procedure](docs/ROBINHOOD_GAS.md).
- Preserve source-specific failures/skips and distinguish new execution from exact
  reuse. Do not rerun unchanged contract/browser/keeper suites. Use focused affected
  checks; record actual method/source/fixture scopes without summing overlaps.
- Current inventory is `evidence/documentation-consolidation-20261127/FUNCTION_INVENTORY.json`.
  Run its offline `--check` after relevant source/plan changes. Generate/review new
  source-scoped candidates, never bypass trusted build/source/ABI admission.
- Keep pending-first receipt recovery and durable intent-before-signing unchanged.
  No automatic resend, used-sender initialization, guessed nonce, clock backdating,
  outbox reset or in-place repair of failed outputs. Original source/configuration/
  package pins and actual capture clocks remain. Readiness flags are not adoption.
- Source13/19 memberships and old journals are not upgraded by new files. Updated
  hashes require matching reviewed writer/checker/tools/policy; verify old packages
  with their original release. Source migration is not ordinary policy `rebind`.
- Same-host recovery against a retained chain is not physical host/OS/chain recovery,
  cross-host signer fencing, durability, provider/channel or sustained-operation proof.
  Remaining limits and accepted trust live in [findings](docs/AUDIT_FINDINGS.md).
- Before Python publication check exact staged blobs with
  `python scripts/check-python-publication.py --index`, then the committed revision.
  Untracked imports cannot establish published closure.

## Documentation and findings maintenance

- Keep **one current human-readable report**, `reports/CURRENT_REVIEW.md`, and
  **one current findings register**, `docs/AUDIT_FINDINGS.md`. Do not add parallel
  dated review/findings documents or copy report timelines into every guide.
- Historical narratives retired by this consolidation are recoverable at
  `fdd599c7698d0e1c0709a4a8b50130e5557ba508`. Use exact Git links and preserve source
  scope. Retain indispensable machine evidence/pins unchanged; historical directory
  manifests attest their original Git tree, not completeness of the reduced checkout.
- Old findings are assessed against current code: keep stable IDs, unresolved
  subclaims, accepted policies and verification gaps. Reconciliation is not closure.
  Do not resurrect retired architecture or silently redesign economic rights.
- `docs/project-todo.json` generates the sole Todo. Keep IDs/statuses and acceptance
  requirements; update the ledger, generate, then `--check`. Follow
  [Todo maintenance](docs/TODO_WORKFLOW.md). Source publication and rollout differ.
- Keep the single [operator manual](docs/OPERATOR_MANUAL.md) complete: calls, caller,
  inputs/units/examples, fresh snapshot/hash acquisition, moving-market validity,
  stop/restart, failures, reverse steps and irreversible/bypass boundaries.
- ABI/function changes require notes, examples, full reference and generated
  operator tables in the same change. Preserve exact generator checks; a template
  is not a live snapshot, simulation, approval or transaction.
- Consolidate genuinely duplicate/deprecated documentation after preserving Git
  provenance and repairing active references. This user-authorized archive policy
  replaces the former requirement to retain every historical Markdown report in
  the current checkout. It authorizes no deletion of essential evidence or user data.
