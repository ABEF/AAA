# Main website interaction state: scoped verification

2026-10-19. Internal frontend checks only; production release NOT APPROVED.
Website implementation published on main as `6a65a5822990b0464de9564be8931fcb41ac911a`; public server unchanged.

## Implemented scope

Main website app/wallet code incorporates per-NFT/mint operation tracking,
independent actions, atomic overlapping-batch rejection, same-origin Web Locks,
latest-state demo commits, bounded lock waits, reset invalidation, explicit storage
errors, silent public-account restoration and wallet-context cancellation.
Dormant financial rows/actions are omitted, fixed royalty multipliers retained,
Claim/Grow separated, inline feedback shown and changed loaded artwork animated.
No test launcher, local-view adapter, backend, Solidity, signer, public deployment,
economics or monitoring change. No public transactions. The serial local server
is intentionally retained; default-only imports do not require restarting it.

## Executed evidence

- `node --test tests/ui-state.test.mjs tests/domain.test.mjs`: **53 passes**,
  no failures/skips. Seventeen new cases cover independent/overlapping resources,
  cross-tab conflicting resources and release on failure, latest-state top-ups,
  competing claims, unique mint identities, reset races, persistence errors,
  context changes during a queued commit, corrupt/full logs, unsupported locks,
  legacy LP-only replay, silent restoration, late connection cancellation, and
  account/network round trips. Thirty-six existing domain/wallet cases cover the
  affected wallet and persistence consumers; unchanged Solidity/artwork suites
  were not rerun.
- JS syntax and the existing static/artwork reference check pass: 89 unique
  element IDs, five views, 2,784 artwork/metadata pairs and 1,000 inventory rows.
  Final build contains **5,588 files**. No new dependency installed.
- Main website browser checks used isolated origin `http://127.0.0.1:4179`,
  not the user's running local contract session. Verified dormant #74 shows ×3
  and no fee/claim controls, with inline missing-acknowledgement feedback.
  #444 claim showed only its own controls pending while other NFTs remained
  enabled. Its cumulative LP + royalties became $196.50 without changing LP.
- Ran #74 $1,000 activation in one tab while #128 claim ran in another.
  Both persisted: #74 became Enhanced with $1,000 LP and zero retroactive fees;
  #128 showed $477.99 lifetime claimed and zero remaining rewards. Total attached
  demo LP became $104,132. Reload retained the connection and both results.
  Reset through the visible UI restored the isolated baseline afterward.
- Browser error/warning log was empty. Visual inspection confirmed dark styling,
  separate buttons, fixed gray dormant multiplier and readable active fee rows.
  Screenshot is saved externally with the task evidence. Public site untouched.

[Source bindings](source-bindings.json) identify the verified website source and
test bodies. App-only feedback refinements after the test run were syntax/build
checked and inspected in the browser; the tested state/store/wallet bodies stayed
unchanged. No unchanged contract suite or production rehearsal is implied.

## Review and limits

The previous page-global operation flag hid two races: stale precomputed results
could overwrite parallel actions, and separate tabs could overwrite their event
logs. Simply removing the flag was unsafe. Resource admission plus revalidation
inside a short locked commit addresses both for the simulation. Lock callbacks
release on rejection; no automatic mutation retry is introduced. State is published
only after persistence succeeds. Reset epochs stop stale actions resurrecting data.
Wallet revision changes also invalidate change-away-and-back cases. Browser restore
never invokes `eth_requestAccounts` automatically or signing RPC methods.

Web Locks and localStorage apply to a single browser origin, not multiple real
users/devices. The public financial path remains simulated and is not production
load-tested. Actual signing/nonces, pinned manifests, fresh quotes, transaction
hash persistence, receipt/replacement/reorg recovery and isolated hosted services
remain under central frontend/service tasks. No task was marked complete from
this simulation. The operator manual and feature reference describe these bounds.
