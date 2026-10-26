# Systematic adversarial review

Baseline `c3289a844f304803495597298688b1d6d89862be`. The
[challenged/final prompt](PROMPT.md) replaces a universal safety guarantee with
source-bound threat coverage, concrete counterexamples, justified corrections
and explicit limits. **Undeployed candidate; production NOT APPROVED.**

## What changed

| Finding | Impact and correction |
| --- | --- |
| RPC accepted noncanonical chain identities and ambiguous/nonfinite JSON | Read integrity: strings such as padded/signed/unprefixed chain IDs could pass; duplicate object fields used last-value-wins. Reject them before the requested action, preserving finite fee-history floats and valid hex-letter case. |
| Malformed result-plus-error response could be classified as a real missing-block rejection | Qualification integrity: a protocol-invalid envelope could masquerade as evidence that the provider correctly rejects unavailable blocks. Require exactly one result/error; retain genuine sanitized remote error classification. |
| Platform JSON decoder recursion failure escaped RPC failover | Availability: normalize decoder-limit errors to sanitized RpcError inside the existing bounded retry/failover path. WorkLimit remains terminal, approved endpoints are chain-checked and decoding receives a final budget checkpoint. |
| Keeper socket inactivity timeout did not bound stalled DNS/trickled data | Availability: source-only main-progress systemd watchdog with a120s example unit and full-group SIGKILL/no-core policy. Real host cleanup/recovery rehearsal remains open; standalone commands still lack that hard supervisor. |
| Holder inventory read a whole file before checking size; accepted ambiguous/nonfinite JSON | Local tool memory/data integrity: read at most2MiB+1, reject duplicate/nonfinite/overflow values and normalize parser-limit failures. Preserve finite/exact-limit inputs, exclusive output and nonapproval semantics. |
| Holder CLI default argument errors echoed supplied values | Secret-handling failure on operator mistakes: invalid flags/commands/numeric values now produce fixed sanitized failure inside the handled boundary. Valid flags/static help remain; credentials still belong outside command lines/Git. |
| Current audit/Todo guidance retained old inputs and misleading donation language | Correct ETH/fixedZZZ-only/98%-default acceptance; preserve historical99%test scopes. Distinguish actual funded PoolManager donations from unallocated raw Vault prefunds. No economic rule changed. |

The first three corrections share [the read-only RPC adapter](../../zzz_ops/rpc.py).
The [watchdog correction](WATCHDOG.md) changes main supervision and the source
unit only, with the Keeper financial/recovery class AST unchanged. The holder fixes affect [one operator CLI](../../scripts/inventory-nft-holders.py).
No production Solidity, storage, ABI, role, economics, input token or signing
capability changed. No deployment, installed unit or running service was modified. No new principal-theft,
unauthorized-claim or accounting bypass was confirmed in the reviewed contracts;
that is a scoped finding, not proof that no exploit exists.

## Review coverage

[Coverage record](coverage.json): **31contracts,608 functions,31 constructors and
13 receive hooks** mapped exactly once, with at least three applicable scenarios
per row. There are1,987 scenario instances across shared families. These are source
review cases, not1987executed tests or an exhaustive state-space exploration.
All44 project Solidity units, transitive helper paths and relevant installed
dependency implementations are identified/pinned. [Readable map](COVERAGE.md).

| Partition | Feature/call-path review |
| --- | --- |
| [Principal/pricing/venue](PRINCIPAL.md) | Admission, Entry callbacks/approvals, factual marginal LP, shares, Oracle/Pyth, native/v4 accounting, ranges, harvest/compound, thin markets and rollback.190callable rows. |
| [Rights/randomness/reporting](RIGHTS.md) | ERC721/VRF/metadata, permanent membership, fractions/claims, royalty cohorts, converters and NFT canonical state.249callable rows plus12financial/indexer files. |
| [Governance/custody/canonical](custody-review.md) | Direct roles/seal, classified reserves/burn, captured budgets, parking/normal/raw exit, exact recovery and same-chain retirement/import/abort.213callable rows plus127operator-function rows. |
| [Backend/keeper composition and watchdog](BACKEND.md) | RPC/HTTP/worker bounds, state/journals/nonces, gas/receipt reconciliation, scheduling/recovery, source-priced reviews and complete history/chunks. Static call-path review plus narrowly affected execution. |

The matrix checks input extremes/duplicates, authority, lifecycle, transaction
order, callbacks, dependency failure, market/fee changes, gas/capacity, reporting
and recovery as applicable. Constants/raw mapping getters are distinguished from
existence-sensitive reads and fund-moving calls. Internal/interface paths are
reviewed alongside concrete callers; matching ABI alone is never authentication.

## Important interactions preserved

- **Owner callbacks:** a claim recipient can legitimately fund royalties or claim
  another ledger before later batch entries. Universal initial-view/payout
  equality would reject valid compositions. Current-owner checks, liability
  updates and atomic rollback remain; no new callback prohibition was added.
- **Entry pricing:** two sources within3% may still make a contribution infeasible
  under the stricter conservative2%execution budget plus conversion costs. These
  are distinct policies. No automatic widening or single-source fallback.
- **Fees versus market evidence:** donated/wash-flow-funded fees are still actual
  cash receipts; they do not prove organic volume or future returns. Unattributed
  raw prefunds remain separate. Claims, conversion and imported/returned backing
  do not become new earned income.
- **Availability versus backing:** failed optional currencies may leave healthy
  ETH claims available while complete history or exact canonical settlement is
  unavailable. Skipping a liability to finish a handoff/abort would be unsafe.
- **Snapshots versus execution:** same-block observations and simulation do not
  reserve ownership, fees, prices, ranges, nonces or future inclusion. Reprepare
  and current on-chain guards remain necessary; no false reservation promise.

## Remaining risks and release decisions

Actual feed independence/proxy/updater controls, supported VRF, liquid conversion
routes, fixed-ZZZ burn behavior, OpenSea primary-mint/royalty settlement, authority
addresses, exact current3 website/services, maximum-state gas and target-chain/
Linux operating rehearsals remain open. Existing website examples still require
their separately tracked current-profile alignment; public signing stays disabled.

Immediate governance and approved external custody remain trusted. A bad approved
dependency/replacement or absent custodian return is not solved by local guards.
Lost keys, incompatible/dead NFT holders, permanent pool-slot mistakes, stalled
original VRF and permanently failed assets can cause unrecoverable or prolonged
unavailability. Per-operation caps do not prevent IL, market loss, MEV within
limits or cumulative turnover; the user retained that policy. No new timelock,
rescue sweep, owner rewrite, reroll, bridge or haircut was introduced.

The [sole Todo](../../TODO.md) records qualification work. Independent audit and
remediation of a frozen release remain required. Local source review and passing
fixtures cannot close those gates.
