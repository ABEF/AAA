# Synchronized inert-target prefunds

A public sync can populate an unused, unsealed receiver's opening pool while it
has zero activated NFTs and zero royalty weight. C07 import classified its entire
actual balance as target prefund/orphaned, but left that old opening pool counted
again by the derived accounted getter. A normal asset row then rejected.

C08 clears the old target opening pool at that row and constructs orphaned as
`(sourceAccounted + actualPrefund) - sourceLiability`. The checked source identity
`sourceAccounted = sourceLiability + sourceOrphaned` and both checked arithmetic
operations retain the original total-prefund overflow bound. There is no external
call between those local assignments. Imported source earnings remain liabilities;
the initial-allocation flag remains set, so no opening allocation is replayed.

One NEW actual-ledger method verifies both ETH and a6-decimal ERC20, with typed
InKindNFT/MockAccess seams. It proves synced target opening balances are classified
once, imported partially claimed earnings reach the current NFT owner, later
receipts retain their1:3 weights, and the governance-reviewed target prefunds can
be fully allocated and claimed. A maximum-value overflow rejects atomically,
leaving the backing-entry list and opening balance intact; a corrected row at the
same index succeeds against the same actual prefund.

Evidence stages are distinct:

- baseline01 selected0methods: compilation caught a mistaken private getter in
  the new test. Its raw diagnostics and hash-verified reconstructed source remain.
- baseline02 executed the one method against C07 and failed `CanonicalState()`;
  its compiled source closure and configuration stayed unchanged.
- postfix01 executed the corrected one method against C08 and passed, including
  all rights, future-receipt, drainage, overflow and retry assertions. The target
  NFT preseed now follows inert preparation, modeling the preceding canonical
  NFT module; the relevant pre-import royalty state is unchanged.

These are two executions of ONE distinct new method, not two new features. No
old method was selected by this producer. Whole-coordinator authentication and
launch-scale gas are separate evidence. The existing funded-abort control was
selected separately by the parent workflow; it is not double-counted here.
