# Current documentation reconciliation

Reviewed 2026-10-26 against published main `6d7459d` and functional source
`2a9c65b`. This is documentation maintenance, not another implementation/audit
campaign or release approval.

The sole [Todo ledger](../../docs/project-todo.json) and generated [Todo](../../TODO.md)
now distinguish current requirements from earlier source-scoped evidence:

- ETH and fixed ZZZ are the only contribution inputs. Historical stablecoin and
  wrapped fixtures retain their own identities, balances and evidence.
- Contribution default2% means a98% marginal deployed-LP floor, with captured
  governance/caller/venue limits; earlier99% examples are historical. Conversion1%,
  maintenance3%, ceilings10% and the3% source-agreement band are unchanged.
- Direct governance2 has no proposer/executor scheduler or queued predecessor
  operations. ZZZ/buyback/normal-exit identity cannot be rebound after sealing.
- Current services/rehearsals require accounting3/fee1/governance2/localV4;
  local Position V3 and canonical handoff V4 are different identifiers.
- OpenSea primary mint needs actual supported integration, not just an approval
  label. The published native2 website reader is not current3 acceptance.
  Public signing stays Anvil-only by user decision. Future-chain history is
  deferred outside this release; no integrated bridge is reintroduced.
- Source-only watchdog support needs an authorized real Linux cgroup/signer-stop
  and preserved-pending/no-resend rehearsal. Optional bad royalty currencies may
  leave healthy balances readable but exact backing/history can remain unavailable.

Repository instructions, current context and resume guidance carry these
boundaries. README, feature reference, roadmap, operator manual and linked
recovery procedures were reviewed; their implementation/procedure descriptions
already match. No new call, permission, parameter, restart or recovery procedure
was introduced. The approval record now describes callable coverage as a source
review matrix rather than implying exhaustive execution.

All65task IDs, areas, order and statuses are preserved. No task is closed by a
wording correction. The [source audit](../system-adversarial-20261026/VERIFICATION.md)
retains its original241passes/3skips across244methods; its1,987scenario instances
are static review coverage. No Solidity/backend/website test suite was rerun for
unchanged implementation. [Documentation checks](validation.json) record actual
generation/reference/link/pin checks and their limits.

No source, ABI, economics, historical report, unrelated draft, website build or
server, installed service, test-chain state or journal was changed. Monitoring
remains paused. Git publication is separate from deployment; production remains
**NOT APPROVED**. Original documentation and dirty-file hashes are preserved in
the external `documentation-sync-20261026/before/` evidence directory under the
workspace evidence root recorded in the [handoff](../../docs/WORK_HANDOFF.md).
