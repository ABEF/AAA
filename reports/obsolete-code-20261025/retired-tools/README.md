# Retired creator-payment tools

These `.txt` files preserve the exact pre-removal bytes and their SHA-256 hashes
in [retirement.json](retirement.json). They are historical source/test artifacts,
not importable Python, active configuration or current passing tests.

- `zzz_ops__revenue_share.py.txt`: unused creator-payment share calculator and
  pinned-liquidity collector, removed from active runtime modules.
- `tests_python__test_revenue_share.py.txt`: tests for that retired proposal,
  removed from normal test discovery. No retired method counts as a new pass.
- `docs__REVENUE_SHARE.md.txt`: former creator agreement and tool instructions.
- `keeper__config.example.json.txt`: old implicit profile-0/accounting-V1 example
  with creator synchronization enabled. Existing installed configurations and
  journals were not changed or converted.

The selected hookless ETH/ZZZ position receives LP fees directly. Marketplace
royalties, historical event readers, saved-transaction recovery and converter
wrapper policies remain separate live responsibilities.
