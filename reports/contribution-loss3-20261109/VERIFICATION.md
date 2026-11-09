# Verification: total contribution default300bps

Baseline main:`793c8e026b1d3fc307256fde2f6d4e82c4efec37`.
Scope: future total activation/growth3% only. This is not target-market,
operating, independent-audit or deployment approval.

## Normal build and constructor comparison

[Normal input](contract/normal-final-a864bb33d5/compiler-input.json), compressed
compiler output and size/source records retain the actual90-source build.
Solidity0.8.26/Cancun/viaIR/optimizer1 with Yul disabled is unchanged.
All47 normal size gates and both royalty Factory data-child gates pass.

[Constructor comparison](contract/CONSTRUCTOR_DEFAULT_EQUIVALENCE.json) verifies:

- All64 deployed object executable bodies match after removing only each exact
  compiler CBOR tail. Raw artifacts and runtime hashes are not asserted equal.
- Every ABI and semantic storage layout matches. The AST difference is confined
  to the approved initializer literal; this is an intentional behavior change.
- Budget creation increases24814→24815 bytes, while runtime stays24018 bytes
  with558 bytes headroom. Migration/NFT embedded metadata differences are
  separately localized; constructor objects are not indiscriminately stripped.
- Royalty creation payload and both immutable data parts remain byte-identical.

Runtime headroom remains Vault32, CanonicalHandoff176, VaultCanonical264,
NFT479, Rewards358, Budget558, Balancer360 and Migration746 bytes. No compiler,
size gate, profile, allowance, venue or financial guard was relaxed to pass.
Earlier failed equivalence attempts are retained in
[the attempts record](contract/EQUIVALENCE_ATTEMPTS.json).

## Static coverage

Actual Slither produces558 detector records. The
[strict current review](static-review.json) covers11 individually reassessed
contexts and547 unique exact referenced-source reuses. Nine reassessed records
reference Budget; two are unchanged executor collect/close descriptions whose
ordering changed. Matching rules are unchanged. Coverage and the default CLI
check pass; the actual source/tool pins and records are retained under
[the static evidence](static/review-coverage.json).

The [payload manifest](contract-static-manifest.json) authenticates29 build/static
files. Previous OpenSea, fee-flow and older reports retain their original scope.
This is source-bound internal review, not independent audit clearance.

## Focused Solidity accounting

Nine new distinct methods pass across two separately scoped runs:7 core
Vault/Pricing/Rewards methods, followed by2 corrected Entry methods. They prove
97% deployed LP with fully backed idle, one-unit-short rejection, rounding up,
donation/incumbent isolation, growth without recentering or clock changes,
rollback of funds/shares/activation/royalty registration and stricter governed
or caller200 limits. An unchanged venue1% retained-value floor still rejects
an actual3% loss even though the aggregate contribution allowance is300.

The first run retained2 Entry setup failures before Entry execution. The old
synthetic Registry had ERC20-only admission; the corrected fixture explicitly
isolates native network admission while exercising real Registry/Assets/Entry
accounting. This test-only override and controlled/correlated feeds are not
actual Robinhood venue or oracle qualification. Seven successful core method
bodies and inherited fixture behavior remain equivalent, as recorded in
[the exact comparison](tests/core-body-equivalence.json); their successes are
not double-counted as a second current run.

Existing deliberate100/200 policy fixtures remain explicitly100/200. Changed
labels/comments identify their narrower scope rather than weakening any guard.
[Maintenance notes](tests/test-maintenance-notes.json) and original source
copies preserve that distinction. Three empty existing-test selections are
retained as zero verification: the proven cause was an end-anchored bare name
filter excluding callable signatures with parentheses. The earlier suspicion
about a brace path glob was not established as the cause.

The final byte-exact isolated209-source import closure runs the corrected
selection under the unchanged normal compiler settings:4 affected existing
methods pass,0 fail, and1 actual-network fork method explicitly skips offline.
The passes cover fresh default/governance events, deliberately governed2%
actual-local-v4 activation/growth, native activation/growth and same-block
users-before-rebalance with the stronger pool floor. Both snapshot and original
sources remain unchanged during the run. This is13 distinct Solidity successes
(9 new+4 affected), not a full-suite or actual Robinhood fork pass. The
[method/stage summary](tests/summary.json) and [test payload hashes](tests/artifact-sha256.json)
retain every success, setup failure, diagnostic and empty selection. No further
tests are counted from the compiler's imported dependency/test closure.

## Preparation and historical fixture maintenance

The [consumer record](consumer/verification.json) contains7 new focused methods
and1 maintained historical actual-trace method:8 passes,0 failures. It checks
current300 getter handling, exact97% integer floors for activation/growth,
one-unit-short rejection, idle/incumbent isolation, tighter venue200 retained-
value floors, the existing5% idle ceiling, old caller200 rejection and exact
Direct Entry3 reviewed calldata. Inputs are synthetic/injected, not live feeds.

The old actual EVM trace remains a200-bps historical artifact. Its original
source closure is authenticated against the immutable original normal-build
START record; no old trace or runtime is relabeled as new300 evidence.
[Package hashes](consumer/package.json) include the original raw log and patch.

Separately,95 existing function-reference, operator-reference and static-review
checker methods pass with unchanged sources during that run. These validate
the changed generated reference, examples and strict review selection; they
are not95 new economic or on-chain integration tests. The
[reference evidence](references/verification.json) identifies every method.

## Evidence limits and preserved environments

Only `ZZZMigrationBudget.contributionLossBps` changes in production Solidity,
from200 to300. The fresh schema17 example changes the matching two numeric
fields; historical templates and actual unset provider/venue observations stay.
Two operator call examples change; other rows retain their prior inputs/roles.
Current callable reference has39 contracts,906 functions,39 constructors,
13 receive hooks and no explanation gaps;958 operator rows remain templates
with readiness false. Readiness is not inferred from documentation generation.

No unchanged market fork or broad contract suite was repeated. Earlier actual
market2%/spot1%/swap2% failures remain valid observations of those exact settings.
The new default does not resolve missing reverse liquidity, qualified independent
feeds, a stricter spot/swap/user floor, or source-spread consumption of the budget.
Focused isolated test gas is not a target-chain fee or acceptance measurement.

No service, site, signer, public/null configuration, saved journal, existing
Anvil, stored cap, NFT/LP/balance or paused heartbeat changes. No authority key,
public transaction or deployment is used. Production remains NOT APPROVED;
actual dependencies, chosen operating settings, matching consumer rollout,
wallet/hosting/recovery rehearsals and independent audit/remediation remain open.
