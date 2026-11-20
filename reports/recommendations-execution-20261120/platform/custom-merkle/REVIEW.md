# Custom Merkle qualification: new phase examples

20 November 2026. The operator selected **qualifying a custom OpenSea path using
the current Merkle design**. This supersedes pursuing standard signed-presale
adaptation as the next implementation choice. The older adaptation plan remains
historical analysis; no signer authority is enabled and mint2 remains unchanged.

## Work executed

The [new report-scoped producer](prepare_phase_examples.py) rebuilt a phase
manifest through the maintained CLI using **105 actual current source pins**.
Its request reproduces the retained manifest/root/proofs exactly. It then
independently encoded two previously unexecuted current-source phase examples:

| Example | Quantity | Gross native value | Proof | Result |
| --- | ---: | ---: | --- | --- |
| Free TEAM | 2 | 0 wei | Freshly rebuilt TEAM leaf; 2 siblings | Offline review matches recipient, quantity, terms and exact zero payment. |
| Paid ALLOWLIST | 1 | 50,000,000,000,000,000 wei / 0.05 ETH | Freshly rebuilt ALLOWLIST leaf; 2 siblings | Offline review matches recipient, one-mint cap, terms and exact payment. |

Both use canonical `mintAllowList` with a 416-byte proof offset and 516-byte
calldata. The exact source transaction is preserved. Every live-readiness flag
stays false. The prior PUBLIC example was not repeated, and no unchanged unit
test, compiler, EVM, network request, signing or transaction ran.

[Execution](examples/EXECUTION.json) records the three new CLI invocations:
one `prepare`, then TEAM and ALLOWLIST `review-mint` calls. Each returned zero.
Original input/artifact bytes stay untouched. [Independent byte inspection](EXAMPLE_VERIFICATION.json)
checks the new words, offsets, proof lengths, recipient and exact values without
calling the reviewer again. It also pins producer and produced artifact hashes.

## Scope and limitations

These are **actual-repository-source, illustrative-input examples**, not actual
OpenSea payloads or mint transactions. NFT address `0x...0001`, participants,
recipient, fee recipient and Unix times 100–399 are dummy fixture values. The
sample paid-stage fee is **1000 bps solely because the reused fixture used it**;
no actual OpenSea fee, fee recipient, payout or creator agreement is approved.
The sample eligibility list is not the operator's complete team/allowlist.

No deployed NFT, current SeaDrop runtime, on-chain counters/time, buyer funding,
remaining phase supply, authority, gas or custom OpenSea onboarding was verified.
A source-bound proof is neither an authorization to send nor proof of payment.
Keep unknown production inputs blocked; rebuild and review exact new artifacts
when actual collection/participants/terms/schedule are supplied.

## Reproduction

The successful producer command used the original external saved example:

```text
python reports/recommendations-execution-20261120/platform/custom-merkle/prepare_phase_examples.py --source-input ORIGINAL_CURRENT_SOURCE_INPUT.json --output-directory NEW_EXAMPLES_DIRECTORY
```

Omit `--source-input` to use the exact same input already published inside
`reports/readiness-advance-20261120/evidence.zip`. The producer rejects source
drift and existing output directories. The full exact command and three CLI
receipts are represented in the producer and execution artifact. New production
source must receive its own reviewed pin update, not relabeled old outputs.

Next follow [the custom onboarding package](ONBOARDING_PACKAGE.md). It identifies
the exact platform evidence and actual inputs needed without silently converting
the sale to signed stages or claiming custom OpenSea support is established.
Production remains NOT APPROVED.
