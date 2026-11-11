# Contract partition: individually reconcile 60 historical obligations

Baseline: `6cfa4f1d478c3d15470519801f9703f9f8a8d656`, main. This partition owns
indices `0:60` of the original 90-row contract packet; the final 30 were
explicitly reassigned to the other reviewer. It does not claim to cover all 271
rows or to be a new audit of every callable contract body.

[FINDINGS.json](FINDINGS.json) contains **one individually written assessment for
every assigned ID**. Each separates current source behavior, live qualification,
accepted risk/superseded recommendations and a concrete remaining action. Every
row retains its original matrix/JSON pointer/hash and existing Todo IDs. The
[ID index](INDEX.md) provides navigation; status is in the full individual row,
not inferred from its title or from another row's test results.

## Material result

One current consumer defect was found while tracing `historical/FB-15`:
`Lineage` inherited a successor's execution-price1 setting into its old V10,
accounting7 LP2 predecessor, while rejecting an explicit predecessor override.
That made a compatible replacement's historical reader request new capabilities
from old pinned contracts. The on-chain handoff only requires the same V10 schema
and exactLP profile plus the individually reviewed destination commitment; it
does not require the predecessor to have execution-price1.

The backend owner fixed the explicit per-predecessor profile, omission0 and
provenance handling during this campaign. The baseline assessment remains frozen
and still describes the defect at `6cfa4f1`; the separate
[post-baseline fix receipt](POST_BASELINE_FIX.json) binds the correction and its
actual checks. The contract reviewer independently inspected the fix and all five
new focused test bodies. No Solidity change or unchanged suite rerun was needed.

The affected run had 38 methods: 37 passed and one old accounting5/6 fixture
method raised two subcase `KeyError: seadrop` errors. Only that outdated assertion
was corrected, then its one-method rerun passed. Thus **38 distinct methods have
composed passing evidence**, including five new focused methods; this is not a
fresh 38-method all-pass run. The metadata check injects already-authenticated
epochs to verify serialization; it is not an actual EVM handoff or archive-service
qualification. Original failures remain retained by the backend reviewer.

## Decisions and older recommendations challenged

- **Entry routes:** the deferred unusable v3 whole-input branch is already removed
  in direct Entry3. It must not be restored, nor confused with the separate earned
  LP converter's optional v3/WETH compatibility. Royalty4 has no converter.
- **Eligibility and timing:** outside-only, 900-second confirmation and 60–600
  jitter were superseded by approved 85%-of-boundary-distance, 600-second sampled
  evidence and 60–300 jitter. Raw cooldown observations and economical near-end
  paid enrollment are implemented. They do not prove uninterrupted history.
- **Optional residual:** the old statement that all second-position work remained
  discussion is superseded. Current main plus at most one residual, distinct
  per-range valuation, main-only contribution and guarded/forced consolidation
  remain the accounting model.
- **Exit authority:** the original permissionless/keeper allocation and delivery
  were superseded by custody5 governance-only batches. The retained historical
  keeper worker rejects that current profile. Holders retain their reward claims
  and owner-only failed-recipient principal fallback; no custody-address exit or
  bridge is reintroduced.
- **Exact units and royalties:** historical index/fraction/royalty-conversion
  arguments are not current implementations. ExactLP7 and royalty4 tickets retain
  independent LP share/equal collective/rarity economics. Royalty opening is one
  hour after the sale end, not 24 hours. Allocated units are assignable, while
  zero-cohort/preadmission receipts still require the reviewed recovery decision.
- **Loss controls:** contribution default3% replaces old1%/2% examples; it does
  not change conversion1%, maintenance3%, additional1%, source agreement3%, caller
  floors or venue limits. A3% source spread can still consume almost the entire
  conservative contribution budget before fees. No auto-widening is justified.
- **Fixed identities and simplification:** native ETH/one ZZZ, fixed burn/return
  identity and permanent four-bucket admission make old arbitrary-pair and foreign
  compound scans obsolete. Historical selectors/codecs retain their explicit
  compatibility purpose. Callback, settlement and exact-backing barriers remain
  distinct protections.

## Still requiring real evidence or an accepted tradeoff

The rows keep existing Todo ownership rather than creating another release
checklist. In particular:

| Remaining matter | Existing Todo ownership |
| --- | --- |
| Independent sources, actual depth, route/target feasibility | `dual-price-qualification`, `creator-zzz-price`, `activation-assets`, `lp-execution-routing` |
| Full operation gas and actual deployment arguments | `deployment-initcode`, `testnet-rehearsal`, `activation-quotes` |
| Repeated permitted losses, keeper/external ordering economics | `security-keeper-manipulation`, `security-external-manipulation` |
| Broken assets, inaccessible receivers and exact funded replacement | `asset-liveness-dust`, `security-dependencies`, `security-chain-recovery` |
| Terminal batch completion, current-owner payout and gas | `custody-composition`, `native-custody-recovery` |
| Authentic history, services, metadata, VRF/OpenSea and independent audit | `financial-history`, `host-services`, `metadata-ops`, `fair-draw`, `opensea-mint`, `audit-release` |

Current full cold Entry costs around15.3M/15.6M for activation and still fails the
unchanged12M default. Existing optional gas policy2 is not automatically enabled
or qualified. The bounded router is not a global/gas-adjusted optimum. Immediate
governance and its explicit emergency financial bypass remain trusted; no
cumulative-loss breaker or timelock was silently added.

The earlier late-increase fee-netting question remains **unverified** and
dependency-qualified, as recorded in the daily audit. No exploit was constructed
and no speculative production check was added. Ordinary outsiders cannot
interleave another transaction inside an atomic join. Actual fixed-token/proxy/
periphery callback reachability and accounting effects still require evidence.

One nonfunctional comment in `ActivationAssets.admitPoolAsset` still mentions a
possible WETH target. Current `PoolRegistry.configureNative` admits only native
ETH/fixed ZZZ, and maintained architecture instructions are authoritative.
Changing Solidity only for that comment would change metadata/runtime pins and
the source/static closure without improving execution; the parent declined such
churn. This is a maintenance note, not an unsupported principal path.

## Evidence and limits

[verification.json](verification.json) checks all 60 exact original JSON pointers
and canonical hashes, **201 baseline source references across 65 files**, line
excerpts and existing Todo IDs. Every baseline evidence byte comes from
`git show 6cfa4f1:<path>`, not mutable central documentation or the concurrently
corrected backend. Both raw and normalized UTF-8/LF hashes are retained.

[original-sections.json](original-sections.json) contains 135 exact section
references, 115 unique sections. All historical file hashes match the retained
original records. One old operations-hardening README is an explicitly labelled
retained **untracked** original, not current Git evidence or a published report.
It was read without editing or staging it. No current source assessment uses that
untracked file as implementation proof.

The report-integrity verifier is not a feature test or proof that the human
assessment is correct. `verification.json` remains the exact original local
receipt, including its then-available external original; it is never rewritten by
the maintained verifier.

The portable read-only command is:

```text
python -O reports/remaining-271-20261111/contracts/verify_review.py
```

It derives the expected first60 records from the tracked 310-row registry at
`6cfa4f1`, its remaining271 set and the original explicit 90-row contract topic
partition. It needs neither the local assignment-packet path nor drafting
helpers, and its explicit integrity checks remain active under Python `-O`.
By default it checks all201 baseline source references and134 Git-backed
historical section references, reporting `external_original_checked:false` and
`complete_original_raw_checks:false` for the one retained untracked README.
An optional `--external-originals ROOT` may supply an archive with the original
repository-relative path to check that additional source. Its absence is explicit,
not a complete135-raw-source pass. No raw README is newly published.

[VERIFIER_QA.json](VERIFIER_QA.json) records the optimized positive artifact check
and an omitted-row negative rejection, with unchanged hashes for both the frozen
findings and the original receipt. Those are artifact checks, not feature tests.
The retained `build_review.py` and `read_original_sections.py` are historical
drafting utilities using the original local preparation packet, not dependencies
of verification. They can regenerate artifacts and should not be rerun against
this frozen record merely to verify it.

New production Solidity, compiler/analyzer runs, forks,
wallet actions, deployment, services, websites, existing Anvil, saved journals,
keys and the user-paused heartbeat were untouched by this partition. Earlier
execution evidence retains its exact source/workload scope. Production remains
**NOT APPROVED**.
