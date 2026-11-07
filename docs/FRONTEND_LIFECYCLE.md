# Confirmed API lifecycle and handoff boundary

The API checks the sealed canonical deployment at the same confirmed block hash
as its balances. This is an unhosted backend implementation; no website or server
was updated. Remaining work belongs to the [read API task](../TODO.md#task-read-api).

## Configuration and response version

Configuration and read responses use **schema 2**. The current release explicitly
selects `accounting_version:7`, explicit custody5/ProtocolPolicy1/fee-intake1,
original-currency royalty reporting5, LP-allocation1 and
`ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9`. The Position codec retains eight words
and Exited5/Dormant3/Parked4. Require the complete independently reviewed runtime
graph in the [read API](FRONTEND_API.md#current-deployment-profile), including
Rewards.canonicalModule(), its fixed access/rewards parents and Handoff.moduleAt(3).
Every request checks runtime hashes and sealed module/helper ownership links.
Historical6/V8 and older readers retain their actual graphs; accounting4 has nine
base pins and accounting3 eight. No old runtime or journal is relabeled.
Existing schema1 configuration fails closed.
An RPC-discovered peer is never automatically accepted as a new deployment.

## Endpoints

| Request | Operating deployment | Frozen / importing / retired / cancelled |
| --- | --- | --- |
| `GET /v1/protocol` | Lifecycle, pause/preparation, original identity and predecessor | Same status fields; retired source also identifies its committed successor |
| `GET /v1/nfts/{id}` | Current verified NFT and funded balances, with lifecycle | HTTP 503 before reading ownership, asset inventories or claimable balances |
| `GET /v1/wallets/{address}/nfts` | Current verified ownership when indexed history is configured | HTTP 503; never a misleading empty or spendable portfolio |

The status endpoint does not call asset lists, token decimals, price feeds or
reward balances. Those can be unavailable after backing has moved. It still
requires valid pinned deployment bindings, lifecycle getters and a fresh canonical
snapshot. Missing/malformed/unknown values, inconsistent phase/state combinations,
wrong origins or helper owners fail closed. No old-interface or `latest` fallback
exists, and all HTTP error bodies remain sanitized.

`lifecycle` reports:

- `state` and `state_code`, the coordinator's `handoff_phase`,
  `preparation_active` and `paused`.
- `origin.chain_id` and `origin.vault`, preserving the original identity namespace.
  Importing/cancelled destinations return `origin: null` and
  `origin_available: false`: their constructor or partially imported identity
  must not be advertised as an activated collection origin.
- `predecessor_controller`, when imported; `successor_controller` only after
  retirement. A restored abort's stale destination is never advertised as a
  successor. `handoff_destination_controller` is reported for a frozen/retired
  source, not as proof that a candidate is active.
- `claims_available_by_lifecycle`, `transfers_available_by_lifecycle` and
  `new_economic_work_available_by_lifecycle`. These are lifecycle permissions,
  not guarantees of token availability, owner authorization, successful execution
  or fee earnings. Pause/preparation does not remove operating holders' funded
  claim or transfer rights; it blocks new economic work.
- `peer_deployments_verified: false`. Peer addresses are commitments read from
  the pinned source, not an independently reviewed destination deployment or a
  cross-chain finality proof. No automatic redirect or peer RPC call occurs.

Accounting4–7 read the irreversible `lp_exit_started` flag and
`lp_exit_phase` / `lp_exit_phase_code` (operating0/closing1/allocating2/ready3).
The module phase and Access flag must agree. After
collective exit begins, new economic work is false even if governance unpauses.
Claims/transfers remain available while canonical state is operating. Terminal
principal-return accounting is separate from funded reward/royalty balances.
LP exit and canonical handoff cannot coexist; the canonical transport does
not carry principal-return liabilities, so replacement stays blocked after exit.

## History continuity

An operating successor can expose its funded balances and independently checked
current ownership. Its local history alone cannot prove lifetime claims across
previous deployments. With the optional [complete predecessor configuration](FRONTEND_LINEAGE.md),
the API now verifies same-chain retirement/activation links and replays all prior
LP/royalty claims. Without it, imported successor lifetime totals remain
unavailable, even if current history contains nonzero claims. Invalid configured
lineage fails closed; zero and partial totals are never substituted. Current V9 source
and successor require accounting7/LP-allocation1; historical6/V8, V5 accounting5/4 andV4 accounting3
retain their separately pinned profiles. They must
use the same canonical schema and codec; historical
reader support does not add cross-codec import compatibility.

Wallet inventory describes current ownership only and does not classify imported
transfers as paid sales. Cross-chain collection relocation is outside this release;
collective principal return does not move the NFT or reward ledgers. Marketplace
cutover and operating qualification remain in the [central Todo](../TODO.md).

## Verification and operational scope

The earlier [source-bound verification](../reports/frontend-lifecycle/VERIFICATION.md)
records its original lifecycle/API candidate. It does not qualify later Position3,
direct-governance or V4 changes. Current exact-LP integration is recorded in
[its scoped review](../reports/exact-lp-integration-20261106/REVIEW.md);
no production operating approval or broad fresh regression is inferred.

Every read uses EIP-1898 `requireCanonical` with one block hash. Final checks
revalidate the full header, deployment anchor, chain, confirmation depth and age
after the last RPC response. Confirmation depth is not protocol finality; a later
reorg remains possible. Responses are `no-store`. Downstream wallets still need
current owner/network/deployment checks, simulation, gas estimation and canonical
receipt handling before treating a transaction as successful.
