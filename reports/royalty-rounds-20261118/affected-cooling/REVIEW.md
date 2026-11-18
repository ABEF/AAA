# Current royalty cold-state fixture maintenance

`RoyaltyAudit20261105Test._coolLedger` no longer guesses the removed tree's raw
slot8/8192-node layout. Pinned Foundry `Vm.cool` marks the account and its storage
cold, while `_coolRecordedContracts` retains the actual recorded dependency-slot
cooling. No selected method body or production source was changed by this repair.

An authenticated minimal projection retains the exact seven relevant functions,
class fields, production sources and imported dependencies. The producer verifies
each selected function byte slice, pinned compiler/tool hashes, compiler metadata
source hashes, unchanged original sources/configuration and protected files.
Projection and source hashes are explicit in START/RESULT; this is not a run of
the other methods from the original large file.

Both affected methods passed: the full rotated cold standalone sync measured
124,096 gas, and the healthy single-currency activation measured329,257 gas.
These are component checks, not the 16-currency/1,000-NFT20M profile qualification.
The original 306MB trace remains outside Git, bound by its SHA256 and file size in
EVIDENCE.json. FORGE_COMPACT.json preserves exact method outcomes and decoded gas
logs; RESULT.json preserves the complete compiled-source proof.
