# Metadata notification: current-source static analysis

Internal review completed 2026-10-15. **Not an independent audit or production approval.** The fresh isolated build and Slither 0.11.6 execution bind all **26 Solidity sources and three compiler/configuration files**. Only `src/ZZZNFT.sol` differs from the previous reviewed source snapshot; its frozen SHA-256 is `b366bb5a58994b442033fad85e55d8312f6affee612f9f7f719da4a88b0a01e6`.

The hash-bound prior compiler input was compared with current source. Its exact change adds `MAX_METADATA_REFRESH_BATCH=50` and `refreshMetadataRange`; the ordinal-to-token map and mint implementation already existed. The raw analyzer report, compiler inputs/output, exact source diff and execution logs remain in the external `slither-release-hardening-20261015/` evidence directory. Earlier report directories were not overwritten.

| Check | Result |
| --- | --- |
| Fresh offline compilation | Exit zero; isolated output/cache, ordinary pinned compiler profile |
| Analyzer | JSON success true, error null; 179 findings, zero newly introduced detector findings |
| Individual review | 175 exact previous fingerprints; four NFT finding locations individually re-read against unchanged function bodies and the new notifier |
| Dispositions | 110 false positives; 42 accepted risks; 27 informational; zero unresolved |
| Source snapshot | All 29 source/configuration hashes unchanged during the run |
| Unchanged coverage gate | Pass for all 179 native findings |
| Matcher regression | Pass for a 180-record historical split-shape fixture; all seven adverse mutations rejected |

The analyzer's findings exit `-1` is represented by Windows as `4294967295`. It is not treated as successful execution by itself: successful compilation, JSON success, no analyzer error, frozen source and complete source-bound review coverage were separately required. The CI checker and detector configuration were not changed or weakened.

The four changed finding descriptions concern `mint` coordinator reentrancy, `notifyContribution` event ordering, retained `_baseURI` dead code, and long VRF configuration-bound literals. Each has its current native fingerprint, specific rationale and prior-review identity in [changed-findings-review.json](changed-findings-review.json). Full review entries remain in [the default source-bound review](../../production/slither-review.json); its previous 179-entry bytes are preserved in [history](../../history/slither-review-pre-release-hardening.json).

The [manual entrypoint review](metadata-entrypoint-review.json) checks short-circuit range validation, inclusive 50-entry bounds, actual hashed token IDs, overflow safety, local ownership reads, lack of external calls/state mutation, pause/outage independence and atomic failure. An agent separate from the implementation author corroborated the source review. Author-reported targeted tests and the 318,466-gas cold 50-token measurement are labelled separately; they are not an external audit. Full execution/size evidence is retained by the parent release-hardening report.

The [coverage receipt](slither-coverage.json), [matcher regression](slither-matcher-replay.json) and [tool/source/hash metadata](slither-review-metadata.json) record the exact scope. The split-shape fixture tests matching stability; it is not another analyzer execution.

Recheck the recorded current report from the repository root:

```sh
python3 scripts/check-slither-review.py reports/release-hardening/static-analysis/slither.json
```

Independent audit/remediation, real selected-market/VRF/provider integration, immutable artwork publication, actual authorities and staged operating evidence remain required. Neither this notification change nor its analyzer review enables the currently unsupported native-ETH/Pons pool.
