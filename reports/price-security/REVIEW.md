# Dual pricing and factual contribution: internal review

Recorded 2026-10-24. Undeployed candidate; production is not approved. This is an
internal implementation/security review, not an independent production audit.
Publication and final verification are recorded separately.

## Findings addressed

| Finding | Resulting protection |
| --- | --- |
| A single USD reporter could misvalue input, incumbent shares and new LP. | Oracle pricing V2 requires two approved sources per asset, distinct declared independence IDs, runtime/precision pins, valid fresh rounds and bounded disagreement. No single-source or presumed stable-peg fallback exists. |
| Separate live price reads could use different policies or rounds during token/router callbacks. | Oracle-created ContributionPricing freezes the source/pair vector before Entry pulls/converts funds. Direct Vault contributions freeze before their pulls. Exact policies, rounds and decimals are checked again before adoption, issuance and Entry cleanup. |
| Capturing the contribution cap only at Vault entry left an earlier conversion-callback gap. | Entry captures the contribution and venue limits with the initial price basis. Budget adoption must match. Later callback changes cannot replace the captured execution floor. |
| Repricing existing LP during deployment could look like new contributed value. | Deliberate balancing reprices incumbent LP before the marginal measurement. Subsequent mint/increase must leave spot unchanged. Manager and Vault-level checkpoints cover pulls, approvals, settlement, refunds and final resets. |
| Earlier custody checks could precede a malicious final callback. | Manager rechecks the actual position owner, PoolKey, ticks and exact liquidity-unit increase last. Existing exact asset/native settlement and prefund exclusion remain. |
| Previously zero historical compound can become funded during settlement. | Newly discovered non-pair backing is marked at the final checkpoint, without overwriting initial marks. It enters only incumbent historical backing, never the entrant's deployed-LP floor. Failed pricing reverts the contribution. |
| The backend trace did not initially accommodate the new historical read phases. | Phase-separated balance observations, historical policy fingerprints and required historical price frames are verified. Missing, conflicting or duplicated observations fail closed. |
| Unconditional historical scans exceeded the existing cold activation gas gate. | The initial failing measurement is retained. Before composition, home/current pair equality makes unrelated historical scans unnecessary. Those scans are skipped only at epoch zero; later epochs retain both initial and final non-pair checks. See final verification for the repaired measurement. |
| Legacy local scaffolding still called the removed single-feed setter. | Current pricing-V2 artifacts are rejected before new state directories, Anvil processes or contract calls. No running fixture is migrated or reset. A fresh qualified V2 rehearsal remains separate work. |

The epoch-zero optimization relies on enforced composition invariants, not on a
guess about current tokens. Ordinary moves/resumes retain the ordered accounting
pair; custody completion records composition; canonical import disallows an
epoch-zero current/home mismatch. Pair prices are already marked. Global reward
indices are not this bucket's historical compound principal.

## Selected policy and valuation

The user selected **3% maximum disagreement** (300 bps). The intended inventory
records it; no live configuration was submitted. Governance's existing bounded
setter retains its 500-bps hard ceiling. Neither value replaces the separate
execution-loss policy: defaults remain 1% contribution, 1% conversion and 3%
maintenance, with immediate governance bounded to 10% and gas separate.

Minimum input uses the lower USD bound. Contribution loss checks compare upper
source value with lower marginal deployed LP and net new backing. Thus an
operation can fail inside the 3% agreement band when it cannot establish the
separate execution floor. The implementation does not average answers, subsidize
the entrant from incumbent funds or automatically raise a cap.

Two parallel internal reviews checked Oracle/price-policy/trace boundaries and
actual liquidity settlement. Those reviews identified the late-history, trace
coverage, early-cap and gas issues above. Focused negative tests exercise atomic
rollback; unchanged tests are reused only within their recorded source scope.

## Residual risks and release requirements

- **Independence is not provable from addresses.** Two providers can share an
  administrator or the same thin underlying market. If both agree on a wrong
  price, two-of-two consensus cannot identify it. The governance review hash and
  independence labels record assertions; they are not cryptographic market truth.
- **Source/proxy administration matters.** A stable proxy runtime does not pin
  its implementation or upstream reporters. Qualify source-specific authorities,
  implementation/configuration checks and continuous operating monitoring.
- **Availability is deliberately conservative.** Either invalid source blocks
  price-dependent contributions. Source replacement is governed; no stale or
  one-source fallback exists. Funded claims and applicable raw custody recovery
  remain independent of pricing; unusable venues/tokens can still prevent exit.
- **Actual market value is not guaranteed.** Raw LP units/inventory are facts;
  USD value depends on the source assumptions. These guards do not remove market
  movement, impermanent loss or permitted MEV/execution cost.
- **Real services are not selected.** ETH, ZZZ, USDG and any admitted USDC input
  need independently qualified source pairs, ages, routes and market depth.
  Creator/team input cannot substitute for that qualification.
- **Capacity qualification remains bounded.** The helper permits 34 distinct
  marks; the current read/preflight inventory supports 33 priced assets. An
  extreme configuration beyond that profile must fail closed until reviewed.
  Synthetic cold gas checks do not qualify actual provider/venue or target-chain
  worst-case gas. Vault runtime margin is particularly small; normal limits stay.
- **No existing deployment is upgraded by these files.** New immutable helper,
  runtimes, pricing-V2 configuration and current trace witnesses require an exact
  new deployment inventory. Existing local journals and historical schemas keep
  their original meaning. Public signing remains disabled.

Use the sole [Todo](../../TODO.md), [price-security runbook](../../docs/PRICE_SECURITY.md)
and [release approval record](../../docs/RELEASE_CHECKLIST.md). Independent audit,
remediation and real provider/route/operating rehearsals remain required.
