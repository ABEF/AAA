# Factory storage and claim planning: scoped implementation

Baseline main `4f7436adf35130aa37256804283a9070b5bf83bd`,5November2026.
This implements the selected deployment-gas and unsigned-claim improvements.
It does not authorize deployment, public signing, service/site rollout, backups
work, Anvil/journal changes or resuming the paused heartbeat.

1. Preserve RoyaltyRewards creation bytes and all settlement4/recovery2/V8
   accounting, economics, current-owner rights and original currencies.
2. Replace Factory's storage-slot payload with exactly two fixed immutable
   inert code-data children. Independently verify part/whole bytes and actual
   constructor-returned runtime/initcode limits, not the compiler placeholder.
3. Introduce explicit inventory14; retain13 and earlier as historical inspection.
   Authenticate both inert addresses outside the18 callable-helper roles.
   Never obtain approved hashes from the provider being checked.
4. Add opt-in typed claim planning: explicit bounded selection, shared work
   budgets, next-batch simulation, original raw denominations, retained zero/
   blocked/unresolved entries and no transaction queue/signing/autoresend.
   Keep prepare,32 operations,12M and existing fee limits unchanged.
5. Verify changed behavior with focused tamper, integration, controlled gas,
   batching/failure/canonicality and configuration checks. Reuse only exact
   unchanged scope; independently review current static contexts.
6. Update central Todo/features/operator/reference/memory and publish main
   only after preservation, source/publication closure and documentation checks.

The fixed format uses `PUSH0/PUSH0/REVERT`, rather than a STOP-only carrier, so
ordinary calls/native sends fail. EVM forced ETH/ERC20 transfers remain possible;
these unsolicited child balances are outside protocol accounting. Factory
remains typed CREATE, with no mutable code, generic executor, delegatecall,
caller salt or arbitrary recipient. No canonical wire change is necessary.

Evidence must distinguish local inner-CREATE gas from an actual wallet receipt,
bounded fixture planning from target-provider acceptance, and20 current static
contexts from exact referenced-source reuse. Production remains NOT APPROVED.
