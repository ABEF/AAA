# Current selected-pool fork verification

Campaign started 2026-10-26; final review 2026-10-27 Europe/Paris. The directory
retains its original name. Earlier `date` fields are campaign labels, not exact
request timestamps; those original bytes are not rewritten. New
runner receipts distinguish the campaign review date from actual UTC start/end.

**Implemented:** a separate current accounting3 native-pool fixture and a bounded
read-only fork runner. **Production NOT APPROVED.** No production Solidity,
economic rule, permission, loss limit, website, service, public transaction or
existing Anvil/NFT/LP/balance/journal was changed by this partition.

## Actual target and source boundaries

Pinax served the selected historical chain4663 state at block96,427,989, hash
`0x0ba14c22200dfc717bbd2c8b5b8842329775374d06f46e30c65e273f067ecbc3`.
The [pool witness](pool-witness.json) records the actual StateView return and the
five runtime/wiring assertions required by the passed current fixture setup.
The PoolKey is native ETH/fixed ZZZ, fee10020, spacing200, no hook, with ID
`0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b`.
At that block, directional protocol fees are1000pips and the combined charge is
11010pips (1.101%). This is a historical observation, not today's quote or depth.

The fixture executes current Vault, Entry, Registry, pricing/strategy, native
LiquidityManager, NFT, membership and LP fee/reward code against actual deployed
Uniswap core/periphery/Permit2/ZZZ. Authority, VRF, USD sources and local funding
are explicit test substitutes. Fixed test ETH/USD and spot-derived ZZZ/USD use
correlated fixtures, not two independent sources or actual-dollar qualification.
MockAccess is not proof of production sealing/authority configuration.

Forge1.4.4 commit05794498 and solc0.8.26/Cancun use the normal committed optimizer
profile. No runtime/initcode/gas guard is raised. [Bindings](bindings.json) preserve
44 production Solidity,31 normal dependencies and4 build-input pins; the37 normal
object gates are reused at those exact pins, not rerun. [Successful-run metadata and
cache checks](profile-settings-verification.json) confirm all four used scopes
actually compiled under default/Cancun/viaIR/optimizer-enabled/runs1/Yul-false
with solc0.8.26; this is artifact inspection, not another EVM run. The actual fork fixture
has separate source pins; normal deployment/gas approval remains open.

## What actually executed

[Summary](verification-summary.json) maps **11 distinct successful EVM methods**
to exact receipts. This is composed affected evidence, **not a fresh run of all11
methods against the final file**:

| Scope | Used successful methods | Evidence |
| --- | ---: | --- |
| Second complete10-method attempt | 8 unchanged methods | [Receipt](attempt2-receipt.json), [results](attempt2-results-summary.json) |
| Corrected swaps-only case | 1 | [Receipt](attempt4-affected-receipt.json), [results](attempt4-affected-results-summary.json) |
| Declared small-growth/both-input case | 1 | [Receipt](attempt5-small-growth-receipt.json), [results](attempt5-small-growth-results-summary.json) |
| New unfillable-growth/atomic-rollback case | 1 | [Receipt](attempt6-growth-rollback-receipt.json), [results](attempt6-growth-rollback-results-summary.json) |

The first8 method bodies remain identical. Their stricter timestamp-equality
expectation is compatible with the final zero-amount/nonfuture-expiration check;
the separately tested swaps-only branch also permits untouched zero expiration.
The final positive method and its original helpers are unchanged after its run;
only read-only snapshot helpers and the new negative method were appended. The
negative method uses the final strict transport and final fixture. Each used
execution reports stable source inputs. Earlier overlapping passes are not added.

Coverage includes actual native LP mint/increase/close; both swap directions;
funded harvest and no repeat harvest; native/token prefunds; missing native input;
stopped-pool unwind; rejecting ETH recipients; one physical LP with independent
NFT shares; exact ZZZ approval/consumption/reset; native activation and $5 growth;
current marked LP; funded claims following transfer; and failed-growth rollback.

The maintained runner still requires **all11 current methods** and rejects
skips, empty/partial results and legacy/extra suites. Its command is in the
[guide](README.md). The report's one-case driver is explicit affected evidence,
not a replacement for that complete-suite gate.

## Useful failures and their limits

The [first attempt](attempt1-summary.json) had4 passes/6 failures. Real Permit2
maps zero expiration to the current block timestamp; zero amount remains zero
spending authority. A one-call sender prank was also consumed by an intermediate
external getter. Those were fixture errors; no production guard was weakened.
The [empty-selection attempt](attempt3-no-tests.json) returned no tests and made
zero archive reads. Result verification rejected it despite Forge's zero exit
code; its selector was corrected and exact returned-name verification retained.

A later native100-unit growth after two native100-unit activations **really
failed its swap-output floor**. The [trace witness](growth-slippage-witness.json)
records `LiquidityManager.unlockCallback` receiving an exact full input of
19,240,206,012,453,380wei and positive output of
3,816,812,783,295,234,678,051ZZZraw, below the minimum
3,821,657,217,445,631,430,489ZZZraw. The proven failure is
`outputDelta < minOut`, not a partial fill or LP-deployment minimum. This does
not independently decompose its cause into fees, depth or reference-price timing.

That limitation is retained as an expected-Slippage case. It verifies identical
before/after user/Entry/Vault/Manager/Core/Fees/Rewards ETH/ZZZ balances, physical
LP/group/spot/shares/contribution accounting, both NFTs' reward indices/fractions,
liabilities, dust and compound/buyback reserves. A funded holder claim still
succeeds afterward. Real network gas would remain spent on a reverted public
transaction; this fork verifies contribution/backing rollback, not gas refunds.

The separately declared positive fixture admits a5-unit pool floor: native100
activation, native5 growth and a100-unit ZZZ activation for the second NFT pass
with exact approval and one physical LP. Global100 activation/5 growth and200bps
execution guards are unchanged. No feed, price, liquidity or loss cap was changed
to rescue the failing larger-growth operation. These are test-USD units under
the disclosed fixtures; they do not qualify real production prices or guarantee
arbitrary contribution sizes are feasible.

## Read-only transport and unresolved provider scope

[Eleven final focused runner methods](runner-tests-final.json) pass: complete-result
inventory, skip/failure/legacy/extra/empty refusal, denial of transaction/wallet
methods, path-credential error redaction, strict duplicate/nonfinite/overflow JSON,
sanitized parser-limit faults, an actual loopback redirect refusal and compiler
environment/effective-configuration admission. Earlier ten/six-method selections
overlap these eleven and are not extra coverage. Request and
response boundaries reuse the shared strict JSON helpers; upstream errors use
fixed messages, and a per-client redirect-denying opener is used.

A final preflight correction strips inherited `FOUNDRY_`/`DAPP_` overrides while
preserving runtime paths, forces `FOUNDRY_PROFILE=default`, and checks the actual
`forge config --json` compiler/source/remapping/size/FFI settings before opening
the RPC relay. This also rejects conflicting dotenv/global settings. Only
reviewed nonsecret fields are retained; the full config may contain unrelated
credentials and is never saved. A [real config-only probe](profile-effective-config.json)
with poisoned inherited overrides and the focused method verify this guard.
The prior actual EVM settings were already normal, as artifact/cache metadata
proves; no successful EVM case was repeated for this preflight-only correction.
[Bindings](bindings.json) retain both the tested and current runner identities.

The source-only transport corrections do not change EVM state/data. The final
negative case exercises this transport with163 real archive reads. The process
tree is bounded and cleaned up; no sustained operating-service qualification is
claimed by these runs.

[Discovery](rpc-probe-network.json) found working Pinax chain/archive access.
The official endpoint failed transport from this environment; BlockVectra's
keyless endpoint rejected the older block outside its public history window.
A separate batch-based full-pool observer failed an HTTP request after its
initial chain/header batch; [diagnostics](pool-observer-diagnostics.json) retain
that failure. No complete batch/hash-selector/log/trace preparation capability,
provider reliability, independent archive completeness or production hosting
approval is inferred from the working serialized fork reads.

Actual feeds/routes, default1% ZZZ-to-ETH reward conversion, real contribution
size/depth and maximum-state gas, authority/sealing inventory, VRF, OpenSea,
current3 hosted services, operations and independent audit/remediation stay open.
Large raw traces and original source snapshots remain in the external
`current-pool-fork-20261026/` evidence root recorded in the work handoff. Their
hashes, exact receipts, source snapshots and concise results are retained here;
historical reports and unrelated drafts keep their original bytes.
