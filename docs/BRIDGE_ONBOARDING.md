# Future chain, pool and bridge onboarding

The vault, economic bridge adapter and custody router are bound once and remain fixed after sealing. The router can start with no policies: local mint, activation and permanent top-ups do not require a bridge. Outbound migration is unavailable until governance approves a provider policy, registers compatible routes and explicitly enables that source policy. This framework is implemented; actual bridge SDK wrappers and funded cross-chain validation are still pending.

## Immutable identities

`TransportPolicy` identifies a reviewed/versioned provider, both EVM chain IDs, source/destination routers and SDK wrappers, wrapper runtime and channel-configuration hashes, provider-specific channel ID, and review-evidence digest. Its ID is `keccak256(abi.encode(policy))`. Registration is append-only. The evidence digest is a reference, not on-chain proof or an audit certificate.

The registry stores `transportPolicyId(routeId)` permanently. A route ID is now `keccak256(abi.encode(route, policyId))`, including the full economic vault/adapter/receiver/pool and ordered asset mapping. `Route` and version-2 economic-message layouts remain unchanged, but `add(Route,bytes32)` replaces the old registration ABI and route IDs must be regenerated. The version-1 transport envelope contains the policy ID and version-2 message bytes. Indexers/operators must use the emitted policy-bound IDs.

Changing providers, channels, settings or peers requires a new policy and new routes. An existing migration plan cannot silently switch providers. Existing nonces and replay domains span providers: `keccak256(abi.encode(sourceChain, sourceEconomicAdapter, nonce))`.

## Approval and execution

After sealing, only the governance timelock can register policies/routes or enable a source policy. The local template has a two-day timelock; each principal move also has the existing two-day migration delay. Guardians can pause outbound operations. Neither governance nor a provider has a router withdrawal, arbitrary-call, refund, upgrade or delegatecall entrypoint.

For each future hop, review destination vault permanence and authorities, supported pool, asset equivalence/decimals, local and remote wrapper identities, bridge security/finality/backing, fee payment and recovery. Deploy and verify destination peers and wrappers separately. Register the identical policy/route on participating chains, plus canonical remote-only metadata for onward custody history. Register return, source-completion ACK, canonical-location ACK and legacy reward routes. Enable the source policy only after staged delivery evidence. The canonical chain may record remote-only graph metadata; it cannot verify remote runtime code on-chain.

`propose` and `execute` both check source readiness before closing LP. The router checks it again before sending. Each local wrapper must report this router and the captured channel configuration, and its runtime hash must match. Sends transfer only the route's exact logical token vector with temporary, cleared approvals; partial consumption, zero receipts, configuration drift during send and pre-existing balance changes revert atomically. Native value is the caller-supplied bridge operating fee, not principal or mint revenue.

## Pending messages and recovery

Disabling a route or source policy stops new sends. It does not erase historical policies or prevent authenticated, exactly funded pending inbound settlement, even during a pause. Old providers can settle their own bound routes; they cannot settle a new provider's route. Wrong origin, provider, envelope policy, ordered tokens, amounts or replay reject. Failed handoff reverts funding and replay markers so the authentic delivery can be retried. Destination LP activation and ACK retries remain separate operations.

A wrapper must authenticate source chain/router with its SDK, enforce finality and backed asset equivalence, then atomically hand off exactly two logical principal entries (a zero slot is allowed), one reward entry or zero ACK entries. Providers with per-token messages, dust trimming or separate compose execution need separately reviewed staging/normalization logic. These behaviors are not implemented by the router. No timeout withdrawal is safe merely because a bridge is slow.

## Trust and limits

Governance still chooses future custody code and bridge providers. A timelock provides notice, not a guarantee of principal safety. Runtime hashes do not detect implementation upgrades behind unchanged proxy bytecode; configuration getters are useful only if reviewed wrappers faithfully commit to all actual settings. Bridge administrators, verification networks, remote chains and asset backing remain external trust assumptions. Inbound code/configuration drift deliberately fails closed and can halt settlement; do not mutate an active wrapper/channel, and preserve old immutable wrappers for pending messages.

Migration supports future EVM chains and equivalent assets in identical nominal units. It does not promise arbitrary asset conversion, bridge availability, capital value, satellite user top-ups or migration of the economic NFT. NFTs and contribution Power stay on their canonical chain. Actual providers, multi-chain rehearsal and an independent security/deployment review are required before funded use.
