# Isolated $1 activation rehearsal

Fresh [accounting6](POSITION_V6.md) uses governed contribution minima. It needs
**no source-patched $1 build**. Its defaults remain $100 activation, $5 growth,
0.05 ETH direct mint and the existing contribution-loss policy. No existing
deployment, service, wallet flow or saved journal changes through this guide.

## Current policy procedure

Use only a separately authorized, isolated test deployment with disposable funds
and reviewed profile6 contracts. This procedure does not authorize deployment,
sealing, signing, public transactions or changing the preserved Anvil stack.

1. Read the deployment's controller, bound ProtocolPolicy, runtime/profile pins,
   governance/bootstrap authority, lifecycle and complete `entryPolicy()` tuple.
   Preserve the original tuple and its fingerprint for the rehearsal record.
2. The authorized configuring wallet may review
   `ProtocolPolicy.setEntryPolicy(1e18,1e18,reviewedIdleBps,reviewHash)`.
   Both minima must be at least $1 and growth cannot exceed activation. Use the
   previously reviewed idle setting unless a separate change is justified; this
   is not permission to widen execution loss, source prices or idle policy.
3. The pool's `minDepositUSD` must also permit $1. It is an independent stronger
   minimum, changed through the full reviewed native ETH/fixed-ZZZ pool config.
   Preserve every unrelated pool setting, exact token identity and custody.
4. Simulate and review each exact operation before any separately authorized
   submission. Confirm actual configuration/events, original-source value,
   marginal new LP, shares, retained backing and gas. With the default 2% loss
   cap, $1 of conservative input still needs at least $0.98 of new deployed LP.
   An oracle-priced token is not assumed to equal $1 per unit.
5. Restore the explicitly reviewed production minima/pool settings before a
   release candidate is considered. Read actual values rather than assuming
   defaults. Policy revisions change even when old numeric values are restored;
   prepare new reviews and reconcile any already-submitted transaction by hash.

Mint terms are separate: lowering contribution minima does not lower the mint
price, redirect mint proceeds, alter rarity/royalties or change the 80/10/5/5 LP
split. The test still needs qualified dependencies and executable routes; a $1
minimum does not guarantee economically viable execution. Public website
deployment remains null and browser signing remains Anvil-only.

## Historical source-patch tool

[prepare-dollar-rehearsal.py](../scripts/prepare-dollar-rehearsal.py) is retained
only for compatible historical source snapshots. The current accounting6+ source
is refused **before compiler lookup, fixture copying, transformation or output
creation**, with a redirect to the governed procedure above. Removing the policy
source file does not bypass an accounting6+ Vault marker. Unknown or changed
legacy patch anchors also fail closed.

For compatible older copies, the tool retains its original two activation-floor
patches and local-chain constructor guards, derives loss caps from the actual
copied Budget and writes source/compiler hashes into a new external directory.
It copies no deployment scripts, keys, RPC configuration or broadcasting tool.
Its fixtures are explicit local substitutes, not production qualification.
Historical generated artifacts and [their evidence](../reports/one-dollar-rehearsal/VERIFICATION.md)
keep their original source/runtime scope; they are never promoted to profile6.

Real routes, dual feeds, wallet/API integration, target-chain gas and operating
rehearsals remain in the [central Todo](../TODO.md#task-testnet-rehearsal).
Stopping a rehearsal cannot erase minted NFTs, chain history or remaining
liabilities. Principal return follows the reviewed collective-exit process;
there is no reset, operator sweep or custody-wallet shortcut.
