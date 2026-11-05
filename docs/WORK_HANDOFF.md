# Work handoff

Reviewed5November2026. Pre-window baseline main c7dad14. Inspect actual Git heads
before claiming publication. Read ../AGENTS.md, ../PROJECT_CONTEXT.md, ../README.md,
../TODO.md, OPERATOR_MANUAL.md and ROYALTY_LAUNCH_WINDOW.md. Production NOT APPROVED.

## Current result

ONE-HOUR royalty grace after final sale end;24-hour drafts superseded. Governed
NFT.setMintEnd can revise a future end only during the OLD sale. Unset/past end
rejects minting. Strict pre-cutoff activated NFT cohort, rarity1/2/3, original
currencies, lazy automatic allocation; late activations future-only. LP claims
independent. No deadline displayed on dormant NFT cards. Zero initial participants
keep unallocated funds for explicit governance allocation.

Separate openingPool from constructor/preadmission prefunds and earned/fraction
backing. New allocateAllUnallocated(asset,reviewHash) allocates every eligible
unallocated unit in ONE currency at current active weights. No swap/payout/sweep.
Capacity starts16ERC20+ETH; governance can increase to64 after gas/service review,
never remove currencies/rights. Review hash is not an on-chain gas proof.

Fresh royalty3/recovery2/canonicalV7/schema12/reporting4/keeper royalty3,18helpers.
V7 header five words carries sale end/capacity; capture waits for finalized opening
and each initial currency sync. Old V6 peers/runtime/storage are not compatible
by tuple shape. No journal/checkpoint adoption. Emergency LP paths remain separate.

## Verification and remaining gates

See ../reports/royalty-launch-window-20261105/VERIFICATION.md and evidence.json:
42normal gates at51production/31dependency pins;479static contexts,103current/
376exact reuse;125distinct scoped one-hour EVM successes across explicit stages;
183affected Python checks,71reference/static/publication checks and157website
cases. Failures/24-hour drafts retained externally. This is not whole-suite,
public CI/target gas/marketplace or independent approval. Source cannot deploy,
seal, turn on public signing or update running services/sites by publication.

Real OpenSea/all mint-path/end binding, token/price/VRF/routes/authorities,
maximum gas/expanded API/history/canonical workloads, fresh source8 clients,
storage/recovery and independent audit remain open in the sole Todo.

## Required maintenance

```text
python scripts/generate-function-reference.py --check
python scripts/generate-operator-reference.py --check
python scripts/sync-project-todo.py --check
python scripts/check-python-publication.py --index
```

The last check reads EXACT staged blobs; repeat against committed HEAD before
publication. Preserve source-bound notes/examples/evidence; do not repin to hide
drift. Current reference36contracts/809functions/36constructors/12receivers and
857short examples has no input/output/explanation gaps. Operator tables are NOT
live snapshots, simulations or signing approval. Update manual/procedures and
reverse/restart/irreversible boundaries with every behavior change.

## Preserve actual state

Main only; source/docs publication is not rollout. Anvil8902, all NFTs/LP/balances,
dist overlays, pending/nonce/receipt/spend journals and shared browser signer stay
unchanged. Popldemo simulation and separately served poplint current3 remain;
fresh source8/config12 is not the served site. Public DEPLOYMENT null, signing
Anvil-only; heartbeat remains user-paused. No public transactions or service reset.

External evidence root:
`C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9`.
Task royalty-launch-window-20261105 archives original source/docs/protected bytes,
all failures/draft24-hour artifacts, final one-hour compiler/EVM/Python/site/static
evidence. Prior2727tracked report files remain byte-identical. Preserve unrelated
untracked drafts and the four tracked dirty files below; never stage them here.

| Protected tracked file | Original SHA256 |
| --- | --- |
| `reports/source-checks.json` | `049dca6943d06ba63de682dc8cdec2cf3935af1dc2e5479e9f3cf14e1af793c4` |
| `scripts/run-fork-checks.py` | `875d27fb56963d92e6e7ec25b9f296b5559b830e007ad411afb856f0f0226f1b` |
| `tests_python/test_fork_runner.py` | `6d50a612ec490ec0f3754d930ac6610173d96d0a684bbc5e4894eaedf4d9abc9` |
| `tests_python/test_frontend_history.py` | `361f6a56153a4b3041b5b6f7eaaf399fea063bae9f46299da71397a08540c7eb` |
