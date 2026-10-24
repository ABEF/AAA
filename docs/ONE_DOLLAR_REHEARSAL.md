# Local $1 activation rehearsal

The user requested a $1 activation minimum for testing on 2026-10-18. This is a
**separate, local-only build**, not a change to the production economics or an
existing deployment. Production activation still requires **$100 original gross
source value**. Minting remains **0.05 ETH** in both builds.

## What the tool changes

[prepare-dollar-rehearsal.py](../scripts/prepare-dollar-rehearsal.py) copies the
current Solidity sources and required test fixtures into a **new directory outside
the repository**. It changes only the gross activation checks in the copied Entry
and fixed VaultCanonical validation companion from $100 to $1. Both copied constructors also
require local chain ID `31337`; their production counterparts are untouched.
Missing or duplicated replacement anchors fail before output is written.

The generated `REHEARSAL.json` records original/generated source hashes, compiler
hash, minimum, mint price and execution budget. The manifest derives contribution default/hard maximum from the byte-identical
Budget source; it does not invent1% or override operating settings. No deployment
scripts, wallet keys, RPC configuration or broadcast mechanism are copied or added. A chain-ID
guard prevents accidental use on normal public networks; it is not a consensus
proof or protection against someone deliberately modifying the generated code.

A newly generated build retains the source candidate's contribution limit: the
current default is 2%, requiring at least $0.98 marginal deployed LP from $1 of
input. It also retains pool-specific bounds, owner checks, shared LP and rewards;
gas is separate. Previously generated 1% builds and their receipts remain
historical artifacts, not silently updated deployments. The inherited historical
AtomicActivation test fixture explicitly selects1% to preserve its original
negative cases; that is an operating override, distinct from the generated
artifact's default. Read both manifest and actual configured getters. A low-cost rehearsal
can still revert on costs, rounding or idle exceeding the captured limit.

The pool's `minDepositUSD` must also allow $1. The fixture configures it to $1;
changing only the Entry check would not be sufficient. A dollar-valued token is
not assumed to equal one dollar: the oracle value and token decimals determine
the minimum raw input, rounded up. The local fixture supplies test ETH for the
unchanged mint price; this does not mint a real NFT for the funded public wallet.

## Running it

From the contract repository, with the existing dependencies installed and a
reviewed local Solidity 0.8.26 compiler:

```text
python scripts/prepare-dollar-rehearsal.py --output /absolute/new/local-rehearsal --solc /absolute/path/to/solc
forge test --root /absolute/new/local-rehearsal --offline --match-contract DollarActivationRehearsalTest --match-test ^testDollar
```

Use absolute paths suitable for your OS and quote paths containing spaces. The
output directory must not already exist. The generated configuration retains the
project's Cancun/via-IR optimizer settings, disables FFI/filesystem permissions,
and references the repository's installed libraries. The test fixture lives
outside the normal `test/` tree so standard production tests cannot accidentally
use its reduced minimum. Generated sources are disposable rehearsal artifacts,
not release sources.

## Integration and evidence boundary

The current website and production transaction-preparation API still use the
$100 rule. This work does not provide a live $1 wallet flow or a deployed $1
contract. Mocked venue, feeds, VRF and authority behavior are explicitly test
scaffolding; the selected Pons pool, real gas costs, funding and external services
remain separately qualified in the [central Todo](../TODO.md#task-testnet-rehearsal).

[Scoped test evidence](../reports/one-dollar-rehearsal/VERIFICATION.md) records
what actually ran. Reuse unchanged production evidence; do not relabel this
modified copy as the production binary. A real defect found through rehearsal
must be fixed in production source with a focused regression and updated evidence.
Do not copy the test-only $1 override or local constructor guards into production.

Public wallet observation uses read-only RPC calls and remains outside Git.
No private key is required for these tests. No public transaction, approval,
deployment, website/server change or monitor restart is part of this rehearsal.
