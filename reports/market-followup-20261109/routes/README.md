# Route evidence entry points

Final narrative: [ROUTES_FINAL_v2.md](ROUTES_FINAL_v2.md).
Final findings/counts: [ROUTE_FINDINGS_FINAL_v2.json](ROUTE_FINDINGS_FINAL_v2.json).
Direction/size/venue matrix: [route-matrix-final-v2.json](route-matrix-final-v2.json).
Necessary principal shared-reference admission bands: [common-reference-bands-v2.json](common-reference-bands-v2.json).
200k gas probes: [gas-budget-probes.json](gas-budget-probes.json).
Economic lower-bound arithmetic: [gas-economy.json](gas-economy.json).
Exact source pins: [source-pins-final.json](source-pins-final.json).
Complete current package integrity: [PACKAGE_MANIFEST_v2.json](PACKAGE_MANIFEST_v2.json).

Current strict Registry fee candidates:70(fee<100000pips),25not principal-admissible by fee(one exact100000 plus24above),95static hookless total. The earlier71 count is only the inclusive Balancer fee-ceiling filter. Eight active principal candidates and the selected+07ee2b necessary common-reference result are unchanged. Selected501122… remains LP destination; another destination is a separate unreviewed decision.

696 official quote calls include23 overlapping gas-budget rechecks; these are not696 distinct full operations.673 initial quote calls are646main,11gap follow-ups and16capacity probes. Full operation acceptance remains unavailable. No new RPC calls were needed for the fee-boundary correction. This package makes no production configuration or public transaction change. Earlier derived narrative/manifests, including README.previous-final.md, remain explicit snapshots.

Current earned conversion accepts only fixedZZZ -> nativeETH. Matrix numeric1% comparators for ETH -> ZZZ are explicitly not applicable as conversion eligibility; native principal balancing can use both directions. V3/WETH remains separate optional manual earned conversion and cannot be acquired after binding with wrapperzero. Fresh7 automation remains native-v4-only.
