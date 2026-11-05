# Royalty receipt, recovery, conversion and claim audit

Baseline main e007618; fresh undeployed accounting6/custody5 source only.
No transaction, deployment, service, website, signer or journal change.

## Scope and decisions

Review the actual NFT/royalty factory, ledger, fixed-ledger converter and typed
routes, claim router, keeper, earnings/indexer readers and operator procedures.
Trace ordinary ETH, admitted ERC20, unsupported receipts, pre-activation funds,
asset outages/recovery, exact transfers, rounding, current-owner transfers,
concurrent claims/conversion, callback changes, pause, terminal LP exit and
canonical retirement. Preserve existing earned entitlements and liabilities.

The user approved restricted recovery of previously unallocated tokens into ETH,
allocated by active rarity weights **at recovery**, without applying this rule to
earned balances or deferred-currency funds owed to an earlier eligible cohort.
Only governance may authorize that exception; the keeper's ordinary conversion
capability must not become an arbitrary balance drain. No external beneficiary,
generic call, principal access, or weakening of ordinary conversion floors.

Keep the pre-seal converter-binding boundary explicit. Future currencies/routes
remain reviewable after sealing. No claim that arbitrary malicious, frozen,
illiquid or unpriced assets can be converted. Check retirement forwarding as well
as the active receiver. ERC2981 requests5%; it does not enforce market payment.
Do not silently introduce transfer-validator restrictions/ERC721-C authority.

## Verification

Archive original dirty docs and all earlier report/source hashes externally.
First check and repair stale test fixtures instead of weakening production guards.
Add boundary, adversarial and conservation regressions for the new recovery path,
including current-weight allocation vs existing earned/deferred rights. Exercise
real local v4 conversion in addition to explicit modeled venues. Run only
affected EVM/Python checks, then required normal size/static/callable checks for
changed Solidity. Retain failed attempts and source-stage identities. Update
the sole Todo, feature/evidence, release boundary and operator guide together.
