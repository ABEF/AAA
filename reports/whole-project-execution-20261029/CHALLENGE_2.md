# Second challenge: independent factual/adversarial verification

Reviewer independently read all draft2, understanding, challenge1 and current
AST/reference inventory and rechecked actual cap/readiness/Entry/Vault/Budget/
Manager/indexer/history code plus official Ethereum JSON-RPC specifications.
Draft2 SHA2560163e0744b29aef46154a1c8407ce9fa0aa30441e72c74d01d5c05c9ddf0c8ba.

Required changes, all applied to final:
1. Filtered eth_getLogs numeric gaps are valid; require transaction grouping and
   consistent supplied index/hash identity, not gapless indices. Test valid gaps.
2. Public signing disabled; browser signing Anvil-only, distinct public/local.
3.1mUSD is intended governed maxPositionUSD configuration, not hard source cap.
4. gap0 stops sampled ordinary readiness; deliberate manual width exception
   still applies after cooldown. Do not erase that exception in prose.
5.122unannotated output positions/nested tuple semantics remain specific work;
   some meanings are already in purpose notes, others must not be invented.
6.742ABI entries are not all implementation bodies. Include private/internal
   functions/modifiers/overrides/libraries/reachable inherited dispatch, and
   distinguish unreferenced dependency package code from reachable behavior.

Confirmed appropriate after correction: fresh2/emergency1 boundaries; explicit
governance trust without accidental privilege leakage; timing/price/loss/idle/
custody separation; cross-callback ownership/claims/fractions and canonical
funding/abort; exact-source evidence reuse, narrow negative controls, external
qualification and source/publication/rollout authorization kept separate.
No first challenge conclusion was accepted without source checking. No code
policy or deployment was changed by revising the prompt. Both critiques and
input/final hashes are retained separately.
