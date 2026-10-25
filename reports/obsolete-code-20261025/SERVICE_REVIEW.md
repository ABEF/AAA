# Service and operator cleanup

This internal review traces current imports, CLI paths, configuration consumers
and operator instructions. It is not provider qualification or an independent
audit. No chain, wallet, service, deployment or website was operated.

## Removed and corrected

1. **Creator-payment measurement was orphaned.** `zzz_ops/revenue_share.py` had
   no current production imports or service callers. Only its own retired test
   module and documentation invoked it. Its 429 source lines and 312 test lines
   are archived as exact historical text. Current revenue comes from physical
   local LP collections, not an invoice calculated for the former Pons creator.
   Active component/feature/navigation rows and operator funding instructions
   were removed; the stable guide URL now explains the retirement.
2. **The shipped keeper example selected the old architecture.** Missing explicit
   accounting/intake versions defaulted to V1/profile0, while creator sync was
   enabled. The current example explicitly uses accounting2/intake1 and omits
   retired jobs. Separate example state paths reduce accidental journal reuse;
   runtime guards still reject profile changes to an existing journal. Actual
   runtime pins and live approval remain unset. Compounding, conversions and
   adaptive range control remain disabled until reviewed configuration exists.
3. **Current prose still advertised stablecoin inputs and creator invoices.**
   The owned component/operator/feature text now uses ETH/fixed-ZZZ contributions
   and actual LP receipts, with separate marketplace royalty accounting. Nothing
   in this cleanup changes royalty-currency admission or reward rights.

The [archive receipt](retired-tools/retirement.json) identifies original bytes.
The central feature/Todo and remaining source cleanup are maintained by the main
review; old source-bound reports keep their original meanings.

## Deliberately retained

- Keeper historical fee0 synchronization and saved-pending recovery: old deployments
  and journals remain valid historical profiles; current fee1 rejects those jobs.
- Historical module IDs, event decoders and predecessor earnings history: dropping
  these would corrupt reporting or recovery rather than simplify current custody.
- Converter wrapper policies and observation: actual LP/royalty v3 conversion
  still validates and unwraps an independently pinned wrapper. This is distinct
  from the unused Registry wrapper-review record removed by the contract review.
- `scripts/verify-robinhood-integration.py`: explicitly labelled historical,
  read-only reproduction of old Pons evidence. Current selected-pool observation
  uses `scripts/verify-hookless-pool.py`.
- Older unrelated dirty routing/recovery research is preserved, not included in
  the creator-tool removal simply because it mentions USDC or an external bridge.

## Verification

[Three focused keeper-example methods](keeper-example-verification.json) passed
once against the actual Keeper constructor and mock RPC: explicit current profile
selection, missing review/runtime pins failing closed, and rejection of a
reintroduced creator-sync job before RPC. These do not qualify a real provider,
key, chain, deployment or operating service. Unchanged broader keeper/history
tests were not rerun. Retired creator-measurement tests are not counted as passes.
