# Source9 website consumer review

The fresh website now has an explicit **schema4/source9/accounting7** read and
unsigned-review path. It does not reinterpret served current3, older manifests,
Anvil deployments or journals. Contract baseline is main2138dd6; website source
is [main b8d871b](https://github.com/ABEF/AAA-website/commit/b8d871b769117fd3b375811fb34a64ae93847663).
No Solidity, runtime, economic rights, running site/service or signer was changed.
Production remains **NOT APPROVED**.

## Material changes

- Require explicit LP-allocation1/custody5/Policy1/direct Entry3/review2/royalty4/
  reporting5/canonicalV9 versions. Pin29 browser roles, exact runtimes, typed
  parent/module/upstream bindings and scoped policy fingerprints. Six concurrent
  verification reads; same-block proofs coalesce and failed proofs cannot poison
  retries. This browser subset does not replace the backend's complete inventory.
- Validate both LP legs, retained NFT shares, current-owner rights, governed
  artwork thresholds, terminal phases and ETH/ZZZ principal separately. Missing
  prices/history remain unavailable while healthy funded reward quantities remain
  visible. Terminal image fallback matches NFTMetadata._stageFile(4).
- Display pending funded LP ZZZ separately from claimable ETH. Original royalty
  currencies keep their exact raw units/decimals; no conversion, imagined ETH
  credit or cross-currency sum. Dormant cards have no fee/claim/window sections.
- Reconstruct Entry3's seven-field static tuple plus loss maximum and scoped
  contribution-policy hash. Verify captured price bounds/minima, exact rounded-up
  activation target, flexible growth minima, entrant-only marginal deployed LP,
  exact ZZZ approval and independent final simulation. Approval requires complete
  fresh preparation after confirmation; no unlimited approval or hidden retry.
- Add explicit transaction-policy1/2 support and complete claim-plan display.
  Preserve every selected entry; only the next freshly simulated batch is an
  unsigned transaction. No queued future transaction, omitted failure or auto-send.
- Keep source9 unsigned even on loopback Anvil. Do not instantiate its signer or
  depend on local mint readiness for portfolio reads. Website mint remains a
  demonstration pending actual OpenSea qualification.
- Correct the stale artwork checker: fixed royalty rarity multiplier1/2/3 is not
  the dormant effective eligibility weight0. All artwork/metadata bytes are kept.
  Include new shared dependencies in both isolated build paths without changing
  the public demo configuration or an existing dist overlay.

## Verification and original failures

| Evidence | Actual scope |
| --- | --- |
| [Final website test output](website-suite-final.txt) |953 tests pass,0fail/skip in one final package run. Includes113 source9 profile/data/API/unsigned methods; these are not additional to953. Earlier overlapping selections are not added. |
| [Source/asset checker](syntax-build-check-final.txt) |Syntax/routes/selectors and2784 self-contained artwork/metadata pairs,1000 inventory entries. Preserved image hashes and correct fixed rarity traits. |
| [Actual handler fixture](https://github.com/ABEF/AAA-website/blob/b8d871b769117fd3b375811fb34a64ae93847663/tests/fixtures/source9-api-v3.json) |35 real Python DTO replies across9 public handler methods against controlled synthetic RPC/SQLite/fees/authority fixtures, plus checkpoint2. Original raw/checkpoint all-time/day/window/event-count equality is asserted. No EVM/provider acceptance implied. |
| [Exact staged producer](staged-producer-proof.json) |360exact staged source/config/fixture files reproduce all10cases. Every output field except separately bound provenance/config identities matches the published website fixture. Temporary archive paths explain those identity differences; raw/checkpoint equality is checked again. Unrelated working changes cannot satisfy this run. |
| [Getter ABI comparison](profile-abi-check.json) |140 checked calls/124unique role-function signatures match retained current compiler ABI selectors and flattened output counts;0mismatch. The artifact retains its original compiler/source scope. No recompilation or new Solidity audit. |
| Unsigned composition |Real Projection/Transactions/ClaimPlanner replies feed DeploymentAPI, FreshProfile and the unchanged read transport. Policies1/2 preserve original USDC units, gas ceilings/headroom and exact calldata. New Entry3 activation DTO cases are explicitly synthetic typed fixtures; actual ActivationTransactions trace-provider emission/EVM qualification remains open. |
| Builds |Isolated demo build5602files; exact-source poplint artifact5595files, revision b8d871b, deployment_configured=false/public_signing=false. New build directories only; neither running root/dist overlay was touched. |
| Visual review |Three isolated synthetic handler cards: active, dormant and terminal return. Exact pending/original quantities and principal separation inspected. Preview server stopped. This is not wallet, full application, mobile or public-host acceptance. |

The initial data test failed because its test harness guessed old1k/10k thresholds
and omitted the Policy pin. It was corrected to use the actual recorded2k/20k
policy/fingerprint and reported current graph; production validation was not
relaxed. The prior website checker also failed on the untouched baseline dormant
trait; its stale zero-weight expectation was corrected. The first full unsigned
composition exposed unsupported eth_getBlockByHash in the unchanged read transport.
Policy2 now uses supported exact-number block reads with hash/number/time checks.
Supplemental fixtures corrected an incorrect test12M-versus-configured40M assumption
and object-key-order comparison; no financial guard was bypassed.
The staged producer extraction initially included unnecessary report snapshots
with overlong Windows paths, then missed an indexer JSON dependency. The final
bounded package/config/fixture extraction preserves both attempts and passes;
these extraction errors required no production code change.

## Preservation and remaining work

The shared signer SHA256 remains
`c8d9b9a96fb815be497e914e7f3054f3cd39bade73870396e36199495f07b106`.
Both public build inputs remain null. Website source publication and isolated
builds did not deploy poplint/popldemo, alter Anvil8902/NFTs/LP/balances/journals,
change services or restart the paused heartbeat. Existing asset bytes and the four
protected unrelated contract working files are preserved. Historical reports keep
their source scopes; only maintained report navigation is updated.

Next qualify actual runtime/API/configuration/fee/RPC bindings, independent feeds,
Entry3 marginal-LP traces, original-token faults, full-history/archive workloads,
gas/latency, wallet execution, authorities, VRF/OpenSea and hosting. Separately
authorize any site/service rollout. Retain independent audit/remediation as a
release gate. No mock response or local pass closes these requirements.

See [profile/operator procedure](../../docs/SOURCE9_WEBSITE_PROFILE.md),
[environment map](../../docs/SITE_ENVIRONMENTS.md), [features](../../docs/IMPLEMENTATION_STATUS.md)
and the [sole Todo](../../TODO.md#task-portfolio).
