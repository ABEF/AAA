# Governance, custody and canonical review

Internal source/call-path partition at baseline `c3289a8`; production remains
**NOT APPROVED**. [Machine inventory](custody-review.json) covers all **213**
callable-reference rows in the nine assigned contracts:199normal functions,
nine constructors and five receive hooks. Each row has at least three explicit
applicable family scenarios, source location, purpose, caller boundary and
evidence status. Inherited getters/constants are included without pretending
they execute financial transactions. Nineteen current production/helper/
dependency source hashes match the preceding closed source manifest.

This is source review coverage, not213new tests, exhaustive state-space proof,
or an assurance that every input/schedule is safe. Existing test files are
cross-references, **not newly executed passes**. No production contract is changed.

## Material call-path conclusions

| Domain | Adversarial cases traced | Assessment |
| --- | --- | --- |
| Governance/bootstrap/seal | Self/zero/wrong wallet; stale pending acceptance; unsupported/duplicate binding; mismatched source/exit/Buyback ZZZ; missing VRF/helper owner; preparation/frozen/retired roles | Exact bootstrap/governance/lifecycle boundaries remain. No rebind, hidden executor or terminal-state reopening path was found. Guardian pause is not unpause/configuration authority. |
| Classified fees/buyback | Native/token mismatch; donated balances; tiny batches/incumbent dust; reserve double-release; unavailable sources; upper-price spend; partial/no-op/reentrant burn | Actual receipts and exact deltas keep reserve purposes separate. Burn checks both acquired balance and supply reduction. Fixed split and purpose reserves do not change on holder claims. |
| Maintenance budget | Wrong phase/bucket/caller; stacked losses; price/policy callback change; released compound;5%idle and one-unit rounding boundary | Original vector and limit are captured before external effects; released compound increases the denominator exactly once. Contributions use their separate frozen pricing context. Reverts clear/restore context and cooldown atomically. |
| Parking/external exit | Stale LP/share/epoch/nonce; old idle/prefund subsidy; one-sided raw minimum; ordinary swap outage; explicit raw mode; recipient behavior | Typed snapshot/minimum/authentication checks remain. Raw exit does not promise a USD floor or overcome a failed venue/token; normal failure never selects raw automatically. External custody is trusted and cannot be forced to return. |
| Completion/recovery | Missing/extra ETH; wrong/taxed tokens; allowance/receiver callback; permissionless fully funded benefit; wrong destination/reservation; duplicate completion | Exact funding is required and old Migration prefunds cannot substitute. Current owner rights/shares persist. No accounting-only completion, timeout write-off or public sweep is added. |
| Six-domain canonical handoff | Live/outbound custody; unrevealed mint; interrupted settling; forged/reordered/legacy records; duplicate funding; prefund substitution; partial-funding abort; repeated successor handoff | Captured cutoffs, ordered rows, source-byte comparisons, roots, exact paired-module backing and atomic retirement/activation prevent the examined competing-authority and replay paths. Imported ERC721 approvals are intentionally absent. |

## Findings and limits

- **Current documentation inconsistency:** the selected-pool Todo acceptance
  still contains retired USDG/USDC contribution and99%default language. This was
  reported to the root reviewer for correction of current guidance; historical
  source-bound receipts must not be rewritten.
- **Dependency availability:** a broken admitted asset after freeze can block
  settlement, funding/return or `canonicalValidate`, including abort completion.
  Skipping a liability or inventing backing would be unsafe. Real service/token/
  recovery qualification and independent audit remain required.
- **Operator mistakes:** permanent reservations/aliases can consume one of four
  slots, and a wrong runtime/recipient/dependency can be harmful despite a valid
  governance signature. Exact identity/reservation/recipient preflight is necessary;
  no cancellation/reassignment or guardian veto is promised.
- **Economics:** caps apply per operation, not to market loss, IL, repeated
  turnover or cumulative MEV. Preserve pre-parking raw ZZZ minimum through the
  reviewed normal-exit procedure; raw mode has explicit raw minima instead.
- **Holder compatibility:** preserving the owner address does not establish
  that old escrows/contract wallets can release a replacement NFT. The existing
  holder preflight and exact successor rehearsal remain necessary.

No new on-chain unauthorized withdrawal, accounting theft or replay was
confirmed in this partition. That conclusion is limited to the inspected source
and call paths; it is not an independent audit or production approval.

## Operator-tool follow-up

The [ops addendum](ops-review.json) records the read-only observer/inventory,
offline release gate, frozen bundle and holder-preflight call paths. The holder
CLI was found to read an entire file before checking its2MiB limit and to accept
ambiguous/nonfinite JSON. The approved narrow correction uses a bounded stream
read, duplicate/nonfinite/overflow rejection and sanitized JSON/argument-parser
failures without echoing mistakenly pasted endpoint values; static help remains.
See [exact source-bound verification](ops-input/VERIFICATION.md). No script is
run against a real RPC, wallet, original database or operating service.
