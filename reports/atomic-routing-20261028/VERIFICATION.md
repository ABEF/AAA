# Atomic LP execution verification

Fresh undeployed LP routing1, production **NOT APPROVED**. [Internal review](REVIEW.md)
distinguishes delivered code from actual market/service qualification.

- **98 distinct affected Solidity methods passed** with exact final-source bindings,
  including27new method names. Actual installed-v4 router/quote/settlement,
  entrant isolation/share accounting, collective exit and selected cold gas
  checks use the exact [method inventory](solidity-methods.json). This is a scoped
  campaign, not a fresh whole-repository regression. 33router/composition methods
  ran on final helper source;65unchanged-suite passes are reused once using
  exact reachable-source metadata [receipts](retained-suites.json), without
  repeating them or claiming the earlier whole run passed.
- **173 affected backend Python methods passed**, zero errors/failures/skips and
  no loaded-source drift; [individual IDs/pins](python-checks.json). Historical
  readers, exact capped traces, request isolation, due harvesting and pending
  recovery remain covered. Separate31function-reference checks passed; these
  are not EVM cases. Earlier overlapping runs are not added to final counts.
- **38 normal object size gates passed**, solc0.8.26/Cancun/viaIR, optimizer1/Yul
  disabled, unchanged compiler/dependencies/build inputs. Vault24064runtime
  (512margin); Manager24152 (424margin), creation47826+160static arguments;
  LPBalancer21285; NFT24400 (176margin). Exact dynamic URI/deployment arguments
  and target-chain gas still need qualification. [Exact sizes](production-size-gates.json).
- All executed-test metadata and fresh normal compiler sources match current
  source bytes. Existing affected recursive storage layouts are preserved;
  Registry alone appends its monotonic configurationRevision. The new helper
  and LP1 ABI/profile are explicit; no installed contract/journal is migrated.
- Source-bound callable reference regenerated:32contracts/634functions,
  32constructors/13receivers, zero explanation/input gaps. Existing122output
  annotations remain purpose-level rather than being relabeled complete.

Initial21-method run had two fixture defects and prefinal source changes;
the exact logs and fixes are retained. One normal Manager artifact exceeded the
runtime limit by143bytes; shared validation recovered space without removing
guards. An obsolete broader pre-refactor compile was stopped with zero tests
executed, not reported as a pass. The next97-method run exposed a strict dust
regression; safeguarded interpolation repairs sizing without relaxing its0.01
threshold. Feasibility-prefix bracketing also prevents an invalid large seed from
hiding smaller valid quotes. Both affected actual-v4 suites rerun on final code.
[Provenance/pins](verification.json) records
commands, source hashes, retained attempts, gas logs and the external raw evidence.

Real v4 venue math/core/periphery execute locally, while native admission,
governance, token/source provenance, feed independence, VRF and Permit2 use
explicit test substitutes. These are not public Robinhood transactions, provider
approval or proof of organic trading. Cold gas observations do not qualify all
maximum solver settings, actual tick depth or full target-chain costs.

Actual feeds/routes/depth/fees, ordering economics, maximal release gas,
OpenSea/VRF/authority inventory, current frontend/services and operating rehearsals
plus independent audit/remediation remain open. Anvil8902/NFTs/LP/balances,
journals, websites/dist/servers, public signing and paused monitor are unchanged.
The four unrelated tracked drafts retain their baseline hashes.
