# Fresh royalty status and exact Book codec

The final isolated candidate fits normal Royalty runtime at **24,562bytes,
14bytes headroom**, creation25,533. It packs per-currency eligibility count,
weight, allocation cursor and initial-allocation flag into one private word.
Count/weight/cursor each have16bits; every production write remains bounded by
1,000NFTs/3,000tickets and the existing canonical checks. Public getter selectors
and types remain; the three former mapping getter input names become `asset`.

Each exact allocation Book puts current/initial normalized cursors in low16/next16
bits, and ordinary lifetime round coefficients in the remaining223bits. A high
bit selects a separate full256 coefficient. No numerical domain is narrowed.
Both monetary liabilities and transfers retain their original checked bounds.
The assembly hashes cleaned address keys and uses only scratch memory0..63 for
status; Book accesses use the typed storage pointer and exactly its next slot.

## Precise domain and zero-book argument

The production `_distribute` returns before credit for a zero amount. Every
positive credit uses the existing authenticated currency cursor, never a
keeper-selected arbitrary cursor. A zero packed word therefore represents an
empty allocation coordinate, or the mathematically equivalent lifetime wrap
to zero round/current/initial cursor. Its gross coefficient is exactly zero.
The next valid credit starts at cursor zero in the latter case. The removed
initialized flag and early-zero gross shortcut do not change any public NFT
right or canonical logical row.

Do not claim equivalence for an arbitrary stand-alone generic caller that first
credits zero at one cursor, then supplies a different cursor. The old library
records the first initial offset even on that zero call; the fresh packed codec
does not. That sequence cannot enter the production host. Generic amount/weight/
cursor validation and monetary overflow checks remain; this representation is
not an admission to use caller-invented cursor sequences.

Wide-to-compact transitions leave an irrelevant old spill word, which is ignored
unless the high tag is set again. All arithmetic on lifetime round coefficients
stays modulo2^256. Monetary receipt/liability arithmetic stays checked.

## Guard deduplication is narrow

The generic `enroll` and `birth` entry points retain every original check.
Production calls `enrollValidated` only after `_enrollTo` returns for count==old
and rejects count<old. Its count derives from bounded activationCount,
openingCount or imported activation ordinals. Fresh activations cap at1,000;
canonical rows cap NFT count/ordinals at1,000 and reject duplicates. The last
stored cohort end equals prior eligibleCount because there is no other writer.
The count is therefore strictly increasing in1..1,000. Its uint16 cast is exact.

Production calls `birthActivated` only after `_ticketShare` has returned for a
zero or ineligible activation ordinal. Binary-search exhaustion still reverts.
The generic wrapper still rejects ordinal zero. No source, permission, balance,
liability, callback, currency-fault or claim guard is removed. No global
activation state is moved before currency synchronization.

## Focused verification

Nine NEW methods cover42 full-round/amount pairs around223-bit/full256 bounds;
modular max→zero→one with zero cursor; a first nonzero cursor1777; retained
generic cohort rejection boundaries; actual normalized2→1/3→1 phase changes;
original-currency opening/fault/current-owner payouts;16ERC20+ETH component
improvement; and actual flat canonical import/release/accept/future payouts plus
funded abort/restore. Exact host size is separately normal; only the composite
test driver has a large test-code allowance. Owner/control/currency interfaces
are typed controlled seams, not the entire canonical coordinator or real market.

The first run has7 successes and2 canonical fixture failures. The fixture had
asked the target to validate backing before transferring it; the guard correctly
rejected that. Only that fixture call order changed. Only the2 affected methods
were rerun and both pass. A single additional failed diagnostic trace locates the
same order error. This is9 distinct new methods and12 total executions, not12
passes or a whole-project verdict. Production source is unchanged across them.

The16-currency component asserts candidate cost is lower but its initial JSON
does not export event amounts; no numerical full-activation saving is claimed
from that assertion. Cold full Entry and mandatory20M/full20% qualification remain
the parent campaign's separate work. Existing twelve-million defaults, all
financial limits, environments and paused heartbeat are unchanged.

Earlier coalesced-cohort and Book/status variants are size-only engineering.
They executed no EVM methods and are not adopted. The final candidate retains
the original cohort representation and exact flat canonical format. Fresh
Royalty creation/data parts and exact source/runtime pins are required; old
private storage, frozen fixtures, artifacts and deployed profiles cannot be
relabelled.
