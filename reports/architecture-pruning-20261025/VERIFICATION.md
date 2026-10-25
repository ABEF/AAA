# Verification of the smaller architecture

This records an undeployed source candidate, not production approval or an
independent audit. No public transaction, existing Anvil state, service, website
build/server, signer policy or paused monitor was changed.

## Solidity execution

**49 distinct selected behaviors pass across two fixture scopes.** The initial
run executed all49:44passed and5failed. The failures were fixture defects, not
confirmed production defects:

- Three fixed-ZZZ pool tests counted the Registry's getter but omitted the test's
  own subsequent assertion read. Expectations now count both; an omitted or extra
  production read still fails the control.
- Two native handoff tests retained a one-day parking deadline from the removed
  scheduling flow. The unchanged ten-minute production guard rejected it. The
  reviewed test request now uses100seconds.

[Exact fixture repairs](fixture-repairs/manifest.json) preserve preimages and
production source hashes. Only the5failed methods were rerun and all5passed;
the earlier44passes were reused, not rerun or added again. Two preceding runner
invocations executed no tests (full-signature regex mismatch and a rejected CLI
correction); they are preserved and never counted as passes. See the
[repair record](fixture-repairs/README.md) and [final five results](fixture-repairs/results.json).

The selected campaign covers direct governance/guardian/bootstrap/handover and
terminal authority; zero-asset record codecs; fixed-ZZZ pair admission; dual
prices/history; caller-bound activation/growth and stronger venue floors; funded
incumbent dust; normal/raw custody and exact native recovery; preparation callback
rollback/draining; full owner/share/trait/LP/royalty handoff; converted ETH credits;
new/old/trailing record rejection; partial funding/replay; funded abort and atomic
retirement. Real Access/financial contracts are used where described by each
fixture; controlled prices, token/venue/ownership helpers are explicit substitutes.

The pinned [AST selection wrapper](solidity/run-selected.py) retains chosen test
bodies and helpers, removes only unselected test methods and leaves production
source unchanged. The external profile/manifests retain exact input/output hashes.
No live RPC, actual Uniswap market qualification, real VRF or persistent chain is
used. No maximal1000-NFT or target-chain gas campaign is inferred.

## Python and service boundaries

**512 distinct methods pass across recorded source scopes**, not a fresh512-case
final-source run:

- [Services](services-tests.json):335initial passes, then1new historical-origin
  regression after restoring the old keeper's exact parked-location semantics.
  Two existing cases were repeated in that targeted check and count once.
  [Targeted record](services-legacy-parked.json):336distinct service methods.
- [API/events](api-tests.json):176methods,174initial passes and2failures. The
  current collection's Dormant3 check still used legacy status5; it now requires
  confirmed zero valuation. The event test's old17-entry literal was updated for
  the explicit33-entry historical catalogue, preserving all exact layouts.
  [Only the2failed methods reran](api-failed-recheck.json), both passing.

These exercise current/legacy profile isolation, eight/15-word decoding, new
statuses, direct-governance inventories, immutable saved journals, current CLI
not loading historical bridge logic, historical validation, current preparation,
actual-view balances, collection/read behavior, trace/price/review/lifecycle
checks and event compatibility. The catalogue has135descriptors: all133prior
entries remain exact and only two governance events are added. See
[event retention](api-event-retention.json). Offline mock RPC/temp SQLite and
HTTP only; no actual hosting/provider/recovery rehearsal.

## Compiler, bytecode and documentation

All127current src/test/script inputs typecheck (ABI/AST), with zero compiler
errors. Initial typechecking omitted two existing Foundry remappings; that
harness failure is retained before using the exact pinned foundry.toml list.
Further typechecks bind final test fixture edits, not repeated execution passes.

All36normal production object gates pass under unchanged0.8.26/Cancun/via-IR
optimizer settings. All41production source hashes match current sources. The
final source-comment checkpoint has its own build; earlier build sizes are not
counted again. [Object comparison](bytecode-comparison.json) explains each delta.
Access total initcode42,177leaves6,975bytes with its static96-byte arguments;
Vault runtime22,852leaves1,724bytes. RoyaltyFactory runtime24,507leaves69bytes.
No EVM/compiler/size waiver is used, and sizes are not execution gas estimates.

The source-bound function reference has31concrete contracts,608functions,
31constructors and13receive hooks. No callable purpose/caller or top-level input
explanation gaps remain; exact tuple/types/outputs are generated from the current
ABI. Old selectors and their stale notes are removed. ABI/storage changes are
fresh-deployment changes, never an in-place upgrade of old contracts/journals.

The current operator, component, lifecycle, profile, source/input, governance,
custody, Todo/features/roadmap and release instructions are updated. Retired
research/tests retain exact archives; unpublished obsolete research drafts are
backed up locally rather than published as working features. Source checks,
Todo/reference/link and source/evidence hashes are recorded in this directory.

## Limits and remaining work

Earlier audits, invariants, static/fork/browser/maximal gas tests retain their
original source scope. No unchanged full suite was rerun simply to inflate counts.
Actual source/feed/proxy independence, cheaper routes, VRF, authorities, OpenSea,
matching native3 website/wallet integration, strategy/gas economics, real operations
and independent audit/remediation remain open. External custody does not provide
an automatic issuer/chain ownership-ledger migration; its continuity plan remains
an operator/release requirement before irreversible exchange.

No new unprivileged theft/dilution/double-claim path was confirmed in this bounded
internal review. This is not a guarantee of exploit absence or universal code
minimality. Immediate governance and external custody are explicitly trusted.
Publication is separate; check its receipt. **Production NOT APPROVED.**
