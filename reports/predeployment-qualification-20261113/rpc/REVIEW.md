# Independent genesis and complete read-only RPC profile

13 November2026; source baseline `11e74883787e32e816b5c01b1213189400fe01fe`.
**The independently established genesis identity and all13 existing
`activation_api_v1` compatibility checks pass.** This is a point-in-time public
RPC result. It does not approve a provider, prove full20M/24M capacity or archive
reliability, qualify markets/fees, or authorize deployment and service adoption.

## Establish identity independently

The [official full-node guide](https://docs.robinhood.com/chain/run-a-full-node/)
links the retained [network configuration](OFFICIAL_NETWORK.json) and genesis
allocation. They identify chain4663, parent Ethereum1, genesis block0, and rollup
`0x23A19d23e89166adedbDcB432518AB01e4272D94`, deployed at Ethereum24994238.
Neither document directly publishes the expected block hash. The626,691-byte
genesis includes ArbOS initialization; hashing only its Ethereum allocations
would be an unjustified substitute. No such shortcut was used.

The expected hash instead comes from the rollup's **initial Ethereum assertion**,
read through the separately operated [Flashbots RPC](https://docs.flashbots.net/flashbots-protect/quick-start).
At deployment block24994238, canonical header
`0xeaf9c755467675307cb7431deeed7e60cdb5be8fd0f632994a6347e2ad5cb190`
was rechecked after reading the rollup's logs and deployment transaction.

Captured Nitro source snapshots establish the exact event/struct layout:

- `BeforeStateData` occupies7 ABI words and the preceding `AssertionState`6.
  The genesis `afterState` therefore begins at word13 of the25-word event.
- The unique initial `AssertionCreated` has a zero parent and empty before-state.
  Its `afterState.globalState.bytes32Vals[0]` is the initial L2 block hash;
  `GlobalState.getBlockHash()` explicitly defines that field.
- Hashing the six-word after-state, then hashing the zero parent, state hash and
  zero inbox accumulator, exactly reproduces indexed assertion
  `0xaa21562a084193231d781b2f6b77f4227c01cc40feee9540dc098f5b332d49f0`.
  The complete ABI-derived event topic matches too.
- `RollupInitialized` independently binds the same event set to chain4663 and
  its WASM root. The deployment transaction carries the same initial commitment.

The resulting expected genesis hash is:

`0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c`

[Proof and source hashes](IDENTITY_PROOF.json), [independent second review](GENESIS_REVIEW.json)
and [actual Ethereum replies](L1_RPC.json) retain the derivation. The candidate
Robinhood RPC was not used to choose the expected value.

This remains an explicitly bounded trust claim. Flashbots returned null for the
deployment receipt, so there is no receipt-trie proof. Its log inclusion fields
and rechecked canonical numbered header are reconciled instead. PublicNode and
Llama's first Ethereum handshakes returned HTTP403 and were stopped without
aliases or client changes. Nine Ethereum HTTP attempts were made: seven JSON-RPC
replies, including the null receipt, and two HTTP denials. No locally verified L1
consensus or full ArbOS/genesis rebuild is claimed. Main-branch source snapshots
are retained by their exact bytes/hashes, not described as a deployed-code build.
The second review accepts this input for the bounded identity probe only.

## Run the existing full profile once

After the separate market study's rate-limit stop and a pause exceeding three
minutes, the unchanged `keeper.probe.probe()` ran once with
`profile='activation_api_v1'`, default12confirmations and12receipt blocks.
Its independent genesis input was the L1-derived hash above. The WETH probe
retains the independently recorded2,202-byte runtime from9November; no candidate
runtime is admitted merely because that candidate reports it.

Only the transport wrapper adds recording and slower1.5-second configured
monotonic spacing. The existing90-second/100-logical-call bounds,8-second
transport timeout,8MiB response bound, strict parser and read-only method list
remain. An additional100-actual-post ceiling cannot expand those limits.
Further HTTP requests stop on401/403/429. No retry for a green result occurred.
This invokes the existing profile function; it does not retest CLI parsing.
The exact captured [runner source](profile-runner.py.txt) is published as inert
text for inspection, with its original hash. It contains reviewed local paths
and is not a portable or newly executed recipe. The stock CLI has no pacing
flag: its default request cadence was not this execution and may hit a rate
limit. A CLI command shown elsewhere is command shape only, not proof of this
paced result or permission to adopt the public provider.

All13 checks passed:

| Check group | Actual observation |
| --- | --- |
| Network identity | Genesis matches the independently reviewed input; fresh head and common confirmed block |
| Canonical state | Same-hash contract call, independently pinned runtime and storage read |
| Missing state | Explicit unknown canonical hash rejected as `-32000/header not found` |
| Trace with logs | Exact discarded `approve(probeAddress,0)` call and its actual `Approval(0)` event |
| Operating reads | Gas price, safe/finalized header shapes and three ordinary receipt samples |
| Final anchor | Same confirmed numbered header rechecked after the observations |

The confirmed reference was113298933, hash
`0xde25040f9dfd29027a0517ade5c0b44e86494f2bb7a02914a059df0e0a1a8342`.
There were24 logical reads and48 actual HTTP posts, including a fresh chain check
for every logical read. All HTTP replies were200; one JSON-RPC reply was the
intentional missing-hash error. The observed UTC span was about70.88seconds;
the largest response was6,422bytes. Configured monotonic pacing is not proof of
exact wall-clock intervals. [Profile result](PROFILE.json) and
[complete recorded requests/replies](PROFILE_RPC.json) retain these boundaries.

The harmless500k trace and small state reads do not qualify full20M/24M execution,
large activation traces, API preparation latency or sustained concurrency. Safe
and finalized tags passing this profile prove returned header shape, not finality
or provider honesty. The three receipts are bounded samples, not complete history.
The [separate capacity work](../capacity/REVIEW.md) retains its own evidence.

## Preservation and remaining work

Only an ephemeral public-endpoint configuration outside Git was used. No private
key, wallet, state override, signature or public transaction was involved. No
provider or fee policy was adopted; no contract, site/service, signer, existing
Anvil, journal or user-paused heartbeat changed. No unchanged test suite or
compiler was run.

Continue qualifying exact deployed PoPL operations, actual depth/routes/feeds,
full fees and spending policies, full-work numerical/response/time limits,
provider plans and independent upstreams, lifetime archive, outages and recovery.
An RPC can fabricate internally consistent replies; identity checks are not an
honesty or consensus proof. Keep all source/runtime, canonical-hash, execution,
fee, funding, request-budget and pending-recovery safeguards.

The offline verifier checks the new evidence and hashes without network, EVM,
compiler or unchanged test execution. Optional external verification checks the
original source/response bytes as well.
