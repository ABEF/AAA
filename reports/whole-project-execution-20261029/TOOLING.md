# Tooling breadth review

Fresh static reads cover25 script/wrapper/workflow files and163 named/nested
bodies or whole shell/workflow/module definitions. `body-coverage.json` records
locations, hashes, review notes and explicit other-stream exclusions. Twenty-three
files exactly match the earlier whole-project source baseline; that comparison
is inherited **source identity only**, not reused test execution or old security
approval. No build, fork, service, signing, deployment, installation or network
operation was run.

## Repaired finding

`scripts/generate-artwork-library.py` used Python `assert` for real catalogue
admission: palette/pattern identity,600/300/100 supply, packed digests, decoded
inventory agreement and code bounds. Python `-O`/`PYTHONOPTIMIZE` removes these
checks. A self-consistent shortened rarity inventory or out-of-range code could
therefore generate Solidity despite ordinary execution rejecting it. Root
authorized replacing these six runtime checks with explicit `ValueError`.
Valid generation output is unchanged. No catalogue, library or artwork asset was
regenerated or modified.

`generator-final.json` records five new distinct methods passing, exercising
normal and optimized Python. The captured original generator fails eight
optimized subcases across four distinct methods (`negative-original.json`);
its valid control passes. Cases isolate shortened supply with matching hash and
codes, palette count, pattern order, digest disagreement, decoded-code mismatch
and out-of-range code with matching digest/inventory. Two existing methods also
pass (`catalogue-existing.json`): exact committed generated source and all1,000
cross-language inventory encodings. The final total is seven distinct methods,
not the number of subprocess/subcase invocations. Source/test/catalogue/library
hashes were stable and asset bytes were unchanged.

The first negative attempt (`generator-negative-before.log`) also contains two
test-fixture failures: JSON reserialization changed the raw-catalogue SHA embedded
in generated comments. The valid control was corrected to preserve exact input
bytes; the production generator/template was not changed to accommodate it.
This failed attempt remains recorded. `git diff --check` passed.

## Boundaries confirmed

- Dependency installation requires the lockfile, suppresses npm lifecycle
  scripts and checks the exact clean forge-std commit. CI actions are immutable
  revisions with read-only repository permissions. No deployment job appears.
- The current pool fork runner checks exact Forge/solc/effective normal profile
  before network use, strips inherited tool/profile/RPC secrets from its child
  environment, uses a bounded read-only relay, sanitizes upstream errors, owns
  only its child process tree, requires a new output directory and binds complete
  expected test inventory plus before/after source hashes. None was executed.
- The historical local labs own a new loopback Anvil, accept no public endpoint
  or wallet key, verify process/genesis/source identity, and reject current
  native/pricing-V2 startup before state/process creation. Their USDG/USDC,
  timelock,99% and mock-market behavior remains historical fixture scope; it is
  not current production policy or current-contract qualification. Existing
  port8902, its Anvil, overlay, signer and journals were untouched.
- Release-review and callable-reference wrappers were read and traced to their
  backend implementations; detailed backend bodies belong to the backend review.
  The dollar rehearsal prepares only a new disjoint directory with explicit
  chain31337 constructor guards, source anchors, pinned loss literals and source/
  generated/compiler hashes. Preparation is not compiler execution or deployment.
- Todo, callable and event-schema generators have explicit check/write boundaries;
  Slither admission requires successful fresh output, exact source coverage and
  recorded finding rationale, without claiming an independent audit.

## Remaining limitations

The historical `verify-local-website.py` writes its requested evidence path in
`finally` and can overwrite an existing file. Root chose to record this as a
low-priority historical provenance limitation; it was not changed or run.
`verify-local-stack.py` separately refuses an existing output file.

The general `verify.sh` wrapper does not sanitize arbitrary inherited Foundry
overrides or independently capture effective profile like the stricter fork
runner. Controlled CI specifies its toolchain; local release evidence still
needs explicit effective-profile/source pins. No false current gate pass was
demonstrated and no compiler/size gate was relaxed.

Local browser recovery and broad discovery remain historical tools: browser
pending-only hashes are returned before durable mined-receipt binding, local
recovery JSON uses permissive parsing, and broad unittest discovery may include
imported fixtures. These are not public signing/recovery guarantees. The focused
evidence here uses exact distinct method identities. The Decimal vector script
also writes fixtures at module import, so it was read statically and not imported.

Toolchain/dependency downloads, actual Unix process supervision, target provider/
gas/finality, real external market/metadata services and exact-revision CI remain
separate qualification. The original dirty `scripts/run-fork-checks.py` and all
protected signing/website/IPFS paths were left unchanged.
