# Reviewed contribution policy: scoped verification

Status: the scoped checks below pass after the documented new-fixture repair.
Production is not approved.

## Functional boundary

The fixed Registry-created Entry exposes `REVIEW_POLICY_VERSION()==1` and
`executeReviewed(Request,uint16 maximumLossBps)` (`0x7d2edfe7`). The original
nine-field Request remains unchanged. Its fixed Oracle-created Pricing helper
exposes `ENTRY_REVIEW_VERSION()==1` and
`beginEntryReviewed(uint256,bytes32,address,uint256,uint16)` (`0x6a45b2ba`).
The old Entry execution and old pricing initializer explicitly revert.

The caller maximum is 0..1,000 bps. Before pulling ERC20s or converting source
funds, Pricing captures the governed contribution cap and rejects a cap above
the signed maximum. A lower governed cap remains stricter. Existing captured
limits, price fingerprints, physical LP checks and final source/approval checks
continue through the complete operation. Native call value returns atomically
on revert; network gas and an earlier separate approval are not refunded by
this guarantee. Zero means zero permitted execution loss, not disabled checks.

This applies to reviewed Entry calls. Raw owner-to-Vault activation/increase
still uses its raw liquidity minimum, deadline and governed policy; it has no
new caller USD-loss argument. The maximum does not freeze future prices,
ranges, routes or all governance settings. No raw-Vault fallback was added.

No helper, factory, custody authority, signer or sweeping capability was added.
Registry no longer seeds a dated WETH metadata policy at construction. Native
accounting never depended on that record; optional wrapper review/activation
continues to require explicit, fresh, fully validated governance actions.

## Solidity results and exact reuse

`entry-review.json`, `entry-review-summary.json`, its stderr log and input
manifest retain the initial 25 invocations: 24 pass and one new fixture failure.
The inherited Atomic activation case ran in two derived suites; it is one
underlying behavior, not two independent findings.

The failed test called `oracle.contributionPricing()` after arming
`expectRevert`, so the successful getter intercepted that expectation before
the intended retired initializer was called. The repair caches the helper
before `prank`/`expectRevert`; no production code changed for this repair.
The incremental follow-up runs that repaired test plus two later-added cases:
malformed uint16 ABI with prefund/allowance preservation, and native ETH
reviewed-cap rejection before conversion followed by a tighter-policy retry.
All three follow-up cases pass in `entry-review-final.json` and its summary;
the exact copied source/test inputs are retained separately. Its production
source snapshot includes the final separate Buyback change; the reused initial
tests retain their earlier exact input scope. Entry/Pricing/Registry are identical
in both runs.

Across both runs there are 28 invocations, 27 distinct suite/test IDs and **26
distinct underlying source methods with passing final outcomes**. The one
repaired test is counted once. The inherited Atomic method appearing in two
derived suites is counted once. Eight new review-policy methods, four native/v4
Entry methods, six pricing-callback methods, seven wrapper-policy methods and
that one inherited Atomic method comprise those26. No unexecuted case is counted.

Already passing initial cases include the caller cap raised before inclusion,
stricter actual policy, zero-loss success/failure, the 10% maximum versus a
stronger physical venue floor, growth rollback, six existing hostile pricing
callbacks, three installed-v4 conversion/native flows, and seven optional
wrapper-policy authorization/revalidation cases. Callback coverage includes
both increased and decreased governance caps during conversion.

The installed Uniswap v4 conversion is real local core execution. LP settlement,
prices, access and VRF in these fixtures are explicitly local substitutes.
These are not live Robinhood route/provider or maximum-state gas qualification.

The current production Entry/Pricing/Registry sources are frozen at:

| Source | SHA-256 |
| --- | --- |
| `src/ZZZActivationEntry.sol` | `b11c5ef8e0dc546bdff99755e311ee7205db8100fb04c75bd00c05bbc7e6d05a` |
| `src/ZZZContributionPricing.sol` | `f7c6bc87542e12d8f388955fc553e92fc817e1cc40a471b42b267602e1efe8be` |
| `src/ZZZPoolRegistry.sol` | `86307c3290bfd5560403b22c898100d52d0e4840b76dbe66c6bbc5bbd8738642` |

## Backend results

The final frozen affected selection passes **98/98 Python cases**, no failures,
errors or skips, in 61.731 seconds. `python-final-bound.json` retains each test
and final source hashes; `.log` retains the complete output. These are synthetic
RPC/trace/profile tests, not Solidity execution or actual provider qualification.

The selection covers exact maximum calldata, explicit profile/getter admission,
malformed values, no legacy or missing-getter fallback, exact pricing-phase
traces, native/routed/growth composition, strict current schema-5 observations,
unavailable observations and preservation of the actual legacy response shape.
Current pricing-V2 prepares and schema-5 manifests require explicit
`review_policy_version:1`; current API service profile is
`accounting_v2_routing_v2_pricing_v2_review_v1`.

Only review1 adds top-level `reviewed_maximum_loss_bps` and
`provenance.review_policy_version`. `execution_limit_bps` remains the actual
captured cap. An approval response is not an Entry execution; it requires a
fresh review after confirmation. Legacy pricing1/review0 response fields and
selector remain unchanged.

Initial Python execution had two errors in newly added mock fixtures (tuple
assignment, and an unrealistic missing-dictionary response). Their sanitized
transcript observations and repairs are retained separately; no missing original
source hashes were invented. The final 98-case bound run supersedes those
provisional results. Earlier repaired/final-shape repeats do not increase the
distinct test count.

## Normal object limits and exclusions

The early size-safe design check passes all 37 ordinary object gates with the
normal Solidity0.8.26/Cancun/via-IR/optimizer1/Yul-false profile. Registry creation
plus its constructor argument is 48,334 bytes (818 below 49,152); Registry runtime
is unchanged at12,027. Entry runtime17,511; Pricing runtime15,200. Vault is
unchanged at24,519 (57 below24,576). No size/gas guard was relaxed.

`production-size-gates.json` here is the early design check, preceding the
separate final Buyback source change. Use the parent report's final combined
37-object record and all42 source hashes for the final project build; do not
misrepresent this earlier snapshot as that final build. Dynamic constructor
qualification retains its separate normal-limit requirements.

No unchanged full regression, fork campaign, real wallet/provider, public
transaction, running service, website build, or independent audit was performed.
The historical `ActivationEntryTest` has a pre-pricing mocked Oracle and was
not presented as a fresh green current regression. Mechanically updated fork
and economic-composition Entry call sites do not create fresh fork evidence.
Existing8902/Anvil/NFT/LP/balances/journals/dist, Anvil-only signer, null public
deployment and paused monitoring remain untouched.
