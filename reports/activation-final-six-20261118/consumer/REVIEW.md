# Payload6 consumer verification

The fresh schema17 template explicitly selects payload6, generated from the
admitted `activation-final-six-20261118/build/final02` normal compilation. Its
Royalty creation is25,533bytes and hashes to
`0xbb0f8ce9cf2c332313c08da26f70174276182fd2202e7b308d4352525207c9e4`.
FORMAT2 remains unchanged: two revert-prefixed data children have runtime lengths
24,576 and963bytes. Source pins are not deployment observations or approval.

The old payload5 helper and JSON retain their exact original hashes. The prior
fresh production template is preserved byte-identically as
`config/production.schema17.payload5.example.json`. Explicit3,4and5 retain their
separate identities. Payload6 cannot consume their data or runtime parts, and
historical payloads cannot consume payload6. Omission still selects historical3.

The production gate and read-only observer apply the existing bounded royalty
read policy only to explicit5or6. The cap bounds, fingerprint domain, source
identities,50000gas default, remaining gas/default policies and financial guards
are unchanged. The shared policy/pre-seal wording now names5/6. The fresh template
retains null deployment/runtime observations, null read-cap observations and all
unverified operating/release status. The unsigned pre-seal planner leaves unknown
inputs and calldata blocked; no sealing or signing is prepared.

## Executed controls and correction

Seven NEW methods verify the fresh normal100-source/48-gate graph and corrupted
source pins; actual source-owned payload/parts; historical F5 identity and
current-preparation rejection; explicit/unknown/mixed profiles; same-anchor
bounded observations and fault isolation; unknown/unapproved template and
blocked pre-seal inputs/read ABIs; and malformed or mutated artifact rejection.

Five affected historical methods retain earlier assertions with explicit
archived inputs: three activation-build methods and two F5 loader/selector
methods. The live corrupted-source assertion moves into the new current-build
method. Historical loaders authenticate every accepted file and complete input
closure without pretending an old archive matches today's filesystem. Current
deployment preparation still requires current source identity.

The first selection in `final01` exposed a new fixture error. It used the
integer-only transaction-input decoder on an already hash-authenticated build
report that legitimately contains fractional elapsed seconds. Two methods
executed: the selector control passed and the archive-dependent method errored;
two classes failed setup before executing their methods. Raw failure output and
its explanation are retained. The correction permits informational report times
while preserving duplicate-key/nonfinite rejection, exact file hashes and the
unchanged integer-only production decoder.

Only the eleven archive-dependent/new methods executed in `final02`.
All eleven pass with a stable source bracket. The already-passing selector
control was not repeated. Across those two source stages,12distinct methods have
passing evidence:7new and5affected. There were13adopted method executions, not13
distinct tests; class-setup errors are separate. The initial runner scope string
miscounted the new class; `final02/METHOD_COUNT_CORRECTION.json` preserves that
correction beside the authoritative raw unittest output.

A separate workflow-only unbound-pin control executed once in `final03` and
passed, but is not adopted or counted as current product coverage: published
F6 pins are constant, and the hypothetical ungenerated state is preparation
workflow rather than a new current-runtime risk. Its source and raw evidence
are retained as discarded engineering evidence. No unchanged Solidity/browser/
backend suite was executed.

## Boundary

These are offline source/artifact checks and injected read-only RPC responses,
not actual provider, wallet, target-fee, market, operating or independent release
acceptance. No public requests/transactions, deployment, sealing, live service,
site, existing chain or journal was changed. The root agent owns the separate
normal build, whole-flow gas qualification and deployment registry adoption.

Exact generated hashes are in `GENERATED_PINS.json`; per-stage source hashes,
commands and results remain in `final01` and `final02`. Historical reports keep
their original source scope.
