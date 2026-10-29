# Two sequential prompt challenges

The user expanded the date-limited third-pass request to the whole project.
Before drafting, three source-pinned understanding maps reconstructed contracts,
backend/operations and website/API features. The [understanding](UNDERSTANDING.md)
and [knowledge assessment](KNOWLEDGE.md) distinguish implemented behavior,
historical compatibility and external release requirements.

## Draft and challenge identities

| Stage | SHA-256 | Result |
| --- | --- | --- |
| Original draft1 | `debf9bc08a9f9621f0105041e38b610b500efe9cd372b6108100a64b52bb8269` | Independently challenged against frontend and operations maps. |
| Revised draft2 | `85544b5b73796cc1d1f30fea03570ad92f472cc01135e540dd761045c15fdae3` | Separate contract reviewer checked actual code, installed dependencies, authorization and counterexamples. |
| [Final executable brief](../../docs/WHOLE_PROJECT_AUDIT_PROMPT.md) | `5cd040ace83c4865dd1cc7aac9e85373b4142603b0ca7af07f4c46d3f7f44206` | Final factual refinements applied before execution began. |

Raw drafts, both first-round critiques and the second-round critique are retained
with hashes in the external `whole-project-audit-20261029` evidence directory.
The final report links their manifest. The second round reviewed draft2 after
first-round revisions; parallel comments on draft1 are not counted as round2.

## Material adaptations and corrections

1. Review all feature families and eight complete user/operator journeys, not
   only October26-28 changes or the confirmation buffer. Include financial
   classes, full six-domain replacement, terminal returns, metadata, UX, versioned
   consumers, CI selection, recovery and critical-path work/latency.
2. Correct a false proposed invariant: royalty claims may index already-received
   funds through `_sync`; LP claims do not harvest or rerun80/10/5/5. Whole
   claimable sums need not equal liabilities because backed fractions/division
   dust remain. Sub20 boundary dust goes to incumbent individual owners, so
   exact lifetime allocation ratios after every entry are not a valid invariant.
3. Four permanent custody slots is an upper bound, not four required funded LPs.
   Lifetime aliases grow independently; quantify workflow rather than delete
   records, invent an import override or silently impose a new policy cap.
4. Separate public read/preparation from wallet authentication; extension-selected
   and dapp-permitted accounts can differ. Preserve confirmed receipts through
   API lag, exact independent card versus atomic-total provenance, current3 versus
   fresh4 profiles, public signing disabled and existing Anvil identities.
5. Distinguish selected12hours/900/300 from permitted governed bounds, polling
   from confirmed observations and permissionless harvesting/batching from
   governance exit authority. Preserve the deliberate final conversion head read.
6. Require findings with reachability, negative/positive evidence and tradeoffs.
   Inventory rows and historic tests are not fresh executions. Record pending
   depth honestly; reuse only exact source/child/dependency/profile evidence.
7. Keep the website read-only outside writable roots; prepare any justified patch
   separately. No new strategy, custody right, token, timelock, grace period,
   public transaction, server/site/service rollout or heartbeat is implied.

Rejected additions: generic security guarantees, new passive/40% strategies,
unrequested role changes, blanket retesting and mandatory live probes. Each would
either contradict settled requirements or create evidence/cost without closing
a demonstrated gap. Actual feeds/routes/VRF/authorities/OpenSea/host/gas and
independent audit remain unresolved release gates.

## Subsequent explicit user steering

During execution the user asked what polling/inclusion meant and the tradeoffs.
After a concrete explanation, they approved four-minute keeper checks, retaining
the15-minute duration and strict five-minute on-chain maximum. This supersedes
draft/final brief's initial300-second service schedule only; the frozen brief
and phase1 maps keep their original hashes. Source rollout, pending recovery,
health compatibility and targeted verification are part of the final review.
No grace period, earlier rebalance, new authority or running-service change follows.
