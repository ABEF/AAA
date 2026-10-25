# Real-service readiness research - 25 October 2026

This is dated official-document research and local tooling preparation. No
provider, randomness service, price pair, authority address, marketplace product
or deployment is approved by it. No public transaction or service change occurred.

## What is known, and what remains external

| Area | Current evidence and remaining decision |
| --- | --- |
| RPC | Robinhood documents mainnet 4663/testnet 46630, archive access for historical reads and commercial infrastructure options. It explicitly warns against using its rate-limited public endpoints as a production plan. Choose reviewed independent providers and actual archive/trace/operating terms. [Official connection guide](https://docs.robinhood.com/chain/connecting/) |
| Prices | Robinhood documents AggregatorV3 crypto feeds and directs integrators to the Chainlink catalog. That does not identify two independent PoPL USD sources or qualify their precision, upstream markets, administrators, heartbeat or operating cost. No defensible independent ZZZ pair was established in this pass. [Official price documentation](https://docs.robinhood.com/chain/oracles-and-price-feeds/) |
| Pull data | A Robinhood Data Streams verifier is documented, but a pull-report verifier is not automatically a continuously updated AggregatorV3 source. An adapter, update service and independent underlying ZZZ data would require separate design and review. [Official Data Streams documentation](https://docs.robinhood.com/chain/data-streams/) |
| Publication trust | Self-managed feeds can expose familiar interfaces while an external operator controls publication and monitoring. Two wrappers, a shared reporter, or a shared upstream market do not establish independence. [Chainlink responsibilities](https://docs.chain.link/data-feeds/self-managed-feeds) |
| Sequencer | Robinhood recommends a sequencer check but supplies no uptime-feed address on its price page. Chainlink's current supported-address list omits Robinhood and says expansion to new networks has stopped. Obtain a genuine supported source or independently justify an explicit no-feed policy; another chain's address cannot be reused. [Chainlink availability notice](https://docs.chain.link/data-feeds/l2-sequencer-feeds) |
| Chainlink VRF | The current v2.5 supported-networks page contains no Robinhood entry. This establishes no approved Chainlink coordinator for PoPL on that chain, rather than proving all randomness services are impossible. [Official coordinator list](https://docs.chain.link/vrf/v2-5/supported-networks) |
| Other randomness | D20DAO publishes a distinct request/proof/recovery integration; RH-VRF documents threshold-BLS/native-payment and zero-key-hash semantics. Neither is selected or independently approved. Current PoPL requires a nonzero lane and a fixed original coordinator; do not remove guards simply to fit a candidate. Provider sources, proof/key security, administration, fees, callback bounds and original-request recovery remain to be verified. [D20DAO deployments](https://d20dao.org/docs/deployments), [RH-VRF documentation](https://rh-vrf.com/docs) |
| OpenSea | Its official compatibility list includes Robinhood. Primary Drops are a separate product using SeaDrop-compatible integration; the mint API documents ERC721 SeaDrop V1 support. Current PoPL custom Vault minting is not automatically accepted by that product. Establish the exact compatible mint/recipient/fee/VRF path before sealing. [Supported chains](https://support.opensea.io/en/articles/8867082-which-blockchains-are-compatible-with-opensea), [SeaDrop](https://docs.opensea.io/docs/seadrop), [mint API](https://docs.opensea.io/reference/build_drop_mint_transaction) |

The [Creator Tasks](../../TODO.md#creator-tasks--zzz-team) retain the unresolved
ZZZ market/source and official-token questions. Historical Pons creator sharing
is optional for the selected hookless pool. Authority wallets were deliberately
left unset; no repeated request or invented addresses closes those gates.

## Useful local progress

Extend the existing [RPC probe](../../docs/RPC_PREPARATION_QUALIFICATION.md), rather
than create another overlapping tool. Its preparation profile can check the
reviewed network/runtime and an actual same-hash `callTracer`/`withLog` event
before PoPL deployment. The existing legacy checks remain separately labeled.
An unavailable-block probe must distinguish a real remote missing-block error
from a timeout, rate limit or unsupported parameter.

This narrows a concrete qualification gap. It cannot manufacture independent
prices, authenticated randomness, OpenSea product acceptance, hosted-service
reliability, permanent artwork publication or an independent audit. Actual
provider observations and operation rehearsals remain explicitly open.
