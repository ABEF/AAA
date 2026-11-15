# Verification scope

Source baseline: `a5a0233a12e3477e7348811d4a3d97c77764a695`.
This report records new controlled execution only; unchanged evidence is reused.

| Evidence | Actual scope |
| --- | --- |
| Four new EVM methods | C14, D14, Parked14 and separately selected outage0; current full graph and actual v4. Six invocations retain two earlier fixture failures. |
| Four focused compile/list stages | Exact test/dependency compiler output; zero test methods during listing. Existing production normal/static gates not rerun. |
| Seven actual CLI attempts | Default real clock/production RPC path; six successful reviews and one original25s-budget timeout. No submission from timed-out node. |
| Six local receipts | Four manual operations plus two distinct park receipts. One earlier park/verifier failure retained; accepted later park→recovery shares one new chain. |
| Exact gas | Actual estimate, full25% arithmetic, full24M-cap call, exact padded call and receipt reconciled separately. All retained masks/floors/expiry match the intent. |
| Negative paths | Governance-only and paused authority, explicit masks, unchanged state on failed reference-venue swap, original caller floors and unauthorized keeper. No silent0 fallback. |
| Rights/backing | Active/dormant/unequal owners, aggregate shares, exact earned books, compound/buyback, prefunds, physical custody/LP identity, nonce/epoch/clock/mode and pause. |
| Independent review | Two source/evidence reviewers plus root's independent integer/transaction/hash reconciliation, offline only. |
| Reused | All61 production Solidity and100 accepted normal source hashes unchanged; prior strict567 review retains its exact scope. No old suite/compiler/static/public RPC repeat. |

The new harness initially exposed setup requirements: fixed ZZZ must be bound
before execution-source admission, and sampled confirmation must be explicitly
configured600/300 (constructor gap0 means stopped). These fixture corrections
use existing legitimate governance calls. A typed-hash encoding adjustment fixed
the new host's compiler limit without changing compiler settings. No production
guard or setting was weakened.

The final rehearsal-runner correction only labels closure evidence N/A when the
Parked prestate has zero live legs. Its verify_post function is checked offline
against the same six captures; operations are not rerun. The earlier actual-run
source hash and bytes remain distinct from this reporting-only source revision.

The current function-reference note correction changes future offline review
provenance, not ABI/runtime/authority. Original notes/reference/Markdown and source
snapshot bytes are archived; old reviews are never regenerated or relabelled.

Use the published portable checker/manifest for exact raw evidence. No unchecked
claim of complete market, fee, maximum-state, host, old-chain state or independent
production acceptance is made. [Full review](REVIEW.md) explains limitations and
retained attempt history.

## Reconcile the published captures without executing anything on-chain

From the repository root, choose a new output path:

```text
python reports/manual-recovery-rehearsal-20261115/verify_evidence.py --repository . --output NEW_OFFLINE_RESULT.json
```

The checker defaults to its adjacent2.14MB public-evidence.zip, validates the
manifest and reads members without extracting them. It uses captured wire
responses, not a running RPC. Public evidence includes all six core transaction
captures and full call trees, derived original event cases and post-receipt wire
slices with original hashes/indices. These slices are explicitly derivatives,
not a claim to contain every raw RPC response. The full63,457,876-byte raw archive
remains outside Git at the external evidence directory in PRESERVATION.json;
SHA256 ad5e569797be73f3a89dc9f2a4c095fe9ae19f46f085bdbf6f936f8a6deb1e13.
Its exact manifest/baseline/attempt and cleanup provenance remain published.
