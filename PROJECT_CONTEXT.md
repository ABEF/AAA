# PoPL current project context

Reviewed 2026-10-27. [AGENTS.md](AGENTS.md) owns work instructions;
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

The user is the single human operator and controls the governance wallet as well
as project services. There is no separate operator authority or committee.
Dedicated keeper/guardian/bootstrap/recipient accounts describe capabilities,
not additional people. A single-owner governance configuration is supported;
actual production wallet type/addresses remain unselected. Keep the keeper's
limited service key separate from the governance key.

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

Latest published functional checkpoint: contract
[8be0f89](https://github.com/ABEF/AAA/commit/8be0f89fd982253ddae7bef2ebfc36b497d836b1)
and website main77501ce. Poplint servesf23c559; the unchanged demo serves9be6d1.
Subsequent handoff/documentation commits do not deploy new artifacts. Next
session should start from the [resume instructions](docs/WORK_HANDOFF.md),
current fork witness and remaining actual feed/route/API qualification, without
repeating unchanged suites. Poplint's unconfigured page is expected until real
reviewed bindings exist; do not replace it with demo or historical Anvil data.

Last backend/keeper security publication [2a9c65b](https://github.com/ABEF/AAA/commit/2a9c65bf2d4dc27cc4eb16a8ba8b629f07f2f22b): [review](reports/system-adversarial-20261026/REVIEW.md),
[coverage](reports/system-adversarial-20261026/COVERAGE.md) and
[verification](reports/system-adversarial-20261026/VERIFICATION.md). All608 functions,
31 constructors and13 receivers have multiple static cases;1,987 scenario instances
are not test passes. Shared RPC rejects malformed identity/ambiguous or nonfinite
JSON/envelopes and keeps decoder limits in bounded failover. The keeper main
path now supports optional systemd progress supervision; the source120s unit
uses main notifications and group SIGKILL/no-core, preserving journal recovery.
Actual host kill/restart qualification remains open; standalone RPC can still
block beyond an inactivity timeout. Holder input reads
are bounded/strict and invalid arguments no longer echo values.244 unique affected
Python methods:241 passes/3 explicit skips,42 new included once; no failures/errors/drift. Actual
contract-wallet callbacks remain supported; conditional preview differences are
not fabricated accounting errors. Solidity/ABI/economics/services are unchanged.
Exact main publication is verified in the [receipt](reports/system-adversarial-20261026/PUBLICATION.md);
actual operating/provider/independent qualification remains open.

Prior market/input publication60bfb96/receiptc3289a8 retains its
[exact scope](reports/market-adversarial-20261026/VERIFICATION.md):223affected
Python methods and15actual-v4 composition cases. No unchanged Solidity/static/
full keeper/website suite was rerun. Actual qualification and independent audit
remain open.

Earlier functional97cbd16 / receipt25ac8d4:
[reward resilience](reports/reward-resilience-20261026/VERIFICATION.md),437affected
Python passes/6skips and one new actual-v4 case retain their original source scope.
No unchanged keeper/claim/full-contract suite was rerun by implication.

Prior allocation/fairness publication0ee9650 and
[receipt](reports/reward-allocation-20261026/PUBLICATION.md) retain their scope;
1,000claim-order fuzz and normal build/static evidence are not rerun by implication.

The preceding published baseline is3ad0e3f (docs receipt), with functional885af8e:
[keeper/LP review](reports/keeper-lp-audit-20261026/REVIEW.md) and
[receipt](reports/keeper-lp-audit-20261026/PUBLICATION.md). It binds loaded-config
health and rejects malformed conversion flags. Website memory-onlyfd8c3e8 remains
its prior verified state; no website update is implied by this contract task.

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
Reference:31contracts/608 functions. Vault runtime22,852; Access constructor total
42,352 in the recorded normal build. Actual release constructor/gas still needs
qualification. No full new regression, green-CI or independent audit is implied.

**Undeployed; production NOT APPROVED.** Actual feeds/routes/RPC/VRF/authorities,
OpenSea primary-mint integration, artwork hosting, explicit current3 website and
service acceptance, gas/strategy economics, operating rehearsals and independent
audit/remediation remain open in the sole Todo. No public contract deployment was requested.

## Workspace and continuation

Contract checkout: `C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2`.
Website checkout: `C:/Users/Ali/Desktop/2.x holas/Oto/aaa-website` (`ABEF/AAA-website`).
Public demonstration: [popldemo.0xwave.com](https://popldemo.0xwave.com).
Separate integration: [www.poplint.0xwave.com](https://www.poplint.0xwave.com).
The user explicitly requested keeping popldemo live and unchanged while building
poplint for current-contract integration; never exchange roots/configs/installers.
Poplint now serves websitef23c559 with HTTPS and a separate certificate-renewal
hook; website main77501ce includes the final operating docs/hook. Demo remains
on9be6d1, unchanged by before/after hashes. See the [serving receipt](reports/current3-website-20261026/DEPLOYMENT.md).
[SITE_ENVIRONMENTS](docs/SITE_ENVIRONMENTS.md) owns the hostname/build/server map.
The extra purchase-rights UI task was declined, not implemented.
Historical native2 readers retain accounting2. The new explicit current3 reader
and unsigned-review implementation belongs to poplint and has451affected JS
passes including46new methods; real contracts/API/provider qualification remains
open. Current3 fixtures use real Python DTO code with synthetic dependencies. Current selectors must be ETH/fixed
ZZZ only and reflect the captured2% default contribution budget (98% deployed),
not historical stablecoin/99% examples. Public transactions are disabled by user
decision, not a missing permission to enable them.

The [documentation reconciliation](reports/documentation-sync-20261026/README.md)
corrects superseded Todo acceptance wording without closing any of its65tasks.
Priorities are actual ETH/ZZZ prices and a cheaper ZZZ-to-ETH conversion route,
matching current3 website/read services, supported OpenSea primary-mint/VRF
integration, then exact-host operating qualification and independent review.
The source-only keeper watchdog still needs a separately authorized Linux
cgroup/signer-stop/journal/no-resend rehearsal; publication does not install it.

Preserve local Anvil/NFT/LP/balances/journals/port8902/dist overlay. Signer remains
Anvil-only, public DEPLOYMENT null, staging monitoring paused. Original dirty
documentation and older checkpoints are backed up outside Git; unrelated code
drafts remain untouched. See [resume instructions](docs/WORK_HANDOFF.md) and
[documentation map](docs/README.md). Verify Git/remote publication separately from
local saves; publication does not deploy the website or contracts.


Current selected-pool harness/RPC: [verification](reports/current-pool-fork-20261026/VERIFICATION.md)
records11successful distinct methods across scoped runs,11runner methods and a
usable keyless Pinax archive at block96,427,989. No fresh whole final11suite or
production provider/feed/VRF/authority qualification is claimed. Both inputs,
small growth and actual fee/ownership behavior pass under stated fixtures;
unfillable larger growth is rejected with atomic rollback. No guard was widened.
