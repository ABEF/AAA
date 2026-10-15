# Separate internal High/Medium review

This is a separate AI-agent internal source review, not an independent external audit or production release approval.

All 91 High/Medium detector identities (29 High / 62 Medium) from the complete successful 160-finding final report are individually recorded in `secondary-review.json`, including raw IDs, canonical fingerprints, full descriptions, source elements and conditional rationales.

Raw report SHA-256: `9d41149623f65884eb77868ac0065c712e589284c2fd88b01f7899e836006bfa`.

All 23 Solidity files and three toolchain inputs are bound by LF-normalized hashes. Primary-review identities were independently checked. A late callback overclaim window was hardened during this review; no further required source change was identified within the supported dependency model.

## Factory and permanent binding

Post-seal governance/timelock only; one fixed-code inbox per positive-share canonical Active bucket, max 16. Fee destination/bucket/home pair/wrapper are immutable, no registered replacement/admin sweep. Factory rejects immutable mint-recipient collision.

## Native and constructor quarantine

Receive has no external calls/writes and requires explicit pair wrapper. Constructor prefunding is immutable quarantine. Sync wraps only new native value, requiring 18 decimals and exact one-unit/wei mint plus protected-native remainder, then exact forwards. Unsupported assets have no rescue. Backed honest immutable wrapper/token behavior still requires admission.

## Allocation and solvency

Only registered inbox may allocateExternal; exact funded pull enters shared 50/30/10/10 ledgers. External telemetry is separate from pending funds/conventional fees/remote liabilities. Repeated sync has zero pending and cannot double count; arbitrary direct donations to other custody contracts are not allocated.

## Membership and NAV

All inboxes process/flush old raw dust before additions, after entry balancing and again AFTER final LP mint/increase. Late own compound is pulled into idle, excluded from entrant netUSD through incumbentNAV, and deployment 95% is rechecked. The global pending/dust barrier follows the last mutating token transfers; owner checkpoint now follows these operations and precedes share issuance. Power checkpoint remains before Power addition. This fixes the independently identified stale owner checkpoint window without allowing late compound to satisfy deployed $500 activation. Future hook/native/callback venue integration still requires new admission/accounting review.

## Pause migration return

Funded processing/claims remain available paused and canonical bucket outbound/remote/inbound. External donations never increment remote expected/received/allocated counters or discharge absent remote funds. Authenticated routes/epochs retain original canonical pair. Home compound reserves await compatible home upkeep after return; automatic remote reinvestment is absent.

## Reentrancy and availability

Vault mutations, inbox sync, allocator and Rewards credit/claim are guarded. Global sync is Vault-only and intentionally allows guarded inbox allocator callbacks; dust/accounted update before credit. Tax/incorrect wrapper failure is atomic. One permanently registered broken token/wrapper can freeze all new entries. Max 16 limits loop count, not arbitrary token gas/availability.

## Review-discovered issue and resolution

Alice 2000 shares, Bob checkpoint 0. Callback donates 1,000 and syncs: owner 500/Alice, collective 300/Alice, liability 800. Bob receives2000 shares with old paidOwnerIndex and can claim past owner 500, making total claimable 1,300 against 800 funding. Exact transfer deltas do not detect an independently funded creator donation.

Root moved owner checkpoint after final LP operation and third global sync, pulled/priced late own compound as incumbent value, rechecked deployed/idle ratio, and added a global pending/dust view barrier after final mutating token calls. New donations are processed at old weights or cause atomic entry rollback before issuance.

The fixed path was independently source-reviewed. It does not authorize unsupported Pons/native LP integration or replace review of future callback-capable/mutable dependencies.

## Remaining production review

- Independent external audit and staging with actual authorities and immutable dependency/runtime identities.
- Explicit creator currency/timing/amount-or-percentage/period agreement; no guaranteed Pons share or historical eligibility snapshot inferred.
- Reviewed honest-balance conventional nonrebasing/non-taxed token and immutable/backed native-wrapper admission; assess callbacks/proxy/admin/blacklist/gas risks. Flags alone do not prove token safety.
- Economically review micro raw-dust owner-only exception for every asset and top-up frequency; it is not exactly50/30/10/10 on micro funds.
- Measure worst-case funded 16-inbox global processing/gas on target chain; review future callback/hook/native venue support beyond this specific membership-window fix.
- Actual native-ETH/Pons-hooked LP adapter and authenticated production bridge/finality/backing remain separate unresolved integrations.
- Canonical 10% compound reserves while physically remote remain at home; future remote reserve transport requires separate funded custody/accounting review.

Tests run by root/other agent are separate evidence. This reviewer inspected source/report identities and did not rerun compilation, fork transactions or invariant tests. No deployment/public-chain transaction occurred.
