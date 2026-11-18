# Payload5, read-policy observation and unsigned preparation

Completed18November2026 at the accepted actual
`royalty-rounds-20261118` build. Internal source review; **production not approved**.

## Current C08 source and affected recheck

The final accepted [build/final](build/final/normal-size-evidence.json) is C08,
Royalty creation25,543 bytes, hash
`0x7005da5d4714523f67459f0e7e9cbf5b8ac2612aafc1e84d5fb683b3d3bba44b`;
manifest canonical SHA256
`6bad11a16db2e530765aeb738b7ad546d95ed35944b10a4b16d63670aee9a71c`.
[FINAL_PAYLOAD5.json](FINAL_PAYLOAD5.json) binds its exact100-source artifacts.
C07 pins/provenance remain in [c07-pins](consumer/c07-pins/INDEX.json).

A source follow-up found that a third party could donate and synchronize a
prefund on an unused successor before import. The derived reserve sum then
counted that old opening category twice after all actual prefunds were assigned
to orphaned. C08 clears the old opening pool at asset import and stores
`orphaned=(acc+prefund)-liability`; the header already checks `acc=liability+orphan`.
Both total addition and subtraction stay checked. This preserves prefunds as
unallocated target funds and imported holder claims; it adds no recipient or
economic authority. The adjacent `pending` getter reuses one same-call reserve
read. New Solidity accounting/recovery checks are separate from consumer tests.

Only four artifact-dependent consumer methods ran after that correction; all
pass with stable source/protected-file brackets. The other eight controls were
not repeated. The relevant consumer/test bodies are byte-identical, the F5
helper differs only in its manifest pin, and the production template differs
only in actual factory code/part/binding pins. These are still12 distinct
consumer methods across explicit stages. [C08 recheck](consumer/C08_RECHECK.json)
retains exact selected methods, source proof and raw results. No compiler, EVM,
network, unchanged suite or release approval is implied.

## Historical C07 source and affected recheck

The then-accepted C07 graph is [build/c07](build/c07/normal-size-evidence.json),
not the initial [build/current](build/current/normal-size-evidence.json) stage.
The final Royalty creation is25,546 bytes, hash
`0xae3492d899e93d293074a8b4ca3c30565470b92512529d213f0f316361a7c1b6`;
manifest canonical SHA256 is
`d9046cad8294c562928a585eb3c5c1e22141553bf51614d84cd3bfb85cb1a8e5`.
Its pinned provenance is retained in [c07-pins](consumer/c07-pins/INDEX.json).
First-source helper/manifest/template/provenance bytes remain separately archived
in [first-source-pins](consumer/first-source-pins/INDEX.json).

Seven methods affected by final pins/ABIs were selected again and pass with a
stable source bracket. Five unchanged controls are reused at their explicit
prior source scope; this is still12 distinct consumer methods, not19. Before
that final pass, strict artifact admission correctly rejected a registry key
pointing at the61-root-source map rather than the existing100-source compiler
content map. The initial seven-method attempt has3 passes/4 errors; it and the
registry-only correction remain visible. No compiler, EVM, network or unchanged
suite was run in either consumer stage. See [final recheck evidence](consumer/FINAL_RECHECK.json).

The final source derives `accounted(asset)` from checked liabilities, orphaned
and opening categories; its removed mapping changes private slot bases. Its
self-only activation wrapper now takes `(address,uint256 readLimits)`; this is
not an operator input. The authenticated low32-bit read cap/full-frame witness
lets healthy cheap accounting finish without unused1M reserve. Partial-frame
read faults defer only after a proved full read allowance; other partial-frame
failures revert. Full-frame failure isolation retains the original1M allowance.
Actual rights/fault/gas behavior remains independently verified by Solidity and
full-flow evidence, not these consumer checks. Historical payload3/4 bytes and
existing state are unchanged.

## Initial source and consumer implementation

Fresh schema17 now explicitly selects factory payload5. The helper/manifest bind
actual normal creation bytes, both immutable data children and all100 accepted
source files. Royalty creation is25,569 bytes, hash
`0x6f4dd3b4b608f1800f1d635a38c105ce2c63ad950d4ad624b0015a78e115a6e1`;
manifest canonical SHA256 is
`4b304846ab5451477229ab11aebbdc06f8b2e135aaa2cfa35ae9ae459cc53cca`.
The source-only template retains null deployed addresses/observations and false
approval flags. It declares allocation version2, while original-currency
settlement remains4. No source10 reporting or canonical-row reinterpretation
is introduced.

Omission/exact3 retains payload3; exact4 retains payload4. Their code helpers,
manifests and archived templates are unchanged. The prior fresh payload4
template is archived byte-for-byte, SHA256
`cc1061255416857aab34b6ccfe4c44b0281f6745fc142cda2440ea08a011692b`.
Exact historical file pins are in [FINAL_PAYLOAD5.json](FINAL_PAYLOAD5.json); the first-source payload5 pins are retained separately above.
Old payload4 tests now explicitly use that archived configuration and the
immutable authenticated q03 build. They do not reinterpret current source as
payload4 or weaken the deployment reader's current-source requirement.

Payload5 adds a scoped `royalty_read_policy` inventory section. It observes the
separate activation-only ERC20 balance-call allowance through
`royaltyBalanceGas()`, authenticates the legacy gas tuple/fingerprint and
reciprocal controller at the same canonical anchor, and checks the exact gas
revision. Its new domain-separated fingerprint is explicitly computed offline;
no nonexistent on-chain fingerprint getter is requested. Failed reads erase
stale positive observations. Unknown declared values remain null/blocked.
Ordinary sync/claims/canonical balance reads and the full1M isolated sync
allowance retain their separate paths.

Unsigned pre-seal preparation preserves the original twelve setup families and
their order. An optional top-level `royalty_balance_policy` request prepares
only the typed cap setter. Omission requests nothing; partial data produces
null calldata and blocks completion. New irreversible-review rows request only
real allocation/cap/gas getters from the accepted current ABI. No actual
authority, code, simulation, submission, cap adoption or sealing is asserted.

## Verification

**At the initial source,12 distinct focused Python methods pass:11 new and1 changed old selector
control;0 failures, errors or skips.** Initial execution passed all12. The new
historical-identity method was then strengthened to execute the actual archived
compiler loader, and only that changed method ran again and passed. Total13
method executions are not13 distinct checks. Exact byte reversal and AST review
prove that all other recorded source and method bodies are unchanged; those11
results are reused, not rerun. Both execution brackets and the four original
dirty-file hashes remain stable. Raw output, compressed source brackets and
method IDs are in [final01](consumer/final01/PUBLICATION.json); the stronger
one-method follow-up and exact reuse proof are in
[final02](consumer/final02/PUBLICATION.json).

The new methods check actual accepted creation/data parts and rejection of old
bytes; unchanged historical identities; strict selectors and mixed profiles;
integer gas/revision bounds and independent fingerprint encoding; real observer
methods against bounded synthetic same-anchor RPC replies; failure clearing and
declaration mismatch; unapproved/null templates; exact optional setter calldata;
unknown/malformed-input rejection; and actual required-read ABIs. The observer
test separately exercises decoding the new allocation-version getter.

No unchanged suite, compiler, EVM or live-RPC test ran in this consumer stage.
Actual engine correctness, maximum-state Entry gas/full20% headroom, normal
build/static review and operating qualification have their own evidence; these
Python checks do not substitute for them.

## Short operator inputs

| Function | Input | Example | Explanation |
|---|---|---|---|
| Policy.royaltyBalanceGas | None | `royaltyBalanceGas()` | Read activation token budget |
| Policy.setRoyaltyBalanceGas | uint32 gasLimit; nonzero bytes32 reviewHash | `50000, REVIEWED_HASH` | Set activation token budget |
| Royalty.ROYALTY_ALLOCATION_VERSION | None | `ROYALTY_ALLOCATION_VERSION()` ->2 | Read allocation engine identity |

Gas values are raw gas units, never ETH, token decimals or basis points. The
setter accepts10000..1000000 and requires the existing configuration authority
and operating state; it increments the existing gas revision. A review hash
must commit the actual reviewed operation. `REVIEWED_HASH` is a placeholder,
not a callable value. Cap increases require actual renewed workload review and
do not raise the holder20M policy, its full20% margin or any existing limit.

For the offline planner, a complete optional request is
`"royalty_balance_policy":{"balanceGas":"50000","reviewHash":"0x..."}`;
replace the ellipsis with all64 reviewed hexadecimal characters. JSON inventory
values use integers instead; this typed ABI-input example uses the planner's
existing canonical decimal-string format.
