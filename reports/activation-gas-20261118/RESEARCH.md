# Primary references and applicability

The compiler remains Solidity0.8.26/Cancun with the existing via-IR/Yul-disabled optimizer settings. No compiler or chain fee assumption is changed to obtain lower measurements.

- [Solidity0.8.26 inline assembly](https://docs.soliditylang.org/en/v0.8.26/assembly.html): assembly bypasses language checks, so the projection relies on a documented sole canonical typed writer, exact layout/length and dedicated differential/memory-boundary checks. It is not used for arbitrary external ABI parsing.
- [Solidity0.8.26 memory layout](https://docs.soliditylang.org/en/v0.8.26/internals/layout_in_memory.html): storage packing and memory layout differ. The49word ABI-to-nested-memory projection is tested with the pinned compiler; it does not infer memory offsets from packed storage fields or write reserved zero/free-memory slots.
- [EIP1153](https://eips.ethereum.org/EIPS/eip-1153): transient state is scoped to its owning contract/transaction and follows revert behavior. The Oracle already uses this mechanism. This change retains its area, controls and clearing; no new persistence, writer or cross-callback price cache is introduced.
- [EIP2929](https://eips.ethereum.org/EIPS/eip-2929): cold and warm accesses have different costs. Measurements therefore separate cold actual calls from component/warm diagnostics; node costs from nested frames are not added into a claimed whole-operation saving.
- The installed Uniswap TickMath and OpenZeppelin Math implementations remain authoritative dependencies. The proposed forward tick bracket was measured and rejected for higher cost. The feed keeps the existing inverse/down-cross rule. Quote algebra has an exact integer-floor proof and differential checks; no spot/freshness/price-agreement/known-fee/loss guard is loosened.

References informed concrete proof obligations; they do not replace current source inspection, independent review or target-chain/provider acceptance. New private packed LP carry keeps a full-width spill rather than assuming all possible future/imported weights fit128bits.
