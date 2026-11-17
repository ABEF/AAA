# Launch claim workload:1,000 NFTs and16 ERC20 royalty currencies

**Three new methods pass at unchanged source/defaults.** They exercise actual
current NFT/trait finalization, Membership, FeeController, exact-unit LP Rewards,
original-currency royalty4 and the immutable claim router. No old suite is run.

The claim ceiling stays **12,000,000**.16ERC20 currencies plus native ETH is the
unchanged launch capacity; optional64ERC20 expansion is not exercised or approved.
`MAX_CLAIMS=32` remains an engineering count limit, not a gas guarantee.

## What was actually constructed

- 1,000 real NFT IDs/ordinals with finalized actual draws:600 Common,300 Rare,
  100 Legendary, giving1,500 active royalty-weight tickets. All1,000 are active.
- Four logical LP share accounts with unequal per-NFT weights and two physically
  funded exact LP books (native ETH/fixed ZZZ). Actual FeeController allocation
  retains compound, buyback and split dust separately.
- Sixteen conventional test ERC20s plus native royalties; fixed ZZZ is also one
  royalty currency, so identical asset addresses across the two ledgers remain
  distinct selectable claims. Each chosen entry has a positive claim amount.
- Actual NFT transfers to the current claimant. The former owner is rejected.
  The32-entry selection demonstrably spans all four LP accounts.

`ExactLPShareFixture` is an unchanged **typed accounting writer**, not physical
liquidity/valuation/entry execution. NFT issuance uses the explicit zero-SeaDrop
direct-mint test profile; it is not primary-sale/OpenSea acceptance. The two LP
claim entries include the deliberate raw fixed-ZZZ recovery right, not a claim
that ordinary ETH-only website settlement needs no conversion.

All enrollment/funding is completed in `setUp`, before the measured test
execution. Each test starts storage-access recording, then explicitly cools the
recorded storage slots and protocol accounts after its expected-value reads.
This avoids calling an account-only cooldown a complete storage cooldown.

## Results and interpretation

| New scenario | Selected entries |12M result | Call-body gas observed |
| --- | ---: | --- | ---: |
| Newly pending17-currency royalties plus both LP books |19|Refused atomically|11,998,017 consumed in refused envelope |
| Already allocated royalties plus both LP books |19|Succeeded|7,766,624 |
| Stored LP claims across16 current-owner NFTs/four buckets |32|Refused atomically|11,993,764 consumed in refused envelope |
| First bounded recovery chunk after pending19 refusal |8|Succeeded|6,566,963 |
| First bounded recovery chunk after32 refusal |8|Succeeded|7,828,399 |

The large refused calls preserve observed rights, wallet/ledger balances,
liabilities, all five LP tree totals, selected per-NFT components and designated
fee reserves. Fresh smaller selections pay exact expected units. No successful
payment is repeated, no right is removed, and no gas ceiling is raised.

The third method separately makes the **last** royalty currency reject its
recipient transfer. An expected call and exact custom error prove that the
intended late transfer was reached. The whole mixed LP/royalty transaction must
roll back, including all earlier successful transfers. A healthy18-entry
selection then pays exact amounts (7,448,523 call-body gas); the failed right
stays backed. After the explicit test token recovers, that one original-currency
claim pays exactly (335,929 call-body gas), and its repeat returns zero.

These are gas-limited **EVM call-body** observations, not RPC estimates, complete
transaction gas, fees or provider approval. Calldata/intrinsic work, independent
transaction boundaries, actual token code and selected consumer policy still
matter. For example, stored19's body-only20% arithmetic is9,319,949; that is not
an exact padded transaction simulation. Current schema2 claim planning separately
requires its full20% headroom; legacy schema1 keeps its distinct behavior.

The first call in each method starts from the cold funded setup state. Later
sequential recovery chunks prove bounded **functional recovery** in the same
test. Cooling does not reset EIP-2200 transaction-original storage semantics, so
later chunk numbers are not silently promoted into separate cold production
transaction qualifications. The parent workload records keep actual RPC work
separate.

## Failed fixture stages retained

The initial combined compilation found a nonexistent test-only `rawTreeDigest`
reference. It ran no EVM methods. The fixture now uses actual public allocation
totals, selected exact components and cash/reserve reads; no production getter or
authorization bypass was added to satisfy the test.

The first owned run compiled, but both `setUp()` calls failed `MemoryLimitOOG`.
It executed **zero test methods**, not two failed financial scenarios. Recording
the entire1,000-NFT setup and copying its repeated accesses made an enormous
cheatcode-return array (the retained trace shows roughly511,000 NFT read entries).
The fixture now records only premeasurement accesses in the actual test
execution. Neither EVM memory limits nor production/default gas policies were
increased. The32-entry selector was also corrected from a two-bucket stride to
an explicitly asserted four-bucket selection before any successful method was
recorded.

## Evidence and boundaries

[VERIFICATION.json](VERIFICATION.json) binds exact three IDs/statuses, emitted
envelopes, pinned tools, full source brackets and168 compiler-source checks
across the two compiled test contracts. Only exact raw bytes or exact CRLF→LF
compiler input normalization is accepted. The small collector checks the exact
expected IDs and parses bounded result prefixes without loading full trace
arrays. Commands and all raw failure/pass artifacts remain under the owned
external `launch-workload-20261117/claims` directory; approximately396MB initial
and621MB final raw traces are not copied into Git.

The test-only harness runtime allowance is1,000,000 bytes. That accommodates the
test's embedded deployment code; it is **not** a production size-gate result or
relaxation. The unchanged production normal build retains its existing gates.

No production source, default, safeguard, NFT right, currency capacity, signer,
existing chain/database/journal, service or paused heartbeat changes. These
controlled ledgers/tokens do not establish actual provider/market/fee/host,
64-currency, complete historical-phase or independent production acceptance.
