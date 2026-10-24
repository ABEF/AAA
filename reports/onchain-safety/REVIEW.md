# On-chain safety and execution-cost review

Recorded 2026-10-24 against the undeployed native/routing/pricing-V2 candidate.
This is an internal adversarial review and focused remediation. It cannot prove
the absence of every exploit or replace independent audit and live qualification.

## Findings and changes

| Finding | Change and retained boundary |
| --- | --- |
| Price source reads were bounded, but the sequencer reader still used high-level calls with unbounded execution/return-data exposure. | All sequencer decimals/round reads now use the existing 500,000-gas, exact-length reader. Wide round decoding rejects malformed `uint80` data with a bounded Oracle error. Status, timestamps, runtime pins, grace period and non-expiring healthy uptime-transition semantics remain. This is availability/grief-cost hardening; no direct user theft was demonstrated. |
| Strategy planning repeated complete source validation about eleven times per swap plan. | One static plan reads the two asset vectors once into memory. The same lower-price amounts, reference/range/spot guard, actual directional protocol/LP fee and upper-input/lower-output quote retain their exact rounding order. No cache survives the call. Execution/final contribution checks remain independent. |
| Contribution marks consumed separate slots for two bounded prices. | Pack lower/upper as `uint128`, checked before narrowing. `1e36` fits. Full values and padded basis/event encoding stay unchanged; maximum-price and fuzzed real contribution tests verify shares and hashes. No liability or persistent deployment schema is imported into a different layout. |
| Multi-currency checkpoints repeatedly fetched the same eligibility or bucket/shares. | Read context once before local per-asset arithmetic. There is no mutable external call inside the loops; single-asset claim/conversion wrappers still fetch fresh context. Fractions, indices, paid balances and rounding stay unchanged. |
| Admission and same-asset quotes repeated reads unnecessarily. | Admission relies on the source validation already inside each round read. Self-quotes validate the pair once, then return the unchanged raw amount. Failed dependencies still reject. |

The new internal price-math library has no external setter, funds or runtime
authority. Callable function/event ABIs, economics, governance powers, exact approvals,
loss limits and source-policy fingerprints are unchanged. No delegatecall,
arbitrary executor, holder redemption or sweep is introduced.

## Reviewed action boundaries

| Action | Reviewed controls and limits |
| --- | --- |
| Mint and activation/growth | Paid dormant issuance and owner/Entry authorization; frozen original-source prices and limits before pulls/conversion; exact token/native deltas; minimum contribution; incumbent-only historic backing; actual LP/range/key/owner/liquidity; final callback/approval-reset rollback. Existing source-scoped mint/VRF evidence is reused; this is not a new marketplace rehearsal. |
| Price reads and strategy | Source runtime/decimals/round/timestamp/disagreement checks, sequencer recovery, conservative valuation, exact rounding, pool/reference deviation, actual directional fee sizing and no stale/single-source fallback. |
| Rebalance, move and compound | Keeper authorization, range/cooldown, explicit same-pair move, frozen rebalance/move maintenance budget, exact settlement and stronger venue minima remain. Compound retains its existing per-swap/deployment guards; it is not newly placed under the ordinary-rebalance aggregate checkpoint. |
| LP/royalty funding, conversion and claim | Actual received backing, separate native reserves, current NFT ownership, CEI/reentrancy protection, exact bounded batch deduplication, proportional conversion rounding, deferred royalty cohorts and preservation of earlier unclaimed rights. No new double-claim, redirect or native-credit alias was identified in inspected paths. Unchanged royalty-only suites are reused. |
| Governance and custody recovery | Governed approval, pause/park, exact snapshots/recipient/nonces, normal all-ZZZ floors versus explicit no-swap raw minima, exact restoration and canonical barriers. Governance-approved external custody remains a deliberately trusted authority, with no enforced guarantee of return. No full custody or future-chain rehearsal was repeated. |

Parallel reviews inspected Oracle/contribution, action/maintenance and
reward/royalty boundaries. A separate diff review challenged the resulting
optimizations. Test receipts and failures retain their real source scope in the
[verification record](VERIFICATION.md).

## Remaining risks and release gates

- Two matching feeds can share a compromised reporter, proxy administrator,
  thin market or USD reference. Independence labels and hashes do not prove
  independence. Actual ETH/ZZZ/input source pairs are still unconfigured and
  unqualified; Chainlink availability alone does not supply two ZZZ sources.
- Strict round/fingerprint checks deliberately reject callback changes and
  malformed/stale sources. The selected 3% agreement band does not waive the
  separate default 1% contribution/conversion floor. No automatic fallback or
  cap increase is allowed. Gas remains separate.
- Runtime pins do not freeze proxy implementations, token semantics or upstream
  governance. Nonstandard/rebasing/taxed/callback assets need explicit review;
  unexpected movement fails atomically rather than becoming valid backing.
- MEV and market/impermanent losses within admitted limits remain possible.
  A compromised keeper can act only within implemented guards, but guard limits
  do not establish that its strategy is economically optimal.
- Immediate governance can configure unsafe dependencies or trusted custody.
  The code does not make that authority trustless. Holder-facing disclosure and
  independent authority/dependency review remain necessary.
- Component gas measurements use explicit mock providers/venues. Qualify actual
  target-chain routes, feeds, gas/fees, cold/max-history states and outages before
  enabling them. Vault's narrow runtime margin and dynamic constructor sizes
  remain release constraints.

No public transaction, deployment, signing-policy expansion, website build,
server/service action, existing local-chain/journal change or monitor restart
occurred. Production remains **NOT APPROVED**. Publication is recorded separately.
