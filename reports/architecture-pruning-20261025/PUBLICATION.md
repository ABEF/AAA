# Architecture pruning publication

Implementation `144d3c9d9dcb73c5aff42adef751eb6bdcae1d10` and website memory-only
`dbd10186ac7f9f777562b1dd933fcdc6e7cfea29` are pushed on **main**. Both exact origin/main
heads were verified at `2026-10-25T19:47:29.798726+00:00`.

This is source/documentation publication, **not deployment**. No public
transaction, website source/build/server, existing8902/Anvil/NFT/LP/balances/
journals/dist overlay, signer, service or paused-monitor change occurred. Public
DEPLOYMENT remains null and signing Anvil-only. Production NOT APPROVED.

The new fresh-deployment profile is accounting3/local8wordPositions, direct
governance2 and canonicalLP_ONLY_V4.31contracts/608functions/13receive hooks;
35fewer functions than baseline. Actual old deployments/readers/journals keep
their original profiles. ETH/fixedZZZ are the only contribution inputs. WETH/
stablecoin royalty/conversion duties and historical decoding remain; integrated
bridge/source remote liquidity code is gone. No issuer/chain NFT-ledger continuity
guarantee follows from external custody exit.

[Verification](VERIFICATION.md):49distinct selected Solidity and512distinct Python
methods pass across precise recorded source/fixture scopes, not a fresh full
regression.127inputs ABI/AST and36normal object gates pass. All41production source
hashes, report artifacts and protected website source hashes match. Original
failures and targeted repairs are retained. Unpublished retired research drafts
remain backed up outside Git; unrelated older drafts were excluded and preserved.

[Bytecode comparison](bytecode-comparison.json) uses identical compiler settings:
13concrete runtimes shrink,16same,2guard-related increases. Controller total
initcode42,177leaves6,975bytes; Vault runtime22,852leaves1,724bytes. RoyaltyFactory
still has69runtime bytes. These are size facts, not gas-optimality or independent
audit claims. Actual matching website3/services, feeds/routes/VRF/authorities/
OpenSea, economic/gas/operating rehearsals and independent audit remain open.

See [review](REVIEW.md), [profile guide](../../docs/POSITION_V3.md) and
[published scope](FINAL_SCOPE.json). Historical compiler/fixture repair scripts
are evidence, not operational commands to mutate an existing deployment.
This receipt is a separate documentation commit and changes no tested code.
