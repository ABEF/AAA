# Isolated keeper restart from a reconstructed recovery kit

Baseline `d6e8a909fd2b2a12eb1bee15173e92d526178cdb`,27 November2026.
This closes a missing composition, not the entire keeper operating qualification.

## Evidence-based adjustment

The c814/c822 records prove actual accepted local transactions and unsigned
recovery separately. The inspected c814 driver loads the earlier F6 base and
does not save a post-transaction chain snapshot. Its canonical receipt JSON
alone cannot recreate a live node containing that transaction; its old head
also fails the unchanged real-clock freshness rule. Do not resend that old
transaction, relabel historical receipts or replace a real node with canned RPC.

Use one new disposable local keeper harvest, submitted once by the stock keeper
against an isolated node loaded from the reviewed immutable F6 base. Necessary
fixture preparation separately refreshes four mock-feed timestamps and authorizes
the new disposable keeper: five planned local governance calls, each simulated
before submission and required to succeed.
Two local balance-funding calls and bounded impersonation apply only to that
synthetic fixture. These are not six keeper submissions or production actions.
No old test or scenario body, contract construction, public transaction,
deployment or sealing is needed. The recovery phase is strictly unsigned.

## Prepared scope and gates

1. Archive current docs, retain independently reviewed source/runtime/input pins
   and record existing host states. Preserve four unrelated dirty files.
2. Review a new bounded lab driver and its dependency closure before execution.
   Require exact current production source bytes and all JSON/runtime resources.
   Use reviewed F6 fixture inputs only; production pool/source qualification
   cannot be inferred from synthetic depth or the copied local graph.
3. Run Anvil in its own separately supervised group. Use one fresh disposable
   keeper setup sender and original pending publication, never the user's keys.
   Keep signer files outside all recovery kits. Preserve 240-second scheduling,
   twelve confirmations, hourly harvest and all gas/fee/RPC/resource safeguards.
4. Fence the setup keeper and every owned restart path. Capture the exact
   accepted-hash journal using the native backup tool, exact original config,
   matching release and independently retained trust. Download to protected
   private desktop storage; rehash actual saved bytes before return. First mine
   the accepted transaction and twelve confirmations within its actual180-second
   harvest deadline, before the desktop round-trip. Keep the isolated node running
   separately throughout; this does not test chain-node reconstruction. Ordinary
   empty blocks may refresh a genuinely stale head using real current time.
5. Reconstruct fresh Ubuntu application paths from those desktop-held files.
   Keep old application folders unavailable; enumerate required read-only OS
   runtime dependencies. Make configured signer files absent/unreadable. Use
   separate new state/health/lock paths only through the reviewed recovery
   mapping; do not hand-edit the journal, nonce, spending, source or captured time.
6. Run the actual stock keeper once without `--live`. Require recovery of the
   original hash, exact canonical receipt/fee/day/nonce/anchor accounting and
   zero new submission attempts. Run one unsigned dry cycle; pending/accounting
   must not settle or charge twice. Do not pretend recovery authorizes signing.
7. Before stopping the isolated chain, take independent final on-chain reads
   and compare principal, NFT rights and classified rewards/reserves. Record
   counters, original-file preservation, source/inode/root separation and new
   locks. Capture diagnostics even when a late assertion fails.
8. Stop all new groups and verify existing services, journals, sites and
   Anvil8902 remain unchanged. Publish only explicitly sanitized evidence.

The desktop heartbeat stays user-paused. Raw configuration, journal, package,
RPC captures and signer material remain outside Git; signer material stays
separate from application recovery inputs. Existing native formats/defaults
and financial/resource limits cannot be raised to make the rehearsal pass.
An interruption resumes saved status/cleanup/export only, not the scenario.

## Completion and limits

Require the new clean-root stock-daemon composition and independently reconciled
saved evidence; unchanged earlier tests are reused rather than rerun. Update the
Todo, operator guide, findings, roadmap and repository handoff with actual results,
including original refusals and any uncompleted partition.

This is one existing-host laboratory composition. Physical second-host/OS
recovery, cross-host/compromised-key fencing, current production canonical truth,
real provider/channel/host-down monitoring, durability and sustained operation
remain separate. No live service/source/checkpoint or website adoption follows.
