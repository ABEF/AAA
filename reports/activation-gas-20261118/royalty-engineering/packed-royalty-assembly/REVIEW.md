# Shared assembly packed-status feasibility

The final explicitly requested isolated probe replaces shared Solidity mapping
reads/RMW with shared memory-safe scratch helpers. Both clean the address key to
160bits, place the canonical mapping slot at scratch32, hash scratch0..63 and
use that exact key for SLOAD/SSTORE. No free-memory pointer or external call is
introduced. Fixed caller masks and valid-value bounds remain as proven in
BOUNDS_REVIEW.json. Only earlier experimental redundant caps were omitted;
all original arithmetic/backing/authority/canonical guards and prefund row order
remain. Scalar getter wire ABIs match except original unnamed input labels.

One exact baseline633f015 closed100-source normal-codegen Royalty-only compile
produces **24,714runtime bytes,138 over24,576**. Creation25,685. This is9bytes
smaller than the shared Solidity helper; it still fails admission. The prior
three candidate stages remain immutable, and VARIANT_COMPARISON.json makes all
four finite size probes explicit. This is not full normal-graph validation.

STOPPED. No further iteration, EVM/component benchmark or gas replay ran. No
savings are measured, no source/profile is adopted, and all100 root source bytes
and four protected files stayed unchanged. No existing node/service/signer,
website/journal or paused heartbeat was touched. Private raw layout is incompatible.
