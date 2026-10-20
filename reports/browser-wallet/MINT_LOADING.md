# Mint loading-state correction - 2026-10-20

The user reported Processing on first refresh before starting any mint. The
rendered button used the shared view's generic busy flag, including data reads
and other NFT operations. It now uses explicit activity/action/stage state.

- First read: Loading mint details; subsequent read: Refreshing mint details.
- Account/network connection: Connecting wallet / Checking network.
- Mint review/preflight, wallet request, submission/receipt and reconciliation
  have separate labels. Only an actual mint action uses mint progress wording.
- Other NFT actions do not masquerade as minting. Pending recovery and stale
  data still disable new actions and show an appropriate state.

This changes the website source used by both local signing modes, not fixture
responses or a hardcoded account. The public simulation already uses its own
mint-specific operation state and was not changed. Financial guards, transaction
submission, balance calculations and artwork confirmation requirements remain.

44 affected cases pass with zero failures/skips:

```text
node --test tests/wallet-lifecycle.test.mjs tests/ui-state.test.mjs tests/contribution-flow.test.mjs
```

Two new cases exercise first load vs mint phases and claims/approvals/activation/
top-up vs mint, plus saved recovery and stale reads. Syntax passes; build produces
5,593 files. [Source bindings](mint-loading-sha256.json) and
[test output](mint-loading-tests.log) record this scope. Served local code matches.
No new on-chain transactions, browser signing acceptance, production deployment,
contract/backend changes, service reset or unchanged signer regression rerun.
Reload the current page to load the source; do not reset the chain or wallet.
