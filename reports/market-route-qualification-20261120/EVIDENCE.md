# Evidence reproduction

`evidence.zip` contains the exact six original capture directories and source
stages. `EVIDENCE_MANIFEST.json` records every member's SHA256 and the ZIP hash.
The original interrupted16-call state phase is intentionally retained. Extract
into a **new empty directory**; never overwrite a journal/configuration/database.

Run only the new offline checker from the matching repository checkout:

```text
python reports/market-route-qualification-20261120/tools/verify_capture.py NEW_EXTRACT_DIRECTORY NEW_VERIFICATION.json
```

It uses baseline Git blobs for the exact historical pool inventory/runtime
evidence and repository Keccak implementation; no untrusted RPC code is executed.
The new output path must not exist. There is no network, signer or chain write.
Recorded raw files, headers, current-source stages and original failures stay
immutable. Reconstructing the report does not select or approve a dependency.

The primary documentation index records URLs and interpretation, not frozen
HTML or signed-provider acceptance. Original dirty/current documents were
archived separately outside Git before editing; BASELINE.json binds their hashes.
No credential, key, keystore or operating configuration is packaged.

The recorder files are included for source transparency. Running them makes
fresh network observations and requires a separately chosen exclusive output;
it is unnecessary to reproduce this captured proof. The copied transport retains
its historical main routine and exact bytes; it is imported by the new drivers,
not used to relabel its old campaign or broaden a production work allowance.
