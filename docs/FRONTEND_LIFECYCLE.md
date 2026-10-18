# Confirmed API lifecycle and handoff boundary

The API checks the sealed canonical deployment at the same confirmed block hash
as its balances. This is an unhosted backend implementation; no website or server
was updated. Remaining work belongs to the [read API task](../TODO.md#task-read-api).

## Configuration and response version

Configuration and read responses now require **schema 2**. Existing schema-1
configurations fail closed. Add independently reviewed runtime/address pins for
`contracts.handoff` and `contracts.vault_canonical`, using the same object format
as the other six contracts. Eight distinct contracts are required. Every request
checks their runtime hashes and sealed controller/module/helper ownership links.
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

## History continuity

An operating successor can expose its funded balances and independently checked
current ownership. Its local history alone cannot prove lifetime claims across
previous deployments. Whenever `predecessor_controller` is present, the NFT
response returns `previously_claimed.available: false`, `assets: null` and an
explicit reason, even if the current deployment's index contains nonzero claims.
Zero and partial totals must not be substituted. Wallet inventory describes
current ownership only; it does not classify imported mint events as paid sales.

Complete predecessor-chain authentication, claim replay across deployments,
duplicate/reorg handling and marketplace collection cutover remain in the
[central Todo](../TODO.md#task-read-api). This guard does not implement that replay.

## Verification and operational scope

See the [source-bound verification](../reports/frontend-lifecycle/VERIFICATION.md)
for boundary, HTTP, real local indexer/history and regression checks. Production
Solidity is unchanged. Existing compiler ABIs are checked against matching source
identities rather than recompiling unchanged contracts.

Every read uses EIP-1898 `requireCanonical` with one block hash. Final checks
revalidate the full header, deployment anchor, chain, confirmation depth and age
after the last RPC response. Confirmation depth is not protocol finality; a later
reorg remains possible. Responses are `no-store`. Downstream wallets still need
current owner/network/deployment checks, simulation, gas estimation and canonical
receipt handling before treating a transaction as successful.
