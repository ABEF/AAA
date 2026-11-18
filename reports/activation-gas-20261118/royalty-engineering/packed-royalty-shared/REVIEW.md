# Final targeted packed-status size probe

This is the final requested isolated engineering variant, never adopted. One
private `_writeStatus(asset,mask,value)` shares all mapping read/modify/write
code. It replaces only the earlier experimental separate setter helpers and
redundant new cap guards. Every ORIGINAL monetary, cursor, eligibility, backing,
authorization and canonical arithmetic guard remains. Public getter wire ABIs
stay identical except argument names. BOUNDS_REVIEW.json enumerates every fixed
private callsite and proves values fit disjoint bit masks from original bounds.
No externally selected mask/value or authority is introduced.

The exact baseline633f015 closed100-source normal-codegen Royalty-only compile
has no errors but produces **24,723runtime bytes,147 over24,576**. Creation25,694.
It saves72bytes versus the first explicit-word variant and95 versus the struct,
but none meets size admission. VARIANT_COMPARISON.json preserves all three finite
one-compile stages. This output is not the full48-object normal graph admission.

STOPPED after this compile as requested. No EVM/component/whole-flow benchmark
ran and no gas savings are measured. All100 root sources and protected4 files
remain byte-stable; no existing node/service/signer/journal/heartbeat changes.
Private layout cannot be adopted through old raw storage/profile identities.
