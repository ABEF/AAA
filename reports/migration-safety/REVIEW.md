# Migration safety and preparation review

Internal development review, 2026-10-17. No public deployment, signing, website
change or server upgrade was performed. This is not an independent audit or
production approval. Progress belongs in the [central Todo](../../TODO.md).

## Implemented scope

The [migration budget helper](../../src/ZZZMigrationBudget.sol) enforces one
aggregate 3% execution-loss limit for atomic local same-ordered-pair moves and
parked resumption. It has no custody, arbitrary calls or configurable executor.
The creating Vault is its sole checkpoint caller. Initial fresh prices/decimals
are reused after harvest, close, balance and mint. Released compound increases
the initial denominator; existing funded rewards cannot subsidize principal loss.
The rounded-up 97% floor covers deployed LP plus attributed idle, with the existing
5% idle ceiling under the same prices. Activation/top-ups retain their separate
99% marginal deployed-LP requirement. Network gas is separate.

Reversible timelocked preparation binds an exact notice, source domain and nonce.
It stops new economic work and protocol module configuration while preserving
current ownership, transfers, funded claims, reveal and settlement/drain paths.
Checks after callbacks prevent a nested announcement from allowing new work to
finish. Incoming custody and funded Reward/ACK delivery are preserved. Only the
timelock can cancel the exact notice or use the narrow parking/cancellation drain
exception; no new rescue recipient or successor authority is introduced.

The keeper reads preparation strictly and checks again before durable intent and
signing. Invalid or unsupported responses fail closed; pending receipt recovery
continues. Its new interface requires coordinated qualification with the deployed
controller. Existing isolated staging remains on its earlier release.

## Issues corrected during development

| Finding | Correction and verification scope |
| --- | --- |
| Taking the migration baseline after harvest could hide loss during a mutable harvest callback. | Snapshot before harvest; add only the attributed-idle increase from released compound. Adversarial tests exercise price/principal mutation during harvest. |
| A mixed-case helper address could alias a creator-payment inbox in the offline manifest checker. | Normalize the copied manifest value before later custody comparisons. The exact failing mutation and four focused regression cases are recorded in [the finding](config-review/finding.md). |
| Initial preparation modifiers pushed Migration above the standard runtime limit. | Factor identical drain-authority checks into one private function; retain all guards and the standard limits. The initial failed build is retained separately. |

## Boundaries and remaining risks

- The 3% check is not an asynchronous bridge budget, a different-pair conversion
  guarantee, a cap on ordinary rebalancing, or a bound on loss incurred in the
  earlier parking transaction. Repeated approved moves can accumulate losses.
- Oracle accuracy, venue backing, token/wrapper behavior and governance admission
  remain trust boundaries. Caching prices cannot make a dishonest initial price
  or venue report accurate. Pre-existing unattributed donations are excluded;
  token behavior/donations during venue callbacks remain dependency review issues.
- Preparation is local. It proves neither satellite shutdown nor complete message
  draining. Inherited role administration and scheduling remain available under
  existing authority; the governance delay remains immutable.
- Preparation does not freeze/export/import NFT and reward ledgers, retire the
  source, or activate a replacement. The selected policy requires verified
  finalized retirement and fully funded imported state, with no multisig-only
  override. Actual proof support remains unselected. These full handoff features
  must be implemented before sealing; post-halt recovery remains deferred.
- Vault has 17 runtime bytes free and Migration 30 under the current compiler
  profile. Further handoff work needs modularization and renewed review. Passing
  object-size checks does not qualify constructor arguments or target-chain gas.
- The manifest validator checks declared consistency, not chain truth or review
  authenticity. A passing manifest is not deployment authorization.

The [verification record](VERIFICATION.md) separates executed checks, earlier
failed attempts and historical evidence. The [preparation keeper review](../canonical-preparation/keeper/README.md)
records its independent internal source inspection and operating compatibility.
