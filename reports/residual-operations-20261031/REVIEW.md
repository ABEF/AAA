# Residual LP management controls

Local source follow-up,31October2026; production NOT APPROVED. The user requested
independent residual closure, forced consolidation, enable/disable controls and
complete long-term operating procedures. Existing source and prior dirty work
were inspected and archived before changes. No deployment/service/site/Anvil,
transaction journal, public signer or heartbeat was changed.

## Existing controls and missing operation

Both positions use the same ETH/ZZZ pool. Existing PortfolioPolicy.setMode
enables/disables future residual creation; it does not trade immediately.
Migration.emergencyRebalance already closes the whole portfolio and creates
one main, with explicit paused governance authority and selected retained guards.
Its token ratio is the concentrated range's actual required ratio, not necessarily
50/50USD. Setting modefalse first makes the desired future strategy single.

The missing operation was independently closing only the residual without
replacing the main. New Migration.closeResidual(ParkingRequest) requires current
governance, sealed/paused/preparation-free operation, pre-terminal lifecycle,
reviewed custody identity, shared parking nonce/epoch, short deadline and raw
minimum principal receipts. Vault harvests both legs before burning only the
registered residual; actual receipts become that same bucket's attributed idle.
There is no swap, external recipient, holder payout or compound release.

Both before/after main physical/accounting fingerprints preserve its owner,
key, packed ticks, liquidity, share supply, deposits, centre and clock, plus
Registry/policy controls. Raw receipts, pause and nonce/epoch are checked again.
The same transaction atomically reverts collection, reserves, burn, approval,
proceeds and review counters if a final guard fails.

The desired mode remains unchanged; callers can disable it first for persistent
single-position behavior or leave it enabled for a later guarded re-creation.
Already-enabled geometry can be explicitly re-reviewed using the existing
same-value configureResidualSide setter, without an artificial mode toggle.
Large attributed idle is deliberate recovery state; normal entrant/deployment
guards are not relaxed. Both-leg parking and terminal holder return remain
separate fallbacks if reinvestment is unavailable.

## Size-safe changes

The typed operation is Vault→Manager→fixed position child. Each exposes the
explicit RESIDUAL_EXIT_VERSION1 capability; existing accounting5/custody4 wires
are unchanged. No arbitrary executor or new authority was added.

An initial measured implementation exceeded Vault/Budget runtime limits.
Identical pre/post terminal checks were deduplicated through a private base
helper. Holder-exit read validation was moved through the existing fixed
Budget/Canonical boundary with unchanged caller, errors and check order.
These are behavior-preserving extractions, not relaxed guards or a delegatecall.
Final normal42size gates pass; Vault runtime23671 leaves905bytes, Budget24290
leaves286. Exact target deployment arguments/gas remain unqualified.

## Verification and remaining boundary

See [verification](VERIFICATION.md) for actual completed checks and retained
failures. The [management guide](../../docs/PORTFOLIO_OPERATIONS.md) gives the
wallet/function matrix, request inputs, emergency procedure, failed receipts,
same-mode reapplication, idle recovery and restart requirements.

Actual token/venue/provider authenticity, target gas, market manipulation,
current-service/site operation and independent audit remain release work.
A broken token or venue can prevent closing; a reviewed emergency swap can lose
principal when financial guards are deliberately bypassed. Enabling residual
mode is not immediate creation or permission to bypass ordinary timing guards.
Source changes remain local/uncommitted and do not update older deployments.
