# Actual local manual recovery and C/D gas rehearsal

**Controlled local milestone passed; production is not approved.** Baseline
`a5a0233a12e3477e7348811d4a3d97c77764a695`,15November2026.

The unchanged production unsigned CLI prepared the exact selected requests at
real confirmed/latest local headers using its default clock. A disposable
governance EOA then executed them on newly owned Anvil31337 instances. This closes
actual local composition and manual gas checks, not real markets or target fees.

| Action | Estimate | Exact25% padded gas | Receipt gas |
| --- | ---: | ---: | ---: |
| Active C14: consolidate residual into existing main | 10,233,104 | 12,791,380 | 9,388,004 |
| Active D14: replace whole physical portfolio | 10,408,641 | 13,010,802 | 9,520,341 |
| Parked D14: recover after actual park on same chain | 8,822,193 | 11,027,742 | 8,181,893 |
| Parked D0: explicitly selected oracle-outage recovery | 3,007,714 | 3,759,643 | 2,626,114 |

Every full24M-cap and exact padded simulation passed. Worst remaining margin is
10,989,198.24M is a ceiling, not charged gas.12M defaults stay unchanged; full
padded Active C/D would not fit them. D0 is a different explicit emergency
scenario, not an optimization or automatic fallback for14.

## What changed

- Added a standalone four-method current-graph host and a strict owned-node
  rehearsal runner. Neither changes production contracts or the manual preparer.
- Reconciled exact calldata, original floors/expiry/mask, receipt, real balances,
  NFT ownership/shares/earned liabilities, reserves, compound, clocks and pause.
- Corrected operator state-transition guidance and the custodyEpoch/parkingNonce
  reference notes. Original review/reference/source bytes remain archived.
- Added a bounded local milestone to the sole Todo and explicitly retained the
  emergency reference-as-venue limitation under the broader routing/operation tasks.

## State and rights actually verified

The fixture uses real Access authority with a genuine empty-code governance EOA,
current mint2/SeaDrop/canonicalV10 and execution1/LP3 readers, actual v4
core/periphery/Manager/router/Oracle/Budget. The Registry derives test-only local
network admission; controlled token, feeds, VRF, Permit2 and external depth are
explicit seams. This is not live ZZZ/dependency admission or OpenSea acceptance.
Two active NFTs have unequal contributions and distinct owners; a third remains
dormant. Real trades and harvest establish nonzero ETH/ZZZ reward, compound and
buyback backing; stray prefunds do not become principal.

C keeps main ID/ticks/centre/lastRebalance, closes the residual and increases main
L; nonce and epoch advance, lastCompound becomes inclusion time. Desired residual
mode is OFF and its legitimate completion increments the control revision.
Park closes both legs into attributed idle, increments nonce only and leaves
designated compound in Fees. Parked14 subsequently deploys into a new Active main
on that same owned chain. D/ParkedD update main/lastRebalance, release designated
compound exactly, and preserve nonce/epoch/lastCompound. Their desired residual
mode remains ON here: the next ordinary adjustment may recreate a residual.
All operations retain global pause. Reopening requires separate reviewed steps.

Current-owner rights, exact shares, existing reward/buyback books, raw backing and
governance receipt gas reconcile. Governance-only authority is retained; the
limited keeper call fails Unauthorized. Positive original swap/L floors remain.
C's old residual closure is authenticated by the exact pool/PosM/ticks/salt/full
negative liquidity delta plus LP-NFT burn where its old getter is unavailable;
other captures also record direct post-state getters. Parked recoveries have no
preexisting live legs to close; their preceding park proves closure separately.

## Important open finding: emergency reference-venue coupling

Ordinary execution1/LP3 authenticates its selected own-swap reference transition.
Retained emergency price-dependent checks instead use a live custody fingerprint.
Actual C/D/Parked14 negative traces show a successful core swap, changed successful
fingerprint and then failed Manager.balance, even with original output and L
floors feasible. State rolls back atomically. Healthy14 successes use a separately
reviewed third execution venue, distinct from both references. This limitation is
not solved and no financial guard/default was weakened to avoid it. A safe
emergency-compatible transition design needs separate review; never auto-retry0.

## Evidence and honest attempt accounting

Four unique new EVM methods pass across six invocations, retaining two earlier
fixture setup/assertion failures. Four focused compiler/list stages execute zero
test methods. Existing normal/compiler/static, old Solidity/Python/browser suites
and public RPC checks were not rerun. Four manual rows and their method/CLI/gas
records describe the same workflows, not additional independent feature counts.

Seven actual CLI attempts include one original25-second-budget timeout and six
successful reviews/transactions. Six unique status1 local receipts include an
earlier successful park whose new verifier incorrectly expected an epoch change.
That receipt was never resent; a new separate owned chain hosted the full later
park→recovery journey. C also had a successful receipt followed by a wrong new
verifier assumption about policy revision; corrected offline without resending.
The recording proxy's per-post local connection overhead was corrected; neither
production work budgets nor confirmations were patched. An earlier pre-spawn
genesis evidence size failure changed only the new test evidence writer's bound,
not production review limits. Original attempts/logs remain in the bundle. An explicit fresh deadline intent
was selected before preparing the accepted Parked14 recovery; the original
selection is archived. No prepared or submitted review expiry was extended.

All six owned nodes stopped: five executed transactions, one timed-out node sent
none. The runner accepts no public/existing RPC target or key, binds loopback and
protects old8902/57306 ports. Existing state/journals were never administered.
The historical RPC was unavailable on bounded before/after reads, so live old
state-root/balance equality is not claimed.5,598 website dist files and three
signer/config sources are byte-identical. Public configs remain null; shared
signing stays Anvil-only; services/sites and paused heartbeat remain unchanged.

The inner offline Catalog's older V9/LP2 string remains its exact provenance label,
not current runtime identity evidence. Actual full current configuration/runtime
getters and pins establish mint2/V10/execution1/LP3 separately. Do not retag old
artifacts. New documentation-derived hashes require new reviews.

## Inspect or reproduce

See [verification](VERIFICATION.md), [gas/transaction ledger](GAS_AND_TRANSACTIONS.json),
[root reconciliation](ROOT_REVIEW.json), [source scope](SOURCE_SCOPE.json),
[operator steps](../../docs/OPERATOR_MANUAL.md#local-manual-recovery-rehearsal) and
[typed inputs](../../docs/MANUAL_LP_PREPARATION.md). The portable evidence manifest
([manifest](EVIDENCE_MANIFEST.json), [checker](verify_evidence.py),
[archive](public-evidence.zip), [result](OFFLINE_VERIFICATION.json)) preserve
accepted and failed stages; verification reads archive bytes
only, without extraction, network, node, signing or test execution.

Real source/route depth and fees, Robinhood numerical provider capacity and
complete Nitro operation cost, maximum cohorts/state, contract-wallet envelopes,
actual host/restart operation and independent audit remain open. No rollout,
public transaction, sealed-instance change or production approval is implied.
