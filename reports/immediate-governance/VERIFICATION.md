# Immediate governance verification - 2026-10-18

**Internal development evidence; release remains NOT APPROVED.**
[Decision and semantics](../../docs/GOVERNANCE.md); [internal review](REVIEW.md).
No deployment, public transaction, website/server update or monitor restart occurred.

| Check | Result and scope |
| --- | --- |
| [Affected Solidity suites](solidity-verification.json) | **228 distinct passes**, zero remaining failures/skips across 15 suites. The first run passed 220 and failed eight obsolete timing assumptions. After fixture correction, only three affected suites reran: 51 passes. The other 177 passes were retained after exact compiler-dependency hashes matched current files. This is combined scoped coverage, not a new full regression run. |
| [Production configuration](python-verification.json) | **142 passes**, including zero-delay/strict-type rejection, unchanged seal/roles and mandatory current authority/parking evidence. Afterwards only two outdated diagnostic strings changed; the exact message-only replacement/hash is recorded. No redundant rerun or deployed-manifest approval is claimed. |
| [Normal production build and sizes](size-gates.json) | **30 objects pass**, all **39 production sources** compiler-bound. AccessController runtime/initcode object: 14,614/33,267 bytes; Migration: 24,515/25,041. Vault remains 24,557 bytes, with 19 bytes headroom. Constructor arguments require separate deployment allowance. |
| [Fresh Slither analysis](static-execution.json) and [internal dispositions](static-review-summary.json) | 378 expressions reviewed: 157 false positives, 75 accepted risks, 146 informational. Coverage passes and five corrupt-review mutations reject. Two new findings concern timestamp sentinel checks; affected previous authority rationales were updated. Not an independent audit. |
| Source and documentation consistency | 39 sources pass the narrow source check; Todo generation, scoped document links and Git whitespace checks are verified before publication. |

The [scope comparison](scope.json) identifies exactly two production behavioral
changes: AccessController and Migration. No new fast-route role was introduced.
The remaining 37 production sources, including custody/reward math, Entry,
Strategy, NFT metadata and randomness, are unchanged. Tests use local mocks for
venues/transport/feeds/randomness; the multi-chain fixture models chain IDs and
message delivery in one local test VM. It is not a live bridge or provider rehearsal.

Coverage includes immediate single/batch authorization; rejected nonzero constructor
and operation delays (1,000 fuzz cases); immutable zero delay; proposer/executor
separation; exact calldata, cancellation, replay and predecessors; atomic batch
rollback; zero/one timestamp sentinels; sealed asset/route/wrapper/feed changes;
guardian pause; preparation/callback guards; complete same-chain handoff; immediate
multi-hop plans with backing, provenance, rollback and old reward preservation.
The range test confirms that immediate governance **does not skip keeper cooldown**.

The original failures and raw logs are preserved externally under
`immediate-governance-20261018`. They are not merged into a fictional clean first
run. No production code changed during the corrective rerun. Historical broad
regression and pool-fork reports retain their original source/fixture scope.

Production qualification still needs reviewed authority addresses, fresh runtime
manifests, actual input routes/feeds/randomness, keeper/backend/wallet rehearsals,
bridge/finality work where applicable, and independent audit/remediation. There
is no advance governance notice window; this is an explicit trust decision.
Exact-commit published CI must be checked separately from these local results.
