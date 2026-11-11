# Independent execution-price boundary review

Scope: current unpublished execution-price1 source after the gas optimization. This is a source implication/boundary review, not an additional execution pass, market qualification or deployment approval.

## Authority and evidence

Ordinary `priceBounds`, `price`, `value` and `referenceX96` remain live. Explicit execution getters return the operation's original bounds/fingerprints only while its typed context exists. They still reject changed controls or an armed/pending swap, but do not independently refresh market evidence. Getter output alone is not execution permission. Full `validateExecution` is explicit at write/callback boundaries; inactive validation is a no-op.

The context belongs to Oracle's fixed Pricing child, or to a standalone fixed-Manager operation. Manager borrows a Pricing context only through its authenticated Vault branch. Nested unrelated Manager/buyback use is rejected. One quote-proven swap is admitted per context; old profiles/runtimes are separate.

## Boundary matrix

| Moment | Full proof |
| --- | --- |
| Before Entry token pull/approval | Pricing starts the context and captures both ETH and both ZZZ rounds, agreement, controls and registered market proofs. |
| After Entry/Vault pulls and initial approvals | Pricing `begin` calls `_unchanged`, including full validation. |
| Before balancing and computing incumbent NAV | First `contributionNav` validates the entire context. |
| Manager start/end | Full current proof before borrowing and before ending; standalone creation performs full capture. |
| Before/after Vault and position approval calls | Manager `_balanceContext` performs full validation before returning the control fingerprint. |
| Immediately before core swap | `beforeSwap` validates current expected state and arms the exact selected quote result. |
| Immediately after core swap | Exact quoted output and `afterSwap` prove complete expected slot0/tick/fees/liquidity before input settlement or output callbacks. |
| After input settlement/output delivery | `_swapExact` explicitly calls full validation before its final price check and return. |
| After Manager refunds | `_balanceContext` and `endManagerExecution` retain full chosen-venue state through balancing completion. |
| Before and after LP mint/increase | Second/third `contributionNav` and position-executor contexts validate source/venue state around the typed LP proof. |
| Before issuing shares | Pricing `finish` calls `_unchanged` after actual marginal LP/net-NAV checks are available. |
| After Entry's final approval reset | `endEntry` calls `_unchanged`, and Oracle end validates before clearing every transient word. |
| End of ordinary maintenance | Budget's exact accounting/custody/loss/utilization checks precede Pricing `endMaintenance` and Oracle's final full proof. |

Direct Vault entry ends its context at Pricing's final result. Subsequent fixed Rewards/Membership/NFT royalty-enrollment calls contain no untrusted mutable callback: currency balance reads are STATICCALLs. Entry keeps the wider scope through its final mutable approval reset. Unpriced harvest/park/terminal-return paths and the explicit emergency mask retain their separate behavior.

## Complete-state and price invariants

The chosen venue's full expected state is checked through balancing end. If that non-reference venue is also the LP destination, only its active-liquidity comparison is subsequently released for the legitimate LP write; exact price/tick/fees remain. Reference and external venue liquidity never receive this exception. Reference/destination identity includes core plus pool ID, so equal hashes on distinct cores do not collide.

The original four full round tuples are cryptographically committed. Registered sources provide one bounded 320-byte proof containing identity/current-state/original-round commitments plus the LIVE five-word round, all derived from one pinned configuration/current pool/ETH observation. Generic sources retain ordinary round reads and exact original-round hashes. ETH's two source rounds, source precision/runtime checks, sequencer checks, freshness and current dual-source disagreement limits remain enforced by full validation. Updated live prices never replace the original financial vector for share, loss, idle or utilization arithmetic.

## Shared wide-word decoder

Ordinary responses are exactly160 bytes with offset0; proof responses are exactly320 bytes with offset160. The decoder verifies that exactly160 bytes remain before reading five words. It preserves nonzero/uint80 round bounds, answered-round order, positive answer, timestamp ordering/future/age checks and the normalized price ceiling. Source validation enforces feed decimals/code/age configuration before the decoder. Returned proof identity uses the first five words; the live round uses only the last five. No arbitrary return/revert payload is copied.

The optimization removes repeated provider reads inside pure getter chains. It does not remove the full proof after any relevant mutable boundary. The original32.5M-gas failure remains evidence of the earlier implementation, not current acceptance. Final normal-size and actual-operation gas/execution evidence must bind the final source revision separately.

## Narrow quote loading follow-up

V1's compiler `abi.encode(Execution)` is an entirely static 49-word/1,568-byte tuple. Save and every load now require that exact length (or zero when inactive). Only the compiler's canonical typed encoder can write this private, domain-separated transient area; successful end clears all words. No outside caller can supply or mutate encoded context bytes.

Pure quote getters load just their 15 needed ABI words into typed named struct fields: controls 0–6, fingerprints 11–12, bounds 13–16, ZZZ decimals 17, and pending-swap flag 38. These are ABI positions, never Solidity memory offsets. Canonical typed stores guarantee the address/uint64/uint8 widths; any nonzero pending flag remains rejected. Whole-context decoders, full source/market validations, and every mutable-boundary proof above remain unchanged. The exact-length assertion makes future struct changes fail closed until this codec and its tests are deliberately reviewed together.

The original fixed-ZZZ identity check is delegated to the already fixed read-only Math child to make room under normal code-size limits. Its registry/assets/token code checks remain the same. This new optional execution-source registration therefore requires the fixed Manager graph to be bound first; ordinary live Oracle pricing remains independent of it. No new module, setter, custody, executor or deployment role is introduced.

Early semantic compilation passed all 100 current closed sources in `abi-7dd65125f7`. Normal size, actual operation gas, and current EVM tests are separate pending acceptance checks; the earlier16.5M full-operation result still exceeds the unchanged12M policy and must not be reported as accepted.
