# Project improvement review - 2026-10-25

**Undeployed candidate; production NOT APPROVED.** This is an internal,
risk-led implementation review. It is not an independent audit or proof that
all possible defects were found. Start with the [challenged executable prompt](PROMPT.md),
[48-area coverage and decision review](COVERAGE.md), [baseline](BASELINE.json)
and [exact verification](VERIFICATION.md). Publication has a separate receipt.

## Material findings and implemented responses

| Finding | Change and practical effect | Boundary/tradeoff |
| --- | --- | --- |
| The displayed contribution cap was not encoded in Entry calldata; governance could widen policy before inclusion | New reviewed Entry V1 accepts a caller maximum, checks the captured governed cap before pulling/converting, and retains complete-operation floors. Pricing, exact ABI/trace, configuration, provenance and current release inventory require explicit versions. | New code rejects old execute calls. Historical local/pricing1 clients stay original; native-V2 website/wallet integration remains open. The maximum does not freeze prices, range or arbitrary governance decisions. |
| Registry's nested creation code left only31bytes under the initcode limit | Remove unused automatic seeding of a historical WETH proxy policy. Native accounting does not use it; optional wrapper policy requires explicit fresh validation/admission. | No new factory or authority, no deployment-limit increase. Final combined sizes/constructor-argument limits are in verification; Vault remains very close to its runtime limit. |
| Missing/malformed RPC ancestry could be treated as a reorg and erase confirmed indexed history | Validate exact block identity, prove bounded contiguous ancestry/start anchor read-only, recheck the boundary, then atomically roll back with a concurrent-state guard. Add fixed sanitized reason codes and a concrete recovery guide. | Provider outage retains old history; it does not make it current. APIs must still report stale/incomplete data unavailable. Deep/unproved reorgs deliberately require operator review. |
| HTTP redirects could escape the configured reviewed RPC endpoint list | Private per-client opener refuses redirects, including same-host; normal configured failover/chain checks/work budgets remain. | Operators must configure a reviewed final provider URL, not rely on redirect convenience. This is a read transport boundary, not new signing capability; other standalone historical transports are separate. |
| Dormant metadata reported royalty weight0 instead of the fixed revealed rarity trait | Metadata shows1/2/3 for revealed Commun/Rare/Legendary and `Unrevealed` for an unknown draw. Separate `royalty_activated` reports ledger activation. | Dormant economic ledger weight remains0; optional currency readiness is separate. No trait assignment, image path, ownership or royalty entitlement changes. |
| Buyback's USD trade ceiling used the lower of two valid source prices | Apply the conservative upper input value, rounded upward, to operating/immutable USD ceilings. | Execution-loss quotes and fixed allocations are unchanged. Valid source disagreement may require a smaller batch; no new fee or beneficiary. |
| Current documentation accumulated contradictory historical launch instructions | Consolidate README status/navigation and release approval record; retain history in source-scoped reports/features. Replace obsolete mandatory bridge instructions and stale cap/review-binding status; update the sole task ledger and operator recovery instructions. | Future bridges/remote canonical transport remain deferred, not silently implemented or waived for a chosen future mode. Release approval remains absent. |
| Focused keeper CI did not select the new maintenance/range suites | Add those existing suites to the Linux keeper workflow selection. | Workflow inspection/local tests are not a claim that remote CI ran or production Linux operations passed. |

## Cross-component review

The changed Entry path keeps owner/deadline/route/value/runtime checks and the
original-source pricing basis before external token calls. Caller maximum and
actual execution cap are distinct fields; exact calldata and trace reject
profile substitution. A tighter policy may apply before inclusion; changing
captured policy during execution still fails final checks. The old selector
cannot silently obtain new semantics. Direct owner-to-Vault calls remain their
own interface, without claiming the reviewed-Entry promise.

Indexed history is a cache, not custody. Missing provider data cannot prove an
orphan; even an earlier tip mismatch cannot authorize deletion without a stable
ancestor. The rollback transaction rechecks local rows/cursor. Ordinary forward
indexing prepares headers/logs before SQL writes and rechecks the end boundary;
actual provider finality and archive completeness remain external qualification.

Metadata expresses a fixed trait and a separate economic state. Marketplace
attributes use supported string/number values; unrevealed rarity is not guessed.
The renderer cannot award royalties, and current marked-value failure cannot
remove earned activation rights. Marketplace refresh/primary-mint compatibility
still needs real qualification. See [OpenSea metadata guidance](https://docs.opensea.io/docs/metadata-standards).

All changes retain the80/10/5/5 LP allocation, separate actually received
rarity royalties, current-owner claims, attributed principal/idle/fractions,
one contribution pool, exact approvals, immediate governance, explicit external
custody trust and2%/1%/3% defaults with gas separate. No new sweep, arbitrary
executor, holder redemption, integrated bridge, reset, timelock or cumulative
loss breaker is introduced.

## Remaining risks and work

- **Actual independent pricing and routes:** two answers can share a manipulated
  upstream. Qualify source/proxy authority, depth, ages/depegs and target-chain
  costs. The selected pool's observed fee is too high for a full default1%
  ZZZ conversion; require a cheaper reviewed route. No live oracle reading or
  new fee/route approval was fabricated here.
- **Native website/wallet integration:** current historical1%/old-selector profile
  must reject new native reviewed Entry. It has not been upgraded or deployed;
  public signing remains disabled. Production primary mint is intended on
  OpenSea, whose chain/product/caller/royalty behavior still needs qualification.
- **Strategy economics and actual gas:** displacement is not measured historical
  volatility, and polling is not execution assurance. Qualify widths, hysteresis,
  cadence, MEV, repeated loss/impermanent loss and real maximal venue/gas states.
- **Governance/custody:** immediate governance can approve dangerous dependencies
  or external custody; a custodian can divert funds and source contracts cannot
  force return. Caller policy binding does not eliminate these accepted powers.
- **Capacity and continuity:** Vault runtime margin is very small. Preserve normal
  limits and exact artifact profiles. Local pool/custody movement does not move
  NFT ownership/reward ledgers to another chain. Whole-chain disappearance and
  future cross-chain canonical transport remain deferred/unsupported.
- **Release evidence:** remaining actual services/authorities/VRF/artwork hosting,
  Linux/target-chain operating rehearsals, complete frozen-release verification
  and independent audit/remediation cannot be closed with mocks or documentation.
  Old stale fixtures and every failed scoped run are disclosed in verification;
  no current full-regression/green-CI claim is made.

The original 48 topics are retained with honest scope labels, including reused
evidence and not-applicable production AI. Broader hypotheses are not invented
findings. No inspected change establishes universal exploit absence.

Existing8902/Anvil/NFT/LP/balances/journals/dist overlay, website source/build/server,
Anvil-only signer/null public DEPLOYMENT and paused monitoring are preserved.
No public transaction, deployment, sealing or service action occurred.
