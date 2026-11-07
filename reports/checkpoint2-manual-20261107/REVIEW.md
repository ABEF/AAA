# Exact earnings checkpoints and typed manual LP preparation

Baseline main `bf2cc72adbed74e12e64b6b987cdd669eb30ce90`. Two backend source
milestones are implemented and locally verified. No contract, ABI, runtime,
financial right, authority, service, site, Anvil, journal or signer is changed.
Production remains NOT APPROVED.

## Exact-unit checkpoint2

Fresh accounting7/LP-allocation1, custody5, fee-intake1 and original-currency
royalty4 can use an explicit reviewed format2 artifact. The optional builder
and earnings readers retain raw owner/collective trees, pending units, high/low
allocation phase, outstanding units, direct ETH credits, orphaned units, fixed
pair and immutable ordinals. Common ownership, cumulative claims/conversions,
royalty tickets/cohorts/cursors, carried fee dust and original-currency earnings
remain exact. Nothing is flattened or counted as new income at conversion/claim.

The builder authenticates the same confirmed source/configuration/history anchor
and reconciles every minted NFT's owner, ordinal, shares, royalty tickets,
LP components and paid/earned rights against on-chain getters. It validates the
serialized state before exclusively publishing a new candidate. Public request
limits, artifact32MiB/node/depth bounds and offline build limits stay unchanged.
Format1 is still historical accounting6; cross-format/profile/source mismatch
rejects before restoring state. Existing artifacts need reviewed rebuild/re-pin
after semantic source changes; changing their labels/hashes is not migration.

Each request restores private state. A served checkpoint must precede the entire
raw24-hour window; recent events are replayed completely, never daily-bucketed,
interpolated or truncated. New reviewed royalty descriptors may be appended with
actual admission/allocation in the suffix; old descriptor meaning cannot change.
All-time/24h original amounts retain today's confirmed-price valuation policy.

This milestone is original-deployment earnings only. Predecessor lineage and
other ownership/claim/preparation readers remain separate. Raw/WAL archives and
old artifacts must remain available. A hash verifies reviewed bytes, not honest
RPC/ingestion or every historical event. Internal phase in operating contracts
is event-derived; component/root reconciliation does not independently expose
that phase or prove log completeness. Actual hosting, maximum currency workload,
archive/rotation/restore and independent approval remain open.

## Typed manual LP preparation

The new read-only CLI prepares explicitly selected Active-state operations for
direct empty-code governance wallets. Contract wallets and delegated EOAs reject
with a stable local unsupported-envelope reason before funding checks; a
multisig may have a different outer sender/gas payer, so its call is not falsely
represented as a direct governance-signed transaction. This is a client scope,
not an on-chain authority restriction. Empty code alone does not prove key
ownership; actual wallet execution still requires qualification. Supported calls:

| Selection | Fixed target/call | Floor meaning |
| --- | --- | --- |
| B | `Migration.consolidateResidual(request,false)` | Positive ADDED main L; checks14/current ticks/automatic reviewed routing |
| C | `Migration.consolidateResidual(request,true)` | Positive ADDED main L; explicit mask/current ticks/swap choice |
| D | `Migration.emergencyRebalance(request)` | Positive NEW-position L; explicit mask/new ticks/swap choice |

It authenticates the current code/helper/controller/governance/pause/lifecycle
and both actual LP legs. It obtains operation-specific custody hashes and a
source-bound provenance review hash, validates explicit inputs, simulates and
estimates the exact call at a confirmed snapshot, then checks a newer canonical
tip and repeats the SAME call once. Normal spot/composition/new price rounds
can move; custody, IDs/ticks/L/shares, nonces/epochs and governed policy identities
and revisions cannot silently change. Financial rounds are distinguished from
active feed/sequencer policies. Latest guard failure refuses the artifact.

Original floors, deadline, swap, mask and calldata never relax or change. Gas
is bounded by the operator AND each block, with full25% estimate headroom,
original fee/price caps and governance funding. The final unsigned transaction
has chainId/from/to/data/value, with no gas, nonce, signature or allowance.
Gas review is separate. A last head/deadline check follows slow work; there is
no third simulation, retry loop, automatic force or output overwrite.

Forced checks0 retains its intended independence from USD prices, ordinary
trigger/sample/cooldown, operation-enabled flags and automatic routing. Mandatory
structural/control/custody checks remain. B/C cannot spend main or designated
compound. D's observed principal/idle/existing compound is a LOWER BOUND: new5%
compound can arise from its own harvest. Exact full simulations, not a false
pre-harvest ceiling, determine the unchanged D input's spendability. Protocol
reward/reserve separation remains enforced by unchanged source contracts.

Both simulated calls are read-only. The first snapshot has configured depth; the
final tip is explicitly NOT described as confirmed. `ready_for_submission` and
`production_approved` remain false. Review hashes grant no authority. The actual
wallet envelope, pending nonce reconciliation, provider honesty/support, target
fees/gas and operator rehearsal remain open. Parked recovery and other actions
are deliberately unsupported by this adapter and keep their existing procedures.
On success, source operations remain paused until deliberate governance unpause.

See [checkpoint procedure](../../docs/EARNINGS_CHECKPOINTS.md), [manual inputs and
workflow](../../docs/MANUAL_LP_PREPARATION.md), the [operator manual](../../docs/OPERATOR_MANUAL.md)
and [verification](VERIFICATION.md). The sole [Todo](../../TODO.md) keeps wider
history and operation qualification in progress; this is not release approval.
