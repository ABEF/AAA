# Operator reference and documentation consolidation

Baseline main `28f75738a01efae2a2e11cf861e5e94d4d10efb3`. Documentation/tooling
change only; Solidity behavior, economic rights and all running environments stay
unchanged. **Production NOT APPROVED.**

## Result

The maintained [Operator manual](../../docs/OPERATOR_MANUAL.md#operator-call-tables)
now has four-column tables covering all820external/public ABI functions,
37constructors and13ETH receivers across37contracts. Each explanation is at most
five words. Groups follow management duties: safety/permissions, daily LP work,
policy/pools/prices, revenue/claims, recovery, NFT/contributions and bound helpers.
Routine calls are visible; reads/constants, module-only calls, callbacks and
deployment entries are folded to keep day-to-day work navigable.

Every overload has an example. Tuples and arrays are expanded in exact ABI order;
ETH transaction value is separate from arguments and gas. Large integers use
exact decimal strings inside JSON examples. Current snapshot symbols remain
unresolved deliberately: there is no approved production address/configuration
from which to manufacture executable examples. The guide explains how to obtain
NFT IDs, bucket IDs, physical LP IDs, policy fingerprints, custody/portfolio
hashes, raw amounts and reviewed-operation hashes. Numerical defaults illustrate
current policy; they are not instructions to overwrite a live configuration.

The [full reference](../../docs/CONTRACT_FUNCTIONS.md) still owns exact outputs,
caller restrictions and behavior notes. The short table does not grant a human
permission to call a module callback. Governance-only terminal distribution,
keeper authorization, holder claims, bootstrap bindings and public reads remain
distinct. Existing detailed procedures retain review/simulation/receipt/reversal
and irreversible boundaries. External ZZZ allowance approval/revocation is
explained separately; native ETH needs no ERC20 approval.

## Consolidation decisions

| Area | Correction |
| --- | --- |
| Operator inputs | Replaced the incomplete partial write catalog with the complete generated appendix. Added ID/hash/unit lookup and exact-allowance guidance. |
| Entry routing | Merged distinct current controls/profile guidance into ACTIVATION_ENTRY; retained ACTIVATION_ROUTING as a stable pointer for historical incoming links. |
| Old plans/prompts | Three superseded pages now point to exact original Git text, retaining old anchors. Their original contents and all earlier reports remain preserved. |
| Audit brief | Replaced the whole-project page's stale third-pass redirect with one current whole-project brief. This consolidation does not execute another audit. |
| Rules and recovery | Corrected fixed-minimum/payee wording, historical profile labeling, single-operator governance and obsolete permanent-quarantine/no-rescue statements. Unallocated recovery1 remains separate from earned/deferred entitlements. |
| Navigation/context | Reconciled README, documentation map, feature reference, roadmap, release record, instructions, context and handoff. Removed duplicate dated checkpoint prose while retaining implementation/evidence links. |
| Ongoing maintenance | The normal verifier checks ABI coverage, source binding and generated examples. Changes to function inputs/outputs/permissions require coordinated notes/examples/manual updates. Task status remains solely in project-todo.json/TODO.md. |

[DOCUMENT_MAP.json](DOCUMENT_MAP.json) records all105baseline maintained Markdown
paths and the actual changed/retained decision. Specialist guides and historical
codecs are kept where they have distinct responsibilities. An unchanged page is
not evidence that every sentence or future scenario has received a fresh audit.

## Boundaries and remaining work

No contract build/EVM suite was rerun for these documentation changes. Focused
reference/tooling checks and exact source/dependency preservation are recorded in
[verification](VERIFICATION.md). Immutable historical evidence is not rewritten
as current proof. Known release requirements remain in the [sole Todo](../../TODO.md):
qualified feeds/routes/VRF/authorities, OpenSea integration, matching services/site,
hosting/history/recovery, actual operating economics/gas and independent audit.
The short call examples do not qualify any of them or authorize deployment,
sealing, public signing, a site/service change or a local-chain reset.
