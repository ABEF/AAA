# Two-source static stage (before the reservation guard)

This immutable stage analyzes the accepted `normal-1` compiler input/output after only the Vault home-chain constructor and metadata bare-scheme checks. It does not include the subsequently authorized reservation guard. Its successful coverage must not qualify later source.

Actual offline Slither reused the exact compiler output, with no extra compilation. Analyzer JSON reports success and no analyzer error; the detector-present Windows exit is retained as `4294967295`, not described as exit zero. All tracked source bytes remain unchanged across this analyzer run.

All 571 detector records are covered: 65 individually current source/context assessments and 506 unique exact-fingerprint reuses with every description-referenced LF source unchanged. Current assessments include 63 false positives and 2 informational records. This is internal scoped review, not an independent audit or a claim that no exploit exists. Three detector text fingerprints differ from the immediately preceding review; each is reviewed explicitly, without broadening fingerprint normalization.

The complete raw output and its exact all-detector projection both pass the strict checker in-process. The full review contains all 571 records; the compressed input retains every exact detector classification/description and binds the raw analyzer and compiler digests. It omits supporting AST/element/compilation metadata only.

- [Full source-bound review](static-review.json)
- [Complete strict input projection](static-input.json.gz)
- [65 individual current-context assessments and source-delta proof](STATIC_REASSESSMENTS.json)
- [506 exact referenced-source reuse proofs](STATIC_REUSE_PROOF.json)
- [Counts, hashes and execution limits](STATIC_RESULT.json)

No default strict-review pointer was changed for this intermediate stage. A later final source stage requires its own accepted normal build, analyzer output and strict coverage. No tests, RPC calls, signing, deployment, sealing, live service or chain actions occur in this static stage.
