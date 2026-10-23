# Governed custody: scoped internal review

Development candidate; not an independent audit or approval for real funds.

## Authority and accepted trust

Governance can approve an EOA/contract recipient with immediate authority. The
source cannot enforce how that recipient uses assets or compel their return.
Neither a runtime hash nor a review reference proves honest recipient behavior;
proxy implementations, signer controls, issuer rights and bridge safety require
independent review. Raw emergency mode deliberately removes the USD loss promise.
No on-chain constraint makes externally custodied principal trustless/permanent.

## Reviewed boundaries

| Boundary | Current control / evidence |
| --- | --- |
| Approval drift and recipient | Exact live source snapshot, code identity, one plan per bucket, fresh deadline, governance authorization; stale/duplicate/invalid destination cases reject. |
| Helper authority | Immutable parent-bound view-only request/destination/parking validation; no token call execution, approval or custody endpoint; mirrored Request ABI checked. |
| Normal execution loss | Source principal + attributed idle valued at original reviewed prices. Explicit all-ZZZ exit minimum and actual local redeployment preserve the same 97% floor; network gas separate. |
| Emergency handling | Separately approved raw mode, explicit close minima, no automatic downgrade when a normal swap fails. Transfer failures roll back exit. Failed/frozen/nontransferable tokens or venues can still prevent movement. |
| Original economic rights | NFT shares unchanged; late creator funding and accrued rewards stay claimable by the current NFT owner. Principal does not sweep royalties, fee reserves, another bucket or unsolicited balances. |
| Destination selection | Existing admitted/reserved local target; holding can bind one target after departure without rewriting source amount, budget or raw mode. Actual funded LP required; balances alone do not complete it. |
| Remote acknowledgement | Domain-separated delivery and return/closure commitments; pinned verifier; no multisig-only, timeout or partial write-off. Test verifier is a fake, not consensus security evidence. |
| Royalty currency custody | Full admitted raw currency only; previous liabilities/quarantine remain. That currency is unavailable until actual full restoration. No donation substitution or new earnings on return; healthy currencies/LP remain separate. |
| Replacement preparation | Capture requires no unresolved principal/royalty custody. Resolve principal before preparation or cancel the exact notice first; stopping custody does not erase it. |
| Obsolete execution paths | Five old LP transport/pair implementations removed; retired controller roles reject binding. Vault legacy import selectors always revert. Historical fee interfaces/record fields do not authorize a new receiver. |
| Deployability | Original compiler profile; normal source-object runtime/initcode gates. This is not measured target-chain gas or an actual deployment hash. |

## Remaining qualification

- Fresh isolated Anvil custody journey, actual venue exit depth, tokens, wrapper,
  swap routes, issuer exchange mechanics, feeds, gas and adverse market behavior.
- Complete governed-v1 production inventory; current template explicitly blocks.
- Keeper/API/indexer exposure of pending principal/royalty custody and new events.
- Real finality verifier/transport, remote reward and canonical ownership ledgers;
  full cross-chain relocation and post-halt recovery are not supplied here.
- Recipient signer/contract/proxy safety, production role addresses, creator terms,
  independent cross-contract/economic audit and remediation.
- Normal per-operation checks do not insure market risk or cumulative losses.

See [verification](VERIFICATION.md), [operator procedure](../../docs/GOVERNED_CUSTODY_HANDOFF.md)
and the [single Todo](../../TODO.md#task-custody-composition).
