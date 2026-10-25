# Controlled Access role-event gas

The controlled baseline and candidate use the same compiler, current dependency
bytes and build settings. Their Access runtime sizes are **9,207 / 9,252** bytes
(+45), and creation objects are **42,081 / 42,256** bytes (+175). The constructor
wire labels and three address arguments are unchanged.

Four isolated Forge tests deploy those saved bytecodes in `setUp`, then check
authority and decoded role events in separate test transaction contexts. They
do not import production Solidity sources, contact RPC, use keys, deploy a
public contract or change the existing Anvil/service state. All four pass.

| Measured operation | Baseline raw execution gas | Candidate raw execution gas | Difference |
| --- | ---: | ---: | ---: |
| Constructor CREATE, including factory creation/code deposit | 8,446,648 | 8,458,960 | +12,312 |
| Guardian grant, committed zero to one | 26,598 | 28,240 | +1,642 |
| Idempotent guardian grant, committed one to one | 6,698 | 8,340 | +1,642 |
| Guardian revoke, committed one to zero | 9,498 | 11,140 | +1,642 |

Gas deltas use identical assembly CREATE/CALL helpers, preallocated bytecode or
payload memory, and cooled target account/storage state. They exclude transaction
intrinsic gas, transaction calldata, L1/network charges and applied refunds.
In particular, the revoke figure is raw execution, not net billed gas after
refunds. Governance/bootstrap share the same test caller; the sealed-governance
authorization branch and target-chain cost are not measured.

The tests assert both deployments retain the same selected governance,
bootstrap, keeper and initial guardian. Baseline constructors emit no role
events; candidate constructors emit exactly the keeper then guardian grant.
Each successful candidate guardian update emits exactly one event with the
expected emitter, indexed account and encoded Boolean; old updates emit none.
Stored role results remain equal after grant, repeat and revoke.

The initial combined control passed, but its first nonverbose JSON omitted
individual observations. A log-only rerun exposed raw measurements. The
combined grant/revoke transaction used dirty-slot pricing, so its revoke gas
is deliberately excluded from this table. Its raw outputs and reason remain
preserved. The four isolated methods replace that measurement limitation;
repeated controls are not additional feature coverage.

[Machine-readable measurements](role-gas.json) retain commands, hashes,
settings/dependency identity, bytecode sizes, constructor labels, raw test
results and limitations. The actual harness/config/compiler artifacts remain
outside Git under the dated `role-gas-isolated` evidence directory. This is not
deployment qualification, a full regression or independent audit. Production
remains **NOT APPROVED**.
