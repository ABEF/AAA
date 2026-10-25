"""Extract exact expectations and record the independent native-fixture review.

This is source evidence extraction, not a Solidity test or security proof.
Reviewed dispositions are explicit below; test counts alone do not establish
equivalence. The original source remains archived byte-for-byte.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
OLD = 'reports/deep-cleanup-20261025/native-liquidity-before.sol.txt'
CURRENT = 'test/NativeLiquidity.t.sol'


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def lexical_mask(raw):
    result = list(raw)
    i = 0
    while i < len(raw):
        end = i
        if raw.startswith('//', i):
            end = raw.find('\n', i)
            if end < 0: end = len(raw)
        elif raw.startswith('/*', i):
            end = raw.find('*/', i + 2) + 2
            if end < 2: raise ValueError('Unclosed comment')
        elif raw[i] in ('"', "'"):
            quote = raw[i]
            end = i + 1
            while end < len(raw):
                if raw[end] == '\\': end += 2; continue
                if raw[end] == quote: end += 1; break
                end += 1
        if end > i:
            for j in range(i, end):
                if result[j] not in '\r\n': result[j] = ' '
            i = end
        else: i += 1
    return ''.join(result)


def functions(path):
    raw = (ROOT / path).read_text(encoding='utf-8-sig')
    masked = lexical_mask(raw)
    found = {}
    for match in re.finditer(r'\bfunction\s+(\w+)\s*\(', masked):
        start = masked.find('{', match.end())
        semi = masked.find(';', match.end())
        if start < 0 or 0 <= semi < start: continue
        depth, end = 1, start + 1
        while depth:
            depth += (masked[end] == '{') - (masked[end] == '}')
            end += 1
        assertions = []
        for call in re.finditer(r'\b(?:assert\w+|vm\.expectRevert|_clearApprovals)\s*\(', masked[start:end]):
            a = start + call.start()
            b = start + call.end()
            nesting = 1
            while nesting:
                nesting += (masked[b] == '(') - (masked[b] == ')')
                b += 1
            assertions.append({'line': raw.count('\n', 0, a) + 1, 'expectation': raw[a:b]})
        name = match.group(1)
        if name in found: continue  # Only reviewed fixture names below are unique.
        found[name] = {'source': path, 'line': raw.count('\n', 0, match.start()) + 1,
                       'body_sha256': hashlib.sha256(raw[start:end].encode()).hexdigest(),
                       'assertions': assertions}
    return found


def ref(path, method):
    return path + ':' + method


N = lambda method: ref(CURRENT, method)
F = lambda method: ref('test/NativeAssetFoundation.t.sol', method)
E = lambda method: ref('test/IntegratedEconomicConservation.t.sol', method)

# Every old method was re-read against current callers and installed dependencies.
# The prior deprecation map is not used as authority or as input to this script.
ROWS = [
 ('testNativeMintSpendsOnlyExactDebtAndPreservesPrefunds', [N('testNativeMintSpendsOnlyExactDebtAndPreservesPrefunds')],
  'Preserved', 'Actual PosM ownership, positive spends, exact caller spend/refund and all native/ERC20/WETH prefunds are checked. Native funds use msg.value rather than pulling WETH. The unused-wrapper approval assertion is deliberately retired; active token/Permit2 allowance and expiration cleanup remain.'),
 ('testNativeIncreaseReusesPositionAndClearsApprovals', [N('testNativeIncreaseReusesPositionAndClearsApprovals')],
  'Preserved', 'Same LP NFT grows without minting another; exact caller ETH/token deltas are added. Only unused native-wrapper approval coupling retires.'),
 ('testNativeCollectWrapsOnlyActualCreditsIncludingDonationFees', [N('testNativeCollectReturnsOnlyActualCoreFeesIncludingDonations'),F('testNativeCollectAndDisabledClosePayETHWithFailedWrapper')],
  'Intentionally changed denomination', 'Native receipts are ETH, not freshly minted WETH. Actual Core donation fee growth can round, so the actual-Core case bounds receipts and checks a second collection is empty; the unchanged deterministic foundation case retains exact +17 ETH/+29 token cash accounting and prefund assertions.'),
 ('testNativeCloseReturnsWrappedPrincipalWithoutExposingNativeToVault', [N('testNativeCloseReturnsActualPrincipalInETHWithoutWrapping')],
  'Intentionally changed denomination', 'Actual principal amounts return in ETH and the pool token, with exact physical deltas and destroyed PosM ownership. Requiring no native ETH at the Vault contradicts current native custody and raw ETH/ZZZ exit.'),
 ('testNativeInputSwapResetsDirtySyncAndUsesNetDelta', [N('testNativeInputSwapResetsActualCoreDirtySyncAndUsesNetDelta')],
  'Preserved with actual venue pricing', 'Real Core dirty sync is reset; exact native input and token output deltas and no Manager residual are checked. The fabricated 0.99 output is replaced by output below gross input and above the requested floor.'),
 ('testNativeOutputSwapWrapsNetDeltaAndPreservesForcedETH', [N('testNativeOutputSwapPaysETHAndPreservesForcedPrefunds')],
  'Intentionally changed denomination', 'Real native output goes directly to the caller and retains forced Manager ETH; token input is exact. Fixed fake 0.99/WETH output is not a current guarantee.'),
 ('testNativePartialInputRejectedAtomically', [N('testNativeUnfillableInputRevertsAllCoreAndWalletState'),F('testNativePartialSettlementAndUnexpectedETHRevertAtomically'),N('testNativeExactInputGuardRejectsPartialFillEvenWhenOutputPassesOracleFloor')],
  'Verification gap identified and strengthened', 'The 1000 ETH/980 ETH replacement proves rollback but its minimum-output check masks removal of the exact-input check. The unchanged foundation short-fill-by-one case still covers that guard. A new actual-Core narrow-range observation proves a partial fill whose output meets the oracle floor, followed by an exact Slippage rejection and full state equality; its execution is recorded separately.'),
 ('testNativeMinOutIncludesExecutionFees', [N('testNativeMinimumOutputIncludesActualLPAndProtocolFees')],
  'Preserved', 'Actual LP/protocol fees and price impact cause the deliberately excessive minimum to reject. Price and caller cash remain unchanged. An additional Manager-zero assertion in this exact test is not retained, but other native cases assert the Manager balance and the revert restores its initial zero balance.'),
 ('testNativeUnexpectedSenderAndCallbackRejected', [N('testNativeUnexpectedSenderAndCallbackRejected')],
  'Preserved', 'Unsolicited native transfer and unauthenticated callback both reject.'),
 ('testNativeIncorrectWrapperRejectedBeforePull', [N('testNativeIdentityMustBeAdmittedBeforePullOrMint'),F('testNativeETHOracleAndSourceAdmissionAreDistinctFromWETH')],
  'Obsolete wrapper rule replaced', 'Registry native identity, not a WETH accounting substitute, controls native entry. Current negative admission preserves ETH/token funds and next PosM ID. Native and WETH feeds/admission are separately tested; an unused wrapper cannot disable custody.'),
 ('testNativeAmountsRemainUint128BoundedWithoutPermitApproval', [N('testNativeAmountsStayUint128BoundedWithoutPermitApproval')],
  'Pre-existing verification gap strengthened', 'Both old and first replacement sent zero msg.value and accepted any revert, so a later value check could hide removal of the uint128 bound. The repaired method supplies matching native value for oversized amount0 and amount1, poisons later pool reads, requires exact InvalidAmount, and checks cash/position/allowances unchanged. Production already had the early guard.'),
 ('testNativeLiquidityCallbackHookMaskRejected', [N('testNativeHookAndDynamicFeePoliciesRejectBeforeVenueExecution')],
  'Preserved', 'Hooked native keys reject and do not mint a PosM NFT. This remains a hookless-only deployment; no hook implementation is added.'),
 ('testNativeDynamicFeeRejected', [N('testNativeHookAndDynamicFeePoliciesRejectBeforeVenueExecution')],
  'Preserved', 'The dynamic-fee key rejects and does not mint a PosM NFT. The two old methods are merged; their policy checks both remain.'),
 ('testNativeBrokenWithdrawRollsBack', [N('testNativeLifecycleDoesNotCallAnUnusedBrokenWrapper'),F('testNativeMintAndIncreaseReturnUnusedETHWithoutCallingBrokenWrapper')],
  'Obsolete wrapper dependency retired', 'Current native mint/increase do not unwrap WETH, so a broken unused withdraw must not block them. Exact native cash/refunds and unspent token/prefund/allowance safety replace the obsolete failure requirement.'),
 ('testNativeBrokenDepositRollsBackCredits', [N('testNativeLifecycleDoesNotCallAnUnusedBrokenWrapper'),F('testNativeRejectedRecipientRollsBackAndReentryCannotCollectTwice')],
  'Obsolete wrapper dependency retired', 'Native collection does not deposit into WETH. Its fee liability must survive actual delivery failure, now tested with a rejecting ETH recipient and successful later retry rather than an irrelevant wrapper deposit failure.'),
 ('testNativeUnconsumedPosmValueRollsBackInsteadOfSweeping', [F('testNativeRetainedPositionValueRevertsInsteadOfSubsidizingLaterLP'),N('testNativePendingFeesMustBeCollectedBeforeIncreasingPrincipal')],
  'Preserved through explicit fault seam', 'The unchanged foundation retainNative fault preserves user ETH/token balances and next ID. Actual PosM fee-netting supplies a second real residual case: increase before harvest rejects, then harvest/increase succeeds. An intentionally broken PosM is not presented as real venue behavior.'),
 ('testNativeForcedETHDuringTakeCannotBeClaimed', [F('testNativePartialSettlementAndUnexpectedETHRevertAtomically'),N('testForcedETHDuringNativeForwardCannotBecomeIncome')],
  'Preserved at both boundaries', 'Foundation still injects forced ETH from the expected Core take path and checks caller balances. The actual-Core case separately forces ETH back during recipient forwarding, verifies failure/Manager zero and permits a clean retry. These are distinct injection points, not identical tests.'),
 ('testNativeWrapperReentryFailsWhileCreditStillSucceeds', [F('testNativeRejectedRecipientRollsBackAndReentryCannotCollectTwice')],
  'Obsolete wrapper callback retired; active callback protected', 'An unused wrapper no longer runs during native swaps. A real ETH recipient callback attempts collect reentry, fails to enter, receives the original credit exactly once and clears its recorded fees.'),
 ('testNativeRegistryAdmissionRejectsUnreviewedDependencies', [ref('test/FixedZZZPool.t.sol','testNativeAdmissionRetainsItsSeparateFixedIdentityGuard'),ref('test/NativeSourceIdentity.t.sol','testMatchingSourceStillCannotBypassNativeRuntimePins')],
  'Negative admission preserved; real qualification open', 'The old any-revert tests could reject for an unset identity/unsupported native getter rather than each claimed runtime dependency. Current source/chain/runtime negative cases are explicit, but neither old nor replacement tests qualify a fully matching real deployed dependency inventory. That remains a release gate.'),
 ('testNativePlanBalancesNetAmountsWithinOnePercentBudget', [N('testNativePlannerReadsActualDirectionalProtocolFee'),E('testActualV4ThinMarketReconcilesActualPostSwapRatioWithinOriginalOnePercentFloor')],
  'Behavior preserved with corrected evidence reference', 'The old fixed 0.99 fake output and >99.25% placement were fixture-specific, not guaranteed economics. The real two-pass Entry test explicitly requests the stricter 1% floor, asserts actual deployed LP >=99 from 100 and low idle. The earlier mapping incorrectly cited the direct paired-input cap test, which does not exercise the single-sided planner.'),
 ('testNativePlanUsesDirectionalProtocolFeesAndRejectsChangedLPFee', [N('testNativePlannerReadsActualDirectionalProtocolFee')],
  'Preserved', 'Actual Core fee changes distinguish the chosen direction from the other packed direction; a mismatched LP fee returned by the explicit StateView fault rejects. The root selected 32-method execution includes this method.'),
 ('testNativeDisabledPoolStillCollectsAndClosesButCannotEnterOrSwap', [N('testNativeDisabledPoolCollectsAndClosesButCannotEnterOrSwap'),F('testNativeCollectAndDisabledClosePayETHWithFailedWrapper')],
  'Preserved; ETH denomination', 'Disabled mint/increase/swap reject; fee collection and close succeed, including with an unavailable oracle. Exact fee/native principal delivery is also retained in the unchanged foundation test. Pool stop must not block raw custody extraction.'),
 ('testNativeDisabledPoolExitDoesNotReadUnavailableOracle', [N('testNativeDisabledPoolCollectsAndClosesButCannotEnterOrSwap')],
  'Preserved by merged case', 'Oracle is explicitly replaced by a reverting contract after disabling operations, and actual collection/close still succeed and burn ownership. The separate old explicit Manager-zero assertion is not repeated in this merged method; native no-residual safety has independent current checks.'),
 ('testNativeExitPolicyIgnoresDisabledFlagButRequiresValidOracle', [N('testNativeExitPriceIgnoresStopFlagButStillRequiresValidOracle')],
  'Preserved', 'Strategy ordinary validation rejects a disabled pool; exit-price validation ignores the stop flag but still rejects unavailable prices. Raw parking/close does not call this oracle-requiring maintenance path.'),
]

# Assertion-specific exceptions to preserved postconditions. This prevents a
# whole-method verdict from silently labelling every old assertion equivalent.
ASSERTION_DIFFERENCES = {
 ('testNativeCollectWrapsOnlyActualCreditsIncludingDonationFees',1): ('Intentional denomination change', 'Actual ETH receipt replaces +17 WETH. Exact +17 ETH cash remains in the unchanged foundation case; actual Core rounds accrued fees.'),
 ('testNativeCollectWrapsOnlyActualCreditsIncludingDonationFees',2): ('Exact check retained in peer', 'The exact +29 token check remains in NativeAssetFoundation; actual Core donation checks are positive/bounded and a second collection is empty.'),
 ('testNativeCloseReturnsWrappedPrincipalWithoutExposingNativeToVault',1): ('Intentional denomination change', 'Exact returned native principal replaces exact newly wrapped principal.'),
 ('testNativeCloseReturnsWrappedPrincipalWithoutExposingNativeToVault',3): ('Obsolete assertion intentionally removed', 'Native ETH must now increase by actual returned principal; requiring an unchanged native balance would contradict direct ETH custody.'),
 ('testNativeInputSwapResetsDirtySyncAndUsesNetDelta',1): ('Fixture-specific quote retired', 'A synthetic fixed 0.99 output is replaced by actual Core output, exact receipt, and caller minimum enforcement.'),
 ('testNativeInputSwapResetsDirtySyncAndUsesNetDelta',3): ('Intentional denomination change', 'Exactly 1 native ETH is spent rather than pulling and unwrapping 1 WETH.'),
 ('testNativeOutputSwapWrapsNetDeltaAndPreservesForcedETH',1): ('Fixture-specific quote retired', 'Actual output must clear the minimum and is received exactly; 0.99 was supplied by the old fake venue.'),
 ('testNativeOutputSwapWrapsNetDeltaAndPreservesForcedETH',2): ('Intentional denomination change', 'Caller ETH increases by the actual returned output, with exact token input and no WETH minted.'),
 ('testNativePartialInputRejectedAtomically',1): ('Verification gap strengthened', 'The broad replacement could fail solely on output minimum. Unchanged foundation checks and the new narrow-range real-delta probe isolate the exact-input restriction.'),
 ('testNativePartialInputRejectedAtomically',2): ('Intentional denomination change', 'Caller native/token balances replace caller wrapped balance, with additional physical LP and pool-price rollback checks.'),
 ('testNativePartialInputRejectedAtomically',3): ('Fake field replaced by actual state checks', 'BoundaryCore.debt does not exist in real Core. Actual unlock enforces zero deltas; new partial-fill proof checks Core balances, price, protocol fees and LP state remain unchanged after rejection.'),
 ('testNativeMinOutIncludesExecutionFees',2): ('Direct assertion moved', 'This exact Manager-zero check is absent from the new minimum-output method. Its revert restores initial zero state; other actual native failure tests explicitly assert Manager balance/prefund equality.'),
 ('testNativeIncorrectWrapperRejectedBeforePull',1): ('Obsolete wrapper admission retired', 'A native identity rejection replaces rejecting a native-to-WETH accounting substitution. The unused wrapper is not a principal dependency.'),
 ('testNativeIncorrectWrapperRejectedBeforePull',2): ('Principal-denomination check replaced', 'Native ETH/token funds and next PosM ID remain unchanged on rejected native admission; no wrapper balance is pulled.'),
 ('testNativeAmountsRemainUint128BoundedWithoutPermitApproval',1): ('Pre-existing weak negative repaired', 'Correct msg.value plus poisoned later reads and exact InvalidAmount now distinguish the actual uint128 bound from a later value mismatch.'),
 ('testNativeBrokenWithdrawRollsBack',1): ('Obsolete failure intentionally inverted', 'Native mint/increase succeed with a broken unused wrapper, because no unwrap is executed.'),
 ('testNativeBrokenWithdrawRollsBack',2): ('Unused wrapper untouched', 'No wrapper call or WETH principal spend occurs; the actual lifecycle checks zero wrapper supply/balance.'),
 ('testNativeBrokenWithdrawRollsBack',3): ('Obsolete failure postcondition retired', 'A broken unused wrapper no longer prevents issuance of an underlying LP NFT; successful mint/growth now check real ownership and liquidity.'),
 ('testNativeBrokenDepositRollsBackCredits',1): ('Obsolete failure intentionally inverted', 'Native collection must not depend on a WETH deposit operation.'),
 ('testNativeBrokenDepositRollsBackCredits',2): ('Relevant delivery liability preserved elsewhere', 'Exact +17 pending native fees survive an actual rejecting recipient in the unchanged foundation case, then are delivered once on retry; wrapper failure is irrelevant.'),
 ('testNativeUnconsumedPosmValueRollsBackInsteadOfSweeping',2): ('Intentional denomination change', 'Unchanged foundation retainNative fault checks exact caller ETH/token preservation rather than a WETH balance.'),
 ('testNativeForcedETHDuringTakeCannotBeClaimed',2): ('Intentional denomination change', 'Current tests check caller ETH/token and Manager prefunds rather than new WETH receipts.'),
 ('testNativeWrapperReentryFailsWhileCreditStillSucceeds',1): ('Inactive callback retired; active callback covered', 'Native settlement no longer invokes the wrapper. An actual ETH recipient callback still attempts and fails reentry while the original fee credit is delivered once.'),
 ('testNativeRegistryAdmissionRejectsUnreviewedDependencies',1): ('Negative test purpose narrowed honestly', 'The old generic configure(native-zero) any-revert did not isolate all runtime pins. Native source/chain/runtime rejection tests remain; full actual venue qualification is not claimed.'),
 ('testNativeRegistryAdmissionRejectsUnreviewedDependencies',2): ('Negative test purpose narrowed honestly', 'The old native configure any-revert could reject at an absent native getter or unset source identity. Current identity/runtime tests make those causes explicit, without pretending positive actual admission.'),
 ('testNativePlanBalancesNetAmountsWithinOnePercentBudget',2): ('Normalized real execution evidence', 'The real two-pass Entry test deploys at least 99 of 100 under an explicit stricter 1% caller/policy bound, not merely idle-inclusive NAV.'),
 ('testNativePlanBalancesNetAmountsWithinOnePercentBudget',3): ('Incidental fixture result retired', '>99.25% for a fake fee/range is not a product rule. Current default is 98%, and an explicitly stricter 99% actual placement scenario is retained.'),
 ('testNativeDisabledPoolStillCollectsAndClosesButCannotEnterOrSwap',4): ('Denomination changed; exact check retained in peer', 'Actual Core pays positive ETH fees while disabled; unchanged foundation checks the exact native +17 amount and principal separately.'),
 ('testNativeDisabledPoolExitDoesNotReadUnavailableOracle',1): ('Direct assertion moved', 'The merged actual disabled/oracle-outage test does not repeat this Manager-zero literal. It still completes collect/close and destroys LP ownership; exact prefund/no-residual checks exist in other native cases.'),
}

old = functions(OLD)
assert len([name for name in old if name.startswith('test')]) == len(ROWS) == 24
references = {}
matrix = []
assertion_rows = []
for old_name, refs, verdict, analysis in ROWS:
    previous = old[old_name]
    for item in refs:
        path, method = item.split(':', 1)
        references[item] = functions(path)[method]
    matrix.append({'previous_method': old_name, 'previous_line': previous['line'],
                   'previous_body_sha256': previous['body_sha256'], 'current_references': refs,
                   'verdict': verdict, 'review': analysis})
    for index, assertion in enumerate(previous['assertions'], 1):
        entry = {'id': f'{old_name}.{index}', 'old_source': OLD, **assertion,
                 'current_references': refs, 'verdict': verdict, 'review': analysis}
        specific = ASSERTION_DIFFERENCES.get((old_name,index),
            ('Preserved postcondition', 'The current referenced method retains this ownership, balance, no-mint, rejection or directional-policy postcondition; exact current assertion text is in current_assertion_references.'))
        entry['assertion_verdict'], entry['assertion_correspondence'] = specific
        if assertion['expectation'] == '_clearApprovals()':
            entry['old_helper_assertions'] = old['_clearApprovals']['assertions']
            entry['current_helper_assertions'] = functions(CURRENT)['_clearApprovals']['assertions']
            entry['helper_difference'] = 'Native ERC20 token and Permit2 amount reset remain, expiry reset is added. A WETH-to-Permit2 allowance check is retired because native operations never approve that unused wrapper; generic ERC20 liquidity still separately resets both actual pair approvals.'
        assertion_rows.append(entry)

source_names = sorted({OLD, CURRENT, *[key.split(':', 1)[0] for key in references]})
result = {'schema': 1, 'purpose': 'Independent assertion-level old/current source review; not a fresh full regression.',
          'original_test_methods': 24, 'first_replacement_methods': 20,
          'current_test_methods': len([name for name in functions(CURRENT) if name.startswith('test')]),
          'original_direct_expectation_and_helper_calls': len(assertion_rows),
          'original_effective_expectations_expanding_two_helper_calls': len(assertion_rows)-2+2*len(old['_clearApprovals']['assertions']),
          'source_sha256': {name: sha(name) for name in source_names}, 'method_matrix': matrix,
          'individual_old_expectations': assertion_rows, 'current_assertion_references': references,
          'verification_limits': [
              'The earlier 32-method execution is separately source/body-bound and is not automatically rerun or relabelled after these test improvements.',
              'The new exact-input and repaired uint128 methods passed in the separately recorded two-case current selected execution: solidity/native-regressions-verification.json.',
              'Referenced unchanged peer tests establish where assertions currently exist. Their original evidence scope is retained; source existence is not a fresh execution pass.',
              'Pinned actual Core/PosM are used for native integration; authority/admission/prices/Permit2 are explicit local seams, not real service qualification.',
              'No production source, custody authority, economic split, loss cap, supported asset or public signing policy changes arise from this review.']}
(OUT / 'native-assertion-matrix.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
lines=['# Independent native-fixture assertion review', '',
       f"The archived 24-method fixture contains {len(assertion_rows)} direct assertions/expectations/helper calls ({result['original_effective_expectations_expanding_two_helper_calls']} expectations when its two approval-helper calls are expanded). Each is extracted verbatim with a source line and reviewed correspondence in [the assertion matrix](native-assertion-matrix.json).", '',
       'The first replacement had 20 methods. Current native tests add one actual-Core exact-input sensitivity case and strengthen the existing uint128-bound case. Production guards are unchanged. Test counts alone do not establish preserved coverage.', '',
       '| Previous test | Current correspondence | Verdict |', '| --- | --- | --- |']
for row in matrix:
    lines.append('| `'+row['previous_method']+'` | '+', '.join('`'+x.split(':',1)[1]+'`' for x in row['current_references'])+' | '+row['verdict']+' |')
lines += ['', '## Material conclusions', '',
 '1. Native-to-WETH custody expectations are legitimately retired: current ETH remains ETH, fixed ZZZ is the other principal token, and raw custody exit sends actual pair assets without requiring WETH. Exact balances, refunds, permissions and liabilities remain required.',
 '2. The broad 1000-ETH unfillable swap test did not isolate the exact-input guard: its output floor also rejects. An unchanged foundation test retained the one-wei short-fill check. The new actual-Core narrow-range probe proves a partial fill whose output clears the floor, then requires the Manager’s exact Slippage error and full rollback.',
 '3. Both old and initial replacement uint128 tests accepted any revert with missing native value. The repaired method supplies matching value for both oversized amount slots, poisons later reads, requires exact InvalidAmount and checks unchanged funds/position/approval state. This is a pre-existing verification weakness, not a production bound regression.',
 '4. The prior planner mapping pointed to a direct paired-input cap test. The correct planner evidence is `testActualV4ThinMarketReconcilesActualPostSwapRatioWithinOriginalOnePercentFloor`, which actually executes single-sided two-pass planning and checks deployed LP rather than idle-inclusive NAV. The artificial >99.25% fixture outcome is not a universal guarantee.',
 '5. Some exact assertions moved to unchanged foundation/typed-executor tests. The matrix distinguishes these from assertions directly present in the 20 replacement methods. Real native admission/runtime qualification remains open; old any-revert admission tests did not prove each dependency independently.',
 '', '## Verification boundary', '',
 'The earlier 32-method pass retains its exact source/body scope. The new exact-input and repaired bound methods now passed in [the separate two-case execution](solidity/NATIVE_REGRESSIONS.md); unchanged peers were not rerun. Referenced peer-test presence is not a fresh pass. No live RPC, existing Anvil, service, wallet journal, deployment or public transaction is used. Actual feeds/routes/VRF/OpenSea/authorities/operations, maximal gas/economics and independent review remain release gates.']
(OUT / 'native-assertion-matrix.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
print(json.dumps({'old_methods':24,'current_methods':result['current_test_methods'],
                  'direct_expectations':len(assertion_rows),'expanded_expectations':result['original_effective_expectations_expanding_two_helper_calls'],
                  'reviewed_peer_methods':len(references),'status':'source review; current new-case execution recorded separately'}))
