# Direct Entry3: remove redundant contribution conversion

Reviewed3November2026. Production **NOT APPROVED**. User approved removal for a
fresh release; no deployment, site/service change, Anvil reset, signing or journal
migration was performed. [Verification](VERIFICATION.md) records exact scopes.

## Decision and implementation

ETH and the one fixed ZZZ already are the pool currencies. Entry's optional
whole-contribution conversion could exchange all input before the Vault balanced
it again. It is removed rather than retained as an unused governed capability.
Only `ZZZActivationEntry.sol` changes among production Solidity sources.

Entry now forwards the exact original pair asset to the fixed Vault. It has no
route catalogue/setters, v3/v4 conversion call, native-swap receiver or conversion
child. The Vault still sizes and executes its bounded reviewed balancing swap and
verifies factual marginal MAIN liquidity. LP-reward and royalty conversion remain
separate, including their own typed executors. No economic split, principal right,
activation/growth minimum, cap, residual policy or keeper behavior was changed.

This is a deliberate capability removal and breaking fresh ABI, **not** a claim
of byte-compatible refactoring. Initial activation and later growth use the same
shorter reviewed call. Current owner, input admission, exact native value/token
pull, pre-pull dual pricing/policy/caller cap, callback isolation, exact allowance
cleanup, final balances/context/owner/policy and atomic rollback remain enforced.
Contributions still checkpoint incumbents and buy shares at aggregate net NAV;
they do not recenter the position or spend incumbent idle/compound/residual.

## Explicit integration boundary

| Identity | Fresh candidate | Historical boundary |
| --- | --- | --- |
| Entry ABI | `ENTRY_ROUTING_VERSION()==3`;7 Request fields | Routed Entry2 has9 fields; old selectors do not execute fresh Entry |
| Captured review/prices | Review-policy2, Pricing entry-review2 | Unchanged captured semantics; routing3 does not mean review-policy3 |
| Inventory | Schema9,20 helpers; no Entry executor | Exact schema8/21-helper example retained for explicit historical inspection |
| Accounting | Accounting6/Portfolio2/canonical V6 | Same wire does not imply identical runtimes or compatible old configuration |
| API | Explicit routing3 config, new selector and trace binding | Old routing1/2 readers stay explicitly selected; no guessed fallback |
| Website | Matching source7 consumer/rollout still required | Served current3/poplint, popldemo and browser signer unchanged |

Fresh runtime/configuration and operation reviews must be rebuilt and qualified.
Do not patch old pending transaction bytes, journal identity or version labels.
Schema8 CLI inspection requires `--historical-consistency`; fresh release tooling
requires schema9. Offline operator manifests use Entry-routing3 while preserving
the hash procedure and false simulation/readiness flags.

The contribution event wire is intentionally preserved for historical accounting.
Fresh `SourceContributed.output` equals `sourceAsset`, and output amount equals
input amount; that event proves forwarding, not LP deployment by itself.

## Measured effect and audit

[Normal compiler evidence](production-size-gates.json) covers52 production sources
plus31 dependencies and43 normal object gates. Entry runtime falls18581→9863bytes
(8718 saved); creation31139→10929. Registry runtime remains10719; its creation
falls42736→22526 because it no longer embeds the Entry conversion child. These
are object sizes, not deployment-gas estimates. See [comparison](size-comparison.json).
Vault635/Budget237/Migration20/Balancer360-byte runtime margins remain tight.

[Current static triage](static-coverage.json) covers471 detector records:428 exact
unchanged contexts reused and43 contexts freshly reviewed. Analyzer findings and
accepted risks remain visible; review coverage is not a no-findings result or an
independent audit. The [compiler assessment](compiler-assessment.json) refreshes
source applicability against the immediately prior official six-disclosure
snapshot. Source graph/layout assumptions are explicit, not a compiler proof.

## Retained failures and corrections

The first20-case test stage failed in fixture setup: an old pooled fixture used
unsorted, zero-decimal tokens inconsistent with the fresh native admission path.
The test fixture was replaced with a sorted18-decimal pair and complete reviewed
bindings; production admission was not relaxed. The next stage passed19 cases and
exposed one incorrect assertion:99 deployed plus1 attributed idle gives100 net NAV
shares, while the independent physical-LP floor still measures99. That assertion
was corrected. An empty regex-selection attempt is retained and counted as zero
coverage. The corrected case and8 actual local-core regressions subsequently pass.
[Stage ledger](test-stages.json) authenticates the19 unchanged successful bodies
and records28 distinct successes across scopes, not one fresh28-case suite.

Retired Entry-routing2 conversion fixtures are preserved byte-identically as
nonexecuting `.sol.txt` records under `test/legacy/entry-routing2`; remaining
historical Python codecs stay active where required for old deployment inspection.

## Remaining gates

Qualify actual ETH/ZZZ dual feeds, reviewed Vault/converter venues, tracing/RPCs,
VRF, authorities, OpenSea minting, exact deployment/target gas, source7 services
and website integration, recovery operations and independent audit/remediation.
No actual target-chain fork was rerun in this campaign. No production readiness,
profitability, attack immunity or complete failure-recovery guarantee is claimed.
Follow the [central Todo](../../TODO.md), [direct Entry procedure](../../docs/ACTIVATION_ENTRY.md)
and [Operator manual](../../docs/OPERATOR_MANUAL.md).
