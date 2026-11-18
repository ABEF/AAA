# Actual post-adoption build producer

`compile_current.py` is prepared and syntax-checked but **has not executed**.
It requires `--actual` and does not modify production source files. The original
`compile_proposed.py`, proposed input/output, reports, hashes and timestamps stay
unchanged; all original `ARTIFACTS.json` entries still match.

Run it only after the valid old-source baseline is captured, the exact proposed
library is explicitly adopted and Foundry's temporary file-permission overlay is
restored. Its four positional inputs are the pinned compiler, trusted previous
normal-build directory, size08 virtual compiler input and a new exclusive output
directory. The intended output directory is externally owned
`q03-activation-gas-20261117/build/adopted01`; its sibling `proposed01` must retain
the preparation's exact uncompressed compiler input/output.

The actual producer then:

1. Verifies the pinned compiler and closed100-source trusted template.
2. Permits exactly the expected allocator change from that template, and requires
   all100 raw filesystem contents to equal the final prepared input exactly.
3. Checks that this actual compiler input is byte-identical to `proposed01`.
4. Inspects the restored effective normal Forge profile without compiling or
   running tests through Forge. An unreviewed file-permission overlay is rejected.
5. Runs a fresh native-solc normal compilation, preserving the original48 gates.
6. Requires the actual output to be byte-identical to the proposed output and
   all100 sources, compiler and four build inputs to stay unchanged during it.
7. Records truthful legacy `source_sha256`, `build_input_sha256`,
   `unchanged_before_build` and `unchanged_during_build` fields for this actual
   stage. Those fields are never retroactively added to the proposed stage.

This deliberate second compiler execution establishes the actual adopted
filesystem/configuration stage; it is not an old test rerun or an admission-rule
relaxation. Existing function-reference and trusted-build checks remain intact.
The compilation still does not approve deployment, markets, fees, operating
services or any signing action.
