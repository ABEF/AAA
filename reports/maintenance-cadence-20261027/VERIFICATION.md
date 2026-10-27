# Coordinated maintenance: verification

Fresh accounting4 candidate, production NOT APPROVED. This change coordinates
standalone compound and physical LP replacement with rebalance/range priority.
[Internal review](REVIEW.md) records behavior changes and residual limits.

## Changed behavior

Budget capability2 requires every standalone compound, including first/no-swap
work, to wait until max(lastCompound,lastRebalance) plus the current pool interval.
An eligible rebalance or available reviewed adaptive selection takes priority.
Rebalance does not read lastCompound; newly needed range maintenance cannot be
postponed by an earlier compound. Harvest, claims, user contributions and the
existing per-operation loss policy remain independent. No24-hour default,
cumulative budget, new recipient or economic entitlement is introduced.

The fresh accounting4 keeper authenticates the exact Budget runtime, mutual
Vault bindings and capability2 before trusting compoundReady. Its local interval
is an additional delay. Historical1/2/3 profiles and journals retain V1 behavior.

## Actual verification

- **73 distinct final affected Solidity methods pass:**62 in the other affected
  suites and11 new cadence methods, across the documented selections. This is
  not a fresh complete repository regression. The scopes include actual installed
  local-v4 compound/rebalance/rollback, two existing conservation invariants at
  the committed default profile and existing collection-scale methods. Mock
  governance, source independence, admission/VRF and fake-venue scenarios remain
  explicit; these do not establish real-market safety or target-chain gas.
- The first run passed62 methods but Foundry rejected the new suite's reserved
  testFail prefix. Renaming exposed two new fixture mistakes: second/independent
  compounds had no new backing and hit the existing zero-input guard. Supplying
  actual fresh fee backing corrected those cases. The final test source passed
  in disjoint2+9 selections; earlier failures and raw logs remain preserved.
  Production guards were not weakened to make fixtures pass.
- **96 distinct Python methods pass** in47+49 disjoint selections, including11
  new cadence cases. Coverage includes authenticated capability/binding/pins,
  canonical boolean handling, local interval, rebalance priority, other-keeper
  readiness, independent due harvest, failure isolation, pending recovery and
  historical compatibility. These results were captured in subagent tool
  outputs; no raw log files were saved or reconstructed. Source hashes were
  captured afterward, with unchanged source supported by tool chronology.
- **37 normal size gates pass**, solc0.8.26/Cancun, viaIR, optimizer1/Yul disabled,
 75 closed inputs. Vault runtime remains23,523bytes (1,053margin); NFT24,400
 (176margin). Budget's recursive storage layout is unchanged. Exact release
 constructor arguments and target-chain gas still require qualification.
- Source-bound ABI reference passes:31contracts/607functions/31constructors/
 13receivers, no missing function purposes or input meanings. Existing122
 unannotated outputs remain the documented getter/unnamed-output boundary.
 Todo generation and narrow44-file source consistency pass. These are neither
 execution counts nor independent security approval.

See [commands, hashes and source bindings](verification.json),
[unique Solidity methods](solidity-methods.json), [normal sizes](production-size-gates.json)
and the per-attempt summary files in this directory. Original compiler/EVM logs
are retained outside Git under the exact external directory in metadata; their
hashes are recorded. Do not add overlapping reruns to the unique method count.
Repository JSON copies use LF line endings after the staged whitespace check
rejected Windows CRLF copies. JSON values are unchanged; original raw bytes are
retained externally, including under publication-json-originals. No check or
compiler policy was relaxed, and no tests were repeated for this formatting fix.

## Pool fee question, separate from release qualification

A read-only observation of the old Pons6538 pool at block98,951,183,
2026-10-27 03:58:52UTC, agrees across the official RPC and Pinax: core LP/protocol
fees0, hook base100bps, additional creator tax0, Pons share30%of hook fees and
buybacks disabled. Exact-input takes1%of pre-hook output; exact-output charges
1%of base input (about0.990099%of total input paid). The UI's0%does not imply
free swaps or ordinary LP entitlement to hook revenue. See the
[pinned witness](pool-fee-observation.json),
[verified hook](https://robinhoodchain.blockscout.com/address/0xE5e702641Ea86F4ae6cC3cDaeD2B886f976Be044?tab=contract)
and [Pons mechanics](https://docs.ponsfamily.com/v2). This is not the selected
hookless5011 pool; no selection or configuration changed.

## Remaining work

The [keeper-originated](../../TODO.md#task-security-keeper-manipulation) and
[outside-actor](../../TODO.md#task-security-external-manipulation) manipulation
tasks are explicit next-session work. Actual independent feeds, depth/fee/MEV
economics, submission providers, operating rehearsals, release inventory,
OpenSea/VRF/authorities and independent audit/remediation remain open. No profitable
attack was proved or disproved by this cadence verification.

No running service, Anvil deployment/state/journal, website, public transaction,
signing policy or deployment was changed. Production remains NOT APPROVED.
