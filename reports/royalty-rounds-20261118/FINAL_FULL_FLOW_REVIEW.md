# C08 full Entry workload: functional success, gas qualification remains partial

**All13 actual20M calls succeed and their financial/royalty checks pass. Five
cases meet20M with full20% padding; eight are refused.** This is one modified
Solidity method with13 exported cases, not13 tests or universal maximum-state
qualification. No failed profile is accepted and no default or safeguard is
raised. See the [strict result](full-flow-final/full04/local-rpc/SUMMARY.json),
[source execution](full-flow-final/full04/EXECUTION.json) and
[evidence manifest](full-flow-final/MANIFEST.json).

## Source and population

The actual fresh graph uses the final C08 royalty source
`35f712bd0b95abdd63a9e696e6e85e63453f2d8e5ec57c089c595e6bfd5f5bbd`.
Its final accepted100-source normal output is
`1947e502348e5e230e6d34792b317683f5d634514ce248ad64c342bb792ff663`.
The exact full fixture is
`f648f3f21f2d3fbf80795211ec2afce7efca1a06d1bc43fc707188c389643e57`.
All200 compiled dependency source identities match the producer, and source
brackets are stable. The final storage proof reads the actual normal layout:
enrollment mapping54, ends offset1; `accounted` is a derived getter rather than
an old storage slot. Every relevant normal metadata dependency is matched to the
producer metadata before interpreting storage.

The fixture mints1,000 actual NFTs through the verified SeaDrop fixture and
activates999 through real Entry, Vault, one physical main Uniswap-v4 LP,
Membership, Rewards and Royalty calls. Incumbents are599Common,300Rare,
100Legendary, weight1,499; the dormant Common at mint ordinal1,000 enters last.
Funding assets are chosen from actual target/reference imbalance; no price
reset or privileged accounting seed supplies the population. Sixteen ERC20
royalty currencies are admitted after activation8, followed by991 actual entries.
Before entrant1,000, ERC20 enrollment arrays have992 ends, so the next append
opens a cold packed word; ETH has999 ends. Royalty amounts use exact raw units,
not USD conversions.

Actual pool trading funds nonzero LP earnings and compound rights. The full
method checks unchanged incumbent shares, ownership, equal LP membership,
rarity-weighted royalty membership and LP backing. It drains all17 currencies
across the999 incumbent NFTs, excludes the newcomer from2,996 earlier units per
currency, verifies empty liabilities/accounted categories after claims and
checks a subsequent1,500-unit receipt belongs1,499units to incumbents and1unit
to the newcomer. It preserves the current position's geometry and entry-clock
semantics. This is an actual state transition sequence, not all-zero balances or
summary-only assertions.

## Cold gas results

Admission requires a successful actual20M call, a complete successful trace,
`ceil(estimate*120/100)<=20,000,000`, a successful call of the same frozen
calldata at that exact padded limit and verified financial/royalty outcomes.
Aggregate Forge counters do not substitute for the cold estimate. These13 cold
cases run only after the exact single producer method succeeds.

| Case | Cold estimate | Full20% ceiling | Admission | Saving vs original matched case |
|---|---:|---:|---|---:|
| Opening ETH |18,035,007|21,642,009|Refused|903,050|
| Opening ZZZ,16faults |16,089,655|19,307,586|Pass|1,768,778|
| Opening ZZZ |18,679,435|22,415,322|Refused|New case|
| Opening ZZZ,16slow reads |19,325,451|23,190,542|Refused|New case|
| Opening ETH,16slow reads |18,681,023|22,417,228|Refused|New case|
| Rotated ZZZ |17,582,618|21,099,142|Refused|1,312,811|
| Rotated ETH,1fault |16,837,543|20,205,052|Refused|1,187,764|
| Rotated ETH,16faults |15,331,306|18,397,568|Pass|1,675,538|
| Rotated ZZZ,16faults |15,975,734|19,170,881|Pass|1,782,018|
| Rotated ZZZ,16slow reads |18,228,634|21,874,361|Refused|1,312,811|
| Rotated ETH |16,938,190|20,325,828|Refused|1,207,112|
| Growth ETH |11,645,827|13,974,993|Pass|824,023|
| Growth ZZZ,16faults |12,291,980|14,750,376|Pass|928,647|

The ten matched-case estimates improve824,023–1,782,018gas against the original
[full02 source stage](FULL_FLOW_REVIEW.md). This comparison is between the named
controlled scenarios; it is not a promise across other market states or orders.
The three added opening cases were not present in full02 and all remain refused.
Original evidence is not relabelled. See the
[exact comparison](full-flow-final/full04/BASELINE_COMPARISON.json).

The worst tested final ceiling is23,190,542. The current20M/full20% policy remains
unchanged, so activation capacity remains a deployment blocker for this workload.
Successful actual20M execution alone does not override the reviewed resource
margin or justify adopting a larger budget.

## Read isolation and exact entitlement checks

Every activation trace contains exactly16 optional50k STATIC balance reads and
the corresponding self-only complete-sync frames. The checker verifies the
packed50k cap/full-frame witness, complete-frame allowance at most1M and the
exact `ActivationReadUnavailable` tag for intentionally faulted currencies.
Healthy reads return the actual2,996-unit balance. Every slow successful read
uses at least45k, so the expensive-read cases are measured rather than labelled.
Faulted assets defer atomically; successful assets allocate to the exact old
999-NFT/1,499-weight cohort before the newcomer joins. Growth performs no royalty
intake. The actual read/deferral/allocation sets, cursors and activation event are
checked, not just their counts. Configured read cap50k and complete-sync1M stay
unchanged; this does not qualify arbitrary future cap increases or64 currencies.

## Execution and evidence boundaries

The compile-only C08 stage completes in590.407seconds with zero EVM tests and no
root configuration mutation. The actual cached single method completes in
140.672seconds. Only its owned export-path permission is temporarily added; the
original configuration is restored byte-for-byte. Large aggregate harness
resources and paused setup/drain tracing are recorded separately from complete
measured calls; they do not relax actual20M execution or normal contract sizes.

Cold checks use at most three new owned loopback nodes, zero unlocked accounts,
read-only RPC, exact PID/listener ownership, original256request/600second/response
and trace bounds, and a32M local diagnostic block limit. All13 nodes stop. All
actual20M calls succeed, so no32M diagnostic is required to justify functional
success. Complete real-network fees/provider capacity remain unqualified.

The original full02 records remain unchanged. A compile-only CLI failure and a
helper-only prelaunch error are retained separately. C07 full03 is explicitly
interrupted when the canonical prefund defect is discovered; no method success
is counted. Whole-session cancellation bypasses the runner's finally block, so
its exact saved export-only config delta is checked and manually restored. C08
fixes that independent import edge before this new actual run. The interrupted
raw output is empty and no cold RPC starts for it. The final run does not reuse
that incomplete state.

The standard `exports.tar.xz` contains every original export byte with per-file
SHA256; the publisher checks all14 regular members without extracting paths.
Source pools, raw producer/artifact data, source-pinned helper copies, RPC
transcripts, per-case results and the compile/interruption records are retained.
Integrity hashes and finite internal execution are not independent audit or a
proof of all branches. Copying/compressing evidence executes zero tests.

## Remaining limits

- This uses one physical main LP,16 currencies, one deterministic999-entry
  arrival order and entrant mint ordinal1,000. An earlier minted NFT activated
  later can traverse different LP-tree carry paths. Optional residual LPs,
  arbitrary ordering/market conditions, expanded capacity and future read caps
  are not qualified by these13 cases.
- Feeds, VRF, authorities/admission, market depth, Permit2 and token behaviors
  remain controlled fixture dependencies. Gas-fault isolation does not make a
  malicious/frozen token transferable or establish its truthful balance.
- No unchanged suite or original cold case is rerun. No public transaction,
  sealing, signer/site/service/heartbeat change, old-chain reset, journal/DB
  rewrite or automatic profile adoption occurs. Production approval remains
  false; actual markets, complete fees, operating adoption and independent
  review remain open.
