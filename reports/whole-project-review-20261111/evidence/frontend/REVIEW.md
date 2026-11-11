# Website audit and source fixes — 11 November 2026

Website base: `2c6f0c822b909a8d44c457c2fd24d3f546745ba8`, main. Source-only changes;
no build, server/service restart, deployment, signing change, existing Anvil,
journal, public configuration, artwork regeneration or served-site update.

## Confirmed fixes

1. **Configured deployment profiles were not completely packaged/served.**
   `deployment-api.js` statically imports source10, source9 and native readers.
   The normal build omitted `deployment-source10.js`; the development server
   rejected five required reader modules. A configured current/source9/source10
   view could therefore fail its module graph with404. The null-config public
   simulation does NOT load that dynamic view and was not broken by this issue.
   Fixed the exact build list and server allowlist. Added a complete literal
   import-graph regression; both checks reproduce failure before the fix and pass
   after it. The recursive integration builder already included these modules.

2. **New demo input/UI policy still described removed currencies and pools.**
   Source UI advertised USDC/USDG and1%/99%, and new activation events named
   ZZZ/WETH despite the current native-ETH/fixed-ZZZ and3%/97% candidate.
   New source writes now use explicit `demo_policy:2`, ETH/ZZZ only and one
   ZZZ/ETH contribution pool. The header, mint explanation, form and FAQ agree.
   This is an illustrative cap, not an actual charge or source qualification.

3. **Historical demo compatibility needed explicit separation.**
   Narrowing the old event validators would silently drop saved activations or
   alter tiny earlier top-ups. Current helpers are separate; unversioned v7
   events retain original assets, pool labels, cent additions and LP-only claims.
   Mixed current/legacy events replay together without resetting storage. Exact
   initial-seed and mixed-legacy replay hashes remain unchanged. Six unused
   imports in app.js were removed; historical implementations remain necessary.

## Verification

- Packaging:2distinct new checks fail before fix and pass after;3syntax checks.
- Demo:6new current-policy/replay cases, included in86affected passing domain,
  UI-concurrency, contribution-flow and net reward-display cases;5syntax checks.
  The pre-fix run observed5failures and1preserved legacy pass (tool-observed,
  original producer log was not saved). No counts from overlapping stages added.
- Static source/config preservation: browser-wallet.js byte-identical at
  `c8d9b9a96fb815be497e914e7f3054f3cd39bade73870396e36199495f07b106`;
  DEPLOYMENT and INTEGRATION_DEPLOYMENT remain null and byte-identical.
- All untouched local/legacy/current3/source9/source10 signing and review modules
  retain their source identities. No unchanged full website/wallet suite rerun.
- Current docs: README, PROJECT_CONTEXT, FRONTEND_STATE, AGENTS updated; earlier
  dated notes retained under their explicit historical boundary.

See `START.json`, `demo-baseline.json`, `before.json`, `after.json`,
`demo-after.json`, exact logs and `VERIFICATION.json`. Thirteen tracked files
changed and two test files added; nothing committed or pushed by this agent.

## Reviewed trust boundaries and remaining work

Manual review covered browser entry/profile routing; source10 immutable graph,
price/admission/scoped-policy checks; source9 DTO/claim/preparation; API manifest,
provenance, portfolio/earnings/collection paths; current view/session/transaction
coordination; Anvil wallet intent/recovery; demo event/concurrency/display logic;
artwork transition/sound; static build/server and environment documentation.
Generated SVGs and existing report fixtures were not exhaustively reread or
regenerated. This is not a fresh proof of every old test, actual browser/provider
acceptance, complete public market qualification or an independent audit.

Preserve these intentional boundaries rather than deleting them as obsolete:

- Existing Anvil browser-intent/local-client profiles still accept their original
  four fixture currencies and old calldata. They are not current production
  inputs; public/current unsigned profiles remain explicit separate versions.
- Current/source9/source10 profiles do not gain a signing path. Actual public
  wallet integration, reviewed authority/service configuration and rollout need
  their own authorization and acceptance.
- Runtime/module/canonical-block checks do not make an API DTO cryptographically
  self-authenticating or prove honest RPCs/markets. Receipt simulations and
  contract ownership/accounting remain the financial enforcement boundary.
- A33-runtime proof and many bound getters can produce substantial RPC work per
  uncached block. The four-hash cache and six read workers are bounded, but actual
  provider/concurrent-user load and stale-window acceptance remain to qualify;
  no benchmark or provider guarantee is fabricated here.
