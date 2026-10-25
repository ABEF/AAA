# Historical creator-revenue measurement

The former Pons creator-payment agreement and sampled-liquidity measurement tool
are **retired from the current release**. PoPL receives actual fees earned by its
own position in the selected hookless ETH/ZZZ pool; it does not calculate a creator
invoice or depend on a promised creator payout.

The old calculation code, tests and guide are preserved as exact historical text
in [the retirement archive](../reports/obsolete-code-20261025/retired-tools/).
They are not importable runtime tools or current test evidence. Earlier reports
retain their original source scope.

For current accounting, use [economics](ECONOMICS.md),
[the simplified release boundary](SIMPLIFIED_RELEASE.md) and
[the operator manual](OPERATOR_MANUAL.md). Marketplace NFT royalties remain a
separate funded ledger; removing creator-payment measurements does not remove
royalty receipts, guarded conversion, claims or historical earnings.
