# Verification scope

Baseline: `aaf1423189e1f8436418540ef7cf85cbbccc9e29`; the archived module is
byte-equal to Git. [ROOT_REVIEW.json](ROOT_REVIEW.json) records exact current
source/test and preserved-source identities.

| Stage | Actual result and scope |
| --- | --- |
| Initial baseline test shape | [Raw log](baseline-new-tests.log) retained; earlier19-method shape, not current candidate acceptance. |
| Earlier post-edit shape | [Raw log](first-post-tests.log) retained;19 new methods passed at that earlier source. Overlaps later27 and is not added to their count. |
| Final27 against archived baseline | [JSON](baseline-final27.json), [log](baseline-final27.log):27methods,29 failing subtest assertions and9errors,0skips. Demonstrates missing diagnostics; not38distinct defects. |
| Accepted27-method source stage | [JSON](post-fix-final27.json), [log](post-fix-final27.log):27methods pass,0failures/errors/skips, source/test unchanged across execution. Original scope retained. |
| Fallback-only final delta | [Before](preparation-fallback-final-before.json)/[log](preparation-fallback-final-before.log):1new method fails on the742source; [after](preparation-fallback-post.json)/[log](preparation-fallback-post.log):1passes on9c139431,0skips/errors. [Scoped AST proof](preparation-fallback-scoped-reuse.json) and [exact patch](preparation-fallback.source.patch): earlier27/helper/preparation bodies unchanged.28unique new methods; no unchanged27 rerun. |
| Compatibility comparison | [Record](artifact-and-ordered-read-equivalence.json): five full artifacts and ordered RPC traces identical;12 negative traces retain base error type/order. No old test method executed. |

Tests cover known local input/configuration/auth/lifecycle/geometry/custody,
gas/fee/funding, initial/final simulation and canonicality/expiry errors; opaque
failure preservation; metadata spoofing/hostile getters/unhashable attributes/
huge or boolean codes; existing/dangling output paths; render, temporary fsync,
hard-link/cleanup and actual final-stdout failure. Complete-file preservation and
no transaction submission are checked. These are finite injected/temporary-file
cases, not EVM, provider, target-fee/gas, Unix durability or operating qualification.

Full baseline/current artifact and ordered transport bytes are retained in the
external evidence directory named in the root record; their hashes are in the
comparison record. Historical source fixtures/rights are not relabelled.

Root mechanical checks cover Todo, new links, unchanged generated references,
source/guard constants, shared writer AST, all61 Solidity and100 normal source
bytes, current strict-source pins, protected local files and exact published
Python closure. [Completion](COMPLETION.json) records those checks. Inventory
selection executes0methods and is never added to test coverage.

Raw logs preserve original bytes. Source/document whitespace checks recognize
existing CRLF line endings and exclude raw evidence logs and the exact evidence patch. No signer, public
RPC, secret, service/site change, chain reset, journal edit or heartbeat resume
was used. Static publication checks are performed on the exact intended index
and committed HEAD; external proofs avoid self-referential report hashes.
