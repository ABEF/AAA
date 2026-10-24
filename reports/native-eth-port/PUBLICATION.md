# Native ETH V2 publication receipt - 2026-10-24

| Repository | Published scope | Verified main commit |
| --- | --- | --- |
| ABEF/AAA | Native ETH accounting/custody, versioned API/keeper profiles, focused checks, operator guidance and central Todo/feature updates | [f907733](https://github.com/ABEF/AAA/commit/f907733e9d9fb7bcb31f930be3bc734e43138c25) |
| ABEF/AAA-website | Both repository memories only | [cb43349](https://github.com/ABEF/AAA-website/commit/cb433496994084d8b0f78c7ef28c889a098b39bf) |

Both commits were pushed normally to main and verified with remote branch hashes
before this receipt. This receipt and the final contract-memory prefix are a
separate documentation-only follow-up. No branch, PR or force push was created.

[Verification and scope](VERIFICATION.md) separates new cases, affected existing
passes, stale fixtures and later targeted repairs. No fresh full regression,
selected-chain fork, public transaction, real provider qualification or independent
audit is claimed. All 34 current production object gates pass normal limits;
78 production compiler bindings and 113 final source/test inputs match. The final
adversarial handoff case checks 91 compiler inputs and preserves 132 companion
plus 12 inbox prefunds through full funding and abort. Cold freeze uses 11,713,754
gas under the unchanged 12M guard. See [internal findings](REVIEW.md).

Native ETH is now a real accounting currency across Entry, Vault, manager,
indexed LP rewards, fee reserves, buyback, raw exit/return and canonical V2
funding/abort. The 80/10/5/5 split, NFT royalty weights and current-owner rights
remain. Contribution/reward conversion retains 1%, ordinary maintenance 3%,
with gas separate. ZZZ still requires a cheaper qualified conversion route.

Atomic ETH/WETH conversion, legacy V1 canonical import, native website profile,
reviewed production inventory, typed v4 conversion, post-seal operating extensions,
actual routes/feeds/VRF/services, target-chain rehearsals and independent audit
remain open. The central [Todo](../../TODO.md) owns task status; the
[operator manual](../../docs/OPERATOR_MANUAL.md) records the exact native version,
funding, price, keeper/runtime and recovery boundaries. Production is NOT APPROVED.

No website source/build/server, existing 8902/Anvil/NFT/LP/balances/journals/dist
overlay, shared signer policy, service control or paused monitor changed. Public
DEPLOYMENT stays null and signing stays Anvil-only. No private key was accessed.
Older unrelated local drafts remain uncommitted and were not bundled into this work.
