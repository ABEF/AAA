# Internal security review - 2026-10-24

Scope: today's selected-pool implementation `7a1d564`, its downstream contract
and service boundaries, the operating procedures, and the broader native ETH
redesign specification. This is an internal review, not an independent audit or
production approval. Public contracts remain undeployed.

## Findings and remediation

| Finding | Effect | Resolution |
| --- | --- | --- |
| P2: ERC20 destination balancing ignored LP/protocol fees | A supported WETH/ZZZ destination at 10,020 LP pips plus 1,000 protocol pips could reject a feasible one-sided contribution: unadjusted sizing deploys less than the mandatory 99%. Transactions revert safely; no loss-floor bypass. | `ZZZStrategy` now applies actual directional static LP/protocol fees to every admitted hookless v4 pool. Both directions demonstrate net deployment above 99% where the old sizing fails. No fallback, arbitrary route or weaker minimum is added. |
| P2: separately mined active approval/exit has a moving snapshot | External trades change LP token quantities even while PoPL is paused, invalidating exact approvals repeatedly. | Operator procedure now pauses and parks with reviewed raw minima before taking the stable parked snapshot. Stale unsent plans must be cancelled first. Preserve the rounded-up original pre-parking ZZZ minimum; do not describe separate transactions as an automatically shared on-chain loss budget. Direct active exit remains snapshot-bound and can be batched. No snapshot check was removed. |
| P3: evidence reader accepted weak RPC identity and unbounded responses | Malformed replies, boolean IDs or oversized payloads could corrupt or exhaust a read-only observation. Runtime hashes were reported without enforcing the reviewed values. | Strict bounded read-only batches, exact integer response identities, EIP-1898 canonical-hash state selectors, six runtime pins, initialization origin checks, ABI bounds and sanitized terminal failures. No older-number/latest fallback. Actual provider support remains unqualified. |
| P3: failed evidence output could destroy the previous record | Direct writes can truncate an existing observation before an I/O failure. | Same-directory temporary output, flush/fsync and atomic replacement preserve the previous complete file on replacement failure; temporary files are cleaned. |
| P3: active documentation retained old dependencies | Zero-fee Pons revenue and removed bridge/module requirements conflicted with the selected hookless pool and current custody model. | README, economics, component architecture, adapter/inventory and operator guidance now distinguish actual LP fees, optional historical creator intake, current WETH accounting and unfinished native work. Older unrelated operations drafts are preserved; only a current-boundary notice is published there. |

The four retired transport IDs were still bound by one old governance test fixture;
the fixture now matches the controller's existing rejection. Dynamic-range vectors
assumed fee-free balancing; assertions now use their independent raw LP vectors and
actual 3,000-pip net output, retaining the original raw tolerances and verifying the
after-fee ratio/deployed amount. Production authorization and contribution floors
were not changed to make either fixture pass.

## Broader native ETH redesign audit

The user explicitly included this design in the audit. The current contracts still
use internal WETH. The native port is **not implemented or verified**. Its expanded
[implementation specification](../../docs/NATIVE_ETH_ARCHITECTURE.md#adversarial-design-review---2026-10-24)
now records these pre-seal requirements:

- Separate native currency zero from unset contract/token identities. In particular,
  an unset `currentZZZ` cannot label a native raw-exit amount as `sentZZZ`.
- Introduce native individual/collective indices and fractions without duplicating
  previously converted ETH credits or historical earnings.
- Preserve historical native compound/dust in incumbent NAV after ETH/WETH moves;
  remove the old skip-zero/32-asset assumptions where native is the 33rd asset.
- Keep canonical funding's existing transfer-then-zero-value-acknowledgment protocol.
  Simply requiring payable value at its acknowledgment would deadlock funding/abort.
- Export/import native backing independently in Vault, Fees, Rewards and royalties.
  Receiver token0/native protection slots must not count the same ETH twice.
- Make raw exit/recovery independent of the optional wrapper transitively, including
  Registry validation, harvesting and fee accounting, not only the final payment.
- Version on-chain state/codecs and per-predecessor backend profiles. Legacy WETH
  remains WETH; zero contract targets remain invalid. Verify every typed child call's
  native value and remove backend-only WETH pricing dependencies for native ETH.
- Preserve current-owner/reentrancy/atomic claim protections. A balance-based royalty
  inbox cannot distinguish forced ETH from a donation; follow receipt/cohort policy
  rather than inventing sender provenance.

These are design-level gaps in a proposed port. They are not new vulnerabilities
introduced into today's still-WETH implementation, and the tests below do not
close them. Do not seal a native-accounting candidate until the complete port and
its source-bound funding, accounting, callback, migration/abort and recovery cases
are verified. A successful wrapper-failure native exit is a required future case;
the current checkpoint cannot pass it.

## Reviewed safeguards retained

- No new authorization bypass or arbitrary execution/sweep path was found in the
  reviewed diff. `movePool` delegates internally to guarded `moveFunds`, preserving
  sender identity, governance, lifecycle and reentrancy checks.
- The normal exit helper tightens to the greater applicable swap minimum. The
  manager independently checks its floor; the aggregate 3% guarantee is unchanged.
- Native full-input settlement, exact rounded-up debt, prefund isolation, callback
  authorization and temporary-approval cleanup remain in place. Fee planning uses
  the bundled Uniswap protocol-fee composition and correct directional bits.
- Shares, funded rewards, royalties and reserves remain distinct. No generic reset,
  confiscation or payout redirection was added. Claims follow current ownership.
- The 1% ZZZ reward-conversion cap remains, gas separate. The selected pool's observed
  approximately 1.101% swap charge requires a cheaper qualified conversion route.
- Immediate governance and approved external-custodian trust remain deliberate risks;
  this review cannot certify governance-approved dependencies or custody recipients.

## Focused verification and reuse

| Check | Result and exact scope |
| --- | --- |
| [New fee-sizing regressions](runs/audit-fee-sizing.log), [source bindings](runs/audit-fee-sizing.json) | Four passed. ERC20 inputs in both directions, actual net LP deployment versus the old planner, directional fees, mismatched/invalid fees and unavailable state. Synthetic venue math, not live liquidity qualification. |
| [Affected existing suites](runs/audit-strategy-affected.log), [bindings](runs/audit-strategy-affected.json) | 58 passed, two fixture failures. Native settlement, dynamic ranges, buyback and range governance; the two fuzz cases used 1,000 runs each. |
| [Only the two repaired fixtures](runs/audit-fixture-fixes.log), [final bindings](runs/audit-fixture-fixes.json) | Two passed. Other 58 passing cases were not repeated; production Strategy source is identical across these runs. All 95 final source/test hashes match the retained final record. This is not a fresh full final-source regression. |
| [Observer tests](runs/observer-tests.log), [bindings](runs/observer-tests.json) | Nine passed with mocked RPC/filesystem only. Covers hash selectors, fee output, bad runtime/origin/reorg/ABI, ambiguous IDs, limits/read-only guard, secret-safe failures and atomic output preservation. No live provider qualification. |
| [Changed Strategy object](runs/strategy-size.json) | Runtime 12,862 bytes; initcode 13,318. Compiled dependency hashes match and unchanged 0.8.26/Cancun/via-IR/optimizer settings pass normal limits. Runtime is 218 bytes smaller than the prior checkpoint. No gas-throughput improvement is claimed. |

The other 32 production object gates and unchanged custody/royalty/parking code
reuse their [prior source-bound evidence](../hookless-pool/VERIFICATION.md); their
source hashes are unchanged. Earlier fork receipts retain the original Strategy
scope. No new fork, broad Solidity rerun, website/JS rerun or load campaign was
performed merely to repeat green results. Current dependency/market and native-port
qualification remain separate. [Evidence integrity](artifact-sha256.json).

## Release and publication boundaries

Production remains **NOT APPROVED**. Actual routes, independent prices, VRF,
marketplace behavior, inventory/authority configuration, operating qualification,
the native implementation and independent audit/remediation remain open in the
[sole Todo](../../TODO.md). Record publication separately; saving this report is
not proof it is committed, pushed, deployed or independently reviewed.

No public transaction/deployment, private key access, website build/server change,
service control, 8902/Anvil/NFT/LP/balance/journal change or monitor restart. The
shared signer remains Anvil-only and public `DEPLOYMENT` remains null. Main only;
older unrelated drafts remain local.
