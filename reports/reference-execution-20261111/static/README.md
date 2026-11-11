# Source-scoped static review

Actual offline Slither0.11.6/crytic-compile0.4.2 analyzed the final closed normal
compiler output `normal-final-a8460b24d0`:61 Solidity source files plus the three
reviewed build/analyzer configuration inputs. No compiler, RPC, wallet, existing
Anvil or operating service was invoked by this analysis. The before/after source
bracket is identical. Analyzer JSON reports success; its nonzero Windows process
exit represents reported findings, rather than an analyzer failure.

The strict current record contains567 unique findings:162 individually reassessed
current contexts and405 unique exact prior fingerprints whose description-referenced
source bytes remain identical. The latter preserve their original transitive and
acceptance limits; they are not a fresh audit of all changed callees. Current
contexts include transient context encoding/clearing, bounded proof reads, exact
quote transitions, callback conservation, controls, both physical LP legs and
the extracted read-only arithmetic. The record has83 false-positive,48
informational and31 accepted-risk current decisions. This is internal triage,
not independent audit or an exploit-absence guarantee.

`check-slither-review.py` selects the matching full record. Its strict check and
44 checker regression tests pass. Source publication and passing normal size or
detector coverage do not establish market/provider/VRF/OpenSea/operating approval.
In particular, the complete cold ETH/ZZZ Entry operations still cost approximately
15.3M/15.6M gas and fail the unchanged12M policy. No financial safeguard or gas
limit was weakened to close that blocker.

`current-162.json` preserves every exact current description/fingerprint and its
individual decision. `exact-reuse.json` records reuse provenance. Compressed raw
analyzer/detector output, original execution logs, source pins and artifact hashes
are retained. The earlier whole-project/spot-reader records keep their original
source scope and are not relabeled as this result.
