# NFT position summary: scoped verification

2026-10-19. Internal presentation verification, not production approval.

The main website and local contract adapter display fixed rarity royalty weight
below the pattern (label: Royalty weight). Cards retain attached LP; active cards show one combined claimable total. The detail view groups
claimable LP rewards (individual plus collective), royalties, attached liquidity,
history and cumulative claims. The pool label is removed from details. Main preview
history remains gross before allocation; local history retains individual,
collective and royalty components with existing missing-price semantics.

- `node --test tests/local-client.test.mjs`: 35 passes, zero failures/skips.
  Updated cases cover dormant omission, sticky activation despite unavailable
  valuation/evolution, unread stale financial payloads, exact same-currency
  addition, distinct-currency preservation, cumulative claims and fixed royalty
  traits before/after activation. Existing transaction client guards also pass.
- `node --check app.js` and `node --check local-view.js`: pass.
- `node build.mjs`: 5,588-file static build passes.
- Browser at localhost:4179: four saved holdings and wallet preserved; royalty
  trait under pattern, one card claim total, and #444 breakdown verified visually.
  #444 retained $1,432 LP, $203.70 gross all-time fees, $2.91 gross daily fees and
  $196.50 lifetime claims. Browser error log empty. No simulated financial action
  or reset was submitted.

The source bindings identify the website files. Backend and unchanged broad
suites were not rerun. Website operator impact: normal asset reload; no service,
signing or financial submission change. The separate registry policy changes
operator pool switching as documented in the manual. Main-only publication; inspect Git for the exact revision. Public
server and paused monitoring unchanged. Production wallet/service qualification
remains tracked in [the central task](../../TODO.md#task-transaction-ui).

## Registry verification and internal review

The user approved one contribution pool at a time, preserving future migration.
Only ZZZPoolRegistry production source changes: explicit selection and atomic
single-enabled-pool invariant at common configuration, dependency-free stop/clear,
getter/event. Generic migration/maintenance support is retained. The alternate
Buyback test route now disables deposits; it still tests rejected wrong-pair swaps.
[Source-bound results](contract-checks.json): 97 affected Solidity cases passed in
the initial run. The new suite was rejected because one name started with the
removed testFail prefix. After renaming only that test, all 14 suite cases pass
(seven new policy cases and seven inherited operator cases). Retained successful
cases have complete unchanged compiler dependency bindings. This is combined
scoped evidence, not one fresh full regression. No failure remains in this scope.

Registry default-profile compiler objects: 12,619 runtime bytes; 34,225 creation
bytes plus the 32-byte constructor argument, below 24,576/49,152 limits. ABI getter
and event are present in compiled output. Source/bytecode/build-info bindings
match; no altered optimizer or raised production size limit. No redundant second
build, unchanged broad Solidity run or live fork was required for this local guard.

Internal review checked both configure entry points sharing the invariant, exact
governance and canonical locks, full validation before selection, dependency-free
stops, disabled historical admission, repeated stops, failed atomic rollback,
same-pool parameter changes and operations-only stops. The fixed asset helper
uses view-only token/oracle reads; there is no untrusted mutable callback before
selection. Existing Entry and Vault budget checks read the stored deposit flag;
old claims and maintenance use separate guards. No new privileged role, transfer
recipient, principal withdrawal, timelock or migration algorithm was added.

The manual requires moving an existing bucket before opening destination
deposits, avoiding a competing activation occupying the target. The unchanged
move validator accepts operations-enabled destinations with deposits disabled.
Production initial selection, real venue/migration execution and independent audit
remain release gates. No deployed registry or local running deployment was changed.

Website follow-up: the combined LP reward renderer passed three affected cases;
the shortened Royalty weight trait passed its affected case. Other test bodies
and transaction handling were unchanged. Final static build and browser checks
confirm the updated labels and grouped rewards. Website main is
`35066cadf4956dbb33b91c490315a0de18806493`; public server unchanged.
