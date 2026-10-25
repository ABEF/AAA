# Deep cleanup and wider internal review - 2026-10-25

The [adapted workflow](ADAPTED_PROMPT.md) applies the supplied prompt to baseline
`964e6b6` / implementation `ea2a70c`. The preceding four refactors were complete;
their exact project-source evidence was reused instead of repeated. This pass
follows ownership, contribution, reward, maintenance, custody and handoff paths,
their installed dependencies and current tooling. This is an internal scoped
review, not a guarantee of exploit absence or independent production approval.

## Implemented findings, separated by consequence

| Finding | Classification | Change and consequence |
| --- | --- | --- |
| Duplicate royalty balance implementation | Behavior-preserving refactor | Removed private `_balance`; all 12 call sites use the already inherited nonvirtual `_canonicalBalance` with identical expression, call order and `address(this)`. No new inheritance or shared balances. Executable code is unchanged after metadata removal. |
| Duplicate v3 error declaration | ABI-metadata cleanup | Reused `ZZZModule.InvalidConfiguration` rather than declaring another identical library error. The inlined revert selector and short-circuit call order remain. Duplicate concrete/abstract error descriptors and the internal library's noncallable error descriptor disappear; no function selector changes. |
| Guardian grants/revocations were invisible to event monitoring | Observable behavior addition | Added `GuardianChanged` after the existing mapping write. Constructor initial Keeper/Guardian grants also emit. Permissions, bootstrap, sealing, two-step governance, pause/unpause and custody authority are unchanged. Access runtime +45 bytes; creation +175. |
| Function-reference checks ignored imported dependency/build drift | Verification-tool fix | Snapshot schema2 binds explicit compiler inputs, imported Solidity, exact existing build/lock files and artifact hashes. Missing/extra inputs, dropped bindings, escaping source roots, truthy string gate flags and malformed hashes fail closed. This changes evidence tooling, not an on-chain profile. |
| Active native-liquidity tests asserted retired wrapping behavior | Fixture replacement | Replaced the obsolete test class/unused boundary registry with 20 actual Core/PositionManager/StateView methods. Preserved six fault helpers used elsewhere and mapped all 24 previous behaviors. Exact preimages retained; current native funds are not represented as WETH. |
| Active ownership test expected optional royalty faults to undo activation | Fixture correction | Real Vault/NFT integration now asserts successful LP/eligibility, isolated currency deferral, protected historical receipts and correct recovery enrollment. No production guard was weakened to make it pass. |
| ClaimRouter documentation incorrectly excluded native LP claims | Documentation correction | Current ETH claims are supported by both reward ledgers. Removed an obsolete creator-inbox reference. Only these exact substitutions were staged from an unrelated dirty documentation file. |

## Architecture and dependency coverage

- [Custody/governance review](custody-review.md): ownership/share accounting,
  exact snapshots/approvals, principal movement, raw/normal exits, classified
  backing, return, parking, canonical preparation/export/import/abort and terminal
  authority. Reviewed inherited token-transfer/reentrancy and relevant venue math.
- [Venue/pricing review](venue-review.md): typed actions, native debt/credit,
  callbacks, prefunds, LP ownership, tick/range math, prices/fingerprints, reviewed
  source entry, conversion and keeper strategy bounds. Actual installed
  core/periphery are exercised locally by the repaired fixture.
- [NFT/reward review](rewards-review.md): ERC-721/2981/4906 behavior, ordered quota
  draws, immutable traits, transfers/current-owner claims, LP/equal collective
  indices, distinct rarity-weighted royalties, conversion, deferred cohorts and
  financial handoff. Installed OpenZeppelin callbacks/libraries are followed.
- Services/tooling review: typed transaction preparation and canonical reads,
  profile/lifecycle/lineage admission, keeper preflight/health/snapshots, current
  deployment examples, workflows, source/reference/event generation and operator
  instructions. Website signing/source and live operating services are untouched.
- [Compiler/upstream review](UPSTREAM.md) and [closed-input graph](rewards-callgraph-summary.json)
  distinguish actual applicability from generic recommendations. No dependency
  upgrade, hooks, proxy architecture or timelock is introduced.

The three component reports record concrete file/hash coverage. They do not mean
every interaction, off-chain module, third-party deployment or adversarial market
scenario has been exhaustively proved. The final compiler includes 44 production
files and 31 imported dependency files explicitly; the all-source AST includes 131
project/test/script files plus 134 dependency files. Existing historical local
deployments/journals retain their old code and profile. No approved production
deployment or public authority inventory exists.

## Retained mechanisms and rejected simplifications

- Preserve repeated authorization, binding and price checks across callbacks;
  identical-looking reads are not necessarily interchangeable.
- Preserve separate LP/royalty ledgers, earned fractions, quarantines, historical
  logs/codecs and incumbent-only dust. No holder principal redemption or sweep.
- Keep WETH and stablecoin royalty/conversion support. Only contribution inputs
  are restricted to ETH/fixed ZZZ; both reward streams retain actual currencies
  until a funded conversion credits ETH.
- Keep source snapshots, custody epochs, code pins, stronger original minima,
  permanent bucket aliases/reservations, exact backing and funded abort flags.
  These are replay, attribution and recovery boundaries, not obsolete migration
  baggage. Integrated bridges remain removed; same-chain movement/handoff stay.
- Do not merge FeeController into funded-ledger inheritance just to reuse a
  three-line helper. Do not rename every remaining numeric Budget phase merely
  for consistency; no material benefit justified more compiler/verification churn.
- Do not weaken native increase's exact-debt/prefund check. Real PositionManager
  can net pending fees against principal; the Vault deliberately harvests first.
  The repaired fixture checks rejection before harvest and success after harvest.

## Remaining decisions and qualification

Unknown royalty currencies received before admission are quarantined as
orphaned. They cannot safely be retroactively distributed by assuming which NFTs
were eligible. Admit reviewed expected marketplace currencies before receipts;
unknown late currencies need explicit provenance/policy review. No recovery
shortcut or discretionary redistribution was added.

Actual feeds and independent source quality, cheaper ZZZ conversion routes,
VRF, authority wallets, OpenSea gross-price/payment/reveal compatibility,
permanent artwork/service hosting, actual Linux/target-chain failure recovery,
strategy economics/maximal gas and independent audit/remediation remain open.
Current native website3 acceptance remains separate. Current selected-pool fork
qualification still requires its reviewed native fixture; a local installed-core
test is not that fork or a live market test. Frozen-source static analysis and
complete release regression remain required; no green CI/full-suite claim.

Governance and approved external custody remain trusted. No source contract can
force a compromised external custodian to return assets or guarantee liquidity,
market prices, fee income, oracle independence or recovery after chain halt.
The cleanup preserves these accepted boundaries rather than silently promising
stronger guarantees. Production NOT APPROVED.

See [verification](VERIFICATION.md) for commands, failures, exact source scopes,
ABI/storage/size results and measured changes, and the [sole Todo](../../TODO.md)
for open work. Publication and deployment are separate facts.
