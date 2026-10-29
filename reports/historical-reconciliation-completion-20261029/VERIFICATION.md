# Verification and evidence boundaries

Reviewed 2026-10-29. Source checkpoint `b266ef74e69bdf58264d53cbb2d4dcee28cc1b84`
plus the five Python source changes and two new test files pinned in
[CLI verification](CLI_VERIFICATION.json). [Review and findings](REVIEW.md).

| Check | Actual result and scope |
| --- | --- |
| New frontend CLI regressions | Four distinct methods pass; 77 invalid subcases reproduce pre-fix acceptance and reject after correction. One method includes valid finite Unicode controls. Constructors/listeners are mocked, not real services. [Receipt](frontend-cli-verification.json), [negative](frontend-cli-before.txt), [final](frontend-cli-after.txt). |
| Shared reader compatibility | Three existing methods pass: atomic roundtrip, explicit missing default and malformed-state failure. Default encoding is unchanged; frontend explicitly retains UTF-8. [Log](frontend-cli-state-compatibility.txt). |
| New indexer CLI regressions | Eight distinct methods pass, zero failures/errors/skips or run-time source drift. Duplicate/nested keys, nonfinite values, nonobject/missing/malformed inputs, injected recursion fault and valid/default behavior covered before resource creation. [Receipt](indexer-config-final.json), [negative](indexer-config-negative-before.log), [final](indexer-config-final.log). |
| Final source/evidence hashes | All final new-test/source and shared compatibility pins match. [CLI verification](CLI_VERIFICATION.json) and [copies](EVIDENCE_COPIES.json). Raw outputs remain external; published copies use LF and omit diagnostic trailing blanks, with both hashes retained. |
| Earlier local verifier changes | Prior 13 methods = 12 passes / one Windows symlink skip, retained at their [published source scope](../historical-reconciliation-20261029/VERIFICATION.md). No rerun, lab requests or financial journey here. |
| Unchanged Solidity/build | Exact 78 source/dependency plus four build-input pins still match build011. The 39 normal gates are **reused**, with no compile/EVM rerun. [Comparison](compiler-reuse.json). Manager initcode37-byte/Vault runtime59-byte margins remain limitations. |
| Historical static review | **Not applicable as a current pass:** 19 of 47 LF-normalized source pins changed; zero files missing. [Comparison](STATIC_APPLICABILITY.json). No new Slither run or independent review. |
| Reading/provenance QA | 352 original report narratives, 91 relevant current guides and two later checkpoint reports accounted; 235 overlapping finding groups. Exact historical/source anchors and preserved snapshots checked separately from execution. [Inventory](READING_INVENTORY.json), [findings](FINDINGS.json), [final QA](PROVENANCE_CHECK.json). |
| Generated docs and preservation | Todo/reference/current links and original-file preservation checked in [final consistency record](FINAL_CHECKS.json) and [preservation](PRESERVATION.json). These are documentation/tool checks, not extra passing Solidity/Python methods or public qualification. |

**New execution total: 15 distinct passing Python methods.** Negative attempts,
subcases, overlapping initial runs, hash checks and prior campaigns are not added
to this number. No full Python/Solidity suite, real DB/listener/provider, wallet,
public chain, keeper service or marketplace execution was performed.

Final domain QA records retain inspection-time hashes. Corrected final current
guide anchors are in the consolidated ledger; the original QA snapshots and
historical report identities remain unchanged. No original error/skip is erased.

Independent feeds/routes/VRF, authorities, OpenSea, accounting4 website/service
acceptance, target gas/economics, operating rehearsals, exact deployment size and
independent audit/remediation remain open. A complete historical reconciliation
does not assert that all historical risks are solved or production is approved.
