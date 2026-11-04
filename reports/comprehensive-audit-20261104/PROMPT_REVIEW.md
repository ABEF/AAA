# Plan challenges and final scope check

The [executed brief](AUDIT_PROMPT.md) is an improvement campaign, not a promise of
formal proof or a new independent audit. Source base: e237aa72; production Solidity
remains e26fc74. Both complete repository READMEs were read, including their
historical/demo sections, before final documentation changes.

## First critique: completeness and trust boundaries

Added the distinction between logical buckets, physical LP legs and NFT shares;
ordinary versus emergency policy; raw need versus sampled readiness versus
service jitter; independent harvest versus reserve use; entrant/incumbent
separation; per-currency royalty admission; terminal payout versus reward claims;
whole-collection versus pool movement; and historical API/runtime/source profiles.
Added SQLite ancestry, configuration aliasing, data lifetime and explicit
documentation/rollout boundaries. Existing source-matched evidence is reusable;
its tests must not be counted as fresh execution.

## Second critique: avoid harmful or unjustified fixes

Do not automatically delete wrappers used by reward conversion, reinstate bridges,
add delay to governance, change economics or promise zero idle. Do not widen the
signer, restart services or choose unknown feeds/VRF/authority addresses. Do not
require price evidence to restart for unrelated optional routing telemetry faults:
the existing incident regression deliberately preserves this distinction. The
initial suspected missing-reset issue was rejected after reading its regression
and coordination policy; no keeper change was made.

## README recheck and final consistency

The website README had current-looking accounting4/custody3 text,99% entry,
removed contribution inputs/bridge language, dormant trait weight0 and obsolete
claims-currency/pattern guidance. Scope therefore includes documentation repair
while retaining actual old fixtures, the current3 served site, null configuration,
local signer and the demo's illustrative arithmetic. A documentation checkpoint
must not imply fresh-source support or a rollout. OpenSea remains unsupported by
the custom direct mint and must not be marked implemented from ERC721 metadata.

The final brief covers economic rights, market behavior, adversarial actions,
all operating lifecycles, services, data, UI, longevity and evidence. It does not
authorize unsafe external actions, assert every function was freshly tested, or
close provider/market/operating/independent-review gates without evidence.
