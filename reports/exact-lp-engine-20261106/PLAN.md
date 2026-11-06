# Todo implementation scope

6 November 2026; baseline mainb76dfcc. Production NOT APPROVED.

## Deliverables

1. Implement the approved exact-unit LP allocation engine in actual Solidity,
   with fixed bounded NFT slots and two fresh-pair books. Preserve all existing
   contracts, profiles, state, journals, signing and services while validating
   this prerequisite for the later ledger integration.
2. Challenge initial reset-to-zero rounding carry and replace it with a reviewed
   bounded phase representation if it improves genuine-weight-change behavior.
   Distinguish exact whole-unit conservation, fixed-cohort batching and dynamic
   rounding-fairness limitations. Do not silently claim flat proportionality.
3. Verify real EVM behavior, independent eager/golden arithmetic, uint256 limits,
   old-weight checkpoints, previews/claims,1,000NFTs and cold harness gas. Reuse
   unchanged old test evidence; do not run the unchanged full project suite.
4. Compile the exact current normal source graph and compare ALL old objects,
   then run/review current static analysis on frozen output. An internal library
   shell is not the future integrated ledger's runtime or gas qualification.
5. Fix the demonstrated operation-review retry inconsistency, preserving worker
   logic, authority, state files, RPC budgets and read-only behavior. Add focused
   sensitivity/precedence/unknown-state checks for the changed output.
6. Update the owning Todo, guide/manual, feature/evidence, roadmap, release and
   repository context. Publish only this task on main with exact staged/committed
   Python closure and preserved unrelated files/reports.

The final report must distinguish the implemented engine and diagnostic fix
from the still-unimplemented Rewards/Vault/canonical/consumer upgrade. Neither
an inert model nor a standalone library closes that whole requirement.

## Knowledge and inspection

The installed pinned OpenZeppelin Math implementation and Solidity0.8.26 behavior
govern the actual build. The official [Math reference](https://docs.openzeppelin.com/contracts/5.x/api/utils)
and [checked-arithmetic release description](https://www.soliditylang.org/blog/2020/12/16/solidity-v0.8.0-release-announcement/)
support full-precision/overflow review, not correctness of the new allocator.
The original design and20-model record remain immutable and source-scoped;
the improved phase policy needs its own new evidence.
