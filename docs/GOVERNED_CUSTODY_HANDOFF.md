# LP movement and holder exit

**External custody-address exits are removed from the fresh accounting6 release.**
There is no principal/royalty exitCustody, all-ZZZ exit, recover, completeLocal or
operator-selected handoff recipient. Their former procedures/evidence remain
historical in Git and their source-bound reports.

Use [Collective LP exit to NFT holders](HOLDER_COLLECTIVE_EXIT.md) for irreversible
governance shutdown, actual proportional ETH+ZZZ returns, bounded direct payouts
and current-owner fallback. NFTs remain transferable and keep future royalties;
previously earned rewards remain claimable.

Before exit, governance can use Migration.moveFunds for an admitted same-native-
ETH/ZZZ pool, or reviewed park/resume. Principal stays inside the protocol.
Follow [the operator procedure](OPERATOR_MANUAL.md#custody-and-lp-migration).
Whole-collection replacement remains separate and is supported only before
collective exit, using [accounting6/canonical V6](POSITION_V6.md) after closing both physical legs and
checking zero active residuals before parked export.
