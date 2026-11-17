# Operator behavior follow-up — 17 November 2026

**Two implementation defects are fixed, and two important verification gaps are
closed.** This follows the user's challenge to the
[92-action source/input audit](../operator-input-audit-20261116/REVIEW.md) at
`6945eeeba24304b8ddf27ac4c08fe55dc553554e`. A complete input catalogue is useful,
but is not dynamic evidence that every operator workflow succeeds.

Production remains **not approved**. No existing chain, deployment, site,
service, signer, database, journal or user-paused monitoring was changed.

## What improved

| Finding | Confirmed behavior | Correction and evidence |
| --- | --- | --- |
| SEAL-01 — medium setup risk | A real controller could seal with an empty NFT artwork root, erase bootstrap and permanently prevent filling that root. | Reject the empty root before irreversible seal. Three new actual Access/NFT/Policy cases cover rejection followed by completed setup, a constructor-populated root, and unauthorized attempts. [Rights review](RIGHTS_REVIEW.md), [original/final results](RIGHTS_VERIFICATION.json). |
| KEEPER-01 — operational lag | Slow strategy/reserve reads could cross a harvest/compound interval, but the due decision used the earlier head and deferred the action another poll. | Refresh chain time before enabled due decisions; reject failed/retreated heads without guessing time. Nine new cycle checks and one adapted timing check. [Keeper review](KEEPER_REVIEW.md), [method evidence](KEEPER_EVIDENCE.json). |
| VERIFY-01 — stale current-behavior fixture | All seven canonical-preparation cases failed in setup using a retired two-token harness, before reaching their intended scenarios. | Move that fixture to native ETH/fixed ZZZ, current bindings and a declared deterministic native venue/execution seam. All seven affected cases pass, including nonzero claims, pending reveal, callbacks/rollback and stale-price raw parking. This is not a live Uniswap or market test. [Rights review](RIGHTS_REVIEW.md). |
| VERIFY-02 — weak exact-unit assertion | Royalty recovery fuzz allowed `paid <= received`; a positive, permanently unclaimable remainder could satisfy it. No production remainder was reproduced. | Require independent six-ticket recipient arithmetic, exact balance deltas, every received unit paid, all relevant backing/liabilities zero and repeated claims zero. One changed method passes 1,000 fuzz inputs. [Rights verification](RIGHTS_VERIFICATION.json). |

The fresh controller normal creation/runtime objects change; all other checked
normal objects, concrete ABIs and semantic storage layouts remain unchanged.
Constructor-empty setup is still valid **before seal**. A nonempty string is not
proof of CID correctness, content completeness, availability or OpenSea retrieval.

## Keeper authority: explicit decision and actual behavior

The operator explicitly chose to **keep the extra compound waiting rule in
keeper software**. No on-chain restriction or new configurable compound policy
was added. Only an authorized keeper address can call keeper operations; an
outsider cannot do so. An authorized key using alternate software can ignore
extra service rules where the contracts permit. Existing authorization,
on-chain cooldowns, financial guards and atomic rollback remain.

Two new methods and one affected positive fixture case verify complementary
boundaries:

- Actual v4 core fees, out-of-range compounding during rebalance cooldown and a
  real balancing swap preserve shares, backing, LP centre and rebalance clock.
- Unauthorized and revoked prepared calls reject; a replacement key still obeys
  the compound interval. Pause blocks compound/harvest while funded claims work;
  unpause and elapsed time permit normal replacement-key operation.
- A separate actual controller test proves governance revoke/grant while paused,
  keeper inability to self-authorize/unpause, and no restoration of a revoked
  grant.

The actual-core test uses an explicit authority fixture, while the controller
test uses binding fixtures. They are not presented as one full production graph
or a compromised-host rehearsal. [LP review](LP_REVIEW.md),
[source-stage evidence](LP-evidence.json).

The operator guide now gives exact revoke/replace, pause, pending-transaction,
canonical-preparation and restart steps. A valid old-key transaction ordered
before revocation may still execute. Reusing the governance signing key as the
keeper key defeats this recovery separation.

## Wider rights and interference review

The follow-up also inspected royalty opening/capacity, deferred entitlements,
recovery, claims/transfers, canonical capture/funding/abort and terminal holder
return. [The source-grounded matrix](RIGHTS_REVIEW.md) separates these assessments
from fresh dynamic passes. It does not relabel historical tests as newly run.

Two limits remain explicit:

1. **Unallocated royalty recovery uses active weights at transaction inclusion.**
   `reviewHash` does not freeze beneficiaries. This is the approved economic
   rule; a pending recovery can encourage an activation ahead of allocation.
   The guide now documents an optional existing deposit-stop/confirm/read/
   allocate/re-enable procedure. Global pause would block that allocation, and
   re-enabling requires healthy full validation.
2. **Terminal ETH and ZZZ payout is atomic for each NFT.** A globally broken,
   blacklisting or non-exact-transfer ZZZ can defer that NFT's healthy ETH too.
   Isolated batches retain backing; incompatible recipients remain a delivery
   limit. No silent partial-liability redesign, arbitrary recipient or sweep is
   introduced. Original-currency royalties can be selected separately.

These are economic/dependency boundaries, not newly reproduced theft or a
promise that every possible token can always be transferred.

## Build, tooling and documentation

The unsigned construction planner now defaults to the exact closed
**`operator-seal-20261117`** family. Both historical metadata2 and original
manual-reference families remain hash-pinned; they cannot silently qualify
changed current source. Construction and pre-seal outputs explain that a blank
constructor root needs bootstrap `NFT.setBaseURI` before seal. They emit neither
that setup call nor sealing, and retain false readiness/approval flags.

The function reference, operator tables/inputs, keeper guides, Todo acceptance,
feature reference, roadmap, release boundary and repository context are updated.
Existing reports retain their original bytes and scope. No broad release task
is marked done because a local subfinding was corrected.

## Verification and its limits

**29 distinct selected methods pass: 16 new and 13 adapted/affected.** The
1,000-input fuzz is one of those methods. Counts exclude zero-selection attempts,
inventories, compiler gates, static detector records and overlapping staged runs.
See [verification](VERIFICATION.md) for exact method/source breakdown.

- **48 normal runtime/initcode gates pass.** Controller full constructor:
  48,377/49,152 bytes, leaving 775. Its runtime is 10,854 bytes. Oracle runtime
  retains only **3 bytes** headroom and Vault **32 bytes**. No compiler, gate,
  budget or safeguard was relaxed.
- Actual Slither analysis reused the accepted current compiler output without
  another compile. **570 records = 5 individually current assessments + 565
  unique exact referenced-source reuses.** Raw output, complete projection and
  the updated strict default pass. This is internal triage, not independent audit.
- No unchanged full Solidity/Python/browser suite, public RPC campaign,
  construction rehearsal or live operating test was rerun. Baseline failures,
  zero-test attempts, fixture repairs and raw/compiler source normalization are
  retained rather than hidden.

Real independent ETH/ZZZ feeds and routes/depth, complete target fees,
maximum-state gas and latency, qualified authorities/host recovery, actual
OpenSea/VRF/artwork retrieval, matching integration rollout and independent
audit/remediation remain open. The new controller also needs its own reviewed
normal construction/fee evidence; older constructor receipts are historical.
