# Audit publication receipt - 2026-10-24

| Repository | Published scope | Commit |
| --- | --- | --- |
| ABEF/AAA | Fee-aware ERC20/native Strategy, evidence-reader hardening, focused tests, current docs/operator/Todo and broader native ETH design audit | [e6b5872](https://github.com/ABEF/AAA/commit/e6b587281c3c050f2a5d86195c02657bc85fe25a) |
| ABEF/AAA-website | Both repository memories only; website source/build/server unchanged | [7849376](https://github.com/ABEF/AAA-website/commit/78493763bd629a52077e4e259395db7de22ba566) |

Both were pushed normally to main and verified using remote branch hashes before
this receipt. The receipt and final contract-memory status are a separate docs-only
follow-up. No branch, PR, force push, public deployment or transaction was created.

[Internal review and scope](REVIEW.md): four new Solidity regressions pass;
58 affected existing cases passed and two stale fixture cases failed, then only
the two repaired cases were rerun and passed. Nine mocked observer tests pass.
All95 final Solidity/test hashes match the published snapshot. Changed Strategy
runtime12,862/initcode13,318 passes normal gates;32 unchanged object gates are
reused. No full fresh regression, new fork, independent audit or release approval
is claimed. Evidence hashes and intended-index file links pass; Todo is generated
and checked from the sole ledger.

The broader native ETH redesign WAS audited as a design. It remains unimplemented.
Its exact identity, indices, historical backing, two-stage handoff/abort, receiver
protection, wrapper independence, schemas and per-epoch service trace requirements
are now explicit pre-seal gates. Current raw exit still sends WETH/ZZZ and depends
on the wrapper. The1% conversion cap remains; a cheaper route is still required.

No private key access, website code/build/server change, Anvil/8902/NFT/LP/balance/
journal modification, service control or monitor restart. Anvil-only signer and
null public DEPLOYMENT remain. Older unrelated local drafts were left unstaged.
Production remains NOT APPROVED.
