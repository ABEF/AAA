# User-reported local acceptance and priority decision - 2026-10-20

## Manual acceptance

After the local two-wallet fixes, the user replied **"All tested correctly"** to
the six proposed scenarios on the disposable setup at http://127.0.0.1:8898/app/.
Record these as user-reported manual passes, not newly executed automated tests
or independently inspected transaction receipts:

| Scenario | Reported result |
| --- | --- |
| Simultaneous activation, one dormant NFT per wallet | Passed per user report |
| Simultaneous top-ups with different amounts on separate NFTs | Passed per user report |
| Cancel after approval, reopen and reuse sufficient allowance | Passed per user report |
| Refresh while pending and recover without duplicate execution | Passed per user report |
| Claim while another wallet contributes, with scoped artwork updates | Passed per user report |
| Invalid amounts / insufficient balances without a stuck interface | Passed per user report |

The chat does not supply per-scenario amounts, assets, hashes, timing or browser
versions. Earlier assistant [two-mint receipts and scoped tests](NONCE_VERIFICATION.md)
remain separate evidence. These passes do not establish arbitrary concurrency,
production wallet integration, real routes/feeds or independent security approval.

## Accepted sequencing

The user explicitly deferred the proposed **10, 25 and 100 concurrent-user load
campaign**, allowing capacity improvements to be revisited after launch if needed.
No campaign is scheduled or authorized to run automatically. Its task remains
open and explicitly deferred; production capacity is **unverified**.

Next focus: real browser-wallet integration with the existing unsigned preparation
services, developed against local Anvil before public funds. The user accepted
that independent user signing/submission, bounded API concurrency and safe
transaction recovery are still required before accepting real funds. Do not deploy
the disposable shared signer/global-lock launcher as the production user service.

Only the scale campaign is deferred. Basic safe operation under configured limits,
RPC/route/feed/VRF and deployment qualification, transaction/accounting safety,
operator recovery and independent release review remain required. The release
approval record remains **NOT APPROVED**. Existing worker limits are not raised.

This update records evidence and priorities only: no code change, test rerun,
transaction, local/public service restart, website deployment or monitor restart.
The [central Todo](../../TODO.md) alone owns status and acceptance criteria.
