# Optional pool-spot composite price source

## Decision and implementation

The user explicitly selected spot for both liquidity placement and the independent
ZZZ/ETH valuation reference. The optional
[ZZZV4SpotPriceFeed](../../src/ZZZV4SpotPriceFeed.sol) composes a reviewed native-v4
ETH/ZZZ reference spot with a reviewed ETH/USD round. Current placement already
uses main ticks, current/post-swap pool state and actual-core quote sizing; no
Vault, Strategy, Balancer or contribution-accounting implementation changed.

The reader pins the full static hookless PoolKey/PoolId, core/StateView/token/feed
identities, decimals, original ETH age, minimum current active liquidity and a
review commitment. Reads are bounded and reject malformed state/rounds. Synthetic
rounds bind the raw pool and ETH observations. No admin, setter, swap, payment,
approval, custody or automatic pool-discovery method exists.

No TWAP/history/persistent-trigger rule is introduced. This accepts increased
temporary reference manipulation exposure. The ordinary keeper's separate
sampled rebalance confirmation and jitter are unchanged; a spot adapter is not
a replacement for those controls or proof of continuous price history.

## Qualification and limitations

Prefer the largest **qualifying external** reference; raw L/displayed TVL alone
does not prove bidirectional depth, source independence or exclusion of PoPL LP.
That qualification is not enforced by an on-chain TVL leaderboard. Two copies
of one ZZZ pool with different ETH feeds remain correlated. The existing
two-source Oracle admission, agreement, financial floors and ownership/custody
checks remain unchanged.

The frozen contribution basis exposes an important configuration interaction:
using the live reference as destination changes its liquidity, and using it for
the executed swap can change its price. The reader then changes its observation
identity/bounds and the existing final contribution check rejects. This safety
check is retained. Qualify a reference untouched by the complete operation,
including route selection; a highest-TVL/best-execution collision is an explicit
remaining market/configuration gate, not a reason to suppress the fingerprint.

PoolManager slot0 has no last-trade timestamp. Returned timestamps belong to the
original ETH observation; a fresh read is not proof of recent ZZZ trading. Outer
runtime pins do not freeze proxy implementations or prove honest market data.
The reader has no production pool, age/L setting or live admission. The dated
[market follow-up](../market-followup-20261109/REVIEW.md) retains its original scope.

The [operator procedure](../../docs/POOL_SPOT_PRICE_SOURCE.md) covers exact Config
inputs, pre-admission review, immediate governed `setDualFeed` changes after seal,
consumer configuration and failure recovery. Replacing a reader is not replacing
the sealed Oracle/Vault implementation. Existing deployments/journals retain
their original profiles.

## Verification status

The [verification record](VERIFICATION.md) binds the final source, compiler,
focused EVM checks, static review and documentation gates. Twenty-three distinct
new EVM methods pass, including a 1,000-input arithmetic property; the second
stage runs only two added boundary methods. Existing59source files and every
existing contract ABI/creation/runtime object are byte-identical. The optional
reader passes normal size gates without consuming existing Vault headroom.

Actual Slither produces560records:558unique exact referenced-source reuses and
two individually reviewed reader contexts. This is internal review, not an
independent audit or proof that arbitrary spot sources are safe. Ninety-five
affected reference/operator/static-review Python checks pass at the first stage.
Final link checking exposed a constructor-only tuple omitted from expanded
operator inputs; a regression reproduces the missing link, and the corrected
generator passes21operator checks including the new regression. These21 overlap
the earlier stage and are not added as21new cases. The two source
inventory checks exposed an older missing SeaDrop helper declaration; the
required-class list now includes it and the new optional reader. The failed
inventory assertion and its focused correction are recorded separately.

The Todo, feature reference, current context/handoff, pricing/service guide and
operator manual are updated. Every new read/output and the exact constructor
tuple has an explicit generated reference and an operator example; no example
is a live snapshot or a transaction ready for submission. Historical reports
retain their exact source scope. Actual source/market admission stays open.

No contract deployment/source admission, public transaction, provider funding,
sealing, website/service rollout, signer change, existing Anvil/journal mutation
or paused-heartbeat restart was performed.
