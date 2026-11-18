# Prepared closed normal build

All100 sources compile, and all48 unchanged runtime/initcode gates pass. All48
host ABIs remain identical. Semantic storage comparison finds only the private
royalty book's checked outstanding counter, while retaining its mapping offset.

This build was deliberately prepared **before source adoption**. `START.json`
records the actual old source hashes and the different proposed library content.
No source file was changed during compilation. Adoption must separately verify
that the exact proposed UTF8/LF bytes and every other input now match the compiled
input. Do not rewrite this preparation's timestamps or claim that adoption had
already occurred.

| Object | Runtime | Runtime margin | Creation plus minimum arguments |
| --- | ---: | ---: | ---: |
| Royalty |24545|31|25575|
| Access |10854|13722|48398|
| NFT |24234|342|31052 minimum; dynamic string requires exact review|
| Vault |24544|32|26083|
| Oracle |24573|3|49073|

The two inert royalty carriers have runtime lengths24576 and973 bytes. They are
derived from the actual newly compiled25543-byte creation payload; no deployment
or adopted address is implied. `ROYALTY_CARRIER_EVIDENCE.json` records exact hashes.

`compiler-input.json.gz` and `compiler-output.json.gz` retain the complete input,
ASTs, metadata, bytecode and layouts. `normal-size-evidence.json` records all48
gates, exact100-source closure, compiler identity and honest actual/proposed flags.
`ABI_STORAGE_COMPARISON.json` includes normalized semantic layouts; AST IDs are
excluded from semantic comparisons. The scoped manual review is in
`SCOPED_STATIC_REVIEW.md`; it is not a new full static-analyzer run.

No test, source adoption, signature, deployment, seal, service, website, chain,
existing database/journal or paused heartbeat action is performed by this build.
Actual gas/markets/configuration/operations and independent approval stay open.
