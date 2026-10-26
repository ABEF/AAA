# Systematic adversarial verification

## Coverage is separate from execution

[Coverage verifier](verify-coverage.py) checks exact catalogue equality, unique
contract/kind/signature keys, at least three distinct applicable cases per row,
source-location validity and source hashes. [Result](coverage.json):31contracts,
608 functions,31 constructors,13 receive hooks and1,987 scenario instances.
All44 project Solidity units are identified/pinned; the NFT canonical interface's
record/header/signature boundary was additionally checked against its concrete
NFT/companion callers. Shared families and inherited instances are not counted as
separate implementation proofs. [Partition map](COVERAGE.md).

Manual threat reasoning, review of existing test source and prior executed
evidence are explicitly labeled in the three matrices. An inventory validator
cannot establish that the judgments are correct or every permutation ran.

## Fresh affected Python checks

[Final runner](run-affected.py) selects only defined TestCase classes across13
usefully affected modules after the new main watchdog integration. [Receipt](affected-suite.json):
**244 unique methods:241 passes,3 explicit skips, zero failures/errors/source drift**.
Forty-two new methods are included once (9RPC,12holder,21watchdog); one of the
watchdog methods is the actual Unix-datagram skip, so41new methods execute/pass.

The three skips are actual Unix datagram behavior, Unix runtime ownership/mode
checks and a cast CLI smoke test because cast is not on PATH. No actual systemd
or cgroup/signing interruption rehearsal occurred. Existing51transport/history,
24holder and21watchdog development scopes overlap the final244and are not added.
The final affected rerun is justified by the new main import/RPC wrapper and
recovery integration; unrelated full keeper/Solidity/website suites did not run.
No real provider, wallet, key, installed Anvil, original database/journal or
operating service was used. [Deduplicated method IDs](execution-scopes.json).

## Counterexamples and test quality

[RPC before](rpc-input/before/rpc.json): the exact final9methods against unchanged
baseline adapter produce19assertion failure records and2injected parser errors;
the valid controls already pass. [After subset](rpc-input/after/rpc.json) records
all9passing with stable source/test hashes; those9are included once in the final244.
Malformed response/chain cases use actual decoding/validation. The recursion
cases explicitly inject the platform decoder-limit exception: JSON nesting
thresholds differ by runtime. The preliminary2000-level nesting probe did not
exercise that exception on this host and is preserved as exploration, not proof
of a fixed host-specific failure.

[Holder verification](ops-input/VERIFICATION.md) preserves two actual source
stages: bounded/strict JSON input and then sanitized argument parsing. Eight
final input-test bodies remain byte-identical to their bound earlier control;
four added argument methods fail pre-parser-fix with SystemExit and pass after.
Final24method/test/source bindings are explicit. Exploratory depth assumptions
and a preliminary narrative count correction remain identified, not relabeled.

Independent partition review of the RPC correction found no concrete regression:
finite fee-history floats, uppercase hex digits, checked integer chain-ID return,
existing profiles/allowlist, sanitized real errors and terminal WorkLimit remain.
Root review checked the holder correction/valid options/exclusive output and
the exact negative/final source stages. The [watchdog review](WATCHDOG.md) records the initial inert Windows fixture
errors and the independently found `.eth_call` progress-wrapper omission, both
corrected before the frozen final run. No Unix-gate relaxation occurred: the real
socket test remains explicitly skipped. A [Keeper-class AST check](keeper-core-equivalence.json)
confirms financial/signing/recovery method bodies are unchanged; main startup/
progress and source unit supervision are the only keeper changes. No assertion
or economic guard was relaxed.

## Reused unchanged contract evidence

The44production Solidity,31normal dependency and4build-input pins match captured
normal evidence;37normal object gates and existing static/size evidence are
**reused**, not newly executed. The previous exact15actual-v4 composition cases
and1000claim-order run retain their original source/fixture scopes. No unchanged
Solidity suite, compiler build, whole static analyzer, full keeper/service suite
or live capacity campaign was repeated for these Python/tooling corrections.

Production Solidity/ABI/storage/permissions/economic rights are unchanged. The
callable reference still checks31contracts/608 functions. Todo/source links,
stable task identities and scoped publication checks are recorded separately in
the final checks; none is production approval.

## Still unverified externally

Actual feed independence/controls, routes/liquidity, VRF, fixed-ZZZ burn support,
OpenSea/authorities, current3 wallet/services, target gas/strategy economics,
Linux/off-host restore/monitoring and independent audit/remediation remain open.
Conditional owner callbacks, immediate governance, trusted custody, failed token/
venue/chain and lost/escrowed owners retain the documented risks. No universal
absence-of-vulnerability or uninterrupted service guarantee is made.
