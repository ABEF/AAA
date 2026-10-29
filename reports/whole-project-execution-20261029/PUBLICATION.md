# Publication and final consistency

Both repositories use **main**. Exact content and remote heads were verified:

| Repository | Published source commit | Scope |
| --- | --- | --- |
| ABEF/AAA | [3398be6](https://github.com/ABEF/AAA/commit/3398be63654c00f4079c7a23519797c3efa7f621) |133allowlisted candidate/source/test/report/document files, including the previously saved reviewed confirmation2/emergency1 work. |
| ABEF/AAA-website | [cae44a1](https://github.com/ABEF/AAA-website/commit/cae44a1d69a6dcec42403de922ff45fadfc47705) |2790allowlisted generator/preview/reference/test/context files. No image/manifest/signer/config/build change. |

This publication record and final formatting/consistency receipts are a separate
documentation follow-up. No later implementation or fresh test pass is implied.
Original four unrelated dirty files remain excluded and byte-identical; all
2247previously tracked report files retain their bytes. Normal staged whitespace,
Todo/source-bound callable generation, Python/JSON syntax and1683relative links
pass. [Documentation receipt](documentation-checks.json) retains its scope.

The first publication check identified one extra EOF blank line in an unpublished
Python fixture and CRLF whitespace in the new JavaScript test. Formatting was
corrected without gate relaxation or executable changes. The [tested website
snapshot](website-changes-tested.json) is retained separately from the
[published-format snapshot](website-changes.json); no fresh test rerun is claimed.
The publication helper was changed to one batched Git-object read rather than
launching a separate process for each of2784metadata files. Every staged blob
was compared to the exact reviewed bytes before commit.

No website build/rollout, server/service/heartbeat, old Anvil/NFT/LP/balance/journal,
signer, public transaction/deployment or sealing changed. popldemo and poplint
remain distinct and unchanged on their servers. Public signing remains disabled.
**Production NOT APPROVED:** live dependencies, operations and independent audit
remain open in the sole Todo. Git publication grants no deployment permission.
