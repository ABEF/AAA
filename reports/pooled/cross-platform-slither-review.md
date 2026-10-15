# Internal review of cross-platform Slither fingerprints

The Windows and Ubuntu artifacts each contain **139 unique findings**. Before normalization, exactly four descriptions differ solely in the order of five nested `_unwind` external callees. With the final narrow normalization, all 139 fingerprints match and both coverage gates pass.

The implementation sorts only contiguous two-tab callee leaf lists inside `External calls:` sections of reentrancy findings. It preserves duplicate leaves, parent groups, root call order, deeper child nodes, state-write lists, expressions, source locations, detector identity, severity and confidence. No detector/finding suppression or source guard bypass was identified.

All **15 gate regression tests passed**. Independent mutated-input checks also rejected duplicate/removed findings, changed severity/confidence, analyzer failure, source-hash/inventory drift, missing rationale and unresolved dispositions. The JSON companion binds both raw outputs, the reviewed checker/tests and the four changed raw IDs.

This is an internal secondary review, not an independent external audit. The reviewer did not edit Solidity source or the primary gate files.
