# Direct Entry3 verification

Reviewed3November2026. Base main revision
`8b8c6c3578f8deb7f9b76f2ff450ef8823410032`. This is selected offline evidence for
fresh source7/direct Entry3; no full-suite, published-CI, operating acceptance or
independent production approval. [Change review](REVIEW.md).

| Evidence | Result | Scope and limitation |
| --- | --- | --- |
| Normal compiler |43normal object gates pass;52 production+31 dependency sources |0.8.26/Cancun/viaIR/optimizer1/Yulfalse. No relaxed production-size limit. Dynamic constructor arguments still require qualification. |
| Entry EVM |20 distinct selected methods succeed across stages | Exact source/policy/owner/callback/cleanup/minimum/share/unsupported-ABI tests; synthetic pair and deterministic LP mock.19 successful unchanged bodies reused after one expectation correction. |
| Native core EVM |8 selected methods pass | Native activation/growth/value/failure/prefund and source admission; six virtual days and both same-block orderings with actual local Uniswap core/periphery, controlled feeds/assets/admission. No live keeper/browser/provider or target gas. |
| Python |314distinct selected methods pass:73+241;0failures/errors/skips | Explicit direct7-word codec, complete helper/version/runtime verifier, schema9 observer/validator and historical routing, plus operator/reference/static/source/publication-tool behavior. Not the full Python suite or actual tracing service. |
| Static analyzer |471records; strict source-bound coverage | Fresh analyzer execution,428 unchanged-context reviews reused,43 fresh contexts.73High/92Medium/209Low/76Info/21Optimization detector labels are not severity-confirmed exploits. |
| Callable reference |37contracts/818function rows/37constructors/13receivers | Generated from current closed compiler ABI; explanation/input/output notes retain separate checks. |
| Compiler applicability |83sources/1011implemented bodies/modifiers | New graph over current output; six-disclosure official snapshot reused from the immediately prior report. No applicable trigger established within documented assumptions; not a compiler proof. |

The EVM fixture code-size allowance applies only to test harnesses; normal
production-size evidence remains separate. The original20setup failures,19+1
assertion stage, empty selection and corrected retries remain in the external raw
archive. An exit-zero empty selection is **not** a test pass. No original failure
or historical report was overwritten, and counts are not accumulated across
repeated bodies. See [test stages](test-stages.json) and
[Python scopes](python-verification.json).

The original analyzer driver retained nonexistent task-local tool-metadata
pointers. [Execution](static-execution.json) explicitly discloses this;
[supplementary current installed metadata](static-tool-provenance.json) is a later
offline observation, not fabricated earlier evidence. Exact source/compiler/output
and analyzer report/log hashes remain captured. Slither's findings exit is retained;
its JSON reports analyzer success, not a clean no-findings exit.

[Normal gates](production-size-gates.json), [size comparison](size-comparison.json),
[static review](static-review.json), [coverage](static-coverage.json),
[compiler applicability](compiler-assessment.json) and the final
[verification record](verification.json) carry source/result hashes and checks.
The final record separately checks generated Todo/reference, current links,
publication closure and preservation. Source publication is separate from any
website rollout, service change, deployment, sealing or public transaction.

Raw evidence/archive root (outside Git):
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/direct-entry-v3-20261103`.
It includes the original585 current files,2678 pre-existing report hashes,
normal compiler input/output and all test/analyzer attempts. Four unrelated dirty
tracked files remain excluded from publication. Existing Anvil8902, sites,
services, journals, signer restrictions and the paused heartbeat remain unchanged.

No external feed/route/VRF/authority/OpenSea or live-service gate is closed by
these local results. Migration runtime has20bytes headroom; further source edits
require new exact-source size/static assessment.
