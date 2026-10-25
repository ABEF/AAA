# Evidence-led cleanup workflow for the current PoPL candidate

## Material adaptations

- Start from `964e6b6` / implementation `ea2a70c`. The four requested initial
  refactors are already complete. Reuse their exact-source ABI/storage/size and
  scoped test evidence; do not perform them again or call old counts a new run.
- The 1,000 collection ERC-721s represent independently accounted nonredeemable
  shares of shared LP. A collection NFT ID, bucket ID and Uniswap position ID
  are different. A rebalance can replace the physical position without replacing
  NFT rights. Minting does not add LP; growth is not income or guaranteed NAV gain.
- Preserve native ETH/fixed ZZZ inputs, $100 activation/$5 growth, captured
  2%/1%/3% defaults and 10% governed maxima, separate gas, dual prices and 3%
  disagreement rejection. Preserve fixed 80/10/5/5 LP allocation, equal active
  collective membership and separate received royalty entitlements at x1/x2/x3.
- There is no holder withdrawal or holder burn flow to invent. Pool closing,
  same-actual-pair moves, trusted all-ZZZ/raw external custody and complete
  compatible same-chain handoff have separate authority/backing rules.
- Core modules are not proxy-upgraded. Governance2 is immediate, with no
  timelock or generic executor. Do not add either. No integrated bridge or hook
  implementation is required for the selected hookless pool. External proxy,
  wrapper, router, oracle and VRF risks still require actual review.
- WETH and admitted stablecoins remain relevant to royalties/conversion and
  historical readers; contribution-only restrictions do not justify deleting
  them. Preserve historical codecs, Anvil deployments, journals and event history.
- Keep accounting3/local Position8/status0..4/canonical LP-only V4 explicit.
  Native website2 is historical; current-profile acceptance remains open.
  No deployment, service restart, signer extension, public transaction, website
  source/build/server or monitoring change is authorized by this cleanup.
- Read pinned installed implementations and current official notices. Do not
  blindly use latest documentation or upgrade dependencies/compiler as cleanup.
  Compiler advisories are triaged against the actual0.8.26/viaIR/Yul-disabled
  configuration, including issues not excluded by disabling the Yul optimizer.
- A coverage matrix and evidence boundaries replace any claim of an exhaustive
  security guarantee. Keep independent audit and real-service gates open.

## Architecture and invariants to follow

| Flow | Components and responsibility | Required invariant |
| --- | --- | --- |
| Mint/identity | Vault charges0.05 ETH; NFT requests ordered verified draws, immutable rarity/color, ERC-721 ownership; metadata marks current LP value. | Dormant mint has no LP/rewards; exact600/300/100 rarity inventory; transfer carries all unclaimed economic rights. OpenSea integration remains unqualified. |
| Activate/grow | Entry/Assets authenticate input and policy; Oracle/Pricing freeze conservative price bounds; Vault joins/checkpoints shares; LiquidityManager executes typed PositionManager actions. | Only genuinely added LP meets captured loss floor; no incumbent backing/history can subsidize entrants; exact approvals, refunds/prefund attribution and atomic rollback. |
| Collect/claim | FeeController allocates actual local fees; Rewards/Membership track individual and equal collective indices; separate RoyaltyRewards and fixed converters preserve original attribution. | All credited rewards are backed; no double income on conversion/claim; no new entrant taking old fees; current owner claims without redeeming principal. |
| Maintain | Off-chain keeper simulates/signs bounded maintenance; Strategy determines approved ranges; Compounder/Buyback/Manager execute within policy. | Keeper cannot choose arbitrary target/recipient or silently widen governance policy; principal/idle/reserves remain classified; callbacks and failed operations cannot expose partial accounting. |
| Recover | Migration/Budget/CustodyValidation close/move or deliver exact approved custody; CanonicalHandoff and six domain codecs freeze/export/import classified backing. | No raw-exit fallback without approval; no sweep of others' reserves; exact returned backing and one active canonical deployment; trusted external custodian risk remains explicit. |
| Read/operate | Indexer, API, preparation, keeper journals and operator tools use pinned profiles/blocks/runtime identities. | Missing data never becomes zero/approval; no journal relabeling, duplicate submission or secret leakage; rebuild generated consumers on ABI/event changes. |

## Execution

1. Capture dirty-worktree hashes, source/dependency/build identities and deployed
   profile boundaries. Preserve unrelated work. Source publication is distinct
   from an installed deployment. Reuse unchanged recorded evidence honestly.
2. Review core custody/accounting, venue/pricing/strategy, NFT/rewards and
   services/tooling in parallel. Follow inherited/dependency implementations,
   actual callbacks and encoded selectors. Record inspected paths and omissions.
3. For each candidate record purpose, consumers, effects/reverts/calls, removal
   evidence, compatibility risk and verification. Do not delete a check, recovery
   mechanism or historical reader merely because local callers/tests are absent.
4. Implement justified coherent changes. Label structural refactors, observable
   behavior additions, bug fixes, fixture repairs, removals and architecture changes
   separately. Do not change rights, rates, authorities or custody promises.
5. Establish meaningful negative controls before fixes where feasible. Test
   actual pinned v4 behavior when repairing venue coverage. Capture all compiler
   inputs including implicit dependencies; detect stale ABI/documentation inputs.
6. Freeze production changes before one normal build/typecheck campaign. Compare
   exact wire ABIs, events/errors, recursive storage, init/runtime size and relevant
   executable bodies. Run only affected economic/callback/lifecycle checks; retain
   failures and count inherited/repeated methods once. Do not weaken normal gates.
7. Update the sole Todo, features, operator/callable documentation and memories.
   Keep actual service/provider/OpenSea/authority/operating/audit gates open.
8. Review the complete owned diff, source/evidence bindings, links and preserved
   drafts. Commit/push on main with a separate verified publication receipt.
   Finish with improvements, measured effects, exact checks, deferred decisions
   and material unreviewed/unqualified areas. No deployment or live operation.
