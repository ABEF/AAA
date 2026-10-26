# Current accounting3 selected-pool fork

Started2026-10-26; final review2026-10-27. See [verification](VERIFICATION.md) for
composed execution scopes, failures and remaining limits.

This campaign uses the current source with the **actual selected native ETH/ZZZ
Uniswap v4 pool** on Robinhood chain4663. It does not revive the archived wrapped
fixture, silently count old Pons tests, deploy publicly or submit transactions.
The existing historical runner and its unrelated local draft are preserved.

## Target and boundary

The target is pool
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`,
PoolKey `(address(0), fixedZZZ, 10020, 200, address(0))`, at block96,427,989,
hash `0x0ba14c22200dfc717bbd2c8b5b8842329775374d06f46e30c65e273f067ecbc3`.
The fixture requires actual Core, PositionManager, StateView, Permit2 and ZZZ
runtime hashes and wiring. This fixed historical block is not today's price,
depth, protocol-fee policy or RPC uptime claim.

The real deployed pool/token/core/periphery execute on an ephemeral local fork.
MockAccess, MockVRF, correlated USD feeds and fork-only account funding are
explicit substitutes. ETH is assigned a fixed test USD price and ZZZ is derived
from the fork spot solely to exercise the current guards. These are **not two
independent market sources** or actual-dollar input-route qualification. No user
key, live authority, oracle provider, randomness provider or public fund is used.

## Coverage and runner

[Current fixture](../../test/CurrentNativePoolFork.t.sol) covers selected native
identity, mint/increase/close, both net-output swap directions, real harvested
fees/no repeat harvest, exact native-value/prefund boundaries, stopped-pool
unwind, rejecting ETH recipients, one shared physical LP for multiple NFT
accounts and funded reward ownership/claim backing.

[Current runner](../../scripts/run-current-pool-fork.py) pins Forge1.4.4 and
solc0.8.26, strips inherited Foundry/Dapp overrides and validates the effective
normal compiler/source/size/FFI profile before network activity, serializes a bounded read-only RPC
allowlist through a loopback relay, applies a process-tree deadline, sanitizes
upstream error payloads and requires every declared current test to pass without
skips. No automatic service or historical journal/profile migration is performed.

From the repository root, with the pinned tools installed:

```sh
python scripts/run-current-pool-fork.py --forge /path/to/forge --solc /path/to/solc-0.8.26 --output /path/to/new-evidence
```

On Windows use `python -X utf8`. The output directory must be new. Optional
`ROBINHOOD_FORK_RPC_URL` selects another reviewed HTTPS archive endpoint; keep
credentialed endpoints in the environment and never put them into reports or Git.
The default keyless Pinax endpoint is a test access path, not an approved hosting
or reliability plan.

## RPC discovery

The [official connection guide](https://docs.robinhood.com/chain/connecting/)
documents chain4663 and warns that public endpoints are rate limited. Pinax's
[own network page](https://pinax.network/chain/robinhood) documents its archive
service. [Bounded probes](rpc-probe-network.json) found working chain/archive
reads at Pinax; the official endpoint failed transport from this environment.
The alternative BlockVectra public endpoint answered the chain ID but rejected
this older block outside its public history window. Those are observations,
not an independent production-provider approval or proof of authentic history.

## Evidence and remaining qualification

The [initial attempt](attempt1-summary.json) preserves four passing and six
failing methods. The failed expectations exposed fixture mistakes: real Permit2
maps zero expiration to the block timestamp, and an intermediate external getter
consumed a one-call sender prank. Production authorization, value/loss guards,
balances, contracts and economic rules were not changed to fix those fixtures.
[Final focused runner checks](runner-tests-final.json) distinguish complete/partial/skipped
results and enforce read-only transport and credential-safe errors. Final EVM
scope and source bindings are recorded in the accompanying verification record;
earlier attempts never become additional test coverage by summing their counts.

Actual independent prices, cheaper ZZZ-to-ETH reward conversion within the default
1% cap, real route/depth/maximum-state gas, authorities, supported VRF, OpenSea,
hosted current3 services and independent audit/remediation remain open. This
fork partition does not deploy `poplint`, modify `popldemo`, restart a keeper or reset
existing Anvil/NFT/LP/balance/journal state. **Production NOT APPROVED.**
