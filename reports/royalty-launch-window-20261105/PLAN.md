# Royalty launch window

Baseline c7dad14. No deployment, live-site/service, signer, journal or Anvil change.

User decisions: official final OpenSea sale end, governance may change it during
minting; royalties open ONE hour later; all receipts during mint/window belong
to NFTs activated strictly before opening, rarity weighted. Late activations
earn only subsequent receipts. If none activated, preserve unallocated funds for
explicit governance allocation. LP rewards and principal remain independent.

Implement an on-chain sale end mirrored to the eventual SeaDrop final stage.
No modification after the configured sale has closed. Unconfigured royalty
opening fails closed; never fabricate a sale end from sellout or UI dates.
ERC20 has no receipt callback: use lazy opening before any post-cutoff activation,
checkpoint each readable currency before that entrant joins, preserve old-cohort
outage isolation and avoid initial-pool double counting. A new post-opening
currency retains the separately approved current-weight recovery rule.

Review mint callbacks/config changes, zero activated, deadline boundaries,
transfers, multiple currencies, token outages, delayed first claim/activation,
rounding and canonical lifecycle. Preserve earned rights and protected files.
Use explicit new profile/read capability and source-bound artifacts. Adapt only
affected checks; retain failures and historical evidence without relabeling.

Currency capacity is a separate consequential design decision: no unbounded
external-call loop or silent delayed-eligibility change is authorized yet.

Final user correction: fixed3600seconds after official mint end. Do not show the deadline on dormant NFT cards. Earlier24-hour draft evidence is superseded, not current verification.
