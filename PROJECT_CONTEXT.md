# PoPL current project context

Reviewed5November2026. Pre-settlement2 task baseline main
`bce897c480cd7df67e4936d278d51908d3d7885f`; verify actual local/remote heads before
claiming publication. Read [instructions](AGENTS.md), [README](README.md),
[sole Todo](TODO.md), [handoff](docs/WORK_HANDOFF.md) and
[Operator manual](docs/OPERATOR_MANUAL.md). **Undeployed; production NOT APPROVED.**
Repository memory is not a background synchronization service.

## Product, rights and source identity

1,000 transferable ERC721 NFTs, exact final600Commun/300Rare/100Legendary quotas.
Fixed artwork draw/reveal, one fixed ZZZ token and native ETH for contributions.
Default activation$100/growth$5; future policy minima>=1USD and growth<=activation,
with stronger admitted limits. Current owners inherit all unpaid rights.

Fresh accounting6/ProtocolPolicy1/portfolio2/maintenance3/confirmation3/compound4/
custody5/emergency2/LP-routing2, pricing2/direct Entry3/review2/governance2/fee1,
royalty settlement2/recovery2. Schema11 inventory17modules/18helpers. Position is eight words;
parked same-chain canonicalV6 wire compatibility never implies runtime compatibility.
[Exact profile](docs/POSITION_V6.md). Preserve historical codecs/readers/journals.

## LP operation and economics

One contribution pool at a time, at most4historical custody buckets. Each bucket
has one main or optional one residual in the same ETH/fixed-ZZZ pool; both LP NFTs
stay Vault-owned. Default single mode. At replacement main>=60% and residual<=40%,
not a continuous target; initial residual half-side5000bps with positive spacing.
Both legs remain valued/harvested/closed until a guarded merge succeeds.

Activation/growth checkpoint incumbents, deploy entrant funds to MAIN only, prove
actual marginal LP and issue shares from aggregate NAV. No clock reset, recenter,
residual change or subsidy from earlier LP/idle/compound. Two reviewed independent
USD sources must agree within3%. Contribution/conversion/maintenance defaults
2%/1%/3%, ceilings10%, gas separate. Additional1%loss after known fees, default5%
idle, caller minima and placement floors are distinct controls.

Ordinary85%centre-to-boundary human ZZZ-in-ETH threshold requires same-side physical
and independent corroboration,600seconds sampled persistence/maxgap300,
240-second raw checks and durable60–300jitter after initial hard12hours. Paid
sample enrollment begins near eligibility; contribution liquidity does not reset
stable geometry. Samples do not prove uninterrupted history or MEV immunity.

Hourly actual harvest allocates fixed80/10/5/5: individual/equal active collective/
compound/fixed-ZZZ buyback-burn. Compound has its own interval and service waits
for in-range/below-trigger/no-pending-geometry state. Harvest, conversion,
compounding, burn and claims remain separate; no holder loop at harvest.

## Royalties and manual allocation

Fresh settlement2/recovery2 removes royalty swapping, unwrap, converter binding
and keeper conversion. Each admitted currency remains itself; owner mixed claims
support32total NFT/asset/ledger operations. Rarity1/2/3, incumbent receipts,
outage cohorts, fractions and transferred unpaid rights remain. Governance
allocateUnallocated(asset,amount,reviewHash) only allocates admitted orphaned
units in that SAME currency at active weights now; earned/deferred liabilities
are excluded. Unsupported tokens require review/admission within16ERC20 plusETH.
No price feed is needed for original claims; missing USD reporting stays unknown.
LP conversion stays separate. Reporting3/converter:null and keeper explicit
royalty_settlement_version2 select fresh behavior; old profiles remain historical.
New ledger storage/runtime and event semantics require fresh bindings and reviewed
checkpoint rebuild, never a relabeled deployment/journal.

## Documentation and verification

[Operator tables](docs/OPERATOR_MANUAL.md#operator-call-tables) cover797functions,
36constructors and12receivers. Four columns, <=5word descriptions, complete typed
input examples with unresolved live values. Reads/callbacks/module-only hooks are
separate from human actions. Never treat these as simulated wallet transactions.
Notes/ABI/examples and generated tables must update together; normal verification
checks both generators. Historical plans now link their exact original Git text.

[Current original-currency verification](reports/royalties-in-kind-20261105/VERIFICATION.md)
binds51production/31dependency sources,42normal size gates and466static contexts
(25current/441exact reuse).58selected EVM methods pass, including1000NFT mixed
wallets and1000-input conservation fuzz;144affected Python methods pass at their
recorded stage. Migration39/Vault635/Budget237/Balancer360runtime margins remain;
royalty18580/factory20127bytes are smaller. No independent or actual target-gas approval.


Checkpoint1 is implemented only for opt-in fresh6/5/1single-deployment earnings.
Other history readers/lineage/archive/rotation/workload qualification remain open;
semantic parser changes require reviewed checkpoint rebuild/re-pin. Claims,
conversion/import and returned principal are not new earned income; first
unallocated recovery is income only at its explicit allocation event.

## Preserved environments and next work

Main only. Preserve the four protected tracked dirty files, original Anvil8902
NFTs/LP/balances, pending/nonce/receipt/spend journals and dist overlays. Popldemo
is simulation; separately served poplint is current3/unconfigured read/unsigned
integration, not fresh source8/accounting6. Public DEPLOYMENT null; browser signing
Anvil-only. User-paused heartbeat stays paused. No deployment, transaction,
sealing, service/site restart, journal migration or signer expansion is authorized.

Actual dual feeds, routes, VRF, authorities, OpenSea primary integration and any
transfer-enforcement decision, matching services/site, metadata hosting, operating
rehearsals/restore, economics/target gas and independent audit/remediation remain
under the [sole Todo](TODO.md). Keep source implementation, local evidence,
published code and operating qualification distinct.
