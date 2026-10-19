# Replacement holder preflight verification

2026-10-19. **Read-only implementation; no production or escrow approval.**

[Twelve targeted Python tests passed](verification.json), no failures or skips.
They exercise confirmed hash reads, source/runtime/NFT binding checks, an optional
distinct inert destination, active/frozen lifecycle, 1,000-NFT paged coverage,
missing/duplicate/mixed/corrupt observations, zero owners, malformed account code,
contract and delegated-account flags, chain/reorg/confirmation rejection and
bounded-work failure. Mock RPC accepts only read methods. No public RPC, deployment,
signer, website/server or monitor was used.

The [tool](../../scripts/inventory-nft-holders.py) and
[implementation](../../zzz_ops/holder_preflight.py) never authorize migration.
The [operator procedure](../../docs/HOLDER_PREFLIGHT.md) requires reviewing exact
replacement withdrawal/claim behavior, resolving incompatible escrows before
freeze, rescanning frozen ownership, and using funded abort before withdrawals
if a problem is discovered after freeze. Retirement remains irreversible.

Internal review checked these boundaries:

- Pages cannot silently fall back to latest reads or combine different snapshots.
  All NFT/owner code reads use the explicit canonical block hash; final header and
  confirmation checks reject a changed anchor. An old snapshot remains historical,
  not automatically valid for committing a handoff.
- A checksum detects accidental file changes, not an adversary forging local
  evidence. This CLI takes trusted operator configuration; providers and reviews
  remain trust boundaries. Use independent evidence for release decisions.
- No-code owners are not declared safe EOAs. Code-bearing owners are always
  unresolved; neither a receiver interface nor a runtime hash proves an escrow
  can release the replacement. Proxy/admin/delegation review remains manual.
- No arbitrary transaction, approval, owner rewrite, NFT transfer or test callback
  is executed. No unreviewed “compatible” flag grants automatic release approval.
- Page bounds, RPC work/time limits and sanitized CLI errors constrain failure.
  Failed reads do not create successful pages; exclusive output creation protects
  previously saved observations. Offline summary makes missing coverage explicit.

Solidity, keeper execution and shared RPC code are unchanged in this follow-up.
Their existing source-bound evidence was reused; no contract regression was
repeated. The preceding [royalty verification](../royalty-conversion/VERIFICATION.md)
remains the latest affected contract evidence. Actual escrow/marketplace operation,
independent review and canonical migration qualification remain open in the
[central Todo](../../TODO.md#task-security-chain-recovery).
