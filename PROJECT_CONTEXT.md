# PoPL current project context

Reviewed 2026-10-26. [AGENTS.md](AGENTS.md) owns work instructions;
[README](README.md) explains the product and code; [Todo](TODO.md) alone owns task
status. This is the current snapshot, not an append-only session transcript.

## Product and implementation

PoPL is an ERC-721 collection capped at1,000 NFTs:600 Commun/300 Rare/100 Legendary.
Mint creates a dormant NFT with no LP or rewards. Activation in ETH/fixed ZZZ
attaches nonredeemable shares of shared LP; later contributions grow that NFT.
Current owner inherits unclaimed rewards, LP allocation and future funded rights.
Value/evolution is current marked on-chain LP NAV, not historic dollars contributed.

| Rule | Current candidate |
| --- | --- |
| Mint | Intended OpenSea buyer price0.05ETH gross, gas separate; recipient net after actual platform fee. Current direct mint pays all0.05ETH and is not OpenSea-compatible. |
| Contribution | ETH or one immutable ZZZ; minimum$100 activation/$5 growth, stronger pool minima apply. |
| Execution | Default2% contribution/1% conversion/3% maintenance, governance maximum10% each; caller/venue minima still apply, gas separate. |
| Prices | Two independently reviewed USD sources per priced asset,3% disagreement band; no qualified live pair yet. |
| LP revenue | Actual fees split80%NFT LP shares/10%equal activated collective/5%compound/5%ZZZ buyback-burn. |
| Royalties | ERC-2981 requests5%; actual eligible receipts shared100% at rarity weights1/2/3. Not universal marketplace enforcement. |
| Custody | Holder cannot redeem principal. Immediate governance can approve external custody; return is trusted, not forced. |
| Maintenance | One shared LP per admitted pool/strategy; one pool accepts contributions at a time. Reviewed keeper ranges may use ZZZ-price-in-ETH +/-25/50%; polling is not a guaranteed rebalance. |

Current source profile is accounting3/governance2/fee intake1/custody2/pricing2/
routing2/Entry review1, canonical `ZZZ_CANONICAL_SAME_CHAIN_NATIVE_LP_ONLY_V4`.
Current Position has eight fields. Same-chain ownership/ledger handoff and
same-actual-pair pool movement remain. External exit handles issuer exchanges
or outside bridging; integrated bridges/creator inboxes/remote ledgers are removed.
There is no post-seal ZZZ identity replacement or timelock operation machinery.

## Artwork and financial reporting

Eight base colors,58 palettes, four stable pattern slots, three rarities and four
evolutions produce2,784 renderer states for the fixed1,000-entry draw inventory.
No new image generation occurs at mint. Verifiable randomness assigns a remaining
entry; provider acceptance is open. Pattern/evolution details are in
[metadata](docs/NFT_METADATA.md); current artifact bytes remain authoritative.
Enhanced starts$1,000; Singularity$10,000; market-value downgrades do not remove
activation or already earned rights. Artwork changes only after confirmed LP.

NFT fee history = individual+collective LP plus royalties, including prior claims
and past owners. Ready to claim is remaining funded balances, and lifetime claimed
is actual payouts. Claims/conversions/imports are not new income; reserves are not
NFT funds. USD history uses today's confirmed prices of original earned currencies.
Pending royalties may be claimable before processed history. Retired royalty receivers forward only already admitted
currencies; unknown new ERC20 receipts have no rescue path. Raw principal exit
does not override that separate royalty boundary. Authentic complete
logs remain necessary despite exact index/credit/dust reconciliation.

## Source, evidence and release

Latest functional publication [885af8e](https://github.com/ABEF/AAA/commit/885af8edaadbc4fa7f8da8021c1d2d2fe66a4a6d):
[keeper/LP audit](reports/keeper-lp-audit-20261026/REVIEW.md),
[verification](reports/keeper-lp-audit-20261026/VERIFICATION.md) and
[publication receipt](reports/keeper-lp-audit-20261026/PUBLICATION.md). Website
memory-onlyfd8c3e8; both remote heads verified. Health binds exact loaded config;
conversion flags reject malformed observations. Current3native rehearsal and
range-test repairs improve qualification:354Python passes/5Unix skips,9range
passes including1000fuzz. Production44Solidity/ABI/economics unchanged. Actual
Linux process/target services remain unqualified; existing runtime unchanged.

Documentation consolidation [5114a1c](https://github.com/ABEF/AAA/commit/5114a1c62a8519c91233983d9123b137a24bbc60) and
website memory-only7dd7c35 are published on main, exact remote heads verified.
[Cleanup receipt](reports/documentation-cleanup-20261026/PUBLICATION.md) records
five redundant removals, current-guide consistency and preserved historical scope.
No implementation/deployment changed; this current paragraph replaces status
rather than adding another session-history preamble.

Earlier fee-integrity publication: [379ae19](https://github.com/ABEF/AAA/commit/379ae19dbb9c5a45a4ebb5c83be18007b67bc816),
backend fee integrity; [receipt](reports/backend-remediation-20261026/PUBLICATION.md).
167distinct affected Python methods pass (31new/136existing),54inputs pinned.
No Solidity changed in that fix. The previous full audit's current399-finding
static triage/47bindings and37object evidence retain their original scope.
Reference:31contracts/608functions. Vault runtime22,852; Access constructor total
42,352 in the recorded normal build. Actual release constructor/gas still needs
qualification. No full new regression, green-CI or independent audit is implied.

**Undeployed; production NOT APPROVED.** Actual feeds/routes/RPC/VRF/authorities,
OpenSea primary-mint integration, artwork hosting, explicit current3 website and
service acceptance, gas/strategy economics, operating rehearsals and independent
audit/remediation remain open in the sole Todo. No deployment was requested.

## Workspace and continuation

Contract checkout: `C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2`.
Website checkout: `C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website` (`ABEF/AAA-website`).
Public demonstration: [popldemo.0xwave.com](https://popldemo.0xwave.com).
Published native website reader still targets accounting2; current3 integration
and example-copy alignment are separate work. Public transactions are disabled.

Preserve local Anvil/NFT/LP/balances/journals/port8902/dist overlay. Signer remains
Anvil-only, public DEPLOYMENT null, staging monitoring paused. Original dirty
documentation and older checkpoints are backed up outside Git; unrelated code
drafts remain untouched. See [resume instructions](docs/WORK_HANDOFF.md) and
[documentation map](docs/README.md). Verify Git/remote publication separately from
local saves; publication does not deploy the website or contracts.
