# Isolated 1,000-NFT history recovery rehearsal

The authorized controlled collection-scale rehearsal passes on baseline main
`f64c005f8b22b1da463d34f9a788cf7ec0b8a22b`. All 1,000 NFTs retain exact
accounting through checkpoint prefix import, backup, verification and restore.
The full raw 24-hour window, nonzero LP high/low phase, original-currency
royalty tickets, previous claims and LP conversions remain intact.

**No production accounting, defaults, limits or contracts changed.** Added one
[explicit rehearsal module](../../tests_python/history_scale_rehearsal.py) and
updated the Todo/operator documentation. No previous test methods/suites,
compiler, EVM, browser or public-provider tests were run. No existing database,
chain, journal, signer, site, service or paused heartbeat was acted on.

## Workload and independent checks

| Area | Actual exercised scope |
| --- | --- |
| Collection | 1,000 full-width IDs, 900 active/100 dormant, mixed shares, rarity weights 1/2/3; 13 final holder wallets, including one holding hundreds of NFTs. |
| Canonical history | Three explicit accounting7/mint2 epochs and two receipt-authenticated controlled handoffs. Actual production Lineage/History/replay/codecs run; dependency/getter/lifecycle truths are synthetic, not on-chain witnesses. |
| History | 7,757 raw logs over 346,800 chain seconds; one logical LP bucket, ETH/fixed-ZZZ LP books and ETH plus one ERC-20 royalty currency. |
| Actions | 31 growths, 36 transfers, 24 ordinary fee receipts, 22 royalty allocations, 24 LP claims, 8 royalty claims and 16 LP conversions. One additional indivisible fee-dust settlement exercises a known recipient and nonzero allocation phase. |
| Independent arithmetic | Literal 80/10/5/5 calculations for divisible receipts and explicit rarity-ticket enumeration. All 1,000 LP components/earnings, royalty earnings, local claims and conversions match. Claims/conversions are not new income. |
| Time window | Events at blocks 226/227/228 test before/exactly at/after the day boundary. Block 227 is excluded; 228 is included. Checkpoint cursor 161 precedes the whole day; the second handoff at 240 stays inside it. No day bucket, pruning or shorter window substitutes for raw replay. |
| Recovery | Original checkpoint2 becomes checkpoint3 through the real prefix importer; exact candidate/review bytes, all cursor/block/log rows, source main/WAL hashes and source SQL change counters are checked. Restore uses new separate files. |
| Reporting | Source and restored copies each pass 72 wallet chunks covering every NFT exactly once, plus five individual NFT reports and collection totals. Wallet IDs/counts/offsets/inventory hashes/block are checked, including dormant and transferred NFTs. |

The independent arithmetic does not call production Tree/split/ticket allocation
helpers. Synthetic getters partly use ExactReplay; equality against restored
results alone is therefore not presented as an independent correctness oracle.
The literal entitlement checks and historical claim/conversion reconciliation
are separate assertions. USD feeds are unconfigured, not guessed or qualified.

## Measured results and unchanged bounds

Windows Python 3.12.14 / SQLite 3.53.1; controlled local observations only.

| Stage | Wall time | Controlled logical reads |
| --- | ---: | ---: |
| Explicit offline original prefix build | 6.65 s | 18,046 |
| Prefix import into three-epoch checkpoint3 | 12.66 s | 18,159 |
| Backup | 1.81 s | Offline/no network |
| Verify backup | 2.12 s | Offline/no network |
| Restore | 3.27 s | Offline/no network |
| Verify restored package | 1.01 s | Offline/no network |
| Worst of 157 bounded read stages | 1.02 s | At most 607 of 1,024 per stage |

The successful child process takes 124.47 seconds including setup, all stages
and cleanup; observed peak Windows working set is 170,029,056 bytes. These are
not chain gas or live-provider latency measurements. The checkpoint is
2,434,854 bytes; the backup is 11,961,434 bytes, restored package 11,962,389 bytes.

The default offline 4,096-call budget correctly refused at exactly 4,096 calls.
That passing source1 record is explicitly reused, not rerun or relabelled as a
fresh final-source result. Positive construction/import explicitly use the
**existing** 65,536-call/post allowance and unchanged 60-second deadline. This
neither changes the 60s/4,096/8,192 defaults nor authorizes production adoption.
HTTP reads retain 25s/1,024calls/2,048posts and 16-NFT wallet chunks. This
fixture's explicit history setting is 10,000 events, within existing bounds.
Checkpoint32MiB, codec1,000,000nodes/depth12, recovery1GiB and JSON1MiB bounds
remain. No real HTTP posts occur; complete live admission costs remain unknown.

## Failures retained and corrected in the new fixture

1. The initial positive attempt reached its 60-second deadline after 11,906
   reads. The old three-NFT fixture rescanned/sorted thousands of owner logs
   for every getter. The new scale fixture caches only the same exact epoch/
   block ownership observation, returns copies and invalidates on emission.
   Every getter still consumes its call budget. No production cache or guard
   was changed, and the old timeout is not evidence of production infeasibility.
2. A second attempt stopped during setup: Windows supplied the same `time_ns`
   value to two temporary-directory allocations. Owned synthetic directories now
   use an exclusive per-run counter. No verification stage or database restore
   ran in that attempt. Original failure artifacts remain available.

Pre-run review also corrected fixture-only temporary-directory patch scope,
ambiguous refusal checks and incomplete per-copy inventory assertions. These
were rehearsal implementation corrections, not claimed production defects.

## Remaining release obligations

This closes one finite local scale/composition milestone under
[financial history](../../TODO.md#task-financial-history) and
[hosting](../../TODO.md#task-host-services); both broad tasks remain In progress.
It does not qualify maximum currencies/buckets/epochs, all-active/long-lived
history, authentic archive completeness, complete runtime/admission RPC work,
provider/network latency or HTTP-post capacity. A real provider can exceed the
existing work bounds; that must fail closed rather than trigger a fallback or
automatic limit increase. Actual Unix storage/off-host transfer/host loss,
operating adoption and independent audit remain open.

Source main/WAL identity is checked while the owned writer connections remain
open during recovery. Their later normal closure may checkpoint WAL; SHM locking
bookkeeping is not claimed byte-identical. No installed database is involved.

See [verification stages](VERIFICATION.md), [lossless evidence](EVIDENCE.json),
[recovery procedure](../../docs/HISTORY_RECOVERY.md) and
[operator instructions](../../docs/OPERATOR_MANUAL.md#collection-scale-history-rehearsal).
