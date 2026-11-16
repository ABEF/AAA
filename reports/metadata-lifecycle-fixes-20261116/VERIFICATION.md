# Metadata lifecycle2 verification and limits

Baseline: `dd242634b7dc4d3ead6d66f8a42c857da587cf15`, reviewed16November2026.
This is scoped internal verification, not production approval, a full regression
suite or actual OpenSea/provider/operating qualification.

## Executed checks

| Evidence | Scope and result |
| --- | --- |
| Solidity snapshots | 18new methods: schema2 state/flags/context, ownership/binding, canonical/preparation/successor, terminal Dormant, allocation/readiness/paid/zero, unavailable values and price-free fingerprints. Controlled dependency snapshots, not real markets. |
| Solidity notifications | 10new methods: five real Access/NFT authority/transition checks plus five actual Vault/NFT/Migration exit/allocation/current-owner/payment checks. Explicit controlled1:1 venue/feed/VRF fixture, not Uniswap market qualification. Successful/failed payout isolation and royalty rights remain covered. |
| Actual tokenURI composition | Included in those10, not another method: exit begins, bucket closes, allocation becomes Ready, NFT transfers, actual ETH+ZZZ principal pays the current owner, metadata becomes paid and royalty activation remains. |
| Renderer differential | Two new methods,110bounded internal cases, comparing accepted historical compiled renderer with current pure preview across traits, stages, availability/unrevealed and escaped URI inputs. Original image/name/value/attribute fields/order/count remain; corrected description is intentionally different. These are not110test methods or all2784media retrievals. |
| Adapted outage fixture | One existing NFTMetadata outage/royalty method selected because its fixture now binds the real fixed NFTCanonical lifecycle companion. No other old NFTMetadata method runs. |
| Keeper | 15distinct new mocked methods pass across explicitly retained source stages. Eight initial successes are reused for unchanged paths; five failing identity/recovery methods pass after the helper correction; one corrupt-identity case and one exact stored-integer case pass at their separate source stages. No unchanged keeper suite/actual service/RPC run. |
| Website | 13new Node checks pass on source hash `89c348cd3895ffd997d677f441fa10aa57a941e6e172763bd094b0a028af29fe`: unavailable fallback, terminal/dormant labels, principal payment states and target-only pending-artwork preservation. No unchanged browser suite, actual wallet or hosted rollout. |

Unique Solidity coverage is **30new +1explicitly adapted methods**. Repeated
invocations caused by changed failed fixtures/helpers retain their exact source
stages and do not increase this count. Five successful controller methods were
not rerun when correcting only the exit fixture. Exact selection excludes all
old methods inherited by the new notification host.

## Failed stages and harness corrections retained

- Initial normal compilation found a Yul stack issue; subsequent normal builds
  detected excessive renderer size. Original compiler settings/limits stayed.
  Shared serialization and read-only context in the existing NFT companion
  produce the accepted sixth normal build.
- Initial combined test compilation exhausted the native compiler stack and
  executed0methods. Split groups isolate the source/harness workload.
- One new method name beginning `testFailed` triggered Foundry's removed
  `testFail` naming convention at discovery; it was renamed, without weakening
  an assertion or executing old tests.
- The historical renderer bytecode initially overwhelmed inline test compilation.
  An intermediate artifact-loading setup demonstrated the differential checks
  but needed manual artifact placement. The maintained final harness instead
  uses linked public **test-only** bytecode chunks, no extra filesystem permission
  or manually staged artifact. The same accepted creation hash is checked before
  CREATE; this is not a new production helper/artifact.
- Five exit checks initially stopped during activation setup: inherited legacy
  mocked venue lacked current `executionStrategy().fixedZZZ()` and validated-price
  read methods. New notification fixtures explicitly supply those existing
  controlled1:1 read seams. Actual metadata/Access/Vault/Migration and allocation,
  current-owner transfers, accounting and payout checks remain real. Production
  code and safeguards were not changed to accommodate a mock.
- New keeper checks exposed helper-name shadowing and malformed stored version
  typing; corrected paths alone were rerun. The browser fallback checks exposed
  missing-last-confirmed-art handling for a pending LP target; its dedicated
  confirmation gate was retained and tested.

No old test failure is erased or relabelled as a pass. These findings do not
establish an all-green historical/full suite or published CI run.

## Normal compiler and size gates

The accepted build uses the exact pinned Solidity0.8.26/Cancun, viaIR,
optimizer-runs1/Yul-disabled profile and closed100-source input:61production plus
39dependencies. All48normal runtime/initcode gates pass. No compiler flag,
deployment limit, gas budget or financial protection is raised.

| Object | Runtime bytes | Runtime headroom |
| --- | ---: | ---: |
| NFTMetadata | 24,121 | 455 |
| NFTCanonical | 23,130 | 1,446 |
| NFT | 24,234 | 342 |
| Migration | 24,005 | 571 |
| Oracle | 24,573 | 3 |
| Vault | 24,544 | 32 |

Access creation is48,017bytes plus96static constructor argument bytes. Exact
future constructors/arguments and provider/market/read/payout/deployment gas
still require separate release qualification. Test-host artifacts are not exact
production deployment pins; use the accepted normal compiler family.
Final normal output SHA256:
`e3cbd59c818873e2adf766eecc7866c4b2530ac280d3b07f9c00640a6db4da0a`.

## Static and mechanical closure

Slither consumes the accepted output without recompilation:569records,
57individually reviewed current contexts plus512unique exact
fingerprint/referenced-source reuses from the prior565review. Every current
source/config pin is rebound; reused records retain their earlier/transitive
limitations. Both full original analyzer output and the compressed all-record
projection pass the strict checker. Its default now points to this review.
Detector-present exit code is not a clean-analysis exit or independent approval.

[Mechanical closure](MECHANICAL_REVIEW.json) compares all61production sources,
accepted compiler inputs/settings, existing storage/ABIs and constructor bodies.
Exactly five production files change. All126existing canonical declarations,
including90implemented bodies, remain exact. Existing financial statements in
Access/Migration match after removing only the added event calls; original
valuation methods and wire/reward math sources remain. Four new public view
methods plus an imported Strings error extend the concrete ABI; old functions
and constructors are preserved.

The source-bound function/input/output reference and operator tables cover
40contracts/963functions/40constructors/13receivers and1,016example rows, with no
explanation gaps. These document examples are not ready signed transactions.
The sole Todo remains open for actual publication/marketplace operation.

## Evidence and preservation

[Bundle](BUNDLE.json), [manifest](EVIDENCE_MANIFEST.json) and `evidence.zip` retain
source stages, failed/successful logs, compiler inputs/results, keeper/browser
checks and reconstruction helpers. The accepted normal full input/output are
also compressed separately under `build/`. Full external raw evidence remains
in the recorded local evidence directory; compressed static replay retains every
detector's exact fingerprinted text/classification, not analyzer AST metadata.

Four unrelated dirty files and three protected website signer/configuration
files remain byte-identical. No existing chain/RPC is contacted, no public
transaction/deployment/seal occurs and no site/service/Anvil/journal/heartbeat
changes. Public configurations remain null and the shared signer stays Anvil-only.
Actual supported-chain OpenSea JSON/media outcome and matching-host operation
remain unqualified. Independent audit/remediation is still required.
