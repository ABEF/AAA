# Day-change audit and implementation improvements

**Production NOT APPROVED.** This is an internal, source-scoped review and repair,
not an independent audit, full final-source regression or deployment approval.
Read the [adapted prompt](ADAPTED_PROMPT.md), [exact scope](SCOPE.json),
[preservation matrix](PRESERVATION.md), [verification](VERIFICATION.md) and
[release gates](READINESS.md). Publication is recorded separately.

## Scope and important prompt corrections

The Paris day has 25 hours because of the DST transition: 24 October 22:00 UTC
through 25 October 23:00 UTC, end exclusive. The review freezes the observed
ancestry, not future commits later in that interval. It covers 24 reachable
commits with no merges from baseline `3551868` to initial main `55011c0`.
Mandatory reference `35007db755ad4007013c1828f83983202647857a` is included;
its immediate parent is `964e6b6`, and subsequent `55011c0` is a receipt only.
Renames/deletions, author/committer dates and all paths are preserved in
[the scope manifest](SCOPE.json). Fourteen unrelated dirty files and unrelated
untracked artifacts are excluded and preserved; owned additions to dirty
documentation are separately staged, never the unrelated suffix.

The generic prompt needed three material changes. First, this release uses
shared LP with per-NFT economic accounts, fixed ETH/ZZZ user inputs, direct
governance and explicit trusted custody, not individual holder withdrawals,
proxy upgrades, integrated bridges or a timelock. Second, intentional daywide
profile removals must not be mistaken for regressions against obsolete ABIs.
Third, exact reused evidence is separated from new execution; neither source
identity nor self-consistent reports prove financial correctness or live readiness.
The [adapted workflow](ADAPTED_PROMPT.md) records the full requirements and exclusions.

## Verdict on the previous completion claims

| Claim at reference35007db | Independent verdict | Evidence and consequence |
| --- | --- | --- |
| Duplicate royalty balance implementation removed | **Confirmed, behavior-preserving in reviewed paths.** The inherited nonvirtual helper has the same expression and ledger context. All12 caller observations retain timing and classification. | [Call-site matrix](royalty-matrix.md). No principal/fee/royalty unit conversion, external call, liability or eligibility change. Existing bytecode/layout evidence is source-matched, not rerun as new tests. |
| Duplicate route error implementation removed | **Confirmed, declaration reuse.** This is an internal v3 venue-identity custom error, not HTTP routing/retry behavior. The selector and original validator branches remain; duplicate noncallable ABI error metadata is removed. | [Preservation matrix](PRESERVATION.md), earlier exact compiler comparison. No new fallback, retry or change to admitted routes. |
| Guardian/initial-role logs are visibility changes, +45 runtime bytes | **Confirmed with qualified costs.** Stored roles, authorization and public function encodings remain. Successful new emissions are an intentional observable difference. Controlled current-context compilation reproduces +45 runtime and +175 creation bytes. | [Size comparison](solidity/controlled-size-comparison.json), [gas/event checks](role-gas.md). CREATE execution increases12,312; each tested guardian update increases1,642. These are raw local execution deltas, not a target-chain bill. |
| Obsolete native/outage expectations replaced | **Justified, but insufficiently sensitive in two cases; strengthened here.** Optional royalty faults should defer that currency, not revert valid LP activation. A partial-fill test could reject on output minimum alone; an oversized test could reject on wrong msg.value. | [Old/new assertion mapping](native-assertion-matrix.md) and [new native checks](solidity/NATIVE_REGRESSIONS.md). Intended guards are independently exercised with exact errors and rollback checks. |
| Evidence checks reject malformed/dependency/build drift | **Partly confirmed but incomplete; corrected here.** Existing source-drift controls worked. Eleven contradictory cases were accepted, including oversized objects plus true success flags and dropped stored dependencies/settings. | [Independent probes](evidence-negative-probes-initial.json), [checker review](evidence-review.md). Snapshot3 recomputes limits, enforces closure and coherent captured evidence. |

## Confirmed findings and corrections

### P2: valid native royalty custody broke NFT reporting and history

**High confidence; pre-existing integration defect.** Contract native custody
and deferred enrollment predate this day. Older readers assumed every active
NFT was already eligible for native royalties; replay rejected native deferral
unconditionally. A new NFT activated during ETH custody could lose its full
read projection, and valid history remained rejected even after full return.
This is availability/reporting failure; no theft or unbacked payment was shown.

The API now requires actual custody nonce plus consistent ordinals, counts and
cohort weights before accepting native eligibility lag. ETH balances remain
unavailable/null while external backing is absent. Healthy LP and other currency
balances can remain readable. Replay authenticates exact exit/return events,
unique IDs, full amounts, currencies and ordering. Returned backing is not new
income; earlier receipts stay with earlier eligible NFTs before recovery enrolls
newcomers. Full earnings reconciliation while funds remain external is still
unavailable. Missing/invalid history is never inferred or zero-filled.

The [royalty review](royalty-matrix.md) records the exact source boundaries and
guards, including conversion/canonical-handoff reasoning. Conversion synchronizes
native eligibility before directly crediting ETH, so deferred-native NFTs cannot
legitimately possess prior direct conversion credit in this pinned operating
implementation. Future new credit writers must revisit that invariant.

### P2: contradictory saved build evidence passed documentation validation

**High confidence; tooling assurance defect.** The old importer checked source
bytes but relied on producer success flags for sizes and ignored important
compiler/freeze/hash metadata. Stored snapshot schema2 also lacked a separate
closed source-name inventory. This could produce misleading documentation
acceptance, not an on-chain bypass or a falsely demonstrated successful compiler run.

The corrected importer captures each bounded JSON artifact once, recomputes
runtime/creation bytes, derives static/minimum dynamic constructor payloads,
enforces normal EIP-170/EIP-3860 limits and checks exact provenance/status/count
coherence. Snapshot3 binds the full compiler name union, dependency/build bytes,
settings, binary identity and unresolved dynamic argument targets. Contradictory
captures fail without replacing existing generated files. The source reference
is regenerated from the unchanged, saved matching normal build, not hand-relabeled.
See [limits and negative controls](evidence-review.md).

A final format follow-up also rejects Boolean/float schema identifiers and
invalid fixed-point ABI width/precision spellings. Two original-failure methods
and one affected control pass; valid current ABI values remain accepted. These
are documentation-format safeguards, not financial implementation changes.

The trusted-producer boundary remains: a malicious party capable of rewriting
compiler outputs, all hashes and reports can invent a coherent story. This check
is not build/test authentication, formal proof or independent analysis.

### Verification gaps: wrong-revert sensitivity in two native cases

The new partial-fill case uses the installed actual v4 Core/PositionManager
context and an actual partial-input observation whose output already meets the
oracle floor; Manager must reject the short exact input itself. The oversized
case now supplies matching native value, poisons the next read and requires the
specific amount error for both currencies. It cannot pass merely because value
is missing. Caller, venue, LP, prefunds and approval state remain checked.
Only test code changes; no financial implementation is weakened to pass.

## Broader project review and deliberate remaining boundaries

The [preservation matrix](PRESERVATION.md) ties ownership, mint/activation,
shares, fees, royalties, claims, compounding, rebalancing, pool moves, custody,
same-chain handoff and services to inspected code and exact evidence. Daywide
architecture removals were authorized fresh-candidate changes: no automatic
compatibility with historical accounting2/remote codecs or old deployments is
claimed. Historical readers and existing Anvil data retain their profiles.

No new unprivileged theft or replay exploit was confirmed in the inspected paths.
That statement is bounded review evidence, not assurance of absence. Immediate
governance can configure reviewed dependencies and authorize external custody;
the external custodian can withhold/divert funds. The source cannot enforce
return. Public wording must preserve that accepted trust rather than claiming
immutability prevents governance movement. Per-operation caps do not protect
against market loss, repeated turnover, common-mode oracle failure or key compromise.

Real independent feeds/routes, a cheaper ZZZ conversion route at the selected
1% policy, VRF, authority addresses, OpenSea primary mint and settlement,
native-profile website/services, worst-state gas/strategy economics, operating
recovery and independent audit remain unqualified. The selected high-fee pool
does not itself qualify a conversion route. The saved Slither review is stale
and is a **FAIL current-source release gate**; no hash-only update can close it.

Core size gates pass their captured scope, but RoyaltyFactory has only69 bytes
of runtime margin. Exact dynamic NFT URI constructor arguments and resulting
release initcode must be checked before deployment. CREATE/CREATE2 inventories
must use actual new artifacts; altered initcode changes CREATE2-derived addresses
where a deployment uses it. No actual deployment address was promised or changed.

## Documentation, operations and publication

The sole Todo keeps stable tasks; feature evidence, roadmap, release disposition,
operator manual, royalty/history guidance, callable snapshot and repository
memories are updated together. Reporting rollout requires retained raw logs,
backups, a separate replay database and both cohorts/current-state comparison.
No database repair or service rollout was performed. Outputs/read availability
changed; no new operator write function, permission, economic setting or signing
capability was introduced.

No public RPC/transaction/deployment/seal, website source/build/server,
existing8902/Anvil/NFT/LP/balance/journal/dist overlay or monitor operation occurred.
Public DEPLOYMENT stays null, signing Anvil-only, monitoring paused. GitHub
publication is a separate source action, recorded only after remote verification.

Official guidance used alongside installed implementations: [Solidity0.8.26
security considerations](https://docs.soliditylang.org/en/v0.8.26/security-considerations.html),
[v4PositionManager](https://developers.uniswap.org/docs/protocols/v4/guides/position-manager)
and [unlock/deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas).
The [same-day upstream review](../deep-cleanup-20261025/UPSTREAM.md) retains its
exact dependency applicability and open compiler-release review boundary.
