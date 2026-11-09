# Phased OpenSea mint integration — source candidate

Reviewed 9 November 2026 from main `15791864437ec8f35414e17d338380a484af5094`.
**Production NOT APPROVED. No deployment, public transaction, service/site,
signer, Anvil8902, journal or heartbeat change.**

## Result and decisions

The previously open custom-primary-mint source path is implemented against the
exact verified Robinhood SeaDrop V1 runtime. It preserves PoPL's dormant NFT,
canonical hashed IDs, original two-word randomness requests, fixed artwork
inventory and existing LP/royalty economic rights.

| Phase | Initial supply | Price | Unused supply |
| --- | --- | --- | --- |
| TEAM | 20 | Free, gas separate | Reserved; does not roll into public |
| Allowlist | 500, one per distinct listed address | Governed price, initially 0.05 ETH gross | Rolls into public FCFS |
| Public | Initially 480 | Same governed price | Cannot consume reserved, unminted TEAM slots |

Allocations, sequential sale windows, future price, cumulative public wallet cap
and batch size are reviewed future configuration. Total supply remains 1,000;
issued counts never reset. Initial TEAM/allowlist lists are disjoint in the
maintained builder. Public per-wallet limits include that original recipient's
earlier mints; transfers never restore an allowance. These are address limits,
not per-person or Sybil-resistance guarantees.

The buyer's paid gross includes the actual platform fee; the creator receives
the remainder. Actual fee BPS/recipient, payer permissions, dates, allowlist and
provider configuration remain unselected or unqualified. No mock value is a
recommended launch address or platform term.

## Evidence-based implementation boundary

The pinned [official registry](https://github.com/ProjectOpenSea/seadrop/blob/d368f55f609a7f4b2245f89ff49c1a933fbeff83/docs/Deployments.md)
identifies Robinhood Chain4663 as a standard drop network. The independently read
SeaDrop at `0x00005EA00Ac477B1030CE78506496e8C2dE24bf5` matches the
[verified deployed source/runtime](https://robinhoodchain.blockscout.com/address/0x00005EA00Ac477B1030CE78506496e8C2dE24bf5?tab=contract).
The 21,081-byte runtime Keccak is
`0x53e4b9339cf624803c9a7d0195576cca5b917920813508d86b3eb93dcbabeb5c`.
Original registry, explorer, source/dependency and read-only RPC responses are
retained in this report's evidence. This does not establish OpenSea accepting the
custom collection in its UI/API product.

The important difference from direct-Vault minting is that SeaDrop calls the NFT
with **zero ETH**, then settles its platform fee and creator net payment. The
new fixed helper authenticates that exact caller/runtime and full reviewed sale
configuration; it reserves the whole batch before receiver callbacks. The Vault
records IDs through its existing selector, and the NFT requests randomness and
safely mints. Failed proof/payment/callback/request or final configuration checks
roll back the complete transaction. There is no extra paid-Vault mint, nested
reentrancy workaround, arbitrary executor or new proceeds/custody recipient.

`Vault.DormantMinted` reports zero received payment on this path. Primary-sale
gross/fee/net accounting must use authenticated SeaDrop receipts and actual
balance changes, never interpret that zero as a free mint or LP/royalty income.

## Material changes

| Area | Change | Classification |
| --- | --- | --- |
| NFT / typed SeaDrop base | Fixed pre-seal helper binding, exact 11-selector interface, zero-value mint callback; direct paid mint disabled when bound | New primary-mint behavior |
| Mint helper | Separate reviewed quotas, lifetime/original-recipient counters, phase/window/fee/payer/root/price validation and callback-safe batch reservations | New feature and security boundary |
| Vault / fixed canonical companion | Existing `mintDormant(bytes32)` distinguishes authenticated NFT callbacks from explicit unbound direct-test configuration | Typed integration; no new Vault selector |
| NFT metadata | Predeployed fixed/controller-checked renderer; constructor now takes renderer; existing read-only metadata orchestration moved to it | Size-driven refactor; metadata semantics preserved |
| Royalties quote | Exact 5% integer result uses `salePrice / 20` | Behavior-preserving simplification for full uint256 domain |
| Canonical V10 | NFT records add original recipient and phase; imports rebuild mint counters and bind source/destination mint mode/runtime/config | Explicit schema/accounting extension; V9 NFT records rejected |
| Inventory17 | Validator/observer authenticate 20 callable helpers plus two inert Factory data children and exact mint books | Explicit new profile; old16 template retained |
| Backend opt-in2 | Same-block helper/SeaDrop pins, V10 read/claim/lineage support; direct mint preparation rejects with Use OpenSea | Explicit consumer support; default1 stays V9 |
| Offline proof builder | Exact source-bound manifest, one-hash ABI leaves, sorted Merkle pairs, strict team/allowlist configuration and exclusive output/checking | Unsigned/offline operator tooling |
| Operator/reference/docs | Current 39-contract ABI reference, expanded exact examples and launch/reconfiguration/recovery procedure | Documentation and maintenance |

Accounting7/LP-allocation1, royalty4, actual 80/10/5/5, current-owner unclaimed
rights, principal custody, contribution/maintenance budgets, holder return and
no-bridge rules remain unchanged. Original LP and royalty body formats are
retained inside the new outer canonical schema. The unchanged royalty Factory
creation payload and both data parts remain byte-identical.

## Reviewed risks and operational limits

1. **Opaque proof roots remain a governance/review trust boundary.** The actual
   SeaDrop callback does not expose price, phase, payer or proof parameters.
   Contract checks, disjoint windows and independent quotas constrain the mint;
   the strict builder binds intended leaf terms. Same-current-root term changes
   are rejected, but initial or historically reused root content is not proved
   by a nonzero reviewHash. Review the complete leaves/proofs and actual platform
   transaction; signed and token-gated minting remain disabled.
2. **Configuration can change before inclusion.** SeaDrop buyer calldata does
   not carry PoPL's custom expected-policy hash. Exact gross payment is enforced,
   but governance may change current fee/net/payee at unchanged gross. The NFT's
   final checks precede SeaDrop payment callbacks; SeaDrop captures its payout
   address before transfers. No invented post-payment NFT callback/outer lock is
   claimed. Pause, reconcile, review and simulate before live configuration changes.
3. **Wallet/stage counters survive transfer and replacement.** Lifetime original
   mints are distinct from current owner balances. V10 rebuilds them from original
   recipients, including dormant NFTs; old V9 records and incompatible mint
   policies are rejected. Whole six-domain commit and fully funded abort are
   locally exercised with positive claims, not just zero preview comparisons.
4. **Reserved TEAM means reserved, not always mintable.** It still needs a valid
   TEAM window/root. Windows are inclusive and disjoint. Reconfiguration must
   respect the official final sale end; after that end passes the existing mint
   cannot reopen. Under-subscription does not delay the one-hour royalty window.
5. **Bindings are release identities.** NFT renderer and mint helper are fixed
   before seal; helper pins actual SeaDrop code. No production script guesses
   those addresses. The local-only deployment scaffold stays unsealed and does
   not represent a complete SeaDrop release deployment.
6. **Runtime space is tight.** Vault has32 bytes and Handoff176 bytes of normal
   runtime headroom. No compiler/size/security guard was relaxed. Future changes
   require new exact normal/static evidence and likely further decomposition;
   passing current limits does not qualify deployment gas or future capacity.
7. **Mutable sale readiness does not block earned claims.** Explicit backend2
   authenticates immutable mint identities for reads/claims; it does not require
   a currently mintable phase/proof. Protocol stage availability stays unknown
   until actual eligibility is verified. Each lineage peer selects its version
   explicitly; source9 website/old consumers are not silently promoted.
8. **Codehash is only the checked runtime identity.** Upstream behavior, actual
   OpenSea acceptance, wallets, routes, VRF, providers, gas and operating recovery
   still need release-specific qualification and independent review.

## Verification and remaining work

See [verification](VERIFICATION.md) for exact stages, source hashes, retained
failures, normal/runtime limits,558 static dispositions and focused EVM/Python
checks. No full-suite, published-CI, independent-audit, target-gas, uninterrupted
service or live-wallet claim is made.

The [sole Todo](../../TODO.md#task-opensea-mint) retains this task in progress.
Remaining launch work includes actual custom-drop/API onboarding; platform fee,
payer and metadata requirements; real VRF/funding/callback qualification; exact
authority/configuration/deployment arguments; matching website/services and
wallets; target-chain gas/economic and recovery rehearsals; and independent
audit/remediation. Follow the [operator procedure](../../docs/OPENSEA_MINT.md).
Publication changes none of the running environments or user-paused monitoring.
